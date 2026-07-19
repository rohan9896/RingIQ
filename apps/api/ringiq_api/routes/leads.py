import csv
import io
import re
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.ringiq_api.auth.context import TenantContext, get_current_tenant_context
from apps.api.ringiq_api.db.session import get_db_session
from apps.api.ringiq_api.models.leads import (
    Lead,
    LeadImport,
    LeadImportRow,
    LeadImportRowStatus,
    LeadManualStatus,
    LeadStatus,
)
from apps.api.ringiq_api.schemas.leads import (
    LeadCreateRequest,
    LeadImportCreateRequest,
    LeadImportDetailResponse,
    LeadImportResponse,
    LeadResponse,
    LeadUpdateRequest,
)

router = APIRouter(prefix="/v1", tags=["leads"])

CANONICAL_COLUMNS = ("name", "email", "phone_number")
HEADER_ALIASES = {
    "name": {"name", "full_name", "lead_name"},
    "email": {"email", "email_address", "mail"},
    "phone_number": {"phone", "phone_number", "mobile", "mobile_number", "contact_number"},
}


def _header_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def _resolve_mapping(headers: list[str], requested: dict[str, str]) -> dict[str, str]:
    header_lookup = {_header_key(header): header for header in headers}
    mapping: dict[str, str] = {}
    for column in CANONICAL_COLUMNS:
        selected = requested.get(column)
        if selected in headers:
            mapping[column] = selected
            continue
        for alias in HEADER_ALIASES[column]:
            if alias in header_lookup:
                mapping[column] = header_lookup[alias]
                break
    return mapping


def _normalize_phone(value: str) -> str | None:
    cleaned = re.sub(r"[^0-9+]", "", value.strip())
    if cleaned.startswith("00"):
        cleaned = "+" + cleaned[2:]
    if cleaned.startswith("+"):
        digits = cleaned[1:]
    else:
        digits = cleaned
        if len(digits) == 10:
            digits = f"91{digits}"
        elif len(digits) == 12 and digits.startswith("91"):
            pass
        else:
            return None
    if not digits.isdigit() or not 10 <= len(digits) <= 15:
        return None
    return f"+{digits}"


def _validate_row(row: dict[str, str], mapping: dict[str, str]) -> tuple[dict[str, str] | None, str | None, str | None]:
    missing = [column for column in CANONICAL_COLUMNS if not row.get(mapping.get(column, ""), "").strip()]
    if missing:
        return None, "missing_required_fields", f"Missing required fields: {', '.join(missing)}."
    email = row[mapping["email"]].strip()
    if "@" not in email or email.startswith("@") or email.endswith("@"):
        return None, "invalid_email", "Email address is invalid."
    normalized_phone = _normalize_phone(row[mapping["phone_number"]])
    if normalized_phone is None:
        return None, "invalid_phone_number", "Phone number must be a valid Indian or E.164 number."
    return {
        "name": row[mapping["name"]].strip(),
        "email": email,
        "phone_number": row[mapping["phone_number"]].strip(),
        "normalized_phone_number": normalized_phone,
    }, None, None


async def _commit(session: AsyncSession, detail: str) -> None:
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=409, detail=detail) from exc
    except SQLAlchemyError as exc:
        await session.rollback()
        raise HTTPException(status_code=503, detail="lead_store_unavailable") from exc


async def _get_lead(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    lead_id: uuid.UUID,
) -> Lead:
    statement = select(Lead).where(
        Lead.id == lead_id,
        Lead.tenant_id == tenant_id,
    )
    lead = (await session.execute(statement)).scalar_one_or_none()
    if lead is None:
        raise HTTPException(status_code=404, detail="lead_not_found")
    return lead


def _validate_email(email: str) -> str:
    normalized_email = email.strip()
    if (
        "@" not in normalized_email
        or normalized_email.startswith("@")
        or normalized_email.endswith("@")
    ):
        raise HTTPException(status_code=422, detail="invalid_email")
    return normalized_email


@router.post("/lead-imports", response_model=LeadImportDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_lead_import(
    payload: LeadImportCreateRequest,
    context: TenantContext = Depends(get_current_tenant_context),
    session: AsyncSession = Depends(get_db_session),
) -> LeadImport:
    try:
        reader = csv.DictReader(io.StringIO(payload.csv_content))
        headers = reader.fieldnames or []
        rows = list(reader)
    except csv.Error as exc:
        raise HTTPException(status_code=422, detail="invalid_csv") from exc
    if not headers:
        raise HTTPException(status_code=422, detail="csv_headers_required")
    if len(rows) > 10_000:
        raise HTTPException(status_code=422, detail="csv_row_limit_exceeded")
    mapping = _resolve_mapping(headers, payload.column_mapping)
    missing_columns = [column for column in CANONICAL_COLUMNS if column not in mapping]
    if missing_columns:
        raise HTTPException(status_code=422, detail={"code": "required_columns_missing", "columns": missing_columns})

    lead_import = LeadImport(
        tenant_id=context.tenant_id,
        filename=payload.filename,
        total_rows=len(rows),
        column_mapping_json=mapping,
        created_by_user_id=context.user_id,
    )
    session.add(lead_import)
    await session.flush()
    import_rows: list[LeadImportRow] = []
    for row_number, raw_row in enumerate(rows, start=2):
        raw_data = {header: value or "" for header, value in raw_row.items() if header is not None}
        valid, error_code, error_message = _validate_row(raw_data, mapping)
        if valid is None:
            lead_import.invalid_rows += 1
            import_rows.append(LeadImportRow(
                tenant_id=context.tenant_id,
                lead_import_id=lead_import.id,
                row_number=row_number,
                status=LeadImportRowStatus.INVALID.value,
                error_code=error_code,
                error_message=error_message,
                raw_data_json=raw_data,
            ))
            continue
        existing = (await session.execute(select(Lead).where(
            Lead.tenant_id == context.tenant_id,
            Lead.normalized_phone_number == valid["normalized_phone_number"],
        ))).scalar_one_or_none()
        if existing is not None:
            lead_import.duplicate_rows += 1
            import_rows.append(LeadImportRow(
                tenant_id=context.tenant_id,
                lead_import_id=lead_import.id,
                lead_id=existing.id,
                row_number=row_number,
                status=LeadImportRowStatus.DUPLICATE.value,
                error_code="duplicate_phone_number",
                error_message="A lead with this phone number already exists in this workspace.",
                raw_data_json=raw_data,
            ))
            continue
        attributes = {
            _header_key(header): value
            for header, value in raw_data.items()
            if header not in mapping.values() and value.strip()
        }
        lead = Lead(
            tenant_id=context.tenant_id,
            name=valid["name"],
            email=valid["email"],
            phone_number=valid["phone_number"],
            normalized_phone_number=valid["normalized_phone_number"],
            attributes_json=attributes,
            created_by_user_id=context.user_id,
            updated_by_user_id=context.user_id,
        )
        session.add(lead)
        await session.flush()
        lead_import.imported_rows += 1
        import_rows.append(LeadImportRow(
            tenant_id=context.tenant_id,
            lead_import_id=lead_import.id,
            lead_id=lead.id,
            row_number=row_number,
            status=LeadImportRowStatus.IMPORTED.value,
            raw_data_json=raw_data,
        ))
    session.add_all(import_rows)
    await _commit(session, "lead_import_conflict")
    await session.refresh(lead_import)
    lead_import.rows = import_rows  # type: ignore[attr-defined]
    return lead_import


@router.get("/lead-imports", response_model=list[LeadImportResponse])
async def list_lead_imports(
    context: TenantContext = Depends(get_current_tenant_context),
    session: AsyncSession = Depends(get_db_session),
) -> list[LeadImport]:
    statement = select(LeadImport).where(LeadImport.tenant_id == context.tenant_id).order_by(LeadImport.created_at.desc())
    return list((await session.execute(statement)).scalars().all())


@router.get("/lead-imports/{lead_import_id}", response_model=LeadImportDetailResponse)
async def get_lead_import(
    lead_import_id: uuid.UUID,
    context: TenantContext = Depends(get_current_tenant_context),
    session: AsyncSession = Depends(get_db_session),
) -> LeadImport:
    lead_import = (await session.execute(select(LeadImport).where(
        LeadImport.id == lead_import_id,
        LeadImport.tenant_id == context.tenant_id,
    ))).scalar_one_or_none()
    if lead_import is None:
        raise HTTPException(status_code=404, detail="lead_import_not_found")
    rows = list((await session.execute(select(LeadImportRow).where(
        LeadImportRow.lead_import_id == lead_import.id,
        LeadImportRow.tenant_id == context.tenant_id,
    ).order_by(LeadImportRow.row_number))).scalars().all())
    lead_import.rows = rows  # type: ignore[attr-defined]
    return lead_import


@router.get("/leads", response_model=list[LeadResponse])
async def list_leads(
    query: str | None = Query(default=None, max_length=255),
    include_archived: bool = False,
    context: TenantContext = Depends(get_current_tenant_context),
    session: AsyncSession = Depends(get_db_session),
) -> list[Lead]:
    statement = select(Lead).where(Lead.tenant_id == context.tenant_id)
    if not include_archived:
        statement = statement.where(Lead.status == LeadStatus.ACTIVE.value)
    if query:
        pattern = f"%{query.strip()}%"
        statement = statement.where(
            Lead.name.ilike(pattern) | Lead.email.ilike(pattern) | Lead.normalized_phone_number.ilike(pattern)
        )
    statement = statement.order_by(Lead.created_at.desc()).limit(200)
    return list((await session.execute(statement)).scalars().all())


@router.post("/leads", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(
    payload: LeadCreateRequest,
    context: TenantContext = Depends(get_current_tenant_context),
    session: AsyncSession = Depends(get_db_session),
) -> Lead:
    phone_number = payload.phone_number.strip()
    normalized_phone_number = _normalize_phone(phone_number)
    if normalized_phone_number is None:
        raise HTTPException(status_code=422, detail="invalid_phone_number")
    lead = Lead(
        tenant_id=context.tenant_id,
        name=payload.name.strip(),
        email=_validate_email(payload.email),
        phone_number=phone_number,
        normalized_phone_number=normalized_phone_number,
        attributes_json=payload.attributes_json,
        created_by_user_id=context.user_id,
        updated_by_user_id=context.user_id,
    )
    session.add(lead)
    await _commit(session, "lead_phone_number_already_exists")
    await session.refresh(lead)
    return lead


@router.get("/leads/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: uuid.UUID,
    context: TenantContext = Depends(get_current_tenant_context),
    session: AsyncSession = Depends(get_db_session),
) -> Lead:
    return await _get_lead(session, context.tenant_id, lead_id)


@router.patch("/leads/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: uuid.UUID,
    payload: LeadUpdateRequest,
    context: TenantContext = Depends(get_current_tenant_context),
    session: AsyncSession = Depends(get_db_session),
) -> Lead:
    lead = await _get_lead(session, context.tenant_id, lead_id)
    updates = payload.model_dump(exclude_unset=True)
    if "email" in updates:
        lead.email = _validate_email(updates.pop("email"))
    if "phone_number" in updates:
        phone_number = updates.pop("phone_number").strip()
        normalized_phone_number = _normalize_phone(phone_number)
        if normalized_phone_number is None:
            raise HTTPException(status_code=422, detail="invalid_phone_number")
        lead.phone_number = phone_number
        lead.normalized_phone_number = normalized_phone_number
    for field, value in updates.items():
        setattr(lead, field, value.value if isinstance(value, LeadManualStatus) else value)
    lead.updated_by_user_id = context.user_id
    await _commit(session, "lead_phone_number_already_exists")
    await session.refresh(lead)
    return lead


@router.post("/leads/{lead_id}/archive", response_model=LeadResponse)
async def archive_lead(
    lead_id: uuid.UUID,
    context: TenantContext = Depends(get_current_tenant_context),
    session: AsyncSession = Depends(get_db_session),
) -> Lead:
    lead = await _get_lead(session, context.tenant_id, lead_id)
    lead.status = LeadStatus.ARCHIVED.value
    lead.archived_at = datetime.now(timezone.utc)
    lead.updated_by_user_id = context.user_id
    await _commit(session, "lead_archive_conflict")
    await session.refresh(lead)
    return lead


@router.post("/leads/{lead_id}/restore", response_model=LeadResponse)
async def restore_lead(
    lead_id: uuid.UUID,
    context: TenantContext = Depends(get_current_tenant_context),
    session: AsyncSession = Depends(get_db_session),
) -> Lead:
    lead = await _get_lead(session, context.tenant_id, lead_id)
    lead.status = LeadStatus.ACTIVE.value
    lead.archived_at = None
    lead.updated_by_user_id = context.user_id
    await _commit(session, "lead_restore_conflict")
    await session.refresh(lead)
    return lead

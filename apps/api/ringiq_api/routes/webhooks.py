import hashlib
import logging
from datetime import UTC, datetime, timedelta
from typing import Any, Mapping

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.ringiq_api.config import IdentitySettings, get_identity_settings
from apps.api.ringiq_api.db.session import get_db_session
from apps.api.ringiq_api.models.identity import WebhookReceipt, WebhookReceiptStatus
from apps.api.ringiq_api.services.clerk_directory import (
    ClerkDirectory,
    ClerkDirectoryUnavailable,
    ClerkUserNotFound,
    get_clerk_directory,
)
from apps.api.ringiq_api.services.platform_identity import (
    PlatformIdentityConflict,
    PlatformIdentityUnavailable,
    PlatformInvitationInvalid,
    clerk_metadata_matches_platform_user,
    deactivate_clerk_user,
    mirror_platform_user,
    platform_user_from_webhook,
    provision_platform_user,
    sync_existing_platform_user,
)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger("ringiq.api.webhooks")
RECEIPT_PROCESSING_LEASE = timedelta(minutes=1)


def verify_clerk_webhook(
    raw_body: bytes,
    headers: Mapping[str, str],
    signing_secret: str,
) -> Mapping[str, Any]:
    from standardwebhooks.webhooks import Webhook, WebhookVerificationError

    try:
        payload = Webhook(signing_secret).verify(raw_body, headers)
    except WebhookVerificationError as exc:
        raise ValueError("invalid webhook signature") from exc
    if not isinstance(payload, Mapping):
        raise ValueError("invalid webhook payload")
    return payload


async def _claim_receipt(
    session: AsyncSession,
    *,
    delivery_id: str,
    event_type: str,
    payload_hash: str,
) -> WebhookReceipt | None:
    existing = await session.scalar(
        select(WebhookReceipt).where(
            WebhookReceipt.provider == "clerk",
            WebhookReceipt.delivery_id == delivery_id,
        )
    )
    if existing is not None:
        if existing.payload_hash != payload_hash:
            raise HTTPException(status_code=400, detail="webhook_delivery_mismatch")
        if existing.status == WebhookReceiptStatus.PROCESSED.value:
            return None
        if existing.status == WebhookReceiptStatus.PROCESSING.value:
            lease_cutoff = datetime.now(UTC) - RECEIPT_PROCESSING_LEASE
            if existing.updated_at > lease_cutoff:
                raise HTTPException(
                    status_code=503,
                    detail="webhook_delivery_processing",
                )
        existing.status = WebhookReceiptStatus.PROCESSING.value
        existing.error = None
        await session.commit()
        return existing

    receipt = WebhookReceipt(
        provider="clerk",
        delivery_id=delivery_id,
        event_type=event_type,
        payload_hash=payload_hash,
    )
    session.add(receipt)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        return await _claim_receipt(
            session,
            delivery_id=delivery_id,
            event_type=event_type,
            payload_hash=payload_hash,
        )
    return receipt


@router.post("/clerk")
async def clerk_webhook(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    clerk_directory: ClerkDirectory = Depends(get_clerk_directory),
    settings: IdentitySettings = Depends(get_identity_settings),
) -> dict[str, bool]:
    if not settings.clerk_webhook_signing_secret:
        raise HTTPException(status_code=503, detail="clerk_webhook_not_configured")
    raw_body = await request.body()
    try:
        payload = verify_clerk_webhook(
            raw_body,
            dict(request.headers),
            settings.clerk_webhook_signing_secret,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="invalid_webhook_signature") from exc

    delivery_id = request.headers.get("webhook-id")
    event_type = payload.get("type")
    data = payload.get("data")
    if not delivery_id or not isinstance(event_type, str) or not isinstance(data, Mapping):
        raise HTTPException(status_code=400, detail="invalid_webhook_payload")

    receipt = await _claim_receipt(
        session,
        delivery_id=delivery_id,
        event_type=event_type,
        payload_hash=hashlib.sha256(raw_body).hexdigest(),
    )
    if receipt is None:
        return {"ok": True}

    receipt_id = receipt.id
    try:
        if event_type in {"user.created", "user.updated"}:
            event_user = platform_user_from_webhook(data)
            try:
                clerk_user = await clerk_directory.get_platform_user(
                    user_id=event_user.user_id
                )
            except ClerkUserNotFound:
                await deactivate_clerk_user(
                    session, clerk_user_id=event_user.user_id
                )
                clerk_user = None
            if clerk_user is None:
                user = None
            else:
                user = await sync_existing_platform_user(session, clerk_user)
                if user is None:
                    user = await provision_platform_user(session, clerk_user)
            if (
                user is not None
                and user.realm == "platform"
                and not clerk_metadata_matches_platform_user(clerk_user, user)
            ):
                await mirror_platform_user(clerk_directory, user)
        elif event_type == "user.deleted":
            clerk_user_id = data.get("id")
            if not isinstance(clerk_user_id, str) or not clerk_user_id:
                raise PlatformInvitationInvalid
            await deactivate_clerk_user(session, clerk_user_id=clerk_user_id)

        receipt.status = WebhookReceiptStatus.PROCESSED.value
        receipt.processed_at = datetime.now(UTC)
        receipt.error = None
        await session.commit()
    except (PlatformInvitationInvalid, PlatformIdentityConflict):
        # User events unrelated to a RingIQ platform invitation are acknowledged.
        receipt.status = WebhookReceiptStatus.PROCESSED.value
        receipt.processed_at = datetime.now(UTC)
        receipt.error = None
        await session.commit()
    except Exception as exc:
        await session.rollback()
        receipt = await session.get(WebhookReceipt, receipt_id)
        if receipt is not None:
            receipt.status = WebhookReceiptStatus.FAILED.value
            receipt.error = type(exc).__name__[:1000]
            await session.commit()
        logger.exception("clerk_webhook.processing_failed delivery_id=%s", delivery_id)
        raise HTTPException(status_code=500, detail="webhook_processing_failed") from exc

    return {"ok": True}

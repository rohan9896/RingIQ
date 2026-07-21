import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Mapping

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.ringiq_api.models.identity import (
    PlatformInvitationStatus,
    PlatformRole,
    PlatformUserInvitation,
    RecordStatus,
    User,
    UserRealm,
)
from apps.api.ringiq_api.services.clerk_directory import (
    ClerkDirectory,
    ClerkDirectoryUnavailable,
    ClerkInvitationConflict,
    ClerkPlatformUser,
)

logger = logging.getLogger("ringiq.api.platform_identity")
INVITATION_DAYS = 30
INVITATION_METADATA_KEY = "ringiq_platform_invitation_id"


class PlatformIdentityConflict(Exception):
    pass


class PlatformInvitationInvalid(Exception):
    pass


class PlatformIdentityUnavailable(Exception):
    pass


def normalize_email(email: str) -> str:
    return email.strip().lower()


def platform_user_from_webhook(data: Mapping[str, Any]) -> ClerkPlatformUser:
    user_id = data.get("id")
    if not isinstance(user_id, str) or not user_id:
        raise PlatformInvitationInvalid
    primary_id = data.get("primary_email_address_id")
    primary: Mapping[str, Any] | None = None
    emails = data.get("email_addresses")
    if isinstance(emails, list):
        for item in emails:
            if isinstance(item, Mapping) and item.get("id") == primary_id:
                primary = item
                break
    verification = primary.get("verification") if primary else None
    verified = isinstance(verification, Mapping) and verification.get("status") == "verified"
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    display_name = " ".join(
        value for value in (first_name, last_name) if isinstance(value, str) and value
    ) or None
    metadata = data.get("public_metadata")
    private_metadata = data.get("private_metadata")
    return ClerkPlatformUser(
        user_id=user_id,
        primary_email=(
            primary.get("email_address")
            if primary and isinstance(primary.get("email_address"), str)
            else None
        ),
        primary_email_verified=verified,
        display_name=display_name,
        public_metadata=metadata if isinstance(metadata, Mapping) else {},
        private_metadata=(
            private_metadata if isinstance(private_metadata, Mapping) else {}
        ),
    )


async def create_platform_invitation(
    session: AsyncSession,
    clerk_directory: ClerkDirectory,
    *,
    email: str,
    display_name: str | None,
    role: PlatformRole,
    invited_by_user_id: uuid.UUID | None,
    redirect_url: str,
) -> PlatformUserInvitation:
    normalized_email = normalize_email(email)
    now = datetime.now(UTC)
    try:
        existing_user = await session.scalar(
            select(User).where(func.lower(User.primary_email) == normalized_email)
        )
        if existing_user is not None:
            raise PlatformIdentityConflict

        open_invitation = await session.scalar(
            select(PlatformUserInvitation).where(
                PlatformUserInvitation.email == normalized_email,
                PlatformUserInvitation.status.in_(
                    [
                        PlatformInvitationStatus.CREATING.value,
                        PlatformInvitationStatus.PENDING.value,
                    ]
                ),
            )
        )
        if open_invitation is not None:
            if open_invitation.expires_at <= now:
                open_invitation.status = PlatformInvitationStatus.EXPIRED.value
                await session.flush()
            else:
                raise PlatformIdentityConflict

        invitation = PlatformUserInvitation(
            email=normalized_email,
            display_name=display_name.strip() if display_name and display_name.strip() else None,
            platform_role=role.value,
            invited_by_user_id=invited_by_user_id,
            expires_at=now + timedelta(days=INVITATION_DAYS),
            status=PlatformInvitationStatus.CREATING.value,
        )
        session.add(invitation)
        await session.commit()
        await session.refresh(invitation)
    except PlatformIdentityConflict:
        await session.rollback()
        raise
    except IntegrityError as exc:
        await session.rollback()
        raise PlatformIdentityConflict from exc
    except SQLAlchemyError as exc:
        await session.rollback()
        raise PlatformIdentityUnavailable from exc

    try:
        clerk_invitation_id = await clerk_directory.create_platform_invitation(
            email=invitation.email,
            invitation_id=str(invitation.id),
            redirect_url=redirect_url,
        )
    except (ClerkInvitationConflict, ClerkDirectoryUnavailable) as exc:
        invitation.status = PlatformInvitationStatus.FAILED.value
        invitation.failure_reason = (
            "clerk_invitation_conflict"
            if isinstance(exc, ClerkInvitationConflict)
            else "clerk_directory_unavailable"
        )
        await session.commit()
        if isinstance(exc, ClerkInvitationConflict):
            raise PlatformIdentityConflict from exc
        raise

    invitation.clerk_invitation_id = clerk_invitation_id
    invitation.status = PlatformInvitationStatus.PENDING.value
    invitation.failure_reason = None
    try:
        await session.commit()
        await session.refresh(invitation)
    except SQLAlchemyError as exc:
        await session.rollback()
        try:
            await clerk_directory.revoke_platform_invitation(
                invitation_id=clerk_invitation_id
            )
        except ClerkDirectoryUnavailable:
            logger.exception(
                "platform_invitation.compensation_failed clerk_invitation_id=%s",
                clerk_invitation_id,
            )
        try:
            stranded = await session.get(PlatformUserInvitation, invitation.id)
            if stranded is not None:
                stranded.clerk_invitation_id = clerk_invitation_id
                stranded.status = PlatformInvitationStatus.FAILED.value
                stranded.failure_reason = "database_persistence_failed"
                await session.commit()
        except SQLAlchemyError:
            await session.rollback()
            logger.exception(
                "platform_invitation.failure_state_persistence_failed invitation_id=%s",
                invitation.id,
            )
        raise PlatformIdentityUnavailable from exc
    return invitation


async def provision_platform_user(
    session: AsyncSession,
    clerk_user: ClerkPlatformUser,
) -> User:
    invitation_id = clerk_user.public_metadata.get(INVITATION_METADATA_KEY)
    try:
        parsed_invitation_id = uuid.UUID(str(invitation_id))
    except (TypeError, ValueError, AttributeError) as exc:
        raise PlatformInvitationInvalid from exc
    if not clerk_user.primary_email or not clerk_user.primary_email_verified:
        raise PlatformInvitationInvalid

    normalized_email = normalize_email(clerk_user.primary_email)
    now = datetime.now(UTC)
    try:
        invitation = await session.scalar(
            select(PlatformUserInvitation)
            .where(PlatformUserInvitation.id == parsed_invitation_id)
            .with_for_update()
        )
        if invitation is None:
            raise PlatformInvitationInvalid

        if invitation.status == PlatformInvitationStatus.ACCEPTED.value:
            accepted = await session.get(User, invitation.accepted_user_id)
            if accepted is None or accepted.clerk_user_id != clerk_user.user_id:
                raise PlatformInvitationInvalid
            accepted.primary_email = clerk_user.primary_email
            accepted.display_name = clerk_user.display_name or invitation.display_name
            await session.commit()
            return accepted

        if invitation.status != PlatformInvitationStatus.PENDING.value:
            raise PlatformInvitationInvalid
        if invitation.expires_at <= now:
            invitation.status = PlatformInvitationStatus.EXPIRED.value
            await session.commit()
            raise PlatformInvitationInvalid
        if invitation.email != normalized_email:
            raise PlatformInvitationInvalid

        user = await session.scalar(
            select(User).where(
                (User.clerk_user_id == clerk_user.user_id)
                | (func.lower(User.primary_email) == normalized_email)
            )
        )
        if user is not None and (
            user.realm != UserRealm.PLATFORM.value
            or user.clerk_user_id != clerk_user.user_id
        ):
            raise PlatformIdentityConflict
        if user is None:
            user = User(
                clerk_user_id=clerk_user.user_id,
                primary_email=clerk_user.primary_email,
                display_name=clerk_user.display_name or invitation.display_name,
                realm=UserRealm.PLATFORM.value,
                platform_role=invitation.platform_role,
                status=RecordStatus.ACTIVE.value,
            )
            session.add(user)
            await session.flush()
        else:
            user.primary_email = clerk_user.primary_email
            user.display_name = clerk_user.display_name or invitation.display_name

        invitation.accepted_user_id = user.id
        invitation.status = PlatformInvitationStatus.ACCEPTED.value
        invitation.failure_reason = None
        await session.commit()
        return user
    except (PlatformInvitationInvalid, PlatformIdentityConflict):
        if session.in_transaction():
            await session.rollback()
        raise
    except IntegrityError as exc:
        await session.rollback()
        raise PlatformIdentityConflict from exc
    except SQLAlchemyError as exc:
        await session.rollback()
        raise PlatformIdentityUnavailable from exc


async def sync_existing_platform_user(
    session: AsyncSession,
    clerk_user: ClerkPlatformUser,
) -> User | None:
    try:
        user = await session.scalar(
            select(User).where(User.clerk_user_id == clerk_user.user_id)
        )
        if user is None:
            return None
        if clerk_user.primary_email and clerk_user.primary_email_verified:
            normalized_email = normalize_email(clerk_user.primary_email)
            email_owner = await session.scalar(
                select(User.id)
                .where(
                    func.lower(User.primary_email) == normalized_email,
                    User.id != user.id,
                )
                .limit(1)
            )
            if email_owner is not None:
                raise PlatformIdentityConflict
            user.primary_email = clerk_user.primary_email
        user.display_name = clerk_user.display_name
        await session.commit()
        return user
    except SQLAlchemyError as exc:
        await session.rollback()
        raise PlatformIdentityUnavailable from exc


async def deactivate_clerk_user(session: AsyncSession, *, clerk_user_id: str) -> None:
    try:
        user = await session.scalar(select(User).where(User.clerk_user_id == clerk_user_id))
        if user is not None:
            user.status = RecordStatus.INACTIVE.value
            await session.commit()
    except SQLAlchemyError as exc:
        await session.rollback()
        raise PlatformIdentityUnavailable from exc


async def mirror_platform_user(
    clerk_directory: ClerkDirectory,
    user: User,
) -> None:
    await clerk_directory.mirror_platform_metadata(
        user_id=user.clerk_user_id,
        metadata=platform_metadata_for_user(user),
    )


def platform_metadata_for_user(user: User) -> dict[str, str | None]:
    return {
        "internal_user_id": str(user.id),
        "realm": UserRealm.PLATFORM.value,
        "platform_role": user.platform_role,
        "status": user.status,
    }


def clerk_metadata_matches_platform_user(
    clerk_user: ClerkPlatformUser,
    user: User,
) -> bool:
    ringiq_metadata = clerk_user.private_metadata.get("ringiq")
    return isinstance(ringiq_metadata, Mapping) and dict(ringiq_metadata) == (
        platform_metadata_for_user(user)
    )

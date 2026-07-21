import argparse
import asyncio
import logging
from datetime import UTC, datetime

from sqlalchemy import func, select, text

from apps.api.ringiq_api.config import get_identity_settings
from apps.api.ringiq_api.db.session import dispose_database, get_session_factory
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
    ClerkUserNotFound,
)
from apps.api.ringiq_api.services.platform_identity import (
    PlatformIdentityConflict,
    create_platform_invitation,
    mirror_platform_user,
    normalize_email,
)

logger = logging.getLogger("ringiq.bootstrap_platform_user")
FIRST_ADMIN_ADVISORY_LOCK_ID = 7_214_001_001


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Provision the first RingIQ platform super administrator."
    )
    parser.add_argument(
        "--clerk-user-id",
        help="Provision an existing dedicated Clerk identity for break-glass recovery.",
    )
    parser.add_argument("--email")
    parser.add_argument("--display-name")
    parser.add_argument(
        "--reconcile-metadata",
        action="store_true",
        help="Mirror all database-owned platform identities into Clerk private metadata.",
    )
    return parser.parse_args()


async def provision_existing_platform_user(args: argparse.Namespace) -> None:
    if not args.clerk_user_id or not args.email:
        raise RuntimeError("--clerk-user-id requires --email")

    normalized_email = normalize_email(args.email)
    directory = ClerkDirectory(get_identity_settings().clerk_secret_key)
    try:
        clerk_user = await directory.get_platform_user(user_id=args.clerk_user_id)
    except ClerkUserNotFound as exc:
        raise RuntimeError("The supplied Clerk user does not exist.") from exc
    except ClerkDirectoryUnavailable as exc:
        raise RuntimeError("Clerk could not verify the supplied recovery user.") from exc
    if (
        not clerk_user.primary_email_verified
        or not clerk_user.primary_email
        or normalize_email(clerk_user.primary_email) != normalized_email
    ):
        raise RuntimeError(
            "The supplied email must be the Clerk user's verified primary email."
        )

    async with get_session_factory()() as session:
        user = (
            await session.execute(
                select(User).where(User.clerk_user_id == args.clerk_user_id)
            )
        ).scalar_one_or_none()

        if user is not None and user.realm != UserRealm.PLATFORM.value:
            raise RuntimeError(
                "This Clerk user is already a tenant identity and cannot become a "
                "platform user. Create a separate Clerk account."
            )

        email_owner = await session.scalar(
            select(User.id)
            .where(
                func.lower(User.primary_email) == normalized_email,
                User.clerk_user_id != args.clerk_user_id,
            )
            .limit(1)
        )
        if email_owner is not None:
            raise RuntimeError(
                "This email already belongs to another RingIQ identity. Use a "
                "separate platform account."
            )

        if user is None:
            user = User(
                clerk_user_id=args.clerk_user_id,
                primary_email=normalized_email,
                display_name=args.display_name or clerk_user.display_name,
                realm=UserRealm.PLATFORM.value,
                platform_role=PlatformRole.SUPER_ADMIN.value,
            )
            session.add(user)
        else:
            user.primary_email = normalized_email
            user.display_name = args.display_name or clerk_user.display_name
            user.status = RecordStatus.ACTIVE.value
            user.platform_role = PlatformRole.SUPER_ADMIN.value

        await session.commit()
        await session.refresh(user)
        try:
            await mirror_platform_user(directory, user)
        except ClerkDirectoryUnavailable:
            logger.exception(
                "break_glass_metadata_mirror_failed clerk_user_id=%s",
                user.clerk_user_id,
            )
            print(
                "Warning: access was provisioned, but Clerk metadata mirroring "
                "failed. Run --reconcile-metadata to retry."
            )
        print(f"Provisioned platform super admin: {args.clerk_user_id}")


async def invite_first_platform_user(args: argparse.Namespace) -> None:
    if not args.email:
        raise RuntimeError("--email is required when creating the first invitation")

    settings = get_identity_settings()
    async with get_session_factory()() as session:
        await session.execute(
            text("SELECT pg_advisory_xact_lock(:lock_id)"),
            {"lock_id": FIRST_ADMIN_ADVISORY_LOCK_ID},
        )
        super_admins = await session.scalar(
            select(func.count())
            .select_from(User)
            .where(
                User.realm == UserRealm.PLATFORM.value,
                User.platform_role == PlatformRole.SUPER_ADMIN.value,
                User.status == RecordStatus.ACTIVE.value,
            )
        )
        if super_admins:
            raise RuntimeError(
                "An active platform super admin already exists. Send subsequent "
                "invitations from /platform/users."
            )
        open_bootstrap_invitation = await session.scalar(
            select(PlatformUserInvitation).where(
                PlatformUserInvitation.platform_role == PlatformRole.SUPER_ADMIN.value,
                PlatformUserInvitation.status.in_(
                    [
                        PlatformInvitationStatus.CREATING.value,
                        PlatformInvitationStatus.PENDING.value,
                    ]
                ),
            )
        )
        if (
            open_bootstrap_invitation is not None
            and open_bootstrap_invitation.expires_at <= datetime.now(UTC)
        ):
            open_bootstrap_invitation.status = PlatformInvitationStatus.EXPIRED.value
            await session.commit()
            open_bootstrap_invitation = None
        if open_bootstrap_invitation is not None:
            raise RuntimeError(
                "A first-super-admin invitation is already open. Revoke or expire "
                "it before creating another."
            )

        try:
            invitation = await create_platform_invitation(
                session,
                ClerkDirectory(settings.clerk_secret_key),
                email=args.email,
                display_name=args.display_name,
                role=PlatformRole.SUPER_ADMIN,
                invited_by_user_id=None,
                redirect_url=settings.platform_invitation_redirect_url,
            )
        except PlatformIdentityConflict as exc:
            raise RuntimeError(
                "This email already has a RingIQ identity or open invitation. "
                "Use a separate platform account."
            ) from exc

        print(f"Invited first platform super admin: {invitation.email}")


async def reconcile_platform_metadata() -> None:
    directory = ClerkDirectory(get_identity_settings().clerk_secret_key)
    async with get_session_factory()() as session:
        users = list(
            (
                await session.scalars(
                    select(User).where(User.realm == UserRealm.PLATFORM.value)
                )
            ).all()
        )

    failures: list[str] = []
    for user in users:
        try:
            await mirror_platform_user(directory, user)
        except ClerkDirectoryUnavailable:
            failures.append(user.clerk_user_id)
            logger.exception(
                "platform_metadata_reconciliation_failed clerk_user_id=%s",
                user.clerk_user_id,
            )

    succeeded = len(users) - len(failures)
    print(f"Reconciled Clerk private metadata for {succeeded} platform user(s).")
    if failures:
        raise RuntimeError(
            "Clerk metadata reconciliation failed for "
            f"{len(failures)} user(s); rerun the command to retry."
        )


async def bootstrap_platform_user(args: argparse.Namespace) -> None:
    if args.reconcile_metadata:
        if args.clerk_user_id or args.email or args.display_name:
            raise RuntimeError(
                "--reconcile-metadata cannot be combined with user provisioning options"
            )
        await reconcile_platform_metadata()
    elif args.clerk_user_id:
        await provision_existing_platform_user(args)
    else:
        await invite_first_platform_user(args)


async def main() -> None:
    try:
        await bootstrap_platform_user(parse_args())
    finally:
        await dispose_database()


if __name__ == "__main__":
    asyncio.run(main())

import argparse
import asyncio

from sqlalchemy import select

from apps.api.ringiq_api.db.session import dispose_database, get_session_factory
from apps.api.ringiq_api.models.identity import PlatformRole, RecordStatus, User, UserRealm


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Provision the first RingIQ platform super administrator."
    )
    parser.add_argument("--clerk-user-id", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--display-name")
    return parser.parse_args()


async def bootstrap_platform_user(args: argparse.Namespace) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
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

        if user is None:
            user = User(
                clerk_user_id=args.clerk_user_id,
                primary_email=args.email,
                display_name=args.display_name,
                realm=UserRealm.PLATFORM.value,
                platform_role=PlatformRole.SUPER_ADMIN.value,
            )
            session.add(user)
        else:
            user.primary_email = args.email
            user.display_name = args.display_name
            user.status = RecordStatus.ACTIVE.value
            user.platform_role = PlatformRole.SUPER_ADMIN.value

        await session.commit()
        print(f"Provisioned platform super admin: {args.clerk_user_id}")


async def main() -> None:
    try:
        await bootstrap_platform_user(parse_args())
    finally:
        await dispose_database()


if __name__ == "__main__":
    asyncio.run(main())

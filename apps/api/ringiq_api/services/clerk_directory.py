import asyncio
from dataclasses import dataclass

from clerk_backend_api import Clerk
from fastapi import Depends

from apps.api.ringiq_api.config import IdentitySettings, get_identity_settings


class ClerkDirectoryUnavailable(Exception):
    pass


class ClerkMembershipNotFound(Exception):
    pass


@dataclass(frozen=True)
class ClerkTenantMembership:
    organization_id: str
    organization_name: str
    organization_slug: str
    user_id: str
    membership_id: str
    role: str
    primary_email: str | None
    display_name: str | None


class ClerkDirectory:
    def __init__(self, secret_key: str) -> None:
        self._secret_key = secret_key

    async def get_tenant_membership(
        self,
        *,
        user_id: str,
        organization_id: str,
    ) -> ClerkTenantMembership:
        try:
            async with Clerk(bearer_auth=self._secret_key) as clerk:
                organization, user, memberships = await asyncio.gather(
                    clerk.organizations.get_async(organization_id=organization_id),
                    clerk.users.get_async(user_id=user_id),
                    clerk.organization_memberships.list_async(
                        organization_id=organization_id,
                        user_id=[user_id],
                        limit=2,
                    ),
                )
        except Exception as exc:
            raise ClerkDirectoryUnavailable from exc

        if len(memberships.data) != 1:
            raise ClerkMembershipNotFound

        membership = memberships.data[0]
        primary_email = next(
            (
                email.email_address
                for email in user.email_addresses
                if email.id == user.primary_email_address_id
            ),
            None,
        )
        display_name = " ".join(
            value for value in (user.first_name, user.last_name) if value
        ) or None
        return ClerkTenantMembership(
            organization_id=organization.id,
            organization_name=organization.name,
            organization_slug=organization.slug,
            user_id=user.id,
            membership_id=membership.id,
            role=membership.role,
            primary_email=primary_email,
            display_name=display_name,
        )


def get_clerk_directory(
    settings: IdentitySettings = Depends(get_identity_settings),
) -> ClerkDirectory:
    return ClerkDirectory(settings.clerk_secret_key)

import asyncio
from dataclasses import dataclass, field
from typing import Any, Mapping

from clerk_backend_api import Clerk
from clerk_backend_api import models as clerk_models
from fastapi import Depends

from apps.api.ringiq_api.config import IdentitySettings, get_identity_settings


class ClerkDirectoryUnavailable(Exception):
    pass


class ClerkMembershipNotFound(Exception):
    pass


class ClerkInvitationConflict(Exception):
    pass


class ClerkUserNotFound(Exception):
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


@dataclass(frozen=True)
class ClerkPlatformUser:
    user_id: str
    primary_email: str | None
    primary_email_verified: bool
    display_name: str | None
    public_metadata: Mapping[str, Any]
    private_metadata: Mapping[str, Any] = field(default_factory=dict)


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

    async def create_platform_invitation(
        self,
        *,
        email: str,
        invitation_id: str,
        redirect_url: str,
    ) -> str:
        try:
            async with Clerk(bearer_auth=self._secret_key) as clerk:
                invitation = await clerk.invitations.create_async(
                    request={
                        "email_address": email,
                        "public_metadata": {
                            "ringiq_platform_invitation_id": invitation_id,
                        },
                        "redirect_url": redirect_url,
                        "notify": True,
                        "ignore_existing": False,
                        "expires_in_days": 30,
                    }
                )
        except clerk_models.ClerkErrors as exc:
            codes = {
                str(getattr(error, "code", "")).lower()
                for error in getattr(getattr(exc, "data", None), "errors", [])
            }
            if any(
                "exist" in code or "duplicate" in code
                for code in codes
            ):
                raise ClerkInvitationConflict from exc
            raise ClerkDirectoryUnavailable from exc
        except Exception as exc:
            raise ClerkDirectoryUnavailable from exc
        return invitation.id

    async def revoke_platform_invitation(self, *, invitation_id: str) -> None:
        try:
            async with Clerk(bearer_auth=self._secret_key) as clerk:
                await clerk.invitations.revoke_async(invitation_id=invitation_id)
        except Exception as exc:
            raise ClerkDirectoryUnavailable from exc

    async def get_platform_user(self, *, user_id: str) -> ClerkPlatformUser:
        try:
            async with Clerk(bearer_auth=self._secret_key) as clerk:
                user = await clerk.users.get_async(user_id=user_id)
        except clerk_models.SDKError as exc:
            response = getattr(exc, "raw_response", None)
            if getattr(response, "status_code", None) == 404:
                raise ClerkUserNotFound from exc
            raise ClerkDirectoryUnavailable from exc
        except Exception as exc:
            raise ClerkDirectoryUnavailable from exc
        return self._platform_user_from_sdk(user)

    async def mirror_platform_metadata(
        self,
        *,
        user_id: str,
        metadata: Mapping[str, Any],
    ) -> None:
        try:
            async with Clerk(bearer_auth=self._secret_key) as clerk:
                await clerk.users.update_metadata_async(
                    user_id=user_id,
                    private_metadata={"ringiq": dict(metadata)},
                )
        except Exception as exc:
            raise ClerkDirectoryUnavailable from exc

    @staticmethod
    def _platform_user_from_sdk(user: Any) -> ClerkPlatformUser:
        primary = next(
            (
                email
                for email in user.email_addresses
                if email.id == user.primary_email_address_id
            ),
            None,
        )
        verification = getattr(primary, "verification", None)
        verification_status = getattr(verification, "status", None)
        if hasattr(verification_status, "value"):
            verification_status = verification_status.value
        display_name = " ".join(
            value for value in (user.first_name, user.last_name) if value
        ) or None
        return ClerkPlatformUser(
            user_id=user.id,
            primary_email=getattr(primary, "email_address", None),
            primary_email_verified=verification_status == "verified",
            display_name=display_name,
            public_metadata=user.public_metadata or {},
            private_metadata=user.private_metadata or {},
        )


def get_clerk_directory(
    settings: IdentitySettings = Depends(get_identity_settings),
) -> ClerkDirectory:
    return ClerkDirectory(settings.clerk_secret_key)

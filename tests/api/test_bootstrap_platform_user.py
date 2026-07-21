import argparse
from unittest.mock import AsyncMock

import pytest

from scripts import bootstrap_platform_user as bootstrap


def args(**overrides) -> argparse.Namespace:
    values = {
        "clerk_user_id": None,
        "email": "admin@ringiq.in",
        "display_name": "RingIQ Admin",
        "reconcile_metadata": False,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


@pytest.mark.asyncio
async def test_default_bootstrap_mode_sends_first_admin_invitation(monkeypatch) -> None:
    invite = AsyncMock()
    monkeypatch.setattr(bootstrap, "invite_first_platform_user", invite)

    await bootstrap.bootstrap_platform_user(args())

    invite.assert_awaited_once()


@pytest.mark.asyncio
async def test_clerk_user_id_selects_break_glass_provisioning(monkeypatch) -> None:
    provision = AsyncMock()
    monkeypatch.setattr(bootstrap, "provision_existing_platform_user", provision)

    await bootstrap.bootstrap_platform_user(args(clerk_user_id="user_admin"))

    provision.assert_awaited_once()


@pytest.mark.asyncio
async def test_reconciliation_cannot_be_combined_with_identity_options() -> None:
    with pytest.raises(RuntimeError, match="cannot be combined"):
        await bootstrap.bootstrap_platform_user(
            args(reconcile_metadata=True, clerk_user_id="user_admin")
        )

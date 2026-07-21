import base64
import json
import uuid
from datetime import UTC, datetime

import pytest
from standardwebhooks.webhooks import Webhook

from apps.api.ringiq_api.routes.webhooks import verify_clerk_webhook
from apps.api.ringiq_api.services.platform_identity import (
    INVITATION_METADATA_KEY,
    PlatformInvitationInvalid,
    normalize_email,
    platform_user_from_webhook,
)


def test_webhook_user_parser_uses_verified_primary_email_and_public_metadata() -> None:
    invitation_id = uuid.uuid4()
    user = platform_user_from_webhook(
        {
            "id": "user_platform",
            "primary_email_address_id": "idn_primary",
            "email_addresses": [
                {
                    "id": "idn_other",
                    "email_address": "other@example.com",
                    "verification": {"status": "verified"},
                },
                {
                    "id": "idn_primary",
                    "email_address": "Admin@Example.com",
                    "verification": {"status": "verified"},
                },
            ],
            "first_name": "RingIQ",
            "last_name": "Admin",
            "public_metadata": {INVITATION_METADATA_KEY: str(invitation_id)},
            "private_metadata": {
                "ringiq": {"platform_role": "platform_super_admin"}
            },
        }
    )

    assert user.user_id == "user_platform"
    assert user.primary_email == "Admin@Example.com"
    assert user.primary_email_verified is True
    assert user.display_name == "RingIQ Admin"
    assert user.public_metadata == {INVITATION_METADATA_KEY: str(invitation_id)}
    assert normalize_email(user.primary_email) == "admin@example.com"


def test_webhook_user_parser_does_not_trust_private_metadata() -> None:
    user = platform_user_from_webhook(
        {
            "id": "user_platform",
            "primary_email_address_id": "idn_primary",
            "email_addresses": [],
            "private_metadata": {
                "ringiq": {"platform_role": "platform_super_admin"}
            },
        }
    )

    assert user.public_metadata == {}
    assert user.primary_email is None
    assert user.primary_email_verified is False


def test_webhook_user_parser_rejects_missing_user_id() -> None:
    with pytest.raises(PlatformInvitationInvalid):
        platform_user_from_webhook({"email_addresses": []})


def test_clerk_webhook_verifier_uses_standard_webhook_headers_and_raw_body() -> None:
    secret = "whsec_" + base64.b64encode(b"ringiq-webhook-secret").decode()
    raw_body = json.dumps({"type": "user.created", "data": {"id": "user_1"}})
    timestamp = datetime.now(UTC)
    signature = Webhook(secret).sign("evt_1", timestamp, raw_body)

    payload = verify_clerk_webhook(
        raw_body.encode(),
        {
            "webhook-id": "evt_1",
            "webhook-timestamp": str(int(timestamp.timestamp())),
            "webhook-signature": signature,
        },
        secret,
    )

    assert payload["type"] == "user.created"


def test_clerk_webhook_verifier_rejects_tampered_body() -> None:
    secret = "whsec_" + base64.b64encode(b"ringiq-webhook-secret").decode()
    timestamp = datetime.now(UTC)
    signature = Webhook(secret).sign("evt_1", timestamp, "{}")

    with pytest.raises(ValueError, match="invalid webhook signature"):
        verify_clerk_webhook(
            b'{"tampered":true}',
            {
                "webhook-id": "evt_1",
                "webhook-timestamp": str(int(timestamp.timestamp())),
                "webhook-signature": signature,
            },
            secret,
        )

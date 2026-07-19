import pytest
from pydantic import ValidationError

from apps.api.ringiq_api.config import AppSettings, VoiceSettings, normalize_database_url
from tests.api.helpers import make_settings


def test_clerk_authorized_parties_are_trimmed_and_empty_values_removed() -> None:
    settings = make_settings(
        clerk_authorized_parties_raw="http://localhost:3000, https://ringiq.example, ",
    )

    assert settings.clerk_authorized_parties == [
        "http://localhost:3000",
        "https://ringiq.example",
    ]


def test_clerk_authorized_parties_cannot_be_empty() -> None:
    with pytest.raises(ValidationError):
        make_settings(clerk_authorized_parties_raw=" , ")


def test_clerk_jwt_key_restores_pem_newlines() -> None:
    settings = make_settings()

    assert "\\n" not in settings.clerk_jwt_public_key
    assert "\n" in settings.clerk_jwt_public_key


def test_voice_settings_do_not_require_identity_configuration() -> None:
    settings = VoiceSettings(
        _env_file=None,
        livekit_url="wss://example.livekit.cloud",
        livekit_api_key="api-key",
        livekit_api_secret="api-secret",
        livekit_sip_outbound_trunk_id="ST_example",
    )

    assert settings.livekit_agent_name == "ringiq-demo-agent"


def test_cors_origins_are_trimmed_and_empty_values_removed() -> None:
    settings = AppSettings(
        _env_file=None,
        cors_allowed_origins_raw="http://localhost:3000, https://ringiq.example, ",
    )

    assert settings.cors_allowed_origins == [
        "http://localhost:3000",
        "https://ringiq.example",
    ]


def test_database_url_normalizes_heroku_scheme_and_requires_ssl() -> None:
    value = normalize_database_url(
        "postgres://ringiq:secret@db.example.com:5432/ringiq",
        environment="staging",
    )

    assert value == (
        "postgresql+asyncpg://ringiq:secret@db.example.com:5432/ringiq"
        "?sslmode=require"
    )


def test_database_url_preserves_local_and_existing_query_options() -> None:
    local = normalize_database_url(
        "postgresql+asyncpg://ringiq:ringiq@127.0.0.1:5432/ringiq",
        environment="local",
    )
    hosted = normalize_database_url(
        "postgresql://ringiq:secret@db.example.com/ringiq?sslmode=verify-full",
        environment="production",
    )

    assert local == "postgresql+asyncpg://ringiq:ringiq@127.0.0.1:5432/ringiq"
    assert hosted.endswith("?sslmode=verify-full")


def test_database_url_rejects_non_postgres_dialects() -> None:
    with pytest.raises(ValueError, match="PostgreSQL"):
        normalize_database_url("sqlite:///ringiq.db", environment="local")

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


def normalize_database_url(value: str, *, environment: str) -> str:
    """Return a SQLAlchemy asyncpg URL suitable for local or hosted Postgres."""
    url = make_url(value)
    if url.drivername in {"postgres", "postgresql"}:
        url = url.set(drivername="postgresql+asyncpg")
    if url.drivername != "postgresql+asyncpg":
        raise ValueError("DATABASE_URL must use PostgreSQL with the asyncpg dialect")
    query = dict(url.query)
    ssl_mode = query.pop("sslmode", None)
    if ssl_mode is not None and "ssl" not in query:
        query["ssl"] = ssl_mode
    if environment.lower() not in {"local", "test"} and "ssl" not in query:
        query["ssl"] = "require"
    url = url.set(query=query)
    return url.render_as_string(hide_password=False)


class AppSettings(BaseSettings):
    app_name: str = "RingIQ API"
    environment: str = "local"
    internal_api_key: str | None = Field(default=None, alias="RINGIQ_INTERNAL_API_KEY")
    cors_allowed_origins_raw: str = Field(
        "http://localhost:3000,http://localhost:3001",
        alias="CORS_ALLOWED_ORIGINS",
    )
    recording_s3_bucket: str | None = Field(
        default=None, alias="LIVEKIT_RECORDING_S3_BUCKET"
    )
    recording_s3_region: str | None = Field(
        default=None, alias="LIVEKIT_RECORDING_S3_REGION"
    )
    recording_s3_access_key: str | None = Field(
        default=None, alias="LIVEKIT_RECORDING_S3_ACCESS_KEY"
    )
    recording_s3_secret: str | None = Field(
        default=None, alias="LIVEKIT_RECORDING_S3_SECRET"
    )
    recording_s3_endpoint: str | None = Field(
        default=None, alias="LIVEKIT_RECORDING_S3_ENDPOINT"
    )
    recording_url_expiry_seconds: int = Field(
        default=900,
        alias="LIVEKIT_RECORDING_URL_EXPIRY_SECONDS",
        ge=60,
        le=3600,
    )
    post_call_outcome_api_key: str | None = Field(
        default=None, alias="POST_CALL_OUTCOME_API_KEY"
    )
    post_call_outcome_base_url: str = Field(
        default="https://api.groq.com/openai/v1", alias="POST_CALL_OUTCOME_BASE_URL"
    )
    post_call_outcome_model: str = Field(
        default="openai/gpt-oss-20b", alias="POST_CALL_OUTCOME_MODEL"
    )
    post_call_outcome_timeout_seconds: float = Field(
        default=30.0, alias="POST_CALL_OUTCOME_TIMEOUT_SECONDS", gt=0, le=120
    )
    post_call_outcome_confidence_threshold: float = Field(
        default=0.6,
        alias="POST_CALL_OUTCOME_CONFIDENCE_THRESHOLD",
        ge=0,
        le=1,
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    @property
    def cors_allowed_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_allowed_origins_raw.split(",")
            if origin.strip()
        ]


class VoiceSettings(AppSettings):
    livekit_url: str = Field(..., alias="LIVEKIT_URL")
    livekit_api_key: str = Field(..., alias="LIVEKIT_API_KEY")
    livekit_api_secret: str = Field(..., alias="LIVEKIT_API_SECRET")
    livekit_sip_outbound_trunk_id: str = Field(..., alias="LIVEKIT_SIP_OUTBOUND_TRUNK_ID")
    livekit_agent_name: str = Field("ringiq-demo-agent", alias="LIVEKIT_AGENT_NAME")
    livekit_wait_until_answered: bool = Field(False, alias="LIVEKIT_WAIT_UNTIL_ANSWERED")
    livekit_sip_participant_identity: str = Field("phone_user", alias="LIVEKIT_SIP_PARTICIPANT_IDENTITY")
    livekit_sip_participant_name: str = Field("Demo Lead", alias="LIVEKIT_SIP_PARTICIPANT_NAME")
    livekit_call_timeout_seconds: Optional[float] = Field(30.0, alias="LIVEKIT_CALL_TIMEOUT_SECONDS")
    livekit_agent_ready_timeout_seconds: float = Field(
        45.0,
        alias="LIVEKIT_AGENT_READY_TIMEOUT_SECONDS",
        gt=0,
    )

class IdentitySettings(AppSettings):
    database_url: str = Field(..., alias="DATABASE_URL")

    clerk_secret_key: str = Field(..., alias="CLERK_SECRET_KEY")
    clerk_jwt_key: str = Field(..., alias="CLERK_JWT_KEY")
    clerk_authorized_parties_raw: str = Field(..., alias="CLERK_AUTHORIZED_PARTIES")

    @model_validator(mode="after")
    def validate_clerk_settings(self) -> "IdentitySettings":
        if not self.clerk_authorized_parties:
            raise ValueError("CLERK_AUTHORIZED_PARTIES must include at least one origin")
        self.database_url = normalize_database_url(
            self.database_url,
            environment=self.environment,
        )
        return self

    @property
    def clerk_authorized_parties(self) -> list[str]:
        return [
            party.strip()
            for party in self.clerk_authorized_parties_raw.split(",")
            if party.strip()
        ]

    @property
    def clerk_jwt_public_key(self) -> str:
        return self.clerk_jwt_key.replace("\\n", "\n")


class Settings(VoiceSettings, IdentitySettings):
    """Combined settings retained for callers that need both service groups."""


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_app_settings() -> AppSettings:
    return AppSettings()


@lru_cache
def get_voice_settings() -> VoiceSettings:
    return VoiceSettings()


@lru_cache
def get_identity_settings() -> IdentitySettings:
    return IdentitySettings()

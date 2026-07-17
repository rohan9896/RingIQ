from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    app_name: str = "RingIQ API"
    environment: str = "local"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


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

class IdentitySettings(AppSettings):
    database_url: str = Field(..., alias="DATABASE_URL")

    clerk_secret_key: str = Field(..., alias="CLERK_SECRET_KEY")
    clerk_jwt_key: str = Field(..., alias="CLERK_JWT_KEY")
    clerk_authorized_parties_raw: str = Field(..., alias="CLERK_AUTHORIZED_PARTIES")

    @model_validator(mode="after")
    def validate_clerk_settings(self) -> "IdentitySettings":
        if not self.clerk_authorized_parties:
            raise ValueError("CLERK_AUTHORIZED_PARTIES must include at least one origin")
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
def get_voice_settings() -> VoiceSettings:
    return VoiceSettings()


@lru_cache
def get_identity_settings() -> IdentitySettings:
    return IdentitySettings()

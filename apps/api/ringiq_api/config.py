from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "RingIQ API"
    environment: str = "local"

    livekit_url: str = Field(..., alias="LIVEKIT_URL")
    livekit_api_key: str = Field(..., alias="LIVEKIT_API_KEY")
    livekit_api_secret: str = Field(..., alias="LIVEKIT_API_SECRET")
    livekit_sip_outbound_trunk_id: str = Field(..., alias="LIVEKIT_SIP_OUTBOUND_TRUNK_ID")
    livekit_agent_name: str = Field("ringiq-demo-agent", alias="LIVEKIT_AGENT_NAME")
    livekit_wait_until_answered: bool = Field(False, alias="LIVEKIT_WAIT_UNTIL_ANSWERED")
    livekit_sip_participant_identity: str = Field("phone_user", alias="LIVEKIT_SIP_PARTICIPANT_IDENTITY")
    livekit_sip_participant_name: str = Field("Demo Lead", alias="LIVEKIT_SIP_PARTICIPANT_NAME")
    livekit_call_timeout_seconds: Optional[float] = Field(30.0, alias="LIVEKIT_CALL_TIMEOUT_SECONDS")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


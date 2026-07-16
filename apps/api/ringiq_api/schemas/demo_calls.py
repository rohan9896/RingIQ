import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator

E164_PHONE_NUMBER = re.compile(r"^\+[1-9]\d{7,14}$")


class DemoCallRequest(BaseModel):
    phone_number: str = Field(
        ...,
        description="Phone number to call in E.164 format, for example +919876543210.",
        examples=["+919876543210"],
    )
    room_name: Optional[str] = Field(
        default=None,
        description="Optional LiveKit room name. If omitted, RingIQ creates a demo room name.",
    )
    metadata: dict[str, str] = Field(
        default_factory=dict,
        description="Optional metadata to pass to the dispatched LiveKit agent.",
    )

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str) -> str:
        if not E164_PHONE_NUMBER.match(value):
            raise ValueError("phone_number must be in E.164 format, for example +919876543210")
        return value


class DemoCallResponse(BaseModel):
    call_id: str
    room_name: str
    phone_number: str
    agent_name: str
    sip_participant_identity: str
    status: str
    livekit_sip_call_id: Optional[str] = None
    message: str


class PipelineEventRequest(BaseModel):
    call_id: str = Field(default="unknown")
    room_name: str = Field(default="unknown")
    stage: str
    provider: Optional[str] = None
    status: str = Field(default="info")
    message: str
    metadata: dict[str, str] = Field(default_factory=dict)

import json
import logging
import uuid
from typing import Any, Optional

from livekit import api

from apps.api.ringiq_api.config import Settings
from apps.api.ringiq_api.schemas.demo_calls import DemoCallRequest, DemoCallResponse

logger = logging.getLogger("ringiq.api.livekit_calls")


class LiveKitCallServiceError(RuntimeError):
    """Raised when the demo call could not be started."""


class LiveKitCallService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def create_demo_call(self, request: DemoCallRequest) -> DemoCallResponse:
        call_id = uuid.uuid4().hex
        room_name = request.room_name or f"ringiq-demo-{call_id[:10]}"
        participant_identity = f"{self._settings.livekit_sip_participant_identity}-{call_id[:8]}"
        metadata = {
            "call_id": call_id,
            "phone_number": request.phone_number,
            "sip_participant_identity": participant_identity,
            "demo": "true",
            **request.metadata,
        }

        lkapi = api.LiveKitAPI(
            url=self._settings.livekit_url,
            api_key=self._settings.livekit_api_key,
            api_secret=self._settings.livekit_api_secret,
        )

        try:
            logger.info(
                "livekit.agent_dispatch.start call_id=%s room=%s agent=%s",
                call_id,
                room_name,
                self._settings.livekit_agent_name,
            )
            await self._dispatch_agent(lkapi, room_name, metadata)
            logger.info(
                "livekit.agent_dispatch.done call_id=%s room=%s agent=%s",
                call_id,
                room_name,
                self._settings.livekit_agent_name,
            )
            logger.info(
                "livekit.sip_participant.start call_id=%s room=%s trunk_id=%s participant_identity=%s",
                call_id,
                room_name,
                self._settings.livekit_sip_outbound_trunk_id,
                participant_identity,
            )
            sip_participant = await self._create_sip_participant(
                lkapi,
                room_name=room_name,
                phone_number=request.phone_number,
                participant_identity=participant_identity,
            )
            logger.info(
                "livekit.sip_participant.done call_id=%s room=%s participant_identity=%s sip_call_id=%s",
                call_id,
                room_name,
                participant_identity,
                self._read_sip_call_id(sip_participant),
            )
        except LiveKitCallServiceError:
            raise
        except Exception as exc:
            raise LiveKitCallServiceError(f"Failed to start demo call: {exc}") from exc
        finally:
            await lkapi.aclose()

        return DemoCallResponse(
            call_id=call_id,
            room_name=room_name,
            phone_number=request.phone_number,
            agent_name=self._settings.livekit_agent_name,
            sip_participant_identity=participant_identity,
            status="call_started",
            livekit_sip_call_id=self._read_sip_call_id(sip_participant),
            message="Demo outbound call requested. The voice worker must be running to handle the conversation.",
        )

    async def _dispatch_agent(
        self,
        lkapi: api.LiveKitAPI,
        room_name: str,
        metadata: dict[str, str],
    ) -> None:
        try:
            await lkapi.agent_dispatch.create_dispatch(
                api.CreateAgentDispatchRequest(
                    agent_name=self._settings.livekit_agent_name,
                    room=room_name,
                    metadata=json.dumps(metadata),
                )
            )
        except api.TwirpError as exc:
            raise LiveKitCallServiceError(
                self._format_twirp_error(
                    exc,
                    stage="agent dispatch",
                    detail=f"agent_name={self._settings.livekit_agent_name}",
                )
            ) from exc

    async def _create_sip_participant(
        self,
        lkapi: api.LiveKitAPI,
        *,
        room_name: str,
        phone_number: str,
        participant_identity: str,
    ) -> Any:
        try:
            return await lkapi.sip.create_sip_participant(
                api.CreateSIPParticipantRequest(
                    room_name=room_name,
                    sip_trunk_id=self._settings.livekit_sip_outbound_trunk_id,
                    sip_call_to=phone_number,
                    participant_identity=participant_identity,
                    participant_name=self._settings.livekit_sip_participant_name,
                    wait_until_answered=self._settings.livekit_wait_until_answered,
                ),
                timeout=self._settings.livekit_call_timeout_seconds,
            )
        except api.TwirpError as exc:
            raise LiveKitCallServiceError(
                self._format_twirp_error(
                    exc,
                    stage="SIP outbound participant",
                    detail=f"trunk_id={self._settings.livekit_sip_outbound_trunk_id}",
                )
            ) from exc

    @staticmethod
    def _format_twirp_error(exc: api.TwirpError, *, stage: str, detail: str) -> str:
        sip_status_code = exc.metadata.get("sip_status_code") if exc.metadata else None
        sip_status = exc.metadata.get("sip_status") if exc.metadata else None
        details = [f"LiveKit {stage} failed: {exc.message}", detail]
        if sip_status_code:
            details.append(f"SIP status code: {sip_status_code}")
        if sip_status:
            details.append(f"SIP status: {sip_status}")
        return "; ".join(details)

    @staticmethod
    def _read_sip_call_id(sip_participant: Any) -> Optional[str]:
        attributes = getattr(sip_participant, "attributes", None)
        if isinstance(attributes, dict):
            return attributes.get("sip.callID")
        return None

import asyncio
import json
import logging
import time
import uuid
from typing import Any, Optional

from livekit import api

from apps.api.ringiq_api.config import VoiceSettings
from apps.api.ringiq_api.schemas.demo_calls import DemoCallRequest, DemoCallResponse

logger = logging.getLogger("ringiq.api.livekit_calls")
AGENT_READY_ATTRIBUTE = "ringiq.agent_ready"
READINESS_PROBE_TIMEOUT_SECONDS = 2.0


class LiveKitCallServiceError(RuntimeError):
    """Raised when the demo call could not be started."""


class LiveKitCallService:
    def __init__(self, settings: VoiceSettings) -> None:
        self._settings = settings

    async def create_demo_call(self, request: DemoCallRequest) -> DemoCallResponse:
        requested_call_id = request.metadata.get("call_id", "").strip()
        call_id = requested_call_id or uuid.uuid4().hex
        room_name = request.room_name or f"ringiq-demo-{call_id[:10]}"
        participant_identity = f"{self._settings.livekit_sip_participant_identity}-{call_id[:8]}"
        metadata = {
            **request.metadata,
            "call_id": call_id,
            "phone_number": request.phone_number,
            "sip_participant_identity": participant_identity,
            "demo": request.metadata.get("demo", "true"),
        }

        lkapi = api.LiveKitAPI(
            url=self._settings.livekit_url,
            api_key=self._settings.livekit_api_key,
            api_secret=self._settings.livekit_api_secret,
        )
        dispatch_created = False

        try:
            logger.info(
                "livekit.agent_dispatch.start call_id=%s room=%s agent=%s",
                call_id,
                room_name,
                self._settings.livekit_agent_name,
            )
            await self._dispatch_agent(lkapi, room_name, metadata)
            dispatch_created = True
            logger.info(
                "livekit.agent_dispatch.done call_id=%s room=%s agent=%s",
                call_id,
                room_name,
                self._settings.livekit_agent_name,
            )
            await self._wait_for_agent_ready(lkapi, room_name=room_name, call_id=call_id)
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
            if dispatch_created:
                await self._delete_room_best_effort(lkapi, room_name=room_name)
            raise
        except Exception as exc:
            if dispatch_created:
                await self._delete_room_best_effort(lkapi, room_name=room_name)
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

    async def create_campaign_call(
        self,
        *,
        phone_number: str,
        room_name: str,
        metadata: dict[str, str],
    ) -> DemoCallResponse:
        return await self.create_demo_call(
            DemoCallRequest(
                phone_number=phone_number,
                room_name=room_name,
                metadata={"demo": "false", **metadata},
            )
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

    async def _wait_for_agent_ready(
        self,
        lkapi: api.LiveKitAPI,
        *,
        room_name: str,
        call_id: str,
    ) -> None:
        timeout = self._settings.livekit_agent_ready_timeout_seconds
        deadline = time.monotonic() + timeout
        last_observation = "no participant response received"
        probe_timeouts = 0
        logger.info(
            "livekit.agent_ready.wait call_id=%s room=%s timeout_seconds=%s",
            call_id,
            room_name,
            timeout,
        )

        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                dispatch_diagnostics = await self._agent_dispatch_diagnostics(
                    lkapi,
                    room_name=room_name,
                )
                raise LiveKitCallServiceError(
                    "LiveKit voice agent did not become ready within "
                    f"{timeout:g} seconds; room={room_name}; "
                    f"last_observation={last_observation}; "
                    f"readiness_probe_timeouts={probe_timeouts}; "
                    f"dispatch={dispatch_diagnostics}; "
                    "the outbound phone call was not placed"
                )

            try:
                response = await asyncio.wait_for(
                    lkapi.room.list_participants(
                        api.ListParticipantsRequest(room=room_name)
                    ),
                    timeout=min(READINESS_PROBE_TIMEOUT_SECONDS, remaining),
                )
                ready_participant = next(
                    (
                        participant
                        for participant in response.participants
                        if participant.attributes.get(AGENT_READY_ATTRIBUTE) == call_id
                    ),
                    None,
                )
                if ready_participant is not None:
                    logger.info(
                        "livekit.agent_ready.done call_id=%s room=%s participant=%s",
                        call_id,
                        room_name,
                        ready_participant.identity,
                    )
                    return
                observed = [
                    {
                        "identity": participant.identity,
                        "ready_call_id": participant.attributes.get(AGENT_READY_ATTRIBUTE),
                    }
                    for participant in response.participants
                ]
                last_observation = f"participants={observed}"
            except asyncio.TimeoutError:
                probe_timeouts += 1
                last_observation = "participant readiness probe timed out"
                logger.warning(
                    "livekit.agent_ready.poll_timeout call_id=%s room=%s probe_timeout_seconds=%s",
                    call_id,
                    room_name,
                    min(READINESS_PROBE_TIMEOUT_SECONDS, remaining),
                )
                continue
            except api.TwirpError as exc:
                # The room may not be visible for a moment immediately after dispatch.
                last_observation = f"LiveKit participant API error: {exc.message}"
                logger.debug(
                    "livekit.agent_ready.poll_pending call_id=%s room=%s error=%s",
                    call_id,
                    room_name,
                    exc.message,
                )

            await asyncio.sleep(min(0.2, max(0.0, deadline - time.monotonic())))

    async def _agent_dispatch_diagnostics(
        self,
        lkapi: api.LiveKitAPI,
        *,
        room_name: str,
    ) -> str:
        try:
            dispatches = await asyncio.wait_for(
                lkapi.agent_dispatch.list_dispatch(room_name),
                timeout=READINESS_PROBE_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            return "dispatch lookup timed out"
        except api.TwirpError as exc:
            return f"dispatch lookup failed: {exc.message}"
        except Exception as exc:
            return f"dispatch lookup failed: {type(exc).__name__}: {exc}"

        if not dispatches:
            return "no dispatch found"

        details: list[str] = []
        for dispatch in dispatches:
            jobs = getattr(dispatch.state, "jobs", ())
            if not jobs:
                details.append(f"dispatch_id={dispatch.id}, jobs=[]")
                continue
            for job in jobs:
                details.append(
                    "dispatch_id={dispatch_id}, job_id={job_id}, status={status}, "
                    "worker_id={worker_id}, participant_identity={participant_identity}, "
                    "error={error}".format(
                        dispatch_id=dispatch.id,
                        job_id=job.id,
                        status=job.state.status,
                        worker_id=job.state.worker_id or "none",
                        participant_identity=job.state.participant_identity or "none",
                        error=job.state.error or "none",
                    )
                )
        return " | ".join(details)

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

    async def _delete_room_best_effort(
        self,
        lkapi: api.LiveKitAPI,
        *,
        room_name: str,
    ) -> None:
        try:
            await asyncio.wait_for(
                lkapi.room.delete_room(api.DeleteRoomRequest(room=room_name)),
                timeout=READINESS_PROBE_TIMEOUT_SECONDS,
            )
            logger.info("livekit.room.cleanup.done room=%s", room_name)
        except Exception as exc:
            logger.warning(
                "livekit.room.cleanup.failed room=%s error=%s",
                room_name,
                exc,
            )

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

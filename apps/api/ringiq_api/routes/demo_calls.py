import logging

from fastapi import APIRouter, Depends, HTTPException, status

from apps.api.ringiq_api.config import Settings, get_settings
from apps.api.ringiq_api.schemas.demo_calls import DemoCallRequest, DemoCallResponse, PipelineEventRequest
from apps.api.ringiq_api.services.livekit_calls import LiveKitCallService, LiveKitCallServiceError

router = APIRouter(prefix="/demo", tags=["demo"])
logger = logging.getLogger("ringiq.api.demo")


@router.post("/calls", response_model=DemoCallResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_demo_call(
    request: DemoCallRequest,
    settings: Settings = Depends(get_settings),
) -> DemoCallResponse:
    logger.info("demo_call.requested phone_number=%s", request.phone_number)
    service = LiveKitCallService(settings)
    try:
        response = await service.create_demo_call(request)
        logger.info(
            "demo_call.accepted call_id=%s room=%s agent=%s sip_identity=%s",
            response.call_id,
            response.room_name,
            response.agent_name,
            response.sip_participant_identity,
        )
        return response
    except LiveKitCallServiceError as exc:
        logger.exception("demo_call.failed reason=%s", exc)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.post("/pipeline-events", status_code=status.HTTP_202_ACCEPTED)
async def log_pipeline_event(event: PipelineEventRequest) -> dict[str, str]:
    logger.info(
        "voice_pipeline.%s call_id=%s room=%s provider=%s status=%s message=%s metadata=%s",
        event.stage,
        event.call_id,
        event.room_name,
        event.provider or "internal",
        event.status,
        event.message,
        event.metadata,
    )
    return {"status": "logged"}

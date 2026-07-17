import pytest
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from apps.api.ringiq_api.db import session as session_module


@pytest.mark.asyncio
async def test_session_construction_failure_is_service_unavailable(monkeypatch) -> None:
    def fail_to_build_session_factory() -> None:
        raise SQLAlchemyError("database unavailable")

    monkeypatch.setattr(
        session_module,
        "get_session_factory",
        fail_to_build_session_factory,
    )

    with pytest.raises(HTTPException) as exc_info:
        await anext(session_module.get_db_session())

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "identity_store_unavailable"

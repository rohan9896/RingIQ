from collections.abc import AsyncIterator
from functools import lru_cache
import logging

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from apps.api.ringiq_api.config import get_identity_settings

logger = logging.getLogger("ringiq.api.database")


@lru_cache
def get_engine() -> AsyncEngine:
    settings = get_identity_settings()
    return create_async_engine(settings.database_url, pool_pre_ping=True)


@lru_cache
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_engine(), expire_on_commit=False)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    try:
        session_factory = get_session_factory()
        async with session_factory() as session:
            yield session
    except SQLAlchemyError as exc:
        logger.exception("database.session_unavailable")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="identity_store_unavailable",
        ) from exc


async def dispose_database() -> None:
    if get_engine.cache_info().currsize:
        await get_engine().dispose()
    get_session_factory.cache_clear()
    get_engine.cache_clear()

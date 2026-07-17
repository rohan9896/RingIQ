import os

from dotenv import load_dotenv
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from apps.api.ringiq_api import models  # noqa: F401
from apps.api.ringiq_api.db.base import Base

load_dotenv()


def get_test_database_url() -> str:
    configured_url = os.environ.get("TEST_DATABASE_URL")
    if configured_url:
        return configured_url

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("TEST_DATABASE_URL or DATABASE_URL is required for API tests")

    base_url, separator, _ = database_url.rpartition("/")
    if not separator:
        raise RuntimeError("DATABASE_URL must include a database name")
    return f"{base_url}/ringiq_test"


def create_test_engine() -> AsyncEngine:
    database_url = get_test_database_url()
    if not database_url.startswith("postgresql+asyncpg://"):
        raise RuntimeError("TEST_DATABASE_URL must use the postgresql+asyncpg dialect")
    return create_async_engine(database_url, pool_pre_ping=True, poolclass=NullPool)


async def reset_database(engine: AsyncEngine) -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

import asyncio

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text

from tests.api.postgres import create_test_engine, get_test_database_url


async def reset_migration_database() -> None:
    engine = create_test_engine()
    try:
        async with engine.begin() as connection:
            await connection.execute(text("DROP SCHEMA public CASCADE"))
            await connection.execute(text("CREATE SCHEMA public"))
    finally:
        await engine.dispose()


async def inspect_migration_database() -> tuple[set[str], set[str], set[str]]:
    engine = create_test_engine()
    try:
        async with engine.connect() as connection:
            return await connection.run_sync(
                lambda sync_connection: (
                    set(inspect(sync_connection).get_table_names()),
                    {
                        column["name"]
                        for column in inspect(sync_connection).get_columns("users")
                    },
                    {
                        column["name"]
                        for column in inspect(sync_connection).get_columns("call_attempts")
                    },
                )
            )
    finally:
        await engine.dispose()


async def get_migration_tables() -> set[str]:
    engine = create_test_engine()
    try:
        async with engine.connect() as connection:
            return await connection.run_sync(
                lambda sync_connection: set(inspect(sync_connection).get_table_names())
            )
    finally:
        await engine.dispose()


def test_identity_migration_upgrade_and_downgrade(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", get_test_database_url())
    config = Config("alembic.ini")

    asyncio.run(reset_migration_database())
    command.upgrade(config, "head")

    tables, user_columns, call_attempt_columns = asyncio.run(inspect_migration_database())
    assert {
        "tenants",
        "users",
        "tenant_memberships",
        "categories",
        "category_template_versions",
        "qna_questions",
        "tenant_knowledge_bases",
        "tenant_knowledge_base_versions",
        "tenant_knowledge_questions",
        "leads",
        "lead_imports",
        "lead_import_rows",
    }.issubset(tables)
    assert {"realm", "platform_role"}.issubset(user_columns)
    assert {
        "transcript_json",
        "recording_egress_id",
        "recording_status",
        "recording_storage_uri",
        "recording_url",
    }.issubset(call_attempt_columns)

    command.downgrade(config, "base")

    assert "tenant_memberships" not in asyncio.run(get_migration_tables())

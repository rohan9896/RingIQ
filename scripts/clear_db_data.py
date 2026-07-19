import argparse
import asyncio
import sys
from pathlib import Path
from typing import Sequence

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from apps.api.ringiq_api.db.base import Base  # noqa: E402
import apps.api.ringiq_api.models  # noqa: E402,F401


class ClearDatabaseSettings(BaseSettings):
    database_url: str = Field(..., alias="DATABASE_URL")
    environment: str = "local"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Clear all RingIQ application data from the configured database. "
            "Alembic migration history is left intact."
        )
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip the interactive confirmation prompt.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the tables that would be truncated without changing data.",
    )
    parser.add_argument(
        "--allow-non-local",
        action="store_true",
        help="Allow clearing data when ENVIRONMENT is not local/test/development.",
    )
    return parser.parse_args()


def application_table_names() -> list[str]:
    return sorted(table.name for table in Base.metadata.sorted_tables)


def quote_table_names(dialect, table_names: Sequence[str]) -> str:
    preparer = dialect.identifier_preparer
    return ", ".join(preparer.quote(table_name) for table_name in table_names)


def confirm_clear(table_names: Sequence[str], environment: str) -> None:
    print("This will delete all RingIQ application data.")
    print(f"Environment: {environment}")
    print("Tables:")
    for table_name in table_names:
        print(f"  - {table_name}")

    answer = input("Type 'clear all data' to continue: ")
    if answer != "clear all data":
        raise SystemExit("Aborted.")


async def clear_database(args: argparse.Namespace) -> None:
    table_names = application_table_names()
    if not table_names:
        raise SystemExit("No application tables were found in SQLAlchemy metadata.")

    if args.dry_run:
        print("Would truncate these application tables:")
        for table_name in table_names:
            print(f"  - {table_name}")
        return

    settings = ClearDatabaseSettings()
    environment = settings.environment.lower()
    local_environments = {"local", "test", "testing", "development", "dev"}

    if environment not in local_environments and not args.allow_non_local:
        raise SystemExit(
            "Refusing to clear a non-local database. Re-run with "
            "--allow-non-local if this is intentional."
        )

    if not args.yes:
        confirm_clear(table_names, settings.environment)

    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    try:
        quoted_table_names = quote_table_names(engine.sync_engine.dialect, table_names)
        statement = text(f"TRUNCATE TABLE {quoted_table_names} RESTART IDENTITY CASCADE")
        async with engine.begin() as connection:
            await connection.execute(statement)
    finally:
        await engine.dispose()

    print(f"Cleared data from {len(table_names)} application tables.")


async def main() -> None:
    await clear_database(parse_args())


if __name__ == "__main__":
    asyncio.run(main())

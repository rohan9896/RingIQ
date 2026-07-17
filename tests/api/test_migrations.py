import sqlite3

from alembic import command
from alembic.config import Config


def test_identity_migration_upgrade_and_downgrade(
    tmp_path,
    monkeypatch,
) -> None:
    database_path = tmp_path / "migration.sqlite3"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{database_path}")
    config = Config("alembic.ini")

    command.upgrade(config, "head")

    with sqlite3.connect(database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
    assert {"tenants", "users", "tenant_memberships"}.issubset(tables)

    command.downgrade(config, "base")

    with sqlite3.connect(database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
    assert "tenant_memberships" not in tables

"""A failed schema upgrade must never be hidden behind create_all()."""

import pytest
from alembic import command

from app.core import database


@pytest.mark.parametrize("environment", ["dev", "staging", "production"])
def test_startup_rejects_migration_error_without_creating_fallback_tables(
    monkeypatch, environment,
):
    """Existing SQLite/MySQL tables cannot be repaired by create_all."""
    monkeypatch.setattr(database.settings, "app_env", environment)
    calls = []

    def failed_upgrade(*_args, **_kwargs):
        calls.append("upgrade")
        raise RuntimeError("evaluations contains multiple rows for homework_id=3")

    def unsafe_create_all(*_args, **_kwargs):
        calls.append("create_all")
        raise AssertionError("must not silently skip failed schema migrations")

    monkeypatch.setattr(command, "upgrade", failed_upgrade)
    monkeypatch.setattr(database.Base.metadata, "create_all", unsafe_create_all)
    with pytest.raises(RuntimeError, match="数据库迁移失败") as error:
        database.init_db()
    assert "homework_id=3" in str(error.value)
    assert calls == ["upgrade"]


def test_startup_uses_alembic_as_single_schema_authority(monkeypatch):
    events = []

    def successful_upgrade(_cfg, revision):
        events.append(("upgrade", revision))

    monkeypatch.setattr(command, "upgrade", successful_upgrade)
    monkeypatch.setattr(
        database.Base.metadata, "create_all",
        lambda *_args, **_kwargs: events.append(("create_all",)),
    )
    database.init_db()
    assert events == [("upgrade", "head")]

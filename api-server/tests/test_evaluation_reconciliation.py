"""Offline migration safety contracts (including pre-attempt legacy schemas)."""

from datetime import datetime

import pytest
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, MetaData, String, Table, create_engine, inspect, select

from app.services.evaluation_reconciliation import (
    ARCHIVE_TABLE, audit_duplicates, reconcile_duplicates,
)


@pytest.fixture
def legacy_database():
    engine = create_engine("sqlite:///:memory:")
    metadata = MetaData()
    evaluations = Table(
        "evaluations", metadata,
        Column("id", Integer, primary_key=True),
        Column("homework_id", Integer, nullable=False),
        Column("status", String(20), nullable=False),
        Column("total_score", Float, nullable=False),
        Column("issues_json", JSON),
        Column("created_at", DateTime),
        Column("updated_at", DateTime),
    )
    metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(evaluations.insert(), [
            {
                "id": 1, "homework_id": 10, "status": "finished",
                "total_score": 8.25, "issues_json": ["old issue"],
                "created_at": datetime(2026, 1, 1),
                "updated_at": datetime(2026, 1, 2),
            },
            {
                "id": 2, "homework_id": 10, "status": "finished",
                "total_score": 9.5, "issues_json": ["new issue"],
                "created_at": datetime(2026, 2, 1),
                "updated_at": datetime(2026, 2, 2),
            },
            {
                "id": 3, "homework_id": 11, "status": "finished",
                "total_score": 6.0, "issues_json": ["other"],
                "created_at": datetime(2026, 2, 1),
                "updated_at": datetime(2026, 2, 2),
            },
        ])
    return engine, evaluations


def _ids(engine, table):
    with engine.connect() as connection:
        return connection.execute(select(table.c.id).order_by(table.c.id)).scalars().all()


def test_audit_does_not_mutate_old_schema_or_guess_winner(legacy_database):
    engine, table = legacy_database
    plan = audit_duplicates(engine)
    assert all(
        len(row["fingerprint"]) == 64 for row in plan["groups"][0]["candidates"]
    )
    summarized = [{
        **group,
        "candidates": [
            {k: v for k, v in candidate.items() if k != "fingerprint"}
            for candidate in group["candidates"]
        ],
    } for group in plan["groups"]]
    assert summarized == [{
        "homework_id": 10,
        "ids": [1, 2],
        "keep_id": None,
        "candidates": [
            {
                "id": 1, "status": "finished", "total_score": 8.25,
                "updated_at": "2026-01-02T00:00:00",
            },
            {
                "id": 2, "status": "finished", "total_score": 9.5,
                "updated_at": "2026-02-02T00:00:00",
            },
        ],
    }]
    assert _ids(engine, table) == [1, 2, 3]
    assert ARCHIVE_TABLE not in inspect(engine).get_table_names()


def test_explicit_keeper_archives_every_other_column_before_deletion(legacy_database):
    engine, table = legacy_database
    plan = audit_duplicates(engine)
    plan["groups"][0]["keep_id"] = 1  # An explicit human decision, not a metric rule.
    assert reconcile_duplicates(engine, plan) == {"archived": 1, "kept": 1}
    assert _ids(engine, table) == [1, 3]
    with engine.connect() as connection:
        archive = Table(ARCHIVE_TABLE, MetaData(), autoload_with=engine)
        saved = connection.execute(select(archive)).mappings().one()
        assert saved["evaluation_id"] == 2
        assert saved["kept_evaluation_id"] == 1
        assert saved["snapshot_json"]["issues_json"] == ["new issue"]
        assert saved["snapshot_json"]["total_score"] == 9.5
        assert saved["snapshot_json"]["created_at"] == "2026-02-01T00:00:00"
    assert audit_duplicates(engine)["groups"] == []


def test_missing_or_stale_keeper_plan_never_deletes_records(legacy_database):
    engine, table = legacy_database
    plan = audit_duplicates(engine)
    with pytest.raises(ValueError, match="choose an existing keep_id"):
        reconcile_duplicates(engine, plan)
    plan["groups"][0]["keep_id"] = 999
    with pytest.raises(ValueError, match="choose an existing keep_id"):
        reconcile_duplicates(engine, plan)
    plan["groups"][0]["keep_id"] = 1
    plan["groups"][0]["ids"].append(999)
    with pytest.raises(ValueError, match="duplicate IDs changed"):
        reconcile_duplicates(engine, plan)
    assert _ids(engine, table) == [1, 2, 3]
    assert ARCHIVE_TABLE not in inspect(engine).get_table_names()


def test_conflicting_archive_insert_rolls_back_all_live_changes(legacy_database):
    engine, table = legacy_database
    plan = audit_duplicates(engine)
    plan["groups"][0]["keep_id"] = 1
    # Make an incompatible pre-existing archived entry for the same legacy id.
    from app.services.evaluation_reconciliation import _archive_definition
    archive = _archive_definition(MetaData())
    archive.create(engine)
    with engine.begin() as connection:
        connection.execute(archive.insert().values(
            evaluation_id=2, homework_id=10, kept_evaluation_id=1,
            snapshot_json={"before": True}, archived_at=datetime(2026, 1, 1),
        ))
    with pytest.raises(Exception):
        reconcile_duplicates(engine, plan)
    assert _ids(engine, table) == [1, 2, 3]
    with engine.connect() as connection:
        assert connection.execute(select(archive.c.snapshot_json)).scalar_one() == {"before": True}


def test_reject_foreign_keys_to_evaluations_without_data_loss(legacy_database):
    engine, table = legacy_database
    # Define the FK using a reflected table to allow SQLAlchemy to create it.
    metadata = MetaData()
    original = Table("evaluations", metadata, autoload_with=engine)
    dependent = Table(
        "dependent", metadata,
        Column("id", Integer, primary_key=True),
        Column("evaluation_id", Integer, ForeignKey(original.c.id)),
    )
    dependent.create(engine)
    plan = audit_duplicates(engine)
    plan["groups"][0]["keep_id"] = 1
    with pytest.raises(RuntimeError, match="foreign key"):
        reconcile_duplicates(engine, plan)
    assert _ids(engine, table) == [1, 2, 3]


def test_reconciliation_rejects_stale_score_even_if_ids_are_unchanged(legacy_database):
    engine, table = legacy_database
    plan = audit_duplicates(engine)
    plan["groups"][0]["keep_id"] = 1
    with engine.begin() as connection:
        connection.execute(
            table.update().where(table.c.id == 2).values(total_score=5.25)
        )
    with pytest.raises(ValueError, match="record contents changed"):
        reconcile_duplicates(engine, plan)
    assert _ids(engine, table) == [1, 2, 3]
    assert ARCHIVE_TABLE not in inspect(engine).get_table_names()


def test_reconciliation_rejects_stale_notes_without_exposing_them(legacy_database):
    engine, table = legacy_database
    plan = audit_duplicates(engine)
    assert "old issue" not in str(plan)
    assert "new issue" not in str(plan)
    plan["groups"][0]["keep_id"] = 1
    with engine.begin() as connection:
        connection.execute(
            table.update().where(table.c.id == 2)
            .values(issues_json=["secret later revision"])
        )
    with pytest.raises(ValueError, match="record contents changed"):
        reconcile_duplicates(engine, plan)
    assert _ids(engine, table) == [1, 2, 3]

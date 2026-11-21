"""Offline, loss-preserving reconciliation of duplicate legacy evaluation rows.

This is an operator action BEFORE the unique-homework migration, not startup
recovery. Only a manually chosen keeper is left in the live table; every other
row is copied in full to a durable archive within the same DB transaction.
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import sqlalchemy as sa


ARCHIVE_TABLE = "evaluations_legacy_archive"


def _table(engine):
    inspector = sa.inspect(engine)
    if "evaluations" not in inspector.get_table_names():
        raise RuntimeError("evaluations table does not exist")
    return sa.Table("evaluations", sa.MetaData(), autoload_with=engine)


def _serialize(value):
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    if isinstance(value, (datetime, date, Decimal)):
        return str(value) if isinstance(value, Decimal) else value.isoformat()
    if isinstance(value, (list, tuple)):
        return [_serialize(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _serialize(v) for k, v in value.items()}
    raise TypeError(f"unsupported historical evaluation value: {type(value).__name__}")


def audit_duplicates(engine) -> dict:
    """Only read records and emit a human-editable keeper decision template.

    No advice text, full issue tags or image paths are put in the audit JSON;
    the archive stores full rows only after explicit approval.
    """
    evaluations = _table(engine)
    with engine.connect() as conn:
        groups = conn.execute(
            sa.select(evaluations.c.homework_id)
            .group_by(evaluations.c.homework_id)
            .having(sa.func.count() > 1)
            .order_by(evaluations.c.homework_id)
        ).scalars().all()
        output = []
        for homework_id in groups:
            rows = conn.execute(
                sa.select(evaluations)
                .where(evaluations.c.homework_id == homework_id)
                .order_by(evaluations.c.id)
            ).mappings().all()
            output.append({
                "homework_id": homework_id,
                "ids": [r["id"] for r in rows],
                "keep_id": None,  # Never choose the winner by score or timestamp.
                "candidates": [
                    {
                        k: _serialize(r[k]) for k in (
                            "id", "status", "provider", "total_score", "updated_at"
                        ) if k in r
                    } for r in rows
                ],
            })
    return {"schema_version": 1, "groups": output}


def _archive_definition(metadata):
    return sa.Table(
        ARCHIVE_TABLE, metadata,
        sa.Column("evaluation_id", sa.Integer, primary_key=True),
        sa.Column("homework_id", sa.Integer, nullable=False),
        sa.Column("kept_evaluation_id", sa.Integer, nullable=False),
        sa.Column("snapshot_json", sa.JSON, nullable=False),
        sa.Column("archived_at", sa.DateTime, nullable=False),
    )


def reconcile_duplicates(engine, plan: dict) -> dict:
    """Archive and remove only precisely approved duplicate IDs.

    Caller must stop writers and take a restorable DB backup. Changes to rows
    or duplicate groups between audit and apply cause rollback without edits.
    """
    if plan.get("schema_version") != 1 or not isinstance(plan.get("groups"), list):
        raise ValueError("unsupported or missing reconciliation plan")
    inspector = sa.inspect(engine)
    for name in inspector.get_table_names():
        for fk in inspector.get_foreign_keys(name):
            if fk.get("referred_table") == "evaluations":
                raise RuntimeError(
                    f"{name} has a foreign key to evaluations; migrate dependents first"
                )

    existing = audit_duplicates(engine)["groups"]
    by_homework = {g["homework_id"]: g for g in existing}
    expected_ids = {h: tuple(g["ids"]) for h, g in by_homework.items()}
    user_groups = plan["groups"]
    if len(user_groups) != len(expected_ids):
        raise ValueError("duplicate groups changed; regenerate the audit")
    decisions = {}
    for item in user_groups:
        hw = item.get("homework_id")
        ids = item.get("ids")
        keep = item.get("keep_id")
        if hw in decisions or not isinstance(ids, list) or tuple(ids) != expected_ids.get(hw):
            raise ValueError(f"duplicate IDs changed or plan repeats homework {hw}")
        if type(keep) is not int or keep not in ids:
            raise ValueError(f"choose an existing keep_id for homework {hw}")
        decisions[hw] = keep
    if set(decisions) != set(expected_ids):
        raise ValueError("duplicate groups changed; regenerate the audit")
    if not decisions:
        return {"archived": 0, "kept": 0}

    evaluations = _table(engine)
    # Creating an empty archive table cannot delete live records. On MySQL this
    # DDL may autocommit; actual snapshot+delete happens in ONE DML transaction.
    archive = _archive_definition(sa.MetaData())
    archive.create(bind=engine, checkfirst=True)
    archived_count = 0
    with engine.begin() as conn:
        # Fresh verification inside the transaction, holding available row
        # locks. SQLite cannot lock rows: operator must stop writers first.
        fresh = conn.execute(
            sa.select(evaluations).where(
                evaluations.c.homework_id.in_(list(decisions))
            ).order_by(evaluations.c.homework_id, evaluations.c.id).with_for_update()
        ).mappings().all()
        grouped = {}
        for row in fresh:
            grouped.setdefault(row["homework_id"], []).append(row)
        for hw, keep_id in decisions.items():
            rows = grouped.get(hw, [])
            if tuple(r["id"] for r in rows) != expected_ids[hw]:
                raise ValueError(f"homework {hw} changed while reconciling")
            for row in rows:
                if row["id"] == keep_id:
                    continue
                conn.execute(archive.insert().values(
                    evaluation_id=row["id"],
                    homework_id=hw,
                    kept_evaluation_id=keep_id,
                    snapshot_json={k: _serialize(v) for k, v in row.items()},
                    archived_at=datetime.utcnow(),
                ))
                result = conn.execute(
                    evaluations.delete().where(
                        evaluations.c.id == row["id"],
                        evaluations.c.homework_id == hw,
                    )
                )
                if result.rowcount != 1:
                    raise RuntimeError("live row changed during archival")
                archived_count += 1
        # Verify the chosen keepers remain without ambiguity before COMMIT.
        for hw, keep_id in decisions.items():
            ids = conn.execute(
                sa.select(evaluations.c.id).where(
                    evaluations.c.homework_id == hw
                )
            ).scalars().all()
            if ids != [keep_id]:
                raise RuntimeError(f"homework {hw} keeper validation failed")
    return {"archived": archived_count, "kept": len(decisions)}

"""Storage maintenance never deletes current, referenced or young images."""

import json
import os
import time
from pathlib import Path

import pytest
from sqlalchemy import Column, Integer, JSON, MetaData, Table
from sqlalchemy.orm import Session

from app.repositories import EvaluationRepository
from app.services import evaluation_overlay_maintenance as maintenance


@pytest.fixture
def overlay_workspace(db_session, seeded_homework, tmp_path):
    root = tmp_path / "uploads"
    root.mkdir()
    (root / "test.png").write_bytes(b"original")
    now = time.time()
    stamps = {
        "orphan": "a" * 32,
        "referenced": "b" * 32,
        "running": "c" * 32,
        "young": "d" * 32,
    }
    for kind, attempt in stamps.items():
        item = root / f"test_result_{attempt}.jpg"
        item.write_bytes(kind.encode())
        timestamp = now - (45 if kind != "young" else 2) * 86400
        os.utime(item, (timestamp, timestamp))
    (root / "test_result.jpg").write_bytes(b"legacy-no-attempt")
    (root / f"unrelated_result_{'e' * 32}.jpg").write_bytes(b"unrelated")
    return root, stamps, now


def _name(root, token):
    return root / f"test_result_{token}.jpg"


def _session_factory(db_session):
    return lambda: Session(bind=db_session.get_bind())


def test_inventory_protects_db_urls_and_current_processing(
    db_session, seeded_homework, overlay_workspace,
):
    root, tokens, now = overlay_workspace
    EvaluationRepository.create_evaluation(
        db_session, homework_id=seeded_homework.id,
        provider="qwen", status="processing", attempt_id=tokens["running"],
        compare_image_url=f"/uploads/test_result_{tokens['referenced']}.jpg",
    )
    files = maintenance.find_orphan_overlays(
        db_session, root, now=now, min_age_seconds=7 * 86400,
    )
    assert [item["attempt_id"] for item in files] == [tokens["orphan"]]
    assert len(list(root.iterdir())) == 7


def test_legacy_archive_reference_is_not_deletable(
    db_session, seeded_homework, overlay_workspace,
):
    root, tokens, now = overlay_workspace
    archived = Table(
        "evaluations_legacy_archive", MetaData(),
        Column("evaluation_id", Integer, primary_key=True),
        Column("snapshot_json", JSON, nullable=False),
    )
    archived.create(db_session.get_bind())
    db_session.execute(archived.insert().values(
        evaluation_id=13,
        snapshot_json={"compare_image_url":
            f"/uploads/test_result_{tokens['orphan']}.jpg"},
    ))
    db_session.commit()
    files = maintenance.find_orphan_overlays(
        db_session, root, now=now, min_age_seconds=7 * 86400,
    )
    assert tokens["orphan"] not in {f["attempt_id"] for f in files}


def test_quarantine_moves_only_old_unreferenced_with_restoration_journal(
    db_session, seeded_homework, overlay_workspace, tmp_path,
):
    root, tokens, now = overlay_workspace
    EvaluationRepository.create_evaluation(
        db_session, homework_id=seeded_homework.id, provider="qwen",
        status="processing", attempt_id=tokens["running"],
        compare_image_url=f"/uploads/test_result_{tokens['referenced']}.jpg",
    )
    destination = tmp_path / "private-quarantine"
    moved = maintenance.quarantine_orphan_overlays(
        _session_factory(db_session), root, destination,
        writers_stopped=True, now=now, min_age_seconds=7 * 86400,
    )
    assert len(moved) == 1
    assert moved[0]["attempt_id"] == tokens["orphan"]
    assert not _name(root, tokens["orphan"]).exists()
    assert _name(destination, tokens["orphan"]).read_bytes() == b"orphan"
    assert _name(root, tokens["referenced"]).exists()
    assert _name(root, tokens["running"]).exists()
    assert _name(root, tokens["young"]).exists()
    entries = [
        json.loads(line) for line in
        (destination / "manifest.jsonl").read_text().splitlines()
    ]
    assert len(entries) == 1
    assert entries[0]["source"] == moved[0]["relative_path"]
    assert entries[0]["size_bytes"] == len(b"orphan")


def test_quarantine_requires_explicit_offline_and_private_destination(
    db_session, overlay_workspace, tmp_path,
):
    root, tokens, now = overlay_workspace
    with pytest.raises(ValueError, match="offline"):
        maintenance.quarantine_orphan_overlays(
            _session_factory(db_session), root, tmp_path / "q",
            writers_stopped=False, now=now,
        )
    with pytest.raises(ValueError, match="outside"):
        maintenance.quarantine_orphan_overlays(
            _session_factory(db_session), root, root / "quarantine",
            writers_stopped=True, now=now,
        )
    assert _name(root, tokens["orphan"]).exists()


def test_destination_collision_is_fail_closed(
    db_session, seeded_homework, overlay_workspace, tmp_path,
):
    root, tokens, now = overlay_workspace
    private = tmp_path / "quarantine"
    target = _name(private, tokens["orphan"])
    target.parent.mkdir(parents=True)
    target.write_bytes(b"do-not-overwrite")
    with pytest.raises(FileExistsError):
        maintenance.quarantine_orphan_overlays(
            _session_factory(db_session), root, private,
            writers_stopped=True, now=now, min_age_seconds=7 * 86400,
        )
    assert target.read_bytes() == b"do-not-overwrite"
    assert _name(root, tokens["orphan"]).exists()


def test_symlink_is_not_a_managed_file(
    db_session, seeded_homework, overlay_workspace, tmp_path,
):
    root, tokens, now = overlay_workspace
    outside = tmp_path / "outside.jpg"
    outside.write_bytes(b"private")
    link = _name(root, "f" * 32)
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are not supported in this filesystem")
    results = maintenance.find_orphan_overlays(
        db_session, root, now=now, min_age_seconds=7 * 86400,
    )
    assert "f" * 32 not in {r["attempt_id"] for r in results}

"""Result overlays belong to individual evaluation attempts, not homework files."""

from pathlib import Path

import pytest
from PIL import Image

from app.services.file_storage_service import FileStorageService
from app.services import file_storage_service as module


@pytest.fixture
def image_workspace(monkeypatch, tmp_path):
    monkeypatch.setattr(
        FileStorageService, "get_storage_root",
        staticmethod(lambda: tmp_path),
    )
    Image.new("RGB", (400, 300), color="white").save(tmp_path / "sample.jpg")
    return "/uploads/sample.jpg", tmp_path


def _scores(value):
    return {
        "total_score": value,
        "structure_score": value,
        "center_score": value,
        "stroke_order_score": value,
    }


def test_independent_attempts_never_overwrite_each_other(image_workspace):
    source_url, folder = image_workspace
    older_id = "a" * 32
    newer_id = "b" * 32
    older = FileStorageService.save_result_overlay(
        source_url, _scores(4.0), [], attempt_id=older_id,
    )
    assert older == f"/uploads/sample_result_{older_id}.jpg"
    older_bytes = FileStorageService.resolve_upload_url(older).read_bytes()

    newer = FileStorageService.save_result_overlay(
        source_url, _scores(9.0), [], attempt_id=newer_id,
    )
    assert newer == f"/uploads/sample_result_{newer_id}.jpg"
    assert newer != older
    assert FileStorageService.resolve_upload_url(older).read_bytes() == older_bytes
    assert FileStorageService.resolve_upload_url(newer).read_bytes() != older_bytes
    assert not (folder / "sample_result.jpg").exists()
    assert not list(folder.glob(".*.tmp"))


def test_invalid_attempt_id_is_not_a_filename_escape(image_workspace):
    source_url, folder = image_workspace
    with pytest.raises(ValueError):
        FileStorageService.save_result_overlay(
            source_url, _scores(8.0), [], attempt_id="../evil",
        )
    assert [f.name for f in folder.iterdir()] == ["sample.jpg"]


def test_result_replace_failure_keeps_previous_image_and_discards_temp(
    image_workspace, monkeypatch,
):
    source_url, folder = image_workspace
    older_id = "a" * 32
    older = FileStorageService.save_result_overlay(
        source_url, _scores(5.0), [], attempt_id=older_id,
    )
    older_bytes = FileStorageService.resolve_upload_url(older).read_bytes()

    def fail_rename(*_):
        raise OSError("simulated rename failure")

    monkeypatch.setattr(module.os, "replace", fail_rename)
    failed_url = FileStorageService.save_result_overlay(
        source_url, _scores(9.0), [], attempt_id="b" * 32,
    )
    assert failed_url == source_url
    assert FileStorageService.resolve_upload_url(older).read_bytes() == older_bytes
    assert not (folder / f"sample_result_{'b' * 32}.jpg").exists()
    assert not list(folder.glob(".*.tmp"))

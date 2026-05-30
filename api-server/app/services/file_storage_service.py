from __future__ import annotations

import os

from pathlib import Path
from uuid import uuid4

from app.core.config import settings


class FileStorageService:
    @staticmethod
    def get_storage_root() -> Path:
        root = Path(settings.storage_root)
        if not root.is_absolute():
            root = Path(__file__).resolve().parents[2] / root
        root.mkdir(parents=True, exist_ok=True)
        return root

    @staticmethod
    def save_homework_image(task_id: int, student_id: int, filename: str, content: bytes) -> tuple[str, Path]:
        suffix = Path(filename).suffix.lower() or ".jpg"
        safe_name = f"{uuid4().hex}{suffix}"
        relative_path = Path("homework") / str(student_id) / str(task_id) / safe_name
        absolute_path = FileStorageService.get_storage_root() / relative_path
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        absolute_path.write_bytes(content)
        file_url = f"/uploads/{relative_path.as_posix()}"
        return file_url, absolute_path

    @staticmethod
    def resolve_upload_url(file_url: str) -> Path:
        normalized = file_url.strip()
        if normalized.startswith("/uploads/"):
            normalized = normalized[len("/uploads/") :]
        return FileStorageService.get_storage_root() / normalized.replace("/", os.sep)

from __future__ import annotations

import os
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from app.core.config import settings

try:
    from PIL import Image
except ImportError:
    Image = None

MAX_IMAGE_DIMENSION = 2048


class FileStorageService:
    @staticmethod
    def get_storage_root() -> Path:
        root = Path(settings.storage_root)
        if not root.is_absolute():
            root = Path(__file__).resolve().parents[2] / root
        root.mkdir(parents=True, exist_ok=True)
        return root

    @staticmethod
    def _normalize_image(content: bytes) -> bytes:
        """用 Pillow 二次规范化：统一 JPEG 格式、去除 EXIF、限制尺寸、处理透明背景。"""
        if Image is None:
            return content
        try:
            img = Image.open(BytesIO(content))

            # 处理透明/索引色模式：转为 RGB 并填充白色背景
            if img.mode in ("RGBA", "LA"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])
                img = background
            elif img.mode == "P":
                img = img.convert("RGBA")
                background = Image.new("RGB", img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])
                img = background
            elif img.mode != "RGB":
                img = img.convert("RGB")

            # 限制最大尺寸
            if img.width > MAX_IMAGE_DIMENSION or img.height > MAX_IMAGE_DIMENSION:
                img.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION))

            # 重新保存为统一 JPEG，EXIF 自动丢弃（不传 exif 参数）
            output = BytesIO()
            img.save(output, format="JPEG", quality=88, optimize=True)
            return output.getvalue()
        except Exception:
            return content

    @staticmethod
    def save_homework_image(task_id: int, student_id: int, filename: str, content: bytes) -> tuple[str, Path]:
        # 二次规范化：统一 JPEG、去 EXIF、限尺寸、处理透明背景
        normalized = FileStorageService._normalize_image(content)
        safe_name = f"{uuid4().hex}.jpg"
        relative_path = Path("homework") / str(student_id) / str(task_id) / safe_name
        absolute_path = FileStorageService.get_storage_root() / relative_path
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        absolute_path.write_bytes(normalized)
        file_url = f"/uploads/{relative_path.as_posix()}"
        return file_url, absolute_path

    @staticmethod
    def resolve_upload_url(file_url: str) -> Path:
        normalized = file_url.strip()
        if normalized.startswith("/uploads/"):
            normalized = normalized[len("/uploads/") :]
        return FileStorageService.get_storage_root() / normalized.replace("/", os.sep)

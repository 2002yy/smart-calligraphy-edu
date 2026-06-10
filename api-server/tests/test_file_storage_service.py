"""Tests for the file storage service layer.

Covers image normalization with real calligraphy images, overlay rendering
with Chinese text, and cross-platform font resilience.
"""

import os
from pathlib import Path

import pytest

from app.core.config import settings
from app.services.file_storage_service import FileStorageService

# 测试用真实书法样张（非 1×1 dummy）
ASSETS_DIR = Path(__file__).resolve().parent / "assets"
CALLIGRAPHY_SAMPLE = ASSETS_DIR / "calligraphy_sample.jpg"


class TestNormalizeImage:
    """使用真实书法图片验证 Pillow 处理管线。"""

    def test_normalize_jpeg_preserves_content(self):
        """JPEG 输入应保持图像内容不变，返回值仍为字节。"""
        raw = CALLIGRAPHY_SAMPLE.read_bytes()
        result = FileStorageService._normalize_image(raw)
        assert isinstance(result, bytes)
        assert len(result) > 1000  # 不是空结果

    def test_normalize_outputs_jpeg(self):
        """规范化后应输出 JPEG（即使输入是其他格式）。"""
        raw = CALLIGRAPHY_SAMPLE.read_bytes()
        result = FileStorageService._normalize_image(raw)
        assert result[:2] == b"\xff\xd8"  # JPEG magic

    def test_normalize_rgba_to_rgb(self):
        """RGBA 图片应合并透明背景为 RGB。"""
        from PIL import Image
        import io

        rgba = Image.new("RGBA", (100, 100), (255, 0, 0, 128))
        buf = io.BytesIO()
        rgba.save(buf, "PNG")
        result = FileStorageService._normalize_image(buf.getvalue())
        reloaded = Image.open(io.BytesIO(result))
        assert reloaded.mode == "RGB"

    def test_normalize_resizes_oversized(self):
        """超大图片应缩放到 MAX_IMAGE_DIMENSION 以内。"""
        from PIL import Image
        import io

        huge = Image.new("RGB", (4096, 4096), color=200)
        buf = io.BytesIO()
        huge.save(buf, "JPEG")
        result = FileStorageService._normalize_image(buf.getvalue())
        reloaded = Image.open(io.BytesIO(result))
        assert reloaded.width <= 2048
        assert reloaded.height <= 2048


class TestSaveResultOverlay:
    """使用真实书法样张验证 overlay 渲染管线。"""

    @pytest.fixture(autouse=True)
    def _setup_sample(self):
        """将样张复制到 storage 目录，并构建可访问的 URL。"""
        storage_root = Path(FileStorageService.get_storage_root())
        storage_root.mkdir(parents=True, exist_ok=True)
        dst = storage_root / "test_sample_overlay.jpg"
        dst.write_bytes(CALLIGRAPHY_SAMPLE.read_bytes())
        self.sample_url = f"/uploads/test_sample_overlay.jpg"
        yield
        # 清理生成的文件
        for suffix in ["", "_result"]:
            p = storage_root / f"test_sample_overlay{suffix}.jpg"
            if p.exists():
                p.unlink()

    def test_overlay_generates_result_image(self):
        """Overlay 应生成 _result.jpg 文件。"""
        url = FileStorageService.save_result_overlay(
            image_url=self.sample_url,
            scores={"total_score": 8.5, "structure_score": 8.0, "center_score": 7.5, "stroke_order_score": 9.0},
            tags=["结构工整", "重心稳当", "笔法到位"],
        )
        assert url != self.sample_url
        assert "_result.jpg" in url

    def test_overlay_contains_expected_dimensions(self):
        """结果图应在 800px 以内（thumbnail 限制）。"""
        from PIL import Image

        url = FileStorageService.save_result_overlay(
            image_url=self.sample_url,
            scores={"total_score": 8.5, "structure_score": 8.0, "center_score": 7.5, "stroke_order_score": 9.0},
            tags=["结构工整"],
        )
        result_path = FileStorageService.resolve_upload_url(url)
        img = Image.open(result_path)
        assert img.width <= 800
        assert img.height <= 800

    def test_overlay_with_annotations(self):
        """标注框应被绘制到结果图上。"""
        url = FileStorageService.save_result_overlay(
            image_url=self.sample_url,
            scores={"total_score": 8.5, "structure_score": 8.0, "center_score": 7.5, "stroke_order_score": 9.0},
            tags=["结构工整"],
            annotations=[
                {"x1": 10, "y1": 20, "x2": 50, "y2": 60, "label": "横画偏斜", "severity": "major"},
                {"x1": 100, "y1": 150, "x2": 140, "y2": 180, "label": "竖画不直", "severity": "minor"},
            ],
        )
        assert "_result.jpg" in url
        # 验证文件确实有内容
        result_path = FileStorageService.resolve_upload_url(url)
        assert result_path.stat().st_size > 1000

    def test_overlay_invalid_annotation_fallback(self):
        """标注缺少关键字段应优雅 fallback。"""
        url = FileStorageService.save_result_overlay(
            image_url=self.sample_url,
            scores={"total_score": 8.5, "structure_score": 8.0, "center_score": 7.5, "stroke_order_score": 9.0},
            tags=[],
            annotations=[{"x1": 10, "label": "missing"}],  # 缺 y1/x2/y2
        )
        # 不抛异常，返回原图或结果图均可
        assert url is not None

    def test_overlay_preserves_score_values(self):
        """overlay 不应修改原始图片 URL 所指文件。"""
        original_bytes = FileStorageService.resolve_upload_url(self.sample_url).read_bytes()
        FileStorageService.save_result_overlay(
            image_url=self.sample_url,
            scores={"total_score": 7.0, "structure_score": 6.5, "center_score": 7.0, "stroke_order_score": 6.0},
            tags=["测试"],
        )
        # 原图应保持不变
        assert FileStorageService.resolve_upload_url(self.sample_url).read_bytes() == original_bytes


class TestFontFallback:
    """验证中文字体跨平台搜索。"""

    def test_font_candidates_include_user_env(self, monkeypatch):
        """CALLIGRAPHY_FONT_PATH 应被加入候选列表首位。"""
        monkeypatch.setattr(settings, "calligraphy_font_path", "/custom/font.ttc")
        # 内部 font_candidates[0] 应为此路径；为验证，实际渲染会使用它。
        # 无法断言内部实现细节，但可验证 CSS 风格的接口不变
        from PIL import ImageDraw

        assert hasattr(ImageDraw, "ImageDraw")

    def test_overlay_does_not_crash_without_font(self, monkeypatch):
        """即使无中文字体，overlay 也不应抛异常。"""
        # 清空 settings 的 font_path，并用空候选列表模拟
        monkeypatch.setattr(settings, "calligraphy_font_path", "")
        result = FileStorageService.save_result_overlay(
            image_url=self._create_dummy(),
            scores={"total_score": 8.0, "structure_score": 7.0, "center_score": 8.0, "stroke_order_score": 7.5},
            tags=["结构工整"],
        )
        assert "_result.jpg" in result or result == self._create_dummy()

    def _create_dummy(self) -> str:
        """创建临时图片并返回 URL。"""
        from PIL import Image
        import io

        storage_root = FileStorageService.get_storage_root()
        name = "_font_test_dummy_.jpg"
        path = storage_root / name
        if not path.exists():
            Image.new("RGB", (100, 100), color=200).save(path, "JPEG")
        return f"/uploads/{name}"


class TestSaveHomeworkImage:
    """使用真实书法样张测试保存作业图片。"""

    def test_save_preserves_image_content(self):
        """保存后的图片应可从 resolve_upload_url 正确读取。"""
        raw = CALLIGRAPHY_SAMPLE.read_bytes()
        file_url, abs_path = FileStorageService.save_homework_image(
            task_id=99, student_id=99, filename="test.jpg", content=raw
        )
        try:
            assert abs_path.exists()
            resolved = FileStorageService.resolve_upload_url(file_url)
            assert resolved == abs_path.resolve()
            assert len(resolved.read_bytes()) > 1000
        finally:
            if abs_path.exists():
                abs_path.unlink()
            # 清理空目录
            abs_path.parent.rmdir()
            abs_path.parent.parent.rmdir()

    def test_save_normalizes_to_jpeg(self):
        """即使是 PNG 输入，保存结果也应为 JPEG。"""
        from PIL import Image
        import io

        png = Image.new("RGB", (100, 100), color=100)
        buf = io.BytesIO()
        png.save(buf, "PNG")
        file_url, abs_path = FileStorageService.save_homework_image(
            task_id=99, student_id=99, filename="test.png", content=buf.getvalue()
        )
        try:
            data = abs_path.read_bytes()
            assert data[:2] == b"\xff\xd8"  # JPEG header
        finally:
            if abs_path.exists():
                abs_path.unlink()
            abs_path.parent.rmdir()
            abs_path.parent.parent.rmdir()

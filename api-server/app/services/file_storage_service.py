from __future__ import annotations

import os
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from app.core.config import settings

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = None
    ImageDraw = None
    ImageFont = None

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

            if img.width > MAX_IMAGE_DIMENSION or img.height > MAX_IMAGE_DIMENSION:
                img.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION))

            output = BytesIO()
            img.save(output, format="JPEG", quality=88, optimize=True)
            return output.getvalue()
        except Exception:
            return content

    @staticmethod
    def save_homework_image(task_id: int, student_id: int, filename: str, content: bytes) -> tuple[str, Path]:
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

    @staticmethod
    def save_result_overlay(
        image_url: str,
        scores: dict,
        tags: list[str],
        annotations: list[dict] | None = None,
    ) -> str:
        """在原图上叠加评分信息和检测框标注，生成结果图。

        Args:
            image_url: 原图 URL（如 /uploads/homework/2/1/xxx.jpg）
            scores: 评分字典 {total_score, structure_score, center_score, stroke_order_score}
            tags: 问题标签列表
            annotations: 可选，检测框标注列表，每项含 type/label/x1/y1/x2/y2/severity

        Returns:
            结果图的 URL，失败则返回原图 URL
        """
        if Image is None or ImageDraw is None:
            return image_url

        src_path = FileStorageService.resolve_upload_url(image_url)
        if not src_path.exists():
            return image_url

        try:
            img = Image.open(src_path).convert("RGB")
            orig_w, orig_h = img.size

            # 缩放到标准尺寸，记录缩放比例
            img.thumbnail((800, 800))
            w, h = img.size
            scale_x = w / orig_w
            scale_y = h / orig_h
            draw = ImageDraw.Draw(img)

            # 加载中文字体
            font_large = None
            font_small = None
            font_tiny = None
            for fp in [
                "C:/Windows/Fonts/msyh.ttc",
                "C:/Windows/Fonts/simsun.ttc",
                "C:/Windows/Fonts/simhei.ttf",
            ]:
                if Path(fp).exists():
                    try:
                        font_large = ImageFont.truetype(fp, 28)
                        font_small = ImageFont.truetype(fp, 18)
                        font_tiny = ImageFont.truetype(fp, 14)
                        break
                    except Exception:
                        continue

            # ── 绘制检测框标注（在底部评分条之前）──
            if annotations:
                for ann in annotations:
                    # 将原始坐标缩放到缩略图尺寸
                    x1 = int(ann["x1"] * scale_x)
                    y1 = int(ann["y1"] * scale_y)
                    x2 = int(ann["x2"] * scale_x)
                    y2 = int(ann["y2"] * scale_y)

                    # 裁剪到图像边界
                    x1 = max(0, min(w, x1))
                    y1 = max(0, min(h, y1))
                    x2 = max(x1, min(w, x2))
                    y2 = max(y1, min(h, y2))
                    box_w = x2 - x1
                    box_h = y2 - y1
                    if box_w < 1 or box_h < 1:
                        continue

                    # 根据 severity 选择颜色
                    severity = ann.get("severity", "minor")
                    if severity == "major":
                        rect_color = (255, 50, 50, 60)
                    else:
                        rect_color = (255, 180, 50, 60)

                    # 绘制半透明矩形覆盖层
                    overlay = Image.new("RGBA", (box_w, box_h), rect_color)
                    img.paste(overlay, (x1, y1), overlay)

                    # 绘制白色连接线与标签
                    label = ann.get("label", ann.get("type", ""))
                    if label and font_tiny:
                        cx = (x1 + x2) // 2
                        line_top = max(y1 - 24, 2)

                        # 竖线：从框顶部中心向上
                        draw.line([(cx, y1), (cx, line_top)], fill=(255, 255, 255), width=1)
                        # 短横线：向右延伸供文字放置
                        draw.line([(cx, line_top), (cx + 36, line_top)], fill=(255, 255, 255), width=1)
                        # 文字标签：放在横线末端
                        draw.text((cx + 40, line_top - 7), label, fill=(255, 255, 255), font=font_tiny)

            # ── 底部半透明黑条（原有逻辑不变）──
            bar_h = 100
            overlay = Image.new("RGBA", (w, bar_h), (0, 0, 0, 160))
            img.paste(overlay, (0, h - bar_h), overlay)

            # 总分（左侧大号）
            total = scores.get("total_score", 0)
            total_text = f"{total}"
            tw = 0
            if font_large:
                bbox = draw.textbbox((0, 0), total_text, font=font_large)
                tw = bbox[2] - bbox[0]
            draw.text((16, h - bar_h + 8), total_text, fill=(255, 255, 255), font=font_large)
            draw.text((16 + tw + 4, h - bar_h + 14), "/10", fill=(200, 200, 200), font=font_small)

            # 子维度分数（中部）
            parts = [
                f"结构 {scores.get('structure_score', 0)}",
                f"重心 {scores.get('center_score', 0)}",
                f"笔顺 {scores.get('stroke_order_score', 0)}",
            ]
            x = 16 + tw + 50
            for part in parts:
                draw.text((x, h - bar_h + 12), part, fill=(220, 220, 220), font=font_small)
                if font_small:
                    bbox = draw.textbbox((0, 0), part, font=font_small)
                    x += (bbox[2] - bbox[0]) + 16

            # 标签（底部右对齐）
            if tags and font_small:
                tag_text = "  ".join(tags)
                bbox = draw.textbbox((0, 0), tag_text, font=font_small)
                tw2 = bbox[2] - bbox[0]
                draw.text((w - tw2 - 16, h - bar_h + 50), tag_text, fill=(255, 200, 100), font=font_small)

            # 保存为新文件
            dst_name = f"{src_path.stem}_result.jpg"
            dst_path = src_path.parent / dst_name
            img.save(dst_path, "JPEG", quality=90, optimize=True)

            url_dir = image_url.rsplit("/", 1)[0]
            return f"{url_dir}/{dst_name}"

        except Exception:
            return image_url

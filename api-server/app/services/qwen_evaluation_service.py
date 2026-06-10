"""Qwen3.5-Plus 视觉书法评测服务

通过阿里云百炼 DashScope API（OpenAI 兼容模式）调用通义千问 qwen3.5-omni-plus 模型，
对上传的书法作品图片进行结构、重心、笔画维度的智能评分。

模型: qwen3.5-omni-plus — 397B 参数（激活 17B），原生多模态，2026年2月发布
价格: ¥0.8/百万输入tokens, ¥4.8/百万输出tokens
       每次评测约 ¥0.002（含图片编码），¥5 可跑约 2500 次
开通: 阿里云百炼控制台 -> 模型广场 -> qwen3.5-omni-plus -> 申请 API Key
API 文档: https://help.aliyun.com/zh/model-studio/developer-reference
"""

from __future__ import annotations

import base64
import json
import logging
import mimetypes
from io import BytesIO
from pathlib import Path

from fastapi import HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None

logger = logging.getLogger(__name__)

# 允许的标签白名单——Qwen 输出中的 tags 必须属于此集合
# ⚠️ 如修改 Qwen prompt 中的标签列表，请同步更新此集合
#    对应位置：本文件 score() 方法的 system prompt "【标签要求】" 段
ALLOWED_TAGS: set[str] = {
    # 正向
    "结构工整", "重心稳当", "笔法到位", "主笔突出", "疏密得当",
    "运笔流畅", "笔画有力",
    # 负向
    "中宫松散", "重心偏左/偏右", "撇捺角度过大", "横画扛肩过度",
    "竖画不直", "主笔不突出", "疏密不当", "笔法有误", "运笔生硬",
    "结构失衡", "大小不一", "间距不均", "笔画过细/过粗", "起笔收笔草率",
}


class QwenAnnotation(BaseModel):
    """标注框 — 用于在图片上标记问题区域。"""

    type: str = Field(default="")  # "structure" | "center" | "stroke"
    label: str = Field(default="")  # short text like "撇捺角度过大"
    x1: float = Field(ge=0, le=100)  # left % coordinate
    y1: float = Field(ge=0, le=100)  # top % coordinate
    x2: float = Field(ge=0, le=100)  # right % coordinate
    y2: float = Field(ge=0, le=100)  # bottom % coordinate
    severity: str = Field(default="minor")  # "minor" | "major"


class QwenThinkingStep(BaseModel):
    """思考步骤中的单个步骤。"""

    step: int = Field(ge=1, le=10)
    title: str = Field(min_length=1, max_length=30)
    detail: str = Field(min_length=1, max_length=500)
    score: float = Field(default=0.0, ge=0, le=10)


class QwenEvaluationResult(BaseModel):
    """Qwen 视觉模型书法评分结果。"""

    total_score: float = Field(ge=0, le=10)
    structure_score: float = Field(ge=0, le=10)
    structure_observation: str = Field(default="")
    structure_suggestion: str = Field(default="")
    center_score: float = Field(ge=0, le=10)
    center_observation: str = Field(default="")
    center_suggestion: str = Field(default="")
    stroke_order_score: float = Field(ge=0, le=10)  # 笔法规范性评分（字段名保留历史兼容，对外语义为笔法质量）
    stroke_order_observation: str = Field(default="")
    stroke_order_suggestion: str = Field(default="")
    tags: list[str] = Field(default_factory=list)
    advice: str = Field(default="", max_length=200)
    thinking_steps: list[QwenThinkingStep] = Field(default_factory=list)
    annotations: list[QwenAnnotation] = Field(default_factory=list)


class QwenEvaluationService:
    """调用阿里云百炼 DashScope（qwen3.5-omni-plus 视觉模型）进行书法评分。"""

    @staticmethod
    def is_configured() -> bool:
        return bool(settings.qwen_evaluation_enabled and settings.qwen_api_key)

    @staticmethod
    def _prepare_image_bytes(image_path: Path) -> tuple[bytes, str]:
        raw_bytes = image_path.read_bytes()
        mime_type = mimetypes.guess_type(image_path.name)[0] or "image/jpeg"

        max_size = settings.qwen_image_max_size
        if Image is None or max_size <= 0:
            return raw_bytes, mime_type

        try:
            with Image.open(image_path) as image:
                if image.mode not in ("RGB", "L"):
                    image = image.convert("RGB")
                image.thumbnail((max_size, max_size))
                output = BytesIO()
                output_format = "PNG" if mime_type == "image/png" else "JPEG"
                save_kwargs = {"optimize": True}
                if output_format == "JPEG":
                    save_kwargs["quality"] = 88
                image.save(output, format=output_format, **save_kwargs)
                return output.getvalue(), "image/png" if output_format == "PNG" else "image/jpeg"
        except Exception:
            return raw_bytes, mime_type

    @staticmethod
    def _extract_json(raw: str) -> str:
        """从模型输出中提取 JSON 内容。

        模型有时会返回 ```json ... ``` 包裹的内容，
        或者在 JSON 前后添加额外的说明文字。
        """
        content = raw.strip()

        # 尝试剥离 markdown 代码块（```json 和 ```）
        for marker in ("```json", "```"):
            idx = content.find(marker)
            if idx != -1:
                start = idx + len(marker)
                end = content.rfind("```")
                if end > start:
                    content = content[start:end].strip()
                else:
                    content = content[start:].strip()

        # 去掉可能的 BOM 或零宽字符
        content = content.strip("﻿​")
        return content

    @staticmethod
    def _filter_tags(tags: list[str]) -> list[str]:
        """只保留白名单内的标签，舍弃模型自编的标签。"""
        if not isinstance(tags, list):
            return []
        return [t for t in tags if t in ALLOWED_TAGS]

    @staticmethod
    def score(
        image_path: Path,
        practice_chars: list[str] | None = None,
        task_title: str | None = None,
    ) -> dict:
        """调用 Qwen3.5-Plus 视觉模型对书法作品评分。

        Args:
            image_path: 书法作业图片的本地路径。
            practice_chars: 任务指定的练习字列表（如 ["永", "大", "木"]）。
            task_title: 任务标题。

        Returns:
            包含 score / tags / advice / thinking_steps 的字典。
        """
        if not settings.qwen_api_key:
            raise HTTPException(
                status_code=400,
                detail="QWEN_API_KEY 未配置。请先在阿里云百炼控制台申请 API Key。",
            )

        if not image_path.exists():
            raise HTTPException(status_code=404, detail="书法作业图片文件未找到")

        # ---- 准备图片 ----
        image_bytes, mime_type = QwenEvaluationService._prepare_image_bytes(image_path)
        encoded_image = base64.b64encode(image_bytes).decode("utf-8")
        data_url = f"data:{mime_type};base64,{encoded_image}"

        practice_text = "、".join(practice_chars or []) or "未指定"
        task_text = task_title or "书法作业"

        # ---- 构造请求（DashScope OpenAI 兼容模式）----
        import httpx

        payload = {
            "model": settings.qwen_evaluation_model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "你是一位专业的中国书法教师，正在批改学生的书法练习作业。\n\n"
                        "【评分体系】三个维度，权重不同：\n"
                        "1. 结构 (权重 40%)：间架结构是否合理，中宫是否收紧，主笔是否突出\n"
                        "2. 重心 (权重 30%)：整体重心是否平稳，左右是否平衡\n"
                        "3. 笔法 (权重 30%)：笔画规范性、运笔痕迹、起收笔质量\n"
                        "综合得分 = 结构×40% + 重心×30% + 笔法×30%\n\n"
                        "【评分锚点】(必须大胆使用整个分数区间，不要只打中间分)\n"
                        "9-10：范本级别，结构精准、重心稳当、笔法娴熟。遇到真写得好的要勇于打\n"
                        "7-8 ：中等偏上，大部分还行但有小毛病\n"
                        "5-6 ：不及格水平，结构松散、重心不稳或笔法有明显问题\n"
                        "3-4 ：很差，多个维度都需要从头练\n"
                        "1-2 ：几乎没训练痕迹，完不成基本书写\n\n"
                        "【标签要求】\n"
                        "必须从以下列表中选出 2-4 个最贴合的标签，不要自己编造：\n"
                        "好的标签：结构工整、重心稳当、笔法到位、主笔突出、疏密得当、运笔流畅、笔画有力\n"
                        "差的标签：中宫松散、重心偏左/偏右、撇捺角度过大、横画扛肩过度、"
                        "竖画不直、主笔不突出、疏密不当、笔法有误、运笔生硬、"
                        "结构失衡、大小不一、间距不均、笔画过细/过粗、起笔收笔草率\n\n"
                        "【批改风格要求】\n"
                        "- 先肯定优点，再指出问题，最后给修改方向\n"
                        "- 使用专业书法术语：主笔、重心、扛肩、收放、疏密\n"
                        "- 观察和建议要具体到笔画层面\n"
                        "- 每个维度的修改建议让学生知道具体怎么改\n\n"
                        "【输出要求】\n"
                        "必须返回严格的 JSON 对象，不要包含任何额外的文字说明。"
                        "如果发现具体问题笔画，请标注其位置坐标(百分比0-100)，例如撇捺角度过大、竖画不直等。\n"
                        "JSON 结构：\n"
                        "{\n"
                        '  "structure_score": <0-10 一位小数>,\n'
                        '  "structure_observation": "结构观察，一句话",\n'
                        '  "structure_suggestion": "结构修改建议，一句话",\n'
                        '  "center_score": <0-10 一位小数>,\n'
                        '  "center_observation": "重心观察，一句话",\n'
                        '  "center_suggestion": "重心修改建议，一句话",\n'
                        '  "stroke_order_score": <0-10 一位小数>,\n'
                        '  "stroke_order_observation": "笔法观察，一句话",\n'
                        '  "stroke_order_suggestion": "笔法修改建议，一句话",\n'
                        '  "total_score": <按权重计算的综合得分>,\n'
                        '  "tags": ["从候选列表中选的2-4个标签"],\n'
                        '  "annotations": [\n'
                        '    {"type": "structure/stroke/center", "label": "问题描述", "x1": 左%, "y1": 上%, "x2": 右%, "y2": 下%, "severity": "major/minor"}\n'
                        '  ],\n'
                        '  "advice": "综合练习建议，不超过120字",\n'
                        '  "thinking_steps": [\n'
                        '    {"step":1,"title":"图像预处理","detail":"观察","score":0},\n'
                        '    {"step":2,"title":"文字区域检测","detail":"检测","score":0},\n'
                        '    {"step":3,"title":"单字分割","detail":"分割","score":0},\n'
                        '    {"step":4,"title":"结构分析","detail":"观察","score":分数},\n'
                        '    {"step":5,"title":"重心检测","detail":"观察","score":分数},\n'
                        '    {"step":6,"title":"笔法验证","detail":"观察","score":分数},\n'
                        '    {"step":7,"title":"综合评分","detail":"总结","score":总分}\n'
                        "  ]\n"
                        "}\n"
                        "注意：每个 step 都需包含 step/title/detail/score 四个字段，score 不能省略。"
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"任务标题：{task_text}\n"
                                    f"练习字：{practice_text}\n"
                                    "请从结构稳定性、重心平衡和笔画完整性三个维度评价这幅书法作品，"
                                    "并给出综合评分和练习建议。",
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": data_url, "detail": settings.qwen_image_detail},
                        },
                    ],
                },
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.7,
        }

        try:
            resp = httpx.post(
                f"{settings.qwen_base_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.qwen_api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=60,
            )
            resp.raise_for_status()
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Qwen API 请求超时，请稍后重试。")
        except httpx.HTTPStatusError as exc:
            detail = f"Qwen API 返回错误 (HTTP {exc.response.status_code})"
            try:
                body = exc.response.json()
                if "error" in body:
                    detail += f": {body['error'].get('message', str(body['error']))}"
            except Exception:
                detail += f": {exc.response.text[:200]}"
            raise HTTPException(status_code=502, detail=detail)

        # ---- 解析响应 ----
        try:
            body = resp.json()
            content = QwenEvaluationService._extract_json(body["choices"][0]["message"]["content"])
            result = json.loads(content)
        except (KeyError, IndexError, json.JSONDecodeError) as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Qwen API 返回格式异常，无法解析评测结果。{exc}",
            )

        # ---- 验证与规范化 ----
        def _clamp(val, default=0):
            try:
                return max(0, min(10, round(float(val), 1)))
            except (ValueError, TypeError):
                return default

        structure_score = _clamp(result.get("structure_score"))
        structure_observation = str(result.get("structure_observation", "") or "")
        structure_suggestion = str(result.get("structure_suggestion", "") or "")
        center_score = _clamp(result.get("center_score"))
        center_observation = str(result.get("center_observation", "") or "")
        center_suggestion = str(result.get("center_suggestion", "") or "")
        stroke_order_score = _clamp(result.get("stroke_order_score"))
        stroke_order_observation = str(result.get("stroke_order_observation", "") or "")
        stroke_order_suggestion = str(result.get("stroke_order_suggestion", "") or "")

        # 综合得分：优先用模型返回的 total_score，否则按权重计算
        total_score = _clamp(result.get("total_score"))
        weighted = round(structure_score * 0.4 + center_score * 0.3 + stroke_order_score * 0.3, 1)
        if total_score == 0 and (structure_score > 0 or center_score > 0 or stroke_order_score > 0):
            total_score = weighted
        elif total_score > 0 and abs(total_score - weighted) >= 1.0:
            # 模型返回的 total 与加权相差 >=1 分，说明模型跑偏了 → 以加权为准
            logger.warning(
                "Qwen total_score(%.1f) deviates from weighted(%.1f), using weighted",
                total_score, weighted,
            )
            total_score = weighted

        # 标签白名单过滤
        tags = QwenEvaluationService._filter_tags(result.get("tags", []))

        advice = str(result.get("advice", "") or "")[:200]

        thinking_steps = result.get("thinking_steps", [])
        if not isinstance(thinking_steps, list):
            thinking_steps = []

        return QwenEvaluationResult(
            total_score=total_score,
            structure_score=structure_score,
            structure_observation=structure_observation,
            structure_suggestion=structure_suggestion,
            center_score=center_score,
            center_observation=center_observation,
            center_suggestion=center_suggestion,
            stroke_order_score=stroke_order_score,
            stroke_order_observation=stroke_order_observation,
            stroke_order_suggestion=stroke_order_suggestion,
            tags=tags,
            advice=advice,
            thinking_steps=thinking_steps,
            annotations=result.get("annotations", []),
        ).model_dump()

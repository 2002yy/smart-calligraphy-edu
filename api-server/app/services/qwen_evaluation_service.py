"""Qwen3.5-Plus 视觉书法评测服务

通过阿里云百炼 DashScope API（OpenAI 兼容模式）调用通义千问视觉模型，
对上传的书法作品图片进行结构、重心、笔画维度的智能评分。

API 文档: https://help.aliyun.com/zh/model-studio/developer-reference
计费: 约 ¥0.8/百万 Token，单次评测约 ¥0.001
开通: 阿里云百炼控制台 -> 模型广场 -> qwen3.5-plus -> 申请 API Key
模型 ID: qwen3.5-plus（全部小写）
"""

from __future__ import annotations

import base64
import json
import mimetypes
from io import BytesIO
from pathlib import Path

from fastapi import HTTPException

from app.core.config import settings

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None


class QwenEvaluationService:
    """调用阿里云百炼 DashScope（qwen3.5-plus 视觉模型）进行书法评分。"""

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
                        "1. 结构 (权重 40%)：间架结构是否合理，中宫是否收紧，横细竖粗特征是否体现，"
                        "主笔是否突出，疏密安排是否得当\n"
                        "2. 重心 (权重 30%)：整体重心是否平稳，左右是否平衡，首笔位置是否准确，"
                        "字是否站得稳、立得正\n"
                        "3. 笔顺 (权重 30%)：笔画顺序是否正确，运笔是否流畅，笔断意连是否体现\n\n"
                        "综合得分 = 结构×40% + 重心×30% + 笔顺×30%\n\n"
                        "【评语风格要求】\n"
                        "- 像真正的书法老师一样，先肯定优点，再指出问题，最后给出修改方向\n"
                        "- 使用专业的书法术语：如主笔、重心、扛肩、收放、疏密、布白、笔断意连等\n"
                        "- 观察和修改建议要具体到笔画层面，不能泛泛而谈\n"
                        "  例如不要说\"结构需要改进\"，而要说\"「永」字的撇捺角度过大，建议收紧15度\"\n"
                        "- 每个维度的修改建议要有可操作性，让学生知道具体怎么改\n\n"
                        "【输出要求】\n"
                        "必须返回严格的 JSON 对象，不要包含任何额外的文字说明。JSON 结构如下：\n"
                        "{\n"
                        '  "structure_score": <0-10 的整数或一位小数>,\n'
                        '  "structure_observation": "结构方面的具体观察，一句话",\n'
                        '  "structure_suggestion": "结构方面的具体修改建议，一句话",\n'
                        '  "center_score": <0-10 的整数或一位小数>,\n'
                        '  "center_observation": "重心方面的具体观察，一句话",\n'
                        '  "center_suggestion": "重心方面的具体修改建议，一句话",\n'
                        '  "stroke_order_score": <0-10 的整数或一位小数>,\n'
                        '  "stroke_order_observation": "笔顺方面的具体观察，一句话",\n'
                        '  "stroke_order_suggestion": "笔顺方面的具体修改建议，一句话",\n'
                        '  "total_score": <按权重计算后的总分>,\n'
                        '  "tags": ["标签1", "标签2", "标签3"],  // 2-4 个中文问题标签\n'
                        '  "advice": "综合练习建议，不超过120字，包括先扬后抑、具体可操作",\n'
                        '  "thinking_steps": [\n'
                        '    {"step": 1, "title": "图像预处理", "detail": "观察描述", "score": 分数},\n'
                        '    {"step": 2, "title": "文字区域检测", "detail": "检测到几个练习字区域", "score": 分数},\n'
                        '    {"step": 3, "title": "单字分割", "detail": "分割与对齐情况", "score": 分数},\n'
                        '    {"step": 4, "title": "结构分析", "detail": "结构稳定性的具体观察", "score": 分数},\n'
                        '    {"step": 5, "title": "重心检测", "detail": "重心位置的具体观察", "score": 分数},\n'
                        '    {"step": 6, "title": "笔顺验证", "detail": "笔顺的具体观察", "score": 分数},\n'
                        '    {"step": 7, "title": "综合评分", "detail": "最终评分的总结", "score": 总分}\n'
                        "  ]\n"
                        "}\n"
                        "注意：每个 step 都必须包含 step、title、detail、score 四个字段，score 不能省略。"
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
            "temperature": 0.3,
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
            content = body["choices"][0]["message"]["content"]
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
        if total_score == 0 and (structure_score > 0 or center_score > 0 or stroke_order_score > 0):
            total_score = round(structure_score * 0.4 + center_score * 0.3 + stroke_order_score * 0.3, 1)

        tags = result.get("tags", [])
        if not isinstance(tags, list):
            tags = []

        advice = str(result.get("advice", "") or "")[:200]

        thinking_steps = result.get("thinking_steps", [])
        if not isinstance(thinking_steps, list):
            thinking_steps = []

        return {
            "total_score": total_score,
            "structure_score": structure_score,
            "structure_observation": structure_observation,
            "structure_suggestion": structure_suggestion,
            "center_score": center_score,
            "center_observation": center_observation,
            "center_suggestion": center_suggestion,
            "stroke_order_score": stroke_order_score,
            "stroke_order_observation": stroke_order_observation,
            "stroke_order_suggestion": stroke_order_suggestion,
            "tags": tags,
            "advice": advice,
            "thinking_steps": thinking_steps,
        }

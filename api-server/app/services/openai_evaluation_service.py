from __future__ import annotations

import base64
import mimetypes
from io import BytesIO
from pathlib import Path

from fastapi import HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None


class ThinkingStepOutput(BaseModel):
    step: int = Field(ge=1, le=10)
    title: str = Field(min_length=1, max_length=30)
    detail: str = Field(min_length=1, max_length=200)
    score: float | None = None


class CalligraphyScoreOutput(BaseModel):
    score: float = Field(ge=0, le=100)
    tags: list[str] = Field(default_factory=list)
    advice: str = Field(min_length=1, max_length=120)
    thinking_steps: list[ThinkingStepOutput] = Field(default_factory=list)


class OpenAIEvaluationService:
    # DEPRECATED: kept for reference. Use QwenEvaluationService (qwen_evaluation_service.py) instead.
    @staticmethod
    def is_configured() -> bool:
        return bool(settings.openai_evaluation_enabled and settings.openai_api_key)

    @staticmethod
    def _get_client():
        if OpenAI is None:
            raise HTTPException(
                status_code=503,
                detail="OpenAI SDK not installed. Please run: pip install openai",
            )

        client_kwargs: dict[str, str] = {"api_key": settings.openai_api_key}
        if settings.openai_base_url:
            client_kwargs["base_url"] = settings.openai_base_url
        return OpenAI(**client_kwargs)

    @staticmethod
    def _prepare_image_bytes(image_path: Path) -> tuple[bytes, str]:
        raw_bytes = image_path.read_bytes()
        mime_type = mimetypes.guess_type(image_path.name)[0] or "image/jpeg"

        if Image is None or settings.openai_image_max_size <= 0:
            return raw_bytes, mime_type

        try:
            with Image.open(image_path) as image:
                if image.mode not in ("RGB", "L"):
                    image = image.convert("RGB")

                image.thumbnail((settings.openai_image_max_size, settings.openai_image_max_size))

                output = BytesIO()
                output_format = "PNG" if mime_type == "image/png" else "JPEG"
                save_kwargs = {"optimize": True}
                if output_format == "JPEG":
                    save_kwargs["quality"] = 88

                image.save(output, format=output_format, **save_kwargs)
                resized_bytes = output.getvalue()
                resized_mime = "image/png" if output_format == "PNG" else "image/jpeg"
                return resized_bytes, resized_mime
        except Exception:
            return raw_bytes, mime_type

    @staticmethod
    def score(image_path: Path, practice_chars: list[str] | None = None, task_title: str | None = None) -> CalligraphyScoreOutput:
        if not settings.openai_api_key:
            raise HTTPException(
                status_code=400,
                detail="OPENAI_API_KEY is missing. Please configure it before enabling OpenAI evaluation.",
            )

        if not image_path.exists():
            raise HTTPException(status_code=404, detail="homework image file not found")

        image_bytes, mime_type = OpenAIEvaluationService._prepare_image_bytes(image_path)
        encoded_image = base64.b64encode(image_bytes).decode("utf-8")
        data_url = f"data:{mime_type};base64,{encoded_image}"

        practice_text = ", ".join(practice_chars or []) or "not specified"
        task_text = task_title or "calligraphy homework"

        client = OpenAIEvaluationService._get_client()
        response = client.responses.parse(
            model=settings.openai_evaluation_model,
            input=[
                {
                    "role": "system",
                    "content": (
                        "You are a calligraphy evaluation assistant. "
                        "Analyze the work step by step across multiple dimensions. "
                        "For each step provide: step (number), title (short name), "
                        "detail (observation in one sentence), and score (0-100, optional). "
                        "Steps to cover: image preprocessing, character region detection, "
                        "character segmentation, structure analysis, center balance, "
                        "stroke completeness, and final scoring. "
                        "Finally provide the overall score, 2-4 short tags, "
                        "and one sentence of advice for the student. "
                        "Return only structured data."
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                f"Task title: {task_text}\n"
                                f"Practice characters: {practice_text}\n"
                                "Judge the uploaded work from structure stability, center balance, "
                                "and stroke completeness. Return a student-friendly result."
                            ),
                        },
                        {
                            "type": "input_image",
                            "image_url": data_url,
                            "detail": settings.openai_image_detail,
                        },
                    ],
                },
            ],
            text_format=CalligraphyScoreOutput,
        )

        for output in response.output:
            if output.type != "message":
                continue

            for item in output.content:
                if item.type == "refusal":
                    raise HTTPException(status_code=502, detail=f"OpenAI refused the evaluation request: {item.refusal}")

                parsed = getattr(item, "parsed", None)
                if parsed:
                    return parsed

        raise HTTPException(status_code=502, detail="OpenAI returned no structured evaluation result")

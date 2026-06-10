from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, computed_field


class EvaluationProvider(str, Enum):
    auto = "auto"
    mock = "mock"
    openai = "openai"  # DEPRECATED: kept for reference. Use qwen instead.
    qwen = "qwen"


class EvaluationRead(BaseModel):
    id: int
    homework_id: int
    score: float
    total_score: float
    structure_score: float
    center_score: float
    stroke_order_score: float

    @computed_field
    @property
    def stroke_quality_score(self) -> float:
        return self.stroke_order_score

    tags: list[str]
    issues: list[str]
    advice: str | None = None
    compare_image_url: str | None = None
    thinking_steps: list[dict] | None = None
    status: str = "finished"
    created_at: datetime | None = None
    calligraphy_images: list[str] = []

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "homework_id": 1,
                "score": 8.7,
                "total_score": 8.7,
                "structure_score": 8.8,
                "center_score": 8.5,
                "stroke_order_score": 8.6,
                "tags": ["结构工整", "重心稳当", "笔法到位"],
                "issues": ["结构工整", "重心稳当", "笔法到位"],
                "advice": "结构整体工整，重心略有偏移，建议加强中宫收紧练习。",
                "compare_image_url": None,
                "thinking_steps": None,
                "status": "finished",
                "created_at": "2026-04-12T10:25:00",
            }
        }
    )


class EvaluationStartRequest(BaseModel):
    homework_id: int
    provider: EvaluationProvider = EvaluationProvider.auto
    force_refresh: bool = False

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "homework_id": 1,
                "provider": "auto",
                "force_refresh": False,
            }
        }
    )


class EvaluationStartRead(BaseModel):
    status: str
    homework_id: int
    evaluation_id: int
    provider: EvaluationProvider

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "finished",
                "homework_id": 1,
                "evaluation_id": 1,
                "provider": "mock",
            }
        }
    )

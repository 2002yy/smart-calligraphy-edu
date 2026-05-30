from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TaskCreate(BaseModel):
    course_id: int
    class_id: int
    title: str
    description: str | None = None
    practice_chars: list[str]
    structure_weight: int = 40
    center_weight: int = 30
    stroke_order_weight: int = 30
    deadline: datetime | None = None
    created_by: int = 1

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "course_id": 1,
                "class_id": 1,
                "title": "Regular Script Drill",
                "description": "Practice balanced structure and clean stroke order",
                "practice_chars": ["yong", "da", "mu", "zhong"],
                "structure_weight": 40,
                "center_weight": 30,
                "stroke_order_weight": 30,
                "deadline": "2026-04-20T23:59:59",
                "created_by": 1,
            }
        }
    )


class TaskRead(BaseModel):
    id: int
    course_id: int
    class_id: int
    title: str
    description: str | None = None
    practice_chars: list[str] = Field(default_factory=list)
    structure_weight: int
    center_weight: int
    stroke_order_weight: int
    deadline: datetime | None = None
    created_by: int
    created_at: datetime | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "course_id": 1,
                "class_id": 1,
                "title": "Regular Script Drill",
                "description": "Practice balanced structure and clean stroke order",
                "practice_chars": ["yong", "da", "mu", "zhong"],
                "structure_weight": 40,
                "center_weight": 30,
                "stroke_order_weight": 30,
                "deadline": "2026-04-20T23:59:59",
                "created_by": 1,
                "created_at": "2026-04-12T10:00:00",
            }
        }
    )

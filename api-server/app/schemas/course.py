from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CourseCreate(BaseModel):
    name: str
    term: str
    description: str | None = None
    teacher_id: int = 1

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Smart Calligraphy Demo Course",
                "term": "2026-Spring",
                "description": "Foundation course for calligraphy practice demo",
                "teacher_id": 1,
            }
        }
    )


class CourseRead(BaseModel):
    id: int
    name: str
    term: str
    description: str | None = None
    teacher_id: int | None = None
    status: str | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "Smart Calligraphy Demo Course",
                "term": "2026-Spring",
                "description": "Foundation course for calligraphy practice demo",
                "teacher_id": 1,
                "status": "active",
                "created_at": "2026-04-12T10:00:00",
            }
        }
    )

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReviewCreate(BaseModel):
    homework_id: int
    teacher_id: int
    comment: str | None = None
    final_score: float | None = None
    status: str = "reviewed"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "homework_id": 1,
                "teacher_id": 1,
                "comment": "Overall structure is stable. Keep refining the horizontal stroke endings.",
                "final_score": 90,
                "status": "reviewed",
            }
        }
    )


class ReviewRead(BaseModel):
    id: int
    homework_id: int
    teacher_id: int
    student_id: int | None = None
    student_name: str | None = None
    task_id: int | None = None
    task_title: str | None = None
    homework_status: str | None = None
    image_url: str | None = None
    submitted_at: datetime | None = None
    comment: str | None = None
    final_score: float | None = None
    score: float | None = None
    tags: list[str] = []
    advice: str | None = None
    compare_image_url: str | None = None
    status: str
    reviewed_at: datetime | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "homework_id": 1,
                "teacher_id": 1,
                "student_id": 2,
                "student_name": "Student One",
                "task_id": 3,
                "task_title": "Basic Character Practice",
                "homework_status": "reviewed",
                "image_url": "/uploads/homework/2/1/demo.png",
                "submitted_at": "2026-04-12T10:20:00",
                "comment": "Overall structure is stable. Keep refining the horizontal stroke endings.",
                "final_score": 90,
                "score": 88.7,
                "tags": ["stable structure", "clear main stroke"],
                "advice": "Keep the main stroke stable and tighten the smaller side structure.",
                "compare_image_url": "/uploads/compare/demo-compare.png",
                "status": "reviewed",
                "reviewed_at": "2026-04-12T10:30:00",
            }
        }
    )

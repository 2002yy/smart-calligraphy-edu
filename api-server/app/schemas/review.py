from datetime import datetime

from pydantic import BaseModel, ConfigDict, computed_field


class ReviewCreate(BaseModel):
    homework_id: int
    teacher_id: int | None = None  # 路由层强制覆盖为 current_user["id"]
    comment: str | None = None
    final_score: float | None = None
    status: str = "reviewed"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "homework_id": 1,
                "comment": "结构整体稳定，横画起收笔还可以再打磨。",
                "final_score": 9.0,
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
    structure_score: float | None = None
    center_score: float | None = None
    stroke_order_score: float | None = None
    tags: list[str] = []
    advice: str | None = None
    compare_image_url: str | None = None
    thinking_steps: list[dict] | None = None
    status: str
    reviewed_at: datetime | None = None

    @computed_field
    @property
    def stroke_quality_score(self) -> float | None:
        return self.stroke_order_score

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "homework_id": 1,
                "teacher_id": 1,
                "student_id": 2,
                "student_name": "张三",
                "task_id": 3,
                "task_title": "欧楷基本笔画训练",
                "homework_status": "reviewed",
                "image_url": "/uploads/homework/2/1/demo.jpg",
                "submitted_at": "2026-04-12T10:20:00",
                "comment": "结构整体稳定，横画起收笔还可以再打磨。",
                "final_score": 9.0,
                "score": 8.7,
                "structure_score": 8.8,
                "center_score": 8.5,
                "stroke_order_score": 8.6,
                "tags": ["结构工整", "主笔突出"],
                "advice": "建议加强横画的起笔和收笔训练。",
                "compare_image_url": "/uploads/homework/2/1/demo_result.jpg",
                "status": "reviewed",
                "reviewed_at": "2026-04-12T10:30:00",
            }
        }
    )

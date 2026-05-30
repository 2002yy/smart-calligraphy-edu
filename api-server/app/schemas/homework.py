from datetime import datetime

from pydantic import BaseModel, ConfigDict


class HomeworkCreate(BaseModel):
    task_id: int
    student_id: int
    image_url: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task_id": 1,
                "student_id": 2,
                "image_url": "/uploads/homework/2/1/demo.png",
            }
        }
    )


class HomeworkSubmitRequest(BaseModel):
    homework_id: int | None = None
    task_id: int | None = None
    student_id: int | None = None
    image_url: str | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "homework_id": 1,
                "image_url": "/uploads/homework/2/1/demo.png",
            }
        }
    )


class HomeworkRead(BaseModel):
    id: int
    task_id: int
    student_id: int
    status: str
    image_url: str
    processed_image_url: str | None = None
    submitted_at: datetime | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "task_id": 1,
                "student_id": 2,
                "status": "submitted",
                "image_url": "/uploads/homework/2/1/demo.png",
                "processed_image_url": None,
                "submitted_at": "2026-04-12T10:20:00",
            }
        }
    )


class HomeworkUploadRead(BaseModel):
    homework_id: int
    file_url: str
    status: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "homework_id": 1,
                "file_url": "/uploads/homework/2/1/demo.png",
                "status": "uploaded",
            }
        }
    )

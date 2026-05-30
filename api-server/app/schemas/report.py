from datetime import datetime

from pydantic import BaseModel, ConfigDict


class StudentReportRead(BaseModel):
    student_id: int
    homework_count: int
    evaluated_count: int
    avg_score: float

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "student_id": 2,
                "homework_count": 4,
                "evaluated_count": 3,
                "avg_score": 88.6,
            }
        }
    )


class ClassReportRead(BaseModel):
    class_id: int
    student_count: int
    task_count: int
    homework_count: int
    evaluated_count: int
    avg_score: float

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "class_id": 1,
                "student_count": 30,
                "task_count": 4,
                "homework_count": 92,
                "evaluated_count": 80,
                "avg_score": 87.4,
            }
        }
    )


class ReportExportRequest(BaseModel):
    type: str
    target_id: int
    format: str = "pdf"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "student",
                "target_id": 2,
                "format": "pdf",
            }
        }
    )


class ReportExportRead(BaseModel):
    file_url: str
    generated_at: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "file_url": "/reports/student_2.pdf",
                "generated_at": "2026-04-12T10:45:00",
            }
        }
    )

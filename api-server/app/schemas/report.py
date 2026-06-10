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


class TagTrendRecord(BaseModel):
    """单次评测的标签记录。"""

    homework_id: int
    created_at: datetime
    score: float
    tags: list[str]


class FrequentIssueTag(BaseModel):
    """反复出现的问题标签统计。"""

    tag: str
    count: int


class ImprovedTag(BaseModel):
    """有改善趋势的标签。"""

    tag: str
    previous_count: int
    recent_count: int


class StudentTagTrendRead(BaseModel):
    """学生端成长档案标签趋势。"""

    student_id: int
    records: list[TagTrendRecord]
    frequent_issue_tags: list[FrequentIssueTag]
    improved_tags: list[ImprovedTag]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "student_id": 2,
                "records": [
                    {
                        "homework_id": 11,
                        "created_at": "2026-06-10T20:10:00",
                        "score": 7.2,
                        "tags": ["中宫松散", "重心偏左"],
                    },
                    {
                        "homework_id": 12,
                        "created_at": "2026-06-12T18:30:00",
                        "score": 8.1,
                        "tags": ["重心居中", "运笔流畅"],
                    },
                ],
                "frequent_issue_tags": [
                    {"tag": "中宫松散", "count": 4},
                    {"tag": "运笔生硬", "count": 3},
                ],
                "improved_tags": [
                    {"tag": "重心偏左", "previous_count": 3, "recent_count": 1},
                    {"tag": "运笔生硬", "previous_count": 2, "recent_count": 0},
                ],
            }
        }
    )

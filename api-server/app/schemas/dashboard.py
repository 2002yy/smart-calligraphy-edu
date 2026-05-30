from pydantic import BaseModel, ConfigDict


class DashboardRead(BaseModel):
    class_id: int
    class_name: str
    student_count: int
    task_count: int
    homework_count: int
    evaluated_count: int
    avg_score: float
    submit_rate: float
    top_issues: list[str]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "class_id": 1,
                "class_name": "Demo Class A",
                "student_count": 30,
                "task_count": 4,
                "homework_count": 92,
                "evaluated_count": 80,
                "avg_score": 87.4,
                "submit_rate": 0.77,
                "top_issues": ["center shifted left", "weak horizontal stroke", "tight structure"],
            }
        }
    )

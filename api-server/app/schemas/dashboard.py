from pydantic import BaseModel, ConfigDict


class TagStatItem(BaseModel):
    """单个标签的统计信息。"""

    tag: str
    category: str
    count: int
    ratio: float


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
    tag_stats: list[TagStatItem] = []
    top_issue_tags: list[str] = []
    top_positive_tags: list[str] = []

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "class_id": 1,
                "class_name": "Demo Class A",
                "student_count": 30,
                "task_count": 4,
                "homework_count": 92,
                "evaluated_count": 80,
                "avg_score": 8.7,
                "submit_rate": 0.77,
                "top_issues": ["中宫松散", "重心偏左", "横画不稳"],
                "tag_stats": [
                    {"tag": "中宫松散", "category": "structure", "count": 12, "ratio": 0.43},
                    {"tag": "重心偏左", "category": "center", "count": 8, "ratio": 0.29},
                    {"tag": "结构工整", "category": "structure", "count": 15, "ratio": 0.54},
                ],
                "top_issue_tags": ["中宫松散", "重心偏左", "横画不稳", "运笔生硬", "笔画无力"],
                "top_positive_tags": ["结构工整", "重心稳当", "笔法到位"],
            }
        }
    )

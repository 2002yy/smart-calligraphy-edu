from pydantic import BaseModel, ConfigDict


class UserRead(BaseModel):
    id: int
    name: str
    role: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 2,
                "name": "Student Zhang",
                "role": "student",
            }
        }
    )


class GrowthRead(BaseModel):
    user_id: int
    avg_score: float
    recent_scores: list[float] = []
    recent_labels: list[str] = []

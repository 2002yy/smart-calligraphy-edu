from pydantic import BaseModel, ConfigDict

from app.schemas.user import UserRead


class ClassCreate(BaseModel):
    course_id: int
    name: str
    invite_code: str | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "course_id": 1,
                "name": "Demo Class A",
                "invite_code": "CALLI2026",
            }
        }
    )


class ClassRead(BaseModel):
    id: int
    course_id: int
    name: str
    invite_code: str | None = None
    student_count: int = 0

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "course_id": 1,
                "name": "Demo Class A",
                "invite_code": "CALLI2026",
                "student_count": 1,
            }
        }
    )


class ClassJoinRequest(BaseModel):
    invite_code: str
    # student_id 不再从前端传入，路由层强制使用 current_user["id"]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "invite_code": "CALLI2026",
            }
        }
    )


class ClassJoinRead(BaseModel):
    class_id: int
    student_id: int
    status: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "class_id": 1,
                "student_id": 2,
                "status": "joined",
            }
        }
    )


class ClassMembersRead(BaseModel):
    class_id: int
    members: list[UserRead]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "class_id": 1,
                "members": [
                    {"id": 2, "name": "Student Zhang", "role": "student"},
                    {"id": 3, "name": "Student Li", "role": "student"},
                ],
            }
        }
    )

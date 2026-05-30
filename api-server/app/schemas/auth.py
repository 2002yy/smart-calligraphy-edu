from pydantic import BaseModel, ConfigDict


class LoginRequest(BaseModel):
    username: str
    password: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "teacher01",
                "password": "123456",
            }
        }
    )


class CurrentUserRead(BaseModel):
    id: int
    username: str
    name: str
    role: str
    school_name: str | None = None
    avatar_url: str | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "username": "teacher01",
                "name": "Teacher Liu",
                "role": "teacher",
                "school_name": "Sichuan University",
                "avatar_url": None,
            }
        }
    )


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400
    user: CurrentUserRead

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "dev-token-1",
                "token_type": "bearer",
                "expires_in": 86400,
                "user": {
                    "id": 1,
                    "username": "teacher01",
                    "name": "Teacher Liu",
                    "role": "teacher",
                    "school_name": "Sichuan University",
                    "avatar_url": None,
                },
            }
        }
    )

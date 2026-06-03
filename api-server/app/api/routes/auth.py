from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.auth import CurrentUserRead, LoginRequest, LoginResponse
from app.schemas.common import APIResponse
from app.services.auth_service import AuthService, get_current_user

router = APIRouter()


@router.post(
    "/login",
    response_model=APIResponse[LoginResponse],
    summary="用户登录",
    description="支持教师与学生账号登录，返回签名 Bearer Token 和当前用户信息。",
)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    data = LoginResponse(**AuthService.login(db, payload))
    return APIResponse[LoginResponse](data=data)


@router.get(
    "/me",
    response_model=APIResponse[CurrentUserRead],
    summary="获取当前用户信息",
)
def me(current_user: dict = Depends(get_current_user)):
    data = CurrentUserRead(**current_user)
    return APIResponse[CurrentUserRead](data=data)

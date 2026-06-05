from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import APIResponse
from app.schemas.user import GrowthRead, UserRead
from app.services import UserService
from app.services.auth_service import get_current_user
from app.services.auth_service import get_current_user

router = APIRouter()


@router.get(
    "/{user_id}",
    response_model=APIResponse[UserRead],
    summary="获取用户信息",
)
def get_user(user_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    data = UserRead(**UserService.get_user(db, user_id, current_user))
    return APIResponse[UserRead](data=data)


@router.get(
    "/{user_id}/growth",
    response_model=APIResponse[GrowthRead],
    summary="获取学生成长数据",
)
def get_growth(user_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    data = GrowthRead(**UserService.get_growth(db, user_id, current_user))
    return APIResponse[GrowthRead](data=data)

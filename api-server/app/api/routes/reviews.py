from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import APIResponse
from app.schemas.review import ReviewCreate, ReviewRead
from app.services import ReviewService
from app.services.auth_service import require_role
from app.services.permission_service import assert_owns_course, assert_owns_homework

router = APIRouter()


@router.get(
    "",
    response_model=APIResponse[list[ReviewRead]],
    summary="获取教师批阅列表",
    description="支持按教师或作业筛选，方便教师端批阅记录页联调。",
)
def list_reviews(
    teacher_id: int | None = None,
    homework_id: int | None = None,
    current_user: dict = Depends(require_role(["teacher"])),
    db: Session = Depends(get_db),
):
    data = [ReviewRead(**item) for item in ReviewService.list_reviews(db, teacher_id=current_user["id"], homework_id=homework_id)]
    return APIResponse[list[ReviewRead]](data=data)


@router.post(
    "",
    response_model=APIResponse[ReviewRead],
    summary="提交教师批阅",
    description="教师可录入评语与最终得分；若该作业已有批阅记录，则本接口执行更新。",
)
def submit_review(payload: ReviewCreate, current_user: dict = Depends(require_role(["teacher"])), db: Session = Depends(get_db)):
    assert_owns_homework(db, current_user, payload.homework_id)
    data = ReviewRead(**ReviewService.create_review(db, payload))
    return APIResponse[ReviewRead](data=data)


@router.get(
    "/{homework_id}",
    response_model=APIResponse[ReviewRead],
    summary="获取作业批阅详情",
)
def get_review(homework_id: int, current_user: dict = Depends(require_role(["teacher"])), db: Session = Depends(get_db)):
    assert_owns_homework(db, current_user, homework_id)
    data = ReviewRead(**ReviewService.get_review(db, homework_id))
    return APIResponse[ReviewRead](data=data)

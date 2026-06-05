from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import APIResponse
from app.schemas.evaluation import EvaluationRead, EvaluationStartRead, EvaluationStartRequest
from app.repositories import HomeworkRepository
from app.services import EvaluationService
from app.services.auth_service import get_current_user, require_role

router = APIRouter()


@router.get(
    "/providers",
    summary="获取可用评测提供方",
    description="返回各评测提供方的可用状态，前端据此切换按钮文案。",
)
def list_providers():
    return APIResponse(data=EvaluationService.get_providers())


@router.post(
    "/start",
    response_model=APIResponse[EvaluationStartRead],
    summary="Start evaluation",
    description="Trigger evaluation for one homework item. Supports mock and OpenAI providers.",
)
def start_evaluation(payload: EvaluationStartRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    # student 只能评测自己的作业
    if current_user["role"] == "student":
        hw = HomeworkRepository.get_by_id(db, payload.homework_id)
        if not hw or hw.student_id != current_user["id"]:
            raise HTTPException(status_code=403, detail="学生只能评测自己的作业")
    data = EvaluationStartRead(
        **EvaluationService.start(
            db,
            payload.homework_id,
            provider=payload.provider,
            force_refresh=payload.force_refresh,
        )
    )
    return APIResponse[EvaluationStartRead](data=data)


@router.get(
    "/{homework_id}",
    response_model=APIResponse[EvaluationRead],
    summary="Get evaluation result",
)
def get_evaluation(homework_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    # student 只能看自己的评测
    if current_user["role"] == "student":
        hw = HomeworkRepository.get_by_id(db, homework_id)
        if not hw or hw.student_id != current_user["id"]:
            raise HTTPException(status_code=403, detail="学生只能查看自己作业的评测")
    data = EvaluationRead(**EvaluationService.get(db, homework_id))
    return APIResponse[EvaluationRead](data=data)

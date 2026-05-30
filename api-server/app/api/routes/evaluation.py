from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import APIResponse
from app.schemas.evaluation import EvaluationRead, EvaluationStartRead, EvaluationStartRequest
from app.services import EvaluationService

router = APIRouter()


@router.post(
    "/start",
    response_model=APIResponse[EvaluationStartRead],
    summary="Start evaluation",
    description="Trigger evaluation for one homework item. Supports mock and OpenAI providers.",
)
def start_evaluation(payload: EvaluationStartRequest, db: Session = Depends(get_db)):
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
def get_evaluation(homework_id: int, db: Session = Depends(get_db)):
    data = EvaluationRead(**EvaluationService.get(db, homework_id))
    return APIResponse[EvaluationRead](data=data)

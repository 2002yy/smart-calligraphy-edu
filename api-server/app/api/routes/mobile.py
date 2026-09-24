import io
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories import ClassMemberRepository, ClassroomRepository, TaskRepository
from app.schemas.auth import CurrentUserRead, LoginRequest, LoginResponse
from app.schemas.common import APIResponse
from app.schemas.evaluation import EvaluationProvider
from app.schemas.homework import HomeworkRead, HomeworkSubmitRequest
from app.schemas.task import TaskRead
from app.schemas.user import GrowthRead
from app.services import ClassService, EvaluationService, HomeworkService, TaskService, UserService
from app.services.auth_service import AuthService, get_current_user
from app.services.permission_service import assert_owns_homework, assert_student

try:
    from PIL import Image
except ImportError:
    Image = None


router = APIRouter()

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024


class MobileJoinClassRequest(BaseModel):
    invite_code: str


def _assert_mobile_student(db: Session, current_user: dict) -> None:
    assert_student(db, current_user)


def _ensure_task_visible_to_student(db: Session, task_id: int, student_id: int) -> None:
    task = TaskRepository.get_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    if not ClassMemberRepository.get_member(db, task.class_id, student_id):
        raise HTTPException(status_code=403, detail="student has not joined this class")


def _score_level(score: float) -> str:
    if score >= 90:
        return "优秀"
    if score >= 80:
        return "良好"
    if score >= 60:
        return "合格"
    return "待加强"


def _format_mobile_result(evaluation: dict, homework: dict | None = None) -> dict:
    score = round(float(evaluation.get("total_score") or evaluation.get("score") or 0) * 10)
    detail_items = [
        ("结构", evaluation.get("structure_score"), "观察字形比例、部件位置和整体稳定性。"),
        ("重心", evaluation.get("center_score"), "观察整体重心是否居中、上下左右是否协调。"),
        ("笔法", evaluation.get("stroke_order_score"), "观察起收笔、行笔和笔画质量。"),
    ]
    return {
        "homework_id": evaluation.get("homework_id"),
        "score": score,
        "level": _score_level(score),
        "summary": evaluation.get("advice") or "本次作品已完成 AI 评分，请根据细项建议继续练习。",
        "details": [
            {
                "name": name,
                "score": round(float(value or 0) * 10),
                "comment": comment,
            }
            for name, value, comment in detail_items
        ],
        "tags": evaluation.get("tags", []),
        "image_url": evaluation.get("compare_image_url") or (homework or {}).get("image_url"),
        "status": evaluation.get("status", "finished"),
        "created_at": evaluation.get("created_at"),
    }


@router.post("/login", response_model=APIResponse[LoginResponse], summary="Mobile student login")
def mobile_login(payload: LoginRequest, db: Session = Depends(get_db)):
    data = AuthService.login(db, payload)
    if data["user"]["role"] != "student":
        raise HTTPException(status_code=403, detail="mobile login only supports student accounts")
    return APIResponse[LoginResponse](data=LoginResponse(**data))


@router.get("/me", response_model=APIResponse[CurrentUserRead], summary="Mobile current student")
def mobile_me(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    _assert_mobile_student(db, current_user)
    return APIResponse[CurrentUserRead](data=CurrentUserRead(**current_user))


@router.post("/classes/join", response_model=APIResponse[dict], summary="Mobile join class by invite code")
def mobile_join_class(
    payload: MobileJoinClassRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _assert_mobile_student(db, current_user)
    invite_code = payload.invite_code.strip()
    if not invite_code:
        raise HTTPException(status_code=400, detail="invite_code is required")

    classroom = ClassroomRepository.get_by_invite_code(db, invite_code)
    if not classroom:
        raise HTTPException(status_code=404, detail="class invite code not found")

    data = ClassService.join_class(db, classroom.id, current_user["id"], invite_code)
    return APIResponse[dict](data={**data, "class_name": classroom.name})


@router.get("/tasks", response_model=APIResponse[list[TaskRead]], summary="Mobile task list")
def mobile_list_tasks(
    class_id: int | None = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _assert_mobile_student(db, current_user)
    if class_id is not None and not ClassMemberRepository.get_member(db, class_id, current_user["id"]):
        raise HTTPException(status_code=403, detail="student has not joined this class")

    if class_id is not None:
        tasks = TaskService.list_tasks(db, class_id=class_id)
    else:
        class_ids = [member.class_id for member in ClassMemberRepository.list_by_student(db, current_user["id"])]
        tasks = []
        for joined_class_id in class_ids:
            tasks.extend(TaskService.list_tasks(db, class_id=joined_class_id))
    return APIResponse[list[TaskRead]](data=[TaskRead(**item) for item in tasks])


@router.get("/tasks/{task_id}", response_model=APIResponse[TaskRead], summary="Mobile task detail")
def mobile_get_task(task_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    _assert_mobile_student(db, current_user)
    _ensure_task_visible_to_student(db, task_id, current_user["id"])
    return APIResponse[TaskRead](data=TaskRead(**TaskService.get_task(db, task_id)))


@router.post("/submissions", response_model=APIResponse[HomeworkRead], summary="Mobile upload and submit homework")
def mobile_submit_homework(
    task_id: int = Form(...),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _assert_mobile_student(db, current_user)
    _ensure_task_visible_to_student(db, task_id, current_user["id"])

    suffix = (Path(file.filename) if file.filename else Path("")).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(status_code=400, detail=f"unsupported file suffix: {suffix}")
    if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail=f"unsupported content type: {file.content_type}")

    file_bytes = file.file.read()
    if len(file_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="image must be 5MB or smaller")

    if Image is not None:
        try:
            image = Image.open(io.BytesIO(file_bytes))
            image.verify()
        except Exception:
            raise HTTPException(status_code=400, detail="file is not a valid image")

    uploaded = HomeworkService.upload_homework(db, task_id, current_user["id"], file.filename or "homework.png", file_bytes)
    submitted = HomeworkService.submit_homework(
        db,
        HomeworkSubmitRequest(homework_id=uploaded["homework_id"], task_id=task_id, image_url=uploaded["file_url"]),
        current_user,
    )
    return APIResponse[HomeworkRead](data=HomeworkRead(**submitted))


@router.post("/submissions/{homework_id}/evaluate", response_model=APIResponse[dict], summary="Mobile start evaluation")
def mobile_start_evaluation(
    homework_id: int,
    provider: EvaluationProvider = EvaluationProvider.auto,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _assert_mobile_student(db, current_user)
    assert_owns_homework(db, current_user, homework_id)
    data = EvaluationService.start(db, homework_id, provider=provider, force_refresh=True)
    return APIResponse[dict](data=data)


@router.get("/submissions/{homework_id}/result", response_model=APIResponse[dict], summary="Mobile evaluation result")
def mobile_get_result(homework_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    _assert_mobile_student(db, current_user)
    assert_owns_homework(db, current_user, homework_id)
    homework = HomeworkService.get_homework(db, homework_id)
    evaluation = EvaluationService.get(db, homework_id)
    return APIResponse[dict](data=_format_mobile_result(evaluation, homework))


@router.get("/submissions", response_model=APIResponse[list[HomeworkRead]], summary="Mobile submission history")
def mobile_list_submissions(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    _assert_mobile_student(db, current_user)
    data = HomeworkService.list_homework(db, student_id=current_user["id"])
    return APIResponse[list[HomeworkRead]](data=[HomeworkRead(**item) for item in data])


@router.get("/profile/progress", response_model=APIResponse[GrowthRead], summary="Mobile profile progress")
def mobile_profile_progress(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    _assert_mobile_student(db, current_user)
    data = UserService.get_growth(db, current_user["id"], current_user)
    return APIResponse[GrowthRead](data=GrowthRead(**data))

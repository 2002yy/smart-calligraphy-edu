import io
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import APIResponse
from app.schemas.homework import HomeworkRead, HomeworkSubmitRequest, HomeworkUploadRead
from app.repositories import TaskRepository
from app.services import HomeworkService
from app.services.auth_service import get_current_user
from app.services.permission_service import assert_owns_class, assert_owns_homework, assert_student
from app.repositories import TaskRepository

try:
    from PIL import Image
except ImportError:
    Image = None

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024

router = APIRouter()


@router.post(
    "/upload",
    response_model=APIResponse[HomeworkUploadRead],
    summary="Upload homework image",
    description="Upload one homework image and save it locally for later evaluation.",
)
def upload_homework(
    task_id: int = Form(...),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    assert_student(db, current_user)
    student_id = current_user["id"]
    # 校验文件类型
    suffix = (Path(file.filename) if file.filename else Path("")).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式：{suffix}，仅支持 {ALLOWED_SUFFIXES}")
    if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail=f"不支持的 MIME 类型：{file.content_type}")

    # 校验文件大小
    file_bytes = file.file.read()
    if len(file_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail=f"文件过大（最大 {MAX_UPLOAD_BYTES//1024//1024}MB）")

    # 验证图像有效性
    if Image is not None:
        try:
            img = Image.open(io.BytesIO(file_bytes))
            img.verify()
        except Exception:
            raise HTTPException(status_code=400, detail="文件不是有效的图片，请重新选择")

    data = HomeworkUploadRead(**HomeworkService.upload_homework(db, task_id, student_id, file.filename, file_bytes))
    return APIResponse[HomeworkUploadRead](data=data)


@router.post(
    "",
    response_model=APIResponse[HomeworkRead],
    summary="Submit homework",
    description="Submit a homework record or finalize a previously uploaded homework item.",
)
def submit_homework(payload: HomeworkSubmitRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.homework_id:
        assert_owns_homework(db, current_user, payload.homework_id)
    if current_user["role"] == "student":
        payload.student_id = current_user["id"]
    data = HomeworkRead(**HomeworkService.submit_homework(db, payload, current_user))
    return APIResponse[HomeworkRead](data=data)


@router.get(
    "",
    response_model=APIResponse[list[HomeworkRead]],
    summary="List homework",
    description="支持按 class_id、task_id、status、tag 筛选。教师必须传 class_id 以限定班级范围。",
)
def list_homework(
    class_id: int | None = None,
    task_id: int | None = None,
    status: str | None = None,
    tag: str | None = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user["role"] == "teacher":
        # 教师必须指定班级
        if class_id is None:
            raise HTTPException(status_code=400, detail="teacher list homework requires class_id")
        assert_owns_class(db, current_user, class_id)
        tasks = TaskRepository.list_tasks(db, class_id=class_id)
        task_ids = [t.id for t in tasks]
        data = [
            HomeworkRead(**item)
            for item in HomeworkService.list_homework(db, task_ids=task_ids, task_id=task_id, status=status, tag=tag)
        ]
    else:
        # 学生只能看自己的作业
        student_id = current_user["id"]
        data = [
            HomeworkRead(**item)
            for item in HomeworkService.list_homework(db, student_id=student_id, task_id=task_id, status=status, tag=tag)
        ]
    return APIResponse[list[HomeworkRead]](data=data)


@router.get(
    "/{homework_id}",
    response_model=APIResponse[HomeworkRead],
    summary="Get homework detail",
)
def get_homework(homework_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    assert_owns_homework(db, current_user, homework_id)
    data = HomeworkRead(**HomeworkService.get_homework(db, homework_id))
    return APIResponse[HomeworkRead](data=data)

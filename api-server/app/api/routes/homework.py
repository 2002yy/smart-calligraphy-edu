import io
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import APIResponse
from app.schemas.homework import HomeworkRead, HomeworkSubmitRequest, HomeworkUploadRead
from app.services import HomeworkService
from app.services.auth_service import get_current_user

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
    student_id = current_user["id"]
    if current_user["role"] != "student":
        raise HTTPException(status_code=403, detail="仅学生可以上传作业")
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
    if current_user["role"] == "student" and payload.student_id is not None and payload.student_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="学生只能提交自己的作业")
    if current_user["role"] == "student" and payload.student_id is None:
        payload.student_id = current_user["id"]
    data = HomeworkRead(**HomeworkService.submit_homework(db, payload))
    return APIResponse[HomeworkRead](data=data)


@router.get(
    "",
    response_model=APIResponse[list[HomeworkRead]],
    summary="List homework",
)
def list_homework(
    task_id: int | None = None,
    status: str | None = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    student_id = current_user["id"] if current_user["role"] == "student" else None
    data = [
        HomeworkRead(**item)
        for item in HomeworkService.list_homework(db, task_id=task_id, student_id=student_id, status=status)
    ]
    data = [HomeworkRead(**item) for item in HomeworkService.list_homework(db, task_id=task_id, student_id=student_id, status=status)]
    return APIResponse[list[HomeworkRead]](data=data)


@router.get(
    "/{homework_id}",
    response_model=APIResponse[HomeworkRead],
    summary="Get homework detail",
)
def get_homework(homework_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    hw = HomeworkService.get_homework(db, homework_id)
    if current_user["role"] == "student" and current_user["id"] != hw["student_id"]:
        raise HTTPException(status_code=403, detail="学生只能查看自己的作业")
    data = HomeworkRead(**hw)
    return APIResponse[HomeworkRead](data=data)

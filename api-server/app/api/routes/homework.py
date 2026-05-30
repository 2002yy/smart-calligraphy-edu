from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import APIResponse
from app.schemas.homework import HomeworkRead, HomeworkSubmitRequest, HomeworkUploadRead
from app.services import HomeworkService

router = APIRouter()


@router.post(
    "/upload",
    response_model=APIResponse[HomeworkUploadRead],
    summary="Upload homework image",
    description="Upload one homework image and save it locally for later evaluation.",
)
def upload_homework(
    task_id: int = Form(...),
    student_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    file_bytes = file.file.read()
    data = HomeworkUploadRead(**HomeworkService.upload_homework(db, task_id, student_id, file.filename, file_bytes))
    return APIResponse[HomeworkUploadRead](data=data)


@router.post(
    "",
    response_model=APIResponse[HomeworkRead],
    summary="Submit homework",
    description="Submit a homework record or finalize a previously uploaded homework item.",
)
def submit_homework(payload: HomeworkSubmitRequest, db: Session = Depends(get_db)):
    data = HomeworkRead(**HomeworkService.submit_homework(db, payload))
    return APIResponse[HomeworkRead](data=data)


@router.get(
    "",
    response_model=APIResponse[list[HomeworkRead]],
    summary="List homework",
)
def list_homework(
    task_id: int | None = None,
    student_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    data = [
        HomeworkRead(**item)
        for item in HomeworkService.list_homework(db, task_id=task_id, student_id=student_id, status=status)
    ]
    return APIResponse[list[HomeworkRead]](data=data)


@router.get(
    "/{homework_id}",
    response_model=APIResponse[HomeworkRead],
    summary="Get homework detail",
)
def get_homework(homework_id: int, db: Session = Depends(get_db)):
    data = HomeworkRead(**HomeworkService.get_homework(db, homework_id))
    return APIResponse[HomeworkRead](data=data)

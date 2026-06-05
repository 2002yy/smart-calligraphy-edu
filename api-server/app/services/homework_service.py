from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories import HomeworkRepository, TaskRepository, UserRepository
from app.schemas.homework import HomeworkSubmitRequest
from app.services.file_storage_service import FileStorageService


class HomeworkService:
    @staticmethod
    def _serialize(homework) -> dict:
        return {
            "id": homework.id,
            "task_id": homework.task_id,
            "student_id": homework.student_id,
            "status": homework.status,
            "image_url": homework.image_url,
            "processed_image_url": homework.processed_image_url,
            "submitted_at": homework.submitted_at,
        }

    @staticmethod
    def upload_homework(db: Session, task_id: int, student_id: int, filename: str, file_bytes: bytes) -> dict:
        task = TaskRepository.get_by_id(db, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="task not found")

        student = UserRepository.get_by_id(db, student_id)
        if not student:
            raise HTTPException(status_code=404, detail="student not found")

        file_url, _ = FileStorageService.save_homework_image(task_id, student_id, filename, file_bytes)
        homework = HomeworkRepository.create_homework(
            db,
            task_id=task_id,
            student_id=student_id,
            image_url=file_url,
            status="uploaded",
        )
        return {
            "homework_id": homework.id,
            "file_url": file_url,
            "status": homework.status,
        }

    @staticmethod
    def submit_homework(db: Session, payload: HomeworkSubmitRequest, current_user: dict | None = None) -> dict:
        if payload.homework_id is not None:
            homework = HomeworkRepository.get_by_id(db, payload.homework_id)
            if not homework:
                raise HTTPException(status_code=404, detail="homework not found")
            if payload.image_url:
                homework.image_url = payload.image_url
            homework.status = "submitted"
            homework = HomeworkRepository.update_homework(db, homework)
            return HomeworkService._serialize(homework)

        if payload.task_id is None or payload.student_id is None or not payload.image_url:
            raise HTTPException(status_code=400, detail="task_id, student_id and image_url are required")

        task = TaskRepository.get_by_id(db, payload.task_id)
        if not task:
            raise HTTPException(status_code=404, detail="task not found")

        student = UserRepository.get_by_id(db, payload.student_id)
        if not student:
            raise HTTPException(status_code=404, detail="student not found")

        homework = HomeworkRepository.create_homework(
            db,
            task_id=payload.task_id,
            student_id=payload.student_id,
            image_url=payload.image_url,
            status="submitted",
        )
        return HomeworkService._serialize(homework)

    @staticmethod
    def list_homework(
        db: Session,
        task_id: int | None = None,
        student_id: int | None = None,
        status: str | None = None,
    ) -> list[dict]:
        items = HomeworkRepository.list_homework(db, task_id=task_id, student_id=student_id, status=status)
        return [HomeworkService._serialize(item) for item in items]

    @staticmethod
    def get_homework(db: Session, homework_id: int) -> dict:
        homework = HomeworkRepository.get_by_id(db, homework_id)
        if not homework:
            raise HTTPException(status_code=404, detail="homework not found")
        return HomeworkService._serialize(homework)

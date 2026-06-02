from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories import ClassroomRepository, CourseRepository, TaskRepository, UserRepository
from app.schemas.task import TaskCreate


class TaskService:
    @staticmethod
    def _serialize(db: Session, task) -> dict:
        practice_chars = [item.character for item in TaskRepository.list_characters(db, task.id)]
        return {
            "id": task.id,
            "course_id": task.course_id,
            "class_id": task.class_id,
            "title": task.title,
            "description": task.description,
            "practice_chars": practice_chars,
            "structure_weight": task.structure_weight,
            "center_weight": task.center_weight,
            "stroke_order_weight": task.stroke_order_weight,
            "deadline": task.deadline,
            "created_by": task.created_by,
            "created_at": task.created_at,
        }

    @staticmethod
    def list_tasks(db: Session, class_id: int | None = None, course_id: int | None = None) -> list[dict]:
        tasks = TaskRepository.list_tasks(db, class_id=class_id, course_id=course_id)
        return [TaskService._serialize(db, task) for task in tasks]

    @staticmethod
    def create_task(db: Session, payload: TaskCreate) -> dict:
        weight_sum = payload.structure_weight + payload.center_weight + payload.stroke_order_weight
        if weight_sum != 100:
            raise HTTPException(status_code=400, detail="weight sum must equal 100")

        course = CourseRepository.get_by_id(db, payload.course_id)
        if not course:
            raise HTTPException(status_code=404, detail="course not found")

        classroom = ClassroomRepository.get_by_id(db, payload.class_id)
        if not classroom:
            raise HTTPException(status_code=404, detail="class not found")
        if classroom.course_id != payload.course_id:
            raise HTTPException(status_code=400, detail="class does not belong to course")

        creator = UserRepository.get_by_id(db, payload.created_by)
        if not creator:
            raise HTTPException(status_code=404, detail="creator not found")

        task = TaskRepository.create_task(
            db,
            course_id=payload.course_id,
            class_id=payload.class_id,
            title=payload.title,
            description=payload.description,
            structure_weight=payload.structure_weight,
            center_weight=payload.center_weight,
            stroke_order_weight=payload.stroke_order_weight,
            deadline=payload.deadline,
            created_by=payload.created_by,
            practice_chars=payload.practice_chars,
        )
        return TaskService._serialize(db, task)

    @staticmethod
    def get_task(db: Session, task_id: int) -> dict:
        task = TaskRepository.get_by_id(db, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="task not found")
        return TaskService._serialize(db, task)

    @staticmethod
    def delete_task(db: Session, task_id: int) -> None:
        task = TaskRepository.get_by_id(db, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="task not found")
        TaskRepository.delete_task(db, task_id)

from datetime import datetime

from sqlalchemy import delete as sa_delete, select
from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.task_character import TaskCharacter


class TaskRepository:
    @staticmethod
    def list_tasks(db: Session, class_id: int | None = None, course_id: int | None = None) -> list[Task]:
        stmt = select(Task).order_by(Task.id.desc())
        if class_id is not None:
            stmt = stmt.where(Task.class_id == class_id)
        if course_id is not None:
            stmt = stmt.where(Task.course_id == course_id)
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_by_id(db: Session, task_id: int) -> Task | None:
        return db.get(Task, task_id)

    @staticmethod
    def list_characters(db: Session, task_id: int) -> list[TaskCharacter]:
        stmt = (
            select(TaskCharacter)
            .where(TaskCharacter.task_id == task_id)
            .order_by(TaskCharacter.sort_order.asc(), TaskCharacter.id.asc())
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def create_task(
        db: Session,
        *,
        course_id: int,
        class_id: int,
        title: str,
        description: str | None,
        structure_weight: int,
        center_weight: int,
        stroke_order_weight: int,
        deadline: datetime | None,
        created_by: int,
        practice_chars: list[str],
    ) -> Task:
        task = Task(
            course_id=course_id,
            class_id=class_id,
            title=title,
            description=description,
            structure_weight=structure_weight,
            center_weight=center_weight,
            stroke_order_weight=stroke_order_weight,
            deadline=deadline,
            created_by=created_by,
        )
        db.add(task)
        db.flush()

        db.add_all(
            [
                TaskCharacter(task_id=task.id, character=char, sort_order=index + 1)
                for index, char in enumerate(practice_chars)
            ]
        )

        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def delete_task(db: Session, task_id: int) -> None:
        # 先删关联的练习字
        db.execute(sa_delete(TaskCharacter).where(TaskCharacter.task_id == task_id))
        # 再删任务
        task = db.get(Task, task_id)
        if task:
            db.delete(task)
        db.commit()

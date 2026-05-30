from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.homework import Homework


class HomeworkRepository:
    @staticmethod
    def get_by_id(db: Session, homework_id: int) -> Homework | None:
        return db.get(Homework, homework_id)

    @staticmethod
    def list_homework(
        db: Session,
        task_id: int | None = None,
        student_id: int | None = None,
        task_ids: list[int] | None = None,
        status: str | None = None,
    ) -> list[Homework]:
        stmt = select(Homework).order_by(Homework.id.desc())
        if task_id is not None:
            stmt = stmt.where(Homework.task_id == task_id)
        if task_ids:
            stmt = stmt.where(Homework.task_id.in_(task_ids))
        if student_id is not None:
            stmt = stmt.where(Homework.student_id == student_id)
        if status is not None:
            stmt = stmt.where(Homework.status == status)
        return list(db.scalars(stmt).all())

    @staticmethod
    def create_homework(
        db: Session,
        *,
        task_id: int,
        student_id: int,
        image_url: str,
        status: str,
    ) -> Homework:
        homework = Homework(
            task_id=task_id,
            student_id=student_id,
            image_url=image_url,
            status=status,
        )
        db.add(homework)
        db.commit()
        db.refresh(homework)
        return homework

    @staticmethod
    def update_homework(db: Session, homework: Homework) -> Homework:
        db.add(homework)
        db.commit()
        db.refresh(homework)
        return homework

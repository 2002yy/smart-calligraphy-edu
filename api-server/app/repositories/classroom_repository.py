from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.classroom import Classroom


class ClassroomRepository:
    @staticmethod
    def list_classes(db: Session, course_id: int | None = None) -> list[Classroom]:
        stmt = select(Classroom).order_by(Classroom.id.desc())
        if course_id is not None:
            stmt = stmt.where(Classroom.course_id == course_id)
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_by_id(db: Session, class_id: int) -> Classroom | None:
        return db.get(Classroom, class_id)

    @staticmethod
    def get_by_invite_code(db: Session, invite_code: str) -> Classroom | None:
        stmt = select(Classroom).where(Classroom.invite_code == invite_code)
        return db.scalar(stmt)

    @staticmethod
    def create_class(
        db: Session,
        *,
        course_id: int,
        name: str,
        invite_code: str,
    ) -> Classroom:
        classroom = Classroom(course_id=course_id, name=name, invite_code=invite_code, student_count=0)
        db.add(classroom)
        db.commit()
        db.refresh(classroom)
        return classroom

    @staticmethod
    def update_class(db: Session, classroom: Classroom) -> Classroom:
        db.add(classroom)
        db.commit()
        db.refresh(classroom)
        return classroom

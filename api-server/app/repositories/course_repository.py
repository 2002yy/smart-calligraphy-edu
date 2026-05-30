from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.course import Course


class CourseRepository:
    @staticmethod
    def list_courses(
        db: Session,
        teacher_id: int | None = None,
        status: str | None = None,
    ) -> list[Course]:
        stmt = select(Course).order_by(Course.id.desc())
        if teacher_id is not None:
            stmt = stmt.where(Course.teacher_id == teacher_id)
        if status is not None:
            stmt = stmt.where(Course.status == status)
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_by_id(db: Session, course_id: int) -> Course | None:
        return db.get(Course, course_id)

    @staticmethod
    def create_course(
        db: Session,
        *,
        name: str,
        term: str,
        description: str | None,
        teacher_id: int,
        status: str = "active",
    ) -> Course:
        course = Course(
            name=name,
            term=term,
            description=description,
            teacher_id=teacher_id,
            status=status,
        )
        db.add(course)
        db.commit()
        db.refresh(course)
        return course

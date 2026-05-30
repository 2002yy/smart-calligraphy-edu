from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories import CourseRepository, UserRepository
from app.schemas.course import CourseCreate


class CourseService:
    @staticmethod
    def _serialize(course) -> dict:
        return {
            "id": course.id,
            "name": course.name,
            "term": course.term,
            "description": course.description,
            "teacher_id": course.teacher_id,
            "status": course.status,
            "created_at": course.created_at,
        }

    @staticmethod
    def list_courses(db: Session, teacher_id: int | None = None, status: str | None = None) -> list[dict]:
        courses = CourseRepository.list_courses(db, teacher_id=teacher_id, status=status)
        return [CourseService._serialize(item) for item in courses]

    @staticmethod
    def create_course(db: Session, payload: CourseCreate) -> dict:
        teacher = UserRepository.get_by_id(db, payload.teacher_id)
        if not teacher or teacher.role != "teacher":
            raise HTTPException(status_code=404, detail="teacher not found")

        course = CourseRepository.create_course(
            db,
            name=payload.name,
            term=payload.term,
            description=payload.description,
            teacher_id=payload.teacher_id,
            status="active",
        )
        return CourseService._serialize(course)

    @staticmethod
    def get_course(db: Session, course_id: int) -> dict:
        course = CourseRepository.get_by_id(db, course_id)
        if not course:
            raise HTTPException(status_code=404, detail="course not found")
        return CourseService._serialize(course)

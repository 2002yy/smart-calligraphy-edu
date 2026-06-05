from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories import ClassMemberRepository, ClassroomRepository, CourseRepository, UserRepository
from app.schemas.classroom import ClassCreate


class ClassService:
    @staticmethod
    def _serialize_class(classroom) -> dict:
        return {
            "id": classroom.id,
            "course_id": classroom.course_id,
            "name": classroom.name,
            "invite_code": classroom.invite_code,
            "student_count": classroom.student_count,
        }

    @staticmethod
    def list_classes(db: Session, course_id: int | None = None) -> list[dict]:
        classrooms = ClassroomRepository.list_classes(db, course_id=course_id)
        return [ClassService._serialize_class(item) for item in classrooms]

    @staticmethod
    def create_class(db: Session, payload: ClassCreate) -> dict:
        course = CourseRepository.get_by_id(db, payload.course_id)
        if not course:
            raise HTTPException(status_code=404, detail="course not found")

        invite_code = payload.invite_code or f"CLASS{payload.course_id:02d}{len(payload.name):02d}"
        classroom = ClassroomRepository.create_class(
            db,
            course_id=payload.course_id,
            name=payload.name,
            invite_code=invite_code,
        )
        return ClassService._serialize_class(classroom)

    @staticmethod
    def join_class(db: Session, class_id: int, student_id: int, invite_code: str) -> dict:
        classroom = ClassroomRepository.get_by_id(db, class_id)
        if not classroom:
            raise HTTPException(status_code=404, detail="class not found")
        if invite_code != classroom.invite_code:
            raise HTTPException(status_code=400, detail="invite code invalid")

        student = UserRepository.get_by_id(db, student_id)
        if not student or student.role != "student":
            raise HTTPException(status_code=404, detail="student not found")

        exists = ClassMemberRepository.get_member(db, class_id, student_id)
        if not exists:
            ClassMemberRepository.create_member(db, class_id=class_id, student_id=student_id)
            classroom.student_count += 1
            ClassroomRepository.update_class(db, classroom)
        return {"class_id": class_id, "student_id": student_id, "status": "joined"}

    @staticmethod
    def get_members(db: Session, class_id: int) -> dict:
        classroom = ClassroomRepository.get_by_id(db, class_id)
        if not classroom:
            raise HTTPException(status_code=404, detail="class not found")

        member_rows = ClassMemberRepository.list_members(db, class_id)
        members = []
        for member in member_rows:
            user = UserRepository.get_by_id(db, member.student_id)
            if user:
                members.append(
                    {
                        "id": user.id,
                        "name": user.name,
                        "role": user.role,
                    }
                )
        return {"class_id": class_id, "members": members}

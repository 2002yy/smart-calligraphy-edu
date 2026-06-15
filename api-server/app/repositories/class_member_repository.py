from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.class_member import ClassMember


class ClassMemberRepository:
    @staticmethod
    def list_members(db: Session, class_id: int) -> list[ClassMember]:
        stmt = select(ClassMember).where(ClassMember.class_id == class_id).order_by(ClassMember.id.asc())
        return list(db.scalars(stmt).all())

    @staticmethod
    def list_by_student(db: Session, student_id: int) -> list[ClassMember]:
        stmt = select(ClassMember).where(ClassMember.student_id == student_id).order_by(ClassMember.id.asc())
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_member(db: Session, class_id: int, student_id: int) -> ClassMember | None:
        stmt = select(ClassMember).where(
            ClassMember.class_id == class_id,
            ClassMember.student_id == student_id,
        )
        return db.scalar(stmt)

    @staticmethod
    def create_member(db: Session, *, class_id: int, student_id: int) -> ClassMember:
        member = ClassMember(class_id=class_id, student_id=student_id)
        db.add(member)
        db.commit()
        db.refresh(member)
        return member

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.review import Review


class ReviewRepository:
    @staticmethod
    def list_reviews(
        db: Session,
        teacher_id: int | None = None,
        homework_id: int | None = None,
    ) -> list[Review]:
        stmt = select(Review).order_by(Review.id.desc())
        if teacher_id is not None:
            stmt = stmt.where(Review.teacher_id == teacher_id)
        if homework_id is not None:
            stmt = stmt.where(Review.homework_id == homework_id)
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_by_homework_id(db: Session, homework_id: int) -> Review | None:
        stmt = select(Review).where(Review.homework_id == homework_id)
        return db.scalar(stmt)

    @staticmethod
    def create_review(
        db: Session,
        *,
        homework_id: int,
        teacher_id: int,
        comment: str | None,
        final_score: float | None,
        review_status: str,
    ) -> Review:
        review = Review(
            homework_id=homework_id,
            teacher_id=teacher_id,
            comment=comment,
            final_score=final_score,
            review_status=review_status,
        )
        db.add(review)
        db.commit()
        db.refresh(review)
        return review

    @staticmethod
    def update_review(db: Session, review: Review) -> Review:
        db.add(review)
        db.commit()
        db.refresh(review)
        return review

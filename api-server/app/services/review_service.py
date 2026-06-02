from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories import EvaluationRepository, HomeworkRepository, ReviewRepository, TaskRepository, UserRepository
from app.schemas.review import ReviewCreate


class ReviewService:
    @staticmethod
    def _serialize(review, evaluation=None, homework=None, task=None, student=None) -> dict:
        return {
            "id": review.id,
            "homework_id": review.homework_id,
            "teacher_id": review.teacher_id,
            "student_id": homework.student_id if homework else None,
            "student_name": student.name if student else None,
            "task_id": homework.task_id if homework else None,
            "task_title": task.title if task else None,
            "homework_status": homework.status if homework else None,
            "image_url": homework.image_url if homework else None,
            "submitted_at": homework.submitted_at if homework else None,
            "comment": review.comment,
            "final_score": review.final_score,
            "score": evaluation.total_score if evaluation else None,
            "structure_score": evaluation.structure_score if evaluation else None,
            "center_score": evaluation.center_score if evaluation else None,
            "stroke_order_score": evaluation.stroke_order_score if evaluation else None,
            "tags": evaluation.issues_json if evaluation and evaluation.issues_json else [],
            "advice": evaluation.advice_text if evaluation else None,
            "compare_image_url": evaluation.compare_image_url if evaluation else None,
            "thinking_steps": evaluation.thinking_steps if evaluation else None,
            "status": review.review_status,
            "reviewed_at": review.reviewed_at,
        }

    @staticmethod
    def list_reviews(
        db: Session,
        teacher_id: int | None = None,
        homework_id: int | None = None,
    ) -> list[dict]:
        reviews = ReviewRepository.list_reviews(db, teacher_id=teacher_id, homework_id=homework_id)
        serialized: list[dict] = []
        for item in reviews:
            homework = HomeworkRepository.get_by_id(db, item.homework_id)
            evaluation = EvaluationRepository.get_by_homework_id(db, item.homework_id)
            task = TaskRepository.get_by_id(db, homework.task_id) if homework else None
            student = UserRepository.get_by_id(db, homework.student_id) if homework else None
            serialized.append(ReviewService._serialize(item, evaluation, homework, task, student))
        return serialized

    @staticmethod
    def create_review(db: Session, payload: ReviewCreate) -> dict:
        homework = HomeworkRepository.get_by_id(db, payload.homework_id)
        if not homework:
            raise HTTPException(status_code=404, detail="homework not found")

        teacher = UserRepository.get_by_id(db, payload.teacher_id)
        if not teacher or teacher.role != "teacher":
            raise HTTPException(status_code=404, detail="teacher not found")

        existing = ReviewRepository.get_by_homework_id(db, payload.homework_id)
        final_score = payload.final_score
        if final_score is None:
            evaluation = EvaluationRepository.get_by_homework_id(db, payload.homework_id)
            final_score = evaluation.total_score if evaluation else None

        if existing:
            existing.teacher_id = payload.teacher_id
            existing.comment = payload.comment
            existing.final_score = final_score
            existing.review_status = payload.status
            review = ReviewRepository.update_review(db, existing)
        else:
            review = ReviewRepository.create_review(
                db,
                homework_id=payload.homework_id,
                teacher_id=payload.teacher_id,
                comment=payload.comment,
                final_score=final_score,
                review_status=payload.status,
            )

        homework.status = "reviewed"
        HomeworkRepository.update_homework(db, homework)
        evaluation = EvaluationRepository.get_by_homework_id(db, payload.homework_id)
        task = TaskRepository.get_by_id(db, homework.task_id)
        student = UserRepository.get_by_id(db, homework.student_id)
        return ReviewService._serialize(review, evaluation, homework, task, student)

    @staticmethod
    def get_review(db: Session, homework_id: int) -> dict:
        review = ReviewRepository.get_by_homework_id(db, homework_id)
        if not review:
            raise HTTPException(status_code=404, detail="review not found")
        homework = HomeworkRepository.get_by_id(db, homework_id)
        evaluation = EvaluationRepository.get_by_homework_id(db, homework_id)
        task = TaskRepository.get_by_id(db, homework.task_id) if homework else None
        student = UserRepository.get_by_id(db, homework.student_id) if homework else None
        return ReviewService._serialize(review, evaluation, homework, task, student)

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.evaluation import Evaluation


class EvaluationRepository:
    @staticmethod
    def get_by_homework_id(db: Session, homework_id: int) -> Evaluation | None:
        stmt = select(Evaluation).where(Evaluation.homework_id == homework_id)
        return db.scalar(stmt)

    @staticmethod
    def list_by_homework_ids(db: Session, homework_ids: list[int]) -> list[Evaluation]:
        if not homework_ids:
            return []
        stmt = select(Evaluation).where(Evaluation.homework_id.in_(homework_ids)).order_by(Evaluation.id.desc())
        return list(db.scalars(stmt).all())

    @staticmethod
    def create_evaluation(
        db: Session,
        *,
        homework_id: int,
        total_score: float,
        structure_score: float,
        center_score: float,
        stroke_order_score: float,
        issues: list[str],
        advice_text: str,
        compare_image_url: str,
        thinking_steps: list | None = None,
    ) -> Evaluation:
        evaluation = Evaluation(
            homework_id=homework_id,
            total_score=total_score,
            structure_score=structure_score,
            center_score=center_score,
            stroke_order_score=stroke_order_score,
            issues_json=issues,
            advice_text=advice_text,
            compare_image_url=compare_image_url,
            thinking_steps=thinking_steps,
        )
        db.add(evaluation)
        db.commit()
        db.refresh(evaluation)
        return evaluation

    @staticmethod
    def update_evaluation(
        db: Session,
        evaluation: Evaluation,
        *,
        total_score: float,
        structure_score: float,
        center_score: float,
        stroke_order_score: float,
        issues: list[str],
        advice_text: str,
        compare_image_url: str | None,
        thinking_steps: list | None = None,
    ) -> Evaluation:
        evaluation.total_score = total_score
        evaluation.structure_score = structure_score
        evaluation.center_score = center_score
        evaluation.stroke_order_score = stroke_order_score
        evaluation.issues_json = issues
        evaluation.advice_text = advice_text
        evaluation.compare_image_url = compare_image_url
        evaluation.thinking_steps = thinking_steps
        db.add(evaluation)
        db.commit()
        db.refresh(evaluation)
        return evaluation

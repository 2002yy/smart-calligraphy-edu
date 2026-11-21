from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.database import utc_now
from app.models.evaluation import Evaluation


class EvaluationRepository:
    REAL_AI_PROVIDERS = frozenset({"qwen", "openai"})

    @staticmethod
    def is_ai_finished(evaluation: Evaluation) -> bool:
        """只有明确的真实模型来源且完成的评分，才进入教学统计。"""
        return evaluation.status == "finished" and evaluation.provider in EvaluationRepository.REAL_AI_PROVIDERS

    @staticmethod
    def fail_stale_processing(db: Session, cutoff: datetime, message: str) -> int:
        """Atomically fail stale processing rows; never rewrite a fresh result.

        The predicate and transition execute in one SQL UPDATE. Startup may run
        in several workers, but a recovered row is counted only once.
        """
        try:
            result = db.execute(
                update(Evaluation)
                .where(
                    Evaluation.status == "processing",
                    Evaluation.updated_at < cutoff,
                )
                .values(status="failed", advice_text=message, updated_at=utc_now())
                .execution_options(synchronize_session=False)
            )
            db.commit()
            return result.rowcount or 0
        except Exception:
            db.rollback()
            raise

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
        status: str = "finished",
        provider: str | None = None,
        total_score: float = 0,
        structure_score: float = 0,
        center_score: float = 0,
        stroke_order_score: float = 0,
        issues: list[str] | None = None,
        advice_text: str = "",
        compare_image_url: str = "",
        thinking_steps: list | None = None,
    ) -> Evaluation:
        evaluation = Evaluation(
            homework_id=homework_id,
            status=status,
            provider=provider,
            total_score=total_score,
            structure_score=structure_score,
            center_score=center_score,
            stroke_order_score=stroke_order_score,
            issues_json=issues or [],
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
        status: str | None = None,
        provider: str | None = None,
        total_score: float | None = None,
        structure_score: float | None = None,
        center_score: float | None = None,
        stroke_order_score: float | None = None,
        issues: list[str] | None = None,
        advice_text: str | None = None,
        compare_image_url: str | None = None,
        thinking_steps: list | None = None,
    ) -> Evaluation:
        if status is not None:
            evaluation.status = status
        if provider is not None:
            evaluation.provider = provider
        if total_score is not None:
            evaluation.total_score = total_score
        if structure_score is not None:
            evaluation.structure_score = structure_score
        if center_score is not None:
            evaluation.center_score = center_score
        if stroke_order_score is not None:
            evaluation.stroke_order_score = stroke_order_score
        if issues is not None:
            evaluation.issues_json = issues
        if advice_text is not None:
            evaluation.advice_text = advice_text
        if compare_image_url is not None:
            evaluation.compare_image_url = compare_image_url
        if thinking_steps is not None:
            evaluation.thinking_steps = thinking_steps
        db.add(evaluation)
        db.commit()
        db.refresh(evaluation)
        return evaluation

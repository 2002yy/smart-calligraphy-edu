"""评分来源是真实学习统计的边界；Mock 和历史未知数据不得混入。"""

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine

from app.models.homework import Homework
from app.repositories import EvaluationRepository
from app.repositories.review_repository import ReviewRepository
from app.schemas.evaluation import EvaluationProvider, EvaluationStartRead
from app.services.dashboard_service import DashboardService
from app.services.evaluation_service import EvaluationService
from app.services.homework_service import HomeworkService
from app.services.report_service import ReportService
from app.services.review_service import ReviewService
from app.services.user_service import UserService


def test_only_finished_ai_scores_reach_learning_statistics(db_session, seeded_homework, seeded_task, student_user):
    task_id, student_id, class_id = seeded_task.id, student_user.id, seeded_task.class_id
    others = [
        Homework(task_id=task_id, student_id=student_id, image_url=f"/uploads/{source}.png", status="evaluated")
        for source in ("mock", "legacy", "processing")
    ]
    db_session.add_all(others)
    db_session.commit()

    EvaluationRepository.create_evaluation(
        db_session, homework_id=seeded_homework.id, provider="qwen", status="finished",
        total_score=8.0, issues=["重心不稳"],
    )
    EvaluationRepository.create_evaluation(
        db_session, homework_id=others[0].id, provider="mock", status="finished",
        total_score=2.0, issues=["结构失衡"],
    )
    EvaluationRepository.create_evaluation(
        db_session, homework_id=others[1].id, status="finished",
        total_score=10.0, issues=["笔法有误"],
    )
    EvaluationRepository.create_evaluation(
        db_session, homework_id=others[2].id, provider="qwen", status="processing",
        total_score=0.0, issues=["重心不稳"],
    )

    growth = UserService.get_growth(db_session, student_id)
    student_report = ReportService.student_report(db_session, student_id)
    class_report = ReportService.class_report(db_session, class_id)
    dashboard = DashboardService.build_class_dashboard(db_session, class_id)
    trend = ReportService.student_tag_trend(db_session, student_id)
    tagged = HomeworkService.list_homework(db_session, task_ids=[task_id], tag="重心不稳")

    assert growth["avg_score"] == 8.0
    assert growth["recent_scores"] == [8.0]
    assert student_report["homework_count"] == 4
    assert student_report["evaluated_count"] == 1
    assert student_report["avg_score"] == 8.0
    assert class_report["evaluated_count"] == 1
    assert dashboard["homework_count"] == 4
    assert dashboard["evaluated_count"] == 1
    assert dashboard["avg_score"] == 8.0
    assert dashboard["top_issues"] == ["重心不稳"]
    assert [r["score"] for r in trend["records"]] == [8.0]
    assert [item["id"] for item in tagged] == [seeded_homework.id]


def test_historical_unknown_provider_is_not_guessed(db_session, seeded_homework, seeded_task):
    EvaluationRepository.create_evaluation(
        db_session, homework_id=seeded_homework.id, status="finished", total_score=9.0,
    )
    existing = EvaluationService.start(db_session, seeded_homework.id, provider=EvaluationProvider.mock)
    assert existing["provider"] is None
    assert EvaluationStartRead(**existing).provider is None
    assert EvaluationService.get(db_session, seeded_homework.id)["provider"] is None

    refreshed = EvaluationService.start(db_session, seeded_homework.id, provider=EvaluationProvider.mock, force_refresh=True)
    assert refreshed["provider"] == EvaluationProvider.mock
    assert EvaluationRepository.get_by_homework_id(db_session, seeded_homework.id).provider == "mock"


def test_mock_does_not_create_teacher_pending_review(db_session, seeded_homework, seeded_task):
    EvaluationService.start(db_session, seeded_homework.id, provider=EvaluationProvider.mock)
    assert ReviewRepository.get_by_homework_id(db_session, seeded_homework.id) is None
    assert ReviewService.list_reviews(db_session, teacher_id=seeded_task.created_by) == []


def test_existing_mock_review_keeps_source_for_audit(db_session, seeded_homework, seeded_task):
    EvaluationService.start(db_session, seeded_homework.id, provider=EvaluationProvider.mock)
    ReviewRepository.create_review(
        db_session, homework_id=seeded_homework.id, teacher_id=seeded_task.created_by,
        comment=None, final_score=None, review_status="pending",
    )
    assert ReviewService.get_review(db_session, seeded_homework.id)["evaluation_provider"] == "mock"
    evaluation = EvaluationRepository.get_by_homework_id(db_session, seeded_homework.id)
    EvaluationRepository.update_evaluation(db_session, evaluation, status="processing", total_score=0)
    in_progress = ReviewService.get_review(db_session, seeded_homework.id)
    assert in_progress["evaluation_status"] == "processing"
    assert in_progress["score"] is None


def test_migration_preserves_old_scores_with_unknown_source(tmp_path, monkeypatch):
    """升级历史库不能将无来源的旧评分猜测成 Qwen 或 Mock。"""
    from pathlib import Path

    database_url = f"sqlite:///{tmp_path / 'legacy.db'}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))

    command.upgrade(cfg, "07d4e0bf7e46")
    engine = create_engine(database_url)
    with engine.begin() as conn:
        conn.exec_driver_sql(
            """INSERT INTO evaluations
               (id, homework_id, status, total_score, structure_score, center_score,
                stroke_order_score, created_at, updated_at)
               VALUES (1, 999, 'finished', 9.5, 9.5, 9.5, 9.5, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"""
        )
    command.upgrade(cfg, "head")
    with engine.connect() as conn:
        assert conn.exec_driver_sql("SELECT total_score, provider FROM evaluations WHERE id = 1").one() == (9.5, None)
    engine.dispose()

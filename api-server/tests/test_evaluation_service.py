"""Tests for the evaluation service layer.

Covers mock evaluation logic, provider resolution, and error handling
for the evaluation workflow.
"""

import pytest
from fastapi import HTTPException

from app.schemas.evaluation import EvaluationProvider
from app.services.evaluation_service import EvaluationService


class TestBuildMockResult:
    """Verify the mock scoring formula produces sensible scores."""

    def test_score_range_with_low_homework_id(self, db_session, seeded_task):
        result = EvaluationService._build_mock_result(1, seeded_task)
        assert 0 <= result["total_score"] <= 10
        assert 0 <= result["structure_score"] <= 10
        assert 0 <= result["center_score"] <= 10
        assert 0 <= result["stroke_order_score"] <= 10
        assert "issues" in result
        assert "advice_text" in result
        assert len(result["thinking_steps"]) == 7

    def test_score_increases_slightly_with_higher_homework_id(self, db_session, seeded_task):
        low = EvaluationService._build_mock_result(1, seeded_task)
        high = EvaluationService._build_mock_result(100, seeded_task)
        assert high["total_score"] >= low["total_score"]

    def test_structure_weight_influences_score(self, db_session, seeded_task):
        seeded_task.structure_weight = 100
        seeded_task.center_weight = 0
        seeded_task.stroke_order_weight = 0
        result = EvaluationService._build_mock_result(1, seeded_task)
        assert result["structure_score"] >= result["center_score"]
        assert result["structure_score"] >= result["stroke_order_score"]

    def test_low_score_produces_corrective_tags(self, db_session, seeded_task):
        """When total_score < 8.8, tags should indicate areas to improve."""
        # homework_id=1 with default weights gives score in the ~8.2 range
        result = EvaluationService._build_mock_result(1, seeded_task)
        assert any(tag in result["issues"] for tag in ["center drift", "weak finish"])

    def test_high_score_produces_positive_tags(self, db_session, seeded_task):
        """When total_score >= 9.0, tags should be affirming."""
        with pytest.MonkeyPatch().context() as mp:
            result = EvaluationService._build_mock_result(999, seeded_task)
        assert any(tag in result["issues"] for tag in ["stable structure", "clear main stroke"])


class TestResolveProvider:
    def test_mock_provider_stays_mock(self):
        resolved = EvaluationService._resolve_provider(EvaluationProvider.mock)
        assert resolved == EvaluationProvider.mock

    def test_auto_falls_back_to_mock_when_openai_not_configured(self):
        resolved = EvaluationService._resolve_provider(EvaluationProvider.auto)
        assert resolved == EvaluationProvider.mock


class TestStartEvaluation:
    def test_fails_when_homework_not_found(self, db_session):
        with pytest.raises(HTTPException) as exc:
            EvaluationService.start(db_session, homework_id=9999)
        assert exc.value.status_code == 404

    def test_succeeds_with_mock_provider(self, db_session, seeded_homework, seeded_task):
        result = EvaluationService.start(db_session, seeded_homework.id, provider=EvaluationProvider.mock)
        assert result["status"] == "finished"
        assert result["homework_id"] == seeded_homework.id
        assert result["provider"] == EvaluationProvider.mock

    def test_returns_existing_evaluation_without_force(self, db_session, seeded_homework, seeded_task):
        first = EvaluationService.start(db_session, seeded_homework.id, provider=EvaluationProvider.mock)
        second = EvaluationService.start(db_session, seeded_homework.id, provider=EvaluationProvider.mock)
        assert second["evaluation_id"] == first["evaluation_id"]

    def test_force_refresh_creates_new_evaluation(self, db_session, seeded_homework, seeded_task):
        first = EvaluationService.start(db_session, seeded_homework.id, provider=EvaluationProvider.mock)
        second = EvaluationService.start(db_session, seeded_homework.id, provider=EvaluationProvider.mock, force_refresh=True)
        # force_refresh updates in-place, so the same ID is reused
        assert second["homework_id"] == seeded_homework.id
        assert second["provider"] == EvaluationProvider.mock

    def test_mark_homework_as_evaluated(self, db_session, seeded_homework, seeded_task):
        EvaluationService.start(db_session, seeded_homework.id, provider=EvaluationProvider.mock)
        assert seeded_homework.status == "evaluated"

    def test_can_retrieve_evaluation_after_start(self, db_session, seeded_homework, seeded_task):
        EvaluationService.start(db_session, seeded_homework.id, provider=EvaluationProvider.mock)
        detail = EvaluationService.get(db_session, seeded_homework.id)
        assert detail["homework_id"] == seeded_homework.id
        assert detail["status"] == "finished"
        assert detail["total_score"] > 0


class TestGetEvaluation:
    def test_fails_when_not_found(self, db_session):
        with pytest.raises(HTTPException) as exc:
            EvaluationService.get(db_session, homework_id=9999)
        assert exc.value.status_code == 404

    def test_returns_evaluation_data(self, db_session, seeded_homework, seeded_task):
        EvaluationService.start(db_session, seeded_homework.id, provider=EvaluationProvider.mock)
        detail = EvaluationService.get(db_session, seeded_homework.id)
        assert "score" in detail
        assert "total_score" in detail
        assert "structure_score" in detail
        assert "center_score" in detail
        assert "stroke_order_score" in detail
        assert "tags" in detail
        assert "issues" in detail
        assert "advice" in detail

    def test_includes_thinking_steps(self, db_session, seeded_homework, seeded_task):
        EvaluationService.start(db_session, seeded_homework.id, provider=EvaluationProvider.mock)
        detail = EvaluationService.get(db_session, seeded_homework.id)
        steps = detail.get("thinking_steps")
        assert steps is not None
        assert len(steps) == 7
        assert steps[0]["title"] == "图像预处理"
        assert steps[0]["status"] == "done"
        assert steps[-1]["title"] == "综合评分"
        assert "score" in steps[-1]

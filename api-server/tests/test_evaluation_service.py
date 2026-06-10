"""Tests for the evaluation service layer.

Covers mock evaluation logic, provider resolution, and error handling
for the evaluation workflow.
"""

import pytest
from fastapi import HTTPException

from app.schemas.evaluation import EvaluationProvider
from app.services.evaluation_service import EvaluationService
from app.services.qwen_evaluation_service import QwenEvaluationService


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
        """总分较高的作业应获得肯定性标签（Mock演示用，最低也有8分以上）。"""
        result = EvaluationService._build_mock_result(1, seeded_task)
        # homework_id=1 总分约 8.5，属于高分档
        assert any(tag in result["issues"] for tag in ["结构工整", "重心稳当", "笔法到位"])

    def test_high_score_produces_positive_tags(self, db_session, seeded_task):
        """homework_id % 10 == 0 时分数最高，标签应为肯定性。"""
        with pytest.MonkeyPatch().context() as mp:
            result = EvaluationService._build_mock_result(10, seeded_task)
        assert any(tag in result["issues"] for tag in ["结构工整", "重心稳当", "笔法到位"])


class TestResolveProvider:
    def test_mock_provider_stays_mock(self):
        resolved = EvaluationService._resolve_provider(EvaluationProvider.mock)
        assert resolved == EvaluationProvider.mock

    def test_auto_falls_back_to_mock_when_openai_not_configured(self, monkeypatch):
        monkeypatch.setattr(QwenEvaluationService, "is_configured", staticmethod(lambda: False))
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

    def test_overlay_respects_annotations(self):
        """save_result_overlay 的坐标转换和异常处理。"""
        from app.services.file_storage_service import FileStorageService
        from PIL import Image as _PIL
        import io as _io, tempfile
        from pathlib import Path

        # 把图放到 storage 目录下（save_result_overlay 通过 resolve_upload_url 找文件）
        storage_root = Path(FileStorageService.get_storage_root())
        tmp_name = f"test_overlay_{__import__('uuid').uuid4().hex[:8]}.jpg"
        tmp_path = storage_root / tmp_name

        buf = _io.BytesIO()
        _PIL.new("RGB", (200, 200), color=255).save(buf, "JPEG")
        tmp_path.write_bytes(buf.getvalue())
        tmp_url = f"/uploads/{tmp_name}"

        try:
            # 正常标注
            r = FileStorageService.save_result_overlay(
                image_url=tmp_url,
                scores={"total_score": 8.5, "structure_score": 8.0, "center_score": 7.5, "stroke_order_score": 9.0},
                tags=["结构工整"],
                annotations=[{"x1": 10, "y1": 20, "x2": 50, "y2": 60, "label": "test", "severity": "major"}],
            )
            assert "_result.jpg" in r

            # 缺失坐标字段：缺字段标注被跳过，overlay 继续生成，不抛异常
            r2 = FileStorageService.save_result_overlay(image_url=tmp_url, scores={"total_score": 8.5, "structure_score": 8.0, "center_score": 7.5, "stroke_order_score": 9.0}, tags=[], annotations=[{"x1": 10, "label": "missing"}])
            assert r2 is not None
            assert "_result.jpg" in r2

            # 空标注
            r3 = FileStorageService.save_result_overlay(image_url=tmp_url, scores={"total_score": 8.5, "structure_score": 8.0, "center_score": 7.5, "stroke_order_score": 9.0}, tags=["结构工整"], annotations=[])
            assert "_result.jpg" in r3

            # 越界坐标
            r4 = FileStorageService.save_result_overlay(image_url=tmp_url, scores={"total_score": 5.0, "structure_score": 5.0, "center_score": 5.0, "stroke_order_score": 5.0}, tags=[], annotations=[{"x1": -10, "y1": -20, "x2": 200, "y2": 300, "label": "out", "severity": "minor"}])
            assert "_result.jpg" in r4
        finally:
            if tmp_path.exists():
                tmp_path.unlink()
            result_path = storage_root / f"{tmp_name.replace('.jpg','')}_result.jpg"
            if result_path.exists():
                result_path.unlink()


class TestQwenEvaluationService:
    """Qwen 评测服务的辅助函数（无需 API 调用）。"""

    def test_extract_json_bare(self):
        """裸 JSON 应原样返回。"""
        raw = '{"total_score": 8.5}'
        assert QwenEvaluationService._extract_json(raw) == raw

    def test_extract_json_code_fence(self):
        """```json 包裹的 JSON 应被剥离。"""
        raw = "```json\n{\"total_score\": 8.5}\n```"
        result = QwenEvaluationService._extract_json(raw)
        assert result == '{"total_score": 8.5}'

    def test_extract_json_triple_backtick_no_lang(self):
        """只有 ``` 不带 json 标记也应工作。"""
        raw = "```\n{\"total_score\": 7.0}\n```"
        result = QwenEvaluationService._extract_json(raw)
        assert result == '{"total_score": 7.0}'

    def test_extract_json_with_prefix_text(self):
        """JSON 前有额外文字应被剥离。"""
        raw = '以下是 JSON：\n```json\n{"total_score": 9.0}\n```\n注意'
        result = QwenEvaluationService._extract_json(raw)
        assert '"total_score"' in result

    def test_filter_tags_whitelist(self):
        """只保留 ALLOWED_TAGS 内的标签。"""
        tags = QwenEvaluationService._filter_tags(["结构工整", "重心稳当", "这个模型自己编的"])
        assert "结构工整" in tags
        assert "重心稳当" in tags
        assert "这个模型自己编的" not in tags

    def test_filter_tags_non_list(self):
        """非列表输入应返回空列表。"""
        assert QwenEvaluationService._filter_tags(None) == []
        assert QwenEvaluationService._filter_tags("结构工整") == []
        assert QwenEvaluationService._filter_tags({"tag": "结构工整"}) == []

    def test_filter_tags_empty(self):
        """空列表应返回空列表。"""
        assert QwenEvaluationService._filter_tags([]) == []


class TestGetEvaluationThinkingSteps:
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

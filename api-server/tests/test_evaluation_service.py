"""Tests for the evaluation service layer.

Covers mock evaluation logic, provider resolution, and error handling
for the evaluation workflow.
"""

import pytest
from fastapi import HTTPException

from app.schemas.evaluation import EvaluationProvider
from app.services.evaluation_service import EvaluationService
from app.services.qwen_evaluation_service import QwenEvaluationService


@pytest.fixture
def deferred_qwen(monkeypatch, db_session):
    """One shared test clock: queue threads and bind their own DB Sessions."""
    from sqlalchemy.orm import Session

    from app.core import database
    from app.services import evaluation_service as module

    callbacks = []

    class DeferredThread:
        def __init__(self, target, daemon):
            assert daemon is True
            self.target = target

        def start(self):
            callbacks.append(self.target)

    monkeypatch.setattr(QwenEvaluationService, "is_configured", staticmethod(lambda: True))
    monkeypatch.setattr(module.threading, "Thread", DeferredThread)
    monkeypatch.setattr(database, "SessionLocal", lambda: Session(bind=db_session.get_bind()))
    return callbacks


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

    def test_qwen_result_with_annotations_is_persisted_as_finished(
        self, db_session, seeded_homework, seeded_task, monkeypatch, deferred_qwen
    ):
        """真实 Qwen 的 payload 含 annotations；图层消费后不能传入 Repository。"""
        from app.repositories import EvaluationRepository
        from app.services.file_storage_service import FileStorageService
        from sqlalchemy.orm import Session

        annotations = [{"x1": 10, "y1": 20, "x2": 30, "y2": 40, "label": "结构偏移"}]
        homework_id = seeded_homework.id
        image_url = seeded_homework.image_url
        payload = EvaluationService._build_mock_result(homework_id, seeded_task)
        payload["annotations"] = annotations
        overlays = []

        monkeypatch.setattr(EvaluationService, "_build_qwen_result", staticmethod(lambda *_: dict(payload)))
        monkeypatch.setattr(
            FileStorageService, "save_result_overlay",
            staticmethod(lambda **kwargs: overlays.append(kwargs["annotations"]) or image_url),
        )

        result = EvaluationService.start(db_session, homework_id, provider=EvaluationProvider.qwen)
        assert len(deferred_qwen) == 1
        db_session.close()  # HTTP 请求返回，原 Session 关闭；后台任务此时才执行。
        deferred_qwen.pop()()
        with Session(bind=db_session.get_bind()) as verification_db:
            stored = EvaluationRepository.get_by_homework_id(verification_db, homework_id)
            assert stored is not None
            assert stored.status == "finished"
            assert stored.total_score == payload["total_score"]
        assert result["provider"] == EvaluationProvider.qwen
        assert overlays == [annotations]


    def test_superseded_attempt_cannot_publish_or_fail_newer_result(
        self, db_session, seeded_homework, seeded_task, monkeypatch, deferred_qwen
    ):
        from app.repositories import EvaluationRepository, ReviewRepository
        from app.services.file_storage_service import FileStorageService

        homework_id = seeded_homework.id
        old = EvaluationService.start(db_session, homework_id, provider=EvaluationProvider.qwen)
        from app.models.evaluation import Evaluation
        old_token = db_session.get(Evaluation, old["evaluation_id"]).attempt_id
        newer = EvaluationService.start(
            db_session, homework_id, provider=EvaluationProvider.qwen, force_refresh=True,
        )
        assert old["evaluation_id"] == newer["evaluation_id"]
        db_session.expire_all()
        current_token = db_session.get(Evaluation, newer["evaluation_id"]).attempt_id
        assert current_token and old_token != current_token

        called = []
        payload = EvaluationService._build_mock_result(homework_id, seeded_task)
        monkeypatch.setattr(EvaluationService, "_build_qwen_result",
                            staticmethod(lambda *_: called.append("model") or dict(payload)))
        monkeypatch.setattr(FileStorageService, "save_result_overlay",
                            staticmethod(lambda **_: seeded_homework.image_url))

        assert len(deferred_qwen) == 2
        deferred_qwen.pop(0)()  # old queue item is stale before its API request
        assert called == []
        assert not EvaluationRepository.fail_attempt(
            db_session, old["evaluation_id"], old_token, "old worker failed"
        )
        deferred_qwen.pop(0)()  # latest attempt owns the result
        db_session.expire_all()
        stored = EvaluationRepository.get_by_homework_id(db_session, homework_id)
        assert called == ["model"]
        assert stored.status == "finished"
        assert stored.attempt_id == current_token
        assert stored.total_score == payload["total_score"]
        assert ReviewRepository.get_by_homework_id(db_session, homework_id) is not None
        assert not EvaluationRepository.fail_attempt(
            db_session, old["evaluation_id"], old_token, "late worker failed"
        )
        db_session.expire_all()
        assert stored.status == "finished"

    def test_refresh_during_overlay_rejects_old_completion(
        self, db_session, seeded_homework, seeded_task, monkeypatch, deferred_qwen
    ):
        """Refresh in the window after model response must defeat old CAS."""
        from app.models.evaluation import Evaluation
        from app.repositories import EvaluationRepository
        from app.services.file_storage_service import FileStorageService

        homework_id = seeded_homework.id
        first = EvaluationService.start(db_session, homework_id, provider=EvaluationProvider.qwen)
        old_token = db_session.get(Evaluation, first["evaluation_id"]).attempt_id
        scores = [4.0, 9.0]
        def build_result(*_):
            payload = EvaluationService._build_mock_result(homework_id, seeded_task)
            value = scores.pop(0)
            payload.update(total_score=value, structure_score=value,
                           center_score=value, stroke_order_score=value)
            return payload

        refreshed = False

        def overlay(**_):
            nonlocal refreshed
            if not refreshed:
                refreshed = True
                EvaluationService.start(
                    db_session, homework_id,
                    provider=EvaluationProvider.qwen, force_refresh=True,
                )
            return seeded_homework.image_url

        monkeypatch.setattr(EvaluationService, "_build_qwen_result", staticmethod(build_result))
        monkeypatch.setattr(FileStorageService, "save_result_overlay", staticmethod(overlay))
        deferred_qwen.pop(0)()
        db_session.expire_all()
        pending = EvaluationRepository.get_by_homework_id(db_session, homework_id)
        assert pending.status == "processing"
        assert pending.attempt_id != old_token
        assert len(deferred_qwen) == 1

        deferred_qwen.pop(0)()
        db_session.expire_all()
        finished = EvaluationRepository.get_by_homework_id(db_session, homework_id)
        assert finished.status == "finished"
        assert finished.total_score == 9.0


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


class TestStaleEvaluationRecovery:
    def test_only_old_processing_is_recovered_once(self, db_session, seeded_homework, seeded_task, monkeypatch):
        """A later startup must not touch completed jobs or active model requests."""
        from datetime import timedelta

        from sqlalchemy import update
        from sqlalchemy.orm import Session

        from app.core import bootstrap
        from app.core.database import utc_now
        from app.models.evaluation import Evaluation
        from app.models.homework import Homework
        from app.repositories import EvaluationRepository

        others = [
            Homework(
                task_id=seeded_task.id,
                student_id=seeded_homework.student_id,
                image_url=f"/uploads/recovery-{i}.png",
                status="submitted",
            )
            for i in range(3)
        ]
        db_session.add_all(others)
        db_session.commit()

        old_processing = EvaluationRepository.create_evaluation(
            db_session, homework_id=seeded_homework.id, provider="qwen", status="processing"
        )
        fresh_processing = EvaluationRepository.create_evaluation(
            db_session, homework_id=others[0].id, provider="qwen", status="processing"
        )
        finished = EvaluationRepository.create_evaluation(
            db_session, homework_id=others[1].id, provider="qwen", status="finished",
            total_score=9.5,
        )
        old_failed = EvaluationRepository.create_evaluation(
            db_session, homework_id=others[2].id, provider="qwen", status="failed"
        )

        stale_time = utc_now() - timedelta(hours=2)
        db_session.execute(
            update(Evaluation)
            .where(Evaluation.id.in_([old_processing.id, finished.id, old_failed.id]))
            .values(updated_at=stale_time)
        )
        db_session.commit()

        monkeypatch.setattr(
            bootstrap, "SessionLocal", lambda: Session(bind=db_session.get_bind())
        )

        assert bootstrap.recover_stuck_evaluations() == 1
        db_session.expire_all()
        assert old_processing.status == "failed"
        assert "中断" in old_processing.advice_text
        assert old_processing.updated_at > stale_time
        assert fresh_processing.status == "processing"
        assert finished.status == "finished"
        assert finished.total_score == 9.5
        assert old_failed.status == "failed"
        assert old_failed.updated_at == stale_time

        assert bootstrap.recover_stuck_evaluations() == 0
        db_session.expire_all()
        assert fresh_processing.status == "processing"
        assert finished.status == "finished"


class TestConcurrentFirstEvaluation:
    def test_database_rejects_two_rows_for_the_same_homework(
        self, db_session, seeded_homework
    ):
        from sqlalchemy.exc import IntegrityError

        from app.repositories import EvaluationRepository

        first = EvaluationRepository.create_evaluation(
            db_session, homework_id=seeded_homework.id,
            status="processing", provider="qwen", attempt_id="a" * 32,
        )
        with pytest.raises(IntegrityError):
            EvaluationRepository.create_evaluation(
                db_session, homework_id=seeded_homework.id,
                status="processing", provider="qwen", attempt_id="b" * 32,
            )
        db_session.rollback()
        still_one = EvaluationRepository.get_by_homework_id(
            db_session, seeded_homework.id,
        )
        assert still_one.id == first.id
        assert still_one.attempt_id == "a" * 32

    def test_stale_empty_read_reuses_insert_winner_without_spawning_worker(
        self, db_session, seeded_homework, monkeypatch, deferred_qwen
    ):
        """Both requests saw no row; only the winner may launch model work."""
        from sqlalchemy import select

        from app.models.evaluation import Evaluation
        from app.repositories import EvaluationRepository

        first = EvaluationRepository.create_evaluation(
            db_session, homework_id=seeded_homework.id,
            status="processing", provider="qwen", attempt_id="a" * 32,
        )
        real_get = EvaluationRepository.get_by_homework_id
        calls = []

        def racing_get(db, homework_id):
            calls.append(homework_id)
            if len(calls) == 1:
                return None  # simulate other request committing after our read
            return real_get(db, homework_id)

        monkeypatch.setattr(
            EvaluationRepository, "get_by_homework_id", staticmethod(racing_get)
        )
        result = EvaluationService.start(
            db_session, seeded_homework.id, provider=EvaluationProvider.qwen
        )
        assert result == {
            "status": "processing", "homework_id": seeded_homework.id,
            "evaluation_id": first.id, "provider": "qwen",
        }
        assert len(deferred_qwen) == 0
        assert len(db_session.scalars(
            select(Evaluation).where(Evaluation.homework_id == seeded_homework.id)
        ).all()) == 1

    def test_force_refresh_after_racing_insert_creates_new_attempt_not_new_row(
        self, db_session, seeded_homework, monkeypatch, deferred_qwen
    ):
        from sqlalchemy import select

        from app.models.evaluation import Evaluation
        from app.repositories import EvaluationRepository

        first = EvaluationRepository.create_evaluation(
            db_session, homework_id=seeded_homework.id,
            status="processing", provider="qwen", attempt_id="a" * 32,
        )
        real_get = EvaluationRepository.get_by_homework_id
        calls = []

        def racing_get(db, homework_id):
            calls.append(homework_id)
            if len(calls) == 1:
                return None
            return real_get(db, homework_id)

        monkeypatch.setattr(
            EvaluationRepository, "get_by_homework_id", staticmethod(racing_get)
        )
        result = EvaluationService.start(
            db_session, seeded_homework.id,
            provider=EvaluationProvider.qwen, force_refresh=True,
        )
        assert result["evaluation_id"] == first.id
        assert result["status"] == "processing"
        assert len(deferred_qwen) == 1
        db_session.expire_all()
        rows = db_session.scalars(
            select(Evaluation).where(Evaluation.homework_id == seeded_homework.id)
        ).all()
        assert len(rows) == 1
        assert rows[0].attempt_id != "a" * 32

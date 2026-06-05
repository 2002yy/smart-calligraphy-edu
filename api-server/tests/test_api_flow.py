from fastapi.testclient import TestClient

from app.main import app
from app.services.openai_evaluation_service import CalligraphyScoreOutput, OpenAIEvaluationService
from app.services.qwen_evaluation_service import QwenEvaluationService


def test_teacher_workflow_end_to_end():
    from unittest.mock import patch
    with patch.object(QwenEvaluationService, "is_configured", return_value=False):
        _run_e2e()


def _run_e2e():
    with TestClient(app) as client:
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "teacher01", "password": "123456"},
        )
        assert login_response.status_code == 200
        login_data = login_response.json()["data"]
        assert login_data["user"]["role"] == "teacher"
        token = login_data["access_token"]

        me_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_response.status_code == 200
        assert me_response.json()["data"]["username"] == "teacher01"

        course_response = client.post(
            "/api/v1/courses",
            json={
                "name": "Pytest Demo Course",
                "term": "2026-Spring",
                "description": "Course used by automated integration test",
                "teacher_id": 1,
            },
        )
        assert course_response.status_code == 200
        course_id = course_response.json()["data"]["id"]

        class_response = client.post(
            "/api/v1/classes",
            json={
                "course_id": course_id,
                "name": "Pytest Demo Class",
                "invite_code": "PYTEST2026",
            },
        )
        assert class_response.status_code == 200
        class_id = class_response.json()["data"]["id"]

        join_response = client.post(
            f"/api/v1/classes/{class_id}/join",
            json={"invite_code": "PYTEST2026", "student_id": 2},
        )
        assert join_response.status_code == 200
        assert join_response.json()["data"]["status"] == "joined"

        task_response = client.post(
            "/api/v1/tasks",
            json={
                "course_id": course_id,
                "class_id": class_id,
                "title": "Regular Script Drill",
                "description": "Validate teacher publish task flow",
                "practice_chars": ["yong", "zhong", "he"],
                "structure_weight": 40,
                "center_weight": 30,
                "stroke_order_weight": 30,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert task_response.status_code == 200
        task_id = task_response.json()["data"]["id"]

        _slogin = client.post("/api/v1/auth/login", json={"username": "student01", "password": "123456"})
        _stok = _slogin.json()["data"]["access_token"]
        homework_response = client.post(
            "/api/v1/homework",
            json={
                "task_id": task_id,
                "student_id": 2,
                "image_url": "/uploads/homework/2/test-demo.png",
            },
            headers={"Authorization": f"Bearer {_stok}"},
        )
        assert homework_response.status_code == 200
        homework_id = homework_response.json()["data"]["id"]

        evaluation_response = client.post(
            "/api/v1/evaluation/start",
            json={"homework_id": homework_id},
        )
        assert evaluation_response.status_code == 200
        assert evaluation_response.json()["data"]["homework_id"] == homework_id

        evaluation_detail_response = client.get(f"/api/v1/evaluation/{homework_id}")
        assert evaluation_detail_response.status_code == 200
        assert evaluation_detail_response.json()["data"]["total_score"] > 0

        review_response = client.post(
            "/api/v1/reviews",
            json={
                "homework_id": homework_id,
                "teacher_id": 1,
                "comment": "Structure looks stable. Keep improving the horizontal stroke.",
                "final_score": 91,
                "status": "reviewed",
            },
        )
        assert review_response.status_code == 200
        assert review_response.json()["data"]["status"] == "reviewed"

        dashboard_response = client.get(f"/api/v1/dashboard/class/{class_id}")
        assert dashboard_response.status_code == 200
        dashboard_data = dashboard_response.json()["data"]
        assert dashboard_data["class_id"] == class_id
        assert dashboard_data["task_count"] >= 1

        report_response = client.get(f"/api/v1/reports/class/{class_id}")
        assert report_response.status_code == 200
        assert report_response.json()["data"]["class_id"] == class_id


def test_homework_upload_and_openai_switch(monkeypatch):
    with TestClient(app) as client:
        _tlogin = client.post("/api/v1/auth/login", json={"username": "teacher01", "password": "123456"})
        _ttok = _tlogin.json()["data"]["access_token"]
        task_response = client.post(
            "/api/v1/tasks",
            json={
                "course_id": 1,
                "class_id": 1,
                "title": "OpenAI Visual Test",
                "description": "Validate upload and provider switch flow",
                "practice_chars": ["yong"],
                "structure_weight": 40,
                "center_weight": 30,
                "stroke_order_weight": 30,
            },
            headers={"Authorization": f"Bearer {_ttok}"},
        )
        assert task_response.status_code == 200
        task_id = task_response.json()["data"]["id"]

        # 1x1 有效 PNG（PIL 生成的测试用最小图片）
        import io as _io
        try:
            from PIL import Image as _PIL
            _buf = _io.BytesIO()
            _PIL.new("RGB", (1, 1), color=255).save(_buf, "PNG")
            _min_png = _buf.getvalue()
        except ImportError:
            _min_png = b""
        _slogin = client.post("/api/v1/auth/login", json={"username": "student01", "password": "123456"})
        _stok = _slogin.json()["data"]["access_token"]
        upload_response = client.post(
            "/api/v1/homework/upload",
            files={"file": ("demo.png", _min_png, "image/png")},
            data={"task_id": str(task_id)},
            headers={"Authorization": f"Bearer {_stok}"},
        )
        assert upload_response.status_code == 200
        homework_id = upload_response.json()["data"]["homework_id"]

        monkeypatch.setattr(OpenAIEvaluationService, "is_configured", staticmethod(lambda: True))
        monkeypatch.setattr(
            OpenAIEvaluationService,
            "score",
            staticmethod(
                lambda *args, **kwargs: CalligraphyScoreOutput(
                    score=93,
                    tags=["stable structure", "clear main stroke"],
                    advice="Keep the main stroke steady and tighten the side structure.",
                )
            ),
        )

        evaluation_response = client.post(
            "/api/v1/evaluation/start",
            json={"homework_id": homework_id, "provider": "openai", "force_refresh": True},
        )
        assert evaluation_response.status_code == 200
        assert evaluation_response.json()["data"]["provider"] == "openai"

        evaluation_detail_response = client.get(f"/api/v1/evaluation/{homework_id}")
        assert evaluation_detail_response.status_code == 200
        detail = evaluation_detail_response.json()["data"]
        assert detail["score"] == 93
        assert detail["tags"] == ["stable structure", "clear main stroke"]

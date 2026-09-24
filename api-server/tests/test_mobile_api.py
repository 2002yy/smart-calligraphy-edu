from fastapi.testclient import TestClient

from app.main import app
from app.services.qwen_evaluation_service import QwenEvaluationService


def _tiny_png() -> bytes:
    import io

    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (1, 1), color=255).save(buffer, "PNG")
    return buffer.getvalue()


def test_mobile_student_mvp_flow(monkeypatch):
    monkeypatch.setattr(QwenEvaluationService, "is_configured", staticmethod(lambda: False))

    with TestClient(app) as client:
        teacher_login = client.post("/api/v1/auth/login", json={"username": "teacher01", "password": "123456"})
        teacher_token = teacher_login.json()["data"]["access_token"]

        course_response = client.post(
            "/api/v1/courses",
            json={"name": "Mobile Demo Course", "term": "2026-Spring", "description": "Mobile API test"},
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert course_response.status_code == 200
        course_id = course_response.json()["data"]["id"]

        class_response = client.post(
            "/api/v1/classes",
            json={"course_id": course_id, "name": "Mobile Demo Class", "invite_code": "MOBILE2026"},
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert class_response.status_code == 200
        class_id = class_response.json()["data"]["id"]

        login_response = client.post("/api/mobile/login", json={"username": "student01", "password": "123456"})
        assert login_response.status_code == 200
        login_data = login_response.json()["data"]
        assert login_data["user"]["role"] == "student"
        student_token = login_data["access_token"]

        me_response = client.get("/api/mobile/me", headers={"Authorization": f"Bearer {student_token}"})
        assert me_response.status_code == 200
        assert me_response.json()["data"]["username"] == "student01"

        join_response = client.post(
            "/api/mobile/classes/join",
            json={"invite_code": "MOBILE2026"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert join_response.status_code == 200
        assert join_response.json()["data"]["class_id"] == class_id

        task_response = client.post(
            "/api/v1/tasks",
            json={
                "course_id": course_id,
                "class_id": class_id,
                "title": "Mobile Upload Drill",
                "description": "Upload from mini program",
                "practice_chars": ["永"],
                "structure_weight": 40,
                "center_weight": 30,
                "stroke_order_weight": 30,
            },
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert task_response.status_code == 200
        task_id = task_response.json()["data"]["id"]

        tasks_response = client.get("/api/mobile/tasks", headers={"Authorization": f"Bearer {student_token}"})
        assert tasks_response.status_code == 200
        assert any(item["id"] == task_id for item in tasks_response.json()["data"])

        submit_response = client.post(
            "/api/mobile/submissions",
            data={"task_id": str(task_id)},
            files={"file": ("demo.png", _tiny_png(), "image/png")},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert submit_response.status_code == 200
        homework_id = submit_response.json()["data"]["id"]

        evaluate_response = client.post(
            f"/api/mobile/submissions/{homework_id}/evaluate",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert evaluate_response.status_code == 200
        assert evaluate_response.json()["data"]["status"] == "finished"

        result_response = client.get(
            f"/api/mobile/submissions/{homework_id}/result",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert result_response.status_code == 200
        result = result_response.json()["data"]
        assert result["homework_id"] == homework_id
        assert "score" in result
        assert result["details"][0]["name"] == "结构"

        progress_response = client.get("/api/mobile/profile/progress", headers={"Authorization": f"Bearer {student_token}"})
        assert progress_response.status_code == 200
        assert progress_response.json()["data"]["user_id"] == login_data["user"]["id"]

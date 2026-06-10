"""
标签统计与看板逻辑的正确性测试（否定弱「字段存在」测试）。

覆盖 7 个场景：
  1. tag count 是否正确
  2. ratio 是否正确
  3. 非白名单 tag 是否被过滤
  4. dashboard 是否需要登录
  5. 教师是否只能看自己班级
  6. tag 筛选是否限制在 class_id 内
  7. processing evaluation 是否不计入 evaluated_count
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal
from app.core.evaluation_tags import ALLOWED_TAGS
from app.services.qwen_evaluation_service import QwenEvaluationService


# ── Fixture ──

@pytest.fixture(autouse=True)
def _disable_qwen():
    """所有测试禁用 Qwen（使用 Mock 评测）。"""
    with patch.object(QwenEvaluationService, "is_configured", return_value=False):
        yield


# ── 辅助函数 ──

def _teacher_login(client):
    r = client.post("/api/v1/auth/login", json={"username": "teacher01", "password": "123456"})
    assert r.status_code == 200
    return r.json()["data"]["access_token"]


def _student_login(client):
    r = client.post("/api/v1/auth/login", json={"username": "student01", "password": "123456"})
    assert r.status_code == 200
    return r.json()["data"]["access_token"]


def _make_course_class_task(client, token, suffix=""):
    """快速创建 course → class → task，返回 (class_id, task_id)。"""
    cr = client.post("/api/v1/courses", json={
        "name": f"T{suffix}", "term": "2026", "description": "",
    }, headers={"Authorization": f"Bearer {token}"})
    cid = cr.json()["data"]["id"]

    cl = client.post("/api/v1/classes", json={
        "course_id": cid, "name": f"C{suffix}", "invite_code": f"X{suffix}",
    }, headers={"Authorization": f"Bearer {token}"})
    clid = cl.json()["data"]["id"]

    tk = client.post("/api/v1/tasks", json={
        "course_id": cid, "class_id": clid, "title": f"T{suffix}", "description": "",
        "practice_chars": ["永"], "structure_weight": 40,
        "center_weight": 30, "stroke_order_weight": 30,
    }, headers={"Authorization": f"Bearer {token}"})
    return clid, tk.json()["data"]["id"]


# ── 测试类 ──

class TestTagDashboardAccuracy:
    """标签统计与看板的逻辑正确性验证。"""

    # ── 场景 1 & 2 ──

    def test_tag_counts_and_ratios(self):
        """
        1. tag count 正确：迭代已知 evaluation → 汇总标签计数 → 与 dashboard 一致
        2. ratio 正确：ratio == round(count / evaluated_count, 2)
        """
        with TestClient(app) as client:
            ttoken = _teacher_login(client)
            class_id, task_id = _make_course_class_task(client, ttoken, "R")

            stok = _student_login(client)
            client.post(f"/api/v1/classes/{class_id}/join", json={"invite_code": "XR"},
                       headers={"Authorization": f"Bearer {stok}"})

            # 建 3 份作业 → mock 评测
            hw_ids = []
            for _ in range(3):
                hw = client.post("/api/v1/homework", json={
                    "task_id": task_id, "image_url": "/uploads/t.png",
                }, headers={"Authorization": f"Bearer {stok}"})
                hid = hw.json()["data"]["id"]
                client.post("/api/v1/evaluation/start", json={
                    "homework_id": hid, "provider": "mock", "force_refresh": True,
                }, headers={"Authorization": f"Bearer {stok}"})
                hw_ids.append(hid)

            # 从实际 evaluation API 读标签，汇总期望计数
            expected: dict[str, int] = {}
            for hid in hw_ids:
                ev = client.get(f"/api/v1/evaluation/{hid}", headers={"Authorization": f"Bearer {stok}"})
                for tag in ev.json()["data"]["tags"]:
                    expected[tag] = expected.get(tag, 0) + 1

            n = len(hw_ids)

            # ── 验证 dashboard 统计 ──
            dash = client.get(f"/api/v1/dashboard/class/{class_id}",
                             headers={"Authorization": f"Bearer {ttoken}"})
            assert dash.status_code == 200
            data = dash.json()["data"]

            # evaluated_count
            assert data["evaluated_count"] == n, \
                f"evaluated_count 应为 {n}, 实际 {data['evaluated_count']}"

            # 每个标签的 count & ratio
            stat_map = {s["tag"]: s for s in data["tag_stats"]}
            for tag, count in expected.items():
                assert tag in stat_map, f"标签 '{tag}' 不在 tag_stats 中"

                s = stat_map[tag]
                assert s["count"] == count, \
                    f"{tag}: count {s['count']} != {count}"
                assert s["ratio"] == round(count / n, 2), \
                    f"{tag}: ratio {s['ratio']} != {round(count / n, 2)}"

            # 无多余标签
            tags_in_stats = set(stat_map)
            assert tags_in_stats == set(expected), \
                f"多余/缺失标签: {tags_in_stats ^ set(expected)}"

    # ── 场景 3 ──

    def test_non_whitelist_tags_filtered(self):
        """
        3. 非白名单 tag 被过滤。
           即使 issues_json 包含非法标签，tag_stats 中也不会出现。
        """
        with TestClient(app) as client:
            ttoken = _teacher_login(client)
            class_id, task_id = _make_course_class_task(client, ttoken, "W")

            stok = _student_login(client)
            client.post(f"/api/v1/classes/{class_id}/join", json={"invite_code": "XW"},
                       headers={"Authorization": f"Bearer {stok}"})

            hw = client.post("/api/v1/homework", json={
                "task_id": task_id, "image_url": "/uploads/w.png",
            }, headers={"Authorization": f"Bearer {stok}"})
            hid = hw.json()["data"]["id"]

            client.post("/api/v1/evaluation/start", json={
                "homework_id": hid, "provider": "mock", "force_refresh": True,
            }, headers={"Authorization": f"Bearer {stok}"})

            # 注入非白名单标签（通过 ORM repository，避免 raw SQL NOT NULL 问题）
            from app.repositories.evaluation_repository import EvaluationRepository

            db = SessionLocal()
            try:
                ev = EvaluationRepository.get_by_homework_id(db, hid)
                tags = list(ev.issues_json or [])
                tags.append("非法标签_IGNORE_ME")
                tags.append("also_not_allowed_fake_tag")
                EvaluationRepository.update_evaluation(db, ev, issues=tags)
                db.commit()
            finally:
                db.close()

            dash = client.get(f"/api/v1/dashboard/class/{class_id}",
                             headers={"Authorization": f"Bearer {ttoken}"})
            assert dash.status_code == 200
            data = dash.json()["data"]

            # 非法标签不得出现
            for s in data["tag_stats"]:
                assert s["tag"] not in ("非法标签_IGNORE_ME", "also_not_allowed_fake_tag"), \
                    f"非白名单标签泄漏: {s['tag']}"

            # 白名单标签仍然存在
            assert len(data["tag_stats"]) > 0, "所有标签被过滤——白名单标签不应丢失"

            # 且所有在 tag_stats 中的标签都在 ALLOWED_TAGS 中
            for s in data["tag_stats"]:
                assert s["tag"] in ALLOWED_TAGS, \
                    f"标签 '{s['tag']}' 不在 ALLOWED_TAGS 中"

            # top_issues 也应已过滤非白名单标签
            for issue in data["top_issues"]:
                assert issue in ALLOWED_TAGS, \
                    f"top_issues 出现非白名单标签: {issue}"

    # ── 场景 4 ──

    def test_dashboard_requires_auth(self):
        """4. dashboard 无 token → 401"""
        with TestClient(app) as client:
            r = client.get("/api/v1/dashboard/class/1")
            assert r.status_code == 401

    # ── 场景 5 ──

    def test_teacher_only_sees_own_class(self):
        """
        5. 教师只能看自己班级的 dashboard。
           teacher01 尝试访问 teacher02 的班级 → 403。
        """
        # 创建 teacher02 及其课程/班级
        db = SessionLocal()
        try:
            import bcrypt
            from app.models.user import User
            from app.models.course import Course
            from app.models.classroom import Classroom

            t2 = User(
                username="t2_isolation_check",
                password_hash=bcrypt.hashpw(b"x", bcrypt.gensalt()).decode(),
                name="赵老师", role="teacher", school_name="川大",
            )
            db.add(t2)
            db.flush()

            c2 = Course(name="t2 专属课", term="2026", teacher_id=t2.id, status="active")
            db.add(c2)
            db.flush()

            cl2 = Classroom(course_id=c2.id, name="t2 专属班", invite_code="T2ONLY", student_count=0)
            db.add(cl2)
            db.commit()
            other_class_id = cl2.id
        finally:
            db.close()

        with TestClient(app) as client:
            ttoken = _teacher_login(client)
            r = client.get(f"/api/v1/dashboard/class/{other_class_id}",
                          headers={"Authorization": f"Bearer {ttoken}"})
            assert r.status_code == 403, \
                f"teacher01 应无法访问 teacher02 班级的 dashboard, 实际 {r.status_code}"

    # ── 场景 6 ──

    def test_tag_filter_scoped_to_class(self):
        """
        6. tag 筛选限制在 class_id 内。
           两个班级各有 1 份含标签 X 的作业。
           class_id=A & tag=X → 只返回 A 的作业，不返回 B 的。
        """
        with TestClient(app) as client:
            ttoken = _teacher_login(client)

            # 建两个班级（同课程，同属 teacher01）
            cr = client.post("/api/v1/courses", json={
                "name": "ScopeTest", "term": "2026", "description": "",
            }, headers={"Authorization": f"Bearer {ttoken}"})
            cid = cr.json()["data"]["id"]

            cl_a = client.post("/api/v1/classes", json={
                "course_id": cid, "name": "ScopeA", "invite_code": "SCOP_A",
            }, headers={"Authorization": f"Bearer {ttoken}"})
            aid = cl_a.json()["data"]["id"]

            cl_b = client.post("/api/v1/classes", json={
                "course_id": cid, "name": "ScopeB", "invite_code": "SCOP_B",
            }, headers={"Authorization": f"Bearer {ttoken}"})
            bid = cl_b.json()["data"]["id"]

            tk_a = client.post("/api/v1/tasks", json={
                "course_id": cid, "class_id": aid, "title": "TA", "description": "",
                "practice_chars": ["永"], "structure_weight": 40,
                "center_weight": 30, "stroke_order_weight": 30,
            }, headers={"Authorization": f"Bearer {ttoken}"})
            taid = tk_a.json()["data"]["id"]

            tk_b = client.post("/api/v1/tasks", json={
                "course_id": cid, "class_id": bid, "title": "TB", "description": "",
                "practice_chars": ["永"], "structure_weight": 40,
                "center_weight": 30, "stroke_order_weight": 30,
            }, headers={"Authorization": f"Bearer {ttoken}"})
            tbid = tk_b.json()["data"]["id"]

            stok = _student_login(client)
            client.post(f"/api/v1/classes/{aid}/join", json={"invite_code": "SCOP_A"},
                       headers={"Authorization": f"Bearer {stok}"})
            client.post(f"/api/v1/classes/{bid}/join", json={"invite_code": "SCOP_B"},
                       headers={"Authorization": f"Bearer {stok}"})

            # 各创建一份作业（不调用 evaluation，后续手动注入已知标签）
            ha = client.post("/api/v1/homework", json={
                "task_id": taid, "image_url": "/uploads/ha.png",
            }, headers={"Authorization": f"Bearer {stok}"})
            haid = ha.json()["data"]["id"]

            hb = client.post("/api/v1/homework", json={
                "task_id": tbid, "image_url": "/uploads/hb.png",
            }, headers={"Authorization": f"Bearer {stok}"})
            hbid = hb.json()["data"]["id"]

            # 手动注入含相同标签的 finished evaluation（通过 ORM repository）
            from app.repositories.evaluation_repository import EvaluationRepository

            COMMON_TAG = "重心不稳"
            db = SessionLocal()
            try:
                EvaluationRepository.create_evaluation(
                    db, homework_id=haid, status="finished",
                    total_score=7.0, issues=["重心不稳", "结构工整"],
                )
                EvaluationRepository.create_evaluation(
                    db, homework_id=hbid, status="finished",
                    total_score=7.0, issues=["重心不稳", "结构工整"],
                )
                db.commit()
            finally:
                db.close()

            # ── Class A ──
            ra = client.get(f"/api/v1/homework?class_id={aid}&tag={COMMON_TAG}",
                           headers={"Authorization": f"Bearer {ttoken}"})
            assert ra.status_code == 200
            da = ra.json()["data"]
            assert len(da) == 1, f"Class A tag 过滤: 期望 1 份, 实际 {len(da)}"
            assert da[0]["task_id"] == taid, \
                f"Class A 返回了错误的 task_id: {da[0]['task_id']}"

            # ── Class B ──
            rb = client.get(f"/api/v1/homework?class_id={bid}&tag={COMMON_TAG}",
                           headers={"Authorization": f"Bearer {ttoken}"})
            assert rb.status_code == 200
            db_list = rb.json()["data"]
            assert len(db_list) == 1, f"Class B tag 过滤: 期望 1 份, 实际 {len(db_list)}"
            assert db_list[0]["task_id"] == tbid, \
                f"Class B 返回了错误的 task_id: {db_list[0]['task_id']}"

    # ── 场景 7 ──

    def test_processing_evaluation_excluded(self):
        """
        7. processing / failed evaluation 不计入 evaluated_count 和标签统计。
           只有 status='finished' 的 evaluation 才被纳入。
        """
        with TestClient(app) as client:
            ttoken = _teacher_login(client)
            class_id, task_id = _make_course_class_task(client, ttoken, "P")

            stok = _student_login(client)
            client.post(f"/api/v1/classes/{class_id}/join", json={"invite_code": "XP"},
                       headers={"Authorization": f"Bearer {stok}"})

            # ── hw1: normal mock → finished ──
            h1 = client.post("/api/v1/homework", json={
                "task_id": task_id, "image_url": "/uploads/p1.png",
            }, headers={"Authorization": f"Bearer {stok}"})
            h1id = h1.json()["data"]["id"]
            client.post("/api/v1/evaluation/start", json={
                "homework_id": h1id, "provider": "mock", "force_refresh": True,
            }, headers={"Authorization": f"Bearer {stok}"})

            # 获取 hw1 的标签，用于后续断言
            ev1 = client.get(f"/api/v1/evaluation/{h1id}", headers={"Authorization": f"Bearer {stok}"})
            hw1_tags = ev1.json()["data"]["tags"]

            # ── hw2: 提交但不评测（无 evaluation 记录）──
            h2 = client.post("/api/v1/homework", json={
                "task_id": task_id, "image_url": "/uploads/p2.png",
            }, headers={"Authorization": f"Bearer {stok}"})

            # ── hw3: 提交 + 手动注入 processing evaluation ──
            h3 = client.post("/api/v1/homework", json={
                "task_id": task_id, "image_url": "/uploads/p3.png",
            }, headers={"Authorization": f"Bearer {stok}"})
            h3id = h3.json()["data"]["id"]

            from app.repositories.evaluation_repository import EvaluationRepository

            db = SessionLocal()
            try:
                EvaluationRepository.create_evaluation(
                    db, homework_id=h3id, status="processing",
                    total_score=0, issues=[],
                )
                db.commit()
            finally:
                db.close()

            # ── 验证 ──
            dash = client.get(f"/api/v1/dashboard/class/{class_id}",
                             headers={"Authorization": f"Bearer {ttoken}"})
            assert dash.status_code == 200
            data = dash.json()["data"]

            # evaluated_count 应仅为 1（只有 hw1 finished）
            assert data["evaluated_count"] == 1, \
                f"预期 evaluated_count=1 (仅 finished), 实际 {data['evaluated_count']}"

            # avg_score > 0
            assert data["avg_score"] > 0, "avg_score 应 > 0"

            # homework_count 应包含全部 3 个（都提交了）
            assert data["homework_count"] == 3, \
                f"homework_count 应为 3, 实际 {data['homework_count']}"

            # tag_stats 只反映 hw1 的标签（3 个，每个 count=1, ratio=1.0）
            assert len(data["tag_stats"]) == len(hw1_tags), \
                f"tag_stats 应与 hw1 标签数一致: {len(data['tag_stats'])} vs {len(hw1_tags)}"
            for s in data["tag_stats"]:
                assert s["count"] == 1, f"{s['tag']}: count 应为 1"
                assert s["ratio"] == 1.0, f"{s['tag']}: ratio 应为 1.0"

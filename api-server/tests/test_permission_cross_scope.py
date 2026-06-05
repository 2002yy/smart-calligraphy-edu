"""跨权限边界测试：有 token 但无权时返回 403。

设置两套完全隔离的上下文（A / B），各自有独立的 teacher/student/course/class/homework，
然后系统性地测试跨 A/B 访问全部返回 403。

使用 conftest.py 的 db_session fixture，不与 seed data 耦合。
"""

import bcrypt
import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.classroom import Classroom
from app.models.task import Task
from app.models.homework import Homework
from app.models.user import User
from app.repositories import ClassMemberRepository
from app.services.permission_service import (
    assert_can_export_report,
    assert_owns_class,
    assert_owns_course,
    assert_owns_homework,
    assert_teacher_can_view_student,
    assert_teacher_owns_task,
    assert_user_can_view_student,
)
from tests.conftest import assert_http_exception


# ── Fixture: 两套完全隔离的上下文 ────────────────────────


@pytest.fixture
def track_a(db_session: Session) -> dict:
    """创建 A 轨道：teacher_a → course_a → class_a → task_a → homework_a（student_a 的作业）。"""
    teacher = _make_user(db_session, "teacher_a", "Teacher A", "teacher")
    student = _make_user(db_session, "student_a", "Student A", "student")
    course = _make_course(db_session, "Course A", teacher)
    cls = _make_classroom(db_session, "Class A", course)
    task = _make_task(db_session, "Task A", cls, course, teacher)
    hw = _make_homework(db_session, task, student)
    _add_member(db_session, cls, student)
    return {
        "teacher": teacher,
        "student": student,
        "course": course,
        "class": cls,
        "task": task,
        "homework": hw,
    }


@pytest.fixture
def track_b(db_session: Session) -> dict:
    """创建 B 轨道：teacher_b → course_b → class_b → task_b → homework_b（student_b 的作业）。"""
    teacher = _make_user(db_session, "teacher_b", "Teacher B", "teacher")
    student = _make_user(db_session, "student_b", "Student B", "student")
    course = _make_course(db_session, "Course B", teacher)
    cls = _make_classroom(db_session, "Class B", course)
    task = _make_task(db_session, "Task B", cls, course, teacher)
    hw = _make_homework(db_session, task, student)
    _add_member(db_session, cls, student)
    return {
        "teacher": teacher,
        "student": student,
        "course": course,
        "class": cls,
        "task": task,
        "homework": hw,
    }


def _make_user(db: Session, username: str, name: str, role: str) -> User:
    u = User(
        username=username,
        password_hash=bcrypt.hashpw(b"p", bcrypt.gensalt()).decode(),
        name=name,
        role=role,
        school_name="Test University",
    )
    db.add(u)
    db.commit()
    return u


def _make_course(db: Session, name: str, teacher: User) -> Course:
    c = Course(name=name, term="2026-Spring", teacher_id=teacher.id, status="active")
    db.add(c)
    db.commit()
    return c


def _make_classroom(db: Session, name: str, course: Course) -> Classroom:
    cl = Classroom(course_id=course.id, name=name, invite_code=f"INVITE_{course.id}", student_count=0)
    db.add(cl)
    db.commit()
    return cl


def _make_task(db: Session, title: str, cls: Classroom, course: Course, teacher: User) -> Task:
    t = Task(
        course_id=course.id,
        class_id=cls.id,
        title=title,
        description="test task",
        structure_weight=40,
        center_weight=30,
        stroke_order_weight=30,
        created_by=teacher.id,
    )
    db.add(t)
    db.commit()
    return t


def _make_homework(db: Session, task: Task, student: User) -> Homework:
    hw = Homework(
        task_id=task.id,
        student_id=student.id,
        image_url="/uploads/test.png",
        status="submitted",
    )
    db.add(hw)
    db.commit()
    return hw


def _add_member(db: Session, cls: Classroom, student: User):
    ClassMemberRepository.create_member(db, class_id=cls.id, student_id=student.id)


def _as(role: str, user: User) -> dict:
    return {"id": user.id, "role": role}


# ── 跨教师访问（teacher_a 不能碰 teacher_b 的资源）─────────


class TestCrossTeacher:
    """teacher_a → teacher_b 权限边界。"""

    def test_cannot_view_other_course(self, db_session: Session, track_a: dict, track_b: dict):
        """teacher_a 不能查看/编辑 teacher_b 的课程。"""
        a = _as("teacher", track_a["teacher"])
        assert_http_exception(403, assert_owns_course, db_session, a, track_b["course"].id)

    def test_cannot_view_other_class(self, db_session: Session, track_a: dict, track_b: dict):
        """teacher_a 不能查看/编辑 teacher_b 的班级。"""
        a = _as("teacher", track_a["teacher"])
        assert_http_exception(403, assert_owns_class, db_session, a, track_b["class"].id)

    def test_cannot_review_other_homework(self, db_session: Session, track_a: dict, track_b: dict):
        """teacher_a 不能 review teacher_b 课程下的 homework。"""
        a = _as("teacher", track_a["teacher"])
        assert_http_exception(403, assert_owns_homework, db_session, a, track_b["homework"].id)

    def test_cannot_manage_other_task(self, db_session: Session, track_a: dict, track_b: dict):
        """teacher_a 不能 delete/update teacher_b 课程下的 task。"""
        a = _as("teacher", track_a["teacher"])
        assert_http_exception(403, assert_teacher_owns_task, db_session, a, track_b["task"].id)

    def test_cannot_export_other_class_report(self, db_session: Session, track_a: dict, track_b: dict):
        """teacher_a 不能导出 teacher_b 的班级报告。"""
        a = _as("teacher", track_a["teacher"])
        assert_http_exception(403, assert_can_export_report, db_session, a, "class", track_b["class"].id)

    def test_cannot_view_other_student(self, db_session: Session, track_a: dict, track_b: dict):
        """teacher_a 不能查看 teacher_b 班级的学生数据。"""
        a = _as("teacher", track_a["teacher"])
        assert_http_exception(403, assert_teacher_can_view_student, db_session, a, track_b["student"].id)

    def test_cannot_export_other_student_report(self, db_session: Session, track_a: dict, track_b: dict):
        """teacher_a 不能导出 teacher_b 班级学生的 report。"""
        a = _as("teacher", track_a["teacher"])
        assert_http_exception(403, assert_can_export_report, db_session, a, "student", track_b["student"].id)

    def test_cannot_create_class_on_other_course(self, db_session: Session, track_a: dict, track_b: dict):
        """teacher_a 不能在 teacher_b 的课程下创建班级（assert_owns_course）。"""
        a = _as("teacher", track_a["teacher"])
        assert_http_exception(403, assert_owns_course, db_session, a, track_b["course"].id)


# ── 跨学生访问（student_a 不能碰 student_b 的资源）─────────


class TestCrossStudent:
    """student_a → student_b 权限边界。"""

    def test_cannot_view_other_homework(self, db_session: Session, track_a: dict, track_b: dict):
        """student_a 不能查看 student_b 的 homework。"""
        a = _as("student", track_a["student"])
        assert_http_exception(403, assert_owns_homework, db_session, a, track_b["homework"].id)

    def test_cannot_export_other_report(self, db_session: Session, track_a: dict, track_b: dict):
        """student_a 不能导出 student_b 的 report。"""
        a = _as("student", track_a["student"])
        assert_http_exception(403, assert_can_export_report, db_session, a, "student", track_b["student"].id)

    def test_cannot_view_other_info(self, db_session: Session, track_a: dict, track_b: dict):
        """student_a 不能查看 student_b 的个人信息。"""
        a = _as("student", track_a["student"])
        assert_http_exception(403, assert_user_can_view_student, db_session, a, track_b["student"].id)


# ── 角色越界（student 不能做 teacher 的事）──────────────


class TestRoleBoundary:
    """角色越界测试。"""

    def test_student_cannot_access_teacher_class(self, db_session: Session, track_a: dict):
        """student 不能查看班级（assert_owns_class 内部由 require_role 兜底，但这里测 service 层）。"""
        a = _as("student", track_a["student"])
        assert_http_exception(403, assert_owns_class, db_session, a, track_a["class"].id)

    def test_student_cannot_access_teacher_course(self, db_session: Session, track_a: dict):
        """student 不能操作课程（assert_owns_course 会走到 teacher_id 比较失败? 但 teacher 不为 403 拦截，所以需看实现）。"""
        a = _as("student", track_a["student"])
        # assert_owns_course 不检查角色，只检查 teacher_id；student 的 id 与 teacher_id 不匹配 → 403
        assert_http_exception(403, assert_owns_course, db_session, a, track_a["course"].id)

    def test_student_cannot_export_class_report(self, db_session: Session, track_a: dict):
        """student 导出班级报告被拒。"""
        a = _as("student", track_a["student"])
        assert_http_exception(403, assert_can_export_report, db_session, a, "class", track_a["class"].id)

    def test_unknown_role_denied_homework(self, db_session: Session, track_a: dict):
        """unknown role 调 assert_owns_homework → 403。"""
        u = {"id": 999, "role": "unknown"}
        assert_http_exception(403, assert_owns_homework, db_session, u, track_a["homework"].id)

    def test_unknown_role_denied_export(self, db_session: Session, track_a: dict):
        """unknown role 调 assert_can_export_report → 403。"""
        u = {"id": 999, "role": "unknown"}
        assert_http_exception(403, assert_can_export_report, db_session, u, "student", track_a["student"].id)

    def test_unknown_role_denied_view_student(self, db_session: Session, track_a: dict):
        """unknown role 调 assert_user_can_view_student → 403。"""
        u = {"id": 999, "role": "unknown"}
        assert_http_exception(403, assert_user_can_view_student, db_session, u, track_a["student"].id)


# ── API 层集成测试（真实 HTTP 请求）────────────────────


class TestCrossScopeHTTP:
    """通过 HTTP client 验证跨越权场景。"""

    @pytest.fixture(autouse=True)
    def _setup(self, request):
        """标记 —— 让 pytest 在 class 级别注入。"""
        pass

    def _login(self, client, username: str, password: str = "123456") -> str:
        resp = client.post("/api/v1/auth/login", json={"username": username, "password": password})
        assert resp.status_code == 200
        return resp.json()["data"]["access_token"]

    def test_teacher_cannot_export_other_student_report(self):
        """teacher01 view non-class student report -> 403 (seed has only student01)."""
        from fastapi.testclient import TestClient
        from app.main import app

        with TestClient(app) as client:
            ttoken = self._login(client, "teacher01")
            # Seed only has student01 (id=2) in teacher01's class.
            # student id=3 doesn't exist in seed -> 404 from service (permission passes as teacher)
            resp = client.get("/api/v1/reports/student/3", headers={"Authorization": f"Bearer {ttoken}"})
            # user 3 not in teacher01's class -> 403
            assert resp.status_code == 403

    def test_teacher_list_student_report_same_class_succeeds(self):
        """teacher01 export own class student (student01 id=2) report -> 200."""
        from fastapi.testclient import TestClient
        from app.main import app

        with TestClient(app) as client:
            ttoken = self._login(client, "teacher01")
            # student01 id=2, in teacher01's class
            resp = client.get("/api/v1/reports/student/2", headers={"Authorization": f"Bearer {ttoken}"})
            assert resp.status_code == 200

    def test_student_cannot_list_class_report(self):
        """student 获取班级报告 → 403。"""
        from fastapi.testclient import TestClient
        from app.main import app

        with TestClient(app) as client:
            stok = self._login(client, "student01")
            resp = client.get("/api/v1/reports/class/1", headers={"Authorization": f"Bearer {stok}"})
            assert resp.status_code == 403

    def test_student_cannot_export_other_student_report_via_api(self):
        """student01 try to view teacher01 report -> 403 (cross-user)."""
        from fastapi.testclient import TestClient
        from app.main import app

        with TestClient(app) as client:
            stok = self._login(client, "student01")
            # student01 id=2, teacher01 id=1 -> view other -> 403
            resp = client.get("/api/v1/reports/student/1", headers={"Authorization": f"Bearer {stok}"})
            assert resp.status_code == 403

    def test_student_can_view_own_report(self):
        """student01 view own report (id=2) -> 200."""
        from fastapi.testclient import TestClient
        from app.main import app

        with TestClient(app) as client:
            stok = self._login(client, "student01")
            # student01 id=2
            resp = client.get("/api/v1/reports/student/2", headers={"Authorization": f"Bearer {stok}"})
            assert resp.status_code == 200

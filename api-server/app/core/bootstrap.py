import hashlib  # fallback
from datetime import UTC, datetime, timedelta

import bcrypt
from sqlalchemy import select

import app.models  # noqa: F401
from app.core.config import settings
from app.core.database import SessionLocal, init_db
from app.models.class_member import ClassMember
from app.models.classroom import Classroom
from app.models.course import Course
from app.models.evaluation import Evaluation
from app.models.task import Task
from app.models.task_character import TaskCharacter
from app.models.user import User


def recover_stuck_evaluations():
    """启动时将超过 30 分钟仍为 processing 的评测标记为 failed。

    Qwen 异步线程在服务重启后会中断，卡住的 processing 记录会永远卡住。
    此函数确保这些记录在下次启动时被清理。
    """
    db = SessionLocal()
    try:
        cutoff = datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=30)
        stuck = db.scalars(
            select(Evaluation).where(
                Evaluation.status == "processing",
                Evaluation.updated_at < cutoff,
            )
        ).all()
        for ev in stuck:
            ev.status = "failed"
            ev.advice_text = "评测因服务重启中断，请重新提交评测。"
        if stuck:
            db.commit()
        # 不打印日志——pytest 抓取 stdout 可能误报
    finally:
        db.close()


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode()


def seed_demo_data():
    db = SessionLocal()
    try:
        existing_user = db.scalar(select(User).limit(1))
        if existing_user:
            return

        pw = _hash(settings.demo_password)
        teacher = User(
            username="teacher01",
            password_hash=pw,
            name="刘老师",
            role="teacher",
            school_name="四川大学",
        )
        student = User(
            username="student01",
            password_hash=pw,
            name="张三",
            role="student",
            school_name="四川大学",
        )
        db.add_all([teacher, student])
        db.flush()

        course = Course(
            name="大学生书法素养提升课",
            term="2026春",
            teacher_id=teacher.id,
            description="面向非书法专业学生的基础书法训练课程",
            status="active",
        )
        db.add(course)
        db.flush()

        classroom = Classroom(
            course_id=course.id,
            name="2026春季1班",
            invite_code="CALLI2026",
            student_count=1,
        )
        db.add(classroom)
        db.flush()

        db.add(ClassMember(class_id=classroom.id, student_id=student.id))

        task = Task(
            course_id=course.id,
            class_id=classroom.id,
            title="欧楷基本笔画训练",
            description="掌握横、竖、撇、捺的基础书写方式",
            structure_weight=40,
            center_weight=30,
            stroke_order_weight=30,
            created_by=teacher.id,
        )
        db.add(task)
        db.flush()

        db.add_all(
            [
                TaskCharacter(task_id=task.id, character="永", sort_order=1),
                TaskCharacter(task_id=task.id, character="大", sort_order=2),
                TaskCharacter(task_id=task.id, character="木", sort_order=3),
                TaskCharacter(task_id=task.id, character="中", sort_order=4),
            ]
        )

        db.commit()
    finally:
        db.close()


def bootstrap_database():
    init_db()
    seed_demo_data()

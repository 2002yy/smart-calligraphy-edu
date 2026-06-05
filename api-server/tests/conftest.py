import atexit
import hashlib  # fallback
import bcrypt
import os
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# ---- Existing file-based DB (used by E2E tests) ----
TEST_DB_PATH = ROOT_DIR / "test_smart_calligraphy.db"
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"


@atexit.register
def cleanup_test_db():
    try:
        from app.core.database import engine
        engine.dispose()
    except Exception:
        pass
    if TEST_DB_PATH.exists():
        try:
            TEST_DB_PATH.unlink()
        except PermissionError:
            pass


# ---- In-memory fixtures for focused service-layer tests ----

@pytest.fixture(scope="function")
def db_session():
    """Provide a clean in-memory SQLite session per test function."""
    engine = create_engine("sqlite:///:memory:", echo=False, connect_args={"check_same_thread": False})
    maker = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    from app.core.database import Base
    Base.metadata.create_all(bind=engine)

    session = maker()
    try:
        yield session
    finally:
        session.close()


# -------- Domain object factories --------

@pytest.fixture
def teacher_user(db_session: Session):
    from app.models.user import User
    user = User(username="teacher01", password_hash=bcrypt.hashpw(b"test_pass", bcrypt.gensalt()).decode(), name="刘老师", role="teacher", school_name="四川大学")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def student_user(db_session: Session):
    from app.models.user import User
    user = User(username="student01", password_hash=bcrypt.hashpw(b"test_pass", bcrypt.gensalt()).decode(), name="张三", role="student", school_name="四川大学")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def seeded_course(db_session: Session, teacher_user):
    from app.models.course import Course
    course = Course(name="书法课", term="2026春", teacher_id=teacher_user.id, description="基础课程", status="active")
    db_session.add(course)
    db_session.commit()
    return course


@pytest.fixture
def seeded_classroom(db_session: Session, seeded_course):
    from app.models.classroom import Classroom
    cls_room = Classroom(course_id=seeded_course.id, name="2026春季1班", invite_code="CALLI2026", student_count=1)
    db_session.add(cls_room)
    db_session.commit()
    return cls_room


@pytest.fixture
def seeded_task(db_session: Session, seeded_course, seeded_classroom, teacher_user):
    from app.models.task import Task
    from app.models.task_character import TaskCharacter
    task = Task(
        course_id=seeded_course.id, class_id=seeded_classroom.id,
        title="欧楷基本笔画训练", description="横竖撇捺基础",
        structure_weight=40, center_weight=30, stroke_order_weight=30,
        created_by=teacher_user.id,
    )
    db_session.add(task)
    db_session.flush()
    chars = [TaskCharacter(task_id=task.id, character=c, sort_order=i)
             for i, c in enumerate(["永", "大", "木", "中"], 1)]
    db_session.add_all(chars)
    db_session.commit()
    return task


@pytest.fixture
def seeded_homework(db_session: Session, seeded_task, student_user):
    from app.models.homework import Homework
    hw = Homework(task_id=seeded_task.id, student_id=student_user.id,
                  image_url="/uploads/test.png", status="submitted")
    db_session.add(hw)
    db_session.commit()
    return hw


def assert_http_exception(status_code: int, func, *args, **kwargs):
    """Assert that *func* raises HTTPException with the expected status."""
    with pytest.raises(HTTPException) as exc_info:
        func(*args, **kwargs)
    assert exc_info.value.status_code == status_code

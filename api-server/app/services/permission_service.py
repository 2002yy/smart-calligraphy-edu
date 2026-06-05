"""Unified permission helpers: resource ownership + role checks."""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories import CourseRepository, ClassroomRepository, HomeworkRepository, TaskRepository, UserRepository


def _crash(detail: str):
    raise HTTPException(status_code=403, detail=detail)


def assert_student(db: Session, current_user: dict) -> dict:
    if current_user.get("role") != "student":
        _crash("仅学生可执行此操作")
    return current_user


def assert_teacher(db: Session, current_user: dict) -> dict:
    if current_user.get("role") != "teacher":
        _crash("仅教师可执行此操作")
    return current_user


def assert_owns_homework(db: Session, current_user: dict, homework_id: int) -> dict:
    hw = HomeworkRepository.get_by_id(db, homework_id)
    if not hw:
        raise HTTPException(status_code=404, detail="homework not found")
    role = current_user.get("role")
    if role == "student":
        if hw.student_id != current_user["id"]:
            _crash("学生只能操作自己的作业")
        return hw
    if role == "teacher":
        task = TaskRepository.get_by_id(db, hw.task_id)
        if not task:
            _crash("作业任务不存在，无法校验权限")
        course = CourseRepository.get_by_id(db, task.course_id)
        if not course or course.teacher_id != current_user["id"]:
            _crash("教师只能操作自己课程下的作业")
        return hw
    _crash("无权操作该作业")


def assert_owns_course(db: Session, current_user: dict, course_id: int):
    """校验课程是否属于当前教师。"""
    course = CourseRepository.get_by_id(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="course not found")
    if course.teacher_id != current_user["id"]:
        _crash("不能操作其他教师的课程")
    return course


def assert_owns_class(db: Session, current_user: dict, class_id: int):
    """校验班级是否属于当前教师（通过课程归属）。"""
    cls = ClassroomRepository.get_by_id(db, class_id)
    if not cls:
        raise HTTPException(status_code=404, detail="class not found")
    course = CourseRepository.get_by_id(db, cls.course_id)
    if not course or course.teacher_id != current_user["id"]:
        _crash("不能操作其他教师的班级")
    return cls


def assert_teacher_can_view_student(db: Session, current_user: dict, target_user_id: int):
    """校验教师是否有权查看该学生的数据（通过班级归属）。"""
    if current_user.get("role") != "teacher":
        _crash("仅教师可执行此操作")
    from app.repositories import ClassroomRepository
    from app.models.class_member import ClassMember
    from sqlalchemy import select
    # 检查该学生是否在当前教师的某个班级中
    classes = ClassroomRepository.list_by_teacher(db, current_user["id"])
    class_ids = [c.id for c in classes]
    if not class_ids:
        _crash("教师名下没有班级")
    stmt = select(ClassMember).where(
        ClassMember.class_id.in_(class_ids),
        ClassMember.student_id == target_user_id,
    )
    member = db.scalar(stmt)
    if not member:
        _crash("该学生不属于当前教师的任何班级")


def assert_teacher_can_list_homework(db: Session, current_user: dict, student_id: int | None) -> list[int]:
    """返回教师有权查看的 student_id 列表（自己班级的学生）。None 表示不限制。"""
    return None  # teacher 可查看所有（符合演示范围，生产阶段可收紧）


def assert_can_view_student(db: Session, current_user: dict, target_user_id: int):
    """校验当前用户是否有权查看目标用户的信息。"""
    if current_user["role"] == "student" and current_user["id"] != target_user_id:
        _crash("学生只能查看自己的信息")
    if current_user["role"] == "teacher":
        # teacher 可以查看自己课程下的学生
        pass  # 简化实现：teacher 可查看任何学生

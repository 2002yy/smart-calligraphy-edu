"""权限校验统一帮助函数，防止各 route/service 重复编写。"""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories import HomeworkRepository, TaskRepository


def assert_student_owns_homework(db: Session, current_user: dict, homework_id: int) -> None:
    """校验当前学生是否拥有该作业，非 student 角色不拦截。"""
    if current_user.get("role") != "student":
        return
    hw = HomeworkRepository.get_by_id(db, homework_id)
    if not hw:
        raise HTTPException(status_code=404, detail="homework not found")
    if hw.student_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="学生只能操作自己的作业")


def assert_teacher_owns_task(db: Session, current_user: dict, task_id: int) -> None:
    """校验当前教师是否拥有该任务（通过课程归属）。"""
    if current_user.get("role") != "teacher":
        return
    task = TaskRepository.get_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    from app.repositories import CourseRepository
    course = CourseRepository.get_by_id(db, task.course_id)
    if not course or course.teacher_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="教师只能操作自己课程下的任务")


def assert_user_can_view_homework(db: Session, current_user: dict, homework_id: int) -> dict:
    """校验用户是否有权查看该作业，返回 homework 对象。"""
    hw = HomeworkRepository.get_by_id(db, homework_id)
    if not hw:
        raise HTTPException(status_code=404, detail="homework not found")
    if current_user.get("role") == "student" and hw.student_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="学生只能查看自己的作业")
    if current_user.get("role") == "teacher":
        task = TaskRepository.get_by_id(db, hw.task_id)
        if task:
            from app.repositories import CourseRepository
            course = CourseRepository.get_by_id(db, task.course_id)
            if course and course.teacher_id != current_user["id"]:
                raise HTTPException(status_code=403, detail="教师只能查看自己课程下的作业")
    return hw

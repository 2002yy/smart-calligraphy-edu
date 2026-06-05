from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import APIResponse
from app.schemas.task import TaskCreate, TaskRead
from app.services import TaskService
from app.services.auth_service import get_current_user, require_role
from app.services.permission_service import assert_teacher_owns_task

router = APIRouter()


@router.get(
    "",
    response_model=APIResponse[list[TaskRead]],
    summary="获取任务列表",
)
def list_tasks(
    class_id: int | None = None,
    course_id: int | None = None,
    db: Session = Depends(get_db),
):
    data = [TaskRead(**item) for item in TaskService.list_tasks(db, class_id=class_id, course_id=course_id)]
    return APIResponse[list[TaskRead]](data=data)


@router.post(
    "",
    response_model=APIResponse[TaskRead],
    summary="创建教学任务",
)
def create_task(payload: TaskCreate, current_user: dict = Depends(require_role(["teacher"])), db: Session = Depends(get_db)):
    payload.created_by = current_user["id"]
    data = TaskRead(**TaskService.create_task(db, payload))
    return APIResponse[TaskRead](data=data)


@router.get(
    "/{task_id}",
    response_model=APIResponse[TaskRead],
    summary="获取任务详情",
)
def get_task(task_id: int, db: Session = Depends(get_db)):
    data = TaskRead(**TaskService.get_task(db, task_id))
    return APIResponse[TaskRead](data=data)


@router.delete(
    "/{task_id}",
    response_model=APIResponse[dict],
    summary="删除任务",
)
def delete_task(task_id: int, current_user: dict = Depends(require_role(["teacher"])), db: Session = Depends(get_db)):
    assert_teacher_owns_task(db, current_user, task_id)
    TaskService.delete_task(db, task_id)
    return APIResponse[dict](data={"deleted": True})

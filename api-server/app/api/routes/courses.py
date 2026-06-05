from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import APIResponse
from app.schemas.course import CourseCreate, CourseRead
from app.services import CourseService
from app.services.auth_service import require_role
from app.services.auth_service import get_current_user, require_role

router = APIRouter()


@router.get(
    "",
    response_model=APIResponse[list[CourseRead]],
    summary="获取课程列表",
    description="支持按教师 ID 和课程状态筛选，适合教师端课程首页展示。",
)
def list_courses(
    teacher_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    data = [CourseRead(**item) for item in CourseService.list_courses(db, teacher_id=teacher_id, status=status)]
    return APIResponse[list[CourseRead]](data=data)


@router.post(
    "",
    response_model=APIResponse[CourseRead],
    summary="创建课程",
    description="教师创建一门新课程，Swagger 中可直接使用示例请求体进行答辩演示。",
)
def create_course(payload: CourseCreate, current_user: dict = Depends(require_role(["teacher"])), db: Session = Depends(get_db)):
    data = CourseRead(**CourseService.create_course(db, payload))
    return APIResponse[CourseRead](data=data)


@router.get(
    "/{course_id}",
    response_model=APIResponse[CourseRead],
    summary="获取课程详情",
)
def get_course(course_id: int, db: Session = Depends(get_db)):
    data = CourseRead(**CourseService.get_course(db, course_id))
    return APIResponse[CourseRead](data=data)

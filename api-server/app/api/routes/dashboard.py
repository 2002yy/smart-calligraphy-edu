from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import APIResponse
from app.schemas.dashboard import DashboardRead
from app.services import DashboardService
from app.services.auth_service import require_role
from app.services.permission_service import assert_owns_class

router = APIRouter()


@router.get(
    "/class/{class_id}",
    response_model=APIResponse[DashboardRead],
    summary="获取班级教学看板",
    description="返回班级作业提交率、平均得分、共性问题等统计信息，适合答辩演示数据大屏。仅教师可访问，且只能访问自己课程下的班级。",
)
def get_dashboard(
    class_id: int,
    current_user: dict = Depends(require_role(["teacher"])),
    db: Session = Depends(get_db),
):
    assert_owns_class(db, current_user, class_id)
    data = DashboardRead(**DashboardService.build_class_dashboard(db, class_id))
    return APIResponse[DashboardRead](data=data)

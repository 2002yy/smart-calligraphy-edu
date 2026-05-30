from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import APIResponse
from app.schemas.dashboard import DashboardRead
from app.services import DashboardService

router = APIRouter()


@router.get(
    "/class/{class_id}",
    response_model=APIResponse[DashboardRead],
    summary="获取班级教学看板",
    description="返回班级作业提交率、平均得分、共性问题等统计信息，适合答辩演示数据大屏。",
)
def get_dashboard(class_id: int, db: Session = Depends(get_db)):
    data = DashboardRead(**DashboardService.build_class_dashboard(db, class_id))
    return APIResponse[DashboardRead](data=data)

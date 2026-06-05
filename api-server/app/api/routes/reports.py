from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import APIResponse
from app.schemas.report import ClassReportRead, ReportExportRead, ReportExportRequest, StudentReportRead
from app.services import ReportService
from app.services.auth_service import require_role

router = APIRouter()


@router.get(
    "/student/{student_id}",
    response_model=APIResponse[StudentReportRead],
    summary="获取学生成长报告",
)
def student_report(student_id: int, db: Session = Depends(get_db)):
    data = StudentReportRead(**ReportService.student_report(db, student_id))
    return APIResponse[StudentReportRead](data=data)


@router.get(
    "/class/{class_id}",
    response_model=APIResponse[ClassReportRead],
    summary="获取班级统计报告",
)
def class_report(class_id: int, db: Session = Depends(get_db)):
    data = ClassReportRead(**ReportService.class_report(db, class_id))
    return APIResponse[ClassReportRead](data=data)


@router.post(
    "/export",
    response_model=APIResponse[ReportExportRead],
    summary="导出报告文件",
    description="支持导出学生报告或班级报告，当前返回可演示的文件路径与生成时间。",
)
def export_report(payload: ReportExportRequest):
    data = ReportExportRead(**ReportService.export_report(payload.type, payload.target_id, payload.format))
    return APIResponse[ReportExportRead](data=data)

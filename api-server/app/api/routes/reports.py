from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import APIResponse
from app.schemas.report import ClassReportRead, ReportExportRead, ReportExportRequest, StudentReportRead, StudentTagTrendRead
from app.services import ReportService
from app.services.auth_service import get_current_user, require_role
from app.services.permission_service import assert_can_export_report, assert_owns_class, assert_user_can_view_student

router = APIRouter()


@router.get(
    "/student/{student_id}",
    response_model=APIResponse[StudentReportRead],
    summary="获取学生成长报告",
)
def student_report(student_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    assert_user_can_view_student(db, current_user, student_id)
    data = StudentReportRead(**ReportService.student_report(db, student_id))
    return APIResponse[StudentReportRead](data=data)


@router.get(
    "/student/{student_id}/tag-trend",
    response_model=APIResponse[StudentTagTrendRead],
    summary="获取学生标签变化趋势",
    description="返回学生历次评测的标签记录、反复出现的问题标签、以及有改善趋势的标签。",
)
def student_tag_trend(student_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.services.permission_service import assert_user_can_view_student
    assert_user_can_view_student(db, current_user, student_id)
    data = StudentTagTrendRead(**ReportService.student_tag_trend(db, student_id))
    return APIResponse[StudentTagTrendRead](data=data)


@router.get(
    "/class/{class_id}",
    response_model=APIResponse[ClassReportRead],
    summary="获取班级统计报告",
)
def class_report(class_id: int, current_user: dict = Depends(require_role(["teacher"])), db: Session = Depends(get_db)):
    assert_owns_class(db, current_user, class_id)
    data = ClassReportRead(**ReportService.class_report(db, class_id))
    return APIResponse[ClassReportRead](data=data)


@router.post(
    "/export",
    response_model=APIResponse[ReportExportRead],
    summary="导出报告文件",
    description="支持导出学生报告或班级报告，当前返回可演示的文件路径与生成时间。",
)
def export_report(payload: ReportExportRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    assert_can_export_report(db, current_user, payload.type, payload.target_id)
    data = ReportExportRead(**ReportService.export_report(payload.type, payload.target_id, payload.format))
    return APIResponse[ReportExportRead](data=data)

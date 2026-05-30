from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.classroom import ClassCreate, ClassJoinRead, ClassJoinRequest, ClassMembersRead, ClassRead
from app.schemas.common import APIResponse
from app.services import ClassService

router = APIRouter()


@router.get(
    "",
    response_model=APIResponse[list[ClassRead]],
    summary="获取班级列表",
    description="支持按课程筛选，适用于教师端班级管理页面。",
)
def list_classes(course_id: int | None = None, db: Session = Depends(get_db)):
    data = [ClassRead(**item) for item in ClassService.list_classes(db, course_id=course_id)]
    return APIResponse[list[ClassRead]](data=data)


@router.post(
    "",
    response_model=APIResponse[ClassRead],
    summary="创建班级",
)
def create_class(payload: ClassCreate, db: Session = Depends(get_db)):
    data = ClassRead(**ClassService.create_class(db, payload))
    return APIResponse[ClassRead](data=data)


@router.post(
    "/{class_id}/join",
    response_model=APIResponse[ClassJoinRead],
    summary="学生加入班级",
)
def join_class(class_id: int, payload: ClassJoinRequest, db: Session = Depends(get_db)):
    data = ClassJoinRead(**ClassService.join_class(db, class_id, payload))
    return APIResponse[ClassJoinRead](data=data)


@router.get(
    "/{class_id}/members",
    response_model=APIResponse[ClassMembersRead],
    summary="获取班级成员",
)
def get_members(class_id: int, db: Session = Depends(get_db)):
    data = ClassMembersRead(**ClassService.get_members(db, class_id))
    return APIResponse[ClassMembersRead](data=data)

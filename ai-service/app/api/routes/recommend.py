from fastapi import APIRouter

router = APIRouter()


@router.post("")
def recommend_practice():
    return {"code": 0, "message": "ok", "data": {"chars": ["都", "部", "郭"]}}


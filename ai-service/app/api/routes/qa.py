from fastapi import APIRouter

router = APIRouter()


@router.post("")
def ask_calligraphy():
    return {"code": 0, "message": "ok", "data": {"answer": "这里是书法知识问答占位接口。"}}

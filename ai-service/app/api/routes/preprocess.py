from fastapi import APIRouter

router = APIRouter()


@router.post("")
def preprocess_image():
    return {"code": 0, "message": "ok", "data": {"status": "preprocessed"}}


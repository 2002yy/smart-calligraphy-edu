from fastapi import APIRouter

router = APIRouter()


@router.post("")
def segment_characters():
    return {"code": 0, "message": "ok", "data": {"status": "segmented"}}


from fastapi import APIRouter

router = APIRouter()


@router.post("")
def score_image():
    return {
        "code": 0,
        "message": "ok",
        "data": {
            "total_score": 84,
            "sub_scores": {
                "structure": 86,
                "center": 80,
                "stroke_order": 87
            },
            "issues": ["右部偏窄", "横画不足"]
        }
    }


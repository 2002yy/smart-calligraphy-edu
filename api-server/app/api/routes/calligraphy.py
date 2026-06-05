"""碑帖查询路由

提供按字检索名家碑帖的功能，用于学生端作业评测结果页的"相关碑帖"展示。
"""

import sqlite3
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from app.schemas.common import APIResponse
from pydantic import BaseModel

ALLOWED_PATH_PREFIXES = ("/uploads/", "/storage/calligraphy_db/")
FORBIDDEN_PATTERNS = ("..", "\\", "//", "~")


def _validate_sign_path(path: str) -> str:
    """校验签名路径：禁止 ..、反斜杠、绝对路径、外部 URL、不合法前缀"""
    if not path.startswith("/"):
        raise HTTPException(status_code=400, detail="路径必须以 / 开头")
    if any(p in path for p in FORBIDDEN_PATTERNS):
        raise HTTPException(status_code=400, detail="路径包含非法字符")
    if not path.startswith(ALLOWED_PATH_PREFIXES):
        raise HTTPException(status_code=400, detail=f"仅支持 {'、'.join(ALLOWED_PATH_PREFIXES)} 路径")
    return path


router = APIRouter()


class CalligraphyMatch(BaseModel):
    character: str
    image_url: str


@router.get(
    "/sign",
    summary="获取图片签名 URL",
    description="传入图片路径，返回带签名的临时 URL（用于 SECURE_STATIC=true 时 <img> 加载）。",
)
def sign_image(
    path: str = Query(..., description="图片路径，如 /uploads/homework/2/1/xxx.jpg"),
):
    path = _validate_sign_path(path)
    from app.services.token_service import sign_image_path
    token = sign_image_path(path)
    return APIResponse(data={"signed_url": f"{path}?token={token}"})


@router.get(
    "/match",
    response_model=APIResponse[list[CalligraphyMatch]],
    summary="按字查询名家碑帖",
    description="传入汉字，返回该字在各名家碑帖中的写法。",
)
def match_calligraphy(
    character: str = Query(..., min_length=1, max_length=2, description="要查询的汉字，如：永"),
    top_k: int = Query(20, ge=1, le=100),
):
    if len(character.encode("utf-8")) != 3:
        raise HTTPException(status_code=400, detail="请输入一个汉字")

    db_path = Path(__file__).resolve().parents[3] / "smart_calligraphy.db"
    if not db_path.exists():
        return APIResponse(data=[])

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT character, image_path FROM calligraphy_db WHERE character = ? LIMIT ?",
        (character, top_k),
    ).fetchall()
    conn.close()

    if not rows:
        return APIResponse(data=[])

    results = [CalligraphyMatch(character=row["character"], image_url=row["image_path"]) for row in rows]
    return APIResponse(data=results)

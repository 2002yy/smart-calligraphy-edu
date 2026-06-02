"""碑帖查询路由

提供按字检索名家碑帖的功能，用于学生端作业评测结果页的"相关碑帖"展示。
"""

import sqlite3
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from app.schemas.common import APIResponse
from pydantic import BaseModel

router = APIRouter()


class CalligraphyMatch(BaseModel):
    character: str
    image_url: str


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

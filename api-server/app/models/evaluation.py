from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, utc_now


class Evaluation(Base):
    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    homework_id: Mapped[int] = mapped_column(ForeignKey("homework.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    total_score: Mapped[float] = mapped_column(default=0)
    structure_score: Mapped[float] = mapped_column(default=0)
    center_score: Mapped[float] = mapped_column(default=0)
    stroke_order_score: Mapped[float] = mapped_column(default=0)  # 笔法规范性评分（字段名保留历史兼容）
    issues_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    advice_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    compare_image_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    thinking_steps: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

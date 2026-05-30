from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, utc_now


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    homework_id: Mapped[int] = mapped_column(ForeignKey("homework.id"), nullable=False)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    final_score: Mapped[float | None] = mapped_column(nullable=True)
    review_status: Mapped[str] = mapped_column(default="reviewed")
    reviewed_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

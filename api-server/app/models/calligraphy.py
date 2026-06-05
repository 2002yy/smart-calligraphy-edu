from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CalligraphyDB(Base):
    __tablename__ = "calligraphy_db"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    character: Mapped[str] = mapped_column(String(10), nullable=False)
    calligrapher: Mapped[str] = mapped_column(String(50), default="", index=True)
    style: Mapped[str] = mapped_column(String(50), default="")
    source: Mapped[str] = mapped_column(String(100), default="")
    period: Mapped[str] = mapped_column(String(20), default="")
    image_path: Mapped[str] = mapped_column(String(255), unique=True)
    description: Mapped[str] = mapped_column(String(500), default="")

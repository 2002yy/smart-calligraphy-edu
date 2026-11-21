from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

DATABASE_URL = settings.database_url or (
    f"mysql+pymysql://{settings.db_user}:{settings.db_password}"
    f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, echo=False, future=True, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Alembic is the sole authority for schema changes in every environment.

    SQLAlchemy create_all does not migrate existing tables or add constraints.
    Falling back after a failed Alembic upgrade would let a development server
    run without the unique evaluation ownership or attempt columns it expects.
    Tests that need ephemeral schemas can still explicitly call create_all.
    """
    try:
        import os
        from alembic.config import Config
        from alembic import command

        alembic_cfg = Config(Path(__file__).resolve().parent.parent.parent / "alembic.ini")
        if os.getenv("DATABASE_URL"):
            alembic_cfg.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])
        command.upgrade(alembic_cfg, "head")
    except Exception as exc:
        raise RuntimeError(
            f"数据库迁移失败（{settings.app_env} 环境不会自动回退建表）：{exc}"
        ) from exc

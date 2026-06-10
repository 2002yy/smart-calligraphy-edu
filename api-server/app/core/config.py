import os
from pathlib import Path

from pydantic import BaseModel

# 自动加载 .env 文件（如果存在）
_env_path = Path(__file__).resolve().parents[2] / ".env"
if _env_path.exists():
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                _k, _v = _k.strip(), _v.strip()
                if not os.getenv(_k):
                    os.environ[_k] = _v


class Settings(BaseModel):
    app_name: str = os.getenv("APP_NAME", "Smart Calligraphy API")
    app_env: str = os.getenv("APP_ENV", "dev")
    app_port: int = int(os.getenv("APP_PORT", "8000"))
    storage_root: str = os.getenv("STORAGE_ROOT", "./storage")
    db_host: str = os.getenv("DB_HOST", "127.0.0.1")
    db_port: int = int(os.getenv("DB_PORT", "3306"))
    db_name: str = os.getenv("DB_NAME", "calligraphy")
    db_user: str = os.getenv("DB_USER", "root")
    db_password: str = os.getenv("DB_PASSWORD", "your_password")
    database_url: str | None = os.getenv("DATABASE_URL", "sqlite:///./smart_calligraphy.db")
    jwt_secret: str = os.getenv("JWT_SECRET", "change_me")
    ai_service_url: str = os.getenv("AI_SERVICE_URL", "http://127.0.0.1:9001")
    evaluation_provider: str = os.getenv("EVALUATION_PROVIDER", "mock")
    openai_evaluation_enabled: bool = os.getenv("OPENAI_EVALUATION_ENABLED", "false").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_base_url: str | None = os.getenv("OPENAI_BASE_URL")
    openai_evaluation_model: str = os.getenv("OPENAI_EVALUATION_MODEL", "gpt-4.1")
    openai_image_detail: str = os.getenv("OPENAI_IMAGE_DETAIL", "low")
    openai_image_max_size: int = int(os.getenv("OPENAI_IMAGE_MAX_SIZE", "768"))
    demo_password: str = os.getenv("DEMO_PASSWORD", "123456")
    secure_static: bool = os.getenv("SECURE_STATIC", "false").lower() in {"1", "true", "yes", "on"}
    cors_origins: list[str] = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174").split(",") if o.strip()]

    # Qwen3.5-omni-plus 视觉评测（通过阿里云百炼 DashScope）
    # 启用方法：复制 .env.example 为 .env，设置 QWEN_API_KEY
    qwen_evaluation_enabled: bool = os.getenv("QWEN_EVALUATION_ENABLED", "false").lower() in {"1", "true", "yes", "on"}
    qwen_api_key: str = os.getenv("QWEN_API_KEY", "")
    qwen_base_url: str = os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    qwen_evaluation_model: str = os.getenv("QWEN_EVALUATION_MODEL", "qwen3.5-omni-plus")
    # ↑ 397B 原生多模态，¥0.8/百万输入，性价比最高。¥5 ≈ 2500次评测
    #   备选: qwen3.6-flash (¥1.2/M 最新轻量), qwen-vl-plus (¥0.8/M 但仅~7B)
    qwen_image_max_size: int = int(os.getenv("QWEN_IMAGE_MAX_SIZE", "768"))
    qwen_image_detail: str = os.getenv("QWEN_IMAGE_DETAIL", "low")

    # 结果图中文覆盖字体路径（优先级最高，会覆盖自动搜索）
    calligraphy_font_path: str = os.getenv("CALLIGRAPHY_FONT_PATH", "")


settings = Settings()

# 生产环境检查：JWT_SECRET 必须修改默认值
if settings.app_env in ("production", "staging") and settings.jwt_secret == "change_me":
    raise RuntimeError(
        "JWT_SECRET 是默认值 'change_me'，不安全。请在 .env 中设置为随机字符串。"
    )

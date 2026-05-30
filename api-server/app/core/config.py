import os

from pydantic import BaseModel


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

    # Qwen3.5-Plus 视觉评测（通过阿里云百炼 DashScope，国内直连，支付宝付款）
    qwen_evaluation_enabled: bool = os.getenv("QWEN_EVALUATION_ENABLED", "false").lower() in {"1", "true", "yes", "on"}
    qwen_api_key: str = os.getenv("QWEN_API_KEY", "")
    qwen_base_url: str = os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    qwen_evaluation_model: str = os.getenv("QWEN_EVALUATION_MODEL", "qwen3.5-plus")
    qwen_image_max_size: int = int(os.getenv("QWEN_IMAGE_MAX_SIZE", "768"))
    qwen_image_detail: str = os.getenv("QWEN_IMAGE_DETAIL", "low")


settings = Settings()

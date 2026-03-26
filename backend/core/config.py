from pydantic_settings import BaseSettings
from functools import lru_cache
import os

# Always point to the .env file sitting next to this config.py
_ENV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Claim360 Email WebApp"
    SECRET_KEY: str = "change-me-in-production-use-strong-secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost/claim360"
    DATABASE_URL_SYNC: str = "postgresql://postgres:password@localhost/claim360"

    # Redis / Celery (Optional - only needed if using background tasks on non-Vercel deployments)
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/oauth/callback"
    GOOGLE_SCOPES: list = [
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.readonly",
        "openid",
        "email",
        "profile",
    ]

    # File storage
    UPLOAD_DIR: str = "uploads"
    MAX_ATTACHMENT_SIZE_MB: int = 25

    # Email sending
    SEND_DELAY_SECONDS: int = 3

    # Tracking
    BASE_URL: str = "http://localhost:8000"

    # Frontend URL (for OAuth redirect)
    FRONTEND_URL: str = "http://localhost:3000"

    # Admin
    ADMIN_EMAIL: str = "admin@company.com"
    ADMIN_PASSWORD: str = "admin123"

    model_config = {
        "env_file": _ENV_FILE,
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    try:
        s = Settings()
        # mask sensitve parts of DB URL for safety in logs
        db_url = s.DATABASE_URL
        if "@" in db_url:
            masked_url = db_url.split("@")[0].split(":")[0] + ":***@" + db_url.split("@")[1]
            print(f"ℹ️ Config loaded. DB Host: {db_url.split('@')[1].split('/')[0]}")
        return s
    except Exception as e:
        print(f"❌ Settings loading FAILED: {str(e)}")
        # Return default settings so the app doesn't crash at module level
        return Settings(_env_file=None)
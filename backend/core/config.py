from pydantic_settings import BaseSettings
from functools import lru_cache
import os

# Point to .env file if it exists (local dev), otherwise use env vars (Vercel)
_ENV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
_ENV_FILE_EXISTS = os.path.exists(_ENV_FILE)


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Claim360 Email WebApp"
    SECRET_KEY: str = "change-me-in-production-use-strong-secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    # Database (CRITICAL - no defaults for production)
    DATABASE_URL: str = ""
    DATABASE_URL_SYNC: str = ""

    # Redis / Celery (Optional - only needed if using background tasks on non-Vercel deployments)
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Google OAuth (CRITICAL - empty means OAuth won't work)
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

    # Tracking (CRITICAL - must be your actual app URL)
    BASE_URL: str = ""

    # Frontend URL (for OAuth redirect) (CRITICAL - must be your actual app URL)
    FRONTEND_URL: str = ""

    # Admin (CRITICAL - must be set in env vars)
    ADMIN_EMAIL: str = ""
    ADMIN_PASSWORD: str = ""

    # Development mode (set DEV_MODE=true in .env)
    DEV_MODE: bool = False

    model_config = {
        "env_file": _ENV_FILE if _ENV_FILE_EXISTS else None,
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    try:
        s = Settings()
        
        # Check for critical missing variables on startup
        critical_vars = {
            "DATABASE_URL": s.DATABASE_URL,
            "DATABASE_URL_SYNC": s.DATABASE_URL_SYNC,
            "SECRET_KEY": s.SECRET_KEY,
            "BASE_URL": s.BASE_URL,
            "FRONTEND_URL": s.FRONTEND_URL,
            "ADMIN_EMAIL": s.ADMIN_EMAIL,
            "ADMIN_PASSWORD": s.ADMIN_PASSWORD,
        }
        
        missing = [k for k, v in critical_vars.items() if not v or v == "change-me-in-production-use-strong-secret"]
        
        if missing:
            warning_msg = f"⚠️ CRITICAL: Missing or default environment variables: {', '.join(missing)}"
            print(warning_msg)
            import logging
            logging.getLogger("config").warning(warning_msg)
        
        # Log successful config load
        if "@" in s.DATABASE_URL:
            db_host = s.DATABASE_URL.split('@')[1].split('/')[0] if s.DATABASE_URL else "NOT SET"
            print(f"✓ Config loaded. Database: {db_host}")
        
        return s
    except Exception as e:
        print(f"❌ Settings loading FAILED: {str(e)}")
        import logging
        logging.getLogger("config").error(f"Settings loading error: {str(e)}")
        # Return default settings so the app doesn't crash at module level
        # This allows better error messages during startup/health checks
        return Settings(_env_file=None)
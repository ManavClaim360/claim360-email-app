from pydantic_settings import BaseSettings
from functools import lru_cache
import os

# Point to .env file if it exists (local dev), otherwise use env vars (Vercel)
_ENV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
_ENV_FILE_EXISTS = os.path.exists(_ENV_FILE)


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Claim360 Email WebApp"
    APP_VERSION: str = "1.0.0"
    SECRET_KEY: str = "change-me-in-production-use-strong-secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    # Database (CRITICAL - no defaults for production)
    DATABASE_URL: str = ""
    DATABASE_URL_SYNC: str = ""

    # Redis / Celery (Optional - only needed if using background tasks on larger deployments)
    REDIS_URL: str = ""
    CELERY_BROKER_URL: str = ""
    CELERY_RESULT_BACKEND: str = ""

    # Google OAuth (CRITICAL - empty means OAuth won't work)
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = ""
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

    model_config = {
        "env_file": _ENV_FILE if _ENV_FILE_EXISTS else None,
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
    }


_MIN_SECRET_KEY_LENGTH = 32


@lru_cache()
def get_settings() -> Settings:
    try:
        s = Settings()

        # Self-healing: guess REDIRECT_URI if BASE_URL is set
        if s.BASE_URL and not s.GOOGLE_REDIRECT_URI:
            s.GOOGLE_REDIRECT_URI = f"{s.BASE_URL.rstrip('/')}/api/auth/oauth/callback"
            print(f"ℹ️ Auto-set GOOGLE_REDIRECT_URI to: {s.GOOGLE_REDIRECT_URI}")

        # ── Validate SECRET_KEY ───────────────────────────────────────
        if (
            not s.SECRET_KEY
            or s.SECRET_KEY == "change-me-in-production-use-strong-secret"
            or len(s.SECRET_KEY) < _MIN_SECRET_KEY_LENGTH
        ):
            if os.environ.get("RENDER") or os.environ.get("RAILWAY") or os.environ.get("FLY_APP_NAME"):
                raise RuntimeError(
                    f"SECRET_KEY is insecure (default or < {_MIN_SECRET_KEY_LENGTH} chars). "
                    "Set a strong random SECRET_KEY in production env vars."
                )
            else:
                print(
                    f"⚠️ WARNING: SECRET_KEY is insecure — using default for local dev only. "
                    f"Set a strong random key (>= {_MIN_SECRET_KEY_LENGTH} chars) before deploying."
                )

        # Check for critical missing variables on startup
        critical_vars = {
            "DATABASE_URL": s.DATABASE_URL,
            "BASE_URL": s.BASE_URL,
            "FRONTEND_URL": s.FRONTEND_URL,
        }

        missing = [k for k, v in critical_vars.items() if not v]

        if missing:
            warning_msg = f"⚠️ CRITICAL: Missing environment variables: {', '.join(missing)}"
            print(warning_msg)

        # Validate Google OAuth vars (warn, don't crash — OAuth may be optional)
        oauth_vars = {"GOOGLE_CLIENT_ID": s.GOOGLE_CLIENT_ID, "GOOGLE_CLIENT_SECRET": s.GOOGLE_CLIENT_SECRET}
        oauth_missing = [k for k, v in oauth_vars.items() if not v]
        if oauth_missing:
            print(f"⚠️ Google OAuth will not work — missing: {', '.join(oauth_missing)}")

        # Log successful config load (without secrets)
        env_name = "RENDER" if os.environ.get("RENDER") else "LOCAL"
        db_host = "NOT SET"
        if s.DATABASE_URL and "@" in s.DATABASE_URL:
            try:
                db_host = s.DATABASE_URL.split('@')[1].split('/')[0]
            except IndexError:
                db_host = "(parse error)"
        print(f"✓ Config loaded. Version={s.APP_VERSION} Env={env_name} DB={db_host}")

        return s
    except RuntimeError:
        raise  # Let startup-fatal errors propagate
    except Exception as e:
        print(f"❌ Settings loading FAILED: {str(e)}")
        return Settings(_env_file=None)
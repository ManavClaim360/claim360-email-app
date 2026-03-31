import logging
import sys
import os

# Add backend directory to Python path so imports work on Vercel
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("main")

from api.auth import router as auth_router
from api.campaigns import router as campaigns_router
from api.templates import router as templates_router
from api.signature import router as signature_router
from api.data import router as data_router
from api.tracking import tracking_router, admin_router as tracking_admin_router
from core.database import get_db, init_db, AsyncSessionLocal
from core.config import get_settings
from core.auth import get_password_hash
from models.user import User, AppSettings
from sqlalchemy import select

settings = get_settings()
import traceback
from fastapi import Request
from fastapi.responses import JSONResponse

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Claim360 API")

from core.config import get_settings
settings = get_settings()

# --- CORS CONFIGURATION ---
allow_origins = []
if settings.FRONTEND_URL:
    # Add exactly what the user provided
    allow_origins.append(settings.FRONTEND_URL.rstrip("/"))
    # Add common variations to be helpful
    if settings.FRONTEND_URL.startswith("https://"):
        allow_origins.append(settings.FRONTEND_URL.replace("https://", "http://").rstrip("/"))
else:
    # Transition fallback for initial Render setup
    if os.environ.get("RENDER"):
        logger.warning("⚠️ FRONTEND_URL not set on Render. Allowing all onrender.com subdomains for transition.")
        allow_origins = ["*"] # Be permissive for initial setup if env vars are missing
    else:
        allow_origins = ["http://localhost:5173", "http://localhost:3000"]
        logger.warning("⚠️ Using local dev origins for CORS.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)
# -------------------------

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"GLOBAL ERROR: {str(exc)}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "error": str(exc)},
    )

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up Claim360 API...")
    try:
        await init_db()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Database initialization FAILED: {str(e)}")
        logger.warning("App will continue - DB may initialize on next request.")
    
    # Seed Admin user if variables are provided
    if settings.ADMIN_EMAIL and settings.ADMIN_PASSWORD:
        try:
            from models.user import User
            from core.auth import get_password_hash
            from core.database import AsyncSessionLocal
            
            admin_email_lower = settings.ADMIN_EMAIL.lower().strip()
            async with AsyncSessionLocal() as session:
                result = await session.execute(select(User).where(User.email == admin_email_lower))
                existing_admin = result.scalar_one_or_none()
                
                if not existing_admin:
                    logger.info(f"🆕 Creating initial admin user: {admin_email_lower}")
                    new_admin = User(
                        email=admin_email_lower,
                        full_name="System Administrator",
                        hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
                        is_admin=True,
                        is_active=True
                    )
                    session.add(new_admin)
                    await session.commit()
                    logger.info("✓ Admin user created successfully.")
                else:
                    logger.info(f"✓ Admin user exists: {admin_email_lower}")
        except Exception as e:
            logger.error(f"Failed to seed admin user: {str(e)}")

    # Seed default AppSettings row (registration toggle) if absent
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(AppSettings))
            if not result.scalars().first():
                session.add(AppSettings(registrations_open=False))
                await session.commit()
                logger.info("✓ AppSettings row created (registrations_open=False by default)")
            else:
                logger.info("✓ AppSettings row exists.")
    except Exception as e:
        logger.error(f"⚠️ AppSettings seeding FAILED: {str(e)}")
        logger.error(traceback.format_exc())
        # We don't crash startup - the app should still run even if settings are missing


    logger.info("=" * 60)
    logger.info(f"✓ Startup complete - API ready to serve requests")
    logger.info(f"Allowed Origins: {allow_origins}")
    if settings.BASE_URL:
        logger.info(f"Base URL (Backend): {settings.BASE_URL}")
    if settings.FRONTEND_URL:
        logger.info(f"Frontend URL: {settings.FRONTEND_URL}")
    logger.info("=" * 60)

app.include_router(auth_router)
app.include_router(campaigns_router)
app.include_router(templates_router)
app.include_router(signature_router)
app.include_router(data_router)
app.include_router(tracking_router)
app.include_router(tracking_admin_router)

# Health and root API endpoints
@app.get("/api/health")
async def health(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "message": "API and Database are connected"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {"status": "error", "message": f"Database connection failed: {str(e)}"}

@app.get("/")
async def root():
    return {"message": "Claim360 API is running"}

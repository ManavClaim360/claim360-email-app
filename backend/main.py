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
from core.database import get_db, init_db
import traceback
from fastapi import Request
from fastapi.responses import JSONResponse

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Claim360 API")

from core.config import get_settings
settings = get_settings()

allow_origins = ["http://localhost:5173", "http://localhost:3000"]
if settings.FRONTEND_URL:
    allow_origins.append(settings.FRONTEND_URL.rstrip("/"))
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    print("⚠️ FRONTEND_URL is not set! Falling back to allow ALL origins for CORS. Please secure this in production by setting FRONTEND_URL.")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

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
    from core.config import get_settings
    logger.info("=" * 60)
    logger.info("🚀 Starting up Claim360 API...")
    logger.info("=" * 60)
    
    # Load and verify configuration
    try:
        settings = get_settings()
        logger.info("✓ Configuration loaded successfully")
        
        # Detect environment
        import os
        is_vercel = "VERCEL" in os.environ or "VERCEL_URL" in os.environ
        env_name = "VERCEL" if is_vercel else "LOCAL"
        logger.info(f"Environment: {env_name}")
    except Exception as e:
        logger.error(f"Configuration loading failed: {str(e)}")
    
    # Initialize database
    try:
        result = await init_db()
        if result:
            logger.info("✓ Database initialized successfully.")
        else:
            logger.warning("Database initialization skipped - may be already initialized.")
    except Exception as e:
        logger.error(f"Database initialization FAILED: {str(e)}")
        logger.warning("App will continue - DB may initialize on next request.")
    
    logger.info("=" * 60)
    logger.info("✓ Startup complete - API ready to serve requests")
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

import logging
import sys
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
from api.tracking import router as tracking_router
from core.database import get_db

app = FastAPI(title="Claim360 API")

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up Claim360 API...")

app.include_router(auth_router)
app.include_router(campaigns_router)
app.include_router(templates_router)
app.include_router(signature_router)
app.include_router(data_router)
app.include_router(tracking_router)

@app.get("/api/health")
async def health(db: AsyncSession = Depends(get_db)):
    try:
        # Check database connection
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "message": "API and Database are connected"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {"status": "error", "message": f"Database connection failed: {str(e)}"}

@app.get("/")
async def root():
    return {"message": "API is running"}

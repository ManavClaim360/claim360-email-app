import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession

# from core.database import init_db, get_db
# from core.config import get_settings
# from core.auth import get_password_hash
# from api.auth import router as auth_router
# from api.templates import router as templates_router
# from api.campaigns import router as campaigns_router
# from api.data import router as data_router
# from api.tracking import tracking_router, admin_router
# from api.signature import router as signature_router

# settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database
    print("🚀 Starting Claim360 API...")
    try:
        # await init_db()
        # await seed_admin()
        print("ℹ️ Database auto-init disabled for debugging.")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Database initialization FAILED: {str(e)}")
    
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    yield


async def seed_admin():
    """Create default admin user if not exists."""
    from core.database import AsyncSessionLocal
    from models.user import User
    from sqlalchemy import select
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == settings.ADMIN_EMAIL))
        if not result.scalar_one_or_none():
            admin = User(
                email=settings.ADMIN_EMAIL,
                full_name="System Admin",
                hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
                is_admin=True,
                is_active=True,
            )
            db.add(admin)
            await db.commit()
            print(f"✅ Admin created: {settings.ADMIN_EMAIL}")


app = FastAPI(
    title="Claim360 Email WebApp API",
    description="Bulk email system with Gmail OAuth, tracking, and team management",
    version="1.0.0",
    # lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
# app.include_router(auth_router)
# app.include_router(templates_router)
# app.include_router(campaigns_router)
# app.include_router(data_router)
# app.include_router(tracking_router)
# app.include_router(admin_router)
# app.include_router(signature_router)

# Serve uploaded files (attachments)
# if os.path.exists(settings.UPLOAD_DIR):
#     app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


@app.get("/")
async def root():
    return {"name": "Claim360 Email WebApp API", "version": "1.0.0", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy", "minimal": "true"}


# Serve built React frontend (when running in production / after `npm run build`)
_static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(_static_dir):
    app.mount("/", StaticFiles(directory=_static_dir, html=True), name="frontend")

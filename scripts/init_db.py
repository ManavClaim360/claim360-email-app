"""
Database initialization and migration script.
Run: python scripts/init_db.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from core.database import engine, Base, AsyncSessionLocal
from core.auth import get_password_hash
from core.config import get_settings
import models.user  # ensure all models are registered

settings = get_settings()


async def create_tables():
    print("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tables created.")


async def seed_admin():
    from models.user import User
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == settings.ADMIN_EMAIL))
        existing = result.scalar_one_or_none()
        if existing:
            print(f"ℹ️  Admin already exists: {settings.ADMIN_EMAIL}")
            return

        admin = User(
            email=settings.ADMIN_EMAIL,
            full_name="System Admin",
            hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
            is_admin=True,
            is_active=True,
        )
        db.add(admin)
        await db.commit()
        print(f"✅ Admin created: {settings.ADMIN_EMAIL} / {settings.ADMIN_PASSWORD}")


async def main():
    await create_tables()
    await seed_admin()
    print("\n🚀 Database ready. Start backend with:")
    print("   cd backend && uvicorn main:app --reload --port 8000")


if __name__ == "__main__":
    asyncio.run(main())

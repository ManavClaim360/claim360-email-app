import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.getcwd())

from core.database import init_db, engine, Base
from models.user import User, AppSettings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

async def force_init():
    print("🚀 Connecting to Neon DB...")
    success = await init_db()
    if success:
        print("✅ Tables created or already exist.")
        
        # Verify AppSettings
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            try:
                result = await session.execute(select(AppSettings))
                settings = result.scalars().first()
                if not settings:
                    print("⚙️ Seeding default AppSettings...")
                    session.add(AppSettings(registrations_open=False))
                    await session.commit()
                    print("✅ Seeding complete.")
                else:
                    print(f"✅ AppSettings found: registrations_open={settings.registrations_open}")
            except Exception as e:
                print(f"❌ Error verifying AppSettings: {e}")
    else:
        print("❌ Database initialization FAILED.")

if __name__ == "__main__":
    asyncio.run(force_init())

"""
Run this once to add the social_links column to signatures table
and create the table if it doesn't exist.
Usage: python scripts/migrate_signature.py
"""
import asyncio, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from dotenv import load_dotenv
BACKEND_DIR = os.path.join(os.path.dirname(__file__), '..', 'backend')
load_dotenv(os.path.join(BACKEND_DIR, '.env'), override=True)

from core.database import engine, Base
from models.user import Signature  # noqa — registers model

async def main():
    async with engine.begin() as conn:
        # Create table if not exists (safe to run multiple times)
        await conn.run_sync(Base.metadata.create_all)
        # Add social_links column if missing (for existing installs)
        try:
            await conn.exec_driver_sql(
                "ALTER TABLE signatures ADD COLUMN IF NOT EXISTS social_links JSON"
            )
            print("✅ social_links column added (or already existed)")
        except Exception as e:
            print(f"Note: {e}")
    print("✅ Migration complete")

asyncio.run(main())

"""
Run once to create/update the signatures table.
Uses psycopg2 (sync) to avoid asyncio cleanup issues on Python 3.14.

Usage:
  cd claim360\backend
  venv\Scripts\activate
  cd ..
  python scripts/create_signatures_table.py
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'), override=True)

import psycopg2

# Build sync DSN from the async DATABASE_URL
DATABASE_URL = os.environ.get('DATABASE_URL', '')
# Convert postgresql+asyncpg://... → postgresql://...
SYNC_DSN = DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')

def run():
    conn = psycopg2.connect(SYNC_DSN)
    conn.autocommit = True
    cur = conn.cursor()

    # 1. Create table if not exists
    cur.execute("""
        CREATE TABLE IF NOT EXISTS signatures (
            id              SERIAL PRIMARY KEY,
            user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name            VARCHAR(255) NOT NULL DEFAULT 'My Signature',
            is_default      BOOLEAN DEFAULT TRUE,
            is_shared       BOOLEAN DEFAULT FALSE,
            full_name       VARCHAR(255),
            title           VARCHAR(255),
            company         VARCHAR(255) DEFAULT 'CLAIM 360',
            phone           VARCHAR(100),
            website         VARCHAR(255),
            email_addr      VARCHAR(255),
            address_mumbai  TEXT,
            address_delhi   TEXT,
            address_london  TEXT,
            cin             VARCHAR(100),
            copyright_text  VARCHAR(500),
            logo_url        TEXT,
            social_links    JSON,
            brand_color     VARCHAR(20) DEFAULT '#1C305E',
            created_at      TIMESTAMPTZ DEFAULT NOW(),
            updated_at      TIMESTAMPTZ
        )
    """)
    print("OK  signatures table created (or already existed)")

    # 2. Widen logo_url to TEXT (safe if already TEXT)
    try:
        cur.execute("ALTER TABLE signatures ALTER COLUMN logo_url TYPE TEXT")
        print("OK  logo_url column widened to TEXT")
    except Exception as e:
        print(f"--  logo_url already TEXT or skipped: {e}")

    # 3. Add social_links column if missing
    try:
        cur.execute("ALTER TABLE signatures ADD COLUMN IF NOT EXISTS social_links JSON")
        print("OK  social_links column present")
    except Exception as e:
        print(f"--  social_links: {e}")

    # 4. Add brand_color column if missing
    try:
        cur.execute("ALTER TABLE signatures ADD COLUMN IF NOT EXISTS brand_color VARCHAR(20) DEFAULT '#1C305E'")
        print("OK  brand_color column present")
    except Exception as e:
        print(f"--  brand_color: {e}")

    cur.close()
    conn.close()
    print("\nDone. Restart your backend now.")

run()
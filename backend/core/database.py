from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
from core.config import get_settings

settings = get_settings()

# Sanitize DATABASE_URL: asyncpg can be picky about sslmode in the string
db_url = settings.DATABASE_URL
if "sslmode=" in db_url:
    # Remove sslmode from string and we will handle it in connect_args
    import re
    db_url = re.sub(r"[?&]sslmode=[^&]+", "", db_url)

engine = create_async_engine(
    db_url,
    echo=False,
    poolclass=NullPool,
    connect_args={"ssl": "require"} if "neon.tech" in db_url else {}
)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    # ── IMPORTANT: import ALL models here so SQLAlchemy registers them
    # in Base.metadata BEFORE create_all runs. Missing an import = missing table.
    import models.user  # noqa — registers User, OAuthToken, Template, Campaign,
                        # EmailLog, TrackingData, Contact, Attachment,
                        # TemplateAttachment, CustomVariable, Signature
    
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        return True
    except Exception as e:
        # On Vercel, database initialization might fail on cold start
        # Don't raise, just log - the app should still start
        import logging
        logging.warning(f"Database initialization issue (may be normal on cold start): {str(e)}")
        return False

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
from core.config import get_settings
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

settings = get_settings()

# Sanitize DATABASE_URL: parse and reconstruct properly
db_url = settings.DATABASE_URL
if "sslmode=" in db_url or "channel_binding=" in db_url:
    try:
        parsed = urlparse(db_url)
        params = parse_qs(parsed.query, keep_blank_values=True)
        
        # Remove sslmode and channel_binding - we'll handle them in connect_args
        params.pop('sslmode', None)
        params.pop('channel_binding', None)
        
        # Reconstruct query string
        new_query = '&'.join(f"{k}={v[0]}" for k, v in params.items()) if params else ""
        new_parsed = parsed._replace(query=new_query)
        db_url = urlunparse(new_parsed)
    except Exception as e:
        print(f"Warning: Failed to sanitize DB URL: {e}")
        # Continue with original URL if parsing fails

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

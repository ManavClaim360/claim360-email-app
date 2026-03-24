from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
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
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

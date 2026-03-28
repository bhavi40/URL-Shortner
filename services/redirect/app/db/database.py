from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker
)
from sqlalchemy.orm import declarative_base
from app.core.config import settings
from app.core.logging import logger

# Read only connection — redirect only reads URLs
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=20,           # higher pool — redirect is high traffic
    max_overflow=40,        # more overflow connections
    pool_pre_ping=True,     # verify connection before use
    pool_recycle=3600,      # recycle every hour
    execution_options={
        "isolation_level": "AUTOCOMMIT"  # read only — no transactions needed
    }
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker
)
from sqlalchemy.orm import declarative_base
from app.core.config import settings
from app.core.logging import logger

# Connection pool settings — critical for production
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,       # only log SQL in debug mode
    pool_size=10,              # max persistent connections
    max_overflow=20,           # extra connections under heavy load
    pool_pre_ping=True,        # check connection is alive before using
    pool_recycle=3600,         # recycle connections every 1 hour
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,    # don't expire objects after commit
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()
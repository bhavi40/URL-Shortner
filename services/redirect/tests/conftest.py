import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.main import app
from app.db.database import Base, get_db

TEST_DATABASE_URL = "postgresql+asyncpg://shortener_user:shortener_pass@127.0.0.1:5432/urlshortener_test"

def make_engine():
    return create_async_engine(TEST_DATABASE_URL, echo=False, pool_pre_ping=True)

def make_session_factory(engine):
    return async_sessionmaker(engine, expire_on_commit=False)

@pytest_asyncio.fixture
async def client():
    engine = make_engine()
    session_factory = make_session_factory(engine)

    async def override():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    with patch("app.services.cache_service.cache_service.get_url", new_callable=AsyncMock, return_value=None), \
         patch("app.services.cache_service.cache_service.set_url", new_callable=AsyncMock), \
         patch("app.services.cache_service.cache_service.get_cache_stats", new_callable=AsyncMock, return_value={}), \
         patch("app.services.cache_service.cache_service.redis") as mock_redis, \
         patch("app.services.kafka_service.kafka_service.start", new_callable=AsyncMock), \
         patch("app.services.kafka_service.kafka_service.stop", new_callable=AsyncMock), \
         patch("app.services.kafka_service.kafka_service.publish_click_event", new_callable=AsyncMock):

        mock_redis.ping = AsyncMock(return_value=True)
        mock_redis.aclose = AsyncMock(return_value=None)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            follow_redirects=False
        ) as ac:
            yield ac, session_factory

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture
async def client_with_cache():
    engine = make_engine()
    session_factory = make_session_factory(engine)

    async def override():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    with patch("app.services.cache_service.cache_service.get_url", new_callable=AsyncMock, return_value="https://www.google.com"), \
         patch("app.services.cache_service.cache_service.set_url", new_callable=AsyncMock), \
         patch("app.services.cache_service.cache_service.get_cache_stats", new_callable=AsyncMock, return_value={}), \
         patch("app.services.cache_service.cache_service.redis") as mock_redis, \
         patch("app.services.kafka_service.kafka_service.start", new_callable=AsyncMock), \
         patch("app.services.kafka_service.kafka_service.stop", new_callable=AsyncMock), \
         patch("app.services.kafka_service.kafka_service.publish_click_event", new_callable=AsyncMock):

        mock_redis.ping = AsyncMock(return_value=True)
        mock_redis.aclose = AsyncMock(return_value=None)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            follow_redirects=False
        ) as ac:
            yield ac, session_factory

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
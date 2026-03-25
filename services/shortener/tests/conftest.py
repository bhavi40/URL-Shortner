import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.main import app
from app.db.database import Base, get_db

TEST_DATABASE_URL = "postgresql+asyncpg://shortener_user:shortener_pass@127.0.0.1:5432/urlshortener_test"

async def override_get_db():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    session_local = async_sessionmaker(engine, expire_on_commit=False)
    async with session_local() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await engine.dispose()

app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Create fresh tables before each test, drop after."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

@pytest.fixture
def paid_user_headers():
    return {
        "x-user-id": "550e8400-e29b-41d4-a716-446655440000",
        "x-user-plan": "paid"
    }

@pytest.fixture
def free_user_headers():
    return {
        "x-user-id": "660e8400-e29b-41d4-a716-446655440000",
        "x-user-plan": "free"
    }

@pytest.fixture
def premium_user_headers():
    return {
        "x-user-id": "770e8400-e29b-41d4-a716-446655440000",
        "x-user-plan": "premium"
    }
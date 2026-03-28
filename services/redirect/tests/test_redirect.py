import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy import insert
from app.models.url import URL

@pytest.mark.asyncio
async def test_health_check(client):
    ac, _ = client
    response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

@pytest.mark.asyncio
async def test_redirect_success(client):
    ac, sf = client
    async with sf() as session:
        await session.execute(insert(URL).values(
            id=uuid.uuid4(),
            short_code="abc123",
            original_url="https://www.google.com",
            user_id=uuid.uuid4(),
            is_active=True,
            deleted_at=None
        ))
        await session.commit()
    response = await ac.get("/r/abc123")
    assert response.status_code == 302
    assert response.headers["location"] == "https://www.google.com"

@pytest.mark.asyncio
async def test_redirect_not_found(client):
    ac, _ = client
    response = await ac.get("/r/doesnotexist")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_redirect_deleted_link(client):
    ac, sf = client
    async with sf() as session:
        await session.execute(insert(URL).values(
            id=uuid.uuid4(),
            short_code="deleted1",
            original_url="https://www.google.com",
            user_id=uuid.uuid4(),
            is_active=False,
            deleted_at=datetime.now(timezone.utc)
        ))
        await session.commit()
    response = await ac.get("/r/deleted1")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_redirect_inactive_link(client):
    ac, sf = client
    async with sf() as session:
        await session.execute(insert(URL).values(
            id=uuid.uuid4(),
            short_code="inactive1",
            original_url="https://www.google.com",
            user_id=uuid.uuid4(),
            is_active=False,
            deleted_at=None
        ))
        await session.commit()
    response = await ac.get("/r/inactive1")
    assert response.status_code == 410

@pytest.mark.asyncio
async def test_redirect_follows_to_original(client):
    ac, sf = client
    async with sf() as session:
        await session.execute(insert(URL).values(
            id=uuid.uuid4(),
            short_code="follow1",
            original_url="https://www.example.com",
            user_id=uuid.uuid4(),
            is_active=True,
            deleted_at=None
        ))
        await session.commit()

    # ✅ Just verify the redirect happens correctly
    # Don't follow to external site
    response = await ac.get("/r/follow1", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "https://www.example.com"
import pytest
import uuid
from sqlalchemy import insert
from app.models.url import URL

@pytest.mark.asyncio
async def test_cache_hit_redirects(client_with_cache):
    ac, _ = client_with_cache
    response = await ac.get("/r/anything")
    assert response.status_code == 302
    assert response.headers["location"] == "https://www.google.com"

@pytest.mark.asyncio
async def test_cache_miss_queries_db(client):
    ac, sf = client
    async with sf() as session:
        await session.execute(insert(URL).values(
            id=uuid.uuid4(),
            short_code="dbhit1",
            original_url="https://www.github.com",
            user_id=uuid.uuid4(),
            is_active=True,
            deleted_at=None
        ))
        await session.commit()
    response = await ac.get("/r/dbhit1")
    assert response.status_code == 302
    assert response.headers["location"] == "https://www.github.com"
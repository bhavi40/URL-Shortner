import pytest
import uuid

@pytest.mark.asyncio
async def test_free_plan_max_5_links(client):
    """Free users can only create 5 links."""
    headers = {
        "x-user-id": str(uuid.uuid4()),  # fresh user each test
        "x-user-plan": "free"
    }
    # Create 5 links — all should succeed
    for i in range(5):
        response = await client.post("/links",
            json={"original_url": f"https://example{i}.com"},
            headers=headers
        )
        assert response.status_code == 201

    # 6th link should fail
    response = await client.post("/links",
        json={"original_url": "https://example6.com"},
        headers=headers
    )
    assert response.status_code == 403
    assert "Link limit reached" in response.json()["detail"]

@pytest.mark.asyncio
async def test_custom_alias_blocked_on_free_plan(client, free_user_headers):
    response = await client.post("/links",
        json={
            "original_url": "https://google.com",
            "custom_alias": "mybrand"
        },
        headers=free_user_headers
    )
    assert response.status_code == 403
    assert "Custom aliases require" in response.json()["detail"]

@pytest.mark.asyncio
async def test_custom_alias_allowed_on_paid_plan(client, paid_user_headers):
    response = await client.post("/links",
        json={
            "original_url": "https://google.com",
            "custom_alias": f"mybrand-{uuid.uuid4().hex[:6]}"
        },
        headers=paid_user_headers
    )
    assert response.status_code == 201

@pytest.mark.asyncio
async def test_duplicate_custom_alias_rejected(client, paid_user_headers):
    alias = f"unique-{uuid.uuid4().hex[:6]}"
    # First use — should work
    await client.post("/links",
        json={"original_url": "https://google.com", "custom_alias": alias},
        headers=paid_user_headers
    )
    # Second use — should fail
    response = await client.post("/links",
        json={"original_url": "https://github.com", "custom_alias": alias},
        headers=paid_user_headers
    )
    assert response.status_code == 409
    assert "already taken" in response.json()["detail"]

@pytest.mark.asyncio
async def test_paid_plan_unlimited_links(client):
    """Paid users can create more than 5 links."""
    headers = {
        "x-user-id": str(uuid.uuid4()),
        "x-user-plan": "paid"
    }
    for i in range(10):
        response = await client.post("/links",
            json={"original_url": f"https://example{i}.com"},
            headers=headers
        )
        assert response.status_code == 201
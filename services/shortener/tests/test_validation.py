import pytest

@pytest.mark.asyncio
async def test_invalid_url_rejected(client, paid_user_headers):
    response = await client.post("/links",
        json={"original_url": "not-a-valid-url"},
        headers=paid_user_headers
    )
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_missing_url_rejected(client, paid_user_headers):
    response = await client.post("/links",
        json={},
        headers=paid_user_headers
    )
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_alias_too_short_rejected(client, paid_user_headers):
    response = await client.post("/links",
        json={"original_url": "https://google.com", "custom_alias": "ab"},
        headers=paid_user_headers
    )
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_alias_special_chars_rejected(client, paid_user_headers):
    response = await client.post("/links",
        json={"original_url": "https://google.com", "custom_alias": "my@brand!"},
        headers=paid_user_headers
    )
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_missing_user_id_header(client):
    response = await client.post("/links",
        json={"original_url": "https://google.com"}
        # no headers
    )
    assert response.status_code == 422
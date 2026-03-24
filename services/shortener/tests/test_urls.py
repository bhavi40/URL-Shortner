import pytest

@pytest.mark.asyncio
async def test_create_short_url(client, paid_user_headers):
    response = await client.post("/links",
        json={"original_url": "https://google.com"},
        headers=paid_user_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert "short_code" in data
    assert "short_url" in data
    assert data["is_active"] == True
    assert data["original_url"] == "https://google.com/"

@pytest.mark.asyncio
async def test_list_urls(client, paid_user_headers):
    response = await client.get("/links", headers=paid_user_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "links" in data
    assert isinstance(data["links"], list)

@pytest.mark.asyncio
async def test_delete_url(client, paid_user_headers):
    # First create a link
    create = await client.post("/links",
        json={"original_url": "https://github.com"},
        headers=paid_user_headers
    )
    short_code = create.json()["short_code"]

    # Then delete it
    response = await client.delete(
        f"/links/{short_code}",
        headers=paid_user_headers
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Link deleted successfully."

@pytest.mark.asyncio
async def test_delete_nonexistent_url(client, paid_user_headers):
    response = await client.delete(
        "/links/doesnotexist",
        headers=paid_user_headers
    )
    assert response.status_code == 404
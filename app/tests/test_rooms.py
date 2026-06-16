import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_rooms_no_auth(client: AsyncClient):
    response = await client.get("/rooms?date=2026-06-15")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_rooms_empty(client: AsyncClient):
    reg_resp = await client.post(
        "/auth/register", json={"username": "user", "password": "Strong!Pass1"}
    )
    token = reg_resp.json()["access_token"]

    response = await client.get(
        "/rooms?date=2026-06-15",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_rooms_missing_date(client: AsyncClient):
    reg_resp = await client.post(
        "/auth/register", json={"username": "user", "password": "Strong!Pass1"}
    )
    token = reg_resp.json()["access_token"]

    response = await client.get(
        "/rooms",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422

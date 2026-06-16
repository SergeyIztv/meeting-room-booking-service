import datetime
import json
import base64

import pytest
from httpx import AsyncClient
from sqlalchemy import insert

from app.models.enums import UserRole
from app.models.room import Room
from app.models.slot import TimeSlot


def _decode_jwt(token: str) -> dict:
    payload_b64 = token.split(".")[1]
    payload_b64 += "=" * (4 - len(payload_b64) % 4)
    return json.loads(base64.urlsafe_b64decode(payload_b64))


@pytest.fixture
async def seed_data(db_session):
    await db_session.execute(insert(Room).values(id=1, name="Room A", description="First room"))
    await db_session.execute(
        insert(TimeSlot).values(id=1, room_id=1, start_time=datetime.time(9, 0), end_time=datetime.time(11, 0))
    )
    await db_session.execute(
        insert(TimeSlot).values(id=2, room_id=1, start_time=datetime.time(13, 0), end_time=datetime.time(16, 0))
    )
    await db_session.flush()


@pytest.mark.asyncio
async def test_create_booking(client: AsyncClient, seed_data):
    reg_resp = await client.post(
        "/auth/register", json={"username": "user", "password": "Strong!Pass1"}
    )
    token = reg_resp.json()["access_token"]

    response = await client.post(
        "/bookings",
        json={"room_id": 1, "slot_id": 1, "date": "2026-12-25"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["room_id"] == 1
    assert data["slot_id"] == 1
    assert data["date"] == "2026-12-25"


@pytest.mark.asyncio
async def test_create_booking_duplicate(client: AsyncClient, seed_data):
    reg_resp = await client.post(
        "/auth/register", json={"username": "user", "password": "Strong!Pass1"}
    )
    token = reg_resp.json()["access_token"]

    await client.post(
        "/bookings",
        json={"room_id": 1, "slot_id": 1, "date": "2026-12-25"},
        headers={"Authorization": f"Bearer {token}"},
    )
    response = await client.post(
        "/bookings",
        json={"room_id": 1, "slot_id": 1, "date": "2026-12-25"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 409
    assert response.json()["code"] == "SLOT_ALREADY_BOOKED"


@pytest.mark.asyncio
async def test_create_booking_room_not_found(client: AsyncClient):
    reg_resp = await client.post(
        "/auth/register", json={"username": "user", "password": "Strong!Pass1"}
    )
    token = reg_resp.json()["access_token"]

    response = await client.post(
        "/bookings",
        json={"room_id": 999, "slot_id": 1, "date": "2026-12-25"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cancel_own_booking(client: AsyncClient, seed_data):
    reg_resp = await client.post(
        "/auth/register", json={"username": "user", "password": "Strong!Pass1"}
    )
    token = reg_resp.json()["access_token"]

    book_resp = await client.post(
        "/bookings",
        json={"room_id": 1, "slot_id": 1, "date": "2026-12-25"},
        headers={"Authorization": f"Bearer {token}"},
    )
    booking_id = book_resp.json()["id"]

    response = await client.delete(
        f"/bookings/{booking_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_cancel_other_booking_forbidden(client: AsyncClient, seed_data):
    reg_resp = await client.post(
        "/auth/register", json={"username": "alice", "password": "Strong!Pass1"}
    )
    alice_token = reg_resp.json()["access_token"]

    reg_resp = await client.post(
        "/auth/register", json={"username": "bob", "password": "Strong!Pass1"}
    )
    bob_token = reg_resp.json()["access_token"]

    book_resp = await client.post(
        "/bookings",
        json={"room_id": 1, "slot_id": 1, "date": "2026-12-25"},
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    booking_id = book_resp.json()["id"]

    response = await client.delete(
        f"/bookings/{booking_id}",
        headers={"Authorization": f"Bearer {bob_token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_cancel_any_booking_as_admin(client: AsyncClient, seed_data, db_session):
    reg_resp = await client.post(
        "/auth/register", json={"username": "alice", "password": "Strong!Pass1"}
    )
    alice_token = reg_resp.json()["access_token"]

    # make alice admin directly in DB
    from sqlalchemy import select
    from app.models.user import User
    alice_id = int(_decode_jwt(alice_token)["sub"])
    result = await db_session.execute(select(User).where(User.id == alice_id))
    result.scalar_one().role = UserRole.ADMIN
    await db_session.flush()

    reg_resp = await client.post(
        "/auth/register", json={"username": "admin_user", "password": "Strong!Pass1"}
    )
    admin_token = reg_resp.json()["access_token"]

    book_resp = await client.post(
        "/bookings",
        json={"room_id": 1, "slot_id": 1, "date": "2026-12-25"},
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    booking_id = book_resp.json()["id"]

    # alice (now admin) promotes admin_user
    admin_user_id = int(_decode_jwt(admin_token)["sub"])
    await client.post(
        "/admins",
        json={"user_id": admin_user_id},
        headers={"Authorization": f"Bearer {alice_token}"},
    )

    response = await client.delete(
        f"/bookings/{booking_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 204

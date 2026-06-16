import datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import insert

from app.models.room import Room
from app.models.slot import TimeSlot


@pytest.fixture
async def seed_data(db_session):
    await db_session.execute(insert(Room).values(id=1, name="Room A", description="First room"))
    await db_session.execute(
        insert(TimeSlot).values(id=1, room_id=1, start_time=datetime.time(9, 0), end_time=datetime.time(11, 0))
    )
    await db_session.execute(
        insert(TimeSlot).values(id=2, room_id=1, start_time=datetime.time(13, 0), end_time=datetime.time(16, 0))
    )
    await db_session.execute(insert(Room).values(id=2, name="Room B", description="Second room"))
    await db_session.execute(
        insert(TimeSlot).values(id=3, room_id=2, start_time=datetime.time(10, 0), end_time=datetime.time(12, 0))
    )
    await db_session.flush()


@pytest.mark.asyncio
async def test_full_booking_flow(client: AsyncClient, seed_data):
    reg_resp = await client.post(
        "/auth/register", json={"username": "alice", "password": "Strong!Pass1"}
    )
    assert reg_resp.status_code == 201
    token = reg_resp.json()["access_token"]

    rooms_resp = await client.get(
        "/rooms?date=2026-12-25",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert rooms_resp.status_code == 200
    rooms = rooms_resp.json()
    assert len(rooms) == 2

    assert rooms[0]["slots"][0]["is_available"] is True

    book_resp = await client.post(
        "/bookings",
        json={"room_id": 1, "slot_id": 1, "date": "2026-12-25"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert book_resp.status_code == 201

    rooms_resp = await client.get(
        "/rooms?date=2026-12-25",
        headers={"Authorization": f"Bearer {token}"},
    )
    rooms = rooms_resp.json()
    room1_slot1 = next(s for s in rooms[0]["slots"] if s["id"] == 1)
    assert room1_slot1["is_available"] is False
    assert room1_slot1["booked_by"] == "alice"

    booking_id = book_resp.json()["id"]
    del_resp = await client.delete(
        f"/bookings/{booking_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert del_resp.status_code == 204

    rooms_resp = await client.get(
        "/rooms?date=2026-12-25",
        headers={"Authorization": f"Bearer {token}"},
    )
    rooms = rooms_resp.json()
    assert rooms[0]["slots"][0]["is_available"] is True

from collections import defaultdict
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.room import Room
from app.models.slot import TimeSlot
from app.models.user import User
from app.schemas.room import RoomDetailResponse
from app.schemas.slot import SlotResponse


class RoomService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_rooms(self, date_str: str) -> list[RoomDetailResponse]:
        booking_date = date.fromisoformat(date_str)

        result = await self.db.execute(select(Room))
        rooms = result.scalars().all()

        result = await self.db.execute(
            select(Booking).where(Booking.date == booking_date)
        )
        bookings = result.scalars().all()

        booked_map: dict[tuple[int, int], int] = {}
        user_ids = set()
        for b in bookings:
            booked_map[(b.room_id, b.slot_id)] = b.user_id
            user_ids.add(b.user_id)

        usernames: dict[int, str] = {}
        if user_ids:
            result = await self.db.execute(
                select(User).where(User.id.in_(user_ids))
            )
            users = result.scalars().all()
            usernames = {u.id: u.username for u in users}

        response = []
        for room in rooms:
            result = await self.db.execute(
                select(TimeSlot).where(TimeSlot.room_id == room.id)
            )
            slots = result.scalars().all()

            slot_list = []
            for slot in slots:
                user_id = booked_map.get((room.id, slot.id))
                slot_list.append(
                    SlotResponse(
                        id=slot.id,
                        start_time=slot.start_time,
                        end_time=slot.end_time,
                        is_available=user_id is None,
                        booked_by=usernames.get(user_id) if user_id else None,
                    )
                )

            response.append(
                RoomDetailResponse(
                    id=room.id,
                    name=room.name,
                    description=room.description,
                    slots=slot_list,
                )
            )

        return response

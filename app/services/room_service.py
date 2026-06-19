import logging
from collections import defaultdict
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from app.models.booking import Booking
from app.models.room import Room
from app.schemas.room import RoomDetailResponse
from app.schemas.slot import SlotResponse

logger = logging.getLogger("app")


class RoomService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_rooms(self, booking_date: date) -> list[RoomDetailResponse]:

        result = await self.db.execute(
            select(Room)
            .options(selectinload(Room.slots))
        )
        rooms = result.scalars().all()

        result = await self.db.execute(
            select(Booking)
            .where(Booking.date == booking_date)
            .options(joinedload(Booking.user))
        )
        bookings = result.scalars().all()

        booked_map: dict[tuple[int, int], str] = {
            (b.room_id, b.slot_id): b.user.username
            for b in bookings if b.user
        }

        response = []
        for room in rooms:
            slot_list = []
            for slot in room.slots:
                booked_by_username = booked_map.get((room.id, slot.id))

                slot_list.append(
                    SlotResponse(
                        id=slot.id,
                        start_time=slot.start_time,
                        end_time=slot.end_time,
                        is_available=booked_by_username is None,
                        booked_by=booked_by_username,
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

        logger.debug(
            "Rooms fetched",
            extra={"date": booking_date, "rooms_count": len(response)},
        )

        return response

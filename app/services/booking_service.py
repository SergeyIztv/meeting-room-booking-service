import logging
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import (
    BookingAlreadyExistsError,
    BookingNotFoundError,
    CancelForbiddenError,
    PastDateBookingError,
    PastBookingCancellationError,
    RoomMismatchError,
    SlotNotFoundError,
)
from app.models.booking import Booking
from app.models.enums import UserRole
from app.models.room import Room
from app.models.slot import TimeSlot
from app.models.user import User

logger = logging.getLogger("app")


class BookingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_booking(
        self, user_id: int, room_id: int, slot_id: int, booking_date: date
    ) -> Booking:
        if booking_date < date.today():
            logger.warning(
                "Attempt to book in the past",
                extra={"user_id": user_id, "booking_date": str(booking_date)},
            )
            raise PastDateBookingError()

        result = await self.db.execute(
            select(TimeSlot).where(
                TimeSlot.id == slot_id
            )
        )
        slot = result.scalar_one_or_none()

        if not slot:
            logger.warning(
                "Slot not found",
                extra={"slot_id": slot_id},
            )
            raise SlotNotFoundError()

        if slot.room_id != room_id:
            logger.warning(
                "Slot does not belong to room",
                extra={"slot_id": slot_id, "room_id": room_id},
            )
            raise RoomMismatchError()

        booking = Booking(
            user_id=user_id,
            room_id=room_id,
            slot_id=slot_id,
            date=booking_date,
        )
        self.db.add(booking)

        try:
            await self.db.commit()
            await self.db.refresh(booking)
            logger.info(
                "Booking created",
                extra={
                    "booking_id": booking.id,
                    "user_id": user_id,
                    "room_id": room_id,
                    "slot_id": slot_id,
                    "date": str(booking_date),
                },
            )
            return booking
        except IntegrityError:
            await self.db.rollback()
            logger.warning(
                "Slot already booked",
                extra={"room_id": room_id, "slot_id": slot_id, "date": str(booking_date)},
            )
            raise BookingAlreadyExistsError()

    async def cancel_booking(self, booking_id: int, current_user: User) -> None:
        result = await self.db.execute(
            select(Booking).where(Booking.id == booking_id)
        )
        booking = result.scalar_one_or_none()
        if not booking:
            logger.warning(
                "Booking not found for cancellation",
                extra={"booking_id": booking_id},
            )
            raise BookingNotFoundError()

        if current_user.role != UserRole.ADMIN and booking.user_id != current_user.id:
            logger.warning(
                "User tried to cancel another user's booking",
                extra={
                    "user_id": current_user.id,
                    "username": current_user.username,
                    "booking_id": booking_id,
                    "booking_owner_id": booking.user_id,
                },
            )
            raise CancelForbiddenError()
        if booking.date < date.today():
            logger.warning(
                "Attempt to cancel past booking",
                extra={"booking_id": booking_id, "booking_date": str(booking.date)},
            )
            raise PastBookingCancellationError()

        await self.db.delete(booking)
        await self.db.commit()

        logger.info(
            "Booking cancelled",
            extra={"booking_id": booking_id, "user_id": current_user.id},
        )

from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from app.models.booking import Booking
from app.models.enums import UserRole
from app.models.room import Room
from app.models.slot import TimeSlot
from app.models.user import User


class BookingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_booking(
        self, user_id: int, room_id: int, slot_id: int, booking_date: date
    ) -> Booking:
        if booking_date < date.today():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "PAST_DATE", "detail": "Cannot book in the past"},
            )

        result = await self.db.execute(
            select(TimeSlot).where(
                TimeSlot.id == slot_id
            )
        )
        slot = result.scalar_one_or_none()

        if not slot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "SLOT_NOT_FOUND", "detail": "Slot not found"},
            )

        if slot.room_id != room_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "ROOM_NOT_FOUND", "detail": "Room not found or slot mismatch"},
            )

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
            return booking
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "SLOT_ALREADY_BOOKED",
                    "detail": "Этот временной слот уже забронирован.",
                },
            )

    async def cancel_booking(self, booking_id: int, current_user: User) -> None:
        result = await self.db.execute(
            select(Booking).where(Booking.id == booking_id)
        )
        booking = result.scalar_one_or_none()
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "BOOKING_NOT_FOUND", "detail": "Booking not found"},
            )

        if current_user.role != UserRole.ADMIN and booking.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "FORBIDDEN",
                    "detail": "Cannot cancel another user's booking",
                },
            )
        if booking.date < date.today():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "PAST_BOOKING_CANCELLATION",
                    "detail": "Нельзя отменить бронирование из прошлого.",
                },
            )

        await self.db.delete(booking)
        await self.db.commit()

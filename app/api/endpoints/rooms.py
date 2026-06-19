from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.error import ErrorResponse
from app.services.room_service import RoomService

router = APIRouter()


@router.get(
    "/rooms",
    responses={401: {"model": ErrorResponse}},
)
async def get_rooms(
    booking_date: date = Query(..., alias="date", description="Target date for room availability"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = RoomService(db)
    return await service.get_rooms(booking_date)

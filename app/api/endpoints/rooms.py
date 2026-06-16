from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.services.room_service import RoomService

router = APIRouter()


@router.get("/rooms")
async def get_rooms(
    date: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = RoomService(db)
    return await service.get_rooms(date)

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import PromoteRequest
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/admins")
async def promote_to_admin(
    body: PromoteRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    service = AuthService(db)
    await service.promote_to_admin(body.user_id)
    return {"detail": f"User {body.user_id} is now admin"}


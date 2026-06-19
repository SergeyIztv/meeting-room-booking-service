import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_admin
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import PromoteRequest
from app.schemas.error import ErrorResponse
from app.services.auth_service import AuthService

logger = logging.getLogger("app")

router = APIRouter()


@router.post(
    "/admins",
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
async def promote_to_admin(
    body: PromoteRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    service = AuthService(db)
    is_new_admin = await service.promote_to_admin(body.user_id)

    if not is_new_admin:
        return {"detail": "User is already an admin"}

    logger.info(
        "Admin promoted user",
        extra={"admin_id": admin.id, "target_user_id": body.user_id},
    )

    return {"detail": "User successfully promoted to admin"}


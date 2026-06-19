import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    InvalidCredentialsError,
    UsernameExistsError,
    UserNotFoundError,
)
from app.core.security import create_access_token, hash_password, verify_password
from app.models.enums import UserRole
from app.models.user import User

logger = logging.getLogger("app")


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, username: str, password: str) -> str:
        result = await self.db.execute(select(User).where(User.username == username))
        if result.scalar_one_or_none():
            logger.warning(
                "Registration failed: username already exists",
                extra={"username": username},
            )
            raise UsernameExistsError()


        user = User(
            username=username,
            hashed_password=hash_password(password)
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        logger.info(
            "User registered successfully",
            extra={"username": username, "user_id": user.id},
        )

        return create_access_token({"sub": str(user.id)})

    async def login(self, username: str, password: str) -> str:
        result = await self.db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        if not user or not verify_password(password, user.hashed_password):
            logger.warning(
                "Failed login attempt",
                extra={"username": username},
            )
            raise InvalidCredentialsError()

        logger.info(
            "User logged in successfully",
            extra={"username": username, "user_id": user.id},
        )

        return create_access_token({"sub": str(user.id)})

    async def promote_to_admin(self, user_id: int) -> bool:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            logger.warning(
                "Promotion failed: user not found",
                extra={"user_id": user_id},
            )
            raise UserNotFoundError()

        if user.role == UserRole.ADMIN:
            logger.info(
                "User is already admin",
                extra={"user_id": user_id},
            )
            return False

        user.role = UserRole.ADMIN
        await self.db.commit()

        logger.info(
            "User promoted to admin",
            extra={"user_id": user_id},
        )
        return True

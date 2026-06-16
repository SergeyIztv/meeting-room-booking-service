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


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, username: str, password: str) -> str:
        result = await self.db.execute(select(User).where(User.username == username))
        if result.scalar_one_or_none():
            raise UsernameExistsError()


        user = User(
            username=username,
            hashed_password=hash_password(password)
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        return create_access_token({"sub": str(user.id)})

    async def login(self, username: str, password: str) -> str:
        result = await self.db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        if not user or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError()

        return create_access_token({"sub": str(user.id)})

    async def promote_to_admin(self, user_id: int) -> None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise UserNotFoundError()

        if user.role == UserRole.ADMIN:
            return

        user.role = UserRole.ADMIN
        await self.db.commit()

import os

# Принудительно ставим test database ДО загрузки settings (чтоб .env не перебил)
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres@localhost:5432/meeting_room_test"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-which-is-long-enough-32bytes"

import asyncio

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app
from app.models.enums import UserRole

# Перебиваем ещё раз — на случай если pydantic_settings перезаписал os.environ из .env
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres@localhost:5432/meeting_room_test"
os.environ["JWT_SECRET_KEY"] = "test-secret-key"
settings.database_url = os.environ["DATABASE_URL"]

engine = create_async_engine(settings.database_url, poolclass=NullPool, echo=False)


@pytest.fixture(scope="session", autouse=True)
async def init_database():
    """Создает структуру таблиц ОДИН раз перед всеми тестами и удаляет после."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session():
    """Изолированная сессия: перехватываем commit -> savepoint rollback + begin_nested.

    Все изменения остаются внутри соединения, rollback в конце теста откатывает всё.
    """
    async with engine.connect() as connection:
        transaction = await connection.begin()
        session = AsyncSession(bind=connection)

        # Имитируем commit: начинаем новый savepoint (старый сольётся сам),
        # но данные остаются внутри внешней транзакции
        async def _intercepted_commit():
            await session.flush()
            # Начинаем новый savepoint, старый автоматически завершается
            await connection.begin_nested()
        session.commit = _intercepted_commit

        await connection.begin_nested()

        yield session

        await session.close()
        await transaction.rollback()


@pytest.fixture
async def client(db_session):
    """Тестовый клиент, который подменяет get_db на изолированную сессию."""

    app.dependency_overrides[get_db] = lambda: db_session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def admin_token(client, db_session):
    """Регистрирует пользователя и назначает ему role=admin напрямую в БД."""
    from app.core.security import hash_password
    from app.models.user import User
    from sqlalchemy import select

    resp = await client.post("/auth/register", json={"username": "admin", "password": "Strong!Pass1"})
    token = resp.json()["access_token"]

    import json, base64
    payload_b64 = token.split(".")[1]
    payload_b64 += "=" * (4 - len(payload_b64) % 4)
    user_id = int(json.loads(base64.urlsafe_b64decode(payload_b64))["sub"])

    result = await db_session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()
    user.role = UserRole.ADMIN
    await db_session.flush()

    return token

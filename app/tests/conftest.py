import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres@localhost:5432/meeting_room_test")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")

import asyncio

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app

engine = create_async_engine(settings.database_url, poolclass=NullPool, echo=False)
TestingSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


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
    """Создает изолированную транзакцию для конкретного теста.

    В конце теста делает ROLLBACK, стирая все изменения этого теста.
    """
    async with engine.connect() as connection:
        transaction = await connection.begin()
        async with TestingSessionLocal(bind=connection) as session:
            yield session
        await transaction.rollback()


@pytest.fixture
async def client(db_session):
    """Тестовый клиент, который подменяет get_db на изолированную сессию."""
    # Переопределяем зависимость FastAPI на нашу тестовую сессию с rollback
    app.dependency_overrides[get_db] = lambda: db_session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()

import os
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app
from app.models.enums import UserRole

os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres@localhost:5432/meeting_room_test"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-which-is-long-enough-32bytes"
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
    async def _override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = _override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def admin_token(client, db_session):
    """Регистрирует пользователя и назначает ему role=admin напрямую в БД."""
    from app.core.security import hash_password
    from app.models.user import User
    from sqlalchemy import select

    admin_user = User(
        username="admin_test",
        hashed_password=hash_password("Strong!Pass1"),
        role=UserRole.ADMIN
    )
    db_session.add(admin_user)
    await db_session.flush()

    login_data = {"username": "admin_test", "password": "Strong!Pass1"}

    resp = await client.post("/auth/login", json=login_data)

    return resp.json()["access_token"]

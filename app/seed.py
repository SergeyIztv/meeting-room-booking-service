import logging
from datetime import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.room import Room
from app.models.slot import TimeSlot

logger = logging.getLogger("app")

ROOMS = [
    {"name": "Конференц-зал А", "description": "Большая переговорная на 20 человек, проектор, видеоконференция"},
    {"name": "Конференц-зал Б", "description": "Средняя переговорная на 10 человек, маркерная доска"},
    {"name": "Переговорная В", "description": "Малая переговорная на 4 человека"},
    {"name": "Лаунж-зона", "description": "Неформальное пространство для встреч на 6 человек"},
]

SLOTS = [
    (time(9, 0), time(10, 0)),
    (time(10, 0), time(11, 0)),
    (time(11, 0), time(12, 0)),
    (time(12, 0), time(13, 0)),
    (time(13, 0), time(14, 0)),
    (time(14, 0), time(15, 0)),
    (time(15, 0), time(16, 0)),
    (time(16, 0), time(17, 0)),
    (time(17, 0), time(18, 0)),
]


async def seed_database(db: AsyncSession) -> None:
    result = await db.execute(select(Room))
    if result.scalars().first():
        return

    for room_data in ROOMS:
        room = Room(name=room_data["name"], description=room_data["description"])
        db.add(room)
        await db.flush()

        for start, end in SLOTS:
            slot = TimeSlot(room_id=room.id, start_time=start, end_time=end)
            db.add(slot)

    await db.commit()
    logger.info("Database seeded with %d rooms and %d slots per room", len(ROOMS), len(SLOTS))


if __name__ == "__main__":
    import asyncio
    from app.core.database import async_session
    from app.core.logger import setup_logging

    setup_logging()

    async def main():
        async with async_session() as session:
            await seed_database(session)

    asyncio.run(main())

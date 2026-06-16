# Спецификация сервиса бронирования переговорных комнат

## 1. Общее описание

Веб-сервис для автоматизации бронирования переговорных комнат в коворкинге. Позволяет сотрудникам просматривать доступность комнат, создавать и отменять свои бронирования. Администраторы могут управлять любыми бронированиями.

---

## 2. Технический стек

| Компонент          | Технология                     |
|---------------------|--------------------------------|
| Язык                | Python 3.11+                   |
| Веб-фреймворк       | FastAPI                        |
| Управление зависимостями | Poetry (pyproject.toml + poetry.lock) |
| Тестирование        | pytest (юнит-тесты + интеграционные тесты) |
| Аутентификация      | JWT (ограниченный срок действия) |
| Контейнеризация     | Docker + Docker Compose        |
| База данных         | PostgreSQL                     |
| ORM                 | SQLAlchemy / SQLModel          |

---

## 3. Модели данных

### 3.1. User (Пользователь)

| Поле       | Тип         | Описание                        |
|------------|-------------|----------------------------------|
| id         | int (PK)    | Уникальный идентификатор         |
| username   | str (unique)| Логин пользователя               |
| hashed_password | str   | Хеш пароля                      |
| role       | str         | Роль: `employee` или `admin`     |
| created_at | datetime    | Дата создания                    |

### 3.2. Room (Комната)

| Поле       | Тип         | Описание                        |
|------------|-------------|----------------------------------|
| id         | int (PK)    | Уникальный идентификатор         |
| name       | str         | Название комнаты                 |
| description| str (opt)   | Описание комнаты                 |

### 3.3. TimeSlot (Временной слот)

| Поле       | Тип         | Описание                        |
|------------|-------------|----------------------------------|
| id         | int (PK)    | Уникальный идентификатор         |
| room_id    | int (FK)    | Ссылка на комнату                |
| start_time | time        | Начало слота (например, 09:00)   |
| end_time   | time        | Конец слота (например, 11:00)    |

### 3.4. Booking (Бронирование)

| Поле       | Тип         | Описание                        |
|------------|-------------|----------------------------------|
| id         | int (PK)    | Уникальный идентификатор         |
| user_id    | int (FK)    | Кто забронировал                 |
| room_id    | int (FK)    | Какая комната                    |
| slot_id    | int (FK)    | Какой слот                       |
| date       | date        | На какую дату                    |
| created_at | datetime    | Дата создания брони              |

---

## 4. Роли и права доступа

| Действие                              | Employee | Admin |
|---------------------------------------|----------|-------|
| Регистрация (всегда employee)         | +        | +     |
| Получение JWT                         | +        | +     |
| Назначение admin                      | -        | +     |
| Просмотр комнат и доступности         | +        | +     |
| Создание брони (только для себя)      | +        | +     |
| Отмена СВОЕГО бронирования            | +        | +     |
| Отмена ЛЮБОГО бронирования            | -        | +     |

---

## 5. API Endpoints

### 5.1. Аутентификация

| Метод | Путь               | Описание                          | Auth |
|-------|--------------------|-----------------------------------|------|
| POST  | `/auth/register`   | Регистрация (всегда employee)     | No   |
| POST  | `/auth/login`      | Получение JWT (логин + пароль)    | No   |
| POST  | `/admins`          | Назначить admin (только admin)    | JWT  |

### 5.2. Комнаты и доступность

| Метод | Путь                    | Описание                          | Auth |
|-------|-------------------------|-----------------------------------|------|
| GET   | `/rooms?date=YYYY-MM-DD` | Список комнат со слотами и доступностью | JWT  |

### 5.3. Бронирования

| Метод | Путь               | Описание                                | Auth     |
|-------|--------------------|------------------------------------------|----------|
| POST  | `/bookings`        | Создать бронирование                     | JWT      |
| DELETE| `/bookings/{id}`   | Отменить бронирование                    | JWT      |

### 5.4. Данные для запросов

**POST `/auth/register`**
```json
{
  "username": "ivan",
  "password": "secret123"
}
```

**POST `/auth/login`**
```json
{
  "username": "ivan",
  "password": "secret123"
}
```
Response:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

**POST `/admins`** (только admin)
```json
{
  "user_id": 2
}
```
Response:
```json
{
  "detail": "User 2 is now admin"
}
```

**GET `/rooms?date=2026-06-15`**
Response:
```json
[
  {
    "id": 1,
    "name": "Конференц-зал А",
    "description": "Вместимость до 20 человек",
    "slots": [
      {
        "id": 1,
        "start_time": "09:00",
        "end_time": "11:00",
        "is_available": true,
        "booked_by": null
      },
      {
        "id": 2,
        "start_time": "13:00",
        "end_time": "16:00",
        "is_available": false,
        "booked_by": "ivan"
      }
    ]
  },
  {
    "id": 2,
    "name": "Переговорная B",
    "description": null,
    "slots": [
      {
        "id": 3,
        "start_time": "09:00",
        "end_time": "10:30",
        "is_available": true,
        "booked_by": null
      }
    ]
  }
]
```

**POST `/bookings`**
```json
{
  "room_id": 1,
  "slot_id": 2,
  "date": "2026-06-15"
}
```

---

## 6. Архитектура приложения (слои)

```
app/
├── main.py                 # Точка входа FastAPI
├── core/
│   ├── __init__.py
│   ├── config.py           # Настройки (БД, JWT secret, etc.)
│   ├── security.py         # Хеширование паролей, создание/верификация JWT
│   └── database.py         # Подключение к БД, сессии SQLAlchemy
├── models/
│   ├── __init__.py
│   ├── user.py             # ORM модель User
│   ├── room.py             # ORM модель Room
│   ├── slot.py             # ORM модель TimeSlot
│   └── booking.py          # ORM модель Booking
├── schemas/
│   ├── __init__.py
│   ├── user.py             # Pydantic схемы (UserCreate, UserResponse, Token)
│   ├── room.py             # Pydantic схемы (RoomResponse)
│   ├── slot.py             # Pydantic схемы (SlotResponse)
│   └── booking.py          # Pydantic схемы (BookingCreate, BookingResponse)
├── api/
│   ├── __init__.py
│   ├── deps.py             # Dependency injection (get_db, get_current_user)
│   └── endpoints/
│       ├── __init__.py
│       ├── auth.py         # Роуты /auth
│       ├── rooms.py        # Роуты /rooms
│       └── bookings.py     # Роуты /bookings
├── services/
│   ├── __init__.py
│   ├── auth_service.py     # Логика регистрации и логина
│   ├── room_service.py     # Логика работы с комнатами и слотами
│   └── booking_service.py  # Логика бронирования (с проверками)
└── tests/
    ├── __init__.py
    ├── conftest.py          # Фикстуры pytest (клиент, тестовая БД)
    ├── test_auth.py         # Юнит-тесты аутентификации
    ├── test_rooms.py        # Юнит-тесты комнат/слотов
    ├── test_bookings.py     # Юнит-тесты бронирований
    └── test_integration.py  # Интеграционные тесты
```

---

## 7. Бизнес-логика

### 7.1. Просмотр доступности
- `GET /rooms?date=...` возвращает все комнаты, каждая со своими слотами.
- Для каждого слота проставляется `is_available` — есть ли booking с `(room_id, slot_id, date)`.
- Если слот занят — указывается `booked_by` (логин пользователя).

### 7.2. Бронирование
1. **Создание бронирования:**
   - Проверить, что комната и слот существуют.
   - Проверить, что слот принадлежит указанной комнате.
   - Проверить, что дата бронирования — не в прошлом.
   - Проверить, что на указанную дату, комнату и слот нет другого бронирования.
   - Создать запись в таблице bookings.

2. **Отмена бронирования:**
   - Employee может отменить только своё бронирование (user_id == current_user.id).
   - Admin может отменить любое бронирование.
   - Бронь удаляется физически или помечается как отменённая (soft delete).

---

## 8. Обработка ошибок

Формат ошибки:
```json
{
  "code": "SLOT_ALREADY_BOOKED",
  "detail": "Этот временной слот уже забронирован."
}
```

| HTTP Status | Описание                               |
|-------------|----------------------------------------|
| 200         | Успех                                  |
| 201         | Успешное создание                      |
| 400         | Некорректные данные                    |
| 401         | Не авторизован (нет / невалидный JWT)  |
| 403         | Доступ запрещён (чужое бронирование)   |
| 404         | Ресурс не найден                       |
| 409         | Конфликт (слот уже занят)              |

---

## 9. Настройки (config)

```
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/meeting_room_db
JWT_SECRET_KEY=<случайная строка>
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
```

---

## 10. Docker

### Dockerfile
- Base image: `python:3.11-slim`
- Установка poetry.
- Копирование pyproject.toml и poetry.lock.
- Установка зависимостей.
- Копирование кода приложения.
- Команда запуска: `uvicorn app.main:app --host 0.0.0.0 --port 8000`

### docker-compose.yml
```yaml
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: meeting_room_db
    ports:
      - "5432:5432"
  app:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - db
    environment:
      DATABASE_URL: postgresql+asyncpg://user:pass@db:5432/meeting_room_db
```

---

## 11. Критерии оценки (напоминание)

1. **Технические требования:** Python 3.11+, FastAPI, poetry, pytest, Docker, Git, README.
2. **Функциональные требования:** Все HTTP методы, REST, JWT-аутентификация.
3. **Дополнительно:** Интеграционные тесты, PostgreSQL + SQLAlchemy, docker-compose.
4. **Изоляция данных:** employee не видит чужие брони, admin видит все.
5. **Качество кода:** разделение на слои (api/services/models/schemas), чистота.
6. **Тестовое покрытие:** юнит-тесты + интеграционные тесты.
7. **Документация:** README с инструкцией по запуску и примерами.

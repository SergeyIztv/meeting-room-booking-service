# Meeting Room Booking Service

Сервис бронирования переговорных комнат.

## Возможности

- **Аутентификация**: Регистрация новых пользователей и авторизация через JWT.
- **Просмотр доступности**: Просмотр списка комнат и статуса их временных слотов на определенную дату.
- **Бронирование**: Создание брони на свободный слот в выбранной комнате.
- **Отмена брони**: Возможность отменить бронирование (обычные пользователи могут отменять только свои брони, администраторы — любые).
- **Администрирование**: Управление правами и повышение пользователей до роли администратора.

## Запуск через Docker

```bash
docker compose up --build
```

Сервис будет доступен на `http://localhost:8000`.
Swagger-документация: `http://localhost:8000/docs`.

При первом запуске автоматически создаются таблицы БД и наполняются начальными данными (4 комнаты, 9 слотов на каждую).

## Требования

- Python 3.12+
- PostgreSQL
- Poetry (для локальной разработки)

## Запуск локально

### Установка

```bash
git clone git@github.com:SergeyIztv/meeting-room-booking-service.git
cd meeting-room-booking-service
poetry install
```

### Настройка

Создайте файл `.env` в корне проекта:

```env
DATABASE_URL=postgresql+asyncpg://postgres@localhost:5432/booking_db
JWT_SECRET_KEY=your-secret-key
JWT_EXPIRE_MINUTES=30
```

### Запуск

```bash
poetry run uvicorn app.main:app --reload
```

### Наполнение БД начальными данными

При запуске через `docker compose` или `uvicorn` данные загружаются автоматически.
Для ручного запуска:

```bash
poetry run python -m app.seed
```

## Переменные окружения

| Переменная | Обязательная | По умолчанию | Описание |
|---|---|---|---|
| `DATABASE_URL` | Да | — | URL подключения к PostgreSQL |
| `JWT_SECRET_KEY` | Да | — | Секретный ключ для подписи JWT |
| `JWT_EXPIRE_MINUTES` | Нет | `60` | Время жизни токена в минутах |
| `LOG_LEVEL` | Нет | `INFO` | Уровень логирования |

## Логирование

В проекте настроено структурированное логирование в формате JSON. При запуске через Docker логи приложения дублируются на хост-машину в папку `./logs/app.log`.

- **Консоль**: читаемые текстовые логи для разработки.
- **Файл `app.log`**: JSON для интеграции со сборщиками логов (Promtail, FluentBit).

## API Endpoints

### Аутентификация

```bash
# Регистрация
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "Strong!Pass1"}'

# Логин
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "Strong!Pass1"}'
```

Ответ содержит `access_token` для последующих запросов.

### Комнаты

```bash
# Просмотр доступности на дату
curl http://localhost:8000/rooms?date=2026-06-19 \
  -H "Authorization: Bearer <token>"
```

### Бронирования

```bash
# Создать бронь
curl -X POST http://localhost:8000/bookings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"room_id": 1, "slot_id": 1, "date": "2026-06-19"}'

# Отменить свою бронь
curl -X DELETE http://localhost:8000/bookings/1 \
  -H "Authorization: Bearer <token>"
```

### Администрирование

```bash
# Повысить пользователя до администратора (требуется токен администратора)
curl -X POST http://localhost:8000/admins \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <admin-token>" \
  -d '{"user_id": 2}'
```

## Тестирование

```bash
pytest app/tests -v
```

Для тестов используется отдельная БД `meeting_room_test` (настраивается в `app/tests/conftest.py`).


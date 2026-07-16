# Avix

Telegram-бот для управления командами и задачами: приглашения, роли, общие и персональные задачи, отчёты, напоминания, подписка через Telegram Stars, админ-панель в боте и REST API.

## Возможности

- Создание команд и безопасные invite-ссылки (токен хранится только как SHA-256 hash)
- Роли: owner, manager, member
- Общие и персональные задачи, дедлайны, вложения, отчёты
- Напоминания и фоновый worker просрочки
- Подписка Premium через Telegram Stars (XTR)
- Админ API (JWT) и админ-меню в Telegram
- Redis: FSM, rate limit, idempotency, distributed locks, cache
- Docker Compose: api, bot, worker, PostgreSQL, Redis

## Архитектура

```mermaid
flowchart TB
    subgraph presentation
        BOT[aiogram bot]
        API[FastAPI]
    end
    subgraph application
        UC[Use cases / services]
        DTO[DTO]
        PORTS[Repository interfaces]
    end
    subgraph domain
        ENT[Entities & enums]
    end
    subgraph infrastructure
        DB[(PostgreSQL)]
        REDIS[(Redis)]
        TG[Telegram sender]
        WORKER[Notification worker]
    end
    BOT --> UC
    API --> UC
    WORKER --> UC
    UC --> PORTS
    UC --> ENT
    PORTS --> DB
    UC --> REDIS
    WORKER --> TG
    BOT --> REDIS
```

## Структура проекта

```
src/app/
  config/           # pydantic-settings
  domain/           # entities
  application/      # use cases, DTO, interfaces, exceptions
  infrastructure/   # SQLAlchemy, Redis, logging, migrations
  presentation/
    bot/            # routers, keyboards, FSM, texts
    api/            # FastAPI routers, auth
  workers/          # notification/overdue worker
  shared/           # enums, constants, container holder
tests/
  unit/
  integration/
  e2e/
scripts/
  start.sh
  wait-for-services.py
```

| Слой | Ответственность |
|------|-----------------|
| `presentation` | Telegram handlers, HTTP endpoints |
| `application` | Бизнес-правила, RBAC, лимиты, идемпотентность |
| `domain` | Сущности и enum |
| `infrastructure` | ORM, Redis, внешние адаптеры |

## Стек

Python 3.13+, aiogram 3, FastAPI, SQLAlchemy 2 async, PostgreSQL, asyncpg, Alembic, Redis, Pydantic v2, structlog, APScheduler-style worker loop, uv, Ruff, mypy, pytest.

## Требования

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)
- Docker & Docker Compose (для production-like запуска)
- Telegram Bot Token

## Локальный запуск

```bash
cp .env.example .env
# заполните BOT_TOKEN, POSTGRES_*, REDIS_URL, JWT_SECRET

uv sync --all-extras
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d postgres redis
uv run alembic upgrade head
uv run python -m app.main api      # терминал 1
uv run python -m app.main bot      # терминал 2 (polling)
uv run python -m app.main worker   # терминал 3
```

## Docker

```bash
cp .env.example .env
make up
# или
docker compose up --build
```

Сервисы: `api` (8000), `bot`, `worker`, `postgres`, `redis`.

## Настройка Telegram-бота

1. Создайте бота через [@BotFather](https://t.me/BotFather)
2. Укажите `BOT_TOKEN` в `.env`
3. Для админов добавьте Telegram ID в `ADMIN_TELEGRAM_IDS`
4. Локально: `BOT_MODE=polling`
5. Production: `BOT_MODE=webhook`

## Webhook

```env
BOT_MODE=webhook
BOT_WEBHOOK_URL=https://your-domain.com
BOT_WEBHOOK_SECRET=long-random-secret
BOT_WEBHOOK_PATH=/telegram/webhook
```

1. Поднимите `api` с TLS (reverse proxy)
2. Запустите `bot` контейнер — он вызовет `setWebhook`
3. Telegram шлёт updates на `POST /telegram/webhook` с заголовком `X-Telegram-Bot-Api-Secret-Token`

## Telegram Stars

1. Включите платежи в BotFather для Stars
2. Пользователь открывает «Подписка» в боте
3. Бот отправляет invoice (`currency=XTR`, `provider_token=""`)
4. Обработчики: `pre_checkout_query`, `successful_payment`
5. `PaymentService` активирует подписку идемпотентно по `payload`

## Переменные окружения

| Переменная | Описание |
|------------|----------|
| `APP_ENV` | development / test / production |
| `APP_DEBUG` | debug flag |
| `BOT_TOKEN` | Telegram bot token |
| `BOT_MODE` | polling / webhook |
| `BOT_WEBHOOK_URL` | Public API URL |
| `BOT_WEBHOOK_SECRET` | Webhook secret |
| `POSTGRES_HOST` | DB host |
| `POSTGRES_PORT` | DB port |
| `POSTGRES_DB` | Database name |
| `POSTGRES_USER` | DB user |
| `POSTGRES_PASSWORD` | DB password |
| `REDIS_URL` | Redis connection URL |
| `JWT_SECRET` | Admin API JWT secret |
| `ADMIN_TELEGRAM_IDS` | Comma-separated admin IDs |
| `LOG_LEVEL` | INFO, DEBUG, ... |

## Миграции

```bash
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "description"
```

## Worker

```bash
uv run python -m app.main worker
```

Каждые `NOTIFICATION_WORKER_INTERVAL_SECONDS` секунд:
- отправляет due notifications из таблицы `notifications`
- помечает просроченные assignments и создаёт уведомления

## Тесты

```bash
# PostgreSQL + Redis должны быть доступны
export TEST_DATABASE_URL=postgresql+asyncpg://avix:avix@localhost:5432/avix_test
export TEST_REDIS_URL=redis://localhost:6379/1
uv run pytest -q
```

## Ruff и mypy

```bash
make lint
make mypy
```

## Бизнес-сценарии

1. `/start` → регистрация пользователя
2. «Создать команду» → owner + invite link
3. Переход по `?start=invite_<token>` → вступление
4. Создание общей задачи → assignments всем участникам
5. Участник отправляет отчёт → уведомление owner
6. Worker помечает просрочку → DM участнику и owner
7. Оплата Premium → активация подписки в транзакции

## Модель ролей

| Роль | Права |
|------|-------|
| owner | команда, подписка, managers, удаление |
| manager | задачи, участники (без оплаты/owner) |
| member | свои задачи, отчёты, вопросы |

## Подписки

| План | Лимиты |
|------|--------|
| Free | 1 команда, 5 участников, 10 активных задач |
| Premium | расширенные лимиты, групповые уведомления, аналитика |

## Уведомления

Типы: назначение, дедлайн (24h/3h/1h/now), просрочка, отчёт, вопрос. Хранятся в `notifications` с `scheduled_at`; worker выбирает пачками.

## Идемпотентность

- `app:idempotency:update:{update_id}` — Telegram updates
- `app:lock:payment:{payload}` — платежи
- Unique constraints на `payments.payload`, `telegram_payment_charge_id`

## Redis

| Key | Назначение |
|-----|------------|
| `app:user:{telegram_id}` | cache user |
| `app:team:{team_id}` | cache team |
| `app:invite:{token_hash}` | invite metadata |
| `app:fsm:*` | aiogram FSM |
| `app:rate_limit:user:{id}:{action}` | rate limiting |

## ER-диаграмма

```mermaid
erDiagram
    users ||--o{ team_members : has
    teams ||--o{ team_members : contains
    teams ||--o{ tasks : has
    tasks ||--o{ task_assignments : has
    task_assignments ||--o{ task_reports : has
    teams ||--o{ subscriptions : has
    subscription_plans ||--o{ subscriptions : defines
    users ||--o{ payments : makes
    teams ||--o{ notifications : receives
```

## Sequence: создание задачи

```mermaid
sequenceDiagram
    participant U as Owner
    participant B as Bot handler
    participant S as TaskService
    participant DB as PostgreSQL
    U->>B: FSM confirm
    B->>S: CreateTaskDTO
    S->>DB: insert task + assignments + notifications
    S-->>B: Task
    B-->>U: confirmation
```

## Sequence: оплата

```mermaid
sequenceDiagram
    participant U as User
    participant B as Bot
    participant P as PaymentService
    participant DB as PostgreSQL
    U->>B: successful_payment
    B->>P: PaymentDTO
    P->>DB: payment + subscription + team update
    P-->>B: Payment
    B-->>U: Premium activated
```

## Добавить новую функцию

1. Use case в `application/services/`
2. Router в `presentation/bot/routers/` или `presentation/api/routers/`
3. Тексты в `presentation/bot/texts/`
4. Тесты в `tests/unit/`

## Добавить use case

См. `CONTRIBUTING.md`.

## Добавить тариф

1. Запись в `shared/plans.py` или через `POST /admin/plans`
2. Обновить payment payload validation при необходимости

## Production checklist

- [ ] `APP_ENV=production`, `APP_DEBUG=false`
- [ ] Сильные секреты (`JWT_SECRET`, `BOT_WEBHOOK_SECRET`)
- [ ] TLS на reverse proxy
- [ ] `API_DOCS_ENABLED=false` или защита docs
- [ ] Backup PostgreSQL
- [ ] Мониторинг `/health`, `/ready`
- [ ] Лимиты ресурсов Docker

## Backup / Restore PostgreSQL

```bash
docker compose exec postgres pg_dump -U avix avix > backup.sql
docker compose exec -T postgres psql -U avix avix < backup.sql
```

## Troubleshooting

| Проблема | Решение |
|----------|---------|
| Бот не отвечает | Проверьте `BOT_TOKEN`, Redis, миграции |
| Webhook 403 | `BOT_WEBHOOK_SECRET` должен совпадать |
| Платёж не активирует Premium | Логи worker/api, дубликат payload |
| FSM сбрасывается | Redis доступен, prefix `app:fsm` |

## Ограничения текущей версии

- Упрощённый FSM создания задачи (не все 11 шагов в UI)
- Нет полного UI для аналитики, шаблонов, recurring tasks
- Групповые уведомления требуют ручной привязки `connected_chat_id`
- E2E тесты требуют поднятого PostgreSQL/Redis

## Roadmap

- Полный 11-шаговый wizard создания задачи
- Подключение Telegram-группы через UI
- Аналитика Premium в боте
- Повторяющиеся задачи и шаблоны
- Экспорт отчётов
- OpenTelemetry metrics

## Лицензия

MIT — см. `LICENSE`.

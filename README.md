# stripe-subscription-api

API для управления подписками и платежами на основе FastAPI + Stripe.

> **Курсовой проект** — «API для управления подписками и платежами (Stripe + FastAPI)»  
> Автор: Закян Арман Каренович

---

## Стек технологий

**Backend**
- Python 3.12 / FastAPI
- SQLAlchemy 2.0 (async) + Alembic
- PostgreSQL 16
- Pydantic v2
- JWT (python-jose) + bcrypt
- Stripe Python SDK v11
- Uvicorn + Docker

**Frontend**
- React 18 + TypeScript
- Vite 5
- TailwindCSS 3
- React Router v6
- TanStack Query v5
- Zustand (state management)
- Axios

**Инфраструктура**
- Docker + Docker Compose
- Nginx (reverse proxy)

---

## Быстрый старт

### 1. Клонирование репозитория

```bash
git clone https://github.com/yumesano/kurs_web.git
cd kurs_web
```

### 2. Конфигурация окружения

```bash
# Backend
cp backend/.env.example backend/.env
# Заполните STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY, STRIPE_WEBHOOK_SECRET
```

### 3. Запуск через Docker Compose

```bash
docker compose up --build
```

После запуска будет доступно:

| Сервис | URL |
|--------|-----|
| Frontend | http://localhost:5173 |
| API (через nginx) | http://localhost:8000/api/v1 |
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Backend (прямой) | http://localhost:8000 |
| Frontend (dev) | http://localhost:5173 |

### 4. Первый вход

Учётные данные администратора (из `seed.py`):
- **Email:** `admin@example.com`
- **Пароль:** `admin123`

---

## Структура проекта

```
stripe-subscription-api/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/   # auth, users, plans, subscriptions, payments, webhooks
│   │   ├── core/               # config, security, deps
│   │   ├── db/                 # session, base
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── schemas/            # Pydantic schemas
│   │   ├── services/           # бизнес-логика
│   │   └── main.py
│   ├── alembic/                # миграции БД
│   ├── requirements.txt
│   ├── Dockerfile
│   └── seed.py
├── frontend/
│   ├── src/
│   │   ├── pages/              # LoginPage, RegisterPage, DashboardPage, ...
│   │   ├── components/ui/      # DashboardLayout, StatusBadge, LoadingSpinner
│   │   ├── hooks/              # useApi.ts (React Query)
│   │   ├── lib/                # apiClient.ts, authStore.ts
│   │   └── types/              # TypeScript типы
│   ├── Dockerfile
│   └── package.json
├── nginx/
│   └── nginx.conf
├── docker/
│   └── init.sql
├── docker-compose.yml
└── README.md
```

---

## API Endpoints

### Аутентификация (`/api/v1/auth`)

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/register` | Регистрация пользователя |
| POST | `/login` | Авторизация, получение токенов |
| POST | `/refresh` | Обновление access-токена |
| POST | `/logout` | Выход, отзыв refresh-токена |
| GET | `/me` | Данные текущего пользователя |

### Тарифы (`/api/v1/plans`)

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/` | Список тарифных планов |
| GET | `/{id}` | Информация о тарифе |
| POST | `/` | Создать тариф (admin) |
| PATCH | `/{id}` | Обновить тариф (admin) |
| DELETE | `/{id}` | Деактивировать тариф (admin) |

### Подписки (`/api/v1/subscriptions`)

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/` | Мои подписки |
| POST | `/checkout` | Создать Stripe Checkout Session |
| GET | `/{id}` | Информация о подписке |
| POST | `/{id}/cancel` | Отменить подписку |
| GET | `/admin/all` | Все подписки (admin) |

### Биллинг (`/api/v1/billing`)

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/invoices` | Мои инвойсы |
| GET | `/invoices/{id}` | Конкретный инвойс |
| GET | `/payments` | История платежей |
| GET | `/admin/invoices` | Все инвойсы (admin) |
| GET | `/admin/payments` | Все платежи (admin) |

### Webhooks (`/api/v1/webhooks`)

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/stripe` | Получение событий от Stripe |

---

## Stripe Webhook

Для локальной разработки используйте [Stripe CLI](https://stripe.com/docs/stripe-cli):

```bash
# Установка Stripe CLI
brew install stripe/stripe-cli/stripe

# Авторизация
stripe login

# Перенаправление webhook-событий
stripe listen --forward-to localhost/api/v1/webhooks/stripe

# Копируйте webhook signing secret из вывода CLI в backend/.env
# STRIPE_WEBHOOK_SECRET=whsec_...
```

Обрабатываемые события:

| Событие | Действие |
|---------|----------|
| `checkout.session.completed` | Активация подписки |
| `customer.subscription.updated` | Обновление статуса подписки |
| `customer.subscription.deleted` | Отмена подписки |
| `invoice.paid` | Запись платежа |
| `invoice.payment_failed` | Статус просрочки |
| `invoice.created` | Создание инвойса |

---

## База данных

### Схема таблиц

- **users** — пользователи (email, пароль, роль, stripe_customer_id)
- **plans** — тарифные планы (название, цена, период, stripe_price_id)
- **subscriptions** — подписки пользователей (статус, stripe_subscription_id, период)
- **invoices** — счета на оплату (сумма, статус, ссылки на PDF)
- **payments** — история платежей (сумма, статус, stripe_payment_intent_id)
- **webhook_events** — лог webhook-событий Stripe
- **refresh_tokens** — активные refresh-токены

### Миграции

```bash
# Применить все миграции
docker compose exec backend alembic upgrade head

# Создать новую миграцию
docker compose exec backend alembic revision --autogenerate -m "описание"

# Откат последней миграции
docker compose exec backend alembic downgrade -1
```

---

## Разработка

### Backend (без Docker)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Запустить PostgreSQL отдельно, затем:
alembic upgrade head
python seed.py
uvicorn app.main:app --reload
```

### Frontend (без Docker)

```bash
cd frontend
npm install
cp .env.example .env.local
# Задайте VITE_API_URL=http://localhost:8000/api/v1
npm run dev
```

---

## Лицензия

MIT License. Проект создан в учебных целях.

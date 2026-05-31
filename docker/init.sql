-- ============================================================
-- Stripe Subscription API — Database Init Script
-- Автор: Закян А.К.
-- Описание: SQL-скрипт для инициализации базы данных
-- Примечание: В проекте используется Alembic для миграций.
--             Данный скрипт приведён для справки.
-- ============================================================

-- Расширения
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Типы (ENUM)
DO $$ BEGIN
    CREATE TYPE userrole AS ENUM ('admin', 'user');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE billinginterval AS ENUM ('monthly', 'yearly');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE subscriptionstatus AS ENUM (
        'active', 'canceled', 'past_due',
        'trialing', 'unpaid', 'incomplete', 'paused'
    );
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE invoicestatus AS ENUM (
        'draft', 'open', 'paid', 'uncollectible', 'void'
    );
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE paymentstatus AS ENUM (
        'pending', 'succeeded', 'failed', 'refunded', 'canceled'
    );
EXCEPTION WHEN duplicate_object THEN null; END $$;

-- ============================================================
-- Таблица: users
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id                  SERIAL PRIMARY KEY,
    email               VARCHAR(255) NOT NULL UNIQUE,
    hashed_password     VARCHAR(255) NOT NULL,
    full_name           VARCHAR(255),
    role                userrole NOT NULL DEFAULT 'user',
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    stripe_customer_id  VARCHAR(255) UNIQUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);
CREATE INDEX IF NOT EXISTS ix_users_stripe_customer_id ON users(stripe_customer_id);

-- ============================================================
-- Таблица: plans
-- ============================================================
CREATE TABLE IF NOT EXISTS plans (
    id                  SERIAL PRIMARY KEY,
    name                VARCHAR(100) NOT NULL,
    description         TEXT,
    price               NUMERIC(10, 2) NOT NULL,
    currency            VARCHAR(3) NOT NULL DEFAULT 'usd',
    interval            billinginterval NOT NULL DEFAULT 'monthly',
    features            TEXT,                        -- JSON array
    stripe_price_id     VARCHAR(255) UNIQUE,
    stripe_product_id   VARCHAR(255) UNIQUE,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- Таблица: subscriptions
-- ============================================================
CREATE TABLE IF NOT EXISTS subscriptions (
    id                      SERIAL PRIMARY KEY,
    user_id                 INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_id                 INTEGER NOT NULL REFERENCES plans(id) ON DELETE RESTRICT,
    status                  subscriptionstatus NOT NULL DEFAULT 'incomplete',
    stripe_subscription_id  VARCHAR(255) UNIQUE,
    stripe_customer_id      VARCHAR(255),
    current_period_start    TIMESTAMPTZ,
    current_period_end      TIMESTAMPTZ,
    canceled_at             TIMESTAMPTZ,
    trial_end               TIMESTAMPTZ,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS ix_subscriptions_status ON subscriptions(status);
CREATE INDEX IF NOT EXISTS ix_subscriptions_stripe_id ON subscriptions(stripe_subscription_id);

-- ============================================================
-- Таблица: invoices
-- ============================================================
CREATE TABLE IF NOT EXISTS invoices (
    id                          SERIAL PRIMARY KEY,
    user_id                     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subscription_id             INTEGER REFERENCES subscriptions(id) ON DELETE SET NULL,
    stripe_invoice_id           VARCHAR(255) UNIQUE,
    stripe_payment_intent_id    VARCHAR(255),
    amount_due                  NUMERIC(10, 2) NOT NULL,
    amount_paid                 NUMERIC(10, 2) NOT NULL DEFAULT 0,
    currency                    VARCHAR(3) NOT NULL DEFAULT 'usd',
    status                      invoicestatus NOT NULL DEFAULT 'draft',
    hosted_invoice_url          TEXT,
    invoice_pdf                 TEXT,
    period_start                TIMESTAMPTZ,
    period_end                  TIMESTAMPTZ,
    due_date                    TIMESTAMPTZ,
    paid_at                     TIMESTAMPTZ,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_invoices_user_id ON invoices(user_id);
CREATE INDEX IF NOT EXISTS ix_invoices_stripe_invoice_id ON invoices(stripe_invoice_id);
CREATE INDEX IF NOT EXISTS ix_invoices_status ON invoices(status);

-- ============================================================
-- Таблица: payments
-- ============================================================
CREATE TABLE IF NOT EXISTS payments (
    id                          SERIAL PRIMARY KEY,
    user_id                     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    invoice_id                  INTEGER REFERENCES invoices(id) ON DELETE SET NULL,
    stripe_payment_intent_id    VARCHAR(255) UNIQUE,
    stripe_charge_id            VARCHAR(255),
    amount                      NUMERIC(10, 2) NOT NULL,
    currency                    VARCHAR(3) NOT NULL DEFAULT 'usd',
    status                      paymentstatus NOT NULL DEFAULT 'pending',
    payment_method              VARCHAR(50),
    failure_message             VARCHAR(500),
    paid_at                     TIMESTAMPTZ,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_payments_user_id ON payments(user_id);
CREATE INDEX IF NOT EXISTS ix_payments_status ON payments(status);

-- ============================================================
-- Таблица: webhook_events
-- ============================================================
CREATE TABLE IF NOT EXISTS webhook_events (
    id                  SERIAL PRIMARY KEY,
    stripe_event_id     VARCHAR(255) NOT NULL UNIQUE,
    event_type          VARCHAR(100) NOT NULL,
    payload             TEXT NOT NULL,
    processed           BOOLEAN NOT NULL DEFAULT FALSE,
    error_message       TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at        TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_webhook_events_stripe_event_id ON webhook_events(stripe_event_id);
CREATE INDEX IF NOT EXISTS ix_webhook_events_event_type ON webhook_events(event_type);
CREATE INDEX IF NOT EXISTS ix_webhook_events_processed ON webhook_events(processed);

-- ============================================================
-- Таблица: refresh_tokens
-- ============================================================
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token       VARCHAR(500) NOT NULL UNIQUE,
    is_revoked  BOOLEAN NOT NULL DEFAULT FALSE,
    expires_at  TIMESTAMPTZ NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS ix_refresh_tokens_token ON refresh_tokens(token);

-- ============================================================
-- Seed data: sample plans
-- ============================================================
INSERT INTO plans (name, description, price, currency, interval, features) VALUES
(
    'Базовый',
    'Базовый тарифный план для начинающих',
    9.99, 'usd', 'monthly',
    '["До 5 проектов", "1 ГБ хранилища", "Email поддержка"]'
),
(
    'Профессиональный',
    'Расширенный план для профессионалов',
    29.99, 'usd', 'monthly',
    '["До 50 проектов", "10 ГБ хранилища", "Приоритетная поддержка", "API доступ"]'
),
(
    'Корпоративный',
    'Полный набор функций для бизнеса',
    99.99, 'usd', 'monthly',
    '["Неограниченные проекты", "100 ГБ хранилища", "24/7 поддержка", "API доступ", "Выделенный менеджер"]'
)
ON CONFLICT DO NOTHING;

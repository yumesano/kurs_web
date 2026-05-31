"""
Script to seed the database with initial data.
Safe to run multiple times — skips existing records.
"""
import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import select

from app.core.config import settings
from app.models.user import User, UserRole
from app.models.plan import Plan, BillingInterval

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

def make_hash(password: str) -> str:
    """Hash password using bcrypt directly to avoid passlib version issues."""
    import bcrypt
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


async def seed_db():
    # Read credentials from settings so they stay in sync with .env
    admin_email    = settings.FIRST_SUPERUSER_EMAIL
    admin_password = settings.FIRST_SUPERUSER_PASSWORD

    async with AsyncSessionLocal() as db:
        # --- Admin user ---
        result = await db.execute(select(User).where(User.email == admin_email))
        existing_admin = result.scalar_one_or_none()

        if not existing_admin:
            admin = User(
                email=admin_email,
                hashed_password=make_hash(admin_password),
                full_name="Administrator",
                role=UserRole.ADMIN,
                is_active=True,
            )
            db.add(admin)
            print(f"✅ Admin created: {admin_email} / {admin_password}")
        else:
            # Always sync the password from .env so login works after password change
            existing_admin.hashed_password = make_hash(admin_password)
            existing_admin.is_active = True
            print(f"✅ Admin password synced: {admin_email}")

        # --- Plans ---
        plans_data = [
            {
                "name": "Базовый",
                "description": "Базовый тарифный план для начинающих",
                "price": 9.99,
                "interval": BillingInterval.MONTHLY,
                "features": ["До 5 проектов", "1 ГБ хранилища", "Email поддержка"],
            },
            {
                "name": "Профессиональный",
                "description": "Расширенный план для профессионалов",
                "price": 29.99,
                "interval": BillingInterval.MONTHLY,
                "features": ["До 50 проектов", "10 ГБ хранилища", "Приоритетная поддержка", "API доступ"],
            },
            {
                "name": "Корпоративный",
                "description": "Полный набор функций для бизнеса",
                "price": 99.99,
                "interval": BillingInterval.MONTHLY,
                "features": ["Неограниченные проекты", "100 ГБ хранилища", "24/7 поддержка", "API доступ", "Выделенный менеджер"],
            },
            {
                "name": "Профессиональный (год)",
                "description": "Профессиональный план с годовой оплатой — скидка 20%",
                "price": 287.90,
                "interval": BillingInterval.YEARLY,
                "features": ["До 50 проектов", "10 ГБ хранилища", "Приоритетная поддержка", "API доступ", "Скидка 20%"],
            },
        ]

        for p in plans_data:
            result = await db.execute(select(Plan).where(Plan.name == p["name"]))
            existing = result.scalar_one_or_none()
            if not existing:
                plan = Plan(
                    name=p["name"],
                    description=p["description"],
                    price=p["price"],
                    currency="usd",
                    interval=p["interval"],
                    features=json.dumps(p["features"], ensure_ascii=False),
                    is_active=True,
                )
                db.add(plan)
                print(f"✅ Plan created: {p['name']}")
            else:
                print(f"ℹ️  Plan '{p['name']}' already exists, skipping.")

        await db.commit()
        print("\n🚀 Seed completed!")


if __name__ == "__main__":
    asyncio.run(seed_db())
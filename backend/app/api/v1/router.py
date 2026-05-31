from fastapi import APIRouter

from app.api.v1.endpoints import auth, plans, subscriptions, payments, webhooks, users

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Аутентификация"])
api_router.include_router(users.router, prefix="/users", tags=["Пользователи"])
api_router.include_router(plans.router, prefix="/plans", tags=["Тарифные планы"])
api_router.include_router(
    subscriptions.router, prefix="/subscriptions", tags=["Подписки"]
)
api_router.include_router(payments.router, prefix="/billing", tags=["Биллинг"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])

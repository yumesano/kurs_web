from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin, get_current_user, get_db
from app.models.subscription import SubscriptionStatus
from app.models.user import User
from app.schemas.subscription import (
    CheckoutSessionResponse,
    SubscriptionCancelResponse,
    SubscriptionCreate,
    SubscriptionResponse,
)
from app.services.plan_service import PlanService
from app.services.subscription_service import SubscriptionService

router = APIRouter()


@router.get("/", response_model=List[SubscriptionResponse])
async def list_my_subscriptions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Получить список подписок текущего пользователя."""
    sub_service = SubscriptionService(db)
    return await sub_service.get_user_subscriptions(current_user.id)


@router.post("/checkout", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    data: SubscriptionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Создать Stripe Checkout Session для оформления подписки."""
    plan_service = PlanService(db)
    plan = await plan_service.get_plan_by_id(data.plan_id)
    if not plan or not plan.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тарифный план не найден или недоступен",
        )

    sub_service = SubscriptionService(db)
    existing_subs = await sub_service.get_user_subscriptions(current_user.id)
    active_subs = [
        s for s in existing_subs if s.status == SubscriptionStatus.ACTIVE
    ]
    if active_subs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="У вас уже есть активная подписка",
        )

    return await sub_service.create_checkout_session(current_user, plan, data)


# Static admin route must be declared BEFORE the parameterized /{subscription_id}
# to prevent FastAPI from trying to coerce "admin" as an integer path param.
@router.get("/admin/all", response_model=List[SubscriptionResponse])
async def list_all_subscriptions(
    skip: int = 0,
    limit: int = 100,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Получить все подписки (только для администраторов)."""
    sub_service = SubscriptionService(db)
    return await sub_service.get_all_subscriptions(skip=skip, limit=limit)


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(
    subscription_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Получить информацию о подписке."""
    sub_service = SubscriptionService(db)
    subscription = await sub_service.get_subscription_by_id(subscription_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Подписка не найдена",
        )
    if subscription.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к этой подписке",
        )
    return subscription


@router.post("/{subscription_id}/cancel", response_model=SubscriptionCancelResponse)
async def cancel_subscription(
    subscription_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Отменить подписку (завершится в конце расчётного периода)."""
    sub_service = SubscriptionService(db)
    subscription = await sub_service.get_subscription_by_id(subscription_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Подписка не найдена",
        )
    if subscription.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к этой подписке",
        )
    if subscription.status == SubscriptionStatus.CANCELED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Подписка уже отменена",
        )

    updated = await sub_service.cancel_subscription(subscription)
    return SubscriptionCancelResponse(
        message="Подписка будет отменена в конце текущего периода",
        subscription_id=updated.id,
        status=updated.status,
    )

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin, get_current_user, get_db
from app.models.user import User
from app.schemas.plan import PlanCreate, PlanResponse, PlanUpdate
from app.services.plan_service import PlanService

router = APIRouter()


@router.get("/", response_model=List[PlanResponse])
async def list_plans(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить список доступных тарифных планов."""
    plan_service = PlanService(db)
    return await plan_service.get_all_plans(active_only=True)


@router.get("/{plan_id}", response_model=PlanResponse)
async def get_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить информацию о конкретном тарифе."""
    plan_service = PlanService(db)
    plan = await plan_service.get_plan_by_id(plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тарифный план не найден",
        )
    return plan


@router.post("/", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
async def create_plan(
    plan_data: PlanCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Создать новый тарифный план (только для администраторов)."""
    plan_service = PlanService(db)
    return await plan_service.create_plan(plan_data)


@router.patch("/{plan_id}", response_model=PlanResponse)
async def update_plan(
    plan_id: int,
    plan_data: PlanUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Обновить тарифный план (только для администраторов)."""
    plan_service = PlanService(db)
    plan = await plan_service.get_plan_by_id(plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тарифный план не найден",
        )
    return await plan_service.update_plan(plan, plan_data)


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Деактивировать тарифный план (только для администраторов)."""
    plan_service = PlanService(db)
    plan = await plan_service.get_plan_by_id(plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тарифный план не найден",
        )
    await plan_service.delete_plan(plan)

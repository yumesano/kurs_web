import asyncio
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin, get_current_user, get_db
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.user import User
from app.schemas.payment import InvoiceResponse, PaymentResponse

router = APIRouter()


@router.post("/sync")
async def sync_my_billing(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Синхронизировать инвойсы и платежи из Stripe напрямую.
    Работает без Stripe CLI — достаточно наличия stripe_customer_id.
    Таймаут 15 с на случай недоступности Stripe API."""
    from app.services.webhook_service import WebhookService
    webhook_service = WebhookService(db)
    try:
        result = await asyncio.wait_for(
            webhook_service.sync_user_billing(current_user),
            timeout=15.0,
        )
        return result
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Stripe API не отвечает. Проверьте подключение к интернету.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка синхронизации: {str(e)}",
        )


@router.get("/invoices", response_model=List[InvoiceResponse])
async def list_my_invoices(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Получить список счетов (инвойсов) текущего пользователя."""
    result = await db.execute(
        select(Invoice)
        .where(Invoice.user_id == current_user.id)
        .order_by(Invoice.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Получить конкретный инвойс."""
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Инвойс не найден")
    if invoice.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа")
    return invoice


@router.get("/payments", response_model=List[PaymentResponse])
async def list_my_payments(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Получить историю платежей текущего пользователя."""
    result = await db.execute(
        select(Payment)
        .where(Payment.user_id == current_user.id)
        .order_by(Payment.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


# Admin endpoints
@router.get("/admin/invoices", response_model=List[InvoiceResponse])
async def list_all_invoices(
    skip: int = 0,
    limit: int = 100,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Получить все инвойсы (только для администраторов)."""
    result = await db.execute(
        select(Invoice)
        .order_by(Invoice.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


@router.get("/admin/payments", response_model=List[PaymentResponse])
async def list_all_payments(
    skip: int = 0,
    limit: int = 100,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Получить все платежи (только для администраторов)."""
    result = await db.execute(
        select(Payment)
        .order_by(Payment.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())

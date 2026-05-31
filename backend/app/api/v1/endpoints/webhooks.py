import logging

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.services.stripe_service import StripeService
from app.services.webhook_service import WebhookService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/stripe", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint для получения webhook-событий от Stripe.
    Stripe подписывает запросы заголовком Stripe-Signature.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Отсутствует заголовок Stripe-Signature",
        )

    stripe_service = StripeService()
    try:
        event = await stripe_service.construct_webhook_event(payload, sig_header)
    except stripe.SignatureVerificationError:
        logger.warning("Invalid Stripe webhook signature")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недействительная подпись webhook",
        )
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ошибка обработки webhook",
        )

    webhook_service = WebhookService(db)
    await webhook_service.process_event(event)

    return {"status": "success", "event_id": event.id}

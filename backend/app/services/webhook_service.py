import json
import logging
from datetime import datetime, timezone
from typing import Optional

import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.invoice import Invoice, InvoiceStatus
from app.models.payment import Payment, PaymentStatus
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.webhook_event import WebhookEvent
from app.services.subscription_service import SubscriptionService

logger = logging.getLogger(__name__)


class WebhookService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.subscription_service = SubscriptionService(db)

    async def store_event(self, event: stripe.Event) -> WebhookEvent:
        """Store a Stripe webhook event in the database."""
        result = await self.db.execute(
            select(WebhookEvent).where(
                WebhookEvent.stripe_event_id == event.id
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        db_event = WebhookEvent(
            stripe_event_id=event.id,
            event_type=event.type,
            payload=json.dumps(dict(event.data.object), default=str),
            processed=False,
        )
        self.db.add(db_event)
        await self.db.commit()
        await self.db.refresh(db_event)
        return db_event

    async def process_event(self, event: stripe.Event) -> None:
        """Route and process a Stripe webhook event."""
        db_event = await self.store_event(event)

        # Idempotency: skip already-processed events
        if db_event.processed:
            logger.info(f"Webhook event {event.id} already processed, skipping")
            return

        try:
            handlers = {
                "checkout.session.completed": self._handle_checkout_completed,
                "customer.subscription.updated": self._handle_subscription_updated,
                "customer.subscription.deleted": self._handle_subscription_deleted,
                "invoice.paid": self._handle_invoice_paid,
                "invoice.payment_failed": self._handle_invoice_payment_failed,
                "invoice.created": self._handle_invoice_created,
            }

            handler = handlers.get(event.type)
            if handler:
                await handler(event.data.object)
                logger.info(f"Processed webhook event: {event.type} ({event.id})")
            else:
                logger.info(f"Unhandled webhook event type: {event.type}")

            db_event.processed = True
            db_event.processed_at = datetime.now(timezone.utc)

        except Exception as e:
            logger.error(f"Error processing webhook {event.id}: {e}", exc_info=True)
            db_event.error_message = str(e)[:500]

        await self.db.commit()

    async def _handle_checkout_completed(self, session: dict) -> None:
        """Handle checkout.session.completed event."""
        subscription_id = session.get("metadata", {}).get("subscription_id")
        stripe_subscription_id = session.get("subscription")

        if not subscription_id or not stripe_subscription_id:
            logger.warning("Checkout completed but missing subscription_id or stripe_subscription_id")
            return

        result = await self.db.execute(
            select(Subscription).where(Subscription.id == int(subscription_id))
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            logger.error(f"Subscription {subscription_id} not found")
            return

        # Retrieve full subscription data via StripeService (async, no event loop blocking)
        stripe_sub = await self.subscription_service.stripe_service.get_subscription(
            stripe_subscription_id
        )
        if not stripe_sub:
            logger.error(f"Could not retrieve Stripe subscription {stripe_subscription_id}")
            return

        await self.subscription_service.update_from_stripe(subscription, stripe_sub)
        logger.info(f"Subscription {subscription_id} activated via checkout")

    async def _handle_subscription_updated(self, stripe_sub: dict) -> None:
        """Handle customer.subscription.updated event."""
        result = await self.db.execute(
            select(Subscription).where(
                Subscription.stripe_subscription_id == stripe_sub["id"]
            )
        )
        subscription = result.scalar_one_or_none()
        if subscription:
            await self.subscription_service.update_from_stripe(subscription, stripe_sub)

    async def _handle_subscription_deleted(self, stripe_sub: dict) -> None:
        """Handle customer.subscription.deleted event."""
        result = await self.db.execute(
            select(Subscription).where(
                Subscription.stripe_subscription_id == stripe_sub["id"]
            )
        )
        subscription = result.scalar_one_or_none()
        if subscription:
            subscription.status = SubscriptionStatus.CANCELED
            if not subscription.canceled_at:
                subscription.canceled_at = datetime.now(timezone.utc)
            await self.db.commit()

    async def _handle_invoice_paid(self, stripe_invoice: dict) -> None:
        """Handle invoice.paid event."""
        await self._upsert_invoice(stripe_invoice, InvoiceStatus.PAID)

        # Create payment record
        payment_intent_id = stripe_invoice.get("payment_intent")
        if payment_intent_id:
            result = await self.db.execute(
                select(Payment).where(
                    Payment.stripe_payment_intent_id == payment_intent_id
                )
            )
            existing_payment = result.scalar_one_or_none()

            customer_id = stripe_invoice.get("customer")
            user_id = await self._get_user_id_by_stripe_customer(customer_id)

            if not existing_payment and user_id:
                invoice_result = await self.db.execute(
                    select(Invoice).where(
                        Invoice.stripe_invoice_id == stripe_invoice.get("id")
                    )
                )
                invoice = invoice_result.scalar_one_or_none()

                payment = Payment(
                    user_id=user_id,
                    invoice_id=invoice.id if invoice else None,
                    stripe_payment_intent_id=payment_intent_id,
                    amount=stripe_invoice.get("amount_paid", 0) / 100,
                    currency=stripe_invoice.get("currency", "usd"),
                    status=PaymentStatus.SUCCEEDED,
                    payment_method="card",
                    paid_at=datetime.now(timezone.utc),
                )
                self.db.add(payment)
                await self.db.commit()

    async def _handle_invoice_payment_failed(self, stripe_invoice: dict) -> None:
        """Handle invoice.payment_failed event."""
        await self._upsert_invoice(stripe_invoice, InvoiceStatus.OPEN)

        subscription_id = stripe_invoice.get("subscription")
        if subscription_id:
            result = await self.db.execute(
                select(Subscription).where(
                    Subscription.stripe_subscription_id == subscription_id
                )
            )
            subscription = result.scalar_one_or_none()
            if subscription:
                subscription.status = SubscriptionStatus.PAST_DUE
                await self.db.commit()

    async def _handle_invoice_created(self, stripe_invoice: dict) -> None:
        """Handle invoice.created event."""
        await self._upsert_invoice(stripe_invoice, InvoiceStatus.DRAFT)

    async def _upsert_invoice(self, stripe_invoice: dict, status: InvoiceStatus) -> Optional[Invoice]:
        """Create or update a local invoice from Stripe data."""
        stripe_invoice_id = stripe_invoice.get("id")
        if not stripe_invoice_id:
            return None

        customer_id = stripe_invoice.get("customer")
        user_id = await self._get_user_id_by_stripe_customer(customer_id)
        if not user_id:
            return None

        subscription_id = None
        stripe_sub_id = stripe_invoice.get("subscription")
        if stripe_sub_id:
            result = await self.db.execute(
                select(Subscription).where(
                    Subscription.stripe_subscription_id == stripe_sub_id
                )
            )
            sub = result.scalar_one_or_none()
            if sub:
                subscription_id = sub.id

        result = await self.db.execute(
            select(Invoice).where(Invoice.stripe_invoice_id == stripe_invoice_id)
        )
        invoice = result.scalar_one_or_none()

        period_start = None
        period_end = None
        if stripe_invoice.get("period_start"):
            period_start = datetime.fromtimestamp(stripe_invoice["period_start"], tz=timezone.utc)
        if stripe_invoice.get("period_end"):
            period_end = datetime.fromtimestamp(stripe_invoice["period_end"], tz=timezone.utc)

        if invoice:
            # Only update status if it's a meaningful forward transition
            invoice.status = status
            invoice.amount_paid = stripe_invoice.get("amount_paid", 0) / 100
            invoice.hosted_invoice_url = stripe_invoice.get("hosted_invoice_url")
            invoice.invoice_pdf = stripe_invoice.get("invoice_pdf")
            if status == InvoiceStatus.PAID and not invoice.paid_at:
                invoice.paid_at = datetime.now(timezone.utc)
        else:
            invoice = Invoice(
                user_id=user_id,
                subscription_id=subscription_id,
                stripe_invoice_id=stripe_invoice_id,
                stripe_payment_intent_id=stripe_invoice.get("payment_intent"),
                amount_due=stripe_invoice.get("amount_due", 0) / 100,
                amount_paid=stripe_invoice.get("amount_paid", 0) / 100,
                currency=stripe_invoice.get("currency", "usd"),
                status=status,
                hosted_invoice_url=stripe_invoice.get("hosted_invoice_url"),
                invoice_pdf=stripe_invoice.get("invoice_pdf"),
                period_start=period_start,
                period_end=period_end,
                paid_at=datetime.now(timezone.utc) if status == InvoiceStatus.PAID else None,
            )
            self.db.add(invoice)

        await self.db.commit()
        return invoice

    async def _get_user_id_by_stripe_customer(self, customer_id: str) -> Optional[int]:
        """Find user ID by Stripe customer ID."""
        from app.models.user import User
        result = await self.db.execute(
            select(User.id).where(User.stripe_customer_id == customer_id)
        )
        row = result.scalar_one_or_none()
        return row

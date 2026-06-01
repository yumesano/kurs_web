import asyncio
import logging
from typing import Optional

import stripe

from app.core.config import settings

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    """Service for interacting with Stripe API."""

    async def create_customer(self, email: str, name: Optional[str] = None) -> stripe.Customer:
        """Create a Stripe customer."""
        try:
            customer = await stripe.Customer.create_async(
                email=email,
                name=name,
                metadata={"source": "stripe-subscription-api"},
            )
            logger.info(f"Created Stripe customer: {customer.id} for email: {email}")
            return customer
        except stripe.StripeError as e:
            logger.error(f"Failed to create Stripe customer: {e}")
            raise

    async def get_customer(self, customer_id: str) -> Optional[stripe.Customer]:
        """Retrieve a Stripe customer."""
        try:
            return await stripe.Customer.retrieve_async(customer_id)
        except stripe.InvalidRequestError:
            return None
        except stripe.StripeError as e:
            logger.error(f"Failed to retrieve Stripe customer {customer_id}: {e}")
            raise

    async def create_checkout_session(
        self,
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        subscription_id: Optional[int] = None,
    ) -> stripe.checkout.Session:
        """Create a Stripe Checkout Session for subscription."""
        try:
            metadata = {}
            if subscription_id:
                metadata["subscription_id"] = str(subscription_id)

            session = await stripe.checkout.Session.create_async(
                customer=customer_id,
                payment_method_types=["card"],
                line_items=[
                    {
                        "price": price_id,
                        "quantity": 1,
                    }
                ],
                mode="subscription",
                success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=cancel_url,
                metadata=metadata,
            )
            logger.info(f"Created checkout session: {session.id}")
            return session
        except stripe.StripeError as e:
            logger.error(f"Failed to create checkout session: {e}")
            raise

    async def create_product(self, name: str, description: Optional[str] = None) -> stripe.Product:
        """Create a Stripe product."""
        try:
            product = await stripe.Product.create_async(
                name=name,
                description=description,
            )
            return product
        except stripe.StripeError as e:
            logger.error(f"Failed to create product: {e}")
            raise

    async def create_price(
        self,
        product_id: str,
        unit_amount: int,
        currency: str,
        interval: str,
    ) -> stripe.Price:
        """Create a Stripe price for a product."""
        try:
            price = await stripe.Price.create_async(
                product=product_id,
                unit_amount=unit_amount,
                currency=currency,
                recurring={"interval": interval},
            )
            return price
        except stripe.StripeError as e:
            logger.error(f"Failed to create price: {e}")
            raise

    async def cancel_subscription(
        self, stripe_subscription_id: str, at_period_end: bool = True
    ) -> stripe.Subscription:
        """Cancel a Stripe subscription."""
        try:
            if at_period_end:
                subscription = await stripe.Subscription.modify_async(
                    stripe_subscription_id,
                    cancel_at_period_end=True,
                )
            else:
                subscription = await stripe.Subscription.cancel_async(stripe_subscription_id)
            logger.info(f"Cancelled Stripe subscription: {stripe_subscription_id}")
            return subscription
        except stripe.StripeError as e:
            logger.error(f"Failed to cancel subscription {stripe_subscription_id}: {e}")
            raise

    async def resume_subscription(self, stripe_subscription_id: str) -> stripe.Subscription:
        """Resume a canceled subscription."""
        try:
            subscription = await stripe.Subscription.modify_async(
                stripe_subscription_id,
                cancel_at_period_end=False,
            )
            return subscription
        except stripe.StripeError as e:
            logger.error(f"Failed to resume subscription: {e}")
            raise

    async def retrieve_checkout_session(
        self, session_id: str
    ) -> Optional[stripe.checkout.Session]:
        """Retrieve a Stripe Checkout Session by ID."""
        try:
            return await stripe.checkout.Session.retrieve_async(session_id)
        except stripe.InvalidRequestError:
            return None
        except stripe.StripeError as e:
            logger.error(f"Failed to retrieve checkout session {session_id}: {e}")
            return None

    async def get_subscription(self, stripe_subscription_id: str) -> Optional[stripe.Subscription]:
        """Retrieve a Stripe subscription."""
        try:
            return await stripe.Subscription.retrieve_async(stripe_subscription_id)
        except stripe.InvalidRequestError:
            return None
        except stripe.StripeError as e:
            logger.error(f"Failed to retrieve Stripe subscription {stripe_subscription_id}: {e}")
            return None

    async def list_invoices(
        self, customer_id: str, limit: int = 10
    ) -> list:
        """List invoices for a customer."""
        try:
            invoices = await stripe.Invoice.list_async(customer=customer_id, limit=limit)
            return list(invoices.data)
        except stripe.StripeError as e:
            logger.error(f"Failed to list invoices: {e}")
            raise

    async def construct_webhook_event(
        self, payload: bytes, sig_header: str
    ) -> stripe.Event:
        """Construct and verify a Stripe webhook event (runs sync verification in thread pool)."""
        try:
            event = await asyncio.to_thread(
                stripe.Webhook.construct_event,
                payload,
                sig_header,
                settings.STRIPE_WEBHOOK_SECRET,
            )
            return event
        except stripe.SignatureVerificationError as e:
            logger.error(f"Webhook signature verification failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Webhook construction failed: {e}")
            raise

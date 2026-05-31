import logging
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.user import User
from app.models.plan import Plan
from app.schemas.subscription import SubscriptionCreate, CheckoutSessionResponse
from app.services.stripe_service import StripeService
from app.services.user_service import UserService

logger = logging.getLogger(__name__)


class SubscriptionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.stripe_service = StripeService()
        self.user_service = UserService(db)

    async def get_subscription_by_id(self, subscription_id: int) -> Optional[Subscription]:
        result = await self.db.execute(
            select(Subscription)
            .options(selectinload(Subscription.plan))
            .where(Subscription.id == subscription_id)
        )
        return result.scalar_one_or_none()

    async def get_user_subscriptions(self, user_id: int) -> List[Subscription]:
        result = await self.db.execute(
            select(Subscription)
            .options(selectinload(Subscription.plan))
            .where(Subscription.user_id == user_id)
            .order_by(Subscription.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_all_subscriptions(self, skip: int = 0, limit: int = 100) -> List[Subscription]:
        result = await self.db.execute(
            select(Subscription)
            .options(selectinload(Subscription.plan))
            .offset(skip)
            .limit(limit)
            .order_by(Subscription.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_stripe_id(self, stripe_subscription_id: str) -> Optional[Subscription]:
        result = await self.db.execute(
            select(Subscription).where(
                Subscription.stripe_subscription_id == stripe_subscription_id
            )
        )
        return result.scalar_one_or_none()

    async def create_checkout_session(
        self, user: User, plan: Plan, data: SubscriptionCreate
    ) -> CheckoutSessionResponse:
        """Create a Stripe checkout session for a subscription."""
        # Ensure Stripe customer exists
        if not user.stripe_customer_id:
            customer = await self.stripe_service.create_customer(
                email=user.email, name=user.full_name
            )
            await self.user_service.update_stripe_customer_id(user, customer.id)
            user.stripe_customer_id = customer.id

        # Ensure plan has Stripe price
        if not plan.stripe_price_id:
            product = await self.stripe_service.create_product(
                name=plan.name, description=plan.description
            )
            interval = "month" if plan.interval.value == "monthly" else "year"
            price = await self.stripe_service.create_price(
                product_id=product.id,
                unit_amount=int(plan.price * 100),  # Convert to cents
                currency=plan.currency,
                interval=interval,
            )
            from app.services.plan_service import PlanService
            plan_service = PlanService(self.db)
            await plan_service.update_stripe_ids(plan, price.id, product.id)
            plan.stripe_price_id = price.id

        # Create pending subscription record
        db_subscription = Subscription(
            user_id=user.id,
            plan_id=plan.id,
            status=SubscriptionStatus.INCOMPLETE,
            stripe_customer_id=user.stripe_customer_id,
        )
        self.db.add(db_subscription)
        await self.db.commit()
        await self.db.refresh(db_subscription)

        # Create Stripe checkout session
        success_url = f"{settings.FRONTEND_URL}/dashboard/subscriptions/success"
        cancel_url = f"{settings.FRONTEND_URL}/dashboard/plans"

        session = await self.stripe_service.create_checkout_session(
            customer_id=user.stripe_customer_id,
            price_id=plan.stripe_price_id,
            success_url=success_url,
            cancel_url=cancel_url,
            subscription_id=db_subscription.id,
        )

        return CheckoutSessionResponse(
            checkout_url=session.url,
            session_id=session.id,
        )

    async def cancel_subscription(self, subscription: Subscription) -> Subscription:
        """Cancel a subscription at period end."""
        if subscription.stripe_subscription_id:
            stripe_sub = await self.stripe_service.cancel_subscription(
                subscription.stripe_subscription_id, at_period_end=True
            )
            # update_from_stripe handles CANCELED status when cancel_at_period_end=True
            await self.update_from_stripe(subscription, stripe_sub)
        else:
            subscription.status = SubscriptionStatus.CANCELED

        # canceled_at is not returned by Stripe for at_period_end cancellations
        if not subscription.canceled_at:
            subscription.canceled_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(subscription)
        return subscription

    async def update_from_stripe(
        self, subscription: Subscription, stripe_data: dict
    ) -> Subscription:
        """Update local subscription from Stripe data."""
        status_map = {
            "active": SubscriptionStatus.ACTIVE,
            "canceled": SubscriptionStatus.CANCELED,
            "past_due": SubscriptionStatus.PAST_DUE,
            "trialing": SubscriptionStatus.TRIALING,
            "unpaid": SubscriptionStatus.UNPAID,
            "incomplete": SubscriptionStatus.INCOMPLETE,
            "paused": SubscriptionStatus.PAUSED,
        }

        stripe_status = stripe_data.get("status", "incomplete")
        # Subscriptions scheduled to cancel (cancel_at_period_end=True) are still
        # "active" in Stripe but should be shown as CANCELED locally so the user
        # knows cancellation is pending.
        if stripe_data.get("cancel_at_period_end") and stripe_status == "active":
            subscription.status = SubscriptionStatus.CANCELED
        else:
            subscription.status = status_map.get(stripe_status, SubscriptionStatus.INCOMPLETE)
        subscription.stripe_subscription_id = stripe_data.get("id")

        if stripe_data.get("current_period_start"):
            subscription.current_period_start = datetime.fromtimestamp(
                stripe_data["current_period_start"], tz=timezone.utc
            )
        if stripe_data.get("current_period_end"):
            subscription.current_period_end = datetime.fromtimestamp(
                stripe_data["current_period_end"], tz=timezone.utc
            )
        if stripe_data.get("canceled_at"):
            subscription.canceled_at = datetime.fromtimestamp(
                stripe_data["canceled_at"], tz=timezone.utc
            )
        if stripe_data.get("trial_end"):
            subscription.trial_end = datetime.fromtimestamp(
                stripe_data["trial_end"], tz=timezone.utc
            )

        await self.db.commit()
        await self.db.refresh(subscription)
        return subscription

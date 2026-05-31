from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.subscription import SubscriptionStatus
from app.schemas.plan import PlanResponse


class SubscriptionCreate(BaseModel):
    plan_id: int


class SubscriptionResponse(BaseModel):
    id: int
    user_id: int
    plan_id: int
    status: SubscriptionStatus
    stripe_subscription_id: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    canceled_at: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    plan: Optional[PlanResponse] = None

    model_config = {"from_attributes": True}


class CheckoutSessionResponse(BaseModel):
    checkout_url: str
    session_id: str


class SubscriptionCancelResponse(BaseModel):
    message: str
    subscription_id: int
    status: SubscriptionStatus

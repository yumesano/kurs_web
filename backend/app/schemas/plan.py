from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, field_validator
import json

from app.models.plan import BillingInterval


class PlanBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    currency: str = "usd"
    interval: BillingInterval = BillingInterval.MONTHLY
    features: Optional[List[str]] = None

    @field_validator("price")
    @classmethod
    def price_positive(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Цена не может быть отрицательной")
        return v


class PlanCreate(PlanBase):
    stripe_price_id: Optional[str] = None
    stripe_product_id: Optional[str] = None


class PlanUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    is_active: Optional[bool] = None
    features: Optional[List[str]] = None


class PlanResponse(PlanBase):
    id: int
    stripe_price_id: Optional[str] = None
    stripe_product_id: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @field_validator("features", mode="before")
    @classmethod
    def parse_features(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return []
        return v

    model_config = {"from_attributes": True}

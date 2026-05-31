from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.invoice import InvoiceStatus
from app.models.payment import PaymentStatus


class InvoiceResponse(BaseModel):
    id: int
    user_id: int
    subscription_id: Optional[int] = None
    stripe_invoice_id: Optional[str] = None
    amount_due: float
    amount_paid: float
    currency: str
    status: InvoiceStatus
    hosted_invoice_url: Optional[str] = None
    invoice_pdf: Optional[str] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    due_date: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaymentResponse(BaseModel):
    id: int
    user_id: int
    invoice_id: Optional[int] = None
    stripe_payment_intent_id: Optional[str] = None
    amount: float
    currency: str
    status: PaymentStatus
    payment_method: Optional[str] = None
    failure_message: Optional[str] = None
    paid_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

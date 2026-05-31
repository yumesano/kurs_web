import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class InvoiceStatus(str, enum.Enum):
    DRAFT = "draft"
    OPEN = "open"
    PAID = "paid"
    UNCOLLECTIBLE = "uncollectible"
    VOID = "void"


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subscription_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True
    )

    stripe_invoice_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=True, index=True)
    stripe_payment_intent_id: Mapped[str] = mapped_column(String(255), nullable=True)

    amount_due: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    amount_paid: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="usd", nullable=False)
    status: Mapped[InvoiceStatus] = mapped_column(
        Enum(InvoiceStatus, values_callable=lambda x: [e.value for e in x]),
        default=InvoiceStatus.DRAFT,
        nullable=False,
        index=True,
    )

    hosted_invoice_url: Mapped[str] = mapped_column(Text, nullable=True)
    invoice_pdf: Mapped[str] = mapped_column(Text, nullable=True)

    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user = relationship("User", back_populates="invoices")
    subscription = relationship("Subscription", back_populates="invoices")
    payments = relationship("Payment", back_populates="invoice", lazy="select")

    def __repr__(self) -> str:
        return f"<Invoice id={self.id} status={self.status}>"

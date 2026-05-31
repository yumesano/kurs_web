import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELED = "canceled"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    invoice_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True
    )

    stripe_payment_intent_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=True, index=True)
    stripe_charge_id: Mapped[str] = mapped_column(String(255), nullable=True)

    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="usd", nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, values_callable=lambda x: [e.value for e in x]),
        default=PaymentStatus.PENDING,
        nullable=False,
        index=True,
    )
    payment_method: Mapped[str] = mapped_column(String(50), nullable=True)
    failure_message: Mapped[str] = mapped_column(String(500), nullable=True)

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

    user = relationship("User", back_populates="payments")
    invoice = relationship("Invoice", back_populates="payments")

    def __repr__(self) -> str:
        return f"<Payment id={self.id} status={self.status}>"

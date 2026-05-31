import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"
    UNPAID = "unpaid"
    INCOMPLETE = "incomplete"
    PAUSED = "paused"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    plan_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("plans.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus, values_callable=lambda x: [e.value for e in x]),
        default=SubscriptionStatus.INCOMPLETE,
        nullable=False,
        index=True,
    )

    stripe_subscription_id: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=True, index=True
    )
    stripe_customer_id: Mapped[str] = mapped_column(String(255), nullable=True)

    current_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    canceled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    trial_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user = relationship("User", back_populates="subscriptions")
    plan = relationship("Plan", back_populates="subscriptions")
    invoices = relationship("Invoice", back_populates="subscription", lazy="select")

    def __repr__(self) -> str:
        return f"<Subscription id={self.id} status={self.status}>"

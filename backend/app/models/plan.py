import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class BillingInterval(str, enum.Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="usd", nullable=False)
    interval: Mapped[BillingInterval] = mapped_column(
        Enum(BillingInterval, values_callable=lambda x: [e.value for e in x]),
        default=BillingInterval.MONTHLY,
        nullable=False,
    )
    features: Mapped[str] = mapped_column(Text, nullable=True)

    stripe_price_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=True)
    stripe_product_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    subscriptions = relationship("Subscription", back_populates="plan", lazy="select")

    def __repr__(self) -> str:
        return f"<Plan id={self.id} name={self.name}>"

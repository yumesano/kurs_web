from app.db.base_class import Base  # noqa: F401

# Import all models here so Alembic can detect them
from app.models.user import User  # noqa: F401
from app.models.plan import Plan  # noqa: F401
from app.models.subscription import Subscription  # noqa: F401
from app.models.invoice import Invoice  # noqa: F401
from app.models.payment import Payment  # noqa: F401
from app.models.webhook_event import WebhookEvent  # noqa: F401
from app.models.refresh_token import RefreshToken  # noqa: F401

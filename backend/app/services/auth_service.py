from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, verify_token
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import TokenResponse


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_tokens(self, user: User) -> TokenResponse:
        access_token = create_access_token(subject=str(user.id))
        refresh_token = create_refresh_token(subject=str(user.id))

        # Save refresh token to DB
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        db_token = RefreshToken(
            user_id=user.id,
            token=refresh_token,
            expires_at=expires_at,
        )
        self.db.add(db_token)
        await self.db.commit()

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        # Verify JWT
        user_id = verify_token(refresh_token, token_type="refresh")
        if not user_id:
            return None

        # Check in DB
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token == refresh_token,
                RefreshToken.is_revoked == False,
                RefreshToken.expires_at > datetime.now(timezone.utc),
            )
        )
        db_token = result.scalar_one_or_none()
        if not db_token:
            return None

        # Return new access token
        return create_access_token(subject=user_id)

    async def revoke_refresh_token(self, refresh_token: str) -> bool:
        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token == refresh_token)
        )
        db_token = result.scalar_one_or_none()
        if not db_token:
            return False
        db_token.is_revoked = True
        await self.db.commit()
        return True

    async def revoke_all_user_tokens(self, user_id: int) -> None:
        await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .values(is_revoked=True)
        )
        await self.db.commit()

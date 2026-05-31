from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import (
    AccessTokenResponse,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
)
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import AuthService
from app.services.user_service import UserService

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """Регистрация нового пользователя."""
    user_service = UserService(db)
    existing_user = await user_service.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже зарегистрирован",
        )
    user = await user_service.create_user(user_data)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Авторизация пользователя, возвращает access и refresh токены."""
    user_service = UserService(db)
    user = await user_service.authenticate_user(credentials.email, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Учётная запись деактивирована",
        )

    auth_service = AuthService(db)
    return await auth_service.create_tokens(user)


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh_token(
    token_data: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """Обновление access-токена с помощью refresh-токена."""
    auth_service = AuthService(db)
    new_access_token = await auth_service.refresh_access_token(token_data.refresh_token)
    if not new_access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный или просроченный refresh-токен",
        )
    return AccessTokenResponse(access_token=new_access_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    token_data: RefreshRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Выход из системы — отзыв refresh-токена."""
    auth_service = AuthService(db)
    await auth_service.revoke_refresh_token(token_data.refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Получение данных текущего пользователя."""
    return current_user

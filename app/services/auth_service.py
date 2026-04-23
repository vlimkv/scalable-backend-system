from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    TokenPairResponse,
    RegisterRequest,
)
from app.schemas.user import UserResponse


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _build_auth_response(self, user: User) -> AuthResponse:
        access_token = create_access_token(user.id, user.role)
        refresh_token = create_refresh_token(user.id, user.token_version)

        return AuthResponse(
            user=UserResponse.model_validate(user),
            tokens=TokenPairResponse(
                access_token=access_token,
                refresh_token=refresh_token,
            ),
        )

    async def register(self, payload: RegisterRequest) -> AuthResponse:
        existing_user = await self.db.scalar(
            select(User).where(User.email == payload.email)
        )
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists",
            )

        user = User(
            email=payload.email,
            full_name=payload.full_name,
            hashed_password=hash_password(payload.password),
            role="member",
            is_active=True,
            token_version=0,
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        return self._build_auth_response(user)

    async def login(self, payload: LoginRequest) -> AuthResponse:
        user = await self.db.scalar(select(User).where(User.email == payload.email))
        if not user or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is inactive",
            )

        return self._build_auth_response(user)

    async def refresh(self, payload: RefreshRequest) -> AuthResponse:
        try:
            decoded = decode_token(payload.refresh_token)
            if decoded.get("type") != "refresh":
                raise ValueError("Invalid token type")

            user_id = int(decoded["sub"])
            token_version = int(decoded["token_version"])
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        user = await self.db.scalar(select(User).where(User.id == user_id))
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        if user.token_version != token_version:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked",
            )

        return self._build_auth_response(user)

    async def logout(self, payload: LogoutRequest) -> dict[str, str]:
        try:
            decoded = decode_token(payload.refresh_token)
            if decoded.get("type") != "refresh":
                raise ValueError("Invalid token type")

            user_id = int(decoded["sub"])
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        user = await self.db.scalar(select(User).where(User.id == user_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        user.token_version += 1
        await self.db.commit()

        return {"message": "Logged out successfully"}
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import (
    AccountDeleteRequest,
    ApiKeyInfoResponse,
    ApiKeyResponse,
    AuthResponse,
    LoginRequest,
    OAuthCallbackRequest,
    ProfileUpdateRequest,
    RegisterRequest,
    UserResponse,
)
from app.services.auth import AuthService

router = APIRouter()


@router.post("/register", response_model=AuthResponse)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    user = await AuthService.create_or_get_user(db, email=body.email, name=body.name)
    token = AuthService.create_jwt(str(user.id), user.email)
    return AuthResponse(token=token, user=UserResponse.model_validate(user))


@router.post("/login", response_model=AuthResponse)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    from sqlalchemy import select

    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    token = AuthService.create_jwt(str(user.id), user.email)
    return AuthResponse(token=token, user=UserResponse.model_validate(user))


@router.post("/oauth/callback", response_model=AuthResponse)
async def oauth_callback(
    body: OAuthCallbackRequest,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    user = await AuthService.create_or_get_user(
        db, email=body.email, name=body.name, avatar_url=body.avatar_url
    )
    token = AuthService.create_jwt(str(user.id), user.email)
    return AuthResponse(token=token, user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(user)


@router.post("/api-keys", response_model=ApiKeyResponse)
async def create_api_key(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApiKeyResponse:
    raw_key, _ = AuthService.generate_api_key()
    await AuthService.set_user_api_key(db, user.id, raw_key)
    return ApiKeyResponse(key=raw_key, created_at=user.created_at)


@router.delete("/api-keys", status_code=204)
async def revoke_api_key(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    from sqlalchemy import select

    result = await db.execute(select(User).where(User.id == user.id))
    u = result.scalar_one()
    u.api_key = None
    await db.commit()


@router.get("/api-keys", response_model=ApiKeyInfoResponse)
async def get_api_key_info(
    user: User = Depends(get_current_user),
) -> ApiKeyInfoResponse:
    if user.api_key:
        return ApiKeyInfoResponse(masked_key="..." + user.api_key[-8:], has_key=True)
    return ApiKeyInfoResponse(masked_key=None, has_key=False)


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    body: ProfileUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> UserResponse:
    if not body.name or not body.name.strip():
        raise HTTPException(status_code=422, detail="Name is required")
    updated = await AuthService.update_profile(db, user.id, body.name.strip())
    return UserResponse.model_validate(updated)


@router.delete("/account", status_code=200)
async def delete_account(
    body: AccountDeleteRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    try:
        await AuthService.delete_account(db, user.id, body.email_confirmation)
    except ValueError:
        raise HTTPException(status_code=400, detail="Email confirmation does not match")
    return {"message": "Account deleted"}

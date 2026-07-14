from collections.abc import AsyncGenerator
from typing import Any

from fastapi import Depends, Header, HTTPException
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models.user import User
from app.services.auth import AuthService

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


async def get_current_user(
    authorization: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = authorization[7:]

    # Try JWT first
    try:
        payload = AuthService.decode_jwt(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        pass

    # Try API key
    if token.startswith("wv_live_"):
        user = await AuthService.get_user_by_api_key(db, token)
        if user:
            return user

    raise HTTPException(status_code=401, detail="Invalid credentials")


async def get_optional_user(
    authorization: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None

    token = authorization[7:]

    try:
        payload = AuthService.decode_jwt(token)
        user_id = payload.get("sub")
        if user_id:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if user:
                return user
    except JWTError:
        pass

    if token.startswith("wv_live_"):
        user = await AuthService.get_user_by_api_key(db, token)
        if user:
            return user

    return None


async def require_admin(
    user: User = Depends(get_current_user),
) -> User:
    if user.plan != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

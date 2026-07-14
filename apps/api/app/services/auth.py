import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User


class AuthService:
    @staticmethod
    async def create_or_get_user(
        db: AsyncSession,
        email: str,
        name: str | None = None,
        avatar_url: str | None = None,
    ) -> User:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user:
            return user
        user = User(email=email, name=name, avatar_url=avatar_url)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    def create_jwt(user_id: str, email: str) -> str:
        payload = {
            "sub": user_id,
            "email": email,
            "exp": datetime.now(timezone.utc)
            + timedelta(minutes=settings.jwt_expiry_minutes),
        }
        return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    @staticmethod
    def decode_jwt(token: str) -> dict:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])

    @staticmethod
    def generate_api_key() -> tuple[str, str]:
        raw_key = "wv_live_" + secrets.token_hex(32)
        hashed = hashlib.sha256(raw_key.encode()).hexdigest()
        return raw_key, hashed

    @staticmethod
    def hash_api_key(raw_key: str) -> str:
        return hashlib.sha256(raw_key.encode()).hexdigest()

    @staticmethod
    async def get_user_by_api_key(db: AsyncSession, raw_key: str) -> User | None:
        hashed = AuthService.hash_api_key(raw_key)
        result = await db.execute(select(User).where(User.api_key == hashed))
        return result.scalar_one_or_none()

    @staticmethod
    async def set_user_api_key(db: AsyncSession, user_id, raw_key: str) -> User:
        hashed = AuthService.hash_api_key(raw_key)
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one()
        user.api_key = hashed
        await db.commit()
        await db.refresh(user)
        return user

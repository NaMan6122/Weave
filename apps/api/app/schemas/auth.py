from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RegisterRequest(BaseModel):
    email: str
    name: str | None = None


class LoginRequest(BaseModel):
    email: str


class OAuthCallbackRequest(BaseModel):
    email: str
    name: str | None = None
    avatar_url: str | None = None
    provider: str


class UserResponse(BaseModel):
    id: UUID
    email: str
    name: str | None = None
    avatar_url: str | None = None
    plan: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuthResponse(BaseModel):
    token: str
    user: UserResponse


class ApiKeyResponse(BaseModel):
    key: str
    created_at: datetime


class ApiKeyInfoResponse(BaseModel):
    masked_key: str | None = None
    has_key: bool


class ProfileUpdateRequest(BaseModel):
    name: str


class AccountDeleteRequest(BaseModel):
    email_confirmation: str

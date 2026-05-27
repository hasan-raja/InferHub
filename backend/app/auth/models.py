from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.security import Role


class Principal(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    api_key_id: UUID
    email: str
    role: Role
    key_prefix: str | None = None
    requests_per_minute: int


class ApiKeyCreateRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    role: Role = Role.FREE
    name: str = Field(min_length=1, max_length=80)
    requests_per_minute: int | None = Field(default=None, ge=1, le=100_000)
    tokens_per_day: int = Field(default=100_000, ge=1)


class ApiKeyCreateResponse(BaseModel):
    user_id: UUID
    api_key_id: UUID
    api_key: str
    prefix: str
    role: Role
    requests_per_minute: int


class ApiKeyValidateResponse(BaseModel):
    valid: bool
    user_id: UUID
    api_key_id: UUID
    role: Role
    requests_per_minute: int


class ApiKeyRevokeResponse(BaseModel):
    api_key_id: UUID
    revoked_at: datetime


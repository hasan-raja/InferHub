from uuid import UUID

from pydantic import BaseModel, Field


class ModelRegistryEntry(BaseModel):
    id: UUID
    family: str
    modality: str
    provider: str
    model_name: str
    active: bool
    supports_streaming: bool
    priority: int
    health: str


class ModelRegistryCreateRequest(BaseModel):
    family: str = Field(min_length=1, max_length=80)
    modality: str = Field(min_length=1, max_length=40)
    provider: str = Field(min_length=1, max_length=80)
    model_name: str = Field(min_length=1, max_length=160)
    active: bool = True
    supports_streaming: bool = False
    priority: int = Field(default=100, ge=0, le=1000)
    health: str = Field(default="unknown", pattern="^(healthy|degraded|unhealthy|unknown)$")


class ModelRegistryUpdateRequest(BaseModel):
    active: bool | None = None
    supports_streaming: bool | None = None
    priority: int | None = Field(default=None, ge=0, le=1000)
    health: str | None = Field(default=None, pattern="^(healthy|degraded|unhealthy|unknown)$")


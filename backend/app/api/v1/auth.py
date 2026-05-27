from uuid import UUID

from fastapi import APIRouter, Depends, Request

from app.auth.dependencies import enforce_rate_limit, require_permission
from app.auth.models import (
    ApiKeyCreateRequest,
    ApiKeyCreateResponse,
    ApiKeyRevokeResponse,
    ApiKeyValidateResponse,
    Principal,
)
from app.auth.service import create_api_key, revoke_api_key
from app.core.config import Settings, get_settings

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.post(
    "/api-keys",
    response_model=ApiKeyCreateResponse,
    dependencies=[Depends(require_permission("keys:create"))],
)
async def create_key(
    payload: ApiKeyCreateRequest,
    request: Request,
    settings: Settings = Depends(get_settings),
) -> ApiKeyCreateResponse:
    return await create_api_key(request.app.state.dependencies.postgres, settings, payload)


@router.get("/api-keys/validate", response_model=ApiKeyValidateResponse)
async def validate_key(principal: Principal = Depends(enforce_rate_limit)) -> ApiKeyValidateResponse:
    return ApiKeyValidateResponse(
        valid=True,
        user_id=principal.user_id,
        api_key_id=principal.api_key_id,
        role=principal.role,
        requests_per_minute=principal.requests_per_minute,
    )


@router.delete(
    "/api-keys/{api_key_id}",
    response_model=ApiKeyRevokeResponse,
    dependencies=[Depends(require_permission("keys:revoke"))],
)
async def revoke_key(api_key_id: UUID, request: Request) -> ApiKeyRevokeResponse:
    revoked_at = await revoke_api_key(request.app.state.dependencies.postgres, api_key_id)
    return ApiKeyRevokeResponse(api_key_id=api_key_id, revoked_at=revoked_at)


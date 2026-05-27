from uuid import UUID

from fastapi import APIRouter, Depends, Request

from app.auth.dependencies import enforce_rate_limit, require_permission
from app.models.registry import create_model, list_models, update_model
from app.models.schemas import ModelRegistryCreateRequest, ModelRegistryEntry, ModelRegistryUpdateRequest

router = APIRouter(prefix="/v1/models", tags=["model-registry"])


@router.get("", response_model=list[ModelRegistryEntry])
async def get_models(
    request: Request,
    active_only: bool = True,
    _principal=Depends(enforce_rate_limit),
) -> list[ModelRegistryEntry]:
    return await list_models(request.app.state.dependencies.postgres, active_only=active_only)


@router.post(
    "",
    response_model=ModelRegistryEntry,
    dependencies=[Depends(require_permission("models:write"))],
)
async def register_model(payload: ModelRegistryCreateRequest, request: Request) -> ModelRegistryEntry:
    return await create_model(request.app.state.dependencies.postgres, payload)


@router.patch(
    "/{model_id}",
    response_model=ModelRegistryEntry,
    dependencies=[Depends(require_permission("models:write"))],
)
async def patch_model(
    model_id: UUID,
    payload: ModelRegistryUpdateRequest,
    request: Request,
) -> ModelRegistryEntry:
    return await update_model(request.app.state.dependencies.postgres, model_id, payload)


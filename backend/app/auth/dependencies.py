from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.models import Principal
from app.auth.rate_limit import check_fixed_window_rate_limit
from app.auth.service import validate_api_key
from app.core.config import Settings, get_settings
from app.core.security import Role, role_has_permission

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_principal(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> Principal:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return await validate_api_key(request.app.state.dependencies.postgres, settings, credentials.credentials)


def require_role(*roles: Role) -> Callable[[Principal], Principal]:
    allowed = set(roles)

    async def dependency(principal: Principal = Depends(get_current_principal)) -> Principal:
        if principal.role not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="insufficient role")
        return principal

    return dependency


def require_permission(permission: str) -> Callable[[Principal], Principal]:
    async def dependency(principal: Principal = Depends(get_current_principal)) -> Principal:
        if not role_has_permission(principal.role, permission):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="insufficient permission")
        return principal

    return dependency


async def enforce_rate_limit(
    request: Request,
    response: Response,
    principal: Principal = Depends(get_current_principal),
) -> Principal:
    result = await check_fixed_window_rate_limit(
        request.app.state.dependencies.redis,
        key=str(principal.api_key_id),
        limit=principal.requests_per_minute,
    )
    response.headers["x-ratelimit-limit"] = str(result.limit)
    response.headers["x-ratelimit-remaining"] = str(result.remaining)
    response.headers["x-ratelimit-reset"] = str(result.reset_seconds)
    if not result.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="rate limit exceeded",
            headers={
                "Retry-After": str(result.reset_seconds),
                "x-ratelimit-limit": str(result.limit),
                "x-ratelimit-remaining": str(result.remaining),
                "x-ratelimit-reset": str(result.reset_seconds),
            },
        )
    return principal


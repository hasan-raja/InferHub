from time import perf_counter
from typing import Any

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from app.models.registry import registry_health

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def readiness(request: Request) -> JSONResponse:
    dependencies = request.app.state.dependencies
    checks: dict[str, dict[str, Any]] = {}

    checks["postgres"] = await _check("postgres", _postgres_ping(dependencies.postgres))
    checks["redis"] = await _check("redis", dependencies.redis.ping())
    checks["clickhouse"] = await _check("clickhouse", _clickhouse_ping(dependencies.clickhouse))
    checks["kafka"] = await _check("kafka", _kafka_ping(dependencies.kafka_producer))
    checks["auth"] = await _check("auth", _auth_ping(dependencies.postgres))
    checks["model_registry"] = await _check("model_registry", _model_registry_ping(dependencies.postgres))

    ready = all(check["ok"] for check in checks.values())
    http_status = status.HTTP_200_OK if ready else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse({"status": "ready" if ready else "degraded", "checks": checks}, status_code=http_status)


async def _check(name: str, awaitable: Any) -> dict[str, Any]:
    started = perf_counter()
    try:
        await awaitable
        return {"ok": True, "latency_ms": round((perf_counter() - started) * 1000, 2)}
    except Exception as exc:  # noqa: BLE001 - health should report dependency failures.
        return {
            "ok": False,
            "latency_ms": round((perf_counter() - started) * 1000, 2),
            "error": f"{name}: {exc.__class__.__name__}",
        }


async def _postgres_ping(pool: Any) -> None:
    async with pool.acquire() as conn:
        await conn.fetchval("SELECT 1")


async def _clickhouse_ping(client: Any) -> None:
    client.command("SELECT 1")


async def _kafka_ping(producer: Any) -> None:
    await producer.client.bootstrap()


async def _auth_ping(pool: Any) -> None:
    async with pool.acquire() as conn:
        await conn.fetchval("SELECT count(*) FROM api_keys")


async def _model_registry_ping(pool: Any) -> None:
    health_counts = await registry_health(pool)
    if not health_counts:
        raise RuntimeError("model registry is empty")


@router.get("/health/security")
async def security_health(request: Request) -> dict[str, Any]:
    dependencies = request.app.state.dependencies
    async with dependencies.postgres.acquire() as conn:
        active_keys = await conn.fetchval("SELECT count(*) FROM api_keys WHERE revoked_at IS NULL")
        users = await conn.fetchval("SELECT count(*) FROM users")
    return {
        "status": "ok",
        "auth": {"users": users, "active_api_keys": active_keys},
        "model_registry": await registry_health(dependencies.postgres),
    }

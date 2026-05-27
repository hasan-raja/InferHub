from uuid import UUID

import asyncpg
from fastapi import HTTPException, status

from app.models.schemas import ModelRegistryCreateRequest, ModelRegistryEntry, ModelRegistryUpdateRequest


async def list_models(pool: asyncpg.Pool, *, active_only: bool = True) -> list[ModelRegistryEntry]:
    predicate = "WHERE active = true" if active_only else ""
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            f"""
            SELECT id, family, modality, provider, model_name, active, supports_streaming, priority, health
            FROM model_registry
            {predicate}
            ORDER BY modality, priority ASC, model_name ASC
            """
        )
    return [ModelRegistryEntry(**dict(row)) for row in rows]


async def create_model(pool: asyncpg.Pool, payload: ModelRegistryCreateRequest) -> ModelRegistryEntry:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO model_registry
                (family, modality, provider, model_name, active, supports_streaming, priority, health)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (provider, model_name) DO UPDATE SET
                family = EXCLUDED.family,
                modality = EXCLUDED.modality,
                active = EXCLUDED.active,
                supports_streaming = EXCLUDED.supports_streaming,
                priority = EXCLUDED.priority,
                health = EXCLUDED.health
            RETURNING id, family, modality, provider, model_name, active, supports_streaming, priority, health
            """,
            payload.family,
            payload.modality,
            payload.provider,
            payload.model_name,
            payload.active,
            payload.supports_streaming,
            payload.priority,
            payload.health,
        )
    return ModelRegistryEntry(**dict(row))


async def update_model(pool: asyncpg.Pool, model_id: UUID, payload: ModelRegistryUpdateRequest) -> ModelRegistryEntry:
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="no fields to update")

    allowed_columns = {
        "active": "active",
        "supports_streaming": "supports_streaming",
        "priority": "priority",
        "health": "health",
    }
    assignments = []
    values = []
    for index, (field, value) in enumerate(updates.items(), start=2):
        assignments.append(f"{allowed_columns[field]} = ${index}")
        values.append(value)

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            f"""
            UPDATE model_registry
            SET {", ".join(assignments)}
            WHERE id = $1
            RETURNING id, family, modality, provider, model_name, active, supports_streaming, priority, health
            """,
            model_id,
            *values,
        )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="model not found")
    return ModelRegistryEntry(**dict(row))


async def registry_health(pool: asyncpg.Pool) -> dict[str, int]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT health, count(*) AS count
            FROM model_registry
            GROUP BY health
            """
        )
    return {row["health"]: row["count"] for row in rows}


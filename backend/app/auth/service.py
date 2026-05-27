from datetime import datetime, timezone
from uuid import UUID

import asyncpg
from fastapi import HTTPException, status

from app.auth.models import ApiKeyCreateRequest, ApiKeyCreateResponse, Principal
from app.core.config import Settings
from app.core.security import Role, default_rpm_for_role, generate_api_key, hash_api_key


async def create_api_key(
    pool: asyncpg.Pool,
    settings: Settings,
    payload: ApiKeyCreateRequest,
) -> ApiKeyCreateResponse:
    generated = generate_api_key(settings)
    rpm = payload.requests_per_minute or default_rpm_for_role(payload.role, settings)
    async with pool.acquire() as conn:
        async with conn.transaction():
            user = await conn.fetchrow(
                """
                INSERT INTO users (email, role)
                VALUES ($1, $2)
                ON CONFLICT (email) DO UPDATE SET role = EXCLUDED.role
                RETURNING id
                """,
                payload.email.lower(),
                payload.role.value,
            )
            quota = await conn.fetchrow("SELECT id FROM quotas WHERE user_id = $1", user["id"])
            if quota:
                await conn.execute(
                    """
                    UPDATE quotas
                    SET requests_per_minute = $1, tokens_per_day = $2
                    WHERE user_id = $3
                    """,
                    rpm,
                    payload.tokens_per_day,
                    user["id"],
                )
            else:
                await conn.execute(
                    """
                    INSERT INTO quotas (user_id, requests_per_minute, tokens_per_day)
                    VALUES ($1, $2, $3)
                    """,
                    user["id"],
                    rpm,
                    payload.tokens_per_day,
                )

            api_key = await conn.fetchrow(
                """
                INSERT INTO api_keys (user_id, key_hash, key_prefix, name)
                VALUES ($1, $2, $3, $4)
                RETURNING id
                """,
                user["id"],
                generated.key_hash,
                generated.prefix,
                payload.name,
            )

    return ApiKeyCreateResponse(
        user_id=user["id"],
        api_key_id=api_key["id"],
        api_key=generated.raw_key,
        prefix=generated.prefix,
        role=payload.role,
        requests_per_minute=rpm,
    )


async def validate_api_key(pool: asyncpg.Pool, settings: Settings, raw_key: str) -> Principal:
    if not raw_key.startswith("ih_"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid api key")

    key_hash = hash_api_key(raw_key, settings)
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                u.id AS user_id,
                u.email,
                u.role,
                k.id AS api_key_id,
                k.key_prefix,
                q.requests_per_minute
            FROM api_keys k
            JOIN users u ON u.id = k.user_id
            LEFT JOIN quotas q ON q.user_id = u.id
            WHERE k.key_hash = $1
              AND k.revoked_at IS NULL
            """,
            key_hash,
        )
        if not row:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid api key")

        await conn.execute("UPDATE api_keys SET last_used_at = now() WHERE id = $1", row["api_key_id"])

    role = Role(row["role"])
    return Principal(
        user_id=row["user_id"],
        api_key_id=row["api_key_id"],
        email=row["email"],
        role=role,
        key_prefix=row["key_prefix"],
        requests_per_minute=row["requests_per_minute"] or default_rpm_for_role(role, settings),
    )


async def revoke_api_key(pool: asyncpg.Pool, api_key_id: UUID) -> datetime:
    revoked_at = datetime.now(timezone.utc)
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE api_keys
            SET revoked_at = $1
            WHERE id = $2 AND revoked_at IS NULL
            RETURNING id
            """,
            revoked_at,
            api_key_id,
        )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="api key not found")
    return revoked_at


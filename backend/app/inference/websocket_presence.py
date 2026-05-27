from uuid import uuid4

from redis.asyncio import Redis


async def mark_connected(
    redis: Redis,
    *,
    modality: str,
    user_id: str,
    ttl_seconds: int,
) -> str:
    connection_id = str(uuid4())
    key = f"ws:{modality}:{connection_id}"
    await redis.hset(
        key,
        mapping={
            "connection_id": connection_id,
            "modality": modality,
            "user_id": user_id,
        },
    )
    await redis.expire(key, ttl_seconds)
    await redis.sadd(f"ws:{modality}:active", connection_id)
    return connection_id


async def refresh(redis: Redis, *, modality: str, connection_id: str, ttl_seconds: int) -> None:
    await redis.expire(f"ws:{modality}:{connection_id}", ttl_seconds)


async def mark_disconnected(redis: Redis, *, modality: str, connection_id: str) -> None:
    await redis.delete(f"ws:{modality}:{connection_id}")
    await redis.srem(f"ws:{modality}:active", connection_id)


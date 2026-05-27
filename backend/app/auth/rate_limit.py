from dataclasses import dataclass
from time import time

from redis.asyncio import Redis


@dataclass(frozen=True, slots=True)
class RateLimitResult:
    allowed: bool
    limit: int
    remaining: int
    reset_seconds: int


async def check_fixed_window_rate_limit(redis: Redis, *, key: str, limit: int, window_seconds: int = 60) -> RateLimitResult:
    window = int(time() // window_seconds)
    redis_key = f"rl:{key}:{window}"
    current = await redis.incr(redis_key)
    if current == 1:
        await redis.expire(redis_key, window_seconds + 2)

    reset_seconds = window_seconds - int(time() % window_seconds)
    remaining = max(limit - current, 0)
    return RateLimitResult(
        allowed=current <= limit,
        limit=limit,
        remaining=remaining,
        reset_seconds=reset_seconds,
    )


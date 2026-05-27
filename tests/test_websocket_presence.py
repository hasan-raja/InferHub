import pytest

from app.inference.websocket_presence import mark_connected, mark_disconnected, refresh


class FakeRedis:
    def __init__(self):
        self.hashes = {}
        self.expirations = {}
        self.sets = {}

    async def hset(self, key, mapping):
        self.hashes[key] = mapping

    async def expire(self, key, seconds):
        self.expirations[key] = seconds

    async def sadd(self, key, value):
        self.sets.setdefault(key, set()).add(value)

    async def delete(self, key):
        self.hashes.pop(key, None)

    async def srem(self, key, value):
        self.sets.setdefault(key, set()).discard(value)


@pytest.mark.asyncio
async def test_websocket_presence_lifecycle():
    redis = FakeRedis()

    connection_id = await mark_connected(redis, modality="llm", user_id="user-1", ttl_seconds=45)
    await refresh(redis, modality="llm", connection_id=connection_id, ttl_seconds=45)
    await mark_disconnected(redis, modality="llm", connection_id=connection_id)

    assert f"ws:llm:{connection_id}" not in redis.hashes
    assert connection_id not in redis.sets["ws:llm:active"]

import pytest

from app.auth.rate_limit import check_fixed_window_rate_limit


class FakeRedis:
    def __init__(self):
        self.values = {}
        self.expirations = {}

    async def incr(self, key):
        self.values[key] = self.values.get(key, 0) + 1
        return self.values[key]

    async def expire(self, key, seconds):
        self.expirations[key] = seconds


@pytest.mark.asyncio
async def test_fixed_window_rate_limit_allows_until_limit():
    redis = FakeRedis()

    first = await check_fixed_window_rate_limit(redis, key="key-1", limit=2)
    second = await check_fixed_window_rate_limit(redis, key="key-1", limit=2)
    third = await check_fixed_window_rate_limit(redis, key="key-1", limit=2)

    assert first.allowed is True
    assert first.remaining == 1
    assert second.allowed is True
    assert second.remaining == 0
    assert third.allowed is False
    assert third.remaining == 0

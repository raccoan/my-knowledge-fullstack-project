from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock

import fakeredis
import pytest
from limits.storage import RedisStorage
from redis.exceptions import ConnectionError

from config.rate_limit import RateLimitSettings
from services.rate_limit import AiRateLimiter, RateLimitRejected, RateLimitUnavailable


def make_limiter(server=None, **options):
    settings = RateLimitSettings(_env_file=None, **options)
    client = fakeredis.FakeRedis(server=server)
    storage = RedisStorage("redis://localhost", connection_pool=client.connection_pool)
    return AiRateLimiter(settings, storage)


def test_users_and_scopes_have_separate_budgets():
    limiter = make_limiter(chat_requests=1, interview_requests=1)
    limiter.check(1, "chat")
    limiter.check(2, "chat")
    limiter.check(1, "interview")
    with pytest.raises(RateLimitRejected) as failure:
        limiter.check(1, "chat")
    assert 1 <= failure.value.retry_after <= 60
    limiter.close()


def test_atomic_admission_across_workers():
    # 两个独立连接池共享 Redis；实际执行 limits 的 Lua 脚本，而非 mock 准入算法。
    server = fakeredis.FakeServer()
    limiters = [make_limiter(server, chat_requests=5) for _ in range(2)]

    def attempt(index):
        try:
            limiters[index % 2].check(7, "chat")
            return True
        except RateLimitRejected:
            return False

    with ThreadPoolExecutor(max_workers=12) as pool:
        assert sum(pool.map(attempt, range(40))) == 5
    for limiter in limiters:
        limiter.close()


def test_window_releases_old_requests(monkeypatch):
    # 推进库和服务共用的时钟，无需等待真实一分钟。
    import time
    start = time.time()
    monkeypatch.setattr(time, "time", lambda: start)
    limiter = make_limiter(chat_requests=1, window_seconds=2)
    limiter.check(1, "chat")
    with pytest.raises(RateLimitRejected):
        limiter.check(1, "chat")
    monkeypatch.setattr(time, "time", lambda: start + 3)
    limiter.check(1, "chat")
    limiter.close()


def test_storage_outage_fails_closed():
    storage = Mock(spec=RedisStorage)
    storage.acquire_entry.side_effect = ConnectionError("unavailable")
    limiter = AiRateLimiter(RateLimitSettings(_env_file=None), storage)
    with pytest.raises(RateLimitUnavailable):
        limiter.check(1, "chat")


def test_disabled_does_not_connect():
    limiter = AiRateLimiter(RateLimitSettings(_env_file=None, enabled=False))
    limiter.check(1, "chat")
    assert limiter.storage is None
    limiter.close()

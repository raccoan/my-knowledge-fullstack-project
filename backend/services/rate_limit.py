import math
import time
from typing import Literal

from limits import RateLimitItemPerSecond
from limits.storage import RedisStorage
from limits.strategies import MovingWindowRateLimiter
from redis.backoff import NoBackoff
from redis.exceptions import RedisError
from redis.retry import Retry

from config.rate_limit import RateLimitSettings

RateLimitScope = Literal["chat", "interview"]


class RateLimitRejected(Exception):
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__("Rate limit exceeded")


class RateLimitUnavailable(Exception):
    """共享存储故障时拒绝新的模型调用，不静默退化到单进程计数。"""


class AiRateLimiter:
    def __init__(self, settings: RateLimitSettings, storage: RedisStorage | None = None):
        self.settings = settings
        self.storage = None
        self.strategy = None
        if settings.enabled:
            self.storage = storage or RedisStorage(
                settings.redis_url.get_secret_value(),
                socket_connect_timeout=settings.redis_timeout_seconds,
                socket_timeout=settings.redis_timeout_seconds,
                retry=Retry(NoBackoff(), 0),
            )
            # 复用 limits 内置的 Redis Lua 准入脚本，计数与过期原子执行。
            self.strategy = MovingWindowRateLimiter(self.storage)
        self.rules = {
            "chat": RateLimitItemPerSecond(settings.chat_requests, settings.window_seconds, namespace=settings.namespace),
            "interview": RateLimitItemPerSecond(settings.interview_requests, settings.window_seconds, namespace=settings.namespace),
        }

    def check(self, user_id: int, scope: RateLimitScope) -> None:
        if self.strategy is None:
            return
        rule = self.rules[scope]
        identifiers = (scope, str(user_id))
        try:
            if self.strategy.hit(rule, *identifiers):
                return
            stats = self.strategy.get_window_stats(rule, *identifiers)
        except RedisError as error:
            raise RateLimitUnavailable() from error
        # 使用库返回的窗口时间，向上取整，避免客户端在边界前反复重试。
        retry_after = max(1, min(self.settings.window_seconds, math.ceil(stats.reset_time - time.time())))
        raise RateLimitRejected(retry_after)

    def close(self) -> None:
        if self.storage is not None:
            self.storage.storage.close()
            self.storage.storage.connection_pool.disconnect()

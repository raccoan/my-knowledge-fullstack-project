import logging
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request

from config.rate_limit import RateLimitSettings
from services.rate_limit import AiRateLimiter, RateLimitRejected, RateLimitScope, RateLimitUnavailable
from utils.auth import get_current_user

logger = logging.getLogger(__name__)


@asynccontextmanager
async def rate_limit_lifespan(app: FastAPI):
    limiter = AiRateLimiter(RateLimitSettings())
    app.state.ai_rate_limiter = limiter
    try:
        yield
    finally:
        limiter.close()


def get_rate_limiter(request: Request) -> AiRateLimiter:
    return request.app.state.ai_rate_limiter


def require_ai_rate_limit(scope: RateLimitScope):
    """认证后按用户和业务范围准入；依赖在路由消息写入和模型调用前执行。"""
    def dependency(
        current_user: Annotated[dict, Depends(get_current_user)],
        limiter: Annotated[AiRateLimiter, Depends(get_rate_limiter)],
    ) -> None:
        try:
            limiter.check(current_user["id"], scope)
        except RateLimitRejected as error:
            raise HTTPException(
                status_code=429,
                detail={
                    "code": "rate_limit_exceeded",
                    "message": "请求过于频繁，请稍后再试",
                    "retry_after": error.retry_after,
                    "scope": scope,
                },
                headers={"Retry-After": str(error.retry_after)},
            ) from error
        except RateLimitUnavailable as error:
            # 不记录 Redis URL、Token、用户输入或原始异常中的连接信息。
            logger.warning("AI rate limiter storage unavailable (%s)", type(error.__cause__).__name__)
            retry_after = limiter.settings.unavailable_retry_seconds
            raise HTTPException(
                status_code=503,
                detail={
                    "code": "rate_limit_unavailable",
                    "message": "AI 服务暂时不可用，请稍后重试",
                    "retry_after": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            ) from error

    return dependency


# 同一用户的普通/流式问答共享配额，创建面试/回答评价共享另一配额，防止换入口绕过。
limit_chat = require_ai_rate_limit("chat")
limit_interview = require_ai_rate_limit("interview")

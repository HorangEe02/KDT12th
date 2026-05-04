"""
Rate limiting helper (#5).

slowapi 기반. 설치되지 않은 환경에서도 서비스가 죽지 않도록 graceful fallback:
- slowapi 설치됨 → 실제 rate limit 적용
- 미설치 → noop 데코레이터 (경고 로그만 출력)

사용 예:
    from nlp_mvp.api.rate_limit import limiter, rate_limit

    @router.post("/chat")
    @rate_limit("5/minute")
    async def chat(request: Request, ...): ...

주의: slowapi 를 쓰려면 엔드포인트 시그니처에 `request: Request` 가 필요하다.
"""
from __future__ import annotations

import os
from typing import Callable

from nlp_mvp.shared.logger import get_logger

logger = get_logger(__name__)

try:
    from slowapi import Limiter
    from slowapi.errors import RateLimitExceeded
    from slowapi.util import get_remote_address

    _SLOWAPI_AVAILABLE = True
except ImportError:  # pragma: no cover
    _SLOWAPI_AVAILABLE = False
    Limiter = None  # type: ignore
    RateLimitExceeded = Exception  # type: ignore
    get_remote_address = None  # type: ignore
    logger.warning("slowapi not installed — rate limiting disabled")


# env 로 전체 비활성화 가능 (테스트 편의)
_RATE_LIMIT_ENABLED = os.getenv("NLP_RATE_LIMIT_ENABLED", "1") != "0"


if _SLOWAPI_AVAILABLE and _RATE_LIMIT_ENABLED:
    limiter = Limiter(
        key_func=get_remote_address,  # type: ignore[arg-type]
        default_limits=["60/minute"],  # 기본값: 분당 60회
        storage_uri="memory://",
    )

    def rate_limit(limit_string: str) -> Callable:
        """`@rate_limit("5/minute")` 형태로 라우트에 적용."""
        return limiter.limit(limit_string)

else:
    limiter = None  # type: ignore

    def rate_limit(limit_string: str) -> Callable:
        def decorator(func: Callable) -> Callable:
            return func
        return decorator


def install_rate_limit_handler(app) -> None:
    """FastAPI app 에 429 핸들러 등록. main.py lifespan 진입 전에 호출."""
    if not _SLOWAPI_AVAILABLE or limiter is None:
        return
    from slowapi.middleware import SlowAPIMiddleware

    app.state.limiter = limiter

    async def _rate_limit_exceeded_handler(request, exc):  # type: ignore[no-untyped-def]
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=429,
            content={
                "code": "rate_limited",
                "message": f"Too many requests: {exc.detail}",
            },
            headers={"Retry-After": "60"},
        )

    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
    logger.info("slowapi rate limiting installed")

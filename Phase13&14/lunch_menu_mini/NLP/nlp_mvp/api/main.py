"""
Mini NLP FastAPI 서버.

포트 8001 에서 구동되는 NLP 전용 마이크로서비스. lunch-optimizer(8000) 와 공용
Mini SQLite DB 를 읽고, 감성 컬럼·정규화 로그 등 보정 컬럼을 기록한다.

기동
----
    cd Mini
    uvicorn nlp_mvp.api.main:app --reload --port 8001

엔드포인트
----------
- GET  /nlp/health
- GET  /nlp/sentiment/top
- GET  /nlp/sentiment/{restaurant_id}
- POST /nlp/sentiment/refresh
- POST /nlp/menu/normalize
- POST /nlp/nutrition/parse
- GET  /nlp/menu/stats
- POST /nlp/chatbot/chat
- POST /nlp/chatbot/reset
- GET  /nlp/chatbot/stats
- GET  /nlp/reports/weekly/{user_id}
- POST /nlp/reports/weekly/{user_id}/regenerate
"""
from __future__ import annotations

import os
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from nlp_mvp.api.rate_limit import install_rate_limit_handler
from nlp_mvp.api.schemas import HealthOut
from nlp_mvp.shared.logger import get_logger

logger = get_logger("nlp_mvp.api")


# =============================================================================
# 모듈 준비 상태 추적
# =============================================================================
_MODULE_STATUS: dict[str, str] = {
    "db": "pending",
    "menu_normalizer": "pending",
    "rag_chatbot_index": "pending",
    "nlg_generator": "pending",
    "scoring_patch_ab": "pending",
}


def _init_db() -> None:
    try:
        from nlp_mvp.shared.db import get_engine
        get_engine()  # side-effect: create engine
        _MODULE_STATUS["db"] = "ok"
    except Exception as e:
        _MODULE_STATUS["db"] = f"error: {e}"
        logger.warning(f"db init failed: {e}")


def _init_menu_normalizer() -> None:
    try:
        from nlp_mvp.api.routers import menu as menu_router
        from nlp_mvp.api.routers import nutrition as nutrition_router
        from nlp_mvp.menu_normalizer.normalizer import MenuNormalizer
        # 임베딩은 첫 요청 시에만 lazy — 여기서는 규칙+레벤슈타인만 준비
        normalizer = MenuNormalizer(enable_embedding=False)
        menu_router.set_normalizer(normalizer)
        nutrition_router.set_normalizer(normalizer)
        _MODULE_STATUS["menu_normalizer"] = "ok"
    except Exception as e:
        _MODULE_STATUS["menu_normalizer"] = f"error: {e}"
        logger.warning(f"MenuNormalizer init failed: {e}")


def _init_rag_index() -> None:
    """chroma_store 가 비어 있으면 자동 인덱싱 (선택적)."""
    if os.getenv("NLP_SKIP_RAG_INDEX", "0") == "1":
        _MODULE_STATUS["rag_chatbot_index"] = "skipped"
        return
    try:
        from nlp_mvp.rag_chatbot.indexer import ChromaDBIndexer
        indexer = ChromaDBIndexer()
        # 각 컬렉션이 비었는지 체크 후 한 번만 빌드
        try:
            coll = indexer.client.get_or_create_collection("restaurants")
            if coll.count() == 0:
                logger.info("chroma_store empty — building all collections")
                indexer.build_all()
        except Exception as e:
            logger.warning(f"chroma auto-build skipped: {e}")
        _MODULE_STATUS["rag_chatbot_index"] = "ok"
    except Exception as e:
        _MODULE_STATUS["rag_chatbot_index"] = f"error: {e}"
        logger.warning(f"RAG index init failed: {e}")


def _init_nlg_generator() -> None:
    """ReportGenerator 싱글톤 생성은 첫 호출 시에 맡기고, 스키마만 준비."""
    try:
        from nlp_mvp.nlg_report.generator import ensure_schema
        ensure_schema()
        _MODULE_STATUS["nlg_generator"] = "ok"
    except Exception as e:
        _MODULE_STATUS["nlg_generator"] = f"error: {e}"
        logger.warning(f"nlg ensure_schema failed: {e}")


def _init_scoring_patch() -> None:
    try:
        from nlp_mvp.integration.scoring_patch_ab import ensure_schema
        ensure_schema()
        _MODULE_STATUS["scoring_patch_ab"] = "ok"
    except Exception as e:
        _MODULE_STATUS["scoring_patch_ab"] = f"error: {e}"
        logger.warning(f"scoring_patch_ab ensure_schema failed: {e}")


# =============================================================================
# Lifespan
# =============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("NLP API starting — initializing modules")
    _init_db()
    _init_menu_normalizer()
    _init_nlg_generator()
    _init_scoring_patch()
    _init_rag_index()
    logger.info(f"Module status: {_MODULE_STATUS}")
    yield
    logger.info("NLP API shutting down")


# =============================================================================
# App
# =============================================================================
app = FastAPI(
    title="Mini NLP API",
    description="감성 / 메뉴 정규화 / RAG 챗봇 / NLG 리포트 통합 서비스",
    version="0.5.0",
    lifespan=lifespan,
)

# CORS — Vite dev server (5173), CRA (3000), 기본 로컬 허용
_DEFAULT_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:3002",
    "http://127.0.0.1:5173",
]
_extra = os.getenv("NLP_API_CORS_ORIGINS", "")
if _extra:
    _DEFAULT_ORIGINS.extend([o.strip() for o in _extra.split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=_DEFAULT_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],  # #7
    allow_headers=["Content-Type", "Authorization", "X-Admin-Token"],   # #7
)

# #5 Rate limiting (slowapi) — gracefully no-op if slowapi not installed
install_rate_limit_handler(app)


# #8 Security headers middleware
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    # HSTS는 HTTPS 환경에서만 의미있음 — nginx 리버스 프록시 쪽에서 관리 권장
    if os.getenv("NLP_ENABLE_HSTS", "0") == "1":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# =============================================================================
# 로깅 미들웨어
# =============================================================================
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    try:
        response = await call_next(request)
    except Exception as e:
        elapsed = int((time.time() - start) * 1000)
        logger.exception(f"{request.method} {request.url.path} -> 500 ({elapsed}ms)")
        return JSONResponse(
            status_code=500,
            content={"code": "internal_error", "message": str(e)},
        )
    elapsed = int((time.time() - start) * 1000)
    logger.info(
        f"{request.method} {request.url.path} -> {response.status_code} ({elapsed}ms)"
    )
    return response


# =============================================================================
# Health
# =============================================================================
@app.get("/nlp/health", response_model=HealthOut, tags=["meta"])
def health() -> HealthOut:
    degraded = any(v.startswith("error") for v in _MODULE_STATUS.values())
    return HealthOut(
        status="degraded" if degraded else "ok",
        version="0.5.0",
        modules=dict(_MODULE_STATUS),
    )


# =============================================================================
# Routers
# =============================================================================
from nlp_mvp.api.routers import chatbot as chatbot_router  # noqa: E402
from nlp_mvp.api.routers import menu as menu_router  # noqa: E402
from nlp_mvp.api.routers import nutrition as nutrition_router  # noqa: E402
from nlp_mvp.api.routers import reports as reports_router  # noqa: E402
from nlp_mvp.api.routers import sentiment as sentiment_router  # noqa: E402
from nlp_mvp.api.routers import settings as settings_router  # noqa: E402

app.include_router(sentiment_router.router)
app.include_router(menu_router.router)
app.include_router(nutrition_router.router)
app.include_router(chatbot_router.router)
app.include_router(reports_router.router)
app.include_router(settings_router.router)

# Phase 6 research v2 (A2 / B2 / E1) — optional, gracefully skipped if
# nlp_research package isn't on PYTHONPATH.
try:
    from nlp_mvp.api.routers import v2 as v2_router  # noqa: E402
    app.include_router(v2_router.router)
    _MODULE_STATUS["research_v2"] = "ok"
except Exception as _e:  # pragma: no cover
    _MODULE_STATUS["research_v2"] = f"error: {_e}"


# =============================================================================
# Entrypoint
# =============================================================================
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("NLP_API_PORT", "8001"))
    uvicorn.run("nlp_mvp.api.main:app", host="0.0.0.0", port=port, reload=True)

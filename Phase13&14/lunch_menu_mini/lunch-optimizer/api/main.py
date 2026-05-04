"""
Mini lunch-optimizer FastAPI 서버.

GUIDE Subtopic 1 §8 의 5개 엔드포인트를 구현.

Run:
    uvicorn api.main:app --reload --port 8000
"""
from __future__ import annotations

import logging
import json
from contextlib import asynccontextmanager
from datetime import date, datetime
from typing import Any, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from config.settings import settings
from database.connection import get_session, init_schema
from engine.recommender import LunchRecommender
from pipeline.collectors.nutrition_collector import NutritionCollector
from pipeline.collectors.vote_collector import VoteError, VoteManager
from pipeline.loaders.db_loader import (
    NutritionLoader, RestaurantLoader, WeatherLoader
)
from pipeline.scheduler import RestaurantPipeline, WeatherPipeline
from pipeline.transformers.nutrition_scorer import (
    MealTracker, MenuNutritionMapper, NutritionDiagnostic,
    NutritionRecommendScorer,
)
from pipeline.transformers.team_scorer import TeamPreferenceAnalyzer
from pipeline.transformers.visit_tracker import VisitTracker
from pipeline.transformers.weather_scorer import WeatherMenuScorer
from api.location_cache import location_cache

logger = logging.getLogger(__name__)


# =============================================================================
# Lifespan
# =============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작 시 스키마 초기화."""
    logger.info("FastAPI starting — initializing DB schema")
    init_schema()
    yield
    logger.info("FastAPI shutting down")


# =============================================================================
# App
# =============================================================================
app = FastAPI(
    title="Mini Lunch Optimizer API",
    description="직장인 점심 최적화 파이프라인 — 음식점 데이터 API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],  # #7
    allow_headers=["Content-Type", "Authorization"],                     # #7
)


# #8 Security headers middleware
@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    import os as _os
    if _os.getenv("LUNCH_ENABLE_HSTS", "0") == "1":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# =============================================================================
# Phase 13&14: 인증/관리자 라우터
# =============================================================================
# 라우터 import 는 모듈 import 시 DB 메타데이터에 의존하므로
# 이 위치에 두어야 init_schema 이후 마이그레이션 영향 받지 않음.
try:
    from api.routers.auth import router as auth_router
    from api.routers.admin import router as admin_router
    app.include_router(auth_router)
    app.include_router(admin_router)
    logger.info("Auth + Admin 라우터 등록 완료")
except ImportError as e:
    logger.warning("Auth 라우터 미등록 (의존성 누락): %s", e)


# =============================================================================
# Pydantic 스키마
# =============================================================================
class RestaurantOut(BaseModel):
    id: str
    name: str
    category: Optional[str] = None
    sub_category: Optional[str] = None
    menu_type: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    lat: float
    lng: float
    distance_m: int
    distance_score: int
    place_url: Optional[str] = None
    indoor: bool = True
    rating: Optional[float] = None
    visit_count: int = 0
    is_active: bool = True
    # 영업 시간대 (헤비 옵션 / 다중 식사 시간) — 기본 True (영업)
    serves_breakfast: bool = True
    serves_lunch: bool = True
    serves_dinner: bool = True


class StatsOut(BaseModel):
    total: int
    active: int
    inactive: int
    categories: dict[str, int]
    avg_distance_m: Optional[float] = None
    avg_distance_score: Optional[float] = None
    last_collected_at: Optional[str] = None


class HealthOut(BaseModel):
    status: str = Field(default="ok")
    db_connected: bool
    last_collected_at: Optional[str] = None
    total_restaurants: int = 0


class PipelineRunOut(BaseModel):
    success: bool
    duration_sec: float
    raw_count: int
    transformed_count: int
    inserted: int
    updated: int
    skipped: int
    deactivated: int
    error: Optional[str] = None


# --- Weather (Subtopic 2) ---
class WeatherCurrentOut(BaseModel):
    collected_at: Optional[str] = None
    temp: Optional[float] = None
    humidity: Optional[int] = None
    rain_type: Optional[int] = None
    rain_type_str: Optional[str] = None
    rain_1h: Optional[float] = None
    wind_speed: Optional[float] = None
    sky: Optional[int] = None
    sky_str: Optional[str] = None
    pop: Optional[int] = None
    tmn: Optional[float] = None
    tmx: Optional[float] = None
    pm10: Optional[int] = None
    pm25: Optional[int] = None
    dust_grade: Optional[str] = None
    outdoor_comfort: Optional[str] = None
    tips: list[str] = Field(default_factory=list)


class WeatherHistoryItem(BaseModel):
    id: int
    collected_at: str
    temp: Optional[float] = None
    sky_str: Optional[str] = None
    pop: Optional[int] = None
    dust_grade: Optional[str] = None
    outdoor_comfort: Optional[str] = None


class MenuRankingItem(BaseModel):
    menu_type: str
    avg_score: int
    reason: Optional[str] = None


class WeatherRankedRestaurantOut(RestaurantOut):
    weather_score: int


class WeatherRefreshOut(BaseModel):
    success: bool
    duration_sec: float
    log_id: Optional[int] = None
    error: Optional[str] = None


# --- Nutrition (Subtopic 3) ---
class NutritionInfoOut(BaseModel):
    id: Optional[int] = None
    restaurant_id: str
    food_name: str
    food_code: Optional[str] = None
    match_type: str
    match_score: Optional[float] = None
    serving_size: float
    calories: Optional[float] = None
    carbs: Optional[float] = None
    protein: Optional[float] = None
    fat: Optional[float] = None
    sugar: Optional[float] = None
    sodium: Optional[float] = None


class MealRecordIn(BaseModel):
    user_id: str
    restaurant_id: str
    menu_name: Optional[str] = None
    meal_date: Optional[str] = None  # ISO date
    satisfaction: Optional[int] = Field(None, ge=1, le=5)


class MealRecordOut(BaseModel):
    id: int
    user_id: str
    restaurant_id: Optional[str] = None
    menu_name: Optional[str] = None
    meal_date: str
    calories: Optional[float] = None
    carbs: Optional[float] = None
    protein: Optional[float] = None
    fat: Optional[float] = None
    sodium: Optional[float] = None
    satisfaction: Optional[int] = None


class RestaurantSnapshotIn(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    category: Optional[str] = None
    address: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    place_url: Optional[str] = None


class NaturalMealItemIn(BaseModel):
    raw_name: str = Field(min_length=1, max_length=100)
    normalized_name: Optional[str] = Field(default=None, max_length=100)
    food_code: Optional[str] = Field(default=None, max_length=50)
    quantity: float = Field(default=1.0, gt=0, le=20)
    unit: str = Field(default="serving", max_length=20)
    serving_size: Optional[float] = Field(default=None, ge=0)
    calories: Optional[float] = Field(default=None, ge=0)
    carbs: Optional[float] = Field(default=None, ge=0)
    protein: Optional[float] = Field(default=None, ge=0)
    fat: Optional[float] = Field(default=None, ge=0)
    sugar: Optional[float] = Field(default=None, ge=0)
    sodium: Optional[float] = Field(default=None, ge=0)
    source: Optional[str] = Field(default=None, max_length=50)
    match_type: Optional[str] = Field(default=None, max_length=30)
    match_confidence: Optional[float] = Field(default=None, ge=0, le=1)
    needs_review: bool = True


class NaturalMealRecordIn(BaseModel):
    user_id: str = Field(min_length=1, max_length=50)
    raw_text: str = Field(min_length=1, max_length=1000)
    meal_date: Optional[str] = None
    meal_type: Optional[str] = Field(default=None, max_length=20)
    restaurant_id: Optional[str] = Field(default=None, max_length=64)
    restaurant_snapshot: Optional[RestaurantSnapshotIn] = None
    satisfaction: Optional[int] = Field(None, ge=1, le=5)
    items: list[NaturalMealItemIn] = Field(min_length=1, max_length=20)


class NaturalMealItemOut(BaseModel):
    id: Optional[int] = None
    raw_name: str
    normalized_name: Optional[str] = None
    food_code: Optional[str] = None
    quantity: float
    unit: str
    serving_size: Optional[float] = None
    calories: Optional[float] = None
    carbs: Optional[float] = None
    protein: Optional[float] = None
    fat: Optional[float] = None
    sugar: Optional[float] = None
    sodium: Optional[float] = None
    source: str
    match_type: str
    match_confidence: Optional[float] = None
    needs_review: bool


class NaturalMealAnalysisOut(BaseModel):
    id: Optional[int] = None
    user_id: str
    raw_text: str
    meal_date: str
    meal_type: Optional[str] = None
    restaurant_id: Optional[str] = None
    restaurant_name_snapshot: Optional[str] = None
    restaurant_place_url: Optional[str] = None
    menu_name: Optional[str] = None
    calories: Optional[float] = None
    carbs: Optional[float] = None
    protein: Optional[float] = None
    fat: Optional[float] = None
    sugar: Optional[float] = None
    sodium: Optional[float] = None
    satisfaction: Optional[int] = None
    nutrition_source: Optional[str] = None
    match_confidence: Optional[float] = None
    needs_review: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    items: list[NaturalMealItemOut] = Field(default_factory=list)


class DeleteMealOut(BaseModel):
    deleted: bool
    meal_id: int


class WeeklySummaryOut(BaseModel):
    period: dict
    meal_count: int
    daily_records: list[dict]
    weekly_avg: dict
    weekly_total: dict
    macro_ratio: dict = Field(default_factory=dict)
    recorded_days: int
    missing_days: list[str]
    # 다중 식사 시간 — 아침/점심/저녁/unknown 별 합계
    by_meal_type: dict = Field(default_factory=dict)


class DiagnosisOut(BaseModel):
    overall_status: str
    overall_score: int
    nutrient_status: dict
    macro_balance: dict
    recommendations: list[str]
    data_warning: Optional[str] = None
    diagnosed_at: str


class NutrientTrendItem(BaseModel):
    date: str
    calories: float
    carbs: float
    protein: float
    fat: float
    sodium: float
    has_record: bool


class NutritionRankedRestaurantOut(RestaurantOut):
    nutrition_score: int
    nutrition_advice: Optional[str] = None


# --- Vote (Subtopic 4) ---
class VoteSessionIn(BaseModel):
    team_id: str
    vote_date: Optional[str] = None  # ISO


class VoteSessionOut(BaseModel):
    id: int
    vote_date: str
    team_id: str
    status: str
    total_votes: int
    winner_restaurant_id: Optional[str] = None


class VoteCastIn(BaseModel):
    user_id: str
    restaurant_id: str
    vote_date: Optional[str] = None
    admin_override: bool = False


class VoteCastOut(BaseModel):
    status: str   # "created" | "updated"
    vote_id: int
    restaurant_id: str
    warning: Optional[str] = None


class VetoIn(BaseModel):
    user_id: str
    restaurant_id: str
    reason: Optional[str] = None
    veto_date: Optional[str] = None


class VetoOut(BaseModel):
    id: int
    veto_date: str
    user_id: str
    restaurant_id: str
    reason: Optional[str] = None


class VoteStatusOut(BaseModel):
    vote_date: str
    status: str
    team_members: int
    voted_count: int
    participation_rate: float
    votes: list[dict]
    not_voted: list[str]
    vetoed: list[dict]
    tally: list[dict]


class VoteCloseIn(BaseModel):
    team_id: str
    vote_date: Optional[str] = None


class VoteCloseOut(BaseModel):
    winner: dict
    total_votes: int
    participation_rate: float
    finalized_at: Optional[str] = None
    warning: Optional[str] = None


# --- History & Preference ---
class RecentVisitItem(BaseModel):
    date: str
    restaurant_id: str
    restaurant_name: str
    participants: int
    satisfaction: Optional[float] = None


class PreferenceOut(BaseModel):
    favorite_categories: list[dict]
    favorite_restaurants: list[dict]
    avoided_restaurants: list[dict]
    preferred_price_range: Optional[dict] = None
    preferred_distance: Optional[dict] = None
    variety_score: int


# --- Composite Recommendation (🎯 최종) ---
class RecommendationOut(BaseModel):
    rank: int
    restaurant_id: str
    restaurant_name: str
    category: Optional[str] = None
    menu_type: Optional[str] = None
    distance_m: Optional[float] = None
    composite_score: int
    scores: dict[str, int]
    highlights: list[str]
    warnings: list[str]
    weights_used: dict[str, float]


# --- Mood-based Weather Recommendation ---
class MoodOption(BaseModel):
    id: str
    emoji: str
    label: str
    description: str

class WeatherMoodOptionsOut(BaseModel):
    weather_summary: str
    mood_options: list[MoodOption]

class MoodRecommendationItem(BaseModel):
    restaurant_id: str
    restaurant_name: str
    category: Optional[str] = None
    menu_type: Optional[str] = None
    distance_m: int
    mood_score: int
    reason: str

class MoodRecommendationGroup(BaseModel):
    group_label: str
    group_emoji: str
    items: list[MoodRecommendationItem]

class MoodRecommendationOut(BaseModel):
    mood_id: str
    weather_summary: str
    groups: list[MoodRecommendationGroup]


# =============================================================================
# 의존성
# =============================================================================
def get_loader() -> RestaurantLoader:
    """Request 단위 RestaurantLoader."""
    with get_session() as session:
        yield RestaurantLoader(session)


def get_weather_loader() -> WeatherLoader:
    """Request 단위 WeatherLoader."""
    with get_session() as session:
        yield WeatherLoader(session)


def get_nutrition_loader() -> NutritionLoader:
    """Request 단위 NutritionLoader."""
    with get_session() as session:
        yield NutritionLoader(session)


def get_vote_manager() -> VoteManager:
    """Request 단위 VoteManager."""
    with get_session() as session:
        yield VoteManager(session)


def get_visit_tracker() -> VisitTracker:
    """Request 단위 VisitTracker."""
    with get_session() as session:
        yield VisitTracker(session)


def get_preference_analyzer() -> TeamPreferenceAnalyzer:
    """Request 단위 TeamPreferenceAnalyzer."""
    with get_session() as session:
        yield TeamPreferenceAnalyzer(session)


# =============================================================================
# 엔드포인트
# =============================================================================
@app.get("/api/health", response_model=HealthOut, tags=["meta"])
def health_check(loader: RestaurantLoader = Depends(get_loader)) -> HealthOut:
    """헬스체크: DB 연결 + 마지막 수집 시각."""
    try:
        stats = loader.get_statistics()
        return HealthOut(
            status="ok",
            db_connected=True,
            last_collected_at=stats.get("last_collected_at"),
            total_restaurants=stats.get("total", 0),
        )
    except Exception as e:
        logger.exception("health_check failed: %s", e)
        return HealthOut(status="degraded", db_connected=False)


@app.get(
    "/api/restaurants",
    response_model=list[RestaurantOut],
    tags=["restaurants"],
)
def list_restaurants(
    category: Optional[str] = Query(None, description="카테고리 필터 (예: 한식)"),
    min_score: Optional[int] = Query(None, ge=0, le=100, description="최소 거리 점수"),
    limit: int = Query(50, ge=1, le=500, description="최대 결과 수"),
    loader: RestaurantLoader = Depends(get_loader),
) -> list[RestaurantOut]:
    """활성 음식점 목록 (거리순)."""
    rows = loader.get_active_restaurants(
        category=category, min_score=min_score, limit=limit
    )
    return [RestaurantOut(**r.to_dict()) for r in rows]


@app.get("/api/restaurants/stats", response_model=StatsOut, tags=["restaurants"])
def get_stats(loader: RestaurantLoader = Depends(get_loader)) -> StatsOut:
    """전체 통계 (총합, 카테고리 분포, 평균 거리·점수)."""
    return StatsOut(**loader.get_statistics())


# =============================================================================
# Nearby — 사용자 위치 기반 음식점 검색 (on-demand + TTL 캐시)
# =============================================================================
@app.get(
    "/api/restaurants/nearby",
    response_model=list[RestaurantOut],
    tags=["restaurants"],
)
def list_nearby_restaurants(
    lat: float = Query(..., description="사용자 위도"),
    lng: float = Query(..., description="사용자 경도"),
    radius: int = Query(800, ge=100, le=5000, description="검색 반경(m)"),
    limit: int = Query(50, ge=1, le=500),
    category: Optional[str] = Query(None),
    loader: RestaurantLoader = Depends(get_loader),
) -> list[RestaurantOut]:
    """
    사용자 현재 위치 기준으로 주변 음식점 검색.

    플로우:
    1. (lat, lng, radius) 캐시 조회 (100m 그리드 + 5분 TTL)
    2. cache miss → Kakao Local API 로 해당 위치 데이터 수집 + DB upsert
    3. DB 에서 Haversine 기반 근접 순 조회
    4. 캐시에 payload 저장 후 반환
    """
    # 1. 캐시 조회
    cached = location_cache.get(lat, lng, radius)
    if cached is not None:
        logger.info(f"nearby cache HIT lat={lat:.4f} lng={lng:.4f} r={radius} ({len(cached)} total, limit={limit})")
        return [RestaurantOut(**item) for item in cached[:limit]]

    logger.info(f"nearby cache MISS lat={lat:.4f} lng={lng:.4f} r={radius}")

    # 2. cache miss — Kakao Local API 호출 → transform → DB upsert
    try:
        from pipeline.collectors.restaurant_collector import RestaurantCollector
        from pipeline.transformers.distance_scorer import RestaurantTransformer

        collector = RestaurantCollector(lat=lat, lng=lng, radius_m=radius)
        raw_docs = collector.collect_all()
        if raw_docs:
            df = RestaurantTransformer.transform(raw_docs)
            df = RestaurantTransformer.enrich_with_scores(df)
            if not df.empty:
                result = loader.upsert_restaurants(df)
                logger.info(
                    "nearby collected %d docs → %d rows, "
                    "inserted=%d updated=%d",
                    len(raw_docs), len(df),
                    result.get("inserted", 0), result.get("updated", 0),
                )
    except Exception as e:
        # 수집 실패해도 기존 DB 데이터는 반환 시도
        logger.warning(f"nearby Kakao fetch failed: {e}")

    # 3. DB 에서 Haversine 근접 조회 (전체 — limit 은 캐시 후 적용)
    scored = loader.list_nearby(
        lat=lat, lng=lng, radius_m=radius, limit=9999, category=category
    )

    # 4. 결과 포맷 — distance_m 을 사용자 위치 기준으로 override
    results: list[dict] = []
    for r, dist in scored:
        payload = r.to_dict()
        payload["distance_m"] = dist
        payload["distance_score"] = max(
            0, int(round(100 * (1 - dist / radius)))
        )
        results.append(payload)

    # 5. 전체 결과를 캐시에 저장 (limit 무관하게)
    location_cache.set(lat, lng, radius, results)
    logger.info(f"nearby cached {len(results)} restaurants for r={radius}m")

    # 6. limit 적용 후 반환
    return [RestaurantOut(**item) for item in results[:limit]]


# =============================================================================
# Recommend — meal_type-aware 위치 기반 식당 추천 (헤비 옵션 / 다중 식사 시간)
# =============================================================================
@app.get(
    "/api/restaurants/recommend",
    response_model=list[RestaurantOut],
    tags=["restaurants"],
)
def recommend_restaurants(
    lat: float = Query(..., description="사용자 위도"),
    lng: float = Query(..., description="사용자 경도"),
    meal_type: str = Query(
        "any",
        regex="^(breakfast|lunch|dinner|any)$",
        description="식사 시간 — breakfast/lunch/dinner/any",
    ),
    radius: int = Query(2000, ge=100, le=5000, description="검색 반경(m)"),
    limit: int = Query(50, ge=1, le=500),
    loader: RestaurantLoader = Depends(get_loader),
) -> list[RestaurantOut]:
    """
    사용자 위치 + 식사 시간(meal_type) 기반 추천.

    `/api/restaurants/nearby` 의 캐시·수집 로직을 재사용하고,
    meal_type 화이트리스트로 카테고리 필터링한다.

    - breakfast: 카페/베이커리/김밥/죽/샌드위치/브런치 등 가벼운 메뉴
    - lunch:     필터 없음 (전체 카테고리)
    - dinner:    한식/일식/중식/양식/고깃집/술집/뷔페 등 본격 식사
    - any:       필터 없음, 시간대 무관 추천 모드
    """
    # nearby 핸들러를 그대로 호출 → 캐시·수집·점수 계산 재사용
    nearby = list_nearby_restaurants(
        lat=lat, lng=lng, radius=radius, limit=500, category=None, loader=loader
    )

    if meal_type == "any":
        return nearby[:limit]

    # meal_type 필터 — Boolean 영업시간 컬럼 우선, 카테고리 화이트리스트 fallback
    from pipeline.transformers.meal_time_filter import matches_restaurant_meal_type

    filtered = [
        r for r in nearby
        if matches_restaurant_meal_type(r.model_dump(), meal_type)
    ]
    logger.info(
        f"recommend meal_type={meal_type} {len(nearby)}→{len(filtered)} "
        f"after hours+category filter"
    )
    return filtered[:limit]


@app.get(
    "/api/restaurants/{restaurant_id}",
    response_model=RestaurantOut,
    tags=["restaurants"],
)
def get_restaurant(
    restaurant_id: str,
    loader: RestaurantLoader = Depends(get_loader),
) -> RestaurantOut:
    """특정 음식점 상세."""
    r = loader.get_by_id(restaurant_id)
    if r is None:
        raise HTTPException(status_code=404, detail=f"Restaurant {restaurant_id} not found")
    return RestaurantOut(**r.to_dict())


@app.post(
    "/api/pipeline/run",
    response_model=PipelineRunOut,
    tags=["pipeline"],
)
def trigger_pipeline() -> PipelineRunOut:
    """수동으로 파이프라인 1회 실행."""
    pipeline = RestaurantPipeline(ensure_schema=False)
    result = pipeline.run_pipeline()
    return PipelineRunOut(**{
        k: v for k, v in result.to_dict().items()
        if k in PipelineRunOut.model_fields
    })


# =============================================================================
# Weather 엔드포인트 (Subtopic 2)
# =============================================================================
# 캐싱 전략 메모:
#   날씨 데이터는 1시간 단위로 갱신되므로, 프론트엔드에서는 1시간 단위 ETag 캐싱 권장.
#   현재 구현은 DB 의 최신 레코드를 매 요청마다 조회한다 (경량 쿼리).

@app.get(
    "/api/weather/current",
    response_model=WeatherCurrentOut,
    tags=["weather"],
)
def get_current_weather(
    lat: Optional[float] = Query(None, description="사용자 위도 (미입력 시 사무실 좌표)"),
    lng: Optional[float] = Query(None, description="사용자 경도 (미입력 시 사무실 좌표)"),
    loader: WeatherLoader = Depends(get_weather_loader),
) -> WeatherCurrentOut:
    """최신 날씨 + 점심 추천 팁. lat/lng 전달 시 해당 위치의 실시간 날씨를 수집."""
    if lat is not None and lng is not None:
        # 사용자 위치 기반 실시간 날씨 수집
        try:
            from pipeline.collectors.weather_collector import WeatherCollector
            from pipeline.collectors.air_quality_collector import AirQualityCollector
            from pipeline.transformers.weather_scorer import WeatherDataIntegrator

            collector = WeatherCollector(nx=None, ny=None)
            # 동적 좌표로 그리드 변환
            from pipeline.utils.coordinate_converter import latlon_to_grid
            grid_nx, grid_ny = latlon_to_grid(lat, lng)
            collector.nx = grid_nx
            collector.ny = grid_ny

            weather_raw = collector.collect()
            if weather_raw is not None:
                # 에어코리아는 가장 가까운 관측소 기준 (동적 위치 반영 한계 → 기존 데이터 사용)
                air_data = None
                try:
                    air_collector = AirQualityCollector()
                    air_data = air_collector.collect()
                except Exception:
                    pass
                integrated = WeatherDataIntegrator.integrate(weather_raw, air_data)
                tips = WeatherMenuScorer.get_weather_tips(integrated)
                return WeatherCurrentOut(**{**integrated, "tips": tips})
        except Exception as e:
            logger.warning("Location-based weather failed (lat=%s, lng=%s): %s", lat, lng, e)
        # 실패 시 DB 저장 데이터로 폴백

    latest = loader.get_latest_weather()
    if latest is None:
        return WeatherCurrentOut(tips=["아직 날씨 데이터가 없어요. /api/weather/refresh 로 수집하세요"])

    weather_dict = latest.to_dict()
    tips = WeatherMenuScorer.get_weather_tips(weather_dict)
    return WeatherCurrentOut(**{**weather_dict, "tips": tips})


@app.get(
    "/api/weather/history",
    response_model=list[WeatherHistoryItem],
    tags=["weather"],
)
def get_weather_history(
    hours: int = Query(24, ge=1, le=168, description="조회 시간 범위"),
    loader: WeatherLoader = Depends(get_weather_loader),
) -> list[WeatherHistoryItem]:
    """최근 N시간 날씨 이력."""
    rows = loader.get_weather_history(hours=hours)
    return [
        WeatherHistoryItem(
            id=r.id,
            collected_at=r.collected_at.isoformat(),
            temp=r.temp,
            sky_str=r.sky_str,
            pop=r.pop,
            dust_grade=r.dust_grade,
            outdoor_comfort=r.outdoor_comfort,
        )
        for r in rows
    ]


@app.get(
    "/api/weather/menu-ranking",
    response_model=list[MenuRankingItem],
    tags=["weather"],
)
def get_menu_ranking(
    loader: WeatherLoader = Depends(get_weather_loader),
) -> list[MenuRankingItem]:
    """현재 날씨 기준 메뉴 타입별 적합도 랭킹."""
    latest = loader.get_latest_weather()
    if latest is None:
        raise HTTPException(
            status_code=404, detail="No weather data. Run /api/weather/refresh first."
        )
    ranking = WeatherMenuScorer.get_menu_type_ranking(latest.to_dict())
    return [MenuRankingItem(**item) for item in ranking]


@app.get(
    "/api/restaurants/weather-ranked",
    response_model=list[WeatherRankedRestaurantOut],
    tags=["restaurants", "weather"],
)
def get_weather_ranked_restaurants(
    limit: int = Query(10, ge=1, le=100),
    category: Optional[str] = Query(None),
    rest_loader: RestaurantLoader = Depends(get_loader),
    weather_loader: WeatherLoader = Depends(get_weather_loader),
) -> list[WeatherRankedRestaurantOut]:
    """날씨 점수 반영 음식점 랭킹."""
    latest = weather_loader.get_latest_weather()
    if latest is None:
        raise HTTPException(status_code=404, detail="No weather data available.")

    restaurants = rest_loader.get_active_restaurants(category=category)
    rest_dicts = [r.to_dict() for r in restaurants]
    ranked = WeatherMenuScorer.rank_restaurants_by_weather(rest_dicts, latest.to_dict())
    return [WeatherRankedRestaurantOut(**r) for r in ranked[:limit]]


@app.get(
    "/api/weather/mood-options",
    response_model=WeatherMoodOptionsOut,
    tags=["weather"],
)
def get_mood_options(
    lat: Optional[float] = Query(None),
    lng: Optional[float] = Query(None),
    loader: WeatherLoader = Depends(get_weather_loader),
) -> WeatherMoodOptionsOut:
    """현재 날씨에 맞는 무드 옵션 목록."""
    # 위치 기반이든 DB 기반이든 날씨 데이터 확보
    weather_dict = None
    if lat is not None and lng is not None:
        try:
            from pipeline.collectors.weather_collector import WeatherCollector
            from pipeline.utils.coordinate_converter import latlon_to_grid
            grid_nx, grid_ny = latlon_to_grid(lat, lng)
            collector = WeatherCollector()
            collector.nx, collector.ny = grid_nx, grid_ny
            weather_dict = collector.collect()
        except Exception:
            pass

    if weather_dict is None:
        latest = loader.get_latest_weather()
        if latest is None:
            raise HTTPException(status_code=404, detail="No weather data.")
        weather_dict = latest.to_dict()

    options = WeatherMenuScorer.get_mood_options(weather_dict)
    temp = weather_dict.get("temp", 0)
    rain_type_str = weather_dict.get("rain_type_str", "없음")
    sky_str = weather_dict.get("sky_str", "맑음")
    summary = f"{temp}°C · {sky_str}"
    if rain_type_str != "없음":
        summary += f" · {rain_type_str}"

    return WeatherMoodOptionsOut(
        weather_summary=summary,
        mood_options=[MoodOption(**o) for o in options],
    )


@app.get(
    "/api/weather/mood-recommend",
    response_model=MoodRecommendationOut,
    tags=["weather"],
)
def get_mood_recommendation(
    mood_id: str = Query(..., description="선택한 무드 ID"),
    lat: Optional[float] = Query(None),
    lng: Optional[float] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    rest_loader: RestaurantLoader = Depends(get_loader),
    weather_loader: WeatherLoader = Depends(get_weather_loader),
) -> MoodRecommendationOut:
    """무드 기반 음식점 추천."""
    # 날씨 데이터
    weather_dict = None
    if lat is not None and lng is not None:
        try:
            from pipeline.collectors.weather_collector import WeatherCollector
            from pipeline.utils.coordinate_converter import latlon_to_grid
            grid_nx, grid_ny = latlon_to_grid(lat, lng)
            collector = WeatherCollector()
            collector.nx, collector.ny = grid_nx, grid_ny
            weather_dict = collector.collect()
        except Exception:
            pass

    if weather_dict is None:
        latest = weather_loader.get_latest_weather()
        if latest is None:
            raise HTTPException(status_code=404, detail="No weather data.")
        weather_dict = latest.to_dict()

    # 음식점 데이터
    restaurants = rest_loader.get_active_restaurants()
    rest_dicts = [r.to_dict() for r in restaurants]

    # 무드 추천
    recs = WeatherMenuScorer.get_mood_recommendations(rest_dicts, weather_dict, mood_id, limit)

    temp = weather_dict.get("temp", 0)
    sky_str = weather_dict.get("sky_str", "맑음")
    summary = f"{temp}°C · {sky_str}"

    items = [
        MoodRecommendationItem(
            restaurant_id=r.get("id", ""),
            restaurant_name=r.get("name", ""),
            category=r.get("category"),
            menu_type=r.get("menu_type"),
            distance_m=int(r.get("distance_m", 0)),
            mood_score=r["mood_score"],
            reason=r["reason"],
        )
        for r in recs
    ]

    return MoodRecommendationOut(
        mood_id=mood_id,
        weather_summary=summary,
        groups=[MoodRecommendationGroup(
            group_label=f"'{mood_id}' 추천",
            group_emoji="⭐",
            items=items,
        )],
    )


@app.get(
    "/api/weather/grouped-recommend",
    response_model=list[MoodRecommendationGroup],
    tags=["weather"],
)
def get_grouped_recommendations(
    lat: Optional[float] = Query(None),
    lng: Optional[float] = Query(None),
    rest_loader: RestaurantLoader = Depends(get_loader),
    weather_loader: WeatherLoader = Depends(get_weather_loader),
) -> list[MoodRecommendationGroup]:
    """날씨 기반 카테고리별 그룹 추천."""
    weather_dict = None
    if lat is not None and lng is not None:
        try:
            from pipeline.collectors.weather_collector import WeatherCollector
            from pipeline.utils.coordinate_converter import latlon_to_grid
            grid_nx, grid_ny = latlon_to_grid(lat, lng)
            collector = WeatherCollector()
            collector.nx, collector.ny = grid_nx, grid_ny
            weather_dict = collector.collect()
        except Exception:
            pass

    if weather_dict is None:
        latest = weather_loader.get_latest_weather()
        if latest is None:
            raise HTTPException(status_code=404, detail="No weather data.")
        weather_dict = latest.to_dict()

    restaurants = rest_loader.get_active_restaurants()
    rest_dicts = [r.to_dict() for r in restaurants]
    groups = WeatherMenuScorer.get_grouped_recommendations(rest_dicts, weather_dict)

    result = []
    for g in groups:
        items = [
            MoodRecommendationItem(
                restaurant_id=r.get("id", ""),
                restaurant_name=r.get("name", ""),
                category=r.get("category"),
                menu_type=r.get("menu_type"),
                distance_m=int(r.get("distance_m", 0)),
                mood_score=r["mood_score"],
                reason=r["reason"],
            )
            for r in g["items"]
        ]
        result.append(MoodRecommendationGroup(
            group_label=g["group_label"],
            group_emoji=g["group_emoji"],
            items=items,
        ))
    return result


@app.post(
    "/api/weather/refresh",
    response_model=WeatherRefreshOut,
    tags=["weather"],
)
def refresh_weather() -> WeatherRefreshOut:
    """날씨 파이프라인 수동 실행."""
    pipeline = WeatherPipeline(ensure_schema_flag=False)
    result = pipeline.run_pipeline()
    return WeatherRefreshOut(
        success=result.success,
        duration_sec=result.duration_sec,
        log_id=result.log_id,
        error=result.error,
    )


# =============================================================================
# Nutrition 엔드포인트 (Subtopic 3)
# =============================================================================
def _get_weekly_summary_dict(
    loader: NutritionLoader, user_id: str, week_offset: int = 0
) -> dict:
    """주간 요약 dict 조회 (탄단지 비율 + meal_type 그룹화 포함)."""
    from datetime import timedelta
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    week_start = monday + timedelta(weeks=week_offset)
    week_end = week_start + timedelta(days=6)
    stats = loader.get_weekly_stats(user_id, week_start)

    # 탄단지 비율 추가
    total = stats.get("weekly_total") or {}
    carbs_kcal = (total.get("carbs", 0)) * 4
    protein_kcal = (total.get("protein", 0)) * 4
    fat_kcal = (total.get("fat", 0)) * 9
    total_macro = carbs_kcal + protein_kcal + fat_kcal
    if total_macro > 0:
        stats["macro_ratio"] = {
            "carbs_pct": round(carbs_kcal / total_macro * 100, 1),
            "protein_pct": round(protein_kcal / total_macro * 100, 1),
            "fat_pct": round(fat_kcal / total_macro * 100, 1),
        }
    else:
        stats["macro_ratio"] = {"carbs_pct": 0.0, "protein_pct": 0.0, "fat_pct": 0.0}

    # meal_type 그룹화 — 헤비 옵션의 핵심
    # 식사 시간별 합계/평균을 별도 분리하여 stacked 차트와 식사별 달성률에 활용
    by_meal_type: dict[str, dict[str, float]] = {
        "breakfast": {"calories": 0.0, "carbs": 0.0, "protein": 0.0, "fat": 0.0, "sodium": 0.0, "count": 0},
        "lunch":     {"calories": 0.0, "carbs": 0.0, "protein": 0.0, "fat": 0.0, "sodium": 0.0, "count": 0},
        "dinner":    {"calories": 0.0, "carbs": 0.0, "protein": 0.0, "fat": 0.0, "sodium": 0.0, "count": 0},
        "unknown":   {"calories": 0.0, "carbs": 0.0, "protein": 0.0, "fat": 0.0, "sodium": 0.0, "count": 0},
    }
    try:
        rows = loader.get_meal_history(user_id, week_start, week_end)
        for r in rows:
            mt = (r.meal_type or "unknown").lower()
            if mt not in by_meal_type:
                mt = "unknown"
            bucket = by_meal_type[mt]
            bucket["calories"] += float(r.calories or 0)
            bucket["carbs"]    += float(r.carbs or 0)
            bucket["protein"]  += float(r.protein or 0)
            bucket["fat"]      += float(r.fat or 0)
            bucket["sodium"]   += float(r.sodium or 0)
            bucket["count"]    += 1
    except Exception as e:
        logger.warning(f"by_meal_type aggregation failed: {e}")

    stats["by_meal_type"] = by_meal_type
    return stats


_NUTRIENT_KEYS = ("calories", "carbs", "protein", "fat", "sugar", "sodium")


def _parse_meal_date(value: Optional[str]) -> date:
    if not value:
        return date.today()
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        raise HTTPException(status_code=400, detail="meal_date must be ISO date (YYYY-MM-DD)")


def _round_nutrient(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    return round(float(value), 2)


def _scaled(value: Optional[float], quantity: float) -> Optional[float]:
    if value is None:
        return None
    return _round_nutrient(float(value) * quantity)


def _item_has_nutrition(item: NaturalMealItemIn) -> bool:
    return any(getattr(item, key) is not None for key in _NUTRIENT_KEYS)


def _nutrition_item_from_info(
    item: NaturalMealItemIn,
    info: Any,
    source: str,
    match_type: str,
    confidence: Optional[float],
) -> dict[str, Any]:
    quantity = float(item.quantity or 1.0)
    return {
        "raw_name": item.raw_name,
        "normalized_name": item.normalized_name or getattr(info, "food_name", None) or item.raw_name,
        "food_code": getattr(info, "food_code", None),
        "quantity": quantity,
        "unit": item.unit or "serving",
        "serving_size": getattr(info, "serving_size", None),
        "calories": _scaled(getattr(info, "calories", None), quantity),
        "carbs": _scaled(getattr(info, "carbs", None), quantity),
        "protein": _scaled(getattr(info, "protein", None), quantity),
        "fat": _scaled(getattr(info, "fat", None), quantity),
        "sugar": _scaled(getattr(info, "sugar", None), quantity),
        "sodium": _scaled(getattr(info, "sodium", None), quantity),
        "source": source,
        "match_type": match_type,
        "match_confidence": confidence,
        "needs_review": confidence is None or confidence < 0.7,
    }


def _nutrition_item_from_api_result(
    item: NaturalMealItemIn,
    result: dict[str, Any],
) -> dict[str, Any]:
    quantity = float(item.quantity or 1.0)
    return {
        "raw_name": item.raw_name,
        "normalized_name": item.normalized_name or result.get("food_name") or item.raw_name,
        "food_code": result.get("food_code"),
        "quantity": quantity,
        "unit": item.unit or "serving",
        "serving_size": result.get("serving_size"),
        "calories": _scaled(result.get("calories"), quantity),
        "carbs": _scaled(result.get("carbs"), quantity),
        "protein": _scaled(result.get("protein"), quantity),
        "fat": _scaled(result.get("fat"), quantity),
        "sugar": _scaled(result.get("sugar"), quantity),
        "sodium": _scaled(result.get("sodium"), quantity),
        "source": "foodsafetykorea:I2790",
        "match_type": "api_keyword",
        "match_confidence": 0.8,
        "needs_review": False,
    }


def _manual_item(item: NaturalMealItemIn) -> dict[str, Any]:
    quantity = float(item.quantity or 1.0)
    source = item.source or ("user_adjusted" if _item_has_nutrition(item) else "unverified")
    needs_review = item.needs_review or not _item_has_nutrition(item)
    return {
        "raw_name": item.raw_name,
        "normalized_name": item.normalized_name or item.raw_name,
        "food_code": item.food_code,
        "quantity": quantity,
        "unit": item.unit or "serving",
        "serving_size": item.serving_size,
        "calories": _scaled(item.calories, quantity),
        "carbs": _scaled(item.carbs, quantity),
        "protein": _scaled(item.protein, quantity),
        "fat": _scaled(item.fat, quantity),
        "sugar": _scaled(item.sugar, quantity),
        "sodium": _scaled(item.sodium, quantity),
        "source": source,
        "match_type": item.match_type or source,
        "match_confidence": item.match_confidence,
        "needs_review": needs_review,
    }


def _try_food_safety(item: NaturalMealItemIn) -> Optional[dict[str, Any]]:
    import os

    if os.getenv("LUNCH_ENABLE_FOOD_SAFETY_LOOKUP", "0") != "1":
        return None
    if not os.getenv("FOOD_SAFETY_API_KEY"):
        return None
    query = (item.normalized_name or item.raw_name).strip()
    if not query:
        return None
    try:
        collector = NutritionCollector()
        rows = collector.search_by_name(query, max_results=1)
    except Exception as e:
        logger.info("Food Safety nutrition lookup skipped for %s: %s", query, e)
        return None
    if not rows:
        return None
    return _nutrition_item_from_api_result(item, rows[0])


def _resolve_natural_item(
    item: NaturalMealItemIn,
    loader: NutritionLoader,
    restaurant_id: Optional[str],
    use_restaurant_default: bool,
) -> dict[str, Any]:
    if _item_has_nutrition(item):
        return _manual_item(item)

    query = item.normalized_name or item.raw_name
    local = loader.find_nutrition_by_food_name(query)
    if local is not None:
        confidence = local.match_score if local.match_score is not None else 0.75
        return _nutrition_item_from_info(
            item=item,
            info=local,
            source="local_cache",
            match_type=local.match_type or "local_food_name",
            confidence=confidence,
        )

    if restaurant_id and use_restaurant_default:
        restaurant_info = loader.get_nutrition_by_restaurant(restaurant_id)
        if restaurant_info is not None:
            confidence = restaurant_info.match_score if restaurant_info.match_score is not None else 0.65
            return _nutrition_item_from_info(
                item=item,
                info=restaurant_info,
                source="restaurant_mapping",
                match_type=restaurant_info.match_type or "restaurant_default",
                confidence=confidence,
            )

    api_item = _try_food_safety(item)
    if api_item is not None:
        return api_item

    return _manual_item(item)


def _sum_items(items: list[dict[str, Any]], key: str) -> Optional[float]:
    values = [float(item[key]) for item in items if item.get(key) is not None]
    if not values:
        return None
    return round(sum(values), 2)


def _menu_summary(items: list[dict[str, Any]]) -> str:
    names = [item.get("normalized_name") or item.get("raw_name") for item in items]
    names = [str(name) for name in names if name]
    if not names:
        return "직접 입력 식단"
    if len(names) == 1:
        return names[0]
    return f"{names[0]} 외 {len(names) - 1}개"


def _combine_sources(items: list[dict[str, Any]]) -> str:
    sources = sorted({str(item.get("source") or "unverified") for item in items})
    if len(sources) == 1:
        return sources[0]
    if any(source == "unverified" for source in sources):
        return "mixed_unverified"
    return "mixed"


def _avg_confidence(items: list[dict[str, Any]]) -> Optional[float]:
    values = [
        float(item["match_confidence"])
        for item in items
        if item.get("match_confidence") is not None
    ]
    if not values:
        return None
    return round(sum(values) / len(values), 3)


def _build_natural_meal_analysis(
    body: NaturalMealRecordIn,
    nutr_loader: NutritionLoader,
    rest_loader: RestaurantLoader,
) -> dict[str, Any]:
    meal_date = _parse_meal_date(body.meal_date)
    restaurant = None
    if body.restaurant_id:
        restaurant = rest_loader.get_by_id(body.restaurant_id)
        if restaurant is None:
            raise HTTPException(status_code=404, detail="Restaurant not found")

    use_restaurant_default = len(body.items) == 1
    resolved_items = [
        _resolve_natural_item(item, nutr_loader, body.restaurant_id, use_restaurant_default)
        for item in body.items
    ]
    needs_review = any(item.get("needs_review", True) for item in resolved_items)
    if not any(item.get("calories") is not None for item in resolved_items):
        needs_review = True

    snapshot = body.restaurant_snapshot
    restaurant_name = (
        restaurant.name if restaurant is not None
        else snapshot.name if snapshot is not None
        else None
    )
    restaurant_url = (
        restaurant.place_url if restaurant is not None
        else snapshot.place_url if snapshot is not None
        else None
    )

    return {
        "user_id": body.user_id,
        "raw_text": body.raw_text,
        "meal_date": meal_date.isoformat(),
        "meal_type": body.meal_type,
        "restaurant_id": body.restaurant_id,
        "restaurant_name_snapshot": restaurant_name,
        "restaurant_place_url": restaurant_url,
        "menu_name": _menu_summary(resolved_items),
        "calories": _sum_items(resolved_items, "calories"),
        "carbs": _sum_items(resolved_items, "carbs"),
        "protein": _sum_items(resolved_items, "protein"),
        "fat": _sum_items(resolved_items, "fat"),
        "sugar": _sum_items(resolved_items, "sugar"),
        "sodium": _sum_items(resolved_items, "sodium"),
        "satisfaction": body.satisfaction,
        "nutrition_source": _combine_sources(resolved_items),
        "match_confidence": _avg_confidence(resolved_items),
        "needs_review": needs_review,
        "items": resolved_items,
    }


def _analysis_to_out(analysis: dict[str, Any]) -> NaturalMealAnalysisOut:
    return NaturalMealAnalysisOut(
        **{
            **analysis,
            "items": [NaturalMealItemOut(**item) for item in analysis["items"]],
        }
    )


def _meal_to_analysis(meal: Any) -> NaturalMealAnalysisOut:
    items = [NaturalMealItemOut(**item.to_dict()) for item in getattr(meal, "items", [])]
    return NaturalMealAnalysisOut(
        id=meal.id,
        user_id=meal.user_id,
        raw_text=meal.raw_text or meal.menu_name or "",
        meal_date=meal.meal_date.isoformat() if meal.meal_date else "",
        meal_type=meal.meal_type,
        restaurant_id=meal.restaurant_id,
        restaurant_name_snapshot=meal.restaurant_name_snapshot,
        restaurant_place_url=meal.restaurant_place_url,
        menu_name=meal.menu_name,
        calories=meal.calories,
        carbs=meal.carbs,
        protein=meal.protein,
        fat=meal.fat,
        sugar=meal.sugar,
        sodium=meal.sodium,
        satisfaction=meal.satisfaction,
        nutrition_source=meal.nutrition_source,
        match_confidence=meal.match_confidence,
        needs_review=bool(meal.needs_review),
        created_at=meal.created_at.isoformat() if meal.created_at else None,
        updated_at=meal.updated_at.isoformat() if getattr(meal, "updated_at", None) else None,
        items=items,
    )


@app.get(
    "/api/nutrition/restaurant/{restaurant_id}",
    response_model=NutritionInfoOut,
    tags=["nutrition"],
)
def get_restaurant_nutrition(
    restaurant_id: str,
    loader: NutritionLoader = Depends(get_nutrition_loader),
) -> NutritionInfoOut:
    """특정 음식점 추정 영양 정보."""
    info = loader.get_nutrition_by_restaurant(restaurant_id)
    if info is None:
        raise HTTPException(
            status_code=404,
            detail=f"No nutrition mapping for restaurant {restaurant_id}",
        )
    return NutritionInfoOut(**info.to_dict())


@app.post(
    "/api/nutrition/meal",
    response_model=MealRecordOut,
    tags=["nutrition"],
)
def record_meal(
    body: MealRecordIn,
    nutr_loader: NutritionLoader = Depends(get_nutrition_loader),
    rest_loader: RestaurantLoader = Depends(get_loader),
) -> MealRecordOut:
    """
    식사 기록 저장. 음식점의 영양 정보가 있으면 자동 매핑.
    """
    from datetime import datetime as _dt

    # 식당 존재 확인
    restaurant = rest_loader.get_by_id(body.restaurant_id)
    if restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    # 영양 정보 자동 조회
    nutrition = nutr_loader.get_nutrition_by_restaurant(body.restaurant_id)
    nutrition_dict = nutrition.to_dict() if nutrition else {}

    # meal_date 파싱
    meal_date_val = date.today()
    if body.meal_date:
        try:
            meal_date_val = _dt.fromisoformat(body.meal_date).date()
        except ValueError:
            raise HTTPException(
                status_code=400, detail="meal_date must be ISO date (YYYY-MM-DD)"
            )

    record = {
        "user_id": body.user_id,
        "restaurant_id": body.restaurant_id,
        "menu_name": body.menu_name or restaurant.name,
        "meal_date": meal_date_val,
        "calories": nutrition_dict.get("calories"),
        "carbs": nutrition_dict.get("carbs"),
        "protein": nutrition_dict.get("protein"),
        "fat": nutrition_dict.get("fat"),
        "sugar": nutrition_dict.get("sugar"),
        "sodium": nutrition_dict.get("sodium"),
        "satisfaction": body.satisfaction,
    }
    saved = nutr_loader.save_meal_record(record)
    return MealRecordOut(**saved.to_dict())


@app.post(
    "/api/nutrition/meal-natural/preview",
    response_model=NaturalMealAnalysisOut,
    tags=["nutrition"],
)
def preview_natural_meal(
    body: NaturalMealRecordIn,
    nutr_loader: NutritionLoader = Depends(get_nutrition_loader),
    rest_loader: RestaurantLoader = Depends(get_loader),
) -> NaturalMealAnalysisOut:
    """
    자연어 식단 파싱 결과를 저장 전에 영양 후보와 합산한다.

    영양값은 사용자가 보낸 값, 로컬 영양 캐시, 식품안전나라 API 결과만 사용한다.
    매칭 실패 항목은 `unverified`로 반환하고 임의 수치를 만들지 않는다.
    """
    analysis = _build_natural_meal_analysis(body, nutr_loader, rest_loader)
    return _analysis_to_out(analysis)


@app.post(
    "/api/nutrition/meal-natural",
    response_model=NaturalMealAnalysisOut,
    tags=["nutrition"],
)
def record_natural_meal(
    body: NaturalMealRecordIn,
    nutr_loader: NutritionLoader = Depends(get_nutrition_loader),
    rest_loader: RestaurantLoader = Depends(get_loader),
) -> NaturalMealAnalysisOut:
    """
    자연어로 입력한 한 끼 식단과 음식별 항목을 저장한다.
    """
    analysis = _build_natural_meal_analysis(body, nutr_loader, rest_loader)
    meal_date = date.fromisoformat(analysis["meal_date"])
    record = {
        "user_id": analysis["user_id"],
        "restaurant_id": analysis.get("restaurant_id"),
        "menu_name": analysis.get("menu_name"),
        "meal_date": meal_date,
        "calories": analysis.get("calories"),
        "carbs": analysis.get("carbs"),
        "protein": analysis.get("protein"),
        "fat": analysis.get("fat"),
        "sugar": analysis.get("sugar"),
        "sodium": analysis.get("sodium"),
        "satisfaction": analysis.get("satisfaction"),
        "raw_text": analysis.get("raw_text"),
        "meal_type": analysis.get("meal_type"),
        "parsed_items_json": json.dumps(analysis["items"], ensure_ascii=False),
        "nutrition_source": analysis.get("nutrition_source"),
        "match_confidence": analysis.get("match_confidence"),
        "needs_review": analysis.get("needs_review"),
        "restaurant_name_snapshot": analysis.get("restaurant_name_snapshot"),
        "restaurant_place_url": analysis.get("restaurant_place_url"),
    }
    meal, items = nutr_loader.save_natural_meal_record(record, analysis["items"])
    analysis["id"] = meal.id
    analysis["items"] = [
        {**item.to_dict(), "id": item.id}
        for item in items
    ]
    return _analysis_to_out(analysis)


@app.get(
    "/api/nutrition/meals",
    response_model=list[NaturalMealAnalysisOut],
    tags=["nutrition"],
)
def list_nutrition_meals(
    user_id: str = Query(..., min_length=1, max_length=50),
    start: Optional[str] = Query(None, description="YYYY-MM-DD"),
    end: Optional[str] = Query(None, description="YYYY-MM-DD"),
    limit: int = Query(30, ge=1, le=100),
    loader: NutritionLoader = Depends(get_nutrition_loader),
) -> list[NaturalMealAnalysisOut]:
    """사용자 식사 기록 목록을 최신순으로 조회한다."""
    start_date = _parse_meal_date(start) if start else None
    end_date = _parse_meal_date(end) if end else None
    rows = loader.list_meal_records(user_id, start_date, end_date, limit)
    return [_meal_to_analysis(row) for row in rows]


@app.patch(
    "/api/nutrition/meals/{meal_id}",
    response_model=NaturalMealAnalysisOut,
    tags=["nutrition"],
)
def update_nutrition_meal(
    meal_id: int,
    body: NaturalMealRecordIn,
    nutr_loader: NutritionLoader = Depends(get_nutrition_loader),
    rest_loader: RestaurantLoader = Depends(get_loader),
) -> NaturalMealAnalysisOut:
    """기존 식사 기록을 재분석 결과로 교체 업데이트한다."""
    existing = nutr_loader.get_meal_record(meal_id)
    if existing is None or existing.user_id != body.user_id:
        raise HTTPException(status_code=404, detail="Meal record not found")

    analysis = _build_natural_meal_analysis(body, nutr_loader, rest_loader)
    record = {
        "user_id": analysis["user_id"],
        "restaurant_id": analysis.get("restaurant_id"),
        "menu_name": analysis.get("menu_name"),
        "meal_date": date.fromisoformat(analysis["meal_date"]),
        "calories": analysis.get("calories"),
        "carbs": analysis.get("carbs"),
        "protein": analysis.get("protein"),
        "fat": analysis.get("fat"),
        "sugar": analysis.get("sugar"),
        "sodium": analysis.get("sodium"),
        "satisfaction": analysis.get("satisfaction"),
        "raw_text": analysis.get("raw_text"),
        "meal_type": analysis.get("meal_type"),
        "parsed_items_json": json.dumps(analysis["items"], ensure_ascii=False),
        "nutrition_source": analysis.get("nutrition_source"),
        "match_confidence": analysis.get("match_confidence"),
        "needs_review": analysis.get("needs_review"),
        "restaurant_name_snapshot": analysis.get("restaurant_name_snapshot"),
        "restaurant_place_url": analysis.get("restaurant_place_url"),
    }
    meal, items = nutr_loader.update_natural_meal_record(
        meal_id, body.user_id, record, analysis["items"]
    )
    analysis["id"] = meal.id
    analysis["created_at"] = meal.created_at.isoformat() if meal.created_at else None
    analysis["updated_at"] = meal.updated_at.isoformat() if meal.updated_at else None
    analysis["items"] = [{**item.to_dict(), "id": item.id} for item in items]
    return _analysis_to_out(analysis)


@app.delete(
    "/api/nutrition/meals/{meal_id}",
    response_model=DeleteMealOut,
    tags=["nutrition"],
)
def delete_nutrition_meal(
    meal_id: int,
    user_id: str = Query(..., min_length=1, max_length=50),
    loader: NutritionLoader = Depends(get_nutrition_loader),
) -> DeleteMealOut:
    """사용자 식사 기록을 삭제한다."""
    deleted = loader.delete_meal_record(meal_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Meal record not found")
    return DeleteMealOut(deleted=True, meal_id=meal_id)


@app.get(
    "/api/nutrition/weekly",
    response_model=WeeklySummaryOut,
    tags=["nutrition"],
)
def get_weekly_nutrition(
    user_id: str = Query(..., description="사용자 ID"),
    week_offset: int = Query(0, ge=-52, le=0, description="0=이번 주, -1=지난 주"),
    loader: NutritionLoader = Depends(get_nutrition_loader),
) -> WeeklySummaryOut:
    """주간 영양 섭취 요약."""
    stats = _get_weekly_summary_dict(loader, user_id, week_offset)
    return WeeklySummaryOut(**stats)


# =============================================================================
# Nutrition targets — 일일 권장량 식사별 분배 (헤비 옵션 / 다중 식사 시간)
# =============================================================================
# 식사 시간별 칼로리·다량영양소 분배 비율 (한국 영양학회 일반 가이드라인)
_MEAL_RATIO: dict[str, float] = {
    "breakfast": 0.25,
    "lunch": 0.35,
    "dinner": 0.40,
}

# 일반 성인 권장량 — 사용자 프로필이 있으면 향후 개인화 가능
_DEFAULT_DAILY: dict[str, float] = {
    "calories": 2000.0,   # kcal
    "carbs": 300.0,       # g
    "protein": 65.0,      # g
    "fat": 55.0,          # g
    "sodium": 2000.0,     # mg
}


@app.get(
    "/api/nutrition/targets/{user_id}",
    tags=["nutrition"],
)
def get_nutrition_targets(user_id: str) -> dict:
    """
    사용자 일일 권장 영양 섭취량을 식사 시간별로 분배.

    아침 25% / 점심 35% / 저녁 40% 비율로 칼로리·탄수화물·단백질·지방·나트륨을 분리.
    프런트 Nutrition 페이지의 stacked 차트 + 식사별 달성률 표시에 사용.
    """
    daily = _DEFAULT_DAILY.copy()

    by_meal: dict[str, dict[str, float]] = {}
    for meal, ratio in _MEAL_RATIO.items():
        by_meal[meal] = {
            "ratio": ratio,
            "calories": round(daily["calories"] * ratio, 1),
            "carbs_g": round(daily["carbs"] * ratio, 1),
            "protein_g": round(daily["protein"] * ratio, 1),
            "fat_g": round(daily["fat"] * ratio, 1),
            "sodium_mg": round(daily["sodium"] * ratio, 1),
        }

    return {
        "user_id": user_id,
        "daily": {
            "calories": daily["calories"],
            "carbs_g": daily["carbs"],
            "protein_g": daily["protein"],
            "fat_g": daily["fat"],
            "sodium_mg": daily["sodium"],
        },
        "by_meal": by_meal,
    }


@app.get(
    "/api/nutrition/diagnosis",
    response_model=DiagnosisOut,
    tags=["nutrition"],
)
def get_diagnosis(
    user_id: str = Query(..., description="사용자 ID"),
    loader: NutritionLoader = Depends(get_nutrition_loader),
) -> DiagnosisOut:
    """영양 밸런스 진단."""
    summary = _get_weekly_summary_dict(loader, user_id, 0)
    diagnosis = NutritionDiagnostic.diagnose_weekly(summary)
    return DiagnosisOut(**diagnosis)


@app.get(
    "/api/nutrition/trend",
    response_model=list[NutrientTrendItem],
    tags=["nutrition"],
)
def get_trend(
    user_id: str = Query(...),
    days: int = Query(14, ge=1, le=90),
    loader: NutritionLoader = Depends(get_nutrition_loader),
) -> list[NutrientTrendItem]:
    """최근 N일 영양소 트렌드."""
    from datetime import timedelta
    today = date.today()
    start = today - timedelta(days=days - 1)
    rows = loader.get_meal_history(user_id, start, today)

    from collections import defaultdict
    by_day: dict = defaultdict(
        lambda: {"calories": 0.0, "carbs": 0.0, "protein": 0.0, "fat": 0.0, "sodium": 0.0, "has_record": False}
    )
    for r in rows:
        d = by_day[r.meal_date]
        d["calories"] += r.calories or 0
        d["carbs"] += r.carbs or 0
        d["protein"] += r.protein or 0
        d["fat"] += r.fat or 0
        d["sodium"] += r.sodium or 0
        d["has_record"] = True

    result = []
    for i in range(days):
        d = start + timedelta(days=i)
        entry = by_day.get(d)
        result.append(NutrientTrendItem(
            date=d.isoformat(),
            calories=entry["calories"] if entry else 0,
            carbs=entry["carbs"] if entry else 0,
            protein=entry["protein"] if entry else 0,
            fat=entry["fat"] if entry else 0,
            sodium=entry["sodium"] if entry else 0,
            has_record=entry["has_record"] if entry else False,
        ))
    return result


@app.get(
    "/api/restaurants/nutrition-ranked",
    response_model=list[NutritionRankedRestaurantOut],
    tags=["restaurants", "nutrition"],
)
def get_nutrition_ranked_restaurants(
    user_id: str = Query(..., description="사용자 ID"),
    limit: int = Query(10, ge=1, le=100),
    category: Optional[str] = Query(None),
    rest_loader: RestaurantLoader = Depends(get_loader),
    nutr_loader: NutritionLoader = Depends(get_nutrition_loader),
) -> list[NutritionRankedRestaurantOut]:
    """
    사용자의 주간 영양 이력 기반 음식점 영양 점수 랭킹.
    """
    summary = _get_weekly_summary_dict(nutr_loader, user_id, 0)
    restaurants = rest_loader.get_active_restaurants(category=category)

    enriched = []
    for r in restaurants:
        info = nutr_loader.get_nutrition_by_restaurant(r.id)
        r_dict = r.to_dict()
        nutrition_dict = info.to_dict() if info else {}
        score = NutritionRecommendScorer.calculate_nutrition_score(
            nutrition_dict, summary
        )
        advice = NutritionRecommendScorer.get_nutrition_advice_for_restaurant(
            nutrition_dict, summary
        )
        enriched.append({
            **r_dict,
            "nutrition_score": score,
            "nutrition_advice": advice,
        })

    enriched.sort(key=lambda x: x["nutrition_score"], reverse=True)
    return [NutritionRankedRestaurantOut(**e) for e in enriched[:limit]]


# =============================================================================
# Vote 엔드포인트 (Subtopic 4)
# =============================================================================
def _parse_date_opt(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    from datetime import datetime as _dt
    try:
        return _dt.fromisoformat(s).date()
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid date: {s}")


@app.post("/api/vote/session", response_model=VoteSessionOut, tags=["vote"], status_code=201)
def open_vote_session(
    body: VoteSessionIn,
    mgr: VoteManager = Depends(get_vote_manager),
) -> VoteSessionOut:
    """투표 세션 개시."""
    try:
        session_obj = mgr.open_session(body.team_id, _parse_date_opt(body.vote_date))
        return VoteSessionOut(
            id=session_obj.id,
            vote_date=session_obj.vote_date.isoformat(),
            team_id=session_obj.team_id,
            status=session_obj.status,
            total_votes=session_obj.total_votes or 0,
            winner_restaurant_id=session_obj.winner_restaurant_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/vote/cast", response_model=VoteCastOut, tags=["vote"], status_code=201)
def cast_vote(
    body: VoteCastIn,
    mgr: VoteManager = Depends(get_vote_manager),
) -> VoteCastOut:
    """투표 행사."""
    try:
        result = mgr.cast_vote(
            user_id=body.user_id,
            restaurant_id=body.restaurant_id,
            vote_date=_parse_date_opt(body.vote_date),
            admin_override=body.admin_override,
        )
        vote = result["vote"]
        return VoteCastOut(
            status=result["status"],
            vote_id=vote.id,
            restaurant_id=vote.restaurant_id,
            warning=result.get("warning"),
        )
    except VoteError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/vote/veto", response_model=VetoOut, tags=["vote"], status_code=201)
def cast_veto(
    body: VetoIn,
    mgr: VoteManager = Depends(get_vote_manager),
) -> VetoOut:
    """거부권 행사."""
    try:
        veto = mgr.cast_veto(
            user_id=body.user_id,
            restaurant_id=body.restaurant_id,
            reason=body.reason,
            veto_date=_parse_date_opt(body.veto_date),
        )
        return VetoOut(**veto.to_dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/vote/status", response_model=VoteStatusOut, tags=["vote"])
def get_vote_status(
    team_id: str = Query(...),
    vote_date: Optional[str] = Query(None),
    mgr: VoteManager = Depends(get_vote_manager),
) -> VoteStatusOut:
    """현재 투표 현황."""
    status = mgr.get_current_status(team_id, _parse_date_opt(vote_date))
    return VoteStatusOut(**status)


@app.post("/api/vote/close", response_model=VoteCloseOut, tags=["vote"])
def close_vote_session(
    body: VoteCloseIn,
    mgr: VoteManager = Depends(get_vote_manager),
) -> VoteCloseOut:
    """투표 마감 및 결과 확정."""
    try:
        result = mgr.close_session(body.team_id, _parse_date_opt(body.vote_date))
        return VoteCloseOut(
            winner=result["winner"],
            total_votes=result.get("total_votes", 0),
            participation_rate=result.get("participation_rate", 0.0),
            finalized_at=result.get("finalized_at"),
            warning=result.get("warning"),
        )
    except VoteError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/vote/history", tags=["vote"])
def get_vote_history(
    team_id: str = Query(...),
    days: int = Query(30, ge=1, le=365),
    mgr: VoteManager = Depends(get_vote_manager),
) -> list[dict]:
    """최근 N일 투표 이력."""
    return mgr.get_vote_history(team_id, days=days)


# =============================================================================
# History & Preference 엔드포인트
# =============================================================================
@app.get("/api/history/visits", response_model=list[RecentVisitItem], tags=["history"])
def get_recent_visits(
    team_id: str = Query(...),
    days: int = Query(10, ge=1, le=90),
    tracker: VisitTracker = Depends(get_visit_tracker),
) -> list[RecentVisitItem]:
    """최근 N 영업일 방문 기록."""
    visits = tracker.get_recent_visits(team_id, days=days)
    return [RecentVisitItem(**v) for v in visits]


@app.get("/api/history/frequency", tags=["history"])
def get_visit_frequency(
    team_id: str = Query(...),
    days: int = Query(30, ge=1, le=365),
    tracker: VisitTracker = Depends(get_visit_tracker),
) -> dict:
    """음식점별 방문 빈도."""
    return tracker.get_visit_frequency(team_id, days=days)


@app.get("/api/history/preference", response_model=PreferenceOut, tags=["history"])
def get_team_preference(
    team_id: str = Query(...),
    days: int = Query(60, ge=1, le=365),
    analyzer: TeamPreferenceAnalyzer = Depends(get_preference_analyzer),
) -> PreferenceOut:
    """팀 선호도 분석 결과."""
    data = analyzer.analyze_team_preference(team_id, days=days)
    return PreferenceOut(**data)


# =============================================================================
# 🎯 통합 추천 엔드포인트 (프로젝트의 핵심)
# =============================================================================
@app.get(
    "/api/recommend",
    response_model=list[RecommendationOut],
    tags=["recommend"],
    summary="🎯 4축 통합 최종 추천",
)
def get_composite_recommendations(
    team_id: str = Query(..., description="팀 ID"),
    user_id: str = Query(..., description="사용자 ID (영양 개인화용)"),
    top_n: int = Query(5, ge=1, le=20),
) -> list[RecommendationOut]:
    """
    **4개 축 통합 최종 추천** (Mini 의 핵심 엔드포인트).

    거리 × 날씨 × 영양 × 팀 → 종합 점수 기반 랭킹.
    """
    with get_session() as session:
        recommender = LunchRecommender(session, team_id=team_id, user_id=user_id)
        results = recommender.get_recommendations(top_n=top_n)
    return [RecommendationOut(**r) for r in results]


@app.get(
    "/api/recommend/{restaurant_id}/explain",
    tags=["recommend"],
    summary="특정 음식점 추천 이유 설명",
)
def explain_recommendation(
    restaurant_id: str,
    team_id: str = Query(...),
    user_id: str = Query(...),
) -> dict:
    """특정 음식점의 4축 점수 및 추천 이유 상세."""
    with get_session() as session:
        recommender = LunchRecommender(session, team_id=team_id, user_id=user_id)
        result = recommender.explain_recommendation(restaurant_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# =============================================================================
# Users (Phase 3 follow-up)
# =============================================================================
class UserOut(BaseModel):
    id: str
    name: str
    team_id: str
    avatar_emoji: str = "🧑‍💻"
    dislike_categories: Optional[str] = None
    allergy_info: Optional[str] = None
    is_active: bool = True


class UserCreateIn(BaseModel):
    id: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=50)
    team_id: str = Field(default="team1")
    avatar_emoji: str = "🧑‍💻"


class UserPrefsIn(BaseModel):
    dislike_categories: Optional[str] = None
    allergy_info: Optional[str] = None
    avatar_emoji: Optional[str] = None
    name: Optional[str] = None


@app.get("/api/users", response_model=list[UserOut], tags=["users"])
def list_users(
    team_id: Optional[str] = Query(None),
) -> list[UserOut]:
    """List all users (optionally scoped to a team)."""
    from sqlalchemy import select
    from database.models import User
    with get_session() as session:
        stmt = select(User).where(User.is_active.is_(True))
        if team_id:
            stmt = stmt.where(User.team_id == team_id)
        rows = session.execute(stmt).scalars().all()
        return [UserOut(**r.to_dict()) for r in rows]


@app.get("/api/users/{user_id}", response_model=UserOut, tags=["users"])
def get_user(user_id: str) -> UserOut:
    from database.models import User
    with get_session() as session:
        user = session.get(User, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return UserOut(**user.to_dict())


@app.post(
    "/api/users",
    response_model=UserOut,
    tags=["users"],
    status_code=201,
)
def create_user(body: UserCreateIn) -> UserOut:
    """Create or reactivate a user account. Idempotent on `id`."""
    from database.models import Team, User
    with get_session() as session:
        existing = session.get(User, body.id)
        if existing is not None:
            existing.is_active = True
            existing.name = body.name
            existing.avatar_emoji = body.avatar_emoji
            session.commit()
            return UserOut(**existing.to_dict())

        # Ensure team exists
        team = session.get(Team, body.team_id)
        if team is None:
            team = Team(id=body.team_id, name=body.team_id)
            session.add(team)

        user = User(
            id=body.id,
            name=body.name,
            team_id=body.team_id,
            avatar_emoji=body.avatar_emoji,
            is_active=True,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return UserOut(**user.to_dict())


@app.patch("/api/users/{user_id}/preferences", response_model=UserOut, tags=["users"])
def update_user_preferences(user_id: str, body: UserPrefsIn) -> UserOut:
    """Persist frontend `UserPreferences` to the DB (select fields)."""
    from database.models import User
    with get_session() as session:
        user = session.get(User, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        if body.dislike_categories is not None:
            user.dislike_categories = body.dislike_categories
        if body.allergy_info is not None:
            user.allergy_info = body.allergy_info
        if body.avatar_emoji is not None:
            user.avatar_emoji = body.avatar_emoji
        if body.name is not None:
            user.name = body.name
        session.commit()
        session.refresh(user)
        return UserOut(**user.to_dict())


# =============================================================================
# Notifications (Phase 3 follow-up) — Slack / webhook
# =============================================================================
class SlackNotifyIn(BaseModel):
    webhook_url: Optional[str] = Field(
        None,
        description="Override webhook URL. If None, uses SLACK_WEBHOOK_URL env var.",
    )
    event: str = Field(
        description="Event name: 'vote_result' | 'weekly_report' | 'custom'",
    )
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=2000)
    emoji: str = "🍱"


class SlackNotifyOut(BaseModel):
    sent: bool
    status_code: Optional[int] = None
    error: Optional[str] = None


@app.post(
    "/api/notify/slack",
    response_model=SlackNotifyOut,
    tags=["notifications"],
)
def notify_slack(body: SlackNotifyIn) -> SlackNotifyOut:
    """
    Post a message to a Slack incoming webhook.

    The webhook URL is taken from the request body or the SLACK_WEBHOOK_URL
    env var. Failures are reported as `sent=false` instead of raising, so the
    caller (usually a React button or a vote-close hook) can show a toast.
    """
    import os
    import requests

    url = body.webhook_url or os.getenv("SLACK_WEBHOOK_URL", "")
    if not url:
        return SlackNotifyOut(sent=False, error="SLACK_WEBHOOK_URL not configured")

    payload = {
        "text": f"{body.emoji} *{body.title}*\n{body.body}",
        "username": "Mini Lunch Optimizer",
        "icon_emoji": body.emoji,
    }
    try:
        resp = requests.post(url, json=payload, timeout=5)
        return SlackNotifyOut(
            sent=resp.ok,
            status_code=resp.status_code,
            error=None if resp.ok else resp.text[:200],
        )
    except Exception as e:
        logger.warning(f"slack notify failed: {e}")
        return SlackNotifyOut(sent=False, error=str(e))


# =============================================================================
# Team Chat — WebSocket + REST
# =============================================================================
class ChatConnectionManager:
    """팀별 WebSocket 연결 관리."""

    def __init__(self):
        self.active: dict[str, list[WebSocket]] = {}

    async def connect(self, team_id: str, ws: WebSocket):
        await ws.accept()
        self.active.setdefault(team_id, []).append(ws)

    def disconnect(self, team_id: str, ws: WebSocket):
        conns = self.active.get(team_id, [])
        if ws in conns:
            conns.remove(ws)

    async def broadcast(self, team_id: str, data: dict):
        for ws in self.active.get(team_id, []):
            try:
                await ws.send_json(data)
            except Exception:
                pass


chat_manager = ChatConnectionManager()


@app.websocket("/ws/chat/{team_id}")
async def ws_chat(ws: WebSocket, team_id: str):
    """팀 채팅 WebSocket. JSON 메시지: {user_id, user_name, avatar_emoji, message}"""
    import json as _json
    from database.models import ChatMessage as ChatMsg

    await chat_manager.connect(team_id, ws)
    try:
        while True:
            raw = await ws.receive_text()
            try:
                data = _json.loads(raw)
            except _json.JSONDecodeError:
                continue

            user_id = data.get("user_id", "")
            user_name = data.get("user_name", "")
            avatar_emoji = data.get("avatar_emoji", "🧑‍💻")
            message = data.get("message", "").strip()
            if not message:
                continue

            # DB 저장
            with get_session() as session:
                msg = ChatMsg(
                    team_id=team_id,
                    user_id=user_id,
                    user_name=user_name,
                    avatar_emoji=avatar_emoji,
                    message=message,
                )
                session.add(msg)
                session.commit()
                session.refresh(msg)
                saved = msg.to_dict()

            # 같은 팀에 broadcast
            await chat_manager.broadcast(team_id, saved)
    except WebSocketDisconnect:
        chat_manager.disconnect(team_id, ws)
    except Exception:
        chat_manager.disconnect(team_id, ws)


class ChatMessageOut(BaseModel):
    id: int
    team_id: str
    user_id: str
    user_name: str
    avatar_emoji: str
    message: str
    created_at: Optional[str] = None


class ChatMessageIn(BaseModel):
    """REST 폴링 기반 팀 채팅의 메시지 입력 스키마.

    WebSocket 핸들러와 동일한 필드를 받지만 HTTPS POST 로 처리.
    Cloudflare 터널·정적 호스팅 환경에서 WS 핸드셰이크가 실패하는 경우의 대안.
    """
    team_id: str
    user_id: str
    user_name: str
    avatar_emoji: Optional[str] = "🧑‍💻"
    message: str = Field(min_length=1, max_length=500)


@app.get("/api/chat/messages", response_model=list[ChatMessageOut], tags=["chat"])
def list_chat_messages(
    team_id: str = Query(...),
    limit: int = Query(50, ge=1, le=200),
):
    """최근 채팅 메시지 조회 (초기 로드용·폴링 기반 채팅용)."""
    from sqlalchemy import select
    from database.models import ChatMessage as ChatMsg

    with get_session() as session:
        stmt = (
            select(ChatMsg)
            .where(ChatMsg.team_id == team_id)
            .order_by(ChatMsg.created_at.desc())
            .limit(limit)
        )
        rows = session.execute(stmt).scalars().all()
        return [ChatMessageOut(**r.to_dict()) for r in reversed(rows)]


@app.post(
    "/api/chat/messages",
    response_model=ChatMessageOut,
    status_code=201,
    tags=["chat"],
)
def post_chat_message(body: ChatMessageIn) -> ChatMessageOut:
    """REST 폴링 기반 채팅 메시지 전송.

    WebSocket 핸들러(`/ws/chat/{team_id}`)와 동일한 chat_messages 테이블에 기록.
    프런트는 GET /api/chat/messages 폴링으로 다른 사용자 메시지를 수신.
    """
    from database.models import ChatMessage as ChatMsg

    msg_text = body.message.strip()
    if not msg_text:
        raise HTTPException(status_code=400, detail="empty message")

    with get_session() as session:
        msg = ChatMsg(
            team_id=body.team_id,
            user_id=body.user_id,
            user_name=body.user_name,
            avatar_emoji=body.avatar_emoji or "🧑‍💻",
            message=msg_text,
        )
        session.add(msg)
        session.commit()
        session.refresh(msg)
        saved = msg.to_dict()

    # 기존 WS 연결자가 있으면 그쪽도 broadcast (REST + WS 혼용 환경 호환)
    try:
        import asyncio
        coro = chat_manager.broadcast(body.team_id, saved)
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(coro)
            else:
                loop.run_until_complete(coro)
        except RuntimeError:
            asyncio.run(coro)
    except Exception:
        pass

    return ChatMessageOut(**saved)


# =============================================================================
# Buddy (밥친구 찾기)
# =============================================================================

class BuddyPostIn(BaseModel):
    team_id: str
    author_id: str
    restaurant_id: Optional[str] = None
    restaurant_name: str
    meal_date: Optional[str] = None  # ISO date, defaults to today
    meal_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    max_buddies: int = Field(3, ge=1, le=10)
    message: Optional[str] = Field(None, max_length=200)


class BuddyJoinerOut(BaseModel):
    user_id: str
    user_name: str
    avatar_emoji: str
    joined_at: Optional[str] = None


class BuddyPostOut(BaseModel):
    id: int
    team_id: str
    author_id: str
    author_name: Optional[str] = None
    author_avatar: Optional[str] = None
    restaurant_id: Optional[str] = None
    restaurant_name: str
    meal_date: str
    meal_time: str
    max_buddies: int
    current_buddies: int = 0
    message: Optional[str] = None
    status: str
    joiners: list[BuddyJoinerOut] = Field(default_factory=list)
    created_at: Optional[str] = None


class BuddyJoinIn(BaseModel):
    user_id: str


class BuddyJoinResult(BaseModel):
    status: str   # "joined" | "already_joined" | "full" | "closed"
    post_id: int
    current_buddies: int


class BuddyStatusIn(BaseModel):
    author_id: str
    status: str = Field(..., pattern=r"^(closed|cancelled)$")


def _build_buddy_post_out(post, session) -> BuddyPostOut:
    """BuddyPost ORM → BuddyPostOut 변환 (author 이름 + joiners 포함)."""
    from database.models import User, BuddyJoin
    from sqlalchemy import select
    from datetime import datetime as _dt

    # author 정보
    author = session.get(User, post.author_id)
    author_name = author.name if author else post.author_id
    author_avatar = author.avatar_emoji if author else "🧑‍💻"

    # joiners
    stmt = (
        select(BuddyJoin, User)
        .outerjoin(User, BuddyJoin.user_id == User.id)
        .where(BuddyJoin.post_id == post.id)
        .order_by(BuddyJoin.joined_at)
    )
    rows = session.execute(stmt).all()
    joiners = [
        BuddyJoinerOut(
            user_id=j.user_id,
            user_name=u.name if u else j.user_id,
            avatar_emoji=u.avatar_emoji if u else "🧑‍💻",
            joined_at=j.joined_at.isoformat() if j.joined_at else None,
        )
        for j, u in rows
    ]

    # expired 계산: 오늘 날짜이고 meal_time 이 지났으면
    status = post.status
    if status == "open":
        try:
            meal_dt = _dt.combine(
                post.meal_date,
                _dt.strptime(post.meal_time, "%H:%M").time()
            )
            if _dt.now() > meal_dt:
                status = "expired"
        except Exception:
            pass

    return BuddyPostOut(
        id=post.id,
        team_id=post.team_id,
        author_id=post.author_id,
        author_name=author_name,
        author_avatar=author_avatar,
        restaurant_id=post.restaurant_id,
        restaurant_name=post.restaurant_name,
        meal_date=post.meal_date.isoformat() if post.meal_date else "",
        meal_time=post.meal_time,
        max_buddies=post.max_buddies,
        current_buddies=len(joiners),
        message=post.message,
        status=status,
        joiners=joiners,
        created_at=post.created_at.isoformat() if post.created_at else None,
    )


@app.post("/api/buddy/posts", response_model=BuddyPostOut, tags=["buddy"], status_code=201)
def create_buddy_post(body: BuddyPostIn):
    """밥친구 모집글 생성. 하루 최대 2개 open 상태 제한."""
    from sqlalchemy import select, func
    from database.models import BuddyPost

    target_date = date.fromisoformat(body.meal_date) if body.meal_date else date.today()

    with get_session() as session:
        # 하루 open 포스트 제한 (2개)
        cnt = session.execute(
            select(func.count())
            .select_from(BuddyPost)
            .where(
                BuddyPost.author_id == body.author_id,
                BuddyPost.meal_date == target_date,
                BuddyPost.status.in_(["open", "full"]),
            )
        ).scalar() or 0
        if cnt >= 2:
            raise HTTPException(400, "하루에 최대 2개의 모집글만 작성할 수 있습니다.")

        post = BuddyPost(
            team_id=body.team_id,
            author_id=body.author_id,
            restaurant_id=body.restaurant_id,
            restaurant_name=body.restaurant_name,
            meal_date=target_date,
            meal_time=body.meal_time,
            max_buddies=body.max_buddies,
            message=body.message,
        )
        session.add(post)
        session.commit()
        session.refresh(post)
        out = _build_buddy_post_out(post, session)

    return out


@app.get("/api/buddy/posts", response_model=list[BuddyPostOut], tags=["buddy"])
def list_buddy_posts(
    team_id: str = Query(...),
    date_str: Optional[str] = Query(None, alias="date"),
    status_filter: Optional[str] = Query(None, alias="status"),
):
    """팀의 밥친구 모집글 목록 (기본: 오늘)."""
    from sqlalchemy import select
    from database.models import BuddyPost

    target_date = date.fromisoformat(date_str) if date_str else date.today()

    with get_session() as session:
        stmt = (
            select(BuddyPost)
            .where(BuddyPost.team_id == team_id, BuddyPost.meal_date == target_date)
            .order_by(BuddyPost.meal_time, BuddyPost.created_at)
        )
        if status_filter:
            stmt = stmt.where(BuddyPost.status == status_filter)

        posts = session.execute(stmt).scalars().all()
        return [_build_buddy_post_out(p, session) for p in posts]


@app.get("/api/buddy/posts/{post_id}", response_model=BuddyPostOut, tags=["buddy"])
def get_buddy_post(post_id: int):
    """단일 모집글 상세."""
    from database.models import BuddyPost

    with get_session() as session:
        post = session.get(BuddyPost, post_id)
        if not post:
            raise HTTPException(404, "모집글을 찾을 수 없습니다.")
        return _build_buddy_post_out(post, session)


@app.post(
    "/api/buddy/posts/{post_id}/join",
    response_model=BuddyJoinResult,
    tags=["buddy"],
    status_code=201,
)
async def join_buddy_post(post_id: int, body: BuddyJoinIn):
    """밥친구 참여. 정원 도달 시 자동 마감 + WebSocket 알림."""
    from sqlalchemy import select, func
    from database.models import BuddyPost, BuddyJoin, User

    with get_session() as session:
        post = session.get(BuddyPost, post_id)
        if not post:
            raise HTTPException(404, "모집글을 찾을 수 없습니다.")
        if post.status not in ("open",):
            return BuddyJoinResult(status=post.status, post_id=post_id, current_buddies=0)
        if body.user_id == post.author_id:
            raise HTTPException(400, "본인의 모집글에는 참여할 수 없습니다.")

        # 중복 체크
        existing = session.execute(
            select(BuddyJoin).where(
                BuddyJoin.post_id == post_id,
                BuddyJoin.user_id == body.user_id,
            )
        ).scalar_one_or_none()
        if existing:
            cnt = session.execute(
                select(func.count()).select_from(BuddyJoin)
                .where(BuddyJoin.post_id == post_id)
            ).scalar() or 0
            return BuddyJoinResult(status="already_joined", post_id=post_id, current_buddies=cnt)

        # 정원 체크
        current_cnt = session.execute(
            select(func.count()).select_from(BuddyJoin)
            .where(BuddyJoin.post_id == post_id)
        ).scalar() or 0
        if current_cnt >= post.max_buddies:
            post.status = "full"
            session.commit()
            return BuddyJoinResult(status="full", post_id=post_id, current_buddies=current_cnt)

        # 참여
        join_rec = BuddyJoin(post_id=post_id, user_id=body.user_id)
        session.add(join_rec)
        new_cnt = current_cnt + 1
        if new_cnt >= post.max_buddies:
            post.status = "full"
        session.commit()

        # 참여자 정보 조회
        user = session.get(User, body.user_id)
        user_name = user.name if user else body.user_id
        user_avatar = user.avatar_emoji if user else "🧑‍💻"

    # WebSocket 알림
    await chat_manager.broadcast(post.team_id, {
        "type": "buddy_event",
        "event": "buddy_joined",
        "post_id": post_id,
        "data": {
            "user_id": body.user_id,
            "user_name": user_name,
            "avatar_emoji": user_avatar,
            "current_buddies": new_cnt,
            "status": post.status,
        },
    })

    return BuddyJoinResult(status="joined", post_id=post_id, current_buddies=new_cnt)


@app.delete("/api/buddy/posts/{post_id}/join", tags=["buddy"])
async def leave_buddy_post(
    post_id: int,
    user_id: str = Query(...),
):
    """밥친구 참여 취소."""
    from sqlalchemy import select, func
    from database.models import BuddyPost, BuddyJoin

    with get_session() as session:
        post = session.get(BuddyPost, post_id)
        if not post:
            raise HTTPException(404, "모집글을 찾을 수 없습니다.")

        existing = session.execute(
            select(BuddyJoin).where(
                BuddyJoin.post_id == post_id,
                BuddyJoin.user_id == user_id,
            )
        ).scalar_one_or_none()
        if not existing:
            raise HTTPException(404, "참여 기록이 없습니다.")

        session.delete(existing)

        # full → open 복귀
        if post.status == "full":
            post.status = "open"

        session.commit()

        remaining = session.execute(
            select(func.count()).select_from(BuddyJoin)
            .where(BuddyJoin.post_id == post_id)
        ).scalar() or 0

    # WebSocket 알림
    await chat_manager.broadcast(post.team_id, {
        "type": "buddy_event",
        "event": "buddy_left",
        "post_id": post_id,
        "data": {"user_id": user_id, "current_buddies": remaining, "status": post.status},
    })

    return {"status": "left", "post_id": post_id, "current_buddies": remaining}


@app.patch("/api/buddy/posts/{post_id}", response_model=BuddyPostOut, tags=["buddy"])
async def update_buddy_post_status(post_id: int, body: BuddyStatusIn):
    """모집글 상태 변경 (작성자만 close/cancel 가능)."""
    from database.models import BuddyPost

    with get_session() as session:
        post = session.get(BuddyPost, post_id)
        if not post:
            raise HTTPException(404, "모집글을 찾을 수 없습니다.")
        if post.author_id != body.author_id:
            raise HTTPException(403, "작성자만 상태를 변경할 수 있습니다.")
        if post.status in ("closed", "cancelled"):
            raise HTTPException(400, f"이미 {post.status} 상태입니다.")

        post.status = body.status
        session.commit()
        session.refresh(post)
        out = _build_buddy_post_out(post, session)

    # WebSocket 알림
    await chat_manager.broadcast(post.team_id, {
        "type": "buddy_event",
        "event": f"buddy_{body.status}",
        "post_id": post_id,
        "data": {"status": body.status},
    })

    return out


# =============================================================================
# Dev: 직접 실행
# =============================================================================
if __name__ == "__main__":
    import uvicorn

    logging.basicConfig(
        level=settings.logging.level,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    uvicorn.run(
        "api.main:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=False,
    )

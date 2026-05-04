"""
SQLAlchemy ORM 모델 (SQLAlchemy 2.0 스타일).

Subtopic 1 에서는 `Restaurant` 만 정의합니다.
Subtopic 2~4 가 진행되면서 WeatherLog, NutritionInfo, MealHistory, User, Vote 등이 추가됩니다.
NLP 레이어는 본 모델의 테이블에 컬럼을 알터(ALTER)하여 확장합니다.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Boolean, Date, DateTime, Float, ForeignKey, Index,
    Integer, String, Text, UniqueConstraint
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """모든 모델의 공통 베이스."""
    pass


# =============================================================================
# Restaurant
# =============================================================================
class Restaurant(Base):
    """
    음식점 마스터.

    Subtopic 1 (카카오 API) 로 수집되며, 이후 Subtopic 2/3/4 · NLP 레이어가
    본 테이블을 조인·확장한다.
    """
    __tablename__ = "restaurants"

    # 기본 정보 — id 는 카카오 place id (string)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    sub_category: Mapped[Optional[str]] = mapped_column(String(50))
    menu_type: Mapped[Optional[str]] = mapped_column(String(50), index=True)

    # 위치
    address: Mapped[Optional[str]] = mapped_column(String(200))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)

    # 거리·점수
    distance_m: Mapped[int] = mapped_column(Integer, index=True, default=0)
    distance_score: Mapped[int] = mapped_column(Integer, default=0)

    # 메타
    place_url: Mapped[Optional[str]] = mapped_column(String(300))
    indoor: Mapped[bool] = mapped_column(Boolean, default=True)
    price_avg: Mapped[Optional[int]] = mapped_column(Integer)
    rating: Mapped[Optional[float]] = mapped_column(Float)

    # 방문 이력 (Subtopic 4 에서 활용)
    visit_count: Mapped[int] = mapped_column(Integer, default=0)
    last_visit_date: Mapped[Optional[date]] = mapped_column(Date)

    # 활성화 플래그 (사라진 음식점 비활성화)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    # 영업 시간대 — 헤비 옵션 (다중 식사 시간 지원)
    # 모르면 True (=허용) 으로 기본값. ETL 이 영업시간 정보를 알게 되면 정확히 갱신.
    serves_breakfast: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    serves_lunch: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    serves_dinner: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # 타임스탬프
    collected_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    __table_args__ = (
        Index("idx_restaurant_location", "lat", "lng"),
        Index("idx_restaurant_active_distance", "is_active", "distance_m"),
    )

    def __repr__(self) -> str:
        return (
            f"<Restaurant(id={self.id!r}, name={self.name!r}, "
            f"category={self.category!r}, distance={self.distance_m}m, "
            f"score={self.distance_score}, active={self.is_active})>"
        )

    def to_dict(self) -> dict:
        """JSON 직렬화."""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "sub_category": self.sub_category,
            "menu_type": self.menu_type,
            "address": self.address,
            "phone": self.phone,
            "lat": self.lat,
            "lng": self.lng,
            "distance_m": self.distance_m,
            "distance_score": self.distance_score,
            "place_url": self.place_url,
            "indoor": self.indoor,
            "price_avg": self.price_avg,
            "rating": self.rating,
            "visit_count": self.visit_count,
            "last_visit_date": self.last_visit_date.isoformat() if self.last_visit_date else None,
            "is_active": self.is_active,
            "serves_breakfast": bool(self.serves_breakfast),
            "serves_lunch": bool(self.serves_lunch),
            "serves_dinner": bool(self.serves_dinner),
            "collected_at": self.collected_at.isoformat() if self.collected_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# =============================================================================
# WeatherLog (Subtopic 2)
# =============================================================================
class WeatherLog(Base):
    """
    시간별 날씨·대기질 이력.
    """
    __tablename__ = "weather_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )

    # 기상청 초단기실황
    temp: Mapped[Optional[float]] = mapped_column(Float)
    humidity: Mapped[Optional[int]] = mapped_column(Integer)
    rain_type: Mapped[Optional[int]] = mapped_column(Integer)
    rain_type_str: Mapped[Optional[str]] = mapped_column(String(20))
    rain_1h: Mapped[Optional[float]] = mapped_column(Float)
    wind_speed: Mapped[Optional[float]] = mapped_column(Float)

    # 기상청 단기예보
    sky: Mapped[Optional[int]] = mapped_column(Integer)
    sky_str: Mapped[Optional[str]] = mapped_column(String(20))
    pop: Mapped[Optional[int]] = mapped_column(Integer)  # 강수확률
    tmn: Mapped[Optional[float]] = mapped_column(Float)
    tmx: Mapped[Optional[float]] = mapped_column(Float)

    # 에어코리아
    pm10: Mapped[Optional[int]] = mapped_column(Integer)
    pm25: Mapped[Optional[int]] = mapped_column(Integer)
    dust_grade: Mapped[Optional[str]] = mapped_column(String(20))

    # 종합
    outdoor_comfort: Mapped[Optional[str]] = mapped_column(String(20))

    def __repr__(self) -> str:
        return (
            f"<WeatherLog(id={self.id}, temp={self.temp}, "
            f"sky={self.sky_str}, dust={self.dust_grade}, "
            f"comfort={self.outdoor_comfort})>"
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "collected_at": self.collected_at.isoformat() if self.collected_at else None,
            "temp": self.temp,
            "humidity": self.humidity,
            "rain_type": self.rain_type,
            "rain_type_str": self.rain_type_str,
            "rain_1h": self.rain_1h,
            "wind_speed": self.wind_speed,
            "sky": self.sky,
            "sky_str": self.sky_str,
            "pop": self.pop,
            "tmn": self.tmn,
            "tmx": self.tmx,
            "pm10": self.pm10,
            "pm25": self.pm25,
            "dust_grade": self.dust_grade,
            "outdoor_comfort": self.outdoor_comfort,
        }


# =============================================================================
# NutritionInfo (Subtopic 3)
# =============================================================================
class NutritionInfo(Base):
    """
    음식점별 추정 영양 정보 캐시.
    매핑 실패 시에도 match_type='category_avg' 로 저장된다.
    """
    __tablename__ = "nutrition_info"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    restaurant_id: Mapped[str] = mapped_column(
        String(64), index=True, unique=True, nullable=False
    )
    food_name: Mapped[str] = mapped_column(String(100), nullable=False)
    food_code: Mapped[Optional[str]] = mapped_column(String(20))
    match_type: Mapped[str] = mapped_column(String(20), default="category_avg")
    match_score: Mapped[Optional[float]] = mapped_column(Float)

    serving_size: Mapped[float] = mapped_column(Float, default=100.0)
    calories: Mapped[Optional[float]] = mapped_column(Float)
    carbs: Mapped[Optional[float]] = mapped_column(Float)
    protein: Mapped[Optional[float]] = mapped_column(Float)
    fat: Mapped[Optional[float]] = mapped_column(Float)
    sugar: Mapped[Optional[float]] = mapped_column(Float)
    sodium: Mapped[Optional[float]] = mapped_column(Float)

    mapped_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<NutritionInfo(restaurant_id={self.restaurant_id!r}, "
            f"food={self.food_name!r}, match={self.match_type}, "
            f"cal={self.calories})>"
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "restaurant_id": self.restaurant_id,
            "food_name": self.food_name,
            "food_code": self.food_code,
            "match_type": self.match_type,
            "match_score": self.match_score,
            "serving_size": self.serving_size,
            "calories": self.calories,
            "carbs": self.carbs,
            "protein": self.protein,
            "fat": self.fat,
            "sugar": self.sugar,
            "sodium": self.sodium,
            "mapped_at": self.mapped_at.isoformat() if self.mapped_at else None,
        }


# =============================================================================
# MealHistory (Subtopic 3)
# =============================================================================
class MealHistory(Base):
    """
    사용자 식사 기록.
    Subtopic 4 에서 팀 추천 이력과도 연동됨.
    """
    __tablename__ = "meal_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    restaurant_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    meal_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    menu_name: Mapped[Optional[str]] = mapped_column(String(100))

    calories: Mapped[Optional[float]] = mapped_column(Float)
    carbs: Mapped[Optional[float]] = mapped_column(Float)
    protein: Mapped[Optional[float]] = mapped_column(Float)
    fat: Mapped[Optional[float]] = mapped_column(Float)
    sugar: Mapped[Optional[float]] = mapped_column(Float)
    sodium: Mapped[Optional[float]] = mapped_column(Float)

    satisfaction: Mapped[Optional[int]] = mapped_column(Integer)  # 1~5
    raw_text: Mapped[Optional[str]] = mapped_column(Text)
    meal_type: Mapped[Optional[str]] = mapped_column(String(20))
    parsed_items_json: Mapped[Optional[str]] = mapped_column(Text)
    nutrition_source: Mapped[Optional[str]] = mapped_column(String(50))
    match_confidence: Mapped[Optional[float]] = mapped_column(Float)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    restaurant_name_snapshot: Mapped[Optional[str]] = mapped_column(String(100))
    restaurant_place_url: Mapped[Optional[str]] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    items: Mapped[list["MealItem"]] = relationship(
        "MealItem", back_populates="meal", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_meal_user_date", "user_id", "meal_date"),
    )

    def __repr__(self) -> str:
        return (
            f"<MealHistory(user={self.user_id!r}, date={self.meal_date}, "
            f"menu={self.menu_name!r}, cal={self.calories})>"
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "restaurant_id": self.restaurant_id,
            "meal_date": self.meal_date.isoformat() if self.meal_date else None,
            "menu_name": self.menu_name,
            "calories": self.calories,
            "carbs": self.carbs,
            "protein": self.protein,
            "fat": self.fat,
            "sugar": self.sugar,
            "sodium": self.sodium,
            "satisfaction": self.satisfaction,
            "raw_text": self.raw_text,
            "meal_type": self.meal_type,
            "parsed_items_json": self.parsed_items_json,
            "nutrition_source": self.nutrition_source,
            "match_confidence": self.match_confidence,
            "needs_review": self.needs_review,
            "restaurant_name_snapshot": self.restaurant_name_snapshot,
            "restaurant_place_url": self.restaurant_place_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class MealItem(Base):
    """음식별 식사 기록 상세 항목."""

    __tablename__ = "meal_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    meal_history_id: Mapped[int] = mapped_column(
        ForeignKey("meal_history.id", ondelete="CASCADE"), nullable=False, index=True
    )
    raw_name: Mapped[str] = mapped_column(String(100), nullable=False)
    normalized_name: Mapped[Optional[str]] = mapped_column(String(100))
    food_code: Mapped[Optional[str]] = mapped_column(String(50))
    quantity: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), default="serving", nullable=False)
    serving_size: Mapped[Optional[float]] = mapped_column(Float)

    calories: Mapped[Optional[float]] = mapped_column(Float)
    carbs: Mapped[Optional[float]] = mapped_column(Float)
    protein: Mapped[Optional[float]] = mapped_column(Float)
    fat: Mapped[Optional[float]] = mapped_column(Float)
    sugar: Mapped[Optional[float]] = mapped_column(Float)
    sodium: Mapped[Optional[float]] = mapped_column(Float)

    source: Mapped[str] = mapped_column(String(50), default="unverified", nullable=False)
    match_type: Mapped[str] = mapped_column(String(30), default="unverified", nullable=False)
    match_confidence: Mapped[Optional[float]] = mapped_column(Float)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    meal: Mapped[MealHistory] = relationship("MealHistory", back_populates="items")

    __table_args__ = (
        Index("idx_meal_items_meal", "meal_history_id"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "meal_history_id": self.meal_history_id,
            "raw_name": self.raw_name,
            "normalized_name": self.normalized_name,
            "food_code": self.food_code,
            "quantity": self.quantity,
            "unit": self.unit,
            "serving_size": self.serving_size,
            "calories": self.calories,
            "carbs": self.carbs,
            "protein": self.protein,
            "fat": self.fat,
            "sugar": self.sugar,
            "sodium": self.sodium,
            "source": self.source,
            "match_type": self.match_type,
            "match_confidence": self.match_confidence,
            "needs_review": self.needs_review,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# =============================================================================
# Team / User (Subtopic 4)
# =============================================================================
class Team(Base):
    """팀 마스터."""
    __tablename__ = "teams"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    users: Mapped[list["User"]] = relationship(
        "User", back_populates="team", cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name,
                "created_at": self.created_at.isoformat() if self.created_at else None}


class User(Base):
    """사용자 마스터 (팀 소속).

    Phase 13&14 확장:
      - email/password_hash: 자체 JWT 인증 (게스트 호환을 위해 nullable=True)
      - role: "admin" 또는 "user" (RBAC)
      - last_login_at, updated_at: 감사 추적
    """
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    email: Mapped[Optional[str]] = mapped_column(
        String(120), unique=True, nullable=True, index=True
    )
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(
        String(20), default="user", nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    team_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("teams.id"), nullable=False, index=True
    )
    avatar_emoji: Mapped[str] = mapped_column(String(10), default="🧑‍💻")
    dislike_categories: Mapped[Optional[str]] = mapped_column(String(200))
    allergy_info: Mapped[Optional[str]] = mapped_column(String(200))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    team: Mapped["Team"] = relationship("Team", back_populates="users")
    votes: Mapped[list["Vote"]] = relationship(
        "Vote", back_populates="user", cascade="all, delete-orphan"
    )

    def to_dict(self, include_sensitive: bool = False) -> dict:
        data = {
            "id": self.id,
            "email": self.email,
            "role": self.role,
            "name": self.name,
            "team_id": self.team_id,
            "avatar_emoji": self.avatar_emoji,
            "dislike_categories": self.dislike_categories,
            "allergy_info": self.allergy_info,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login_at": (
                self.last_login_at.isoformat() if self.last_login_at else None
            ),
        }
        if include_sensitive:
            data["password_hash"] = self.password_hash
        return data


# =============================================================================
# Vote / VoteSession / Veto
# =============================================================================
class VoteSession(Base):
    """
    일 단위 투표 세션. 하루에 팀당 1개.
    """
    __tablename__ = "vote_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vote_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    team_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("teams.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(20), default="open")  # open/closed/finalized
    open_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    close_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    winner_restaurant_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("restaurants.id")
    )
    total_votes: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    __table_args__ = (
        UniqueConstraint("vote_date", "team_id", name="uq_vote_session_date_team"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "vote_date": self.vote_date.isoformat() if self.vote_date else None,
            "team_id": self.team_id,
            "status": self.status,
            "open_at": self.open_at.isoformat() if self.open_at else None,
            "close_at": self.close_at.isoformat() if self.close_at else None,
            "winner_restaurant_id": self.winner_restaurant_id,
            "total_votes": self.total_votes,
        }


class Vote(Base):
    """
    사용자의 일일 투표. 한 사용자는 하루에 1표만 가능 (UPDATE 가능).
    """
    __tablename__ = "votes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vote_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("users.id"), nullable=False, index=True
    )
    restaurant_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("restaurants.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    __table_args__ = (
        UniqueConstraint("vote_date", "user_id", name="uq_vote_date_user"),
    )

    user: Mapped["User"] = relationship("User", back_populates="votes")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "vote_date": self.vote_date.isoformat() if self.vote_date else None,
            "user_id": self.user_id,
            "restaurant_id": self.restaurant_id,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Veto(Base):
    """
    거부권: "오늘 이 집은 안 가요".
    """
    __tablename__ = "vetoes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    veto_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("users.id"), nullable=False
    )
    restaurant_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("restaurants.id"), nullable=False
    )
    reason: Mapped[Optional[str]] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "veto_date", "user_id", "restaurant_id", name="uq_veto_date_user_rest"
        ),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "veto_date": self.veto_date.isoformat() if self.veto_date else None,
            "user_id": self.user_id,
            "restaurant_id": self.restaurant_id,
            "reason": self.reason,
        }


# =============================================================================
# VisitHistory
# =============================================================================
class VisitHistory(Base):
    """팀의 식당 방문 이력."""
    __tablename__ = "visit_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    visit_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    team_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("teams.id"), nullable=False, index=True
    )
    restaurant_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("restaurants.id"), nullable=False, index=True
    )
    participant_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_satisfaction: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    __table_args__ = (
        Index("idx_visit_team_restaurant", "team_id", "restaurant_id"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "visit_date": self.visit_date.isoformat() if self.visit_date else None,
            "team_id": self.team_id,
            "restaurant_id": self.restaurant_id,
            "participant_count": self.participant_count,
            "avg_satisfaction": self.avg_satisfaction,
        }


# =============================================================================
# ChatMessage (팀 채팅)
# =============================================================================
class ChatMessage(Base):
    """팀 채팅 메시지."""
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    team_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("teams.id"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(String(50), nullable=False)
    user_name: Mapped[str] = mapped_column(String(50), nullable=False)
    avatar_emoji: Mapped[str] = mapped_column(String(10), default="🧑‍💻")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    __table_args__ = (
        Index("idx_chat_team_created", "team_id", "created_at"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "team_id": self.team_id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "avatar_emoji": self.avatar_emoji,
            "message": self.message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# =============================================================================
# BuddyPost / BuddyJoin (밥친구 찾기)
# =============================================================================
class BuddyPost(Base):
    """
    밥친구 모집글.

    팀원이 특정 식당·시간에 함께 먹을 사람을 모집하는 게시글.
    status 흐름: open → full / closed / cancelled (expired 는 조회 시 계산).
    """
    __tablename__ = "buddy_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    team_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("teams.id"), nullable=False, index=True
    )
    author_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("users.id"), nullable=False, index=True
    )

    # 식당 — DB 에 없는 식당도 restaurant_name 으로 자유 입력 가능
    restaurant_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("restaurants.id")
    )
    restaurant_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # 일시
    meal_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    meal_time: Mapped[str] = mapped_column(String(5), nullable=False)  # "HH:MM"

    # 모집 설정
    max_buddies: Mapped[int] = mapped_column(Integer, default=3)  # 작성자 제외
    message: Mapped[Optional[str]] = mapped_column(String(200))

    # 상태
    status: Mapped[str] = mapped_column(String(20), default="open")

    # 타임스탬프
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # relationships
    joins: Mapped[list["BuddyJoin"]] = relationship(
        "BuddyJoin", back_populates="post", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_buddy_post_team_date", "team_id", "meal_date"),
        Index("idx_buddy_post_status", "status"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "team_id": self.team_id,
            "author_id": self.author_id,
            "restaurant_id": self.restaurant_id,
            "restaurant_name": self.restaurant_name,
            "meal_date": self.meal_date.isoformat() if self.meal_date else None,
            "meal_time": self.meal_time,
            "max_buddies": self.max_buddies,
            "message": self.message,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class BuddyJoin(Base):
    """밥친구 참여 기록. post_id + user_id 유니크."""
    __tablename__ = "buddy_joins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("buddy_posts.id"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("users.id"), nullable=False
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # relationship
    post: Mapped["BuddyPost"] = relationship("BuddyPost", back_populates="joins")

    __table_args__ = (
        UniqueConstraint("post_id", "user_id", name="uq_buddy_join_post_user"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "post_id": self.post_id,
            "user_id": self.user_id,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
        }

"""
Restaurant + Weather + Nutrition DB 적재기.

GUIDE Subtopic 1 §5.2 + Subtopic 2 §7 + Subtopic 3 §8 의 명세 구현.
"""
from __future__ import annotations

import logging
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from typing import Any, Optional

import pandas as pd
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from database.models import MealHistory, MealItem, NutritionInfo, Restaurant, WeatherLog

logger = logging.getLogger(__name__)


class RestaurantLoader:
    """
    DataFrame → Restaurant 테이블 UPSERT.

    트랜잭션은 메서드 단위 (전체 성공 or 전체 롤백).
    """

    def __init__(self, session: Session):
        self.session = session

    # -------------------------------------------------------------------------
    # UPSERT
    # -------------------------------------------------------------------------
    def upsert_restaurants(self, df: pd.DataFrame) -> dict[str, int]:
        """
        DataFrame 의 음식점 데이터를 UPSERT.

        업데이트 시 갱신되는 필드:
            distance_m, distance_score, collected_at, is_active

        삽입 시 모든 필드 채움.

        Returns:
            {"inserted": int, "updated": int, "skipped": int}
        """
        stats = {"inserted": 0, "updated": 0, "skipped": 0}

        if df is None or df.empty:
            logger.info("upsert_restaurants() called with empty df")
            return stats

        try:
            now = datetime.utcnow()
            for _, row in df.iterrows():
                rid = str(row.get("id", "")).strip()
                if not rid:
                    stats["skipped"] += 1
                    continue

                existing = self.session.get(Restaurant, rid)
                if existing is None:
                    new_restaurant = Restaurant(
                        id=rid,
                        name=row.get("name") or "",
                        category=row.get("category"),
                        sub_category=row.get("sub_category"),
                        menu_type=row.get("menu_type"),
                        address=row.get("address"),
                        phone=row.get("phone"),
                        lat=float(row.get("lat") or 0.0),
                        lng=float(row.get("lng") or 0.0),
                        distance_m=int(row.get("distance_m") or 0),
                        distance_score=int(row.get("distance_score") or 0),
                        place_url=row.get("place_url"),
                        indoor=True,
                        collected_at=now,
                        is_active=True,
                    )
                    self.session.add(new_restaurant)
                    stats["inserted"] += 1
                else:
                    # 업데이트: 변동성 높은 필드만
                    existing.distance_m = int(row.get("distance_m") or 0)
                    existing.distance_score = int(row.get("distance_score") or 0)
                    existing.collected_at = now
                    existing.is_active = True
                    stats["updated"] += 1

            self.session.commit()
            logger.info("upsert_restaurants done: %s", stats)
            return stats
        except Exception as e:
            self.session.rollback()
            logger.exception("upsert_restaurants failed, rolled back: %s", e)
            raise

    # -------------------------------------------------------------------------
    # 사라진 음식점 비활성화
    # -------------------------------------------------------------------------
    def deactivate_missing(self, active_ids: list[str]) -> int:
        """
        active_ids 에 없는 모든 활성 음식점을 비활성화.

        Returns:
            비활성화된 건수
        """
        if not active_ids:
            return 0
        try:
            stmt = select(Restaurant).where(
                Restaurant.is_active == True,  # noqa: E712
                ~Restaurant.id.in_(active_ids),
            )
            to_deactivate = self.session.execute(stmt).scalars().all()
            count = 0
            for r in to_deactivate:
                r.is_active = False
                count += 1
            self.session.commit()
            if count > 0:
                logger.info("deactivate_missing: %d restaurants deactivated", count)
            return count
        except Exception as e:
            self.session.rollback()
            logger.exception("deactivate_missing failed: %s", e)
            raise

    # -------------------------------------------------------------------------
    # 조회
    # -------------------------------------------------------------------------
    def get_active_restaurants(
        self,
        category: Optional[str] = None,
        min_score: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> list[Restaurant]:
        """활성 음식점 조회 (거리순)."""
        stmt = select(Restaurant).where(Restaurant.is_active == True)  # noqa: E712
        if category:
            stmt = stmt.where(Restaurant.category == category)
        if min_score is not None:
            stmt = stmt.where(Restaurant.distance_score >= min_score)
        stmt = stmt.order_by(Restaurant.distance_m.asc())
        if limit is not None and limit > 0:
            stmt = stmt.limit(limit)
        return list(self.session.execute(stmt).scalars().all())

    def get_by_id(self, restaurant_id: str) -> Optional[Restaurant]:
        return self.session.get(Restaurant, restaurant_id)

    def list_nearby(
        self,
        lat: float,
        lng: float,
        radius_m: int = 800,
        limit: int = 50,
        category: Optional[str] = None,
    ) -> list[tuple[Restaurant, int]]:
        """
        사용자 좌표 기준으로 활성 음식점을 근접 순으로 조회.

        Haversine 거리를 Python-side 에서 계산합니다. SQLite 는 기본적으로
        sin/cos/radians 함수를 제공하지 않아 SQL 단에서 계산하기 번거롭고,
        현재 데이터량(< 수천 건) 에서 Python 계산이 훨씬 단순·안전합니다.

        Args:
            lat, lng: 사용자 현재 좌표
            radius_m: 반경 (미터). 이 이내만 반환.
            limit: 반환 최대 개수
            category: 선택적 카테고리 필터

        Returns:
            [(Restaurant, distance_m_int), ...]  — 거리 오름차순
        """
        import math

        stmt = select(Restaurant).where(Restaurant.is_active == True)  # noqa: E712
        if category:
            stmt = stmt.where(Restaurant.category == category)
        rows = list(self.session.execute(stmt).scalars().all())

        # Haversine (WGS84)
        R = 6_371_000.0  # meters
        lat_rad = math.radians(lat)
        lng_rad = math.radians(lng)

        scored: list[tuple[Restaurant, int]] = []
        for r in rows:
            if r.lat is None or r.lng is None:
                continue
            dlat = math.radians(r.lat) - lat_rad
            dlng = math.radians(r.lng) - lng_rad
            a = (
                math.sin(dlat / 2) ** 2
                + math.cos(lat_rad) * math.cos(math.radians(r.lat))
                * math.sin(dlng / 2) ** 2
            )
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            dist = int(round(R * c))
            if dist <= radius_m:
                scored.append((r, dist))

        scored.sort(key=lambda t: t[1])
        return scored[:limit]

    def get_statistics(self) -> dict[str, Any]:
        """
        통계 요약.

        Returns:
            {
              "total": int,
              "active": int,
              "inactive": int,
              "categories": {"한식": 20, "일식": 5, ...},
              "avg_distance_m": float,
              "avg_distance_score": float,
              "last_collected_at": str | None
            }
        """
        total = self.session.execute(
            select(func.count()).select_from(Restaurant)
        ).scalar() or 0

        active = self.session.execute(
            select(func.count()).select_from(Restaurant).where(
                Restaurant.is_active == True  # noqa: E712
            )
        ).scalar() or 0

        # 카테고리 분포
        rows = self.session.execute(
            select(Restaurant.category).where(Restaurant.is_active == True)  # noqa: E712
        ).scalars().all()
        categories = dict(Counter(c for c in rows if c))

        # 평균 거리·점수
        avg_dist = self.session.execute(
            select(func.avg(Restaurant.distance_m)).where(
                Restaurant.is_active == True  # noqa: E712
            )
        ).scalar()
        avg_score = self.session.execute(
            select(func.avg(Restaurant.distance_score)).where(
                Restaurant.is_active == True  # noqa: E712
            )
        ).scalar()

        last_collected = self.session.execute(
            select(func.max(Restaurant.collected_at))
        ).scalar()

        return {
            "total": int(total),
            "active": int(active),
            "inactive": int(total - active),
            "categories": categories,
            "avg_distance_m": float(avg_dist) if avg_dist is not None else None,
            "avg_distance_score": float(avg_score) if avg_score is not None else None,
            "last_collected_at": last_collected.isoformat() if last_collected else None,
        }


# =============================================================================
# WeatherLoader (Subtopic 2)
# =============================================================================
class WeatherLoader:
    """통합 날씨 dict 를 WeatherLog 테이블에 저장·조회."""

    def __init__(self, session: Session):
        self.session = session

    # -------------------------------------------------------------------------
    def save_weather_log(self, weather: dict[str, Any]) -> WeatherLog:
        """통합 날씨 dict → WeatherLog 저장."""
        try:
            log = WeatherLog(
                collected_at=datetime.utcnow(),
                temp=weather.get("temp"),
                humidity=weather.get("humidity"),
                rain_type=weather.get("rain_type"),
                rain_type_str=weather.get("rain_type_str"),
                rain_1h=weather.get("rain_1h"),
                wind_speed=weather.get("wind_speed"),
                sky=weather.get("sky"),
                sky_str=weather.get("sky_str"),
                pop=weather.get("pop"),
                tmn=weather.get("tmn"),
                tmx=weather.get("tmx"),
                pm10=weather.get("pm10"),
                pm25=weather.get("pm25"),
                dust_grade=weather.get("dust_grade"),
                outdoor_comfort=weather.get("outdoor_comfort"),
            )
            self.session.add(log)
            self.session.commit()
            self.session.refresh(log)
            logger.info("WeatherLog saved: %s", log)
            return log
        except Exception as e:
            self.session.rollback()
            logger.exception("save_weather_log failed: %s", e)
            raise

    # -------------------------------------------------------------------------
    def get_latest_weather(self) -> Optional[WeatherLog]:
        stmt = select(WeatherLog).order_by(desc(WeatherLog.collected_at)).limit(1)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_weather_history(self, hours: int = 24) -> list[WeatherLog]:
        since = datetime.utcnow() - timedelta(hours=hours)
        stmt = (
            select(WeatherLog)
            .where(WeatherLog.collected_at >= since)
            .order_by(WeatherLog.collected_at.asc())
        )
        return list(self.session.execute(stmt).scalars().all())

    # -------------------------------------------------------------------------
    def get_today_weather_summary(self) -> dict[str, Any]:
        """오늘 하루 날씨 요약 (UTC 자정 기준)."""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        stmt = select(WeatherLog).where(WeatherLog.collected_at >= today_start)
        rows = list(self.session.execute(stmt).scalars().all())

        if not rows:
            return {
                "avg_temp": None,
                "max_temp": None,
                "min_temp": None,
                "avg_pm10": None,
                "rain_occurred": False,
                "dominant_sky": None,
                "sample_count": 0,
            }

        temps = [r.temp for r in rows if r.temp is not None]
        pm10s = [r.pm10 for r in rows if r.pm10 is not None]
        rain_occurred = any((r.rain_type or 0) != 0 for r in rows)
        sky_counter = Counter(r.sky_str for r in rows if r.sky_str)
        dominant_sky = sky_counter.most_common(1)[0][0] if sky_counter else None

        return {
            "avg_temp": sum(temps) / len(temps) if temps else None,
            "max_temp": max(temps) if temps else None,
            "min_temp": min(temps) if temps else None,
            "avg_pm10": sum(pm10s) / len(pm10s) if pm10s else None,
            "rain_occurred": rain_occurred,
            "dominant_sky": dominant_sky,
            "sample_count": len(rows),
        }


# =============================================================================
# NutritionLoader (Subtopic 3)
# =============================================================================
class NutritionLoader:
    """
    음식점 영양 매핑 (`NutritionInfo`) + 사용자 식사 기록 (`MealHistory`) 관리.
    """

    def __init__(self, session: Session):
        self.session = session

    # -------------------------------------------------------------------------
    # NutritionInfo
    # -------------------------------------------------------------------------
    def save_nutrition_mapping(
        self,
        restaurant_id: str,
        nutrition: dict[str, Any],
        match_type: str = "category_avg",
    ) -> NutritionInfo:
        """
        음식점 → 영양 매핑 UPSERT.
        """
        try:
            existing = self.session.execute(
                select(NutritionInfo).where(NutritionInfo.restaurant_id == restaurant_id)
            ).scalar_one_or_none()

            if existing is None:
                info = NutritionInfo(
                    restaurant_id=restaurant_id,
                    food_name=nutrition.get("food_name") or f"[{match_type}]",
                    food_code=nutrition.get("food_code"),
                    match_type=nutrition.get("match_type") or match_type,
                    match_score=nutrition.get("match_score"),
                    serving_size=float(nutrition.get("serving_size") or 100.0),
                    calories=nutrition.get("calories"),
                    carbs=nutrition.get("carbs"),
                    protein=nutrition.get("protein"),
                    fat=nutrition.get("fat"),
                    sugar=nutrition.get("sugar"),
                    sodium=nutrition.get("sodium"),
                )
                self.session.add(info)
                self.session.commit()
                self.session.refresh(info)
                return info

            # update
            existing.food_name = nutrition.get("food_name") or existing.food_name
            existing.food_code = nutrition.get("food_code")
            existing.match_type = nutrition.get("match_type") or match_type
            existing.match_score = nutrition.get("match_score")
            existing.serving_size = float(nutrition.get("serving_size") or 100.0)
            existing.calories = nutrition.get("calories")
            existing.carbs = nutrition.get("carbs")
            existing.protein = nutrition.get("protein")
            existing.fat = nutrition.get("fat")
            existing.sugar = nutrition.get("sugar")
            existing.sodium = nutrition.get("sodium")
            self.session.commit()
            self.session.refresh(existing)
            return existing
        except Exception as e:
            self.session.rollback()
            logger.exception("save_nutrition_mapping failed: %s", e)
            raise

    def bulk_save_nutrition(
        self,
        mapping: dict[str, dict[str, Any]],
    ) -> dict[str, int]:
        """`{restaurant_id: nutrition_dict}` 를 일괄 저장."""
        stats = {"inserted": 0, "updated": 0, "errors": 0}
        for rid, nutrition in mapping.items():
            try:
                existing = self.get_nutrition_by_restaurant(rid)
                self.save_nutrition_mapping(rid, nutrition)
                if existing is None:
                    stats["inserted"] += 1
                else:
                    stats["updated"] += 1
            except Exception:
                stats["errors"] += 1
        return stats

    def get_nutrition_by_restaurant(
        self, restaurant_id: str
    ) -> Optional[NutritionInfo]:
        return self.session.execute(
            select(NutritionInfo).where(NutritionInfo.restaurant_id == restaurant_id)
        ).scalar_one_or_none()

    def find_nutrition_by_food_name(
        self, food_name: str
    ) -> Optional[NutritionInfo]:
        """로컬 영양 캐시에서 음식명 유사 후보를 찾는다."""
        name = (food_name or "").strip()
        if not name:
            return None
        exact = self.session.execute(
            select(NutritionInfo).where(NutritionInfo.food_name == name)
        ).scalar_one_or_none()
        if exact is not None:
            return exact
        return self.session.execute(
            select(NutritionInfo)
            .where(NutritionInfo.food_name.ilike(f"%{name}%"))
            .order_by(NutritionInfo.match_score.desc().nullslast())
            .limit(1)
        ).scalar_one_or_none()

    # -------------------------------------------------------------------------
    # MealHistory
    # -------------------------------------------------------------------------
    def save_meal_record(self, record: dict[str, Any]) -> MealHistory:
        """식사 기록 INSERT."""
        try:
            meal = MealHistory(
                user_id=str(record["user_id"]),
                restaurant_id=str(record["restaurant_id"]) if record.get("restaurant_id") else None,
                meal_date=record.get("meal_date") or date.today(),
                menu_name=record.get("menu_name"),
                calories=record.get("calories"),
                carbs=record.get("carbs"),
                protein=record.get("protein"),
                fat=record.get("fat"),
                sugar=record.get("sugar"),
                sodium=record.get("sodium"),
                satisfaction=record.get("satisfaction"),
                raw_text=record.get("raw_text"),
                meal_type=record.get("meal_type"),
                parsed_items_json=record.get("parsed_items_json"),
                nutrition_source=record.get("nutrition_source"),
                match_confidence=record.get("match_confidence"),
                needs_review=bool(record.get("needs_review", False)),
                restaurant_name_snapshot=record.get("restaurant_name_snapshot"),
                restaurant_place_url=record.get("restaurant_place_url"),
            )
            self.session.add(meal)
            self.session.commit()
            self.session.refresh(meal)
            return meal
        except Exception as e:
            self.session.rollback()
            logger.exception("save_meal_record failed: %s", e)
            raise

    def save_natural_meal_record(
        self,
        record: dict[str, Any],
        items: list[dict[str, Any]],
    ) -> tuple[MealHistory, list[MealItem]]:
        """자연어 식단 한 끼와 음식별 상세 항목을 같은 트랜잭션으로 저장한다."""
        try:
            meal = MealHistory(
                user_id=str(record["user_id"]),
                restaurant_id=str(record["restaurant_id"]) if record.get("restaurant_id") else None,
                meal_date=record.get("meal_date") or date.today(),
                menu_name=record.get("menu_name"),
                calories=record.get("calories"),
                carbs=record.get("carbs"),
                protein=record.get("protein"),
                fat=record.get("fat"),
                sugar=record.get("sugar"),
                sodium=record.get("sodium"),
                satisfaction=record.get("satisfaction"),
                raw_text=record.get("raw_text"),
                meal_type=record.get("meal_type"),
                parsed_items_json=record.get("parsed_items_json"),
                nutrition_source=record.get("nutrition_source"),
                match_confidence=record.get("match_confidence"),
                needs_review=bool(record.get("needs_review", False)),
                restaurant_name_snapshot=record.get("restaurant_name_snapshot"),
                restaurant_place_url=record.get("restaurant_place_url"),
            )
            self.session.add(meal)
            self.session.flush()

            saved_items: list[MealItem] = []
            for item in items:
                meal_item = MealItem(
                    meal_history_id=meal.id,
                    raw_name=str(item["raw_name"]),
                    normalized_name=item.get("normalized_name"),
                    food_code=item.get("food_code"),
                    quantity=float(item.get("quantity") or 1.0),
                    unit=item.get("unit") or "serving",
                    serving_size=item.get("serving_size"),
                    calories=item.get("calories"),
                    carbs=item.get("carbs"),
                    protein=item.get("protein"),
                    fat=item.get("fat"),
                    sugar=item.get("sugar"),
                    sodium=item.get("sodium"),
                    source=item.get("source") or "unverified",
                    match_type=item.get("match_type") or "unverified",
                    match_confidence=item.get("match_confidence"),
                    needs_review=bool(item.get("needs_review", True)),
                )
                self.session.add(meal_item)
                saved_items.append(meal_item)

            self.session.commit()
            self.session.refresh(meal)
            for item in saved_items:
                self.session.refresh(item)
            return meal, saved_items
        except Exception as e:
            self.session.rollback()
            logger.exception("save_natural_meal_record failed: %s", e)
            raise

    def list_meal_records(
        self,
        user_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 30,
    ) -> list[MealHistory]:
        """사용자 식사 기록을 최신순으로 조회한다."""
        stmt = select(MealHistory).where(MealHistory.user_id == str(user_id))
        if start_date is not None:
            stmt = stmt.where(MealHistory.meal_date >= start_date)
        if end_date is not None:
            stmt = stmt.where(MealHistory.meal_date <= end_date)
        stmt = stmt.order_by(MealHistory.meal_date.desc(), MealHistory.id.desc())
        stmt = stmt.limit(max(1, min(int(limit or 30), 100)))
        return list(self.session.execute(stmt).scalars().all())

    def get_meal_record(self, meal_id: int) -> Optional[MealHistory]:
        return self.session.get(MealHistory, meal_id)

    def update_natural_meal_record(
        self,
        meal_id: int,
        user_id: str,
        record: dict[str, Any],
        items: list[dict[str, Any]],
    ) -> tuple[MealHistory, list[MealItem]]:
        """기존 자연어 식사 기록을 교체 업데이트한다."""
        try:
            meal = self.session.get(MealHistory, meal_id)
            if meal is None or meal.user_id != str(user_id):
                raise KeyError("meal record not found")

            meal.restaurant_id = str(record["restaurant_id"]) if record.get("restaurant_id") else None
            meal.meal_date = record.get("meal_date") or meal.meal_date
            meal.menu_name = record.get("menu_name")
            meal.calories = record.get("calories")
            meal.carbs = record.get("carbs")
            meal.protein = record.get("protein")
            meal.fat = record.get("fat")
            meal.sugar = record.get("sugar")
            meal.sodium = record.get("sodium")
            meal.satisfaction = record.get("satisfaction")
            meal.raw_text = record.get("raw_text")
            meal.meal_type = record.get("meal_type")
            meal.parsed_items_json = record.get("parsed_items_json")
            meal.nutrition_source = record.get("nutrition_source")
            meal.match_confidence = record.get("match_confidence")
            meal.needs_review = bool(record.get("needs_review", False))
            meal.restaurant_name_snapshot = record.get("restaurant_name_snapshot")
            meal.restaurant_place_url = record.get("restaurant_place_url")
            meal.updated_at = datetime.utcnow()

            self.session.query(MealItem).filter(
                MealItem.meal_history_id == meal.id
            ).delete(synchronize_session=False)
            self.session.flush()

            saved_items: list[MealItem] = []
            for item in items:
                meal_item = MealItem(
                    meal_history_id=meal.id,
                    raw_name=str(item["raw_name"]),
                    normalized_name=item.get("normalized_name"),
                    food_code=item.get("food_code"),
                    quantity=float(item.get("quantity") or 1.0),
                    unit=item.get("unit") or "serving",
                    serving_size=item.get("serving_size"),
                    calories=item.get("calories"),
                    carbs=item.get("carbs"),
                    protein=item.get("protein"),
                    fat=item.get("fat"),
                    sugar=item.get("sugar"),
                    sodium=item.get("sodium"),
                    source=item.get("source") or "unverified",
                    match_type=item.get("match_type") or "unverified",
                    match_confidence=item.get("match_confidence"),
                    needs_review=bool(item.get("needs_review", True)),
                )
                self.session.add(meal_item)
                saved_items.append(meal_item)

            self.session.commit()
            self.session.refresh(meal)
            for item in saved_items:
                self.session.refresh(item)
            return meal, saved_items
        except Exception as e:
            self.session.rollback()
            logger.exception("update_natural_meal_record failed: %s", e)
            raise

    def delete_meal_record(self, meal_id: int, user_id: str) -> bool:
        """사용자 식사 기록을 삭제한다."""
        try:
            meal = self.session.get(MealHistory, meal_id)
            if meal is None or meal.user_id != str(user_id):
                return False
            self.session.delete(meal)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            logger.exception("delete_meal_record failed: %s", e)
            raise

    def get_meal_history(
        self,
        user_id: str,
        start_date: date,
        end_date: date,
    ) -> list[MealHistory]:
        stmt = (
            select(MealHistory)
            .where(
                MealHistory.user_id == user_id,
                MealHistory.meal_date >= start_date,
                MealHistory.meal_date <= end_date,
            )
            .order_by(MealHistory.meal_date.asc(), MealHistory.id.asc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_weekly_stats(
        self,
        user_id: str,
        week_start: date,
    ) -> dict[str, Any]:
        """
        주간 일별 합계 및 평균.
        """
        week_end = week_start + timedelta(days=6)
        rows = self.get_meal_history(user_id, week_start, week_end)

        if not rows:
            return {
                "period": {"start": week_start.isoformat(), "end": week_end.isoformat()},
                "meal_count": 0,
                "daily_records": [],
                "weekly_avg": {},
                "weekly_total": {},
                "recorded_days": 0,
                "missing_days": [
                    (week_start + timedelta(days=i)).isoformat() for i in range(7)
                ],
            }

        by_day: dict[date, list[MealHistory]] = defaultdict(list)
        for r in rows:
            by_day[r.meal_date].append(r)

        daily_records = []
        for i in range(7):
            d = week_start + timedelta(days=i)
            day_rows = by_day.get(d, [])
            if not day_rows:
                continue
            daily_records.append({
                "date": d.isoformat(),
                "day": ["월", "화", "수", "목", "금", "토", "일"][i],
                "calories": sum((r.calories or 0) for r in day_rows),
                "carbs": sum((r.carbs or 0) for r in day_rows),
                "protein": sum((r.protein or 0) for r in day_rows),
                "fat": sum((r.fat or 0) for r in day_rows),
                "sodium": sum((r.sodium or 0) for r in day_rows),
            })

        recorded = len(daily_records)
        weekly_avg = {
            k: sum(d[k] for d in daily_records) / recorded
            for k in ("calories", "carbs", "protein", "fat", "sodium")
        }
        weekly_total = {
            k: sum(d[k] for d in daily_records)
            for k in ("calories", "carbs", "protein", "fat", "sodium")
        }

        missing_days = [
            (week_start + timedelta(days=i)).isoformat()
            for i in range(7)
            if not by_day.get(week_start + timedelta(days=i))
        ]

        return {
            "period": {"start": week_start.isoformat(), "end": week_end.isoformat()},
            "meal_count": len(rows),
            "daily_records": daily_records,
            "weekly_avg": weekly_avg,
            "weekly_total": weekly_total,
            "recorded_days": recorded,
            "missing_days": missing_days,
        }

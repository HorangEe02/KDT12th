"""
날씨 데이터 통합 + 메뉴 적합도 점수 산출.

- WeatherDataIntegrator : 기상청 + 에어코리아 → 통합 dict + 외출 쾌적도
- WeatherMenuScorer     : 음식점 메뉴 타입 × 날씨 → 0~100 적합도
"""
from __future__ import annotations

import logging
from typing import Any, Final, Optional

from pipeline.collectors.air_quality_collector import _GRADE_MAP

logger = logging.getLogger(__name__)


# =============================================================================
# WeatherDataIntegrator
# =============================================================================
class WeatherDataIntegrator:
    """기상청 + 에어코리아 결과를 하나의 통합 dict 로 합친다."""

    @staticmethod
    def integrate(
        weather_data: Optional[dict[str, Any]],
        air_data: Optional[dict[str, Any]],
    ) -> dict[str, Any]:
        weather_data = weather_data or {}

        pm10 = air_data.get("pm10_value") if air_data else None
        pm25 = air_data.get("pm25_value") if air_data else None

        dust_grade: Optional[str] = None
        if air_data:
            pm10_g = air_data.get("pm10_grade")
            pm25_g = air_data.get("pm25_grade")
            grades = [g for g in (pm10_g, pm25_g) if g is not None]
            if grades:
                dust_grade = _GRADE_MAP.get(max(grades))

        result: dict[str, Any] = {
            "temp": weather_data.get("temp", 0.0),
            "humidity": weather_data.get("humidity", 0),
            "rain_type": weather_data.get("rain_type", 0),
            "rain_type_str": weather_data.get("rain_type_str", "없음"),
            "rain_1h": weather_data.get("rain_1h", 0.0),
            "wind_speed": weather_data.get("wind_speed", 0.0),
            "sky": weather_data.get("sky", 1),
            "sky_str": weather_data.get("sky_str", "맑음"),
            "pop": weather_data.get("pop", 0),
            "tmn": weather_data.get("tmn", 0.0),
            "tmx": weather_data.get("tmx", 0.0),
            "pm10": pm10,
            "pm25": pm25,
            "dust_grade": dust_grade,
            "collected_at": weather_data.get("collected_at"),
        }
        result["outdoor_comfort"] = WeatherDataIntegrator.calculate_outdoor_comfort(
            temp=result["temp"],
            rain_type=result["rain_type"],
            pop=result["pop"],
            dust_grade=dust_grade,
            wind_speed=result["wind_speed"],
        )
        return result

    @staticmethod
    def calculate_outdoor_comfort(
        temp: float,
        rain_type: int,
        pop: int,
        dust_grade: Optional[str],
        wind_speed: float,
    ) -> str:
        """종합 외출 쾌적도."""
        # 매우나쁨
        if dust_grade == "매우나쁨":
            return "매우나쁨"
        if temp < -5 or temp > 38:
            return "매우나쁨"

        # 나쁨
        if dust_grade == "나쁨":
            return "나쁨"
        if rain_type != 0:
            return "나쁨"
        if temp < 0 or temp >= 35:
            return "나쁨"

        # 매우좋음
        if (
            15 <= temp <= 25
            and pop < 20
            and (dust_grade is None or dust_grade == "좋음")
            and wind_speed < 3
        ):
            return "매우좋음"

        # 좋음
        if (
            10 <= temp <= 28
            and pop < 40
            and (dust_grade is None or dust_grade in ("좋음", "보통"))
        ):
            return "좋음"

        return "보통"


# =============================================================================
# WeatherMenuScorer
# =============================================================================
_SOUP_TYPES: Final[set[str]] = {"국물", "죽", "탕"}
_NOODLE_TYPES: Final[set[str]] = {"면류"}
_COLD_TYPES: Final[set[str]] = {"초밥", "샐러드"}
_COLD_NOODLE_KEYWORDS: Final[set[str]] = {"냉면"}
# 확장 메뉴 태그
_JEON_ANJU_TYPES: Final[set[str]] = {"전", "부침개", "파전"}
_JEON_ANJU_KEYWORDS: Final[set[str]] = {"전", "부침", "파전", "막걸리", "동동주", "탁주"}
_SPICY_TYPES: Final[set[str]] = {"매운음식", "떡볶이"}
_SPICY_KEYWORDS: Final[set[str]] = {"매운", "불닭", "매운탕", "떡볶이", "짬뽕"}
_HEARTY_TYPES: Final[set[str]] = {"백반", "정식", "한식"}
_LIGHT_TYPES: Final[set[str]] = {"샐러드", "샌드위치", "카페"}


class WeatherMenuScorer:
    """
    음식점 × 날씨 조건 → 0~100 적합도.

    Input 음식점 dict keys (모두 선택):
        - menu_type: "국물" | "면류" | "초밥" | "샐러드" | ...
        - sub_category: "냉면" 등
        - distance_m (int)
        - indoor (bool)
    """

    BASE_SCORE: Final[int] = 50

    @staticmethod
    def _is_cold_noodle(restaurant: dict[str, Any]) -> bool:
        sub = (restaurant.get("sub_category") or "").strip()
        return any(k in sub for k in _COLD_NOODLE_KEYWORDS)

    @staticmethod
    def _menu_type_of(restaurant: dict[str, Any]) -> str:
        return (restaurant.get("menu_type") or "").strip()

    @classmethod
    def calculate_weather_score(
        cls,
        restaurant: dict[str, Any],
        weather: dict[str, Any],
    ) -> int:
        """음식점 × 날씨 적합도 (0~100)."""
        score = cls.BASE_SCORE
        menu_type = cls._menu_type_of(restaurant)
        is_cold_noodle = cls._is_cold_noodle(restaurant)
        distance_m = int(restaurant.get("distance_m", 0) or 0)
        indoor = bool(restaurant.get("indoor", True))

        temp = float(weather.get("temp", 0.0) or 0.0)
        rain_type = int(weather.get("rain_type", 0) or 0)
        pop = int(weather.get("pop", 0) or 0)
        dust_grade = weather.get("dust_grade")
        wind_speed = float(weather.get("wind_speed", 0.0) or 0.0)

        # 기온
        if temp < 5:
            if menu_type in _SOUP_TYPES:
                score += 30
            elif menu_type in _NOODLE_TYPES and not is_cold_noodle:
                score += 15
            elif menu_type in _COLD_TYPES or is_cold_noodle:
                score -= 10
        elif 5 <= temp < 10:
            if menu_type in _SOUP_TYPES:
                score += 25
            elif menu_type in _NOODLE_TYPES and not is_cold_noodle:
                score += 10
        elif 10 <= temp < 15:
            score += 5
        elif 25 <= temp < 30:
            if is_cold_noodle or menu_type in _COLD_TYPES:
                score += 25
            elif menu_type in _SOUP_TYPES:
                score -= 10
        elif temp >= 30:
            if is_cold_noodle or menu_type in _COLD_TYPES:
                score += 30
            elif menu_type in _SOUP_TYPES:
                score -= 15

        # 강수
        rainy = rain_type != 0 or pop > 60
        if rainy:
            if distance_m <= 200:
                score += 15
            elif distance_m >= 400:
                score -= 15
            if menu_type in _SOUP_TYPES:
                score += 10

        # 미세먼지
        if dust_grade in ("나쁨", "매우나쁨") and indoor:
            score += 15

        # 바람
        if wind_speed > 8 and distance_m >= 300:
            score -= 10

        return max(0, min(100, int(round(score))))

    @classmethod
    def get_weather_tips(cls, weather: dict[str, Any]) -> list[str]:
        tips: list[str] = []

        temp = float(weather.get("temp", 0.0) or 0.0)
        rain_type = int(weather.get("rain_type", 0) or 0)
        pop = int(weather.get("pop", 0) or 0)
        dust_grade = weather.get("dust_grade")
        wind_speed = float(weather.get("wind_speed", 0.0) or 0.0)

        if temp < 5:
            tips.append("영하권 강추위! 따뜻한 국물류를 추천합니다")
        elif temp < 10:
            tips.append("쌀쌀한 날씨에는 뜨끈한 국밥이나 찌개가 좋겠어요")

        if temp > 30:
            tips.append("무더운 날씨! 시원한 냉면이나 초밥은 어떨까요")

        if rain_type != 0:
            tips.append("현재 비가 오고 있어요. 실내 가까운 곳으로!")
        elif pop > 60:
            tips.append("비 올 확률이 높아요. 가까운 곳을 추천합니다")

        if dust_grade == "매우나쁨":
            tips.append("미세먼지 매우나쁨! 가급적 실내에서 식사하세요")
        elif dust_grade == "나쁨":
            tips.append("미세먼지가 나쁩니다. 실내 식당을 이용하세요")

        if wind_speed > 8:
            tips.append("바람이 강해요. 가까운 곳을 선택하세요")

        if not tips:
            tips.append("오늘은 어떤 메뉴든 좋은 날씨예요!")

        return tips

    @classmethod
    def rank_restaurants_by_weather(
        cls,
        restaurants: list[dict[str, Any]],
        weather: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """각 음식점에 weather_score 추가 후 내림차순 정렬."""
        scored: list[dict[str, Any]] = []
        for r in restaurants:
            new_r = dict(r)
            new_r["weather_score"] = cls.calculate_weather_score(r, weather)
            scored.append(new_r)
        scored.sort(key=lambda x: x["weather_score"], reverse=True)
        return scored

    @classmethod
    def get_menu_type_ranking(cls, weather: dict[str, Any]) -> list[dict[str, Any]]:
        """현재 날씨 기준 메뉴 타입별 평균 적합도 랭킹."""
        menu_types = ["국물", "죽", "면류", "냉면", "초밥", "샐러드", "버거", "한식", "일식", "양식", "카페"]

        results = []
        for mt in menu_types:
            if mt == "냉면":
                dummy_r = {
                    "menu_type": "면류", "sub_category": "냉면",
                    "distance_m": 200, "indoor": True,
                }
            else:
                dummy_r = {"menu_type": mt, "distance_m": 200, "indoor": True}
            score = cls.calculate_weather_score(dummy_r, weather)
            results.append({"menu_type": mt, "avg_score": score})

        results.sort(key=lambda x: x["avg_score"], reverse=True)
        return results

    # -----------------------------------------------------------------
    # 복합 날씨 효과 (기온 × 강수 매트릭스)
    # -----------------------------------------------------------------
    @staticmethod
    def get_compound_bonus(weather: dict[str, Any], menu_type: str, sub_category: str = "") -> int:
        """기온 × 강수/하늘 복합 보너스. 기존 독립 룰 위에 추가로 적용."""
        temp = float(weather.get("temp", 0.0) or 0.0)
        rain_type = int(weather.get("rain_type", 0) or 0)
        pop = int(weather.get("pop", 0) or 0)
        rainy = rain_type != 0 or pop > 60

        is_soup = menu_type in _SOUP_TYPES
        is_jeon = menu_type in _JEON_ANJU_TYPES or any(k in sub_category for k in _JEON_ANJU_KEYWORDS)

        bonus = 0

        # 비 + 쌀쌀(5~15°C) = 전+막걸리 보너스
        if rainy and 5 <= temp < 15 and is_jeon:
            bonus += 20

        # 비 + 추움(<5°C) = 국물 강화
        if rainy and temp < 5 and is_soup:
            bonus += 10  # 기존 +30(추움) +10(비) 위에 +10 추가

        # 비 + 더움(28+) = 평소와 다른 패턴 → 국물도 괜찮음
        if rainy and temp >= 28 and is_soup:
            bonus += 15  # 더운날 국물 페널티 상쇄

        return bonus

    # -----------------------------------------------------------------
    # 무드 기반 추천
    # -----------------------------------------------------------------
    @staticmethod
    def get_mood_options(weather: dict[str, Any]) -> list[dict[str, Any]]:
        """현재 날씨에 맞는 무드 옵션 목록 반환."""
        temp = float(weather.get("temp", 0.0) or 0.0)
        rain_type = int(weather.get("rain_type", 0) or 0)
        pop = int(weather.get("pop", 0) or 0)
        dust_grade = weather.get("dust_grade")
        rainy = rain_type != 0 or pop > 60

        options: list[dict[str, Any]] = []
        sky_str = weather.get("sky_str", "")

        # --- 비 관련 ---
        if rainy:
            options.extend([
                {"id": "stay_close", "emoji": "🏠", "label": "나가기 싫어요", "description": "가까운 곳에서 빠르게 해결"},
                {"id": "soup_craving", "emoji": "🍜", "label": "국물이 땡겨요", "description": "따뜻한 국물요리가 먹고 싶어요"},
                {"id": "rain_anju", "emoji": "🍶", "label": "막걸리+안주 먹고싶어요", "description": "비 오는 날 전에 막걸리 한잔"},
                {"id": "rainy_walk", "emoji": "🚶", "label": "산책 겸 다녀올래요", "description": "비 소리 들으며 여유롭게"},
            ])

        # --- 추움 (10°C 미만) ---
        if temp < 10:
            options.extend([
                {"id": "warm_food", "emoji": "🔥", "label": "따뜻한 음식이요", "description": "추운 날씨에 몸을 녹일 음식"},
                {"id": "spicy_craving", "emoji": "🌶️", "label": "매운거 먹고싶어요", "description": "얼큰하고 매운 음식으로"},
            ])
            if not rainy:
                options.append({"id": "stay_close", "emoji": "🏠", "label": "나가기 싫어요", "description": "추워서 가까운 곳에서"})

        # --- 쌀쌀 (10~17°C) — 기존에 빠져있던 구간 ---
        if 10 <= temp < 17:
            options.extend([
                {"id": "soup_craving", "emoji": "🍜", "label": "국물이 땡겨요", "description": "쌀쌀한 날씨에 따뜻한 국물"},
                {"id": "warm_food", "emoji": "🔥", "label": "든든하게 먹고싶어요", "description": "몸을 녹이는 따뜻한 식사"},
            ])

        # --- 더움 (28°C 이상) ---
        if temp >= 28:
            options.extend([
                {"id": "cool_food", "emoji": "🧊", "label": "시원한 음식이요", "description": "더위를 식힐 냉면이나 초밥"},
                {"id": "light_meal", "emoji": "🥗", "label": "가볍게 먹을래요", "description": "더운 날 가벼운 식사"},
            ])

        # --- 미세먼지 ---
        if dust_grade in ("나쁨", "매우나쁨"):
            options.append({"id": "indoor_only", "emoji": "😷", "label": "실내에서만 먹을래요", "description": "미세먼지가 나빠서 실내 식당만"})

        # --- 흐림/구름 (비 아닌데 흐린 날) ---
        if sky_str in ("흐림", "구름많음") and not rainy:
            options.append({"id": "spicy_craving", "emoji": "🌶️", "label": "매운거 먹고싶어요", "description": "흐린 날 얼큰한 한 그릇"})

        # --- 날씨 좋은 날 ---
        if 17 <= temp <= 25 and not rainy and dust_grade not in ("나쁨", "매우나쁨"):
            options.append({"id": "walk_enjoy", "emoji": "🚶", "label": "좀 걸어가도 좋아요", "description": "날씨가 좋으니 멀어도 괜찮아요"})

        # --- 항상 공통 ---
        options.extend([
            {"id": "stay_close", "emoji": "🏠", "label": "가까운 곳에서", "description": "가까운 곳에서 빠르게"},
            {"id": "default", "emoji": "😐", "label": "평소대로 먹을래요", "description": "날씨 상관없이 평소처럼"},
        ])

        # 중복 id 제거 (첫 항목 유지)
        seen: set[str] = set()
        unique: list[dict[str, Any]] = []
        for o in options:
            if o["id"] not in seen:
                seen.add(o["id"])
                unique.append(o)

        return unique

    @classmethod
    def calculate_mood_score(
        cls,
        restaurant: dict[str, Any],
        weather: dict[str, Any],
        mood_id: str,
    ) -> tuple[int, str]:
        """무드 기반 점수 (0~100) + 추천 이유 문자열."""
        base = cls.calculate_weather_score(restaurant, weather)
        menu_type = cls._menu_type_of(restaurant)
        sub_cat = (restaurant.get("sub_category") or "").strip()
        distance_m = int(restaurant.get("distance_m", 0) or 0)
        indoor = bool(restaurant.get("indoor", True))

        bonus = 0
        reason = ""

        if mood_id == "stay_close":
            # 거리에 극단적 가중치
            if distance_m <= 100:
                bonus += 30
                reason = "100m 이내 초근접"
            elif distance_m <= 200:
                bonus += 15
                reason = "200m 이내 가까운 거리"
            elif distance_m >= 300:
                bonus -= 25
                reason = "거리가 멀어요"

        elif mood_id == "soup_craving":
            if menu_type in _SOUP_TYPES:
                bonus += 35
                reason = "따뜻한 국물 요리"
            elif menu_type in _NOODLE_TYPES and not cls._is_cold_noodle(restaurant):
                bonus += 15
                reason = "따뜻한 면 요리"
            else:
                bonus -= 10

        elif mood_id == "rain_anju":
            is_jeon = any(k in sub_cat for k in _JEON_ANJU_KEYWORDS) or any(k in menu_type for k in _JEON_ANJU_KEYWORDS)
            if is_jeon or menu_type in _JEON_ANJU_TYPES:
                bonus += 35
                reason = "비 오는 날 전+막걸리"
            elif menu_type in _SOUP_TYPES:
                bonus += 10
                reason = "안주로도 좋은 국물"
            elif menu_type in ("한식",):
                bonus += 15
                reason = "한식 안주 메뉴"
            else:
                bonus -= 5

        elif mood_id == "rainy_walk":
            # 산책하고 싶은 사람 → 거리 페널티 없음, 오히려 중거리 보너스
            if 200 <= distance_m <= 400:
                bonus += 20
                reason = "산책하기 좋은 거리"
            elif distance_m > 400:
                bonus += 10
                reason = "여유롭게 걸어가기"
            else:
                bonus += 5
                reason = "가까이서도 좋아요"

        elif mood_id == "warm_food":
            if menu_type in _SOUP_TYPES:
                bonus += 30
                reason = "몸을 녹이는 국물"
            elif menu_type in _NOODLE_TYPES and not cls._is_cold_noodle(restaurant):
                bonus += 20
                reason = "따뜻한 면 요리"
            elif menu_type in _HEARTY_TYPES:
                bonus += 15
                reason = "든든한 한 끼"

        elif mood_id == "spicy_craving":
            is_spicy = any(k in sub_cat for k in _SPICY_KEYWORDS) or menu_type in _SPICY_TYPES
            if is_spicy:
                bonus += 35
                reason = "얼큰하고 매운 맛"
            elif menu_type in _SOUP_TYPES:
                bonus += 10
                reason = "매운탕·찌개류"

        elif mood_id == "cool_food":
            if cls._is_cold_noodle(restaurant) or menu_type in _COLD_TYPES:
                bonus += 35
                reason = "시원한 한 그릇"
            elif menu_type in _LIGHT_TYPES:
                bonus += 15
                reason = "가볍고 시원하게"

        elif mood_id == "light_meal":
            if menu_type in _LIGHT_TYPES:
                bonus += 30
                reason = "가벼운 식사"
            elif menu_type in _COLD_TYPES:
                bonus += 15
                reason = "시원하고 가볍게"

        elif mood_id == "indoor_only":
            if indoor:
                bonus += 25
                reason = "실내 식당"
            else:
                bonus -= 30
                reason = "야외 좌석 있음"

        elif mood_id == "walk_enjoy":
            # 걸어가도 좋은 사람 → 거리 페널티 크게 완화
            if distance_m >= 300:
                bonus += 15
                reason = "날씨 좋은 날 산책 코스"
            bonus += 5  # 모든 곳 약간 보너스

        else:  # "default"
            reason = "날씨 기본 추천"

        # 복합 효과 보너스 추가
        compound = cls.get_compound_bonus(weather, menu_type, sub_cat)
        final = max(0, min(100, base + bonus + compound))
        return final, reason if reason else "날씨 기본 추천"

    @classmethod
    def get_mood_recommendations(
        cls,
        restaurants: list[dict[str, Any]],
        weather: dict[str, Any],
        mood_id: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """무드 기반 음식점 추천 리스트."""
        scored = []
        for r in restaurants:
            mood_score, reason = cls.calculate_mood_score(r, weather, mood_id)
            scored.append({**r, "mood_score": mood_score, "reason": reason})
        scored.sort(key=lambda x: x["mood_score"], reverse=True)
        return scored[:limit]

    @classmethod
    def get_grouped_recommendations(
        cls,
        restaurants: list[dict[str, Any]],
        weather: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """날씨에 따른 카테고리별 그룹 추천."""
        temp = float(weather.get("temp", 0.0) or 0.0)
        rain_type = int(weather.get("rain_type", 0) or 0)
        pop = int(weather.get("pop", 0) or 0)
        rainy = rain_type != 0 or pop > 60

        groups: list[dict[str, Any]] = []

        if rainy or temp < 10:
            # 국물 그룹
            soup_recs = cls.get_mood_recommendations(restaurants, weather, "soup_craving", 3)
            if soup_recs:
                groups.append({
                    "group_label": "따뜻한 국물이 땡길 때",
                    "group_emoji": "🍜",
                    "items": soup_recs,
                })

        if rainy and temp >= 5:
            # 전+막걸리 그룹
            anju_recs = cls.get_mood_recommendations(restaurants, weather, "rain_anju", 3)
            if anju_recs:
                groups.append({
                    "group_label": "비 오는 날 막걸리 한잔",
                    "group_emoji": "🍶",
                    "items": anju_recs,
                })

        if rainy:
            # 가까운 곳 그룹
            close_recs = cls.get_mood_recommendations(restaurants, weather, "stay_close", 3)
            if close_recs:
                groups.append({
                    "group_label": "가까운 곳에서 빠르게",
                    "group_emoji": "🏠",
                    "items": close_recs,
                })

        if temp >= 28:
            cool_recs = cls.get_mood_recommendations(restaurants, weather, "cool_food", 3)
            if cool_recs:
                groups.append({
                    "group_label": "시원하게 한 그릇",
                    "group_emoji": "🧊",
                    "items": cool_recs,
                })

        # 항상: 기본 추천
        default_recs = cls.get_mood_recommendations(restaurants, weather, "default", 3)
        if default_recs:
            groups.append({
                "group_label": "오늘의 추천",
                "group_emoji": "⭐",
                "items": default_recs,
            })

        return groups

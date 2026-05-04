"""
식사 시간(meal_type) 기반 식당 카테고리 필터링.

다중 식사 시간 지원(헤비 옵션)의 핵심 모듈.
사용자가 아침/점심/저녁 중 어느 시간대를 선택했는지에 따라
적절한 카테고리의 식당만 추천 후보로 남긴다.

영업시간 정확도가 필요할 경우 향후 `restaurants` 테이블에
`hours_breakfast`, `hours_lunch`, `hours_dinner` 컬럼 추가로 확장 가능.
현재는 카테고리 화이트리스트 기반의 휴리스틱.
"""
from __future__ import annotations

from typing import Iterable, Literal, Optional

MealType = Literal["breakfast", "lunch", "dinner", "any"]

# 아침 식사 적합 카테고리: 빠르고 가벼운, 7-10시 영업이 일반적
BREAKFAST_CATEGORIES: frozenset[str] = frozenset({
    "카페",
    "베이커리",
    "샌드위치",
    "브런치",
    "김밥",
    "분식",
    "죽",
    "도시락",
    "간식",
})

# 점심: 모든 카테고리 허용 (직장인 점심은 메뉴 다양성 우선)
# None 은 "필터링하지 않음" 을 의미
LUNCH_CATEGORIES: Optional[frozenset[str]] = None

# 저녁 식사 적합 카테고리: 회식·가족식 적합
DINNER_CATEGORIES: frozenset[str] = frozenset({
    "한식",
    "일식",
    "중식",
    "양식",
    "고깃집",
    "구이",
    "회",
    "초밥",
    "술집",
    "주점",
    "이자카야",
    "호프",
    "뷔페",
    "동남아",
    "아시아음식",
    "샤브샤브",
    "치킨",
    "곱창",
    "전골",
    "찌개",
})


def matches_meal_type(category: Optional[str], meal_type: str) -> bool:
    """주어진 카테고리가 meal_type 화이트리스트와 일치하는지 판정.

    Args:
        category: 식당 카테고리 ("한식", "카페" 등). None 또는 빈 문자열이면 통과(보수적).
        meal_type: "breakfast" | "lunch" | "dinner" | "any"

    Returns:
        True 이면 추천 후보로 유지, False 이면 제외.
    """
    if meal_type == "any" or meal_type == "lunch":
        # 점심 = 전체 허용, any = 필터 비활성
        return True

    if not category:
        # 카테고리가 비어 있으면 보수적으로 통과시켜 추천 후보 풀이 0이 되지 않도록 함
        return True

    cat = category.strip()

    if meal_type == "breakfast":
        return cat in BREAKFAST_CATEGORIES
    if meal_type == "dinner":
        return cat in DINNER_CATEGORIES

    # 알 수 없는 meal_type → 안전하게 통과
    return True


def matches_restaurant_meal_type(restaurant: dict, meal_type: str) -> bool:
    """식당 dict 가 meal_type 으로 추천 적합한지 종합 판정.

    의미론:
    - serves_{breakfast|lunch|dinner} Boolean 은 **부정 override** 용 (False = 명시적 제외)
    - True 또는 누락은 "큐레이션 안 됨" 으로 간주 → 카테고리 화이트리스트가 권위
    - 향후 ETL 이 정확한 영업시간을 알면 False 로 명시적 닫음

    Args:
        restaurant: 식당 dict (category, serves_breakfast, serves_lunch, serves_dinner)
        meal_type: "breakfast" | "lunch" | "dinner" | "any"

    Returns:
        True 이면 추천 후보로 유지.
    """
    if meal_type == "any":
        return True

    # Boolean = False 인 경우만 명시적 제외 (override)
    serves_val = restaurant.get(f"serves_{meal_type}")
    if serves_val is False:
        return False

    # 그 외에는 카테고리 휴리스틱이 권위
    return matches_meal_type(restaurant.get("category"), meal_type)


def filter_by_meal_type(
    restaurants: Iterable[dict],
    meal_type: str,
    *,
    category_key: str = "category",
) -> list[dict]:
    """식당 dict 리스트를 meal_type 으로 필터링.

    Args:
        restaurants: 식당 dict iterable (각 dict 에 category_key 가 있어야 함)
        meal_type: "breakfast" | "lunch" | "dinner" | "any"
        category_key: dict 에서 카테고리를 꺼낼 키 (기본 "category")

    Returns:
        필터링된 식당 리스트. meal_type=any/lunch 면 원본 그대로.
    """
    if meal_type in ("any", "lunch"):
        return list(restaurants)

    return [
        r for r in restaurants
        if matches_meal_type(r.get(category_key), meal_type)
    ]


def infer_meal_type_from_hour(hour: int) -> MealType:
    """현재 시각(0-23)으로부터 가장 적절한 meal_type 을 추정.

    Args:
        hour: 0-23 범위의 시각

    Returns:
        breakfast (06-10) / lunch (10-15) / dinner (15-23 또는 00-05) / any
    """
    if 6 <= hour < 10:
        return "breakfast"
    if 10 <= hour < 15:
        return "lunch"
    if 15 <= hour < 23 or hour < 6:
        return "dinner"
    # fallback (이론적으로 도달하지 않음)
    return "any"

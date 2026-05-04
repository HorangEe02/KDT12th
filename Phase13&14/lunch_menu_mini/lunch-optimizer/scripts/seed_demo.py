"""
데모 시드 스크립트.

실제 API 키가 없거나 접근 불가능한 환경에서 전체 파이프라인을
end-to-end 시연할 수 있도록 SQLite 에 합성 데이터를 심는다.

실행:
    source venv/bin/activate
    python -m scripts.seed_demo
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path

from database.connection import get_engine, get_session, init_schema
from database.models import (
    Base, MealHistory, NutritionInfo, Restaurant, Team, User,
    VisitHistory, WeatherLog,
)


# =============================================================================
# 시드 데이터 정의
# =============================================================================
RESTAURANTS = [
    # (id, name, category, menu_type, sub, distance_m, score, price, lat, lng)
    ("k-100", "한솥도시락 시청점",    "한식", "밥류",   "도시락",    120, 100, 6500,  37.5670, 126.9781),
    ("k-101", "본죽&비빔밥 시청점",   "한식", "죽",     "죽",         180,  85, 8000,  37.5672, 126.9785),
    ("k-102", "김치찌개 전문 장인",   "한식", "국물",   "국/탕/찌개", 200,  85, 8500,  37.5668, 126.9790),
    ("k-103", "서브웨이 시청역",      "양식", "기타",   "샌드위치",   250,  70, 9500,  37.5673, 126.9795),
    ("k-104", "정연낙시메 (라멘)",    "일식", "면류",   "라멘",       280,  70, 10000, 37.5663, 126.9798),
    ("k-105", "스시지로 (초밥)",      "일식", "초밥",   "초밥/롤",    320,  70, 18000, 37.5660, 126.9800),
    ("k-106", "파스타하우스",         "양식", "면류",   "파스타",     380,  50, 13000, 37.5685, 126.9810),
    ("k-107", "셰프스테이블",         "양식", "버거",   "햄버거",     420,  30, 15000, 37.5690, 126.9815),
    ("k-108", "올리브영 샐러드바",    "샐러드", "샐러드", "샐러드",   350,  50, 12000, 37.5658, 126.9805),
    ("k-109", "쌀국수 천국",          "동남아", "면류", "쌀국수",     290,  70, 9000,  37.5680, 126.9800),
]

# 음식점별 영양 정보 (식약처 매핑이 불가하니 카테고리 평균 기반)
NUTRITION_MAP = {
    "k-100": {"calories": 620, "carbs": 95, "protein": 22, "fat": 16, "sugar": 8,  "sodium": 950},
    "k-101": {"calories": 520, "carbs": 75, "protein": 20, "fat": 12, "sugar": 6,  "sodium": 600},
    "k-102": {"calories": 480, "carbs": 48, "protein": 25, "fat": 18, "sugar": 5,  "sodium": 1450},
    "k-103": {"calories": 480, "carbs": 60, "protein": 28, "fat": 14, "sugar": 8,  "sodium": 950},
    "k-104": {"calories": 580, "carbs": 78, "protein": 22, "fat": 18, "sugar": 5,  "sodium": 1650},
    "k-105": {"calories": 520, "carbs": 68, "protein": 30, "fat": 14, "sugar": 10, "sodium": 900},
    "k-106": {"calories": 720, "carbs": 88, "protein": 24, "fat": 30, "sugar": 12, "sodium": 1100},
    "k-107": {"calories": 820, "carbs": 65, "protein": 36, "fat": 44, "sugar": 12, "sodium": 1250},
    "k-108": {"calories": 380, "carbs": 32, "protein": 24, "fat": 16, "sugar": 8,  "sodium": 520},
    "k-109": {"calories": 540, "carbs": 72, "protein": 26, "fat": 14, "sugar": 6,  "sodium": 1100},
}


def seed_team_and_users(session):
    team = session.get(Team, "team1")
    if team is None:
        session.add(Team(id="team1", name="개발1팀"))

    users_data = [
        ("user1", "김민수", "🧑‍💻"),
        ("user2", "이수진", "👩‍💼"),
        ("user3", "박준혁", "👨‍🔬"),
        ("user4", "정하은", "👩‍🎨"),
        ("user5", "최동원", "🧑‍🚀"),
    ]
    for uid, name, emoji in users_data:
        if session.get(User, uid) is None:
            session.add(User(id=uid, name=name, team_id="team1", avatar_emoji=emoji))
    session.commit()
    print(f"  ✓ Team + 5 users seeded")


def seed_restaurants(session):
    inserted = 0
    for rid, name, cat, menu, sub, dist, score, price, lat, lng in RESTAURANTS:
        if session.get(Restaurant, rid) is None:
            session.add(Restaurant(
                id=rid, name=name, category=cat, menu_type=menu, sub_category=sub,
                lat=lat, lng=lng, distance_m=dist, distance_score=score,
                price_avg=price, indoor=True,
            ))
            inserted += 1
    session.commit()
    print(f"  ✓ {inserted} restaurants seeded ({len(RESTAURANTS)} total)")


def seed_weather(session):
    log = WeatherLog(
        temp=18.5, humidity=55, rain_type=0, rain_type_str="없음",
        rain_1h=0.0, wind_speed=2.3,
        sky=1, sky_str="맑음",
        pop=10, tmn=12, tmx=22,
        pm10=45, pm25=22, dust_grade="보통",
        outdoor_comfort="좋음",
    )
    session.add(log)
    session.commit()
    print(f"  ✓ Weather log seeded (18.5°C, 맑음, 먼지 보통)")


def seed_nutrition(session):
    count = 0
    for rid, n in NUTRITION_MAP.items():
        existing = session.query(NutritionInfo).filter_by(restaurant_id=rid).first()
        if existing is None:
            session.add(NutritionInfo(
                restaurant_id=rid,
                food_name=next(r[1] for r in RESTAURANTS if r[0] == rid),
                match_type="category_avg",
                serving_size=100.0,
                **n,
            ))
            count += 1
    session.commit()
    print(f"  ✓ {count} nutrition mappings seeded")


def seed_visit_history(session):
    """지난 2주간 팀 방문 이력 — k-100 은 최근 방문 / k-109 는 오래 전 / k-107 은 미방문."""
    visits = [
        (date.today() - timedelta(days=1),  "k-100", 5, 4.0),
        (date.today() - timedelta(days=3),  "k-103", 5, 3.8),
        (date.today() - timedelta(days=4),  "k-100", 4, 4.2),
        (date.today() - timedelta(days=7),  "k-102", 5, 4.5),
        (date.today() - timedelta(days=8),  "k-105", 3, 4.0),
        (date.today() - timedelta(days=10), "k-106", 5, 3.5),
        (date.today() - timedelta(days=13), "k-104", 5, 4.1),
        (date.today() - timedelta(days=20), "k-109", 4, 3.9),
    ]
    for vd, rid, pc, sat in visits:
        existing = session.query(VisitHistory).filter_by(
            visit_date=vd, team_id="team1", restaurant_id=rid
        ).first()
        if existing is None:
            session.add(VisitHistory(
                visit_date=vd, team_id="team1", restaurant_id=rid,
                participant_count=pc, avg_satisfaction=sat,
            ))
    session.commit()
    print(f"  ✓ {len(visits)} visit history entries seeded")


def seed_meal_history(session):
    """user1 의 최근 1주 식사 기록 — 단백질이 살짝 부족한 패턴."""
    meals = [
        # (date, restaurant_id, menu, cal, carbs, protein, fat, sodium)
        (date.today() - timedelta(days=6), "k-100", "한솥도시락", 620, 95, 22, 16, 950),
        (date.today() - timedelta(days=5), "k-101", "본죽",       520, 75, 20, 12, 600),
        (date.today() - timedelta(days=4), "k-103", "샌드위치",   480, 60, 28, 14, 950),
        (date.today() - timedelta(days=3), "k-106", "파스타",     720, 88, 24, 30, 1100),
        (date.today() - timedelta(days=1), "k-100", "한솥도시락", 620, 95, 22, 16, 950),
    ]
    for md, rid, menu, cal, carbs, protein, fat, sodium in meals:
        existing = session.query(MealHistory).filter_by(
            user_id="user1", meal_date=md, restaurant_id=rid
        ).first()
        if existing is None:
            session.add(MealHistory(
                user_id="user1",
                restaurant_id=rid,
                meal_date=md,
                menu_name=menu,
                calories=cal, carbs=carbs, protein=protein, fat=fat, sodium=sodium,
                satisfaction=4,
            ))
    session.commit()
    print(f"  ✓ {len(meals)} meal history entries seeded for user1")


def main():
    print("=" * 60)
    print("Mini Demo Seed — 합성 데이터 주입")
    print("=" * 60)

    # DB 초기화
    init_schema()
    print("  ✓ Schema initialized")

    with get_session() as session:
        seed_team_and_users(session)
        seed_restaurants(session)
        seed_weather(session)
        seed_nutrition(session)
        seed_visit_history(session)
        seed_meal_history(session)

    print("=" * 60)
    print("✅ Seed complete. Run:")
    print("   uvicorn api.main:app --reload --port 8000")
    print("   curl 'http://localhost:8000/api/recommend?team_id=team1&user_id=user1&top_n=5'")
    print("=" * 60)


if __name__ == "__main__":
    main()

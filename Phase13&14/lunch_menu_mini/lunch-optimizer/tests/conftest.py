"""
공용 pytest fixtures.

- in-memory SQLite 엔진 + 세션 (DB 격리)
- 가짜 카카오 API 응답
- 환경 변수 패치
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from database import connection as db_conn
from database.models import Base


# =============================================================================
# DB
# =============================================================================
@pytest.fixture
def memory_engine(monkeypatch):
    """in-memory SQLite 엔진. 각 테스트마다 격리."""
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)

    monkeypatch.setattr(db_conn, "_engine", engine)
    monkeypatch.setattr(db_conn, "_SessionLocal", SessionLocal)

    yield engine

    monkeypatch.setattr(db_conn, "_engine", None)
    monkeypatch.setattr(db_conn, "_SessionLocal", None)
    engine.dispose()


@pytest.fixture
def db_session(memory_engine) -> Session:
    """짧은 수명의 DB 세션 (테스트 종료 시 자동 close)."""
    SessionLocal = db_conn.get_sessionmaker()
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# =============================================================================
# 환경 변수 (가짜 카카오 키)
# =============================================================================
@pytest.fixture
def fake_kakao_key(monkeypatch):
    """KAKAO_REST_API_KEY 패치 + settings reload."""
    monkeypatch.setenv("KAKAO_REST_API_KEY", "test_key_for_unit_test")
    from importlib import reload
    import config.settings as s
    reload(s)
    yield
    reload(s)


@pytest.fixture
def fake_datago_key(monkeypatch):
    """공공데이터포털 키 (기상청·에어코리아 공용) 패치."""
    monkeypatch.setenv("DATA_GO_KR_API_KEY_DECODED", "test_datago_key")
    from importlib import reload
    import config.settings as s
    reload(s)
    yield
    reload(s)


# =============================================================================
# 샘플 데이터
# =============================================================================
@pytest.fixture
def sample_kakao_documents() -> list[dict[str, Any]]:
    """카카오 API documents 샘플 5건."""
    return [
        {
            "id": "kakao-100",
            "place_name": "한식당A",
            "category_name": "음식점 > 한식 > 국/탕/찌개",
            "category_group_code": "FD6",
            "phone": "02-100-0001",
            "address_name": "서울 중구 테스트 1",
            "road_address_name": "서울 중구 테스트로 1",
            "x": "126.9800",
            "y": "37.5680",
            "place_url": "http://place.map.kakao.com/100",
            "distance": "120",
        },
        {
            "id": "kakao-200",
            "place_name": "일식당B",
            "category_name": "음식점 > 일식 > 초밥/롤",
            "category_group_code": "FD6",
            "phone": "",
            "address_name": "서울 중구 테스트 2",
            "road_address_name": "서울 중구 테스트로 2",
            "x": "126.9810",
            "y": "37.5690",
            "place_url": "http://place.map.kakao.com/200",
            "distance": "250",
        },
        {
            "id": "kakao-300",
            "place_name": "양식당C",
            "category_name": "음식점 > 양식 > 햄버거",
            "category_group_code": "FD6",
            "phone": "02-300-0003",
            "address_name": "서울 중구 테스트 3",
            "road_address_name": "서울 중구 테스트로 3",
            "x": "126.9820",
            "y": "37.5700",
            "place_url": "http://place.map.kakao.com/300",
            "distance": "350",
        },
        {
            "id": "kakao-400",
            "place_name": "카페D",
            "category_name": "음식점 > 카페",  # 2단계만
            "category_group_code": "FD6",
            "phone": "",
            "address_name": "서울 중구 테스트 4",
            "road_address_name": "서울 중구 테스트로 4",
            "x": "126.9830",
            "y": "37.5710",
            "place_url": "http://place.map.kakao.com/400",
            "distance": "450",
        },
        {
            "id": "kakao-100",  # 중복!
            "place_name": "한식당A_dup",
            "category_name": "음식점 > 한식",
            "category_group_code": "FD6",
            "phone": "",
            "address_name": "dup",
            "road_address_name": "dup",
            "x": "126.9800",
            "y": "37.5680",
            "place_url": "http://place.map.kakao.com/100",
            "distance": "120",
        },
    ]


@pytest.fixture
def sample_kakao_response(sample_kakao_documents) -> dict[str, Any]:
    """단일 페이지 API 응답 (is_end=True)."""
    return {
        "meta": {
            "total_count": len(sample_kakao_documents),
            "pageable_count": len(sample_kakao_documents),
            "is_end": True,
            "same_name": None,
        },
        "documents": sample_kakao_documents,
    }


# =============================================================================
# 기상청 API 샘플
# =============================================================================
@pytest.fixture
def kma_ncst_response() -> dict[str, Any]:
    """기상청 초단기실황 샘플 응답."""
    return {
        "response": {
            "header": {"resultCode": "00", "resultMsg": "NORMAL_SERVICE"},
            "body": {
                "items": {
                    "item": [
                        {"category": "T1H", "obsrValue": "12.5"},
                        {"category": "REH", "obsrValue": "55"},
                        {"category": "PTY", "obsrValue": "0"},
                        {"category": "RN1", "obsrValue": "0"},
                        {"category": "WSD", "obsrValue": "2.3"},
                        {"category": "VEC", "obsrValue": "270"},
                        {"category": "UUU", "obsrValue": "0.5"},
                        {"category": "VVV", "obsrValue": "0.2"},
                    ]
                }
            },
        }
    }


@pytest.fixture
def kma_fcst_response() -> dict[str, Any]:
    """기상청 단기예보 샘플 응답 (2 시간대 × 5 카테고리)."""
    from datetime import datetime
    today = datetime.now().strftime("%Y%m%d")
    items = []
    for ft in ("1200", "1500"):
        items.extend([
            {"category": "SKY", "fcstDate": today, "fcstTime": ft, "fcstValue": "4"},
            {"category": "POP", "fcstDate": today, "fcstTime": ft, "fcstValue": "30"},
            {"category": "TMP", "fcstDate": today, "fcstTime": ft, "fcstValue": "13"},
            {"category": "TMN", "fcstDate": today, "fcstTime": "0600", "fcstValue": "8"},
            {"category": "TMX", "fcstDate": today, "fcstTime": "1500", "fcstValue": "18"},
        ])
    return {
        "response": {
            "header": {"resultCode": "00", "resultMsg": "NORMAL_SERVICE"},
            "body": {"items": {"item": items}},
        }
    }


# =============================================================================
# 에어코리아 샘플
# =============================================================================
@pytest.fixture
def airkorea_response() -> dict[str, Any]:
    return {
        "response": {
            "header": {"resultCode": "00", "resultMsg": "OK"},
            "body": {
                "items": [
                    {
                        "pm10Value": "45",
                        "pm25Value": "22",
                        "pm10Grade": "2",
                        "pm25Grade": "2",
                        "khaiValue": "68",
                        "khaiGrade": "2",
                        "o3Value": "0.035",
                        "dataTime": "2026-04-05 11:00",
                    }
                ]
            },
        }
    }


@pytest.fixture
def airkorea_dashed_response() -> dict[str, Any]:
    """PM 값이 '-' (점검 시간) 인 경우."""
    return {
        "response": {
            "header": {"resultCode": "00", "resultMsg": "OK"},
            "body": {
                "items": [
                    {
                        "pm10Value": "-",
                        "pm25Value": "",
                        "pm10Grade": "",
                        "pm25Grade": "",
                        "khaiValue": "-",
                        "khaiGrade": "",
                        "o3Value": "-",
                        "dataTime": "2026-04-05 03:00",
                    }
                ]
            },
        }
    }


# =============================================================================
# 식품안전나라 샘플 (Subtopic 3)
# =============================================================================
@pytest.fixture
def fake_food_safety_key(monkeypatch):
    """FOOD_SAFETY_API_KEY 패치 + settings reload."""
    monkeypatch.setenv("FOOD_SAFETY_API_KEY", "test_food_safety_key")
    from importlib import reload
    import config.settings as s
    reload(s)
    yield
    reload(s)


@pytest.fixture
def nutrition_api_response() -> dict[str, Any]:
    """I2790 정상 응답."""
    return {
        "I2790": {
            "RESULT": {"MSG": "정상처리되었습니다.", "CODE": "INFO-000"},
            "total_count": "3",
            "row": [
                {
                    "NUM": "1",
                    "FOOD_CD": "D100001",
                    "DESC_KOR": "김치찌개",
                    "SERVING_SIZE": "400",
                    "NUTR_CONT1": "520",   # kcal
                    "NUTR_CONT2": "45",    # carbs
                    "NUTR_CONT3": "28",    # protein
                    "NUTR_CONT4": "22",    # fat
                    "NUTR_CONT5": "5",     # sugar
                    "NUTR_CONT6": "1450",  # sodium
                    "NUTR_CONT7": "60",
                    "NUTR_CONT8": "6",
                    "NUTR_CONT9": "0.2",
                    "GROUP_NAME": "음식류",
                    "MAKER_NAME": "",
                    "SUB_REF_NAME": "식약처",
                    "RESEARCH_YEAR": "2022",
                },
                {
                    "NUM": "2",
                    "FOOD_CD": "D100002",
                    "DESC_KOR": "참치김치찌개",
                    "SERVING_SIZE": "450",
                    "NUTR_CONT1": "580",
                    "NUTR_CONT2": "48",
                    "NUTR_CONT3": "32",
                    "NUTR_CONT4": "24",
                    "NUTR_CONT5": "5",
                    "NUTR_CONT6": "1550",
                    "NUTR_CONT7": "65",
                    "NUTR_CONT8": "6.5",
                    "NUTR_CONT9": "0.3",
                    "GROUP_NAME": "음식류",
                    "MAKER_NAME": "",
                    "SUB_REF_NAME": "식약처",
                    "RESEARCH_YEAR": "2022",
                },
                {
                    "NUM": "3",
                    "FOOD_CD": "D100003",
                    "DESC_KOR": "두부김치찌개",
                    "SERVING_SIZE": "420",
                    "NUTR_CONT1": "500",
                    "NUTR_CONT2": "42",
                    "NUTR_CONT3": "30",
                    "NUTR_CONT4": "",      # 빈 문자열 → 0.0
                    "NUTR_CONT5": "N/A",   # 없는 값 → None
                    "NUTR_CONT6": "1400",
                    "NUTR_CONT7": "",
                    "NUTR_CONT8": "",
                    "NUTR_CONT9": "",
                    "GROUP_NAME": "음식류",
                    "MAKER_NAME": "",
                    "SUB_REF_NAME": "식약처",
                    "RESEARCH_YEAR": "2022",
                },
            ],
        }
    }


@pytest.fixture
def nutrition_api_no_result() -> dict[str, Any]:
    """INFO-200: 데이터 없음."""
    return {
        "I2790": {
            "RESULT": {"MSG": "해당하는 데이터가 없습니다.", "CODE": "INFO-200"},
        }
    }


# =============================================================================
# 주간 영양 샘플 (Subtopic 3)
# =============================================================================
@pytest.fixture
def balanced_week() -> dict[str, Any]:
    """균형 잡힌 5일 식사."""
    return {
        "period": {"start": "2026-03-30", "end": "2026-04-05"},
        "meal_count": 5,
        "daily_records": [
            {"date": f"2026-03-{30+i}", "day": "월", "calories": 650, "carbs": 85,
             "protein": 28, "fat": 18, "sodium": 700}
            for i in range(5)
        ],
        "weekly_avg": {
            "calories": 650, "carbs": 85, "protein": 28, "fat": 18, "sodium": 700
        },
        "weekly_total": {
            "calories": 3250, "carbs": 425, "protein": 140, "fat": 90, "sodium": 3500
        },
        "macro_ratio": {"carbs_pct": 59.7, "protein_pct": 19.7, "fat_pct": 20.6},
        "recorded_days": 5,
        "missing_days": ["2026-04-04", "2026-04-05"],
    }


@pytest.fixture
def protein_deficient_week() -> dict[str, Any]:
    return {
        "period": {"start": "2026-03-30", "end": "2026-04-05"},
        "meal_count": 5,
        "daily_records": [],
        "weekly_avg": {
            "calories": 580, "carbs": 100, "protein": 15, "fat": 16, "sodium": 900
        },
        "weekly_total": {},
        "macro_ratio": {"carbs_pct": 70.0, "protein_pct": 10.0, "fat_pct": 20.0},
        "recorded_days": 5,
        "missing_days": [],
    }


@pytest.fixture
def sodium_excess_week() -> dict[str, Any]:
    return {
        "period": {"start": "2026-03-30", "end": "2026-04-05"},
        "meal_count": 5,
        "daily_records": [],
        "weekly_avg": {
            "calories": 680, "carbs": 90, "protein": 28, "fat": 20, "sodium": 1500
        },
        "weekly_total": {},
        "macro_ratio": {"carbs_pct": 55.0, "protein_pct": 20.0, "fat_pct": 25.0},
        "recorded_days": 5,
        "missing_days": [],
    }


# =============================================================================
# 팀·사용자·식당 seed 데이터 (Subtopic 4)
# =============================================================================
@pytest.fixture
def seed_team_and_users(memory_engine):
    """Team 1 + Users 5 + Restaurants 6 seed. admin_override 투표 가능."""
    from database.connection import get_session
    from database.models import Restaurant, Team, User

    with get_session() as session:
        team = Team(id="team1", name="개발1팀")
        session.add(team)

        users = []
        for i in range(1, 6):
            users.append(User(
                id=f"user{i}",
                name=f"사용자{i}",
                team_id="team1",
                avatar_emoji="🧑‍💻",
            ))
        session.add_all(users)

        restaurants = []
        for i, (rid, name, cat, menu, dist, score) in enumerate([
            ("r1", "한솥도시락", "한식", "밥류", 120, 100),
            ("r2", "서브웨이", "양식", "기타", 180, 85),
            ("r3", "맥도날드", "양식", "버거", 250, 70),
            ("r4", "김밥천국", "분식", "기타", 300, 70),
            ("r5", "스시집", "일식", "초밥", 350, 50),
            ("r6", "파스타하우스", "양식", "면류", 450, 30),
        ]):
            restaurants.append(Restaurant(
                id=rid, name=name, category=cat, menu_type=menu,
                lat=37.5665, lng=126.9780,
                distance_m=dist, distance_score=score,
                price_avg=8000,
                is_active=True,
            ))
        session.add_all(restaurants)
        session.commit()

    yield


@pytest.fixture
def always_vote_time(monkeypatch):
    """VoteManager 가 항상 '투표 시간' 으로 인식하도록 패치."""
    def _true(self, now=None):
        return True
    from pipeline.collectors import vote_collector
    monkeypatch.setattr(vote_collector.VoteManager, "_is_vote_time", _true)
    yield

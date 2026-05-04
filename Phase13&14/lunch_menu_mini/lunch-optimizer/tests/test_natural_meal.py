"""자연어 식단 저장 API 테스트."""
from __future__ import annotations

from importlib import reload

import pytest
from fastapi.testclient import TestClient

from database.models import MealItem, NutritionInfo


@pytest.fixture
def natural_client(tmp_path, monkeypatch):
    db_path = tmp_path / "natural.db"
    monkeypatch.setenv("MINI_DB_PATH", str(db_path))
    monkeypatch.setenv("DB_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("JWT_SECRET", "test-secret-do-not-use-in-prod-32bytes-padding")

    from config import settings as settings_mod
    from database import connection as conn_mod
    reload(settings_mod)
    reload(conn_mod)
    conn_mod.init_schema()
    from api import main as api_main
    reload(api_main)

    return TestClient(api_main.app), conn_mod


def test_record_natural_meal_with_local_nutrition(natural_client):
    client, conn_mod = natural_client
    with conn_mod.get_session() as session:
        session.add(
            NutritionInfo(
                restaurant_id="local-kimchi",
                food_name="김치찌개",
                match_type="manual_seed",
                match_score=0.9,
                serving_size=400,
                calories=480,
                carbs=48,
                protein=25,
                fat=18,
                sugar=4,
                sodium=1450,
            )
        )
        session.commit()

    response = client.post(
        "/api/nutrition/meal-natural",
        json={
            "user_id": "user1",
            "raw_text": "오늘 점심에 김치찌개 먹었어.",
            "meal_date": "2026-05-01",
            "meal_type": "lunch",
            "items": [
                {
                    "raw_name": "김치찌개",
                    "normalized_name": "김치찌개",
                    "quantity": 1,
                    "unit": "serving",
                }
            ],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "user1"
    assert data["calories"] == 480
    assert data["protein"] == 25
    assert data["nutrition_source"] == "local_cache"
    assert data["needs_review"] is False

    with conn_mod.get_session() as session:
        saved_item = session.query(MealItem).one()
        assert saved_item.raw_name == "김치찌개"
        assert saved_item.source == "local_cache"


def test_record_natural_meal_without_match_is_unverified(natural_client):
    client, _conn_mod = natural_client
    response = client.post(
        "/api/nutrition/meal-natural",
        json={
            "user_id": "user1",
            "raw_text": "오늘 점심에 테스트메뉴 먹었어.",
            "meal_date": "2026-05-01",
            "meal_type": "lunch",
            "items": [
                {
                    "raw_name": "테스트메뉴",
                    "normalized_name": "테스트메뉴",
                    "quantity": 1,
                    "unit": "serving",
                }
            ],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["calories"] is None
    assert data["nutrition_source"] == "unverified"
    assert data["needs_review"] is True


def test_list_and_delete_natural_meal(natural_client):
    client, _conn_mod = natural_client
    create = client.post(
        "/api/nutrition/meal-natural",
        json={
            "user_id": "user1",
            "raw_text": "오늘 점심에 테스트메뉴 먹었어.",
            "meal_date": "2026-05-01",
            "meal_type": "lunch",
            "items": [
                {
                    "raw_name": "테스트메뉴",
                    "normalized_name": "테스트메뉴",
                    "quantity": 1,
                    "unit": "serving",
                    "calories": 500,
                    "protein": 20,
                    "carbs": 70,
                    "fat": 12,
                    "sodium": 900,
                }
            ],
        },
    )
    assert create.status_code == 200
    meal_id = create.json()["id"]

    listed = client.get("/api/nutrition/meals?user_id=user1&limit=5")
    assert listed.status_code == 200
    rows = listed.json()
    assert len(rows) == 1
    assert rows[0]["id"] == meal_id
    assert rows[0]["calories"] == 500

    deleted = client.delete(f"/api/nutrition/meals/{meal_id}?user_id=user1")
    assert deleted.status_code == 200
    assert deleted.json() == {"deleted": True, "meal_id": meal_id}

    listed_again = client.get("/api/nutrition/meals?user_id=user1&limit=5")
    assert listed_again.status_code == 200
    assert listed_again.json() == []

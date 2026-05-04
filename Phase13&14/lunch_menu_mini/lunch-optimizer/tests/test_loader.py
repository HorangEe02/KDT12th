"""
RestaurantLoader 통합 테스트.

in-memory SQLite + 실제 SQLAlchemy 세션 (mocking 없음).
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from database.connection import get_session
from database.models import Restaurant
from pipeline.loaders.db_loader import RestaurantLoader
from pipeline.scheduler import RestaurantPipeline
from pipeline.transformers.distance_scorer import RestaurantTransformer


# =============================================================================
# 헬퍼
# =============================================================================
def _build_df(items: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(items)


@pytest.fixture
def sample_df() -> pd.DataFrame:
    return _build_df([
        {
            "id": "k1", "name": "식당1", "category": "한식",
            "sub_category": "국/탕/찌개", "menu_type": "국물",
            "address": "주소1", "phone": "02-0001",
            "lat": 37.57, "lng": 126.98, "distance_m": 100, "distance_score": 100,
            "place_url": "u1",
        },
        {
            "id": "k2", "name": "식당2", "category": "일식",
            "sub_category": "초밥/롤", "menu_type": "초밥",
            "address": "주소2", "phone": None,
            "lat": 37.57, "lng": 126.98, "distance_m": 250, "distance_score": 70,
            "place_url": "u2",
        },
        {
            "id": "k3", "name": "식당3", "category": "양식",
            "sub_category": "햄버거", "menu_type": "버거",
            "address": "주소3", "phone": "02-0003",
            "lat": 37.57, "lng": 126.98, "distance_m": 350, "distance_score": 50,
            "place_url": "u3",
        },
    ])


# =============================================================================
# upsert_restaurants
# =============================================================================
class TestUpsert:
    def test_insert_new(self, db_session, sample_df):
        loader = RestaurantLoader(db_session)
        stats = loader.upsert_restaurants(sample_df)
        assert stats == {"inserted": 3, "updated": 0, "skipped": 0}

        rows = db_session.query(Restaurant).order_by(Restaurant.distance_m).all()
        assert [r.id for r in rows] == ["k1", "k2", "k3"]

    def test_update_existing(self, db_session, sample_df):
        loader = RestaurantLoader(db_session)
        loader.upsert_restaurants(sample_df)

        # 같은 id, 다른 distance
        updated_df = _build_df([
            {**sample_df.iloc[0].to_dict(), "distance_m": 50, "distance_score": 100},
        ])
        stats = loader.upsert_restaurants(updated_df)
        assert stats == {"inserted": 0, "updated": 1, "skipped": 0}

        r = db_session.get(Restaurant, "k1")
        assert r.distance_m == 50

    def test_empty_df(self, db_session):
        loader = RestaurantLoader(db_session)
        stats = loader.upsert_restaurants(pd.DataFrame())
        assert stats == {"inserted": 0, "updated": 0, "skipped": 0}

    def test_skips_missing_id(self, db_session):
        loader = RestaurantLoader(db_session)
        df = _build_df([{"id": "", "name": "X", "lat": 0.0, "lng": 0.0,
                         "distance_m": 0, "distance_score": 100}])
        stats = loader.upsert_restaurants(df)
        assert stats["skipped"] == 1
        assert stats["inserted"] == 0


# =============================================================================
# deactivate_missing
# =============================================================================
class TestDeactivate:
    def test_deactivates_when_id_not_in_active_list(self, db_session, sample_df):
        loader = RestaurantLoader(db_session)
        loader.upsert_restaurants(sample_df)

        # k2 만 활성으로 유지
        count = loader.deactivate_missing(active_ids=["k2"])
        assert count == 2

        active = db_session.query(Restaurant).filter_by(is_active=True).all()
        assert len(active) == 1
        assert active[0].id == "k2"

    def test_empty_list_does_nothing(self, db_session, sample_df):
        loader = RestaurantLoader(db_session)
        loader.upsert_restaurants(sample_df)
        count = loader.deactivate_missing(active_ids=[])
        assert count == 0


# =============================================================================
# 조회
# =============================================================================
class TestQueries:
    def test_get_active_restaurants_sorted(self, db_session, sample_df):
        loader = RestaurantLoader(db_session)
        loader.upsert_restaurants(sample_df)
        rows = loader.get_active_restaurants()
        assert len(rows) == 3
        assert [r.id for r in rows] == ["k1", "k2", "k3"]  # distance asc

    def test_filter_by_category(self, db_session, sample_df):
        loader = RestaurantLoader(db_session)
        loader.upsert_restaurants(sample_df)
        rows = loader.get_active_restaurants(category="한식")
        assert len(rows) == 1
        assert rows[0].id == "k1"

    def test_min_score_filter(self, db_session, sample_df):
        loader = RestaurantLoader(db_session)
        loader.upsert_restaurants(sample_df)
        rows = loader.get_active_restaurants(min_score=80)
        assert len(rows) == 1
        assert rows[0].id == "k1"

    def test_get_by_id(self, db_session, sample_df):
        loader = RestaurantLoader(db_session)
        loader.upsert_restaurants(sample_df)
        r = loader.get_by_id("k2")
        assert r is not None
        assert r.name == "식당2"
        assert loader.get_by_id("nonexistent") is None

    def test_statistics(self, db_session, sample_df):
        loader = RestaurantLoader(db_session)
        loader.upsert_restaurants(sample_df)
        stats = loader.get_statistics()
        assert stats["total"] == 3
        assert stats["active"] == 3
        assert stats["categories"] == {"한식": 1, "일식": 1, "양식": 1}
        assert stats["avg_distance_m"] == pytest.approx((100 + 250 + 350) / 3)


# =============================================================================
# 통합: collect → transform → load
# =============================================================================
class TestFullPipelineFlow:
    def test_end_to_end(self, memory_engine, fake_kakao_key, sample_kakao_response):
        """Mock 카카오 응답으로 전체 파이프라인 통합 검증."""
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = sample_kakao_response
        mock_resp.raise_for_status = lambda: None

        with patch("requests.get", return_value=mock_resp), patch("time.sleep"):
            pipeline = RestaurantPipeline(ensure_schema=False)
            result = pipeline.run_pipeline()

        assert result.success is True
        assert result.raw_count == 5
        assert result.transformed_count == 4  # 중복 1건 제거
        assert result.inserted == 4
        assert result.updated == 0

        # DB 검증
        with get_session() as session:
            count = session.query(Restaurant).filter_by(is_active=True).count()
        assert count == 4

    def test_idempotent_re_run(self, memory_engine, fake_kakao_key, sample_kakao_response):
        """동일 응답으로 두 번 실행하면 두 번째는 모두 update."""
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = sample_kakao_response
        mock_resp.raise_for_status = lambda: None

        with patch("requests.get", return_value=mock_resp), patch("time.sleep"):
            pipeline = RestaurantPipeline(ensure_schema=False)
            r1 = pipeline.run_pipeline()
            pipeline2 = RestaurantPipeline(ensure_schema=False)
            r2 = pipeline2.run_pipeline()

        assert r1.inserted == 4 and r1.updated == 0
        assert r2.inserted == 0 and r2.updated == 4

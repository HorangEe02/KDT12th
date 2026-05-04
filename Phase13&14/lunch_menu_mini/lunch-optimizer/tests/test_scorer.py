"""
distance_scorer + RestaurantTransformer 단위 테스트.
"""
from __future__ import annotations

import math

import pandas as pd
import pytest

from pipeline.transformers.distance_scorer import (
    EARTH_RADIUS_M,
    RestaurantTransformer,
    calculate_distance_score,
    classify_menu_type,
    compute_distance_score,
    haversine_distance,
)


# =============================================================================
# Haversine
# =============================================================================
class TestHaversineDistance:
    def test_same_point_is_zero(self):
        assert haversine_distance(37.5665, 126.9780, 37.5665, 126.9780) == 0.0

    def test_symmetric(self):
        d1 = haversine_distance(37.5665, 126.9780, 37.5700, 126.9800)
        d2 = haversine_distance(37.5700, 126.9800, 37.5665, 126.9780)
        assert math.isclose(d1, d2, rel_tol=1e-9)

    def test_seoul_to_busan(self):
        d = haversine_distance(37.5665, 126.9780, 35.1796, 129.0756)
        assert 320_000 < d < 330_000

    def test_half_globe(self):
        d = haversine_distance(0, 0, 0, 180)
        assert math.isclose(d, math.pi * EARTH_RADIUS_M, rel_tol=1e-6)


# =============================================================================
# 거리 점수
# =============================================================================
class TestDistanceScoreBoundaries:
    @pytest.mark.parametrize(
        "distance,expected",
        [
            (0, 100), (50, 100), (100, 100),
            (101, 85), (200, 85),
            (250, 70), (300, 70),
            (350, 50), (400, 50),
            (401, 30), (1000, 30),
        ],
    )
    def test_compute(self, distance, expected):
        assert compute_distance_score(distance) == expected

    def test_alias_calculate(self):
        assert calculate_distance_score(150) == 85

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            compute_distance_score(-1)


# =============================================================================
# 메뉴 타입 분류
# =============================================================================
class TestClassifyMenuType:
    @pytest.mark.parametrize(
        "category,sub,expected",
        [
            ("한식", "국수/칼국수", "면류"),
            ("한식", "국/탕/찌개", "국물"),
            ("한식", "죽", "죽"),
            ("일식", "초밥/롤", "초밥"),
            ("일식", "라멘", "면류"),
            ("양식", "햄버거", "버거"),
            ("양식", "파스타", "면류"),
            ("카페", None, "카페"),
            (None, None, "기타"),
        ],
    )
    def test_cases(self, category, sub, expected):
        assert classify_menu_type(category, sub) == expected


# =============================================================================
# RestaurantTransformer
# =============================================================================
class TestRestaurantTransformer:
    def test_transform_basic(self, sample_kakao_documents):
        df = RestaurantTransformer.transform(sample_kakao_documents)
        # 5 입력 - 1 중복 = 4
        assert len(df) == 4
        assert {"id", "name", "category", "sub_category", "menu_type",
                "lat", "lng", "distance_m", "place_url", "collected_at"}.issubset(df.columns)

    def test_transform_category_parsing_3level(self, sample_kakao_documents):
        df = RestaurantTransformer.transform(sample_kakao_documents)
        row = df[df["id"] == "kakao-100"].iloc[0]
        assert row["category"] == "한식"
        assert row["sub_category"] == "국/탕/찌개"
        assert row["menu_type"] == "국물"

    def test_transform_category_parsing_2level(self, sample_kakao_documents):
        df = RestaurantTransformer.transform(sample_kakao_documents)
        row = df[df["id"] == "kakao-400"].iloc[0]
        assert row["category"] == "카페"
        assert row["sub_category"] is None
        assert row["menu_type"] == "카페"

    def test_transform_deduplication(self, sample_kakao_documents):
        df = RestaurantTransformer.transform(sample_kakao_documents)
        # kakao-100 은 두 번 들어왔지만 1건만 남아야
        assert len(df[df["id"] == "kakao-100"]) == 1

    def test_transform_sorted_by_distance(self, sample_kakao_documents):
        df = RestaurantTransformer.transform(sample_kakao_documents)
        distances = df["distance_m"].tolist()
        assert distances == sorted(distances)

    def test_transform_empty(self):
        df = RestaurantTransformer.transform([])
        assert df.empty

    def test_transform_handles_malformed(self):
        bad_docs = [{"missing_id": True}, {"id": "ok-1", "place_name": "OK"}]
        df = RestaurantTransformer.transform(bad_docs)
        assert len(df) == 1
        assert df.iloc[0]["id"] == "ok-1"

    def test_enrich_with_scores(self, sample_kakao_documents):
        df = RestaurantTransformer.transform(sample_kakao_documents)
        enriched = RestaurantTransformer.enrich_with_scores(df)
        assert "distance_score" in enriched.columns
        # 120m → 85, 250m → 70, 350m → 50, 450m → 30
        scores = dict(zip(enriched["id"], enriched["distance_score"]))
        assert scores["kakao-100"] == 85
        assert scores["kakao-200"] == 70
        assert scores["kakao-300"] == 50
        assert scores["kakao-400"] == 30

    def test_enrich_empty(self):
        df = RestaurantTransformer.enrich_with_scores(pd.DataFrame())
        assert df.empty

    def test_phone_empty_string_becomes_none(self, sample_kakao_documents):
        df = RestaurantTransformer.transform(sample_kakao_documents)
        row = df[df["id"] == "kakao-200"].iloc[0]
        assert row["phone"] is None

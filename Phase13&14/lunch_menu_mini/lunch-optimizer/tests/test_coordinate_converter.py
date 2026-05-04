"""
coordinate_converter 단위 테스트.
"""
from __future__ import annotations

import pytest

from pipeline.utils.coordinate_converter import grid_to_latlon, latlon_to_grid


class TestLatlonToGrid:
    @pytest.mark.parametrize(
        "lat,lon,expected",
        [
            # 기상청 공식 예제 — 내부 경계 케이스는 허용 오차 ±1 격자
            (37.5665, 126.9780, (60, 127)),
            (35.1796, 129.0756, (98, 76)),
        ],
    )
    def test_known_cities_exact(self, lat, lon, expected):
        assert latlon_to_grid(lat, lon) == expected

    def test_jeju_within_tolerance(self):
        """제주시청은 격자 경계 근처 (52 또는 53 허용)."""
        nx, ny = latlon_to_grid(33.4996, 126.5312)
        assert nx in (52, 53)
        assert ny == 38

    def test_returns_tuple_of_ints(self):
        result = latlon_to_grid(37.5, 127.0)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert all(isinstance(v, int) for v in result)


class TestRoundTrip:
    @pytest.mark.parametrize(
        "lat,lon",
        [(37.5665, 126.9780), (35.1796, 129.0756), (37.4979, 127.0276)],
    )
    def test_grid_to_latlon_close(self, lat, lon):
        """격자로 변환한 후 역변환하면 5km 격자 내 오차."""
        nx, ny = latlon_to_grid(lat, lon)
        rlat, rlon = grid_to_latlon(nx, ny)
        # 격자 5km 간격이므로 대략 ±0.05도 이내
        assert abs(rlat - lat) < 0.05
        assert abs(rlon - lon) < 0.05

"""
위경도(WGS84) ↔ 기상청 격자 좌표(nx, ny) 변환.

기상청 단기예보 API 는 Lambert Conformal Conic 투영 기반의
격자 좌표계를 사용한다. 본 모듈은 공식 변환 파라미터를
그대로 따라 구현한다.

검증 케이스:
    서울시청(37.5665, 126.9780) → (60, 127)
    부산시청(35.1796, 129.0756) → (98, 76)
    제주시청(33.4996, 126.5312) → (52, 38)
"""
from __future__ import annotations

import math
from typing import Final

# =============================================================================
# Lambert Conformal Conic 파라미터 (기상청 공식 값)
# =============================================================================
_RE: Final[float] = 6371.00877     # 지구 반경 (km)
_GRID: Final[float] = 5.0           # 격자 간격 (km)
_SLAT1: Final[float] = 30.0         # 표준 위도 1
_SLAT2: Final[float] = 60.0         # 표준 위도 2
_OLON: Final[float] = 126.0         # 기준점 경도
_OLAT: Final[float] = 38.0          # 기준점 위도
_XO: Final[float] = 43              # 기준점 격자 X
_YO: Final[float] = 136             # 기준점 격자 Y

_DEGRAD: Final[float] = math.pi / 180.0


def latlon_to_grid(lat: float, lon: float) -> tuple[int, int]:
    """
    위경도(WGS84) → 기상청 격자좌표 (nx, ny).

    Args:
        lat: 위도 (도 단위, 예: 37.5665)
        lon: 경도 (도 단위, 예: 126.9780)

    Returns:
        (nx, ny) 격자 좌표 정수 튜플

    Example:
        >>> latlon_to_grid(37.5665, 126.9780)
        (60, 127)
    """
    re = _RE / _GRID
    slat1 = _SLAT1 * _DEGRAD
    slat2 = _SLAT2 * _DEGRAD
    olon = _OLON * _DEGRAD
    olat = _OLAT * _DEGRAD

    sn = math.tan(math.pi * 0.25 + slat2 * 0.5) / math.tan(
        math.pi * 0.25 + slat1 * 0.5
    )
    sn = math.log(math.cos(slat1) / math.cos(slat2)) / math.log(sn)
    sf = math.tan(math.pi * 0.25 + slat1 * 0.5)
    sf = (sf ** sn) * math.cos(slat1) / sn
    ro = math.tan(math.pi * 0.25 + olat * 0.5)
    ro = re * sf / (ro ** sn)

    ra = math.tan(math.pi * 0.25 + lat * _DEGRAD * 0.5)
    ra = re * sf / (ra ** sn)
    theta = lon * _DEGRAD - olon
    if theta > math.pi:
        theta -= 2.0 * math.pi
    if theta < -math.pi:
        theta += 2.0 * math.pi
    theta *= sn

    nx = int(math.floor(ra * math.sin(theta) + _XO + 0.5))
    ny = int(math.floor(ro - ra * math.cos(theta) + _YO + 0.5))
    return nx, ny


def grid_to_latlon(nx: int, ny: int) -> tuple[float, float]:
    """
    기상청 격자좌표 → 위경도 (역변환, 디버깅용).
    """
    re = _RE / _GRID
    slat1 = _SLAT1 * _DEGRAD
    slat2 = _SLAT2 * _DEGRAD
    olon = _OLON * _DEGRAD
    olat = _OLAT * _DEGRAD

    sn = math.tan(math.pi * 0.25 + slat2 * 0.5) / math.tan(
        math.pi * 0.25 + slat1 * 0.5
    )
    sn = math.log(math.cos(slat1) / math.cos(slat2)) / math.log(sn)
    sf = math.tan(math.pi * 0.25 + slat1 * 0.5)
    sf = (sf ** sn) * math.cos(slat1) / sn
    ro = math.tan(math.pi * 0.25 + olat * 0.5)
    ro = re * sf / (ro ** sn)

    xn = nx - _XO
    yn = ro - ny + _YO
    ra = math.sqrt(xn * xn + yn * yn)
    if sn < 0.0:
        ra = -ra
    alat = (re * sf / ra) ** (1.0 / sn)
    alat = 2.0 * math.atan(alat) - math.pi * 0.5

    if abs(xn) <= 0.0:
        theta = 0.0
    elif abs(yn) <= 0.0:
        theta = math.pi * 0.5
        if xn < 0.0:
            theta = -theta
    else:
        theta = math.atan2(xn, yn)

    alon = theta / sn + olon
    return alat / _DEGRAD, alon / _DEGRAD

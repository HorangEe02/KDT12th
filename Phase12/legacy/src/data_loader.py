"""통합 데이터 로더 — Phase 2~4 담당자는 이 모듈만 import."""
from __future__ import annotations

import json
import logging
from typing import Callable, TypeVar

import pandas as pd

from src import config

log = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable)


def _noop_cache(*_args, **_kwargs):
    def decorator(func: F) -> F:
        return func
    return decorator


def _in_streamlit_runtime() -> bool:
    try:
        from streamlit.runtime import exists
        return bool(exists())
    except Exception:
        return False


if _in_streamlit_runtime():
    from streamlit import cache_data as _cache_data
else:
    _cache_data = _noop_cache


_SCHEDULE_DTYPES = {
    "game_id": "string",
    "day_of_week": "string",
    "home_team": "string",
    "away_team": "string",
    "stadium": "string",
    "start_time": "string",
    "broadcast": "string",
}

_STADIUM_DTYPES = {
    "stadium_name": "string",
    "short_name": "string",
    "home_team": "string",
    "city": "string",
    "address": "string",
    "lat": "float64",
    "lng": "float64",
    "capacity": "int64",
    "subway_station": "string",
}

_TEAM_STATS_DTYPES = {
    "year": "int64",
    "team": "string",
    "games_played": "int64",
    "wins": "int64",
    "losses": "int64",
    "draws": "int64",
    "win_rate": "float64",
    "home_win_rate": "float64",
    "away_win_rate": "float64",
    "final_rank": "int64",
}


def _ensure_exists(path, label: str) -> None:
    if not path.exists():
        raise FileNotFoundError(
            f"{label} 파일이 없습니다: {path}\n"
            f"먼저 `python scripts/seed_dummy_data.py`를 실행하세요."
        )


@_cache_data(ttl=config.DEFAULT_CACHE_TTL)
def load_schedule() -> pd.DataFrame:
    _ensure_exists(config.SCHEDULE_CSV, "KBO 경기 일정")
    df = pd.read_csv(
        config.SCHEDULE_CSV,
        dtype=_SCHEDULE_DTYPES,
        parse_dates=["date"],
        encoding="utf-8-sig",
    )
    return df


@_cache_data(ttl=config.DEFAULT_CACHE_TTL)
def load_stadiums() -> pd.DataFrame:
    _ensure_exists(config.STADIUMS_CSV, "구장 정보")
    return pd.read_csv(config.STADIUMS_CSV, dtype=_STADIUM_DTYPES, encoding="utf-8-sig")


@_cache_data(ttl=config.DEFAULT_CACHE_TTL)
def load_team_stats() -> pd.DataFrame:
    _ensure_exists(config.TEAM_STATS_CSV, "팀 전적")
    return pd.read_csv(config.TEAM_STATS_CSV, dtype=_TEAM_STATS_DTYPES, encoding="utf-8-sig")


@_cache_data(ttl=config.DEFAULT_CACHE_TTL)
def load_poi(stadium_short_name: str, category: str) -> list[dict]:
    if category not in config.CONTENT_TYPE:
        raise ValueError(f"지원하지 않는 카테고리: {category}")
    path = config.POI_CACHE_DIR / f"{stadium_short_name}_{category}.json"
    if not path.exists():
        log.warning("POI 캐시 없음: %s", path.name)
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        log.warning("POI JSON 파싱 실패 %s: %s", path.name, exc)
        return []


def load_all_data() -> dict:
    """Phase 1 통합 검증용. 모든 데이터를 단일 dict로 반환."""
    schedule = load_schedule()
    stadiums = load_stadiums()
    team_stats = load_team_stats()

    poi_counts: dict[str, int] = {}
    for _, row in stadiums.iterrows():
        short = row["short_name"]
        for cat in config.CONTENT_TYPE:
            key = f"{short}_{cat}"
            poi_counts[key] = len(load_poi(short, cat))

    return {
        "schedule": schedule,
        "stadiums": stadiums,
        "team_stats": team_stats,
        "poi_counts": poi_counts,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    data = load_all_data()
    print(f"경기 수      : {len(data['schedule'])}")
    print(f"구장 수      : {len(data['stadiums'])}")
    print(f"팀 기록 수   : {len(data['team_stats'])}")
    print(f"POI 캐시 합계: {sum(data['poi_counts'].values())}개")

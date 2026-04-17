"""LLM Function Calling 도구 정의 + 실제 실행 디스패처.

OpenAI 호환 tool_use 스키마를 Ollama가 수용.
도구 5종: search_game, predict_win_rate, get_weather, find_places, get_route
(+ 옵션 6종: search_knowledge — src/ai/rag.py 의존)
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Any

log = logging.getLogger(__name__)


TOOL_SCHEMAS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "search_game",
            "description": (
                "특정 팀의 원정 경기를 날짜 범위로 검색합니다. "
                "사용자가 '다음 원정 경기', '이번 주말 경기' 같은 질문을 할 때 호출하세요."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "team": {
                        "type": "string",
                        "description": "응원팀 약칭. 예: LG, KT, SSG, 두산, KIA, NC, 삼성, 롯데, 한화, 키움",
                    },
                    "start_date": {
                        "type": "string",
                        "description": "시작 날짜 YYYY-MM-DD. 생략 시 오늘.",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "종료 날짜 YYYY-MM-DD. 생략 시 start_date + 7일.",
                    },
                },
                "required": ["team"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "predict_win_rate",
            "description": (
                "특정 팀이 상대팀 원정에서 이길 확률을 로지스틱 회귀로 예측합니다. "
                "'LG vs KT 승률', '원정 가면 이길까?' 같은 질문에 호출하세요."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "team": {"type": "string", "description": "원정 팀 약칭"},
                    "opponent": {"type": "string", "description": "홈 팀 약칭"},
                },
                "required": ["team", "opponent"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": (
                "구장 좌표의 특정 날짜 날씨 예보 (기상청 단기예보). "
                "'비 올까?', '날씨 어때?' 질문에 호출하세요."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "stadium": {
                        "type": "string",
                        "description": "구장 short_name. 예: 잠실, 수원, 광주, 부산, 대구, 창원, 대전, 문학, 고척, 사직",
                    },
                    "target_date": {
                        "type": "string",
                        "description": "YYYY-MM-DD. 기본 오늘.",
                    },
                },
                "required": ["stadium"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_places",
            "description": (
                "구장 주변 맛집/숙소/관광지 POI 리스트를 조회합니다. "
                "'광주 맛집', '수원 숙소', '부산 관광지' 질문에 호출하세요."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "stadium": {
                        "type": "string",
                        "description": "구장 short_name. 예: 잠실, 수원, 광주 …",
                    },
                    "category": {
                        "type": "string",
                        "enum": ["food", "stay", "tour"],
                        "description": "food=음식점, stay=숙박, tour=관광지",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "최대 반환 개수 (기본 5, 최대 10)",
                    },
                },
                "required": ["stadium", "category"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_route",
            "description": (
                "출발지 → 경기장 자동차 경로 거리/시간/통행료를 조회합니다. "
                "'거리 얼마나 되나?', '얼마 걸려?' 질문에 호출하세요."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {
                        "type": "string",
                        "description": "출발지 (서울역, 강남역, 수원역, 대전역 중 하나 또는 '위도,경도')",
                    },
                    "destination_stadium": {
                        "type": "string",
                        "description": "목적지 구장 short_name",
                    },
                },
                "required": ["origin", "destination_stadium"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge",
            "description": (
                "구장별 원정 응원 팁·노하우를 의미 검색으로 조회합니다 (RAG). "
                "'어느 자리가 좋아?', '팁 알려줘' 질문에 호출하세요."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "검색 의도 한국어 문장"},
                    "stadium": {"type": "string", "description": "구장 필터 (선택)"},
                },
                "required": ["query"],
            },
        },
    },
]


_ORIGIN_PRESETS = {
    "서울역": (37.5547, 126.9707),
    "강남역": (37.4979, 127.0276),
    "수원역": (37.2657, 127.0009),
    "대전역": (36.3322, 127.4342),
    "부산역": (35.1159, 129.0416),
    "광주송정역": (35.1395, 126.7931),
    "동대구역": (35.8775, 128.6286),
}


def _parse_origin(origin: str) -> tuple[float, float] | None:
    if not origin:
        return None
    if origin in _ORIGIN_PRESETS:
        return _ORIGIN_PRESETS[origin]
    try:
        parts = [p.strip() for p in origin.split(",")]
        if len(parts) == 2:
            return (float(parts[0]), float(parts[1]))
    except (ValueError, AttributeError):
        pass
    return None


def _search_game(team: str, start_date: str | None = None, end_date: str | None = None) -> dict:
    import pandas as pd
    from src.data_loader import load_schedule

    df = load_schedule()
    away = df[df["away_team"] == team]
    if start_date:
        try:
            away = away[away["date"] >= pd.Timestamp(start_date)]
        except ValueError:
            pass
    if end_date:
        try:
            away = away[away["date"] <= pd.Timestamp(end_date)]
        except ValueError:
            pass
    rows = away.head(8).to_dict("records")
    for g in rows:
        g["date"] = str(g["date"].date()) if hasattr(g["date"], "date") else str(g["date"])
    return {"success": True, "data": {"games": rows, "count": len(rows)}}


def _predict_win_rate(team: str, opponent: str) -> dict:
    from src.ai.predict import load_model, predict_win_rate
    from src.data_loader import load_team_stats

    try:
        model = load_model()
    except FileNotFoundError:
        return {"success": False, "error": "승률 모델이 없습니다. `python -m src.ai.predict` 실행 후 재시도."}
    prob = predict_win_rate(team, opponent, load_team_stats(), model)
    return {
        "success": True,
        "data": {
            "team": team,
            "opponent": opponent,
            "win_probability": round(prob, 3),
            "win_percentage": f"{prob * 100:.1f}%",
        },
    }


def _get_weather(stadium: str, target_date: str | None = None) -> dict:
    from src.api.weather_api import get_forecast
    from src.data_loader import load_stadiums

    stadiums = load_stadiums()
    row = stadiums[stadiums["short_name"] == stadium]
    if row.empty:
        return {"success": False, "error": f"알 수 없는 구장: {stadium}"}
    r = row.iloc[0]
    dt = target_date or str(date.today())
    data = get_forecast(float(r["lat"]), float(r["lng"]), dt)
    return {"success": True, "data": data}


def _find_places(stadium: str, category: str, limit: int = 5) -> dict:
    from src.data_loader import load_poi

    limit = max(1, min(int(limit or 5), 10))
    items = load_poi(stadium, category)
    items_sorted = sorted(items, key=lambda p: int(p.get("dist_m") or 0))[:limit]
    compact = [
        {
            "title": p.get("title"),
            "addr": p.get("addr"),
            "dist_m": int(p.get("dist_m") or 0),
            "tel": p.get("tel", ""),
        }
        for p in items_sorted
    ]
    return {
        "success": True,
        "data": {"stadium": stadium, "category": category, "count": len(compact), "places": compact},
    }


def _get_route(origin: str, destination_stadium: str) -> dict:
    from src.api.kakao_map import get_car_route
    from src.data_loader import load_stadiums

    origin_pt = _parse_origin(origin)
    if origin_pt is None:
        return {
            "success": False,
            "error": f"알 수 없는 출발지: {origin}. 지원: {', '.join(_ORIGIN_PRESETS.keys())} 또는 '위도,경도'",
        }
    stadiums = load_stadiums()
    row = stadiums[stadiums["short_name"] == destination_stadium]
    if row.empty:
        return {"success": False, "error": f"알 수 없는 구장: {destination_stadium}"}
    r = row.iloc[0]
    result = get_car_route(origin_pt, (float(r["lat"]), float(r["lng"])))
    return {
        "success": True,
        "data": {
            "origin": origin,
            "destination_stadium": destination_stadium,
            "distance_km": round((result.get("distance_m") or 0) / 1000, 1),
            "duration_min": (result["duration_sec"] // 60) if result.get("duration_sec") else None,
            "toll_fare": result.get("toll_fare"),
            "fallback": bool(result.get("fallback")),
        },
    }


def _search_knowledge(query: str, stadium: str | None = None) -> dict:
    try:
        from src.ai.rag import search_tips
    except ImportError:
        return {"success": False, "error": "RAG 모듈이 아직 초기화되지 않았습니다."}
    try:
        tips = search_tips(query, stadium=stadium, top_k=3)
        return {"success": True, "data": {"tips": tips}}
    except Exception as exc:
        return {"success": False, "error": f"RAG 검색 실패: {exc}"}


_DISPATCH = {
    "search_game": _search_game,
    "predict_win_rate": _predict_win_rate,
    "get_weather": _get_weather,
    "find_places": _find_places,
    "get_route": _get_route,
    "search_knowledge": _search_knowledge,
}


def execute_tool(name: str, arguments: dict) -> dict:
    """LLM 도구 호출 실행. 항상 {success, data|error} dict 반환."""
    fn = _DISPATCH.get(name)
    if fn is None:
        return {"success": False, "error": f"알 수 없는 도구: {name}"}
    try:
        args = arguments or {}
        return fn(**args)
    except TypeError as exc:
        log.warning("도구 %s 인자 오류: %s", name, exc)
        return {"success": False, "error": f"인자 오류: {exc}"}
    except Exception as exc:
        log.warning("도구 %s 실행 실패: %s", name, exc)
        return {"success": False, "error": f"실행 실패: {exc}"}


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    tests = [
        ("search_game", {"team": "LG", "start_date": "2026-04-18", "end_date": "2026-04-25"}),
        ("predict_win_rate", {"team": "LG", "opponent": "KT"}),
        ("find_places", {"stadium": "광주", "category": "food", "limit": 3}),
        ("get_route", {"origin": "서울역", "destination_stadium": "광주"}),
    ]
    for name, args in tests:
        res = execute_tool(name, args)
        print(f"\n--- {name}({args}) ---")
        print(json.dumps(res, ensure_ascii=False, default=str)[:500])

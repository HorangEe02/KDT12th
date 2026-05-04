"""
8 Tool Function schemas — Ollama / OpenAI-style JSON Schema.

These are the tools the LLM can call during a chat turn. Each entry mirrors
an existing lunch-optimizer or NLP endpoint, so adding a new tool is usually
just a matter of pointing at another FastAPI route.

다중 식사 시간(헤비 옵션) 지원: 추천/투표/기록 도구는 meal_type 파라미터로
아침/점심/저녁을 구분한다. 기본값은 "any" (시간대 무관).

Format reference:
    https://ollama.com/blog/tool-support (Ollama)
    https://platform.openai.com/docs/guides/function-calling (OpenAI)
"""
from __future__ import annotations

from typing import Any

# 식사 시간 파라미터 — 여러 도구가 공유
_MEAL_TYPE_PARAM: dict[str, Any] = {
    "type": "string",
    "enum": ["breakfast", "lunch", "dinner", "any"],
    "description": (
        "식사 시간 — breakfast(아침)/lunch(점심)/dinner(저녁)/any(무관). "
        "사용자 query에 [아침]/[점심]/[저녁] prefix가 있거나 시간 키워드(아침/브런치/점심/저녁/회식)가 "
        "있으면 그에 맞춰 지정. 모호하면 any."
    ),
    "default": "any",
}


TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_meal_recommendations",
            "description": (
                "4축 종합 식사 추천 (거리+날씨+영양+팀선호)을 조회한다. "
                "사용자가 '뭐 먹지?', '추천해줘', '아침/점심/저녁 추천' 처럼 일반 추천을 요청할 때 사용. "
                "meal_type 으로 시간대를 명시하면 적합한 카테고리만 필터됨 "
                "(아침=카페/베이커리/죽/김밥, 저녁=한식/일식/고깃집/회식)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "team_id": {
                        "type": "string",
                        "description": "팀 ID (기본: team1)",
                        "default": "team1",
                    },
                    "user_id": {
                        "type": "string",
                        "description": "사용자 ID (기본: user1)",
                        "default": "user1",
                    },
                    "top_n": {
                        "type": "integer",
                        "description": "추천 개수 (1~20)",
                        "default": 5,
                    },
                    "meal_type": _MEAL_TYPE_PARAM,
                },
                "required": [],
            },
        },
    },
    # 하위 호환 alias — 기존 클라이언트가 get_lunch_recommendations 를 부르던 경우
    {
        "type": "function",
        "function": {
            "name": "get_lunch_recommendations",
            "description": (
                "[Deprecated alias of get_meal_recommendations] "
                "점심 추천 (meal_type=lunch 와 동일). 신규 코드는 get_meal_recommendations 사용 권장."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "team_id": {"type": "string", "default": "team1"},
                    "user_id": {"type": "string", "default": "user1"},
                    "top_n": {"type": "integer", "default": 5},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": (
                "현재 날씨·미세먼지·강수확률 정보와 식사 추천 팁을 조회한다. "
                "사용자가 날씨를 묻거나 '비 와?', '추워?' 등 날씨 관련 질문 시 사용."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_nutrition_diagnosis",
            "description": (
                "사용자의 이번 주 영양 섭취 진단을 조회한다. "
                "'이번 주 영양은?', '단백질 부족해?', '아침/저녁 식사 균형' 등 영양 상태 질문 시 사용."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "사용자 ID",
                        "default": "user1",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_restaurant_info",
            "description": (
                "특정 음식점의 상세 정보 (거리/카테고리/영양/좌표) 를 조회한다. "
                "사용자가 구체적인 음식점 이름을 언급하거나 '거기 얼마야?' 등의 질문 시 사용."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "restaurant_id": {
                        "type": "string",
                        "description": "음식점 ID (예: R001)",
                    },
                },
                "required": ["restaurant_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cast_vote",
            "description": (
                "사용자 대신 식사 투표를 행사한다. 쓰기 작업이므로 사용자가 "
                "'○○에 투표해줘', '○○로 결정' 이라고 명시적으로 요청할 때만 사용. "
                "meal_type 을 함께 받으면 어느 식사 시간 투표인지 라벨링."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "사용자 ID"},
                    "restaurant_id": {
                        "type": "string",
                        "description": "투표할 음식점 ID",
                    },
                    "meal_type": _MEAL_TYPE_PARAM,
                },
                "required": ["user_id", "restaurant_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_vote_status",
            "description": (
                "현재 진행 중인 팀 투표 현황(득표수, 참여율, 임시 우승자)을 조회한다. "
                "'투표 어떻게 돼가?', '몇 명이나 투표했어?' 등의 질문 시 사용."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "team_id": {
                        "type": "string",
                        "description": "팀 ID",
                        "default": "team1",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "record_meal",
            "description": (
                "사용자의 식사를 기록한다. 쓰기 작업이므로 '○○ 먹었어', "
                "'방금 ○○ 먹고 왔어' 등 명시적 기록 요청 시에만 사용. "
                "meal_type 으로 아침/점심/저녁 구분 (생략 시 시각 기반 자동 추정)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "사용자 ID"},
                    "restaurant_id": {
                        "type": "string",
                        "description": "방문 음식점 ID",
                    },
                    "menu_name": {
                        "type": "string",
                        "description": "먹은 메뉴 이름 (선택)",
                    },
                    "satisfaction": {
                        "type": "integer",
                        "description": "만족도 1~5점 (선택)",
                    },
                    "meal_type": _MEAL_TYPE_PARAM,
                },
                "required": ["user_id", "restaurant_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_visit_history",
            "description": (
                "최근 팀 방문 이력 (어제/지난주 뭐 먹었는지) 을 조회한다. "
                "'어제 뭐 먹었지?', '이번 주에 중복 없이 추천해줘' 등에 사용. "
                "meal_type 으로 특정 식사 시간만 필터 가능."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "team_id": {
                        "type": "string",
                        "description": "팀 ID",
                        "default": "team1",
                    },
                    "days": {
                        "type": "integer",
                        "description": "조회 기간 (일)",
                        "default": 10,
                    },
                    "meal_type": _MEAL_TYPE_PARAM,
                },
                "required": [],
            },
        },
    },
]

TOOL_NAMES: list[str] = [t["function"]["name"] for t in TOOL_DEFINITIONS]


def get_tool_schema(name: str) -> dict[str, Any] | None:
    """Return the JSON schema for a named tool (or None if unknown)."""
    for t in TOOL_DEFINITIONS:
        if t["function"]["name"] == name:
            return t
    return None

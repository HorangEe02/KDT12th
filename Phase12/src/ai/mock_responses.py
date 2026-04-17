"""시연 안전장치 — Ollama 서버 OFF 시 재생할 사전 녹화 응답.

발표 당일 네트워크·서버 이슈 대비. 사이드바 '🎬 시연 모드' 토글로 강제 활성화 가능.
"""
from __future__ import annotations

MOCK_RESPONSES: list[dict] = [
    {
        "keywords": ["광주", "가족", "아이", "1박"],
        "query_sample": "광주 원정 1박 2일, 아이랑 가려는데 추천해줘",
        "response": (
            "어이~ 광주 원정이시군요! 1일차 경기 전에는 '1913송정역시장'에서 아이랑 간식 드시고 "
            "KIA 챔피언스필드 1루 외야석 추천드려요(햇빛 피할 수 있어요). 저녁은 '영미오리탕'(3만원대, "
            "어린이 메뉴 있음), 숙소는 첨단지구 비즈니스호텔(15만원대)이면 예산 30만원 내에서 무난합니다.\n\n"
            "2일차는 국립아시아문화전당 어린이체험관 3시간 즐기고 송정역에서 상경하시면 되고요. "
            "정확한 위치·거리는 탭 2 '동선 지도'에서 확인해 주세요!"
        ),
        "tool_calls_shown": ["search_game", "find_places", "get_route"],
    },
    {
        "keywords": ["부산", "맛집", "사직"],
        "query_sample": "이번 주말 부산 맛집 세 곳 알려줘",
        "response": (
            "부산 사직구장 근처 추천 세 곳 드릴게예:\n\n"
            "1. **할매집** — 돼지국밥 원조 (1만원대, 경기 전 든든하게)\n"
            "2. **해운대 밀면** — 여름 필수 (9천원)\n"
            "3. **광안리 회타운** — 경기 후 회식 추천 (3만원대)\n\n"
            "지도 탭에서 정확한 위치와 경기장에서의 거리를 확인해 주세요. "
            "사직 도보 5분 거리부터 해운대·광안리까지 지하철 30분 이내입니다."
        ),
        "tool_calls_shown": ["find_places"],
    },
    {
        "keywords": ["비", "우천", "실내", "관광"],
        "query_sample": "비 올 확률 높으면 실내 관광지는?",
        "response": (
            "우천 대비 실내 코스 드립니다:\n\n"
            "- **광주**: 국립아시아문화전당 (성인 5천원, 어린이 체험관 있음)\n"
            "- **부산**: 부산현대미술관(무료), 롯데월드 어드벤처 부산(3만원대)\n"
            "- **대구**: 간송미술관 대구관(1만원)\n"
            "- **서울(잠실·고척)**: 롯데월드몰, 아쿠아리움\n\n"
            "경기장별 우천 확률은 탭 2 '동선 지도'의 경기장 마커를 클릭하시면 확인 가능해요. "
            "강수 확률 60% 이상이면 '☔ 우산 필수' 배지가 표시됩니다."
        ),
        "tool_calls_shown": ["get_weather"],
    },
]


def get_mock_response(query: str) -> dict | None:
    """쿼리 키워드 매칭으로 가장 적합한 mock 응답 선택."""
    if not query:
        return None
    q_lower = query.lower()
    best: dict | None = None
    best_score = 0
    for mock in MOCK_RESPONSES:
        score = sum(1 for k in mock["keywords"] if k.lower() in q_lower)
        if score > best_score:
            best_score = score
            best = mock
    if best_score == 0:
        return None
    return best


FALLBACK_RESPONSE: dict = {
    "response": (
        "AI 서비스가 일시적으로 응답하지 않습니다. 좌측 사이드바에서 팀·기간을 선택하시면 "
        "탭 1~3에서 경기 일정·지도·맛집 정보를 직접 확인하실 수 있어요. "
        "Ollama 서버 상태는 `curl http://localhost:11434/api/tags`로 점검해 주세요."
    ),
    "tool_calls_shown": [],
}

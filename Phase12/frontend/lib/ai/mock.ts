/**
 * 시연 안전장치 — Gemini/네트워크 장애 대비 사전 녹화 Mock 응답.
 * 포팅 원본: src/ai/mock_responses.py
 *
 * 매칭 규칙: 사용자 질문의 키워드 조합으로 3 시나리오 중 선택.
 * 없으면 null → 실제 LLM 호출.
 */

export interface MockScenario {
  id: string;
  keywords: string[][]; // 모든 그룹 중 하나 이상의 키워드 필요 (AND-of-OR)
  title: string;
  reply: string;
}

export const MOCK_SCENARIOS: MockScenario[] = [
  {
    id: "gwangju-family",
    keywords: [
      ["광주", "KIA"],
      ["가족", "아이", "어린이"],
    ],
    title: "광주 가족 원정",
    reply: `어이~ 광주 가족 원정이시군요! 경기 전에는 **1913송정역시장**에서 아이랑 간식 드시고
KIA 챔피언스필드 **1루 외야석**을 추천드려요 (햇빛 피할 수 있어요).

**저녁 추천**
- 영미오리탕 (3만원대 · 어린이 메뉴 있음)
- 첨단지구 비즈니스호텔 (15만원대)

**2일차 코스**
- 국립아시아문화전당 어린이체험관 3시간
- 상경 경로: 광주송정역 → KTX 서울 (1시간 52분)

지도 탭에서 실제 위치와 동선을 확인하실 수 있습니다. 🎒`,
  },
  {
    id: "busan-food",
    keywords: [
      ["부산", "사직", "롯데"],
      ["맛집", "먹을", "음식", "식당"],
    ],
    title: "부산 맛집 추천",
    reply: `부산 원정 오셨어예! 사직구장 주변은 돼지국밥 성지입니다.

**구장 도보 5분**
- 합천일류돼지국밥 (9,000원 · 밤 늦게 영업)
- 수요회장 (밀면 · 8,000원대)
- 밀양돼지국밥 본점 (돼지국밥 명소)

**경기 후 추천**
- 광안리 해수욕장 (10km · 택시 20분)
- 흰여울문화마을 (감성샷 스팟)

맛집 탭에서 거리-평점 분포와 전화번호를 확인하세요 🍜`,
  },
  {
    id: "rainy-day",
    keywords: [
      ["비", "우천", "비올", "취소"],
      [],
    ],
    title: "우천 대비 실내 코스",
    reply: `우천 확률이 높으신가 봐요. 경기 취소 대비 **지역별 실내 플랜 B**를 추천드립니다.

| 지역 | 추천 실내 코스 |
|---|---|
| 광주 | 국립아시아문화전당 (성인 5,000원 · 3시간) |
| 부산 | 부산현대미술관 · 롯데월드 어드벤처 부산 |
| 대구 | 간송미술관 대구관 · 대구미술관 |
| 창원 | 창원SM타운 · 더시티세븐 |
| 대전 | 국립중앙과학관 · 한밭수목원 열대식물원 |

지도 탭의 **구장 마커 팝업**에서 해당 지역 우천 확률을 확인하실 수 있어요.
경기 취소 시 티켓 환불은 KBO 공식 앱에서 자동 처리됩니다. ☂️`,
  },
];

export function pickMock(userQuery: string): MockScenario | null {
  const q = userQuery.toLowerCase();
  for (const sc of MOCK_SCENARIOS) {
    let matched = true;
    for (const group of sc.keywords) {
      if (group.length === 0) continue;
      const hit = group.some((k) => q.includes(k.toLowerCase()));
      if (!hit) {
        matched = false;
        break;
      }
    }
    if (matched) return sc;
  }
  return null;
}

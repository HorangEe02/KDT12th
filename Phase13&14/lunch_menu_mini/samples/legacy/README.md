# legacy/

Mini Next.js 마이그레이션 (M1~M10) 이전의 레거시 자산.

## 파일

### `lunch-optimizer-dashboard.jsx.bak`

- **출처:** `Mini/lunch-optimizer-dashboard.jsx` (2026-04-08 Step 5 기준)
- **크기:** ~1,458 lines, 인라인 CSS + `useState`/`useEffect`
- **구성:** 단일 파일 React 컴포넌트 · 7개 탭(Discovery/Weather/Nutrition/Vote/AI 추천/Concierge/Insights)
- **이유:** Next.js 16 + Tailwind v4 + TanStack Query 기반 `dashboard-web/` 으로 완전 이식 완료 (M10). 시각 레퍼런스 및 롤백 보험 목적으로 보존.

## 언제 다시 쓰나

- 새 페이지가 레거시와 시각적으로 다르게 보여 비교가 필요할 때
- 특정 스코어링 로직/차트 구성이 누락되지 않았는지 확인할 때
- `dashboard-web/` 기반 전환에 롤백이 필요한 비상 상황

## 새 구현 위치

| 기능 | 레거시 위치 | 신규 위치 |
|---|---|---|
| 점수 함수 (distance/weather/nutrition/composite) | L53-94 | `dashboard-web/src/lib/scoring.ts` |
| Mock 상수 | L6-50 | `dashboard-web/src/lib/mock.ts` |
| RestaurantCard + SentimentBadge | L112-207 | `dashboard-web/src/components/discover/` |
| TabRestaurants (Discovery) | L209-278 | `dashboard-web/src/app/discover/page.tsx` |
| TabWeather | L365-476 | `dashboard-web/src/app/weather/` + `components/weather/` |
| TabNutrition + AICommentCard | L478-580 + L960+ | `dashboard-web/src/app/nutrition/` + `components/nutrition/` |
| TabTeamVote | L582-733 | `dashboard-web/src/app/vote/` + `components/vote/` |
| TabConcierge (SSE) | L1018+ | `dashboard-web/src/app/concierge/` + `components/concierge/` + NLP `/chat/stream` |
| TabInsights (NLP 5-카드) | L1159+ | `dashboard-web/src/app/insights/` + `components/insights/` |

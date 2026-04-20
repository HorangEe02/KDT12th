# 📱 옵션 B — Mobile UIUX 정밀 반영 상세 구현 계획

> 작성: 2026-04-19 · 부모 문서: 옵션 A 완료 후 후속 작업
> 출처: `uiux/mobile_uiux/` 9개 mockup 정밀 분석
> 범위: 7개 모바일 mockup → 7개 페이지/Shell 컴포넌트 정밀 반영

---

## 0. 한눈에 — 현재 vs mockup 갭 매트릭스

| 페이지 | mockup | 옵션 A 적용 | 옵션 B 갭 (정밀 반영 시 차이) | 작업 시간 | 우선순위 |
|---|---|---|---|---|---|
| `/` Landing | `landing_hero_mobile` | ✅ Hero 자동 반응형 | center+풀스크린 BG + 영문 hero + Bento team grid + Start Planning CTA | 1.5h | P2 (현재 OK) |
| `/login`, `/signup` | `login_signup_mobile` | ✅ 슬라이드업 적용 | 거의 일치 | 0.2h | ✅ 완료 |
| `/admin` | `admin_dashboard_mobile` | ✅ Welcome+Bento 적용 | 거의 일치 | 0.2h | ✅ 완료 |
| `/matches` | `matches_predictions_mobile` | ❌ 미적용 (web 그대로) | Mobile 헤더 + Hero VS card + Bento Matrix | 2.5h | **P0** |
| `/map` | `itinerary_route_map_mobile` | ❌ 미적용 | 풀스크린 지도 + Floating top/bottom card + Stops list | 3h | **P0** |
| `/places` | `eats_stays_mobile` | ❌ 미적용 | Search + Filter chips + Hotel-style cards + Map FAB | 2.5h | **P1** |
| `/ai` | `ai_travel_planner_chat_mobile` | ❌ 미적용 | Chat bubble + Itinerary card + Glass input + Action chips | 2h | **P1** |
| `/badges` | `my_badges_records_mobile` | ❌ 미적용 | Stadium Tour bento + Achievement scroll + Timeline | 2.5h | **P2** |

**총합**: 약 14.5시간 (P0~P2 전체) · P0 만 = 5.5시간

---

## 1. 공통 인프라 — 모바일 전용 BottomNav (선행 필수)

### 1-1. 현재 구조 vs mockup
- **현재**: `TopNav` (데스크톱 horizontal nav) 만 존재. 모바일도 동일 nav.
- **mockup**: 모든 모바일 mockup 이 **하단 고정 BottomNav 5탭** 사용 (Matches / Map / Stays / AI / Badges) + 활성 탭은 **녹색 fill 원형 pill** (scale-110)

### 1-2. 신규 컴포넌트
- [`components/nav/mobile-bottom-nav.tsx`](frontend/components/nav/mobile-bottom-nav.tsx) 🆕
  - `md:hidden` (모바일 전용)
  - 5탭 + 활성 표시 (녹색 pill + scale-110)
  - 라우트 동적 active 감지 (`usePathname`)
  - 진동 피드백 (active:scale-90)
- [`components/nav/mobile-top-bar.tsx`](frontend/components/nav/mobile-top-bar.tsx) 🆕
  - 페이지마다 다른 mobile header (햄버거 + 타이틀 + 우측 액션)
  - Sticky top + backdrop blur
  - 또는 페이지마다 inline 헤더로 처리

### 1-3. (shell) layout 통합
- [`app/(shell)/layout.tsx`](frontend/app/(shell)/layout.tsx)
  - 데스크톱: 기존 `TopNav` + `Sidebar`
  - 모바일: `MobileBottomNav` 표시 + `TopNav`/`Sidebar` 숨김
  - main 영역 `pb-24 md:pb-0` (BottomNav 공간)

### 1-4. 작업 시간
- 약 1시간 (디자인 픽셀 매칭 포함)
- **P0 — 모든 모바일 페이지의 전제 조건**

---

## 2. 페이지별 상세 계획

### 📌 2-1. `/matches` (P0 · 2.5h)

#### Mockup 핵심 요소
```
[Mobile Header] "Matches" 큰 헤딩 + 우측 tune 필터 버튼
[Section: Upcoming Fixture]
  [Live Odds 표시]
  [Hero Card] 팀1 로고 (Home 배지) ─ VS ─ 팀2 로고 (Away 배지)
                  18:30 KST
              [승률 게이지 LG 52% / NC 48%]
              [View Detailed Analysis CTA]
[Section: Away Matrix]
  [Card 1] 이동수단 아이콘 + vs SSG + Tomorrow 배지 + 22°C + 3 Stays chips
  [Card 2] vs Lotte + Oct 12 + 18°C
```

#### 신규 / 수정 컴포넌트
| 파일 | 역할 |
|---|---|
| `app/(shell)/matches/mobile-page.tsx` 🆕 | 모바일 전용 layout (md:hidden) |
| `components/matches/upcoming-fixture-hero.tsx` 🆕 | VS 대결 hero card + 승률 게이지 |
| `components/matches/away-matrix-card.tsx` 🆕 | 다음 원정 경기 bento card |
| `app/(shell)/matches/page.tsx` (수정) | 데스크톱(기존) + 모바일(`md:hidden`) 분기 |

#### 데이터 매핑
- `Upcoming Fixture` = filterAwayGames 첫 번째 row
- `Away Matrix` = 다음 5개 원정 경기
- 승률 = 기존 `predict.ts` 활용
- 날씨 = `lib/api/weather.ts` 호출 (Tomorrow / +3day)

#### 트레이드오프
- 기존 `/matches` 의 Plotly 차트 (gauge, bar) 는 데스크톱 유지, 모바일은 mockup 의 단순 progress bar
- 한국어: "Upcoming Fixture" → "다가오는 경기", "Away Matrix" → "원정 일정"

---

### 📌 2-2. `/map` (P0 · 3h · 가장 복잡)

#### Mockup 핵심 요소
```
[풀스크린 지도 배경] (현재 Leaflet 그대로)
[Floating Top]
  [< back] [Seoul Itinerary 라벨] [⋮]
[Floating Bottom Card]
  [Game Day Route 헤딩] [Optimal 배지]
  3 Stops • 45m Total Transit
  [Stop 1] hotel icon + Shilla Stay + 2:00 PM
  [Stop 2] restaurant icon + Jamsil BBQ + 4:30 PM
  [Stop 3] sports_baseball icon + Stadium + Live dot + 6:30 PM
  [Start Navigation CTA] (gradient + 화살표 아이콘)
[Bottom Nav] (Map 활성)
```

#### 신규 / 수정 컴포넌트
| 파일 | 역할 |
|---|---|
| `components/map/floating-top-bar.tsx` 🆕 | 뒤로 + 라벨 + 더보기 (모바일 only) |
| `components/map/journey-summary-card.tsx` 🆕 | 하단 floating card (Stops + Navigate CTA) |
| `app/(shell)/map/page.tsx` (수정) | 데스크톱: 기존 layout · 모바일: 풀스크린 지도 + floating |

#### 데이터 매핑
- Stops 리스트 = 출발지 → 식당(가까운 1개) → 경기장 (3 stops)
- "45m Total Transit" = `requestRoute` 의 `duration_min` (이미 있음)
- Optimal 배지 = `route.source === "kakao"` 면 "정밀", "osrm" 이면 "최적", "haversine" 이면 "직선"
- Live dot = `selectedGame.date === today` 일 때만 표시

#### 트레이드오프
- 모바일 hero 글씨 크기는 `text-xl` 이하로 강제
- Sidebar 의 출발지 그룹 버튼은 모바일에서 숨기거나 floating sheet 로 이동

---

### 📌 2-3. `/places` (P1 · 2.5h)

#### Mockup 핵심 요소
```
[Header] "Find Stays" 큰 헤딩
[Search Bar] rounded full + 검색 아이콘 + tune 버튼
[Filter Chips Horizontal Scroll] All / Near Stadium / Luxury / Budget / Pet Friendly
[Hotel Cards Vertical List]
  [Card] 썸네일(1/3) + 정보(2/3): 별점 / 이름 / 거리 / 카테고리 chips / 가격 (할인전/후)
  [Recommended] = 좌측 secondary-fixed 1px accent bar
[Floating FAB] Map View (모바일) 또는 우측 하단 button (데스크톱)
[Bottom Nav] (Stays 활성)
```

#### 신규 / 수정 컴포넌트
| 파일 | 역할 |
|---|---|
| `components/places/places-search-bar.tsx` 🆕 | 검색 + 필터 토글 |
| `components/places/places-filter-chips.tsx` 🆕 | 카테고리 horizontal scroll chips |
| `components/places/poi-card-mobile.tsx` 🆕 | 썸네일 좌 + 정보 우 (높이 128px 고정) |
| `components/places/places-map-fab.tsx` 🆕 | floating action button (지도로 이동) |
| `app/(shell)/places/page.tsx` (수정) | 데스크톱(기존) + 모바일 분기 |

#### 데이터 매핑
- 검색: 클라이언트 필터 (POI 이름)
- Filter chips: All / 음식점 / 숙박 / 관광지 (기존 카테고리 분리 유지)
- 썸네일: TourAPI 의 `firstimage` (이미 데이터에 있음 — 없으면 카테고리 기본 이미지)
- 거리: `dist_m / 1000 + "km to {stadium}"`
- 가격: TourAPI 데이터 없음 → 별점만 표시 (또는 hide)
- Recommended: `dist_m < 500` (반경 500m)

#### 트레이드오프
- mockup 의 가격 표시는 호텔 데이터 없으니 생략 또는 "주변" 라벨 변경
- Pet Friendly 같은 chips 는 데이터 없으니 "신상" / "인기" / "근처" 같은 한국 chips

---

### 📌 2-4. `/ai` (P1 · 2h)

#### Mockup 핵심 요소
```
[AI Greeting Bubble] 좌측, glass effect, AI avatar (auto_awesome) + greeting
[User Request Bubble] 우측, primary gradient, 사용자 avatar + 요청
[AI Response]
  [Text bubble] "Excellent choice. ..."
  [Itinerary Card] accent bar + 헤딩 + Confirmed 배지
    [Event] hotel icon + 호텔명 + 시간/위치
    [Event] restaurant icon + 식당명 + 시간
    [Event] sports_baseball icon + 경기명 + 시간 + Tickets CTA
[Action Chips] Book Itinerary / Modify Hotel
[Bottom Glass Input] rounded full + 입력 필드 + send 원형 버튼
[Bottom Nav] (AI 활성, scale-110 pill)
```

#### 신규 / 수정 컴포넌트
| 파일 | 역할 |
|---|---|
| `components/ai/chat-bubble.tsx` (수정) | glass-effect 스타일 통일 (current: 단순 bubble) |
| `components/ai/itinerary-card.tsx` 🆕 | accent bar + 이벤트 list + Confirmed 배지 + CTA |
| `components/ai/action-chips.tsx` 🆕 | Book / Modify / Re-plan chips |
| `components/ai/glass-input.tsx` 🆕 | floating glass + send 원형 버튼 (현재 `chat-ui.tsx` 의 input 영역 교체) |
| `components/ai/chat-ui.tsx` (수정) | 위 컴포넌트들 통합 |

#### 데이터 매핑
- AI greeting = "안녕하세요. KBO 컨시어지입니다. 어떤 원정을 도와드릴까요?"
- Itinerary card = AI 가 tool call 한 결과 (search_game + find_places + get_route 합성)
- Action chips: Book → "이 코스 저장", Modify → "다른 옵션", Re-plan → "처음부터"

#### 트레이드오프
- 기존 `tool-viz.tsx` (도구 호출 시각화) 유지 — itinerary card 와 별개
- Bottom input 위치: bottom-[88px] (BottomNav 위) 정확 픽셀 매칭

---

### 📌 2-5. `/badges` (P2 · 2.5h)

#### Mockup 핵심 요소
```
[Hero Title] "Records" + 부제 "Your KBO Journey & Achievements"
[Stadium Tour Bento]
  [헤더] Stadium Tour + "3 of 9 Visited" + explore 아이콘
  [2x2 Grid] 구장 사진 카드 (방문 시 체크마크 + 이름 + 도시)
[Achievement Badges Horizontal Scroll]
  [Badge] gradient 원형 + 아이콘 + 이름(2줄) + 날짜 (locked 시 grayscale)
[Away Timeline]
  [Item] 좌측 dot + 연결선 + 카드 [W/L 배지 + 날짜 + 매치 + 위치]
[Bottom Nav] (Badges 활성)
```

#### 신규 / 수정 컴포넌트
| 파일 | 역할 |
|---|---|
| `components/badges/stadium-tour-bento.tsx` 🆕 | 2x2 grid 사진 카드 (mobile 전용) |
| `components/badges/achievement-scroll.tsx` 🆕 | horizontal scroll badge list |
| `components/badges/away-timeline.tsx` 🆕 | timeline dot + line + 카드 |
| `components/badges/stadium-tour.tsx` (수정) | 기존 데스크톱 5x2 grid 유지 + 모바일 분기 |

#### 데이터 매핑
- 구장 사진: 기존 `stadiums.json` 에 사진 URL 없음 → Unsplash 무료 이미지 또는 팀 컬러 그라디언트 placeholder
- Achievement badges: 신규 데이터 (예: "첫 원정", "5 구장 방문", "10 구장 정복", "3시즌 연속")
- Away Timeline: `user_plans` 또는 `user_visits.perStadium` 의 lastAt 기록 활용

#### 트레이드오프
- Achievement badges 데이터는 신규 도입 필요 (간단한 클라이언트 계산 가능)
- Away Timeline 은 user_plans 의 createdAt 또는 user_visits 만 사용 (단순화)

---

### 📌 2-6. `/` Landing (P2 · 1.5h)

옵션 A 가 현재 잘 동작 중이라 **선택적**. mockup 정밀 반영 시:

#### Mockup 핵심 요소
```
[풀스크린 stadium BG image] (opacity 20% mask)
[중앙 정렬 텍스트]
  "Welcome to the Big Leagues" (작은 secondary 라벨)
  "Your Away Game / Companion." (4xl, 한국어 유지: "원정 응원 컴패니언" 또는 "원정 응원 플래너")
  "Curated travel itineraries..." 부제
[Bento Card] Select Your Team
  [3x3 grid] 원형 팀 로고 + 짧은 라벨
[Primary CTA] Start Planning + 화살표 (signature gradient)
```

#### 신규 / 수정
- 현재 `Hero` + `TeamSelector` + `NEXT_TABS` grid 구조와 다름
- mockup 정밀 반영하려면 Landing 자체를 `LandingHeroMobile` 컴포넌트로 분리

#### 결정 필요
- Mockup 의 "center + 풀스크린 BG" vs 현재 "그라디언트 카드 + 5탭 링크"
- 후자가 한국 사용자 데이터 풍부 보여주기 좋음 → **현재 유지 권장**

---

## 3. 우선순위 + 의존성 그래프

```
[P0 선행 — 1h]
  ⛓ MobileBottomNav + (shell)/layout 통합
       ↓
[P0 핵심 — 5.5h]
  ⛓ /matches (2.5h)
  ⛓ /map (3h)
       ↓ 의존: BottomNav
[P1 보강 — 4.5h]
  ⛓ /places (2.5h)
  ⛓ /ai (2h)
       ↓ 의존: BottomNav
[P2 마무리 — 4h]
  ⛓ /badges (2.5h)
  ⛓ / Landing (1.5h, 선택)
       ↓ 의존: BottomNav
```

---

## 4. 작업 순서 권장

### 🟢 **단계 B0** — 공통 인프라 (1h)
1. `components/nav/mobile-bottom-nav.tsx` 신규
2. `(shell)/layout.tsx` 통합 (md:hidden / hidden md:flex)
3. 모든 모바일 페이지 `pb-24` 추가
4. 검증: 모든 라우트에서 모바일 BottomNav 표시

### 🟢 **단계 B1** — `/matches` 모바일 (2.5h)
1. `upcoming-fixture-hero.tsx` (VS card)
2. `away-matrix-card.tsx`
3. `/matches/page.tsx` 모바일 분기 (`<div className="md:hidden">`)
4. 시각 검증 + 한국어 카피 확정

### 🟢 **단계 B2** — `/map` 모바일 (3h)
1. `floating-top-bar.tsx`
2. `journey-summary-card.tsx`
3. 모바일 분기: 풀스크린 지도 + floating cards
4. 시각 검증

### 🟡 **단계 B3** — `/places` 모바일 (2.5h)
1. `places-search-bar.tsx`
2. `places-filter-chips.tsx`
3. `poi-card-mobile.tsx`
4. `places-map-fab.tsx`
5. 모바일 분기

### 🟡 **단계 B4** — `/ai` 모바일 (2h)
1. `chat-bubble.tsx` 수정 (glass effect)
2. `itinerary-card.tsx` 신규
3. `action-chips.tsx` 신규
4. `glass-input.tsx` 신규
5. `chat-ui.tsx` 통합

### 🟢 **단계 B5** — `/badges` 모바일 (2.5h)
1. `stadium-tour-bento.tsx`
2. `achievement-scroll.tsx`
3. `away-timeline.tsx`
4. 데스크톱 / 모바일 분기

### 🟢 **단계 B6 (선택)** — `/` Landing 모바일 (1.5h)
- 옵션 A 결과로 충분하면 skip
- mockup 정밀 반영 원하면 진행

---

## 5. 한국어 카피 매핑

mockup 영문 → 한국어 변환 표:

| mockup | 한국어 | 비고 |
|---|---|---|
| Matches | 원정 경기 | TopNav 와 통일 |
| Map | 동선 지도 | |
| Stays / Places | 가볼 만한 곳 | 음식점 + 숙박 + 관광 통합 |
| AI / Concierge | AI 플래너 | |
| Badges / Records | 내 뱃지 | |
| Upcoming Fixture | 다가오는 경기 | |
| Away Matrix | 원정 일정 | |
| Live Odds | 실시간 승률 | |
| View Detailed Analysis | 자세히 보기 | |
| Game Day Route | 경기일 동선 | |
| Total Transit | 총 이동 시간 | |
| Optimal | 최적 경로 | |
| Start Navigation | 길 안내 시작 | |
| Find Stays | 주변 검색 | |
| Near Stadium | 경기장 근처 | |
| Recommended | 추천 | |
| Map View | 지도 보기 | |
| Concierge | 컨시어지 | 또는 "AI 플래너" |
| Itinerary | 코스 | |
| Confirmed | 확정 | |
| Tickets | 예매 | |
| Book Itinerary | 코스 저장 | |
| Modify Hotel | 옵션 변경 | |
| Records | 기록 | |
| Stadium Tour | 구장 정복 | |
| 3 of 9 Visited | 9개 중 3개 방문 | |
| Achievement Badges | 도전 과제 | |
| Sweep Watcher | 스윕 워처 | |
| First Pitch | 첫 원정 | |
| Away Warrior | 원정 전사 | |
| Locked | 잠김 | |
| Away Timeline | 원정 기록 | |

---

## 6. 트레이드오프 분석

| 옵션 | 작업 시간 | 디자인 정밀도 | 유지보수 | 데이터 영향 |
|---|---|---|---|---|
| **현 상태 (옵션 A)** | 0 | 70% | 단일 컴포넌트 (반응형) | 없음 |
| **옵션 B 부분 (P0만)** | 6.5h | 85% | 컴포넌트 2배 (mobile/desktop) | 작음 (날씨 추가) |
| **옵션 B 전체 (P0~P2)** | 14.5h | 95% | 컴포넌트 2~3배 | 중 (achievement, timeline 데이터) |

### 주요 트레이드오프
1. **컴포넌트 분리 vs 단일 반응형**
   - 분리: 디자인 정밀, 유지보수 비용 ↑
   - 반응형: 코드 단순, 디자인 타협
2. **영문 mockup vs 한국어 카피**
   - 영문 그대로: 디자인 일치, 사용자 거리감 ↑
   - 한국어 번역: 사용자 친화, 줄 길이 변동
3. **신규 데이터 (achievement, timeline) 도입**
   - 도입: 풍부한 UX
   - 미도입: 단순함 + 빠른 출시

---

## 7. 검증 매트릭스

각 페이지 적용 후 점검:

| 항목 | iPhone SE | iPhone 17 Pro | Galaxy S22 | iPad mini |
|---|---|---|---|---|
| 320×568 | 393×852 | 360×780 | 768×1024 |

- 모든 텍스트 wrap 자연스러움 (글자별 깨짐 0)
- BottomNav 5탭 모두 표시 + 활성 표시
- Floating element 가 BottomNav 와 겹치지 않음 (bottom-[88px+])
- Safe area inset (iPhone notch/Dynamic Island)
- 가로 스크롤 chips 정상 동작

---

## 8. 단계별 결정 요청

진행 옵션:

### 🟢 **A — 단계 B0+B1+B2 만 진행 (P0 핵심, 6.5h)**
가장 ROI 높음. 사용자가 자주 쓰는 핵심 페이지 (matches, map) 모바일 화 + BottomNav.
**추천 이유**: P0 만으로도 모바일 UX 80% 향상. 나머지는 점진적 적용.

### 🟡 **B — 단계 B0~B5 진행 (P0+P1+P2, 14.5h)**
모든 페이지 모바일 mockup 정밀 반영. Landing 만 옵션 A 유지.
**추천 이유**: 풀 모바일 경험 완성. 시간 충분 시 권장.

### 🔴 **C — 단계 B0+B1만 진행 (BottomNav + Matches, 3.5h)**
가장 빠른 검증. BottomNav 패턴 한 페이지로 검증 후 나머지 점진 진행.
**추천 이유**: 디자인/구현 패턴 빠르게 안착시키고 다른 페이지에 적용.

### ⚪ **D — 단계별 합의 후 시작**
각 단계 직전에 mockup vs 한국어 카피 vs 데이터 매핑 함께 검토.

---

## 9. 다음 행동

진행 옵션 (A/B/C/D) 선택 → 즉시 단계 B0 (공통 인프라) 부터 시작.

**권장**: **옵션 C** (BottomNav + Matches 만 먼저) → 결과 확인 후 **옵션 A** (P0 나머지) 진행.

---

*작성: 2026-04-19 · 짝 문서: `docs/NEXT_SESSION_PLAN.md`, `docs/AUTH_ADMIN_UI_PLAN.md`*

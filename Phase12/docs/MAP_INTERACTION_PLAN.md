# 🗺️ /map 페이지 사용자 상호작용 확장 — 상세 구현 계획

> 작성: 2026-04-19 · 트리거: 모바일 /map 페이지에서 (1) 동선 카드 토글 (2) 길 안내 실행 (3) 출발지/도착지/날짜/경유지 종합 설정 요청
> 부모 문서: `docs/MOBILE_USER_CONTROLS_PLAN.md` (옵션 3 vaul 적용 완료 후)
> 영향 범위: /map 페이지의 floating card + tune sheet + 외부 navigation app deeplink

---

## 0. 한눈에 — 3 요청 실현 가능성 + 시간

| # | 요청 | 가능? | 난이도 | 시간 | 비고 |
|---|---|---|---|---|---|
| 1 | 경기일 동선 카드 숨기기/다시 보기 | ✅ | 낮 | 1h | vaul snap point 또는 자체 collapse |
| 2 | 길 안내 시작 (출발/도착/날짜 변경 + 진짜 안내) | ✅ | 중상 | 4~5h | 외부 deeplink (카카오/네이버/구글/애플) |
| 3 | tune 버튼에 길찾기 종합 설정 (날짜/출발/도착/경유지) | ✅ | 중 | 2h | 기존 sheet + 길찾기 섹션 추가 |
| **합계** | | | | **7~8h** | |

→ 모두 실현 가능. 외부 deeplink 가 핵심 종속.

---

## 1. 요청 1 — 경기일 동선 카드 숨기기/다시 보기

### 1-1. UX 옵션

#### A. 우상단 chevron 버튼 ✨ 권장
```
┌──────────────────────┐
│ 경기일 동선  [최적] [▼]│  ← chevron-down 클릭 → 접힘
│ 3 stops · 12분        │
│ ...                   │
└──────────────────────┘

접힌 상태:
┌──────────────────────┐
│ 3 stops · 12분 [▲]    │  ← chevron-up 클릭 → 펼침
└──────────────────────┘
```
**Pros**: 명확 · 빠른 토글 · 손가락 reach OK
**Cons**: 토글 위치 학습 필요

#### B. Vaul snap points (drag swipe) ✨ 권장 추가
- snap: `["80px", "auto"]`
- 사용자가 drag handle 아래로 swipe → 80px 로 축소
- 위로 swipe → 원본 복귀
**Pros**: 모바일 네이티브 swipe 패턴
**Cons**: vaul 로 컨버트 필요 (현재는 fixed div)

#### C. 두 패턴 혼합 (A + B) — **최종 권장**
- chevron 버튼: 명시적 토글 (1탭)
- drag swipe: 자연스러운 제스처
- 둘 다 같은 state 공유

### 1-2. 구현 결정

```typescript
// useMobileMapCard 신규 store
type CardState = "expanded" | "collapsed";
```

**옵션 1 (단순)**: useState + chevron 버튼만
**옵션 2 (vaul)**: JourneySummaryCard 를 vaul Drawer 로 변환 + snap points

→ **옵션 2 권장**: vaul 의 `snapPoints={[80, "auto"]}` 사용 → drag + 시각적 chevron 모두 동작.

### 1-3. 작업 (1h)
1. `JourneySummaryCard` 를 vaul 기반 persistent drawer 로 변환 (closed 안 됨, 항상 표시)
2. snap points: `[80, "auto"]`
3. 헤더 우측에 chevron 버튼 추가 → snap 토글
4. localStorage `map-card-collapsed` 로 상태 persist

---

## 2. 요청 2 — 길 안내 시작 버튼 (출발/도착/날짜 + 진짜 안내)

### 2-1. 분해

| 하위 기능 | 현재 상태 | 신규 작업 |
|---|---|---|
| 출발 변경 | ✅ origin picker (M3 완료) | 그대로 활용 |
| 도착지 변경 | ❌ 자동 (경기장) | **신규** — destination override |
| 날짜 선택 | ⚠ 사이드바 기간 → 자동 | **신규** — 경기 picker 안에 날짜 그룹화 또는 별도 |
| 진짜 길 안내 | ❌ 동작 없음 | **신규** — 외부 deeplink |

### 2-2. 도착지 변경 — 3 옵션

**A. 다른 경기 선택 = 다른 stadium** (자동)
- 이미 game picker (M3) 가 게임 선택 시 stadium 자동 전환
- 사용자가 "도착지 변경 = 경기 변경" 으로 인식

**B. 임의 POI 도착지** (예: 호텔 → 식당 → 경기장)
- 주변 POI 목록에서 선택
- 사용자 자유도 ↑ 그러나 복잡도 ↑

**C. 직접 좌표 입력 또는 검색**
- 카카오 주소 검색 API 연동 필요

→ **권장**: **A** (간단) + **B** (선택, 후속) — 첫 단계는 game picker 가 도착지 변경 역할 겸함

### 2-3. 날짜 선택 — 3 옵션

**A. 경기 picker 안에 날짜 그룹화**
- "오늘" / "내일" / "이번 주말" / "다음 주" / "한달 뒤"
- 그룹별로 list 분할

**B. 별도 inline date picker chip**
- floating top bar 에 날짜 chip 추가 (예: "4/19 ▾")
- 클릭 시 date sheet

**C. tune sheet 의 기존 기간 선택 활용**
- 이미 tune sheet 에 `?start=&end=` 있음
- 사용자가 기간 변경 → 게임 list 자동 업데이트

→ **권장**: **A + C** — 경기 picker 가 날짜 그룹 + 기간 변경은 tune sheet (기존)

### 2-4. 진짜 길 안내 — 외부 deeplink 매트릭스

| 앱 | URL scheme | iOS | Android | Desktop |
|---|---|---|---|---|
| **카카오맵** | `kakaomap://route?sp=lat,lng&ep=lat,lng&by=CAR` | ✅ | ✅ | ❌ (앱 필요) |
| **네이버지도** | `nmap://route/public?slat=&slng=&dlat=&dlng=&appname=` | ✅ | ✅ | ❌ |
| **Google Maps** | `https://www.google.com/maps/dir/?api=1&origin=&destination=&travelmode=transit` | ✅ | ✅ | ✅ (웹) |
| **Apple Maps** | `https://maps.apple.com/?saddr=&daddr=&dirflg=r` | ✅ | ❌ | ✅ (Safari) |
| **Tmap** | `tmap://route?startx=&starty=&endx=&endy=` | ✅ | ✅ | ❌ |

#### 동작 방식
```typescript
function launchNavigation(app: NavApp, origin: [lat, lng], dest: [lat, lng]) {
  const urls: Record<NavApp, string> = {
    kakao: `kakaomap://route?sp=${origin[0]},${origin[1]}&ep=${dest[0]},${dest[1]}&by=PUBLICTRANSIT`,
    naver: `nmap://route/public?slat=${origin[0]}&slng=${origin[1]}&dlat=${dest[0]}&dlng=${dest[1]}&appname=stadium-editorial`,
    google: `https://www.google.com/maps/dir/?api=1&origin=${origin[0]},${origin[1]}&destination=${dest[0]},${dest[1]}&travelmode=transit`,
    apple: `https://maps.apple.com/?saddr=${origin[0]},${origin[1]}&daddr=${dest[0]},${dest[1]}&dirflg=r`,
  };
  window.location.href = urls[app];
}
```

#### 앱 미설치 fallback
- iOS Safari → kakaomap:// 미설치 시 빈 화면. 1초 후 fallback 으로 App Store 또는 Google Maps 웹 이동.
- 가장 안전: **Google Maps 웹** 을 default fallback (universal)

### 2-5. UX 설계 — Trip Confirmation Sheet

길 안내 시작 클릭 → 새 BottomSheet (확인 + 변경 + 앱 선택):

```
┌──────────────────────────────┐
│ ━━━                            │
│ 길 안내 시작            [X]   │
├──────────────────────────────┤
│ 📍 출발                       │
│   서울역                  [변경]│  ← 출발지 picker 트리거
│                                │
│ ⚾ 도착                       │
│   고척스카이돔            [변경]│  ← 경기 picker 트리거 = 도착지
│                                │
│ 📅 날짜                       │
│   2026-04-22 (수)         [변경]│
│                                │
│ 🚌 이동수단                    │
│   대중교통 ▾                  │  ← inline select
│                                │
├──────────────────────────────┤
│ 어떤 앱으로 길 안내?            │
│ [🟡 카카오] [🟢 네이버]         │
│ [🔵 구글]   [🍎 애플]          │
└──────────────────────────────┘
```

### 2-6. 작업 (4~5h)

| 작업 | 시간 |
|---|---|
| `components/map/trip-confirmation-sheet.tsx` 신규 | 1.5h |
| `lib/nav-deeplink.ts` 신규 (4 앱 deeplink + OS 감지) | 1h |
| `components/map/nav-app-picker.tsx` 신규 (4 앱 chip) | 0.5h |
| `journey-summary-card.tsx` 의 길안내 button → trip confirmation 트리거 | 0.5h |
| 도착지 override 처리 (선택) | 0.5h |
| 테스트 (실기기 deeplink 발사) | 0.5h |

---

## 3. 요청 3 — tune 버튼에 길찾기 종합 설정 추가

### 3-1. 옵션 비교

#### A. tune sheet 안에 길찾기 섹션 추가 (페이지별 컨텍스트)
- 현재 tune sheet 는 글로벌 (모든 페이지에서 동일 내용)
- /map 페이지일 때 추가 섹션 자동 노출:
  ```
  ─────
  🗺️ 길찾기 설정 (지도 페이지)
  📍 출발지: 서울역  [변경]
  ⚾ 도착지: 고척스카이돔  [변경]
  📅 날짜: 2026-04-22  [변경]
  🚏 경유지: 0개  [추가]
  ─────
  ```
- `usePathname` 으로 /map 감지 → 섹션 조건부 렌더

#### B. tune 버튼 우측에 두 번째 버튼 추가 (route 아이콘)
- /map 만 우상단에 [⚙ tune] [🗺️ route] 두 개
- route 클릭 → 길찾기 전용 sheet

#### C. 새 sheet 종류 추가 (`mobile-sheet` store 에 `route` kind)
- tune 메뉴 안에 "🗺️ 길찾기 설정 →" 항목 → route sheet 열기

→ **권장**: **A** — 가장 자연스러움 + 추가 button 없음 + 사용자가 한 sheet 에서 모든 설정.

### 3-2. 경유지 (Waypoint) 처리

#### 데이터 모델
```typescript
// lib/store/trip.ts (신규)
interface TripWaypoint {
  id: string;
  label: string;
  lat: number;
  lng: number;
  type: "food" | "stay" | "tour" | "custom";
}

interface TripState {
  waypoints: TripWaypoint[];
  addWaypoint: (wp: TripWaypoint) => void;
  removeWaypoint: (id: string) => void;
  reorderWaypoints: (oldIdx: number, newIdx: number) => void;
}
```

#### URL 직렬화
- `?wp=한식당:37.5,127.0|호텔:37.6,126.9` (간단)
- 또는 zustand persist (localStorage)

#### Route API 처리
- OSRM: `via` parameter 지원 — `https://router.project-osrm.org/route/v1/driving/{lon1,lat1};{wp1};{lon2,lat2}`
- Kakao Mobility: 다중 waypoint 지원 (POST body)
- Haversine: 단순 직선 (waypoint 무시 또는 단순 합산)

#### UI
```
🚏 경유지 (2개)
  1. 잠실 명동교자  ⋮⋮ [×]
  2. 잠실 스타벅스  ⋮⋮ [×]
  [+ 경유지 추가]      ← POI picker sub-sheet
```

### 3-3. 작업 (2h, waypoints 제외 시 1h)

| 작업 | 시간 |
|---|---|
| `MobileFilterSheet` 안에 길찾기 섹션 추가 (usePathname 분기) | 0.5h |
| 출발/도착/날짜 chip + 변경 button → 기존 picker 트리거 | 0.5h |
| 경유지 list + add/remove/reorder | 1h (선택) |

---

## 4. 종합 권장 진행

### 🟢 옵션 A — **P0 핵심 (요청 1 + 2 핵심)** — 5h
1. 단계 1 — Card 토글 (vaul snap points + chevron) — 1h
2. 단계 2 — Trip Confirmation Sheet — 1.5h
3. 단계 3 — Nav app picker (4 앱 deeplink) — 1.5h
4. 단계 4 — Journey card 의 길안내 button → confirmation 트리거 — 0.5h
5. 검증 — 0.5h

### 🟡 옵션 B — **P0 + P1 (요청 1 + 2 + 3 chip 만)** — 6h
- 옵션 A + tune sheet 안에 길찾기 chip 섹션 (waypoints 제외) — 1h

### 🔴 옵션 C — **풀 (요청 1 + 2 + 3 + waypoints)** — 8h
- 옵션 B + waypoints (URL 직렬화 + POI picker + drag reorder + OSRM via) — 2h

---

## 5. 데이터 모델 영향

### 5-1. URL 파라미터 추가
| 신규 | 의미 | 예 |
|---|---|---|
| `?dest_lat=` `?dest_lng=` | 도착지 override (경기장 외) | 호텔로 가기 |
| `?wp=` (반복) | 경유지 list | `wp=명동교자:37.5,127.0` |
| `?nav=` | 선호 nav 앱 | `nav=kakao` (last selected persist) |

### 5-2. localStorage
- `map-card-collapsed`: 동선 카드 접힘 여부
- `nav-app-preference`: 선호 길안내 앱

### 5-3. Route API 호출 변경
- 현재: `requestRoute(origin, dest)` (단방향)
- 신규: `requestRoute(origin, dest, waypoints?)` — 옵션 C 만

---

## 6. 트레이드오프 분석

| 옵션 | 작업 | 사용자 가치 | 복잡도 |
|---|---|---|---|
| A (P0) | 5h | 80% — 동선 토글 + 실제 길안내 | 낮 |
| B (P1) | 6h | 90% — A + tune 통합 설정 | 중 |
| C (풀) | 8h | 95% — B + waypoint | 중상 |

### 주요 리스크
| 리스크 | 완화 |
|---|---|
| 카카오/네이버 앱 미설치 시 빈 화면 | 1초 후 Google Maps 웹 fallback |
| Vaul snap to 80px 시 drag handle 가시성 | 80px 영역에 chip + chevron 명시 |
| 경유지 reorder UX 복잡 | 옵션 C 만, drag-drop library (dnd-kit) 신규 |
| OSRM via parameter 다중 경유지 성능 | 최대 5개 제한 + 경고 |
| iOS Safari deeplink 동작 차이 | OS 감지 후 UA 별 fallback |

---

## 7. 외부 deeplink 핵심 코드

```typescript
// lib/nav-deeplink.ts
export type NavApp = "kakao" | "naver" | "google" | "apple" | "tmap";

export interface NavDeepLinkParams {
  origin: [number, number];      // [lat, lng]
  destination: [number, number];
  waypoints?: [number, number][];
  mode?: "transit" | "car" | "walk";
}

const FALLBACK_TIMEOUT_MS = 1500;

export function launchNavigation(app: NavApp, p: NavDeepLinkParams) {
  const url = buildUrl(app, p);
  const fallback = buildUrl("google", p); // 항상 fallback 으로 Google

  if (app === "google" || app === "apple") {
    // 웹 URL — 새 탭
    window.open(url, "_blank", "noopener,noreferrer");
    return;
  }

  // 앱 deeplink — 미설치 시 fallback
  const start = Date.now();
  window.location.href = url;
  setTimeout(() => {
    if (Date.now() - start < FALLBACK_TIMEOUT_MS + 100) {
      // 페이지가 여전히 활성 → 앱 전환 안 됨 → fallback
      window.open(fallback, "_blank");
    }
  }, FALLBACK_TIMEOUT_MS);
}

function buildUrl(app: NavApp, p: NavDeepLinkParams): string {
  const [olat, olng] = p.origin;
  const [dlat, dlng] = p.destination;
  switch (app) {
    case "kakao":
      return `kakaomap://route?sp=${olat},${olng}&ep=${dlat},${dlng}&by=${
        p.mode === "car" ? "CAR" : "PUBLICTRANSIT"
      }`;
    case "naver":
      return `nmap://route/public?slat=${olat}&slng=${olng}&dlat=${dlat}&dlng=${dlng}&appname=stadium-editorial`;
    case "google":
      const wp = p.waypoints?.map(([la, ln]) => `${la},${ln}`).join("|") ?? "";
      return `https://www.google.com/maps/dir/?api=1&origin=${olat},${olng}&destination=${dlat},${dlng}&travelmode=transit${wp ? `&waypoints=${wp}` : ""}`;
    case "apple":
      return `https://maps.apple.com/?saddr=${olat},${olng}&daddr=${dlat},${dlng}&dirflg=r`;
    case "tmap":
      return `tmap://route?startx=${olng}&starty=${olat}&endx=${dlng}&endy=${dlat}`;
  }
}
```

---

## 8. 검증 매트릭스

| 항목 | iPhone (Safari) | Android (Chrome) | iPad |
|---|---|---|---|
| Card snap to 80px (drag) | ✓ | ✓ | (데스크톱 모드 분기) |
| Card chevron 토글 | ✓ | ✓ | - |
| Trip Confirmation 열림 | ✓ | ✓ | - |
| 출발지 변경 (sub-sheet) | ✓ | ✓ | - |
| 도착지 변경 (game picker) | ✓ | ✓ | - |
| 카카오맵 deeplink (앱 설치 시) | ✓ | ✓ | - |
| 네이버지도 deeplink | ✓ | ✓ | - |
| Google Maps 웹 (fallback) | ✓ | ✓ | ✓ |
| Apple Maps (iOS) | ✓ | ❌ (Android 미지원) | ✓ |

---

## 9. 단계별 결정 요청

진행 옵션:

### 🟢 **A — P0 (5h)** ✨ 권장
- 동선 카드 토글 + Trip Confirmation + 4 앱 deeplink
- 가장 빠른 가치 + 핵심 사용 흐름 완성

### 🟡 **B — P0+P1 (6h)**
- A + tune sheet 안에 길찾기 종합 chip 섹션 (요청 3)
- 사용자가 한 곳에서 모든 설정

### 🔴 **C — 풀 (8h)**
- B + 경유지 (waypoints + drag reorder + OSRM via)
- 가장 풍부

### ⚪ **D — 단계별 합의**
- 각 단계 직전 추가 검토

---

*작성: 2026-04-19 · 짝 문서: `docs/MOBILE_USER_CONTROLS_PLAN.md`*

진행 옵션 선택 후 즉시 단계 1 (카드 토글) 부터 시작.

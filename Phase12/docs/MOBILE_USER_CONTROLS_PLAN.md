# 📱 모바일 사용자 설정 기능 — 상세 구현 계획

> 작성: 2026-04-19 · 트리거: 모바일에서 사이드바 필터 + 출발지/경기 선택 불가능
> 부모 문서: `docs/MOBILE_UIUX_OPTION_B_PLAN.md` (옵션 B 6 단계 완료 후)
> 영향 범위: /matches · /map · /places · /badges 모바일 사용자 설정 진입점

---

## 0. 문제 정의

### 0-1. 현재 구조 (옵션 B 완료 시점)
- **데스크톱**: `FilterSidebar` (260px 좌측) — 응원팀/기간/예산/인원/이동수단/시연모드 + 코스 생성 + 공유
- **모바일**: 사이드바 `md:block` 으로 숨김 → **모든 사용자 설정 접근 불가**
- `/map` 의 `MapControls` (경기 select + 출발지 그룹 accordion + 내 위치) — 데스크톱만
- `/places` 의 `StadiumPicker` (10 구장 chip) — 데스크톱만

### 0-2. 사용자 영향
| 페이지 | 모바일 사용자가 못하는 것 |
|---|---|
| `/matches` | 응원팀 변경 / 기간 변경 |
| `/map` | 응원팀 / 기간 / **출발지** / **경기** 변경 |
| `/places` | **구장 선택** / 응원팀 변경 |
| `/ai` | 응원팀 / 기간 / 예산 / 인원 / 이동수단 (AI 컨텍스트) |
| `/badges` | 공유 링크 외 거의 영향 없음 |

→ 본질적으로 **모바일 사용자는 LG 트윈스 default 만 영원히** 보게 됨.

### 0-3. mockup 의 단서
- 모든 모바일 mockup 우상단에 **`tune` 아이콘 버튼** 또는 **햄버거** 가 있음
- 이미 `matches-mobile-view.tsx` 에 tune 버튼 placeholder 가 있고 (현재 onClick 없음)
- `/map` floating-top-bar 에 `more_vert` 버튼 있음 (현재 onClick 없음)
- 이 버튼들에 **실제 동작** 만 연결하면 됨

---

## 1. UX 패턴 비교 (5가지)

### 🟢 A. **Bottom Sheet** (권장 ✨)
화면 하단에서 위로 슬라이드. iOS Maps · Uber · Toss 패턴.

```
┌────────────────────┐
│   페이지 콘텐츠     │
│                    │
│                    │
├────────────────────┤  ← drag handle (___)
│  ━━━               │
│  원정 설정          │
│  [필터 내용]        │
│  ...               │
└────────────────────┘
```

**Pros**: 모바일 네이티브 패턴 · 페이지 컨텍스트 유지 · 부드러운 UX · backdrop tap dismiss
**Cons**: 구현 복잡 (drag/snap/animation) · scroll lock 필요

### 🟡 B. Fullscreen Modal
우상단 tune → 전체 화면 모달.
**Pros**: 간단 · 모든 control 한 화면
**Cons**: 답답한 느낌 · 모바일 네이티브 X

### 🟡 C. Side Drawer (좌/우 슬라이드)
햄버거 → 좌측 또는 우측에서 슬라이드.
**Pros**: 데스크톱 사이드바와 일관성
**Cons**: BottomNav 와 동선 충돌 · iOS 에서 어색

### 🔴 D. Top Drawer
햄버거 → 상단에서 펼침. 일부 mockup 에 있음.
**Pros**: 랜딩 mockup 의 햄버거 패턴 일치
**Cons**: 손가락 reach 어려움 · BottomNav 와 거리 멀음

### 🟡 E. 페이지별 Inline Controls
사이드바 폐기, 각 페이지에 필요한 chip 만 노출.
**Pros**: 빠른 접근 · UX 명확
**Cons**: 모든 페이지에 chip 분산 · 일관성 ↓ · 시연 모드 같은 글로벌 설정 둘 곳 없음

### 🟢 F. **A + E 조합** (최고 권장 ⭐)
- 우상단 tune → **Bottom Sheet** (사이드바 전체 = 글로벌 설정)
- 페이지별 핵심 control 은 **inline chip** (빠른 변경)
  - /map: 출발지 chip + 경기 chip
  - /places: stadium picker chip (수평 스크롤)
  - /matches: 응원팀 chip (이미 헤더에 표시)

---

## 2. 권장 방안 — F (A + E 조합)

### 2-1. BottomSheet (글로벌 설정)
모든 모바일 페이지 우상단의 **tune 버튼** → BottomSheet 열림.
사이드바 내용 (응원팀/기간/예산/인원/이동수단/코스생성/시연모드/공유) 그대로 노출.

### 2-2. 페이지별 inline chip (빠른 컨텍스트 변경)
| 페이지 | inline chip 위치 | 변경 가능 항목 |
|---|---|---|
| `/matches` | 모바일 헤더 (이미 응원팀 표시) | tune 버튼만 (전체 sheet) |
| `/map` | floating top bar 또는 journey card | **출발지** + **경기** chip |
| `/places` | 헤더 아래 stadium chip 가로 스크롤 | **구장** + tune 버튼 |
| `/ai` | header gradient bar (이미 팀/기간 표시) | tune 버튼만 |
| `/badges` | 헤더 옆 | tune 버튼만 |

---

## 3. 컴포넌트 설계

### 3-1. 신규 파일
```
frontend/components/
├── ui/
│   └── bottom-sheet.tsx               🆕 재사용 BottomSheet
├── sidebar/
│   └── mobile-filter-sheet.tsx        🆕 사이드바 내용 BottomSheet wrap
├── map/
│   ├── mobile-game-picker.tsx         🆕 경기 선택 chip + sub-sheet
│   └── mobile-origin-picker.tsx       🆕 출발지 chip + sub-sheet
└── places/
    └── mobile-stadium-picker.tsx      🆕 구장 chip horizontal scroll
```

### 3-2. 수정 파일
```
frontend/components/
├── matches/
│   └── matches-mobile-view.tsx        (tune 버튼 onClick → setSheetOpen)
├── map/
│   ├── floating-top-bar.tsx           (more_vert → openSheet, title clickable → game picker)
│   └── journey-summary-card.tsx       (origin label clickable → origin picker)
├── places/
│   └── places-mobile-view.tsx         (헤더에 stadium picker + tune 추가)
├── ai/
│   └── chat-ui.tsx                    (모바일 헤더 tune 버튼 추가)
└── badges/
    └── badges-mobile-view.tsx         (헤더 우측 tune 버튼 추가)
```

---

## 4. BottomSheet 컴포넌트 상세 설계

### 4-1. API
```tsx
<BottomSheet
  open={open}
  onClose={() => setOpen(false)}
  title="원정 설정"
  snapPoints={["50%", "90%"]}     // 선택: 다단계 snap
  initialSnap={0}
>
  {children}
</BottomSheet>
```

### 4-2. 핵심 동작
- **열기**: tune 버튼 onClick → `setOpen(true)` → 슬라이드 업 + backdrop fade-in
- **닫기**: backdrop tap / X 버튼 / drag-down threshold / Escape 키
- **drag handle** (━━━): visual cue 만, 실제 drag 는 본격 도입 시
- **body scroll lock**: 열림 동안 `document.body.style.overflow = "hidden"`
- **focus trap**: 첫 focusable element 자동 focus
- **safe area inset**: bottom padding 자동
- **animation**: CSS `transform: translateY(100%)` ↔ `translateY(0)` + backdrop opacity

### 4-3. CSS / 토큰
```css
/* globals.css 추가 */
@keyframes se-sheet-slide-up {
  from { transform: translateY(100%); }
  to { transform: translateY(0); }
}
@keyframes se-sheet-slide-down {
  from { transform: translateY(0); }
  to { transform: translateY(100%); }
}
@keyframes se-fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}
```

### 4-4. 접근성
- `role="dialog"` + `aria-modal="true"` + `aria-labelledby={titleId}`
- ESC 키 → close
- 첫 mount 시 첫 focusable 에 focus
- 닫힌 후 trigger 버튼에 focus 복구

### 4-5. 라이브러리 선택
| 옵션 | Pros | Cons |
|---|---|---|
| **자체 구현** | 의존성 0 · 디자인 완전 제어 | 코드량 ↑ |
| `vaul` (Sonner 만든 사람) | 1KB · drag 지원 · 접근성 완벽 | 신규 의존성 |
| `@radix-ui/react-dialog` | 검증됨 · 접근성 완벽 | drag 미지원 (자체 슬라이드) |

**선택**: **자체 구현** (단순한 modal + slide animation 만 필요, drag 는 v2)

---

## 5. MobileFilterSheet 내용 설계

기존 `FilterSidebar` 의 핵심 control 을 재사용. 단, 모바일 친화적으로 spacing 조정.

```
┌─────────────────────────────┐
│ ━━━                          │  drag handle
│                              │
│ 🎽 원정 설정       [X]       │  title + close
├─────────────────────────────┤
│ 응원팀                       │
│ [LG ▾]                       │
│                              │
│ 원정 기간                    │
│ [2026-04-19] ~ [2026-05-19]  │
│                              │
│ 예산 (만원)             30   │
│ [━━━━━●━━━━━]                │
│                              │
│ 인원 구성                    │
│ [혼자] [커플] [가족] [친구]   │
│                              │
│ 이동수단                     │
│ [KTX] [자차] [버스]          │
│                              │
│ ┌──────────────────────────┐ │
│ │ 🎯 코스 생성              │ │
│ └──────────────────────────┘ │
│ ☐ 🎬 시연 모드                │
│ ─────────────                │
│ 🔗 원정 계획 공유             │
└─────────────────────────────┘
```

→ 기존 `FilterSidebar` 컴포넌트의 **JSX 만 분리**해서 BottomSheet 안에 넣음. 동작 (Zustand → URL 동기화) 은 그대로.

---

## 6. /map 페이지 inline controls

### 6-1. Floating Top Bar 확장
```
┌──────────────────────────────────┐
│ [←]  [📍 LG 원정 ▾]    [⚙ tune] │
└──────────────────────────────────┘
       ↑ 가운데 라벨 클릭 시
       ┌────────────────┐
       │ 경기 선택        │
       │ 4/19 vs KT      │  ← 현재
       │ 4/22 vs SSG     │
       │ 4/25 vs KIA     │
       │ ...             │
       └────────────────┘
```

### 6-2. Journey Summary Card 확장
```
[경기일 동선]                  [최적 ▾]
3 stops · 33분

[●] 서울역                    출발 [변경]  ← 클릭 시 origin picker sheet
[●] 수원 이디야커피            경유
[●] 수원KT위즈파크             도착 18:30

[길 안내 시작]
```

### 6-3. 신규 컴포넌트
- `mobile-game-picker.tsx` — 경기 list bottom sheet (스크롤)
- `mobile-origin-picker.tsx` — 출발지 그룹 accordion bottom sheet (현재 데스크톱 MapControls 재사용)

---

## 7. /places 페이지 inline controls

### 7-1. 헤더 아래 stadium chip horizontal scroll
```
[가볼 만한 곳] [⚙]
잠실야구장 주변 · 27건

[잠실 ●] [수원] [잠실(보조)] [인천] [대전] [대구] ...
       ↑ 활성 (녹색 fill)
```

### 7-2. 신규 컴포넌트
- `mobile-stadium-picker.tsx` — 10 구장 chip 가로 스크롤 (활성 표시 + URL `?s=` 갱신)

---

## 8. 단계별 구현 순서 + 작업 시간

### 🟢 단계 M0 — BottomSheet 인프라 (1.5h, P0)
1. `components/ui/bottom-sheet.tsx` 신규 (slide + backdrop + scroll lock + ESC)
2. `globals.css` 에 slide-up/down keyframes 추가
3. 단독 시각 검증 (storybook 없으니 임시 페이지 또는 dev 직접)

### 🟢 단계 M1 — MobileFilterSheet (0.5h, P0)
1. `components/sidebar/mobile-filter-sheet.tsx` 신규
2. `FilterSidebar` 의 form 부분 재사용 (export 분리 또는 복사)
3. BottomSheet 안에 포함

### 🟢 단계 M2 — 모든 페이지 tune 버튼 통합 (1h, P0)
1. `matches-mobile-view.tsx` — tune onClick → setSheetOpen(true)
2. `map/floating-top-bar.tsx` — more_vert → openSheet
3. `places-mobile-view.tsx` — 헤더 tune 버튼 추가 → openSheet
4. `ai/chat-ui.tsx` — 모바일 헤더 우측 tune 추가 → openSheet
5. `badges-mobile-view.tsx` — 헤더 우측 tune 추가 → openSheet

> **공통화 옵션**: BottomNav 처럼 `<MobileSettingsTrigger>` 컴포넌트로 wrap → 한 곳에서 sheet 상태 관리

### 🟡 단계 M3 — /map inline controls (1.5h, P1)
1. `mobile-game-picker.tsx` — 경기 list sub-sheet
2. `mobile-origin-picker.tsx` — 출발지 sub-sheet
3. `floating-top-bar.tsx` 의 가운데 라벨 → 경기 picker 트리거
4. `journey-summary-card.tsx` 의 출발지 라벨 → origin picker 트리거

### 🟡 단계 M4 — /places inline stadium chip (0.5h, P1)
1. `mobile-stadium-picker.tsx` 신규
2. `places-mobile-view.tsx` 헤더 아래 통합

### 🟢 단계 M5 — 시각 검증 + Edge case (0.5h, P0)
1. body scroll lock 테스트
2. iOS keyboard 노출 시 sheet 위치
3. backdrop tap dismiss
4. ESC 키 dismiss

**총 시간**:
- P0 (M0+M1+M2+M5) = **3.5h** ✨ 최소 권장
- P0 + P1 (M0~M5 전체) = **5.5h** — full

---

## 9. 데이터 흐름

```
사용자 tune 클릭
  → setSheetOpen(true)
  → MobileFilterSheet mount
  → 사이드바 form (기존 useFilters Zustand store 직접 mutation)
  → 변경 시 URL ?team=, ?start=, ?end=, ?budget=, ... 동기화
  → 페이지 server component 가 URL 보고 데이터 새로 fetch
  → 화면 자동 갱신
  → 사용자 X 또는 backdrop 탭
  → setSheetOpen(false)
  → 페이지 컨텍스트 그대로 유지
```

핵심: **기존 `useFilters` Zustand store 그대로 활용** — 새 상태 관리 도입 X.

---

## 10. 트레이드오프 분석

| 옵션 | 작업 시간 | UX 정밀도 | 유지보수 | 일관성 |
|---|---|---|---|---|
| **단계 M0~M2 (sheet only)** | 3.5h | 80% | 단일 sheet 컴포넌트 | ✅ 모든 페이지 동일 패턴 |
| **단계 M0~M5 (sheet + inline)** | 5.5h | 95% | 페이지별 chip 추가 | ⚠ 각 페이지 다른 control |
| **mockup 정밀 (drag handle + snap)** | 8h+ | 99% | drag library 도입 (vaul) | ✅ 일관성 |

---

## 11. 리스크 + 완화

| 리스크 | 완화 |
|---|---|
| Body scroll lock 후 iOS Safari "탄력 스크롤" 깨짐 | `position: fixed` + `top: -scrollY` 패턴 |
| Sheet 열린 상태에서 BottomNav 와 z-index 충돌 | sheet z-index 60+, nav z-50 |
| 사용자가 sheet 열고 다른 페이지 navigate → sheet 안 닫힘 | `usePathname` effect 로 자동 close |
| Keyboard 노출 시 input 가림 | `viewport-fit=cover` + `env(safe-area-inset)` + visualViewport API |
| 다중 sheet (예: filter sheet 안에서 origin sub-sheet) | sheet 중첩 지원 또는 stack 방식 |
| 시연 모드 토글이 sheet 안에 묻힘 | 자주 안 쓰니 OK · 또는 별도 위치 |

---

## 12. 완료 조건 (Definition of Done)

| 항목 | 기준 |
|---|---|
| 모든 모바일 페이지 우상단에 tune 버튼 표시 | ✓ |
| tune 클릭 → BottomSheet slide up + backdrop | ✓ |
| Sheet 안에서 응원팀 변경 → URL `?team=` 갱신 + 페이지 새 데이터 | ✓ |
| Sheet 안에서 기간/예산/인원/이동수단 변경 → 즉시 동작 | ✓ |
| 코스 생성 버튼 → toast + /matches 이동 (기존 동작) | ✓ |
| 시연 모드 토글 → AI 페이지 mock 응답 | ✓ |
| 공유 링크 버튼 → 클립보드 복사 (기존 동작) | ✓ |
| /map 출발지 변경 → URL `?origin=` + 경로 재계산 | (M3) |
| /map 경기 변경 → URL `?game=` + 동선 갱신 | (M3) |
| /places 구장 chip 변경 → URL `?s=` + POI 새로 로드 | (M4) |
| Body scroll lock 정상 (sheet 열린 동안 페이지 스크롤 X) | ✓ |
| backdrop tap → close | ✓ |
| ESC 키 → close | ✓ |
| 페이지 navigate → 자동 close | ✓ |

---

## 13. 검증 매트릭스

| 항목 | iPhone SE | iPhone 17 Pro | Galaxy S22 | iPad mini |
|---|---|---|---|---|
| Sheet slide up animation 부드러움 | ✓ | ✓ | ✓ | (데스크톱 분기) |
| Sheet 높이 적절 (입력 다 보임) | ✓ | ✓ | ✓ | - |
| Body scroll lock 정상 | ✓ | ✓ | ✓ | - |
| Keyboard 노출 시 input 안 가림 | ✓ | ✓ | ✓ | - |

---

## 14. 다음 행동 — 옵션 선택

### 🟢 **옵션 1 — 최소 (단계 M0~M2 + M5, 3.5h)** ✨ 권장
사이드바 전체를 BottomSheet 로 모든 페이지에서 접근 가능하게.
**장점**: 가장 빠른 안착 + 모든 사용자 설정 즉시 가능
**단점**: /map 출발지/경기 변경 시 sheet 열고 닫기 한 번 더 필요

### 🟡 **옵션 2 — 중간 (단계 M0~M5 전체, 5.5h)**
옵션 1 + /map inline 출발지/경기 chip + /places stadium chip.
**장점**: 자주 쓰는 변경은 1탭으로 가능
**단점**: 작업 시간 + 페이지별 차이

### 🔴 **옵션 3 — 풀 (drag handle + snap + vaul library, 8h+)**
mockup 정밀 반영.
**장점**: iOS 네이티브 수준 UX
**단점**: 작업량 큼 + 신규 의존성

---

*작성: 2026-04-19 · 짝 문서: `docs/MOBILE_UIUX_OPTION_B_PLAN.md`*

진행 옵션 선택 후 즉시 단계 M0 (BottomSheet 인프라) 부터 시작.

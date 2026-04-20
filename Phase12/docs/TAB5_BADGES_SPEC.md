# 🏆 Tab 5. 뱃지 — 기능 설명서

> **"10 구장 전부 원정 응원 가기"** — KBO 팬의 작은 버킷리스트.
> 그 여정을 체크리스트로 쌓고, 완성한 계획을 친구에게 링크 하나로 공유하는 공간입니다.

**라우트**: `/badges` · **배포 URL**: [my-web-app--mini12-310f5.asia-east1.hosted.app/badges](https://my-web-app--mini12-310f5.asia-east1.hosted.app/badges)

---

## 📖 起 (기) — 왜 필요한가? 문제 제기

### 원정 응원러의 두 가지 욕망

KBO 팬에게 원정은 단순한 관람이 아닙니다:

> **욕망 1 — "기록하고 싶다"**
> "작년에 대전·창원·사직 가봤고, 올해는 광주·대구 도전!" 같은 **방문 기록을 남기고 자랑하고 싶은** 욕구.
>
> **욕망 2 — "공유하고 싶다"**
> "4월 25일 수원 원정, 우리 함께 가자!" 메시지에 **계획(응원팀·기간·예산·인원·이동수단) 전체를 링크 하나로** 친구에게 넘기고 싶은 욕구.

### 기존 방식의 한계

- 엑셀·메모장에 기록 → 디바이스 바꾸면 유실
- 카카오톡으로 계획 설명 → 받은 친구가 다시 앱을 하나하나 설정
- 인스타 방문 인증 → 10 구장 진척도를 한눈에 보기 어려움

### 이 탭의 약속

**"10 구장 투어 체크리스트 · 디바이스 간 자동 동기화 · 계획 한 번에 공유"** 세 가지를 한 페이지에서 제공합니다.

---

## 🚀 承 (승) — 무엇을 하는가? 기능 소개

### 기능 5가지

#### 1. Stadium Tour 체크리스트
- 10개 KBO 구장이 **2×5 또는 5×2 그리드**로 표시
- 방문한 구장은 **팀 컬러 풀컬러** · 미방문은 **회색(grayscale)**
- 카드 탭 → 즉시 토글 · 진행률 업데이트 (예: `3/10 → 4/10`)

#### 2. 10/10 Celebrate
- 10개 구장 전부 체크 시 **축하 UI + 달성 배지** 표시
- 진행률 바가 100% 녹색으로 채워짐
- 원정 응원 풀 투어 완주 기념

#### 3. 디바이스 간 자동 동기화
- 로그인 상태: 아이폰에서 체크 → PC Chrome 에서 같은 계정 로그인 → **자동으로 동일 상태 반영** (약 0.5초 이내)
- 서로 다른 기기에서도 같은 뱃지 현황을 즉시 확인 가능

#### 4. 오프라인 / 비로그인 대응
- 비로그인 · Firebase 미구성 상황에서도 체크리스트는 정상 작동
- 브라우저 로컬 저장소에 기록 → **"🏠 로컬 저장"** 배지로 상태 명시
- 로그인하면 익명 기록이 계정으로 자동 이관

#### 5. 계획 공유 링크 (Share Plan)
- 사이드바 **"📤 공유"** 버튼 → 현재 필터(응원팀·기간·예산·인원·이동수단) 상태를 URL로 변환
- 링크 클릭한 친구는 **동일 세팅으로 앱을 시작** (팀·기간 등 5 필드 자동 복원)
- 짧은 링크 (`/share/abc123`) 와 긴 링크 (URL 파라미터) 둘 다 지원

### 화면 예시

**💻 데스크톱**
```
┌─ 🏆 Stadium Tour ─────────────────────┐
│ 5/10 구장 방문 완료                     │
├─ 진행률 바 [▓▓▓▓▓░░░░░] 50% ─────────┤
├─ 구장 그리드 (5×2) ──────────────────┤
│ [LG ✅] [KT ✅] [SSG ✅] [두산] [KIA ✅] │
│ [NC] [삼성 ✅] [롯데] [한화] [키움]      │
├─ 🏅 누적 기록 · 리그별 달성 현황 ───────┤
└───────────────────────────────────────┘
```

**📱 모바일**
```
┌─ 🏆 내 기록 ─────────────────────┐
│ 5/10 구장 방문                    │
├─ 큰 원형 진행률 (팀 컬러 테두리) ─┤
├─ 구장 그리드 (2열) ──────────────┤
│ [LG ✅]  [KT ✅]                   │
│ [SSG ✅] [두산]                    │
│ [KIA ✅] [NC]                     │
│ [삼성 ✅][롯데]                    │
│ [한화]  [키움]                     │
├─ 최근 방문 타임라인 ─────────────┤
└──────────────────────────────────┘
```

---

## ⚙️ 轉 (전) — 어떻게 만들었는가? 기술과 원리

> 데이터 저장·동기화 기술을 **비유와 예시**로 풀어씁니다.

### 💾 이중화 저장 (Dual Storage) — "로컬 + 클라우드 동시 저장"

**쉽게 말하면**:
> "편의점 포인트처럼, **영수증(localStorage)에도 찍고 · 앱(Firestore)에도 기록**. 둘 중 하나만 있어도 혜택을 받을 수 있도록 설계."

```
 사용자 체크 동작
       │
       ├──► localStorage (즉시 · 로컬만)
       │     └─ 브라우저에 남음 · 오프라인에서도 유지
       │
       └──► Firestore (비동기 · 클라우드)
             └─ 계정에 묶임 · 다른 기기에서도 조회 가능
```

**왜 이중화?**:
- **Firebase only**: 비로그인 사용자 못 씀 → UX 저하
- **localStorage only**: 다른 기기에서 볼 수 없음 · 브라우저 삭제 시 유실
- **이중화**: 두 단점을 서로 커버. Firebase 미구성이면 자동으로 localStorage 만 쓰는 **graceful degradation** (점진적 성능 저하)

### 🏪 Zustand + localStorage persist — "브라우저 내 작은 기억 보관소"

**쉽게 말하면**:
> "웹앱이 페이지 이동해도·새로고침해도 **"내가 뭘 체크했는지" 기억해 두는 상자**. 이 상자는 **Zustand** 라는 도구로 만들고, **브라우저 localStorage에 자동 저장**하도록 설정했습니다."

```ts
const useBadges = create(persist(
  (set) => ({
    visited: [],                          // 방문한 구장 배열
    toggle: (code) => set((s) => ({
      visited: s.visited.includes(code)
        ? s.visited.filter(v => v !== code)
        : [...s.visited, code],
    })),
  }),
  { name: "badges-v1" }                   // localStorage 키 이름
));
```

### 🔥 Firestore Real-time Sync — "실시간 클라우드 구독"

**쉽게 말하면**:
> "Google의 실시간 데이터베이스. 특정 문서에 **'구독 신청'** 해두면, 그 문서가 어디서든 바뀔 때 **자동으로 내 화면에도 통지**됩니다."

비유: **카카오톡 단톡방**. 다른 사람이 쓴 메시지가 실시간으로 내 화면에 뜨는 원리 = Firestore `onSnapshot` 구독.

```
📱 아이폰에서 "잠실" 체크
    │
    ▼ (약 100ms)
☁️ Firestore 의 user_visits/{uid} 문서 업데이트
    │
    ▼ (약 500ms)
💻 PC Chrome 의 구독 콜백이 발화
    │
    ▼
화면에 자동으로 "잠실 ✅" 반영
```

**중복 쓰기 방지**: 자기가 쓴 데이터가 다시 구독으로 들어올 때는 **"시그니처 비교"** 로 무한루프를 차단합니다.

### 🎭 Anonymous UUID — "비로그인 사용자에게도 ID 발급"

**쉽게 말하면**:
> "계정 없이 방문한 사용자에게도 **브라우저별 랜덤 ID (예: `a7f3-2c8b-...`)** 를 발급해서 기록을 잇습니다."

```
첫 방문 → crypto.randomUUID() 로 ID 발급 → localStorage 저장
체크 동작 → 이 ID 기반으로 익명 기록 유지
나중에 로그인 → 익명 데이터를 자동으로 계정에 머지 (syncOnSignIn)
```

비유: **"스타벅스 카드 없이 쿠폰만 찍다가, 나중에 가입할 때 쿠폰 이어받기"** 같은 UX.

### 🔗 URL 직렬화 — "현재 상태를 주소창에 압축"

**쉽게 말하면**:
> "응원팀·기간·예산·인원·이동수단 **5 필드를 URL 쿼리 파라미터로 인코딩**. 링크 받은 친구는 앱 진입하자마자 같은 세팅으로 시작."

```
우리 상태:
{ team: "KIA", dateStart: "2026-04-25", dateEnd: "2026-04-26",
  budget: 50, party: "family", transport: "train" }

URL 직렬화:
/?team=KIA&start=2026-04-25&end=2026-04-26&budget=50&party=family&transport=train
```

### 🔖 `/share/{id}` — "링크 단축 서비스"

위 URL 은 길어서 보기 불편합니다. 그래서:

```
사용자 공유 클릭
  │
  ▼
POST /api/plans  (상태를 Firestore 에 저장)
  │
  └─ nanoid(10) 로 짧은 ID 발급 → "abc123xyz"
        │
        ▼
 짧은 링크 생성: /share/abc123xyz
        │
        ▼
친구가 열면 → Firestore 조회 → 원래 URL 로 리다이렉트 (307)
```

비유: **bit.ly 같은 링크 단축 서비스**를 Firestore로 구현.

**왜 두 가지 방식?**:
- Firebase 구성됨 → 짧은 링크 (`/share/abc123`) · 사람이 외우기 좋음
- Firebase 미구성 → 긴 링크 (`/?team=KIA&...`) · 서버 없이 작동 · graceful fallback

### 🛡️ Firestore Security Rules — "문지기 역할"

```js
match /user_visits/{uid} {
  allow read, write: if request.auth.uid == uid;
}
match /shared_plans/{id} {
  allow read: if true;            // 공유 링크는 누구나 읽기
  allow create: if request.auth != null;
  allow update, delete: if false; // 일회성 링크 · 수정 불가
}
```

비유: **아파트 경비실**. "누가 어디에 쓰고/읽을 수 있는지" 를 규칙으로 정해두고, Firebase 가 매 요청마다 검사.

### 🔗 데이터 흐름 한눈에 보기

```
사용자 구장 토글
  │
  ├─► localStorage (즉시 반영, optimistic UI)
  │
  └─► 0.4초 디바운스
       │
       ▼
     Firestore user_visits/{uid}
       │
       └─► onSnapshot 실시간 전파
              │
              ▼
       다른 기기에서도 자동 갱신
```

---

## 🎯 結 (결) — 어떤 가치를 만들었는가? 결과와 의미

### 숫자로 본 성과

| 지표 | 결과 |
|---|---|
| 체크리스트 토글 반응 | **즉시** (optimistic UI, localStorage 먼저) |
| Firestore 쓰기 지연 | **약 100ms** (평균) |
| 다른 기기 동기화 | **약 500ms** (구독 콜백 발화) |
| 10/10 Celebrate | 모두 체크 시 축하 UI + 배지 |
| 공유 링크 생성 | `POST /api/plans` → 짧은 ID · 30일 만료 |
| graceful degradation | Firebase 미구성 시 localStorage + 긴 URL 로 자동 전환 |
| 모바일 자동 테스트 | iPhone SE · 14 Pro · iPad **전 환경 통과** |
| 라이브 주소 | [배포 완료 ✅](https://my-web-app--mini12-310f5.asia-east1.hosted.app/badges) |

### 사용자에게 남기는 것

**"내 원정 기록을 · 어느 기기에서도 · 계정 없이도 유지하며 · 친구에게는 링크 한 번으로."**

- 종이·엑셀에 기록하는 대신 **10 구장 투어 진행률**이 시각적으로 쌓임
- 10/10 완주 시 **뿌듯함이 즉시 확인**되는 축하 UI
- 친구 초대가 **"링크 복붙 → 같은 세팅"** 한 번에 완결

### 기술적 의의

- **이중화 아키텍처**: 클라우드(Firestore) + 로컬(localStorage) 조합으로 **오프라인 내성 · 비로그인 UX · 다기기 동기화** 3가지 모두 확보
- **Optimistic UI + 디바운스 쓰기**: 사용자 체감 속도는 0ms (즉시 반영) · 서버 호출은 0.4초 묶어서 한 번 (리소스 절약)
- **Graceful Degradation**: Firebase 미구성 · 네트워크 실패 · 비로그인 상태 어디에서도 **핵심 체크리스트 기능은 유지**
- **URL 직렬화 + 단축 링크 이중화**: 서버리스 환경에서도 공유 가능 (`?team=...`), 서버 있을 때는 짧은 ID (`/share/abc123`) 로 업그레이드
- **Firestore Security Rules**: 사용자 A가 B의 뱃지를 조작하지 못하도록 서버 레벨에서 차단

---

## 🔍 부록 — 개발자용 상세 정보

아래는 코드를 다루는 개발자를 위한 참조입니다. 일반 독자는 건너뛰어도 좋습니다.

### A. Firestore 스키마

**`user_visits/{uid}`**
```ts
{
  uid: string,
  visited: string[],              // ["LG", "KT", "두산", ...]
  updatedAt: Timestamp,
}
```

**`shared_plans/{id}`**
```ts
{
  id: string,                     // nanoid(10)
  createdBy: string,              // uid or "anonymous"
  filters: {
    team: string,
    dateStart: string,
    dateEnd: string,
    budget: number,
    party: string,
    transport: string,
  },
  createdAt: Timestamp,
  expiresAt: Timestamp,           // createdAt + 30일
}
```

### B. API 명세

**`POST /api/plans`**
- Body: 현재 `filters` 상태
- 성공: `{ id: string, shortUrl: "/share/{id}" }`
- Firebase 미구성: 503 → 클라이언트 폴백 (long URL 생성 후 클립보드 복사)

**`GET /share/[id]`**
- Firestore 조회 → 발견 시 `redirect(/?team=...)` (307)
- 미발견: "공유 링크를 찾을 수 없습니다" 안내 페이지 (404 대신)
- 만료 (`expiresAt < now`): "링크 만료" 안내

### C. 컴포넌트 매핑

| 컴포넌트 | 파일 | 역할 |
|---|---|---|
| `BadgesPage` | `app/(shell)/badges/page.tsx` | 페이지 엔트리 |
| `BadgesMobileView` | `components/badges/badges-mobile-view.tsx` | 모바일 전용 |
| `StadiumTour` | `components/badges/stadium-tour.tsx` | 10 구장 그리드 + 10/10 celebrate |
| `SharePlanButton` | `components/badges/share-plan-button.tsx` | 공유 URL 생성 · 클립보드 복사 |
| `useBadges` | `lib/store/badges.ts` | Zustand + persist + anonId |
| `useFirestoreSync` | `lib/firebase/use-firestore-sync.ts` | store ↔ Firestore 양방향 |
| 직렬화 | `lib/share/serialize.ts` | Filters ↔ URLSearchParams |
| `/api/plans` | `app/api/plans/route.ts` | POST · 503 graceful |
| `/share/[id]` | `app/share/[id]/page.tsx` | Firestore 조회 → redirect |

### D. 기술 스택

| 계층 | 기술 |
|---|---|
| 클라이언트 상태 | Zustand + persist 미들웨어 |
| 서버 저장소 | Firebase Firestore (Native mode) |
| 실시간 구독 | Firebase Web SDK `onSnapshot` |
| 서버 쓰기 | Firebase Admin SDK (API Route) |
| 공유 URL | `URLSearchParams` · `nanoid` (단축 ID) |
| 익명 ID | `crypto.randomUUID()` |
| 클립보드 | `navigator.clipboard.writeText` |
| 토스트 | sonner |
| 보안 | Firestore Security Rules |

### E. 관련 문서

- [SESSION_E_PLAN.md](./SESSION_E_PLAN.md) — Badges + 공유 구현 원본 설계
- [TAB1_MATCHES_SPEC.md](./TAB1_MATCHES_SPEC.md) — 응원팀 기반 공유 필터 연결
- [TAB3_PLACES_SPEC.md](./TAB3_PLACES_SPEC.md) — 구장 기반 POI 연결
- [TAB4_AI_SPEC.md](./TAB4_AI_SPEC.md) — 동일 Session E 에서 동시 구현
- `frontend/lib/store/badges.ts` — Zustand store + anonId
- `frontend/lib/firebase/use-firestore-sync.ts` — 실시간 동기화 훅
- `frontend/components/badges/stadium-tour.tsx` — Stadium Tour UI
- `frontend/components/badges/share-plan-button.tsx` — 공유 로직
- `frontend/app/share/[id]/page.tsx` — 공유 링크 수신 핸들러
- `firestore.rules` · `firestore.indexes.json` — 보안·인덱스 규칙

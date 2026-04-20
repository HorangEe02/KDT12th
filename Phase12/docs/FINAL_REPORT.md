# 🏟️ 원정 응원 플래너 — 최종 프로젝트 보고서

> **"내 팀 원정 경기 하나만 고르면, 티켓·교통·맛집·숙소·관광을 AI가 한 번에 짜주는 스포츠 관광 플래너"**

**📅 보고서 작성**: 2026-04-19
**🌐 라이브 URL**: [my-web-app--mini12-310f5.asia-east1.hosted.app](https://my-web-app--mini12-310f5.asia-east1.hosted.app)
**🔗 GitHub 저장소**: [HorangEe02/KNU_KDT_12th](https://github.com/HorangEe02/KNU_KDT_12th)
**☁️ 배포 환경**: Firebase App Hosting · Cloud Run `asia-east1` · Firestore `asia-northeast3`

---

## 📋 요약 (Executive Summary)

### 한 줄 소개
KBO 10개 구단 · 전국 8개 도시 · 연간 720경기를 대상으로, **원정 응원러**라는 좁고 깊은 타깃에게 "한 번의 선택으로 전 동선을 완성"하는 **AI 기반 풀스택 웹 서비스**.

### 핵심 성과 6가지

| 영역 | 결과 |
|---|---|
| 🚀 배포 | Firebase App Hosting · Cloud Run Live · 공용 URL 접속 가능 |
| 📱 모바일 최적화 | 자동 테스트 **138/138 PASS** (iPhone SE · 14 Pro · iPad) |
| 🤖 AI 에이전트 | **6 도구 호출 · 4-단계 Multi-Agent · 45 RAG 팁** 통합 |
| 🗺 길찾기 안전망 | Kakao → OSRM → Haversine **3-tier 폴백 100% 성공률** |
| ⚡ 성능 | 캐시 적중 시 **40배 단축** (828ms → 20ms) |
| 🔐 운영 비용 | **무료 티어로 완전 운영** (Gemini · OSRM · TourAPI 조합) |

### 프로젝트 기간
- Phase 1~5 (Python/Streamlit): ~2026-04-17
- Phase 6 (Next.js 마이그레이션): 2026-04-17 ~ 2026-04-19
- 모바일 UX 정비 + 프로필 편집 + AI 개선: 2026-04-19

---

# 📖 起 (기) — 배경과 문제 제기

## 1. 시장의 가능성 — "수요는 이미 폭발했다"

### 숫자로 본 수요
- **KBO 2024 관중**: 1,088만 명 돌파 (프로스포츠 사상 최다)
- **원정 응원 비중**: 역대 최대
- **MZ 세대 팬덤 경제**: 직관 + 인증샷 + 여행의 결합이 일상화

### MZ 원정러의 페르소나
> 25세, 수도권 거주, 월 1~2회 원정. 경기는 물론 **경기장 주변 맛집·인스타 스폿까지 사전에 다 찍고 가는 타입**. 친구 2~3명 함께 가기 때문에 **일정·예산·이동수단을 조율할 "공통 화면"** 이 필요.

## 2. 기존 서비스의 공백 — "전용 서비스가 없다"

원정 응원러가 한 번의 원정을 준비하며 거치는 앱 여정:

| 단계 | 사용 앱 | 문제점 |
|---|---|---|
| 경기 일정 확인 | KBO 공식 · 구단 앱 | 홈/원정 구분 번거로움 |
| 승률·상대 전적 | 네이버 · 블로그 | 데이터 흩어져 있음 |
| 티켓 예매 | 티켓링크 · 인터파크 | 전용 앱 분리 |
| 구장 이동 | 카카오맵 · 네이버지도 | 경기 시간 반영 안 됨 |
| 맛집 찾기 | 블로그 · 인스타 · 망고플레이트 | 정보 일관성 부족 |
| 숙박 예약 | 야놀자 · 여기어때 · 부킹닷컴 | 경기장 근처 거리 재측정 필요 |
| 관광지 검색 | 여행 앱 · 카카오 로드뷰 | 일정 맞춤 안 됨 |

**결과**: 원정 1회 준비에 평균 **2~3시간 검색 + 앱 5~7개 순회**. 이 피로를 해결할 **"원정 응원러 전용 통합 서비스"** 가 시장에 없었습니다.

## 3. 우리의 가설

> **"KBO 일정 · TourAPI 관광 · 기상청 예보 · 카카오 지도 + AI 에이전트"**
> 공공·상용 데이터 4종을 통합하고, 그 위에 자연어 AI 플래너를 얹으면,
> **"경기 하나 선택 → 전 동선 자동 큐레이션"** 의 원클릭 경험을 만들 수 있다.

## 4. 왜 "원정 응원러" 에 집중했나?

- **좁은 타깃 = 깊은 만족**: 범용 여행앱 대비 도메인 특화 큐레이션이 가능
- **데이터 접근성**: KBO 일정·공공 관광·공공 기상이 모두 무료 공공 API
- **감정 드라이버**: "내 팀을 응원하는 여행"이라는 강한 정서적 몰입

---

# 🚀 承 (승) — 솔루션: 5개 탭 기능 소개

사용자의 원정 여정은 **"일정 확인 → 동선 짜기 → 주변 탐색 → AI 상담 → 기록·공유"** 5단계로 이어집니다. 각 단계를 탭 1개씩 맡아 해결합니다.

## Tab 1. 🏟 경기 & 승리예측 — "이길 수 있을까?"

### 왜?
원정 경기 일정 · 상대 전적 · 승률 예측을 한 번에 볼 곳이 없었습니다.

### 뭘?
- 응원팀 원정 경기 **자동 필터** (기간 · 요일 · 중계 · 투수)
- **AI 승률 예측 게이지** (로지스틱 회귀 모델)
- 최근 3년 10팀 **원정 승률 랭킹 바**
- 경기 클릭 시 URL 공유 가능

### 어떻게?
Python **scikit-learn 로지스틱 회귀** 모델을 TypeScript로 이식. 5가지 힌트(원정 승률·홈 승률·순위·순위차)로 0~100% 확률 계산. Plotly로 인터랙티브 차트 렌더링.

### 성과
- Python ↔ TypeScript 예측값 **100% 일치** (4개 샘플 대조)
- 첫 화면 약 1초 (서버사이드 렌더링)

📎 상세: [TAB1_MATCHES_SPEC.md](./TAB1_MATCHES_SPEC.md)

---

## Tab 2. 🗺 동선 지도 — "얼마나 걸리지?"

### 왜?
경기장 · 맛집 · 숙박 · 관광 · 경로 정보가 앱 5~6개에 흩어져 있어, 팬이 매번 같은 좌표를 여러 앱에 복붙해야 했습니다.

### 뭘?
- **4-레이어 지도** (경기장 · 음식점 · 숙박 · 관광지) 토글
- **3단계 길찾기 안전망** (Kakao → OSRM → Haversine)
- 출발지 프리셋 4종 + GPS "내 위치"
- 모바일 전용 하단 카드 (3 stops 전부 탭하여 변경)
- **외부 지도 앱 딥링크** (네이버지도·카카오맵)

### 어떻게?
무료·오픈소스 **Leaflet + OpenStreetMap** 기반 지도. 길찾기는 **엘리베이터→계단→걷기 식 3단계 폴백** — 어떤 상황에서도 경로를 보여줌. 서버 메모리 캐시로 40배 속도 향상. `safe-area-inset` CSS로 iPhone 노치 자동 대응.

### 성과
- 길찾기 **성공률 100%** (어떤 환경에서도 경로 반환)
- 캐시 적중 **828ms → 20ms** (40× 단축)
- 카카오 승인 없이도 OSRM 자동 폴백으로 정상 작동

📎 상세: [TAB2_MAP_SPEC.md](./TAB2_MAP_SPEC.md) · [OSM_FALLBACK_PLAN.md](./OSM_FALLBACK_PLAN.md)

---

## Tab 3. 🍽 주변 플레이스 — "뭐 먹고·자고·보지?"

### 왜?
경기장 주변 맛집·숙박·관광지는 블로그·인스타·여행앱에 흩어져 있어 매번 "블로그 5~6개 돌려보기" 를 반복했습니다.

### 뭘?
- 10 구장 × 3 카테고리 **POI 카드 리스트** (총 약 600KB)
- **거리순 자동 정렬** + 500m 이내 "추천" 배지
- **"더 보기" 버튼** 으로 12개씩 점진 로딩
- 데스크톱 **TOP 10 미니 지도 + 거리×평점 산점도**
- 모바일 **플로팅 지도 버튼(FAB)**: 원터치 지도 탭 이동

### 어떻게?
**한국관광공사 TourAPI** (정부 공식 관광 DB) 에서 구장별 반경 2km · 카테고리별 100건을 **빌드 타임에 미리 수집** 해 JSON 파일로 저장. URL `?limit=N` 기반 페이지네이션. 마커 ↔ 카드 양방향 연동으로 지도·리스트 대화.

### 성과
- 데이터 자동 캐시로 **런타임 API 호출 0건** · 안정성 극대화
- "더 보기" 연속 확장 테스트 **PASS**
- URL 기반 상태 공유 가능

📎 상세: [TAB3_PLACES_SPEC.md](./TAB3_PLACES_SPEC.md)

---

## Tab 4. 🤖 AI 플래너 — "비 올까? 몇 시야?"

### 왜?
일반 ChatGPT에게 "이번 주말 한화 원정 경기 알려줘" 라고 물으면 *"실시간 정보는 확인이 어렵습니다"* 라고 답합니다. AI가 **실제 데이터를 모르기** 때문.

### 뭘?
- 자연어 **멀티턴 채팅** (ChatGPT 스타일 스트리밍)
- **6개 도구 호출** (경기·승률·날씨·맛집·길찾기·팁)
- **Multi-Agent 4-단계 협업** (총괄 → 전문가 병렬 → 작성자)
- **RAG (45개 원정 팁)** 으로 전문성 보강
- 🎬 **Mock 시연 모드** (네트워크 무관 3 시나리오)

### 어떻게?
**Google Gemini 2.5 Flash Lite** (무료 티어) + **Vercel AI SDK v6**. AI에 "손(도구)" 을 달아 실제 함수 호출 후 결과 기반 답변 생성. 기상청 API는 **Lambert 격자 좌표 변환** 공식을 Python → TypeScript로 정확 이식. 실시간 스트리밍으로 체감 속도 ↑.

### 성과
- 실무급 AI 에이전트 시스템 (도구 + 멀티에이전트 + RAG + 스트리밍) 통합
- 0건 결과 시 명시적 메시지 ("해당 원정 경기 일정은 없습니다")
- Mock 모드로 발표장 네트워크 무관 데모

📎 상세: [TAB4_AI_SPEC.md](./TAB4_AI_SPEC.md)

---

## Tab 5. 🏆 뱃지 & 공유 — "기록하고·나누고 싶다"

### 왜?
"10 구장 전부 원정 응원 가기"는 KBO 팬의 작은 버킷리스트. 종이·엑셀로 관리하면 유실되고, 친구에게 계획 공유하려면 카톡으로 일일이 설명해야 했습니다.

### 뭘?
- 10 구장 **Stadium Tour 체크리스트**
- 10/10 완주 시 **축하 UI + 달성 배지**
- **디바이스 간 자동 동기화** (Firestore 실시간)
- **비로그인도 체크 가능** (익명 UUID + localStorage)
- **계획 공유 링크** (짧은 `/share/abc123` + 긴 URL 이중화)

### 어떻게?
**이중화 저장** (편의점 포인트처럼 영수증/앱 둘 다 기록): localStorage 즉시 + Firestore 비동기. **실시간 구독** 으로 다기기 동기화 (카카오톡 단톡방 원리). **Graceful Degradation** 으로 Firebase 미구성 · 네트워크 실패 · 비로그인 상태에서도 핵심 기능 유지. 공유 링크는 `bit.ly` 스타일 Firestore 단축 서비스.

### 성과
- 다기기 동기화 약 **500ms** (Firestore 실시간 콜백)
- 공유 링크 짧은 ID 10자 · 30일 만료
- Firebase 미구성 시 자동 long URL 폴백

📎 상세: [TAB5_BADGES_SPEC.md](./TAB5_BADGES_SPEC.md)

---

# ⚙️ 轉 (전) — 전체 기술과 아키텍처

## 1. 시스템 아키텍처 전체도

```
┌────────────────────────────────────────────────────────────────┐
│  📱💻 사용자 브라우저 (iPhone · iPad · PC)                       │
│  React 19.2 · Tailwind v4 · Zustand · Leaflet · Plotly · AI SDK │
└──────────────────────┬─────────────────────────────────────────┘
                       │ HTTPS · SSR · UIMessageStream
                       ▼
┌────────────────────────────────────────────────────────────────┐
│  ☁️ Firebase App Hosting (Next.js 16 / Cloud Run asia-east1)    │
│  ├ App Router: 5 routes + /account + /share                     │
│  ├ API Routes: predict · route · chat · plans · profile         │
│  ├ Middleware: 인증 게이트 (미로그인 → /login)                    │
│  └ Static: /public/data/*.json · /logos/*.svg                  │
└─────────┬───────────────┬────────────────────┬─────────────────┘
          ▼               ▼                    ▼
     🧠 Google        🗺 Kakao / OSRM      ☁️ Firebase (Firestore)
       Gemini 2.5      (3-tier route)       · users (프로필)
      (Tool+RAG)                             · user_visits (뱃지)
                      🌧 기상청 API          · shared_plans (공유)
                      (Lambert 변환)         · Auth (세션 쿠키)

                      🏛 TourAPI (빌드 타임 수집)
```

## 2. 계층별 기술 스택

### 프론트엔드
| 기술 | 역할 | 선택 이유 |
|---|---|---|
| **Next.js 16 App Router** | 프레임워크 (SSR + API) | 최신 Server Component · 빠른 첫 페인트 · Cloud Run 호환 |
| **React 19.2** | UI 라이브러리 | 업계 표준 · 컴포넌트 생태계 |
| **Tailwind v4 + SE 토큰** | 스타일 | 디자인 토큰 기반 테마 · Stadium Editorial 디자인 시스템 |
| **Zustand** | 클라이언트 상태 | Redux 대비 경량 · persist 미들웨어 |
| **Leaflet + React-Leaflet** | 지도 | 무료·오픈소스 · 상용 API 대비 비용 0 |
| **Plotly.js** | 차트 | 인터랙티브 + 반응형 + 한글 지원 |
| **vaul** | Bottom Sheet | 네이티브 iOS UX · 드래그 핸들 + snap point |

### 백엔드 · API
| 기술 | 역할 | 선택 이유 |
|---|---|---|
| **Firebase App Hosting** | 배포 | Next.js 풀스택 배포 · GitHub 연동 가능 · 무료 티어 |
| **Firebase Admin SDK** | 서버 권한 | 세션 쿠키 검증 · Firestore 서버 쓰기 |
| **Firebase Web SDK** | 클라이언트 | 실시간 구독 · Auth 흐름 |
| **Google Gemini 2.5 Flash Lite** | LLM | 무료 티어 15 RPM · 한국어 우수 · tool calling |
| **Vercel AI SDK v6** | AI 통합 | Zod 기반 tool 정의 · 스트리밍 · UIMessageStream |

### 데이터
| 소스 | 용도 | 접근 방식 |
|---|---|---|
| **KBO 2026 일정** | 경기 데이터 | CSV → JSON 빌드 타임 변환 |
| **팀 10년 통계** | 승률 모델 학습 | CSV → sklearn 훈련 → TS 이식 |
| **한국관광공사 TourAPI** | POI (맛집·숙박·관광) | 빌드 타임 수집 → JSON 캐시 |
| **기상청 단기예보** | 날씨 | 런타임 Lambert 변환 후 호출 |
| **카카오 모빌리티 API** | 길찾기 Tier 1 | 무권한 시 skip |
| **OSRM public demo** | 길찾기 Tier 2 | 무료·HTTPS · 5초 timeout |

### 보안 · 운영
| 기술 | 역할 |
|---|---|
| **Firebase Auth + 세션 쿠키 (5일)** | 로그인 · `__session` httpOnly |
| **Firestore Security Rules** | `auth.uid == document id` 검증 |
| **Next.js Middleware** | 미인증 → `/login?next=` 자동 리다이렉트 |
| **Secret Manager (7 시크릿)** | API 키 안전 보관 (env 비노출) |
| **Zod 런타임 검증** | API body · 외부 데이터 파싱 |
| **`viewportFit: "cover"` + `env(safe-area-inset-*)`** | 노치·홈 인디케이터 자동 대응 |

## 3. 핵심 설계 의사결정

### 의사결정 1 — "왜 Python Streamlit 에서 Next.js 로 옮겼나?"
**이유**: Streamlit 은 프로토타이핑엔 최적이지만 모바일 UX·공유 가능 URL·SEO 가 약함. Next.js 16 으로 마이그레이션하면서:
- 모바일 전용 뷰 (AiMobileView · MatchesMobileView 등) 별도 구현
- URL 직렬화로 상태 공유
- SSR 첫 페인트 1초 이내

### 의사결정 2 — "왜 무료 기술을 고집했나?"
**이유**: 학생·개인 프로젝트에서 **월 고정비 0원 운영** 을 증명하고자 함.
- Gemini Flash Lite (무료 티어)
- OpenStreetMap + OSRM (무료)
- Firebase 무료 티어 (Firestore 일 5만 reads · Hosting 10GB)
- TourAPI (무료)

### 의사결정 3 — "왜 3-tier 길찾기 안전망을 만들었나?"
**이유**: 상용 API (카카오 모빌리티) 는 유료 승인 필요, 공개 API (OSRM) 는 가끔 다운됨. 사용자에게 **"경로를 못 보여주는 상황"** 을 만들지 않으려면 수학적 직선 거리 공식 (Haversine) 까지 3단계 방어가 필요.

### 의사결정 4 — "왜 뱃지 저장을 이중화했나?"
**이유**: "Firebase 로만 저장하면 비로그인 사용자 불가 · 로컬만 저장하면 다기기 동기화 불가" 의 딜레마. localStorage + Firestore **이중화**로 둘 다 해결, graceful degradation 으로 어느 한쪽이 실패해도 핵심 기능 유지.

### 의사결정 5 — "왜 모든 탭에 모바일 전용 뷰를 별도로 만들었나?"
**이유**: Tailwind 반응형만으로는 모바일의 **bottom sheet + 풀스크린 지도 + glass pill 입력** 같은 네이티브 패턴을 재현하기 어려움. 각 탭마다 `*MobileView` 컴포넌트를 독립 구현해 `md:hidden` 으로 렌더 분기.

## 4. 전 탭을 관통하는 기술 비유 (비전공자용 복습)

| 기술 | 비유 |
|---|---|
| **승률 예측 모델** | 과거 데이터로 미래 확률을 계산하는 수학적 점술 |
| **3-tier 길찾기** | 엘리베이터 → 계단 → 걷기 안전망 3단계 |
| **캐시** | "엄마가 어제 물어본 레시피 또 물어보면 바로 대답하는 것" |
| **TourAPI** | 정부 공식 관광 DB · 공공 위키피디아 |
| **도구 호출 AI** | AI에게 "손"을 달아 실제 함수 호출시키기 |
| **Multi-Agent** | 변호사·의사·세무사에게 각각 묻고 한 사람이 종합 |
| **RAG** | 시험 치기 전 참고 자료 미리 읽혀주기 |
| **이중화 저장** | 편의점 포인트 — 영수증 찍고 · 앱도 찍기 |
| **실시간 Firestore** | 카카오톡 단톡방 (타인 메시지가 내 화면에 즉시) |
| **safe-area-inset** | 방 배치할 때 기둥 피해서 가구 놓기 |

---

# 🎯 結 (결) — 성과와 프로젝트의 의의

## 1. 종합 실측 성과표

| 영역 | 지표 | 결과 |
|---|---|---|
| **배포** | 프로덕션 URL | ✅ [Live](https://my-web-app--mini12-310f5.asia-east1.hosted.app) |
| **배포** | Firestore rules + indexes | ✅ 배포 완료 |
| **배포** | 6 라우트 + 2 API | 모두 200 OK |
| **모바일** | 자동 테스트 (Playwright) | **138/138 PASS** (3 뷰포트) |
| **모바일** | 8 모바일 이슈 정비 | 모두 완료 (viewport · safe-area · 44px · BottomSheet · pagination · iPad sidebar · overflow 가드) |
| **성능** | 첫 페인트 (SSR) | < 1초 |
| **성능** | 캐시 적중 | 20ms (40× 단축) |
| **AI** | Tool calling | `predict_win_rate` · `search_game` 등 자동 호출 PASS |
| **AI** | Mock 모드 | 3 시나리오 즉시 스트리밍 PASS |
| **승률 모델** | Python ↔ TypeScript 일치 | **100%** (4 샘플) |
| **보안** | 인증 게이트 | 미로그인 시 /login 자동 리다이렉트 PASS |
| **비용** | 월 운영비 | **₩0** (무료 티어 조합) |

## 2. 사용자 관점의 가치

### "시간 절약"
- 원정 준비 평균 2~3시간 → 약 5~10분
- 앱 5~7개 순회 → 탭 하나에서 완결

### "결정 근거"
- "이길 것 같다" 감이 아닌 **AI 승률 예측 %** 제공
- 블로그 순회가 아닌 **TourAPI 공공 데이터** 큐레이션
- "대충 근처" 가 아닌 **정확한 거리·시간** 안내

### "공유 가능"
- URL 하나로 친구에게 **전체 계획 상태** 이관
- 10/10 Stadium Tour 달성 시 **뱃지** 로 인증

### "어디서든"
- iPhone (노치·홈 인디케이터 자동 대응) · iPad · 안드로이드 · 데스크톱 모두 최적화
- 로그인·비로그인 모두 핵심 기능 사용 가능
- 네트워크 불안정 시에도 Mock/캐시로 대응

## 3. 기술적 의의

### 🎯 도메인 특화 AI 에이전트의 실증
- 단순 ChatGPT 호출이 아닌 **실제 데이터에 접근하는 tool-calling + multi-agent + RAG** 통합 시스템 구축
- 프롬프트에 답변 원칙 7조 명시 · 0건 응답 명시적 메시지 등 **실무급 에이전트 품질 관리**

### 🗺 무료 생태계로도 완성 가능 증명
- Gemini · OSM · TourAPI · KMA 등 **무료 공공·오픈소스 API 조합** 으로 상용 수준 서비스 운영
- 3-tier 길찾기 폴백으로 상용 API 없어도 완전한 길찾기 기능 구현

### 📱 모바일 퍼스트 실전 적용
- viewport meta · safe-area-inset · 동적 snap points · 페이지네이션 · 44px 터치 타깃
- 자동 스모크 테스트 138/138 PASS 로 회귀 방지 체계 구축

### 🔄 Python → TypeScript 정확 이식
- scikit-learn 로지스틱 회귀 수학식 직접 이식
- 기상청 Lambert 격자 변환 공식 이식
- 두 언어 예측값 100% 일치 검증

### 🛡 안전한 배포 운영
- Middleware 인증 게이트 · Firestore Security Rules · httpOnly 세션 쿠키
- Secret Manager 7 시크릿 분리 관리 · 소스 코드 하드코딩 0건

## 4. 프로젝트 개발 과정 회고

### Phase 1~5 (Python / Streamlit · ~2026-04-17)
- 데이터 파이프라인 · React 하이브리드 UI
- Folium 지도 · Plotly 차트 · Kakao 경로
- scikit-learn 승률 모델 · Ollama 로컬 LLM
- Firebase 풀스택 배포 코드

### Phase 6 (Next.js 마이그레이션 · 2026-04-17 ~ 19)
- **Session A**: Next.js 16 스캐폴딩 · 의존성 16개
- **Session B**: SE 테마 + Hero + TeamSelector
- **Session C**: 승률 TS 포팅 + matches 탭
- **Session D**: OSM 3-tier 폴백 + map 탭
- **Session E**: AI 챗봇 + 뱃지 + 공유
- **Session F**: App Hosting 배포 준비 + 런북

### Phase 6 + 확장 (2026-04-19)
- 모바일 UX 정비 8 이슈 + 자동 스모크 138/138
- 프로덕션 배포 + 레거시 Cloud Run 정리
- 프로필 편집 페이지 + 인증 게이트 + 로그아웃
- AI 0건 응답 개선 + Topnav 팀 배지 수정

## 5. 남은 과제 · 향후 개선 포인트

| 영역 | 과제 |
|---|---|
| **데이터 신선도** | TourAPI 자동 재수집 스케줄러 (현재는 수동 빌드) |
| **실제 사용자 테스트** | 베타 사용자 모집 · UX 설문 · 전환율 측정 |
| **관리자 기능 확장** | 타 회원 프로필 편집 · 콘텐츠 모더레이션 |
| **알림** | 원정 D-1 푸시 알림 · 날씨 급변 알림 |
| **예약 연동** | 티켓링크 · 호텔 예약 딥링크 심화 |
| **커뮤니티** | "같이 가요" 동행 찾기 기능 |
| **다국어** | 일본·대만 KBO 팬 대상 다국어 지원 |

---

## 📎 부록

### A. 상세 기능 설명서 (5탭)

| 탭 | 파일 | 핵심 비유 |
|---|---|---|
| 1. 경기 & 승리예측 | [TAB1_MATCHES_SPEC.md](./TAB1_MATCHES_SPEC.md) | 로지스틱 회귀 = 과거로 미래 확률 계산 |
| 2. 동선 지도 | [TAB2_MAP_SPEC.md](./TAB2_MAP_SPEC.md) | 엘리베이터→계단→걷기 3단계 안전망 |
| 3. 주변 플레이스 | [TAB3_PLACES_SPEC.md](./TAB3_PLACES_SPEC.md) | TourAPI = 정부 공식 관광 DB |
| 4. AI 플래너 | [TAB4_AI_SPEC.md](./TAB4_AI_SPEC.md) | AI에게 "손" 달아주기 + 전문가 4인 협업 |
| 5. 뱃지 & 공유 | [TAB5_BADGES_SPEC.md](./TAB5_BADGES_SPEC.md) | 편의점 포인트 이중화 + 단톡방 sync |

### B. 설계 · 운영 문서

- [PHASE6_NEXTJS_MIGRATION.md](./PHASE6_NEXTJS_MIGRATION.md) — 마이그레이션 전체 로드맵
- [OSM_FALLBACK_PLAN.md](./OSM_FALLBACK_PLAN.md) — 3-tier 길찾기 설계
- [SESSION_E_PLAN.md](./SESSION_E_PLAN.md) — AI + 뱃지 + 공유 구현
- [SESSION_F_DEPLOY_RUNBOOK.md](./SESSION_F_DEPLOY_RUNBOOK.md) — 배포 단계별 가이드
- [ARCHITECTURE.md](./ARCHITECTURE.md) — 시스템 아키텍처
- [DEMO_SCRIPT.md](./DEMO_SCRIPT.md) — 3분 발표 시나리오
- [QA_PREP.md](./QA_PREP.md) — 예상 질문·답변

### C. 디렉토리 맵 (최상위)

```
Phase12/
├ frontend/              # Next.js 16 메인 앱 (Production)
│  ├ app/                # App Router 라우트 · API Route
│  ├ components/         # UI 컴포넌트 (모바일/데스크톱 분기)
│  ├ lib/                # 데이터·AI·스토어·검증 로직
│  ├ public/             # 정적 에셋 (data JSON · 팀 로고)
│  └ middleware.ts       # 인증 게이트
├ docs/                  # 모든 문서 (본 보고서 포함)
├ data/                  # 원본 CSV (KBO 일정·팀 통계)
├ scripts/               # preflight · 데이터 검증
├ legacy/                # Phase 1~5 Python 레거시 (보존)
└ firebase.json          # App Hosting 배포 설정
```

### D. 실행 방법

#### 로컬 개발
```bash
cd frontend
pnpm install
pnpm dev                 # http://localhost:3000
```

#### 프로덕션 빌드 + 배포
```bash
cd frontend
pnpm build               # 로컬 빌드 검증
cd ..
bash scripts/preflight.sh            # 사전 점검
firebase deploy --only apphosting --project mini12-310f5  # 배포
```

### E. 자동 테스트

```bash
python3 /tmp/mobile_smoke_test.py    # 모바일 138/138 체크
```

### F. 기술 용어 미니 사전 (비전공자용)

| 용어 | 설명 |
|---|---|
| **API** | 외부 서비스와 데이터 주고받는 창구 |
| **SSR** | 서버에서 미리 페이지 만들어 보내주는 방식 |
| **CSR** | 브라우저에서 JavaScript로 페이지 조립 |
| **LLM** | 대형 언어 모델 (ChatGPT·Gemini 등) |
| **Tool Calling** | AI가 외부 함수 호출해서 실제 데이터 조회 |
| **RAG** | AI에게 참고 자료 먼저 보여주고 답변 생성 |
| **Firestore** | Google의 실시간 클라우드 DB |
| **localStorage** | 브라우저 내부 작은 메모장 |
| **Zustand** | React 앱의 상태 관리 라이브러리 |
| **Zod** | 데이터 형식 검사 라이브러리 (문지기) |
| **Leaflet** | 오픈소스 지도 라이브러리 |
| **OSRM** | 오픈소스 길찾기 서비스 |
| **Haversine** | 두 좌표 간 직선 거리 계산 공식 |
| **viewport-fit: cover** | iPhone 노치 영역까지 컨텐츠 확장 |
| **safe-area-inset** | 노치·홈인디케이터 안전 여백 |
| **Middleware** | 요청이 라우트에 도착하기 전에 가로채는 미들웨어 |
| **Graceful Degradation** | 점진적 성능 저하 (일부 기능 실패 시에도 핵심 유지) |

---

**📅 문서 작성일**: 2026-04-19
**✍️ 최종 상태**: Phase 6 배포 완료 + 모바일 UX 정비 완료 + 프로필 편집 완료 + AI 개선 완료
**🌐 라이브**: https://my-web-app--mini12-310f5.asia-east1.hosted.app

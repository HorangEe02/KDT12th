# FORGE SENTINEL 대시보드 — 전체 개선 이력 & 최종 상태

> 초기 모놀리식 → 현재 모듈 아키텍처까지의 전체 개선 기록

---

## 1. 프로젝트 진화 과정

### 1.1 수치로 보는 Before → After

| 항목 | Before (최초) | Phase 1 (아키텍처) | Phase D (고급 기능) | 최종 (현재) |
|------|--------------|-------------------|-------------------|------------|
| 소스 파일 수 | 4개 | 38개 | 55개 | **59개** |
| App.jsx 줄 수 | 481줄 | 146줄 | 155줄 | **155줄** |
| 총 코드 줄 수 | ~600줄 | ~2,620줄 | ~3,600줄 | **~4,000줄** |
| 프로덕션 의존성 | 2개 | 4개 | 4개 | **4개** |
| CSS 방식 | 인라인 100% | CSS Modules | CSS Modules | **CSS Modules + CSS 변수 테마** |
| 라우팅 | useState | React Router | React Router | **React Router (8개 경로)** |
| 코드 스플리팅 | 없음 | React.lazy | React.lazy | **7개 페이지 청크** |
| 차트 | SVG polyline | Recharts | Recharts | **Area/Radar/Bar/Line 4종** |
| 이미지 용량 | 22MB PNG | 22MB PNG | 22MB PNG | **3.5MB WebP (84%↓)** |
| 빌드 시간 | ~230ms | ~300ms | ~400ms | **~460ms** |
| i18n 키 수 | 0 | 0 | 75키 | **150키 (한/영 완전)** |

### 1.2 구현 완료 단계별 요약

#### Phase 1: 아키텍처 기반 (✅ 완료)
- **1A** 모놀리식 파일 분리 → components/pages/data/hooks/styles
- **1B** 인라인 스타일 → CSS Modules (13개 .module.css)
- **1C** React Router + React.lazy 코드 스플리팅

#### Phase 2: UI/UX 강화 (✅ 완료)
- **2C** Recharts 도입 (AreaChart, RadarChart, BarChart)
- **2A** 페이지 전환 fadeIn 애니메이션
- **2B** 대시보드 카드 클릭 → 해당 페이지 이동

#### Phase 3: 신규 기능 (✅ 완료)
- **3A** Settings 페이지 (토글/슬라이더/셀렉트/시스템 정보)
- **3B** 실시간 알림 시뮬레이션 (5초 간격 + 교대 근무 패턴)
- **3C** 모델 비교 테이블/차트 토글 + 메트릭 선택
- **3D** CSV 내보내기

#### Phase A: 품질 개선 (✅ 완료)
- **A1** Error Boundary (페이지 로드 실패 시 RETRY UI)
- **A2** React.memo (6개 컴포넌트 + 2개 ChartTooltip)
- **A3** 미사용 파일 삭제 (theme.js, src/assets/)
- **A4** 잔존 인라인 스타일 CSS 클래스 전환

#### Phase B/C: 상태 관리 + 테마 (✅ 완료)
- **B2** Settings localStorage 영속화
- **B3** Context API (SettingsContext, ToastContext, SearchContext)
- **C2** 다크/라이트 테마 (CSS 변수 + data-theme 전환)
- **C4** Toast 알림 시스템 (critical 알림 팝업)

#### Phase D: 고급 기능 (✅ 완료)
- **D1** 글로벌 검색 (Cmd+K 커맨드 팔레트, 퍼지 매칭)
- **D2** 모델 히스토리 (20에폭 학습 곡선, 모듈/모델 선택, LineChart)
- **D3** PDF 리포트 (window.print + @media print, pageContent.js 추출)
- **D4** 다국어 i18n (en/ko 150키, useTranslation 훅)

#### 기술 부채 해결 (✅ 전체 해결)
- **H2** Recharts 색상 하드코딩 → useChartColors() CSS 변수 연동
- **H3** 이미지 22MB → 3.5MB WebP 변환 (84% 절감)
- **L7** 잔존 인라인 스타일 2건 CSS 클래스 전환

#### 한글화 (✅ 완료)
- ko.json 150키 완전 번역 (네비게이션, 설정, 데이터셋, 인사이트, 알림, 테이블, 시스템 정보)
- pageContent.js → i18n 키 참조 방식 전환
- History/Settings/Dashboard/PrintLayout 모두 t() 호출 적용

---

## 2. 최종 아키텍처

```
src/ (59개 파일)
├── components/  12개 (AnimNum, CircGauge, StatusDot, Label, Panel,
│                      MiniChart, ImgModal, ErrorBoundary, ToastContainer,
│                      CommandPalette, ReportButton, PrintLayout)
├── pages/       8개  (Dashboard, Casting, SegTile, PCB, NLP,
│                      History, Settings, SubPage)
├── context/     3개  (SettingsContext, ToastContext, SearchContext)
├── data/        7개  (navigation, metrics, models, images, alerts,
│                      pageContent, modelHistory)
├── hooks/       3개  (useSimStream, useSearchIndex, useTranslation)
├── i18n/        3개  (en.json, ko.json, index.js)
├── utils/       2개  (fuzzyMatch, cssVar)
├── styles/      2개  (global.css, print.css)
├── App.jsx + App.module.css
└── main.jsx
```

---

## 3. 향후 과제 (미구현)

아래 항목들은 브레인스토밍에서 제안되었으나 현재 프로젝트 범위에서 구현하지 않은 기능입니다.

| 카테고리 | 항목 | 난이도 | 비고 |
|----------|------|--------|------|
| 테스트 | Vitest + React Testing Library | 중 | 핵심 컴포넌트 커버리지 |
| 배포 | GitHub Pages / Vercel | 낮 | 데모 URL 확보 |
| 검색 고도화 | 다국어 검색 (ko.json 키 기반) | 중 | 현재 영어만 검색 |
| 대시보드 | 위젯 드래그&드롭 커스터마이징 | 높 | react-grid-layout |
| 백엔드 | 사용자 인증 + DB | 높 | 실제 배포 시 필수 |
| 제조 | OEE/SPC/배치추적 | 높 | 실제 공장 투입 시 필수 |

---

*최종 업데이트: 2026-04-06*
*프로젝트: FORGE SENTINEL v2.4.1*

# FORGE SENTINEL

> AI 스마트 팩토리 품질관리 대시보드

**React 19** + **Vite 8** + **Recharts** + **React Router** 기반의 스마트 팩토리 품질관리 대시보드입니다.
4가지 딥러닝 모델(CNN, U-Net, YOLOv8, DistilBERT)의 성능 메트릭을 실시간으로 모니터링합니다.

---

## Tech Stack

| 기술 | 버전 | 용도 |
|------|------|------|
| React | 19.2 | UI 프레임워크 |
| Vite | 8.0 | 빌드 도구 (HMR, 코드 스플리팅) |
| React Router | 7.14 | 클라이언트 라우팅 (URL 동기화) |
| Recharts | 3.8 | 인터랙티브 차트 (Area, Radar, Bar, Line) |
| CSS Modules | - | 스코프드 스타일링 + CSS 변수 테마 |

## Features

### 핵심 기능
- **대시보드 개요** — 4개 모델 원형 게이지, 레이더 차트, 실시간 생산 트렌드(시간 범위 1H/6H/24H/7D)
- **AI 모듈 상세 페이지** — Casting / Segmentation / PCB / NLP 모델별 벤치마크 + 분석 이미지 갤러리
- **모델 히스토리** — 20에폭 학습 곡선 시각화, 모듈별/모델별 선택, 최종 에폭 요약 테이블
- **모델 비교** — 테이블 ↔ Bar Chart 토글 뷰, 메트릭 선택, CSV 내보내기

### 인터랙티브
- **글로벌 검색** — `Ctrl+K` / `Cmd+K` 커맨드 팔레트 (퍼지 매칭, 화살표 키 탐색)
- **실시간 알림** — 5초 간격 자동 생성, Toast 팝업, 심각도별 색상, LIVE 인디케이터
- **다크/라이트 테마** — Settings에서 실시간 전환, Recharts 차트 색상도 자동 연동
- **PDF 리포트** — 모듈별 또는 전체 리포트, `window.print()` + @media print CSS

### 다국어 (i18n)
- **한국어/영어 전환** — Settings → 언어 → 즉시 전체 UI 전환
- **150+ 번역 키** — 네비게이션, 설정, 데이터셋, 인사이트, 알림, 시스템 정보 완전 한글화
- **localStorage 영속** — 새로고침 후에도 언어/테마 설정 유지

### 품질 & 성능
- **Error Boundary** — 페이지 로드 실패 시 우아한 에러 UI + RETRY 버튼
- **React.memo** — 6개 컴포넌트 + 2개 ChartTooltip 메모이제이션
- **코드 스플리팅** — `React.lazy()` + `Suspense` 페이지별 청크 분리
- **이미지 최적화** — PNG → WebP 변환 (22MB → 3.5MB, 84% 절감) + lazy loading
- **CSS 변수 테마** — 다크/라이트 전환 시 차트 포함 전체 색상 동기화

## Project Structure

```
src/ (59개 파일, ~4,000줄)
├── components/       AnimNum, CircGauge, StatusDot, Label, Panel,
│                     MiniChart, ImgModal, ErrorBoundary, ToastContainer,
│                     CommandPalette, ReportButton, PrintLayout
├── pages/            Dashboard, Casting, SegTile, PCB, NLP,
│                     History, Settings, SubPage (공통 템플릿)
├── context/          SettingsContext (localStorage), ToastContext,
│                     SearchContext (Cmd+K)
├── data/             navigation, metrics, models, images, alerts,
│                     pageContent, modelHistory
├── hooks/            useSimStream, useSearchIndex, useTranslation
├── i18n/             en.json (150키), ko.json (150키), index.js
├── utils/            fuzzyMatch, cssVar (Recharts 테마 연동)
├── styles/           global.css (다크/라이트 변수), print.css
├── App.jsx           Router shell + 레이아웃
└── main.jsx          Providers (Search > Settings > Toast)
```

## Getting Started

```bash
# 의존성 설치
npm install

# 개발 서버 실행
npm run dev

# 프로덕션 빌드
npm run build

# 빌드 미리보기
npm run preview
```

## Keyboard Shortcuts

| 단축키 | 동작 |
|--------|------|
| `1`~`7` | 페이지 이동 (대시보드 → 모델 히스토리 → 설정) |
| `Ctrl+K` / `Cmd+K` | 글로벌 검색 커맨드 팔레트 |
| `ESC` | 모달 / 검색 닫기 |
| `↑↓` | 검색 결과 탐색 |
| `Enter` | 검색 결과 선택 |

## AI Models

| 모듈 | 모델 | 메트릭 | 성능 |
|------|------|--------|------|
| 주조 불량 분류 | EfficientNet-B0 | Accuracy | 96.5% |
| 표면 결함 세그먼테이션 | ResNet34-UNet | Dice Score | 80.0% |
| PCB 결함 탐지 | YOLOv8m | mAP@0.5 | 95.0% |
| 설비 고장 예측 | DistilBERT | Accuracy | 97.4% |

## Build Info

| 항목 | 수치 |
|------|------|
| 소스 파일 | 59개 |
| 코드 줄 수 | ~4,000줄 |
| 프로덕션 의존성 | 4개 |
| 빌드 시간 | ~460ms |
| 이미지 용량 | 3.5MB (WebP) |

---

> K-Digital Training 딥러닝 12기 미니프로젝트
> 상세 프로젝트 개요: [../README.md](../README.md)

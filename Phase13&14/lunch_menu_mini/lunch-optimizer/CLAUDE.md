# CLAUDE.md — lunch-optimizer

이 파일은 Claude Code 가 본 프로젝트를 작업할 때 참고하는 컨텍스트 문서입니다.

## 프로젝트 개요

**lunch-optimizer** 는 Mini "직장인 점심 최적화 파이프라인" 의 Python 백엔드입니다.
React 대시보드 (`../lunch-optimizer-dashboard.jsx`) 와 연동되는 데이터 파이프라인 ·
REST API · 추천 엔진을 제공합니다.

## 상위 문서

- **전체 조감:** `../0README.md`
- **상세 기획서:** `../README.md`
- **서브토픽 가이드:** `../GUIDE/GUIDE_SUBTOPIC_{1..4}_*.md`
- **NLP 확장:** `../NLP/README.md`

## 기술 스택

| 레이어 | 기술 |
|---|---|
| 언어 | Python 3.10+ |
| ORM | SQLAlchemy 2.0 |
| DB | SQLite (MVP) |
| API 서버 | FastAPI + uvicorn |
| HTTP 클라이언트 | requests, httpx |
| 스케줄러 | APScheduler |
| 테스트 | pytest |
| 린트 | ruff |

## 환경 변수

**공용 `.env` 는 `Mini/.env`** (상위 경로) 에 위치합니다.
본 프로젝트는 상위 경로의 `.env` 를 자동으로 로드합니다.

주요 변수:
- `KAKAO_REST_API_KEY` — 카카오 로컬 API
- `DATA_GO_KR_API_KEY_DECODED` — 공공데이터포털 (기상청·식약처 공용)
- `OFFICE_LAT`, `OFFICE_LNG` — 사무실 좌표
- `DB_URL` — SQLite 경로

## 프로젝트 구조

```
lunch-optimizer/
├── CLAUDE.md                      # 본 파일
├── requirements.txt
├── config/
│   └── settings.py               # 환경 변수 로드 + 공용 설정
├── database/
│   ├── connection.py             # SQLAlchemy 엔진/세션
│   └── models.py                 # ORM 모델
├── pipeline/
│   ├── collectors/               # 외부 API 수집
│   │   └── restaurant_collector.py   # Subtopic 1
│   ├── transformers/             # 데이터 정제·점수 산출
│   │   └── distance_scorer.py        # Subtopic 1
│   ├── loaders/
│   │   └── db_loader.py          # DB 적재
│   └── scheduler.py              # APScheduler
├── api/
│   └── main.py                   # FastAPI 엔드포인트
└── tests/
    └── test_*.py
```

## NLP 레이어 통합

본 프로젝트의 SQLite DB (`database/mini.db`) 는 **`../NLP/nlp_mvp/`** 모듈에서도
공용으로 사용됩니다. NLP/.env 의 `MINI_DB_PATH` 가 본 DB 를 가리킵니다.

- NLP 레이어는 `restaurants`, `meal_history`, `nutrition_info` 테이블을 읽고
- 보정 컬럼 (`sentiment_score`, `normalized_menu_id`) 을 기존 테이블에 추가합니다.

## 진행 상태

- [x] Phase 0 — 프로젝트 scaffolding
- [ ] **Subtopic 1 — 음식점 데이터 수집 (진행 중)**
- [ ] Subtopic 2 — 날씨 추천
- [ ] Subtopic 3 — 영양 분석
- [ ] Subtopic 4 — 팀 투표 + 통합 추천 엔진

## 코드 스타일

- 타입 힌트 필수
- docstring (Google 스타일)
- ruff 기본 규칙 준수
- 순수 함수 선호, side-effect 는 경계에서만

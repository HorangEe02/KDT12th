# Phase 0 — 사전 결정 기록

> 2026-04-07 에 확정된 Mini 프로젝트 구조 결정 사항.
> 이후 모든 GUIDE Subtopic 및 NLP 레이어 구현이 본 문서의 결정을 전제로 진행됩니다.

---

## 1. 프로젝트 루트 위치

**결정:** `Mini/lunch-optimizer/`

- 기존 `Mini/NLP/`, `Mini/GUIDE/`, `Mini/ChatBOT/` 와 **병렬 구조** 유지
- 상대 경로 관리가 단순해짐
- React 대시보드 (`Mini/lunch-optimizer-dashboard.jsx`) 는 루트에 그대로 둠

**대안 폐기:**
- ❌ Mini/ 직하위에 pipeline/ 등 펼치기 — NLP·GUIDE 와 혼재
- ❌ 드라이브 외부 경로 — 공유 관리 어려움

---

## 2. NLP 레이어와의 통합 방식

**결정:** **공용 DB (Option 6-a)**

- lunch-optimizer 가 생성한 SQLite (`lunch-optimizer/database/mini.db`) 를
  NLP 레이어가 **동일하게 참조**
- `NLP/.env` 의 `MINI_DB_PATH` 를 해당 경로로 지정
- `NLP/nlp_mvp/shared/db.py` 의 기존 구현 **그대로 재사용**
- NLP 는 `restaurants`, `meal_history`, `nutrition_info` 테이블에 **컬럼만 추가**
  (`sentiment_score`, `normalized_menu_id` 등)

**대안 폐기:**
- ❌ 별도 DB 분리 — 데이터 동기화 부담
- ❌ NLP 를 lunch-optimizer 내부로 흡수 — 기존 문서·링크 재작성 필요

### 통합 지점 미리보기

| 컬럼/테이블 | 생성자 | 사용자 |
|---|---|---|
| `restaurants` (기본) | lunch-optimizer Subtopic 1 | NLP A1 감성분석 (컬럼 추가) |
| `nutrition_info` | lunch-optimizer Subtopic 3 | NLP B1 메뉴 정규화 (표준 메뉴 소스) |
| `meal_history` | lunch-optimizer Subtopic 3 | NLP D5 NLG 리포트 |
| `sentiment_score` 외 | NLP A1 `ensure_schema()` | lunch-optimizer Subtopic 4 (통합 스코어링) |
| `normalized_menu_id` | NLP B1 `ensure_schema()` | lunch-optimizer 영양 조인 |
| `nutrition_reports` | NLP D5 | React 대시보드 AI 코멘트 카드 |

---

## 3. 환경 변수 관리

**결정:** **공용 `Mini/.env`** (상위 경로 단일 파일)

- 모든 API 키·좌표·DB 경로를 `Mini/.env` 1 파일에 기록
- `lunch-optimizer/config/settings.py` 가 **상위 경로 `.env` 를 자동 로드**
- `NLP/nlp_mvp/shared/db.py`·`logger.py`·`ollama_client.py` 도 동일하게
  상위 경로 `.env` 를 로드 (dotenv 기본 동작)
- 각 하위 프로젝트의 `.env` 는 **override 전용 (선택)**

**.env 로드 우선순위 (`lunch-optimizer/config/settings.py`):**
1. 프로세스 환경 변수 (최우선)
2. `Mini/.env` (공용)
3. `lunch-optimizer/.env` (local override, 존재 시)
4. 코드 내 기본값

### `.env` 예시 (실제 값 제외)

```bash
# Mini/.env.example 참고
KAKAO_REST_API_KEY=<from api/maps/api.pdf>
DATA_GO_KR_API_KEY_DECODED=<from api/weather/*.pdf>
OFFICE_LAT=37.5665
OFFICE_LNG=126.9780
SEARCH_RADIUS=500
DB_URL=sqlite:///./lunch-optimizer/database/mini.db
OLLAMA_MODEL=qwen2.5:7b-instruct
```

---

## 4. 실제 적용 결과 (Subtopic 1 Day 1 착수 완료)

### 4.1 생성된 scaffolding

```
Mini/
├── .env.example                              ← 🆕 공용 환경 변수 템플릿
├── lunch-optimizer/                          ← 🆕 Python 백엔드 루트
│   ├── CLAUDE.md
│   ├── PHASE0_DECISIONS.md                   ← 본 문서
│   ├── .gitignore
│   ├── requirements.txt
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py                       ← ✅ 구현 완료
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py                     ← ✅ 구현 완료
│   │   └── models.py                         ← ✅ Restaurant 모델
│   ├── pipeline/
│   │   ├── collectors/
│   │   │   └── restaurant_collector.py       ← ✅ 카카오 API 연동 완료
│   │   ├── transformers/
│   │   │   └── distance_scorer.py            ← ✅ 거리 점수 완료
│   │   ├── loaders/
│   │   │   └── db_loader.py                  ← ⬜ (Subtopic 1 Step 3 에서 작성)
│   │   └── scheduler.py                      ← ⬜ (Subtopic 1 Step 4)
│   ├── api/
│   │   └── main.py                           ← ⬜ (Subtopic 1 Step 6)
│   ├── tests/
│   │   ├── test_scorer.py                    ← ✅ 14 케이스
│   │   └── test_collector.py                 ← ✅ 5 케이스 (mocking)
│   └── logs/
└── NLP/                                       ← 기존 유지
    └── .env.example                           ← ✏️ MINI_DB_PATH 업데이트
```

### 4.2 완료된 Subtopic 1 항목

- [x] §2.3 프로젝트 구조 생성
- [x] §3.1 설정 모듈 (`config/settings.py`)
- [x] §3.2 음식점 수집기 (`restaurant_collector.py`)
- [x] 4.x 거리 점수 (`distance_scorer.py`) — 로직 선행 구현
- [x] §3.3 테스트 (`test_scorer.py`, `test_collector.py`)

### 4.3 아직 남은 Subtopic 1 작업

- [ ] §4 Step 2 데이터 정제 파이프라인 연결
- [ ] §5 Step 3 `db_loader.py` — 별도 로더 모듈 (현재는 collector 내부에 있음, 분리 선택)
- [ ] §6 Step 4 `scheduler.py` — APScheduler 일일 갱신
- [ ] §7 Step 5 실제 API 호출 end-to-end 검증 (실 키 필요)
- [ ] §8 Step 6 `api/main.py` — FastAPI 엔드포인트
- [ ] 체크리스트 완료 확인

---

## 5. 다음 단계 권장

1. **즉시:** `Mini/.env` 파일 생성 및 실제 키 입력 (`api/*.pdf` 참고)
2. **로컬 실행 검증:**
   ```bash
   cd Mini/lunch-optimizer
   python -m venv venv && source venv/bin/activate
   pip install -r requirements.txt
   pytest tests/test_scorer.py -v
   python -m config.settings  # 환경 변수 로드 확인
   ```
3. **실 API 호출:**
   ```bash
   python -m pipeline.collectors.restaurant_collector --radius 500
   ```
4. Subtopic 1 의 §4~§8 순차 진행 또는 Subtopic 2 착수

---

**문서 버전:** v1.0
**작성일:** 2026-04-07
**선행 문서:** `Mini/GUIDE/GUIDE_SUBTOPIC_1_RESTAURANT_COLLECTOR.md`
**관련 문서:** `Mini/NLP/README.md`

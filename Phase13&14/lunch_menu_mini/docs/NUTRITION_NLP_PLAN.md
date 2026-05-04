# 영양 리포트 자연어 입력 기능 — 사전 상세 구현 계획서

> **작성일**: 2026-04-29
> **목표**: 사용자가 "오늘 점심 김치찌개랑 공깃밥 먹었어" 같은 자연어를 입력하면, 시스템이 음식·양·시간·영양값을 자동 추출해 `meal_history` 에 저장하고 주간 리포트를 즉시 갱신.
> **예상 규모**: 백엔드 ~450 LOC + 프런트엔드 ~350 LOC + 테스트 ~200 LOC, 총 1.5–2일

---

## 1. 현재 영양 모듈 진단

### 1-1. 식품안전나라 API 사용 여부 — ✅ **사용 중**

| 위치 | 역할 |
|---|---|
| [lunch-optimizer/pipeline/collectors/nutrition_collector.py](lunch_menu_mini/lunch-optimizer/pipeline/collectors/nutrition_collector.py) | `NutritionCollector` 클래스 (line 86), 식약처 I2790 OpenAPI 호출 |
| [lunch-optimizer/config/settings.py](lunch_menu_mini/lunch-optimizer/config/settings.py) | `FOOD_SAFETY_API_KEY` 또는 `DATA_GO_KR_API_KEY_DECODED` 사용 |
| `nutrition_info` 테이블 | API 결과 캐싱 (food_name, calories, carbs, protein, fat) |
| `pipeline/transformers/nutrition_scorer.py` | `MenuNutritionMapper` (퍼지 매칭 ≥ 0.80), `MealTracker` |

### 1-2. 기존 영양 관련 엔드포인트
```
POST /api/nutrition/meal              # 단일 식사 기록 (사용자 입력)
GET  /api/nutrition/weekly            # 주간 합산
GET  /api/nutrition/diagnosis         # 영양 진단 (DEFICIENT/IDEAL/EXCESSIVE)
GET  /api/nutrition/trend             # 트렌드
GET  /api/nutrition/restaurant/{id}   # 식당 메뉴 영양값
```

### 1-3. 활용 가능한 NLP 자산 — 🟢 **풍부**

| 모듈 | 위치 | 활용 |
|---|---|---|
| **B1 메뉴 정규화** | [NLP/nlp_mvp/menu_normalizer/](lunch_menu_mini/NLP/nlp_mvp/menu_normalizer/) | 3-stage(rules → Levenshtein → S-BERT) — "공기밥" → "쌀밥" 매핑 |
| **D5 NLG 리포트** | [NLP/nlp_mvp/nlg_report/](lunch_menu_mini/NLP/nlp_mvp/nlg_report/) | 주간 리포트 자연어 코멘트 생성 (Gemini/Ollama) |
| **D3 RAG 챗봇** | [NLP/nlp_mvp/rag_chatbot/](lunch_menu_mini/NLP/nlp_mvp/rag_chatbot/) | Gemini Tool Calling 패턴 기 보유 |
| **NutritionInfo DB** | mini.db | 표준 음식 영양 캐시 |

### 1-4. 현재 한계 (개선 대상)

| # | 한계 | 사용자 영향 |
|:-:|---|---|
| 1 | `/api/nutrition/meal` POST에 음식명·칼로리·매크로 모두 직접 입력해야 함 | 매번 calorie 검색 필요, UX 나쁨 |
| 2 | 여러 음식을 한 번에 기록 불가 (1회 1메뉴) | 식사당 여러 호출 |
| 3 | "공기밥 1공기" 같은 단위 표현 미지원 | 양 환산을 사용자가 직접 |
| 4 | 음식명 오타·구어체 미허용 (정규화 미적용) | "라면" vs "라멘" 매칭 어려움 |
| 5 | 식약처 DB에 없는 음식 처리 부재 | 사용자가 빈 값 입력 |

→ **자연어 입력 1줄로 전부 해결.**

---

## 2. 핵심 아키텍처 설계

### 2-1. 데이터 흐름

```
사용자 입력
"오늘 점심에 김치찌개랑 공기밥 한 그릇,
 그리고 야쿠르트 1개 먹었어. 12시쯤 먹음"
        ↓
┌─────────────────────────────────────────┐
│ Step 1: LLM Tool Calling (Gemini)       │
│   - JSON schema 강제 (구조화 응답)      │
│   - 출력: [{food, qty, unit, time}, …]  │
└─────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────┐
│ Step 2: B1 menu_normalizer              │
│   - "공기밥" → "쌀밥" (synonym)         │
│   - "라멘" → "라면" (Levenshtein)       │
│   - 동음이의어는 컨텍스트 유지          │
└─────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────┐
│ Step 3: NutritionInfo DB 조회           │
│   - 표준 100g 영양값 가져옴            │
│   - 누락 시: 식약처 API 즉시 fetch      │
│   - 그래도 없으면: LLM 추정 (낮은 신뢰) │
└─────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────┐
│ Step 4: 양(qty/unit) → 그램 환산        │
│   - "1공기" = 210g, "1잔" = 250ml       │
│   - 영양값 = 100g당 × (실제그램 / 100)  │
└─────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────┐
│ Step 5: 사용자 미리보기 + 확정          │
│   - 추출된 음식 리스트 + 영양값 표시    │
│   - 항목별 수정/삭제/추가 가능          │
│   - "확정" 클릭 시 meal_history 저장    │
└─────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────┐
│ Step 6: 주간 리포트 즉시 갱신            │
│   - TanStack Query invalidate            │
│   - D5 NLG 코멘트 자동 재생성           │
└─────────────────────────────────────────┘
```

### 2-2. LLM Tool Calling JSON Schema (Gemini Function Calling)

```python
PARSE_FOOD_TOOL = {
    "name": "extract_meal_items",
    "description": "사용자의 자연어 식사 메시지에서 음식 항목을 추출",
    "parameters": {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "food": {"type": "string", "description": "음식 이름 (한국어)"},
                        "qty": {"type": "number", "description": "수량, 명시 없으면 1"},
                        "unit": {
                            "type": "string",
                            "enum": ["인분", "그릇", "공기", "잔", "개", "조각", "g", "ml"],
                        },
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    },
                    "required": ["food", "qty", "unit"],
                },
            },
            "meal_time": {
                "type": "string",
                "description": "식사 시간 (HH:MM 또는 'breakfast'/'lunch'/'dinner'/'snack')",
            },
            "raw_input": {"type": "string", "description": "원문"},
        },
        "required": ["items"],
    },
}
```

### 2-3. 단위 환산 표준값

| 단위 | 그램 환산 | 비고 |
|---|---:|---|
| 1 인분 / 그릇 (밥류) | 210 | 공기밥 표준 |
| 1 인분 (국/찌개) | 350 | 보통 1인분 |
| 1 인분 (면류) | 500 | 라면 1봉지 |
| 1 잔 (음료) | 250 | ml |
| 1 개 (사과류) | 200 | 중간 크기 |
| 1 조각 (피자) | 130 | 한 조각 |
| g / ml | 그대로 | |

상수는 [config/nutrition_units.py](lunch_menu_mini/lunch-optimizer/config/nutrition_units.py) 신규 파일에 정의.

---

## 3. 옵션 비교 및 권장안

### 옵션 A — Pure NLP (Food NER + 정규식)
- 외부 의존: 0
- 정확도: 70% (단위/시간 추출 약함)
- 학습 가치: NER 모델 사용
- ❌ Food NER 모델 가중치 부재 (현재 폴백만 동작)

### 옵션 B — Pure LLM (Gemini Tool Calling)
- 외부 의존: Gemini API
- 정확도: 90%+
- 학습 가치: LLM Function Calling
- ✅ 이미 NLP 레이어에 Gemini 통합됨
- ⚠ 식약처 DB 매칭은 별도 필요

### ⭐ 옵션 C — **하이브리드 (권장)**
- LLM 추출 → B1 메뉴 정규화 → DB/식약처 조회 → 양 환산
- 외부 의존: Gemini (또는 Ollama 폴백)
- 정확도: 95%+ (각 단계가 약점 보완)
- 학습 가치: LLM Tool Calling + 자체 NLP 정규화 + 식약처 API 통합 모두 활용
- ✅ 기존 자산 100% 활용

---

## 4. 구현 단계 (4 Phase, 약 12–15시간)

### Phase A — 백엔드 코어 (4–5시간)

#### A-1. 자연어 파싱 모듈 신규
- `lunch-optimizer/nutrition_parser/__init__.py` 신규
- `parse_natural_language(text: str) -> ParsedMeal`
  - LLM Tool Calling (`Gemini`/`Ollama`) — 옵셔널 의존
  - 응답 검증 + Pydantic 모델 변환

#### A-2. 음식 → 영양값 매핑
- `nutrition_parser/resolver.py`
- `resolve_nutrition(item: ParsedItem) -> NutritionFact`
  - B1 menu_normalizer 호출 (NLP_API:8001 내부)
  - nutrition_info DB 조회
  - 미스 시 식약처 API on-demand fetch (`NutritionCollector` 재사용)
  - 마지막 폴백: LLM 추정 (`confidence < 0.5` 마킹)

#### A-3. 단위 환산 유틸
- `config/nutrition_units.py` — 표준 환산표
- `nutrition_parser/units.py` — `convert_to_grams(qty, unit, food_category)`

#### A-4. 신규 엔드포인트 3개

```python
POST /api/nutrition/parse
Body: {"text": "..."}
Resp: {
  "items": [{food, qty, unit, grams, calories, protein, ...}],
  "total": {calories, protein, carbs, fat},
  "meal_time": "12:30",
  "warnings": ["..."]   # 매칭 실패, 낮은 신뢰도 등
}

POST /api/nutrition/log-from-text
Body: {"text": "...", "user_id": "..."}
→ parse + 즉시 meal_history 저장 (단일 호출 편의)

POST /api/nutrition/log-confirmed
Body: {"items": [{...수정된 항목...}], "user_id": "...", "eaten_at": "..."}
→ 사용자가 미리보기에서 수정 후 확정 저장
```

#### A-5. 권한
- 모두 `Depends(get_current_user)` 적용 — 본인 user_id 만 기록 가능
- admin은 다른 user 대신 기록 가능 (admin override)

---

### Phase B — NLG 리포트 통합 (2–3시간)

#### B-1. 기존 D5 generator 재활용
- 자연어 입력으로 새 식사 추가되면 → 주간 리포트 캐시 무효화
- `nutrition_reports` 테이블의 해당 주차 row 삭제 → 다음 호출 시 재생성

#### B-2. 즉시 피드백 코멘트 (선택)
- 신규 엔드포인트: `POST /api/nutrition/instant-comment`
- 한 끼 직후 짧은 코멘트 ("오늘 단백질이 부족해요. 저녁엔 닭가슴살 어떠세요?")
- D5 generator 패턴 활용, 짧은 프롬프트

---

### Phase C — 프런트엔드 (3–4시간)

#### C-1. 신규 컴포넌트 구조
```
src/components/nutrition/
├── NLInputCard.tsx          # 자연어 입력 박스 + 음성 입력 (옵션)
├── ParsePreview.tsx          # 추출 결과 카드 (편집 가능)
├── ParsedItemRow.tsx         # 항목 1개 (음식명 / qty / unit / kcal / 매크로)
├── ConfirmActions.tsx        # [확정 저장] [다시 입력] [취소]
└── 기존 (AICommentCard, StatCard, MacroDonut, CalorieTrend, DailyBreakdown)
```

#### C-2. UX 흐름
```
/nutrition 페이지 상단 신규:
┌─────────────────────────────────────────┐
│ 🍽 오늘 뭐 먹었나요?                      │
│ ┌─────────────────────────────────────┐ │
│ │ 점심에 김치찌개랑 공깃밥…           │ │
│ └─────────────────────────────────────┘ │
│                       [기록하기 →]      │
└─────────────────────────────────────────┘

기록하기 클릭 시:
   → POST /api/nutrition/parse
   → ParsePreview 카드 표시
       음식 1 │ 김치찌개 350g  │ 281 kcal  [✏️] [🗑️]
       음식 2 │ 쌀밥 210g      │ 280 kcal  [✏️] [🗑️]
       총합   │              │ 561 kcal
   → [확정 저장] 시 POST /api/nutrition/log-confirmed
   → 주간 리포트 자동 갱신 (queryClient.invalidateQueries)
```

#### C-3. 인증 연동
- `getCurrentUser()` 에서 user_id 추출
- 게스트는 데모 모드 (저장은 로컬 only)

---

### Phase D — 테스트 + 보안 + 배포 (2–3시간)

#### D-1. 백엔드 pytest
- `test_nutrition_parser.py`
  - LLM 응답 파싱 (mock)
  - menu_normalizer 통합
  - 단위 환산 (1공기, 1잔, …)
  - DB miss → 식약처 fetch 재시도
- `test_nutrition_log_endpoints.py`
  - POST /parse 정상 응답
  - POST /log-confirmed 시 meal_history insert + 주간 리포트 invalidate
  - 다른 user_id 기록 차단 (403)

#### D-2. 보안 점검
- LLM 입력 길이 제한 (≤ 500자)
- Rate limit (slowapi) — 1분 5회/사용자
- LLM 응답에 PII 누출 가드 (system prompt에 명시)
- 식약처 API 키 백엔드 only (이미 적용)

#### D-3. 프런트 빌드 + 재배포
- `deploy_demo.sh` 재실행
- 모바일 검증 (반응형)
- E2E: 자연어 입력 → 미리보기 → 저장 → 주간 리포트 갱신

---

## 5. 데이터베이스 영향

### 5-1. 변경 없는 테이블
- `nutrition_info`: 그대로 (식약처 캐시)
- `meal_history`: 그대로 (이미 user_id, menu_name, calories, carbs, protein, fat 보유)

### 5-2. 새 컬럼 (선택)
- `meal_history.source`: enum("manual", "nl_input", "auto") — 입력 경로 추적
- `meal_history.confidence`: float — LLM 추정 신뢰도

→ 신규 마이그레이션: `scripts/migrate_meal_source.py` (idempotent ALTER TABLE)

### 5-3. 기존 데이터
- archive 후 신규 데이터로 통합 (사용자가 admin 콘솔에서 일괄 정리 가능)

---

## 6. 위험 매트릭스

| # | 위험 | 가능성 | 영향 | 완화 |
|:-:|---|:-:|:-:|---|
| 1 | LLM 응답 JSON 파싱 실패 | 🟡 | 🟡 | Pydantic 검증 + 재시도 1회 + 정규식 폴백 |
| 2 | 식약처 API 무응답/quota 초과 | 🟡 | 🟡 | DB 캐시 우선, 응답 못 받으면 LLM 추정 표시 |
| 3 | menu_normalizer 잘못된 매칭 | 🟢 | 🟡 | confidence 점수 노출, 사용자가 미리보기에서 수정 |
| 4 | 단위 환산 오차 (예: "큰 그릇") | 🟡 | 🟢 | 디폴트 + 사용자 수정 가능 |
| 5 | 사용자가 잘못된 음식 저장 | 🟢 | 🟢 | 24h 내 삭제 가능 (POST /api/nutrition/meal/{id}/delete) |
| 6 | LLM 비용 폭증 (남용) | 🟡 | 🟡 | rate limit 1분 5회/사용자, 길이 500자 제한 |
| 7 | 비영어/오타 입력 | 🟡 | 🟢 | 한국어 우선 학습된 Gemini-2.5-pro 사용 |

---

## 7. 단계별 산출물 체크리스트

### Phase A
- [ ] `lunch-optimizer/nutrition_parser/__init__.py`, `resolver.py`, `units.py`
- [ ] `config/nutrition_units.py`
- [ ] `api/routers/nutrition_nl.py` (3 신규 엔드포인트)
- [ ] `main.py` 라우터 등록

### Phase B
- [ ] D5 generator 캐시 invalidation
- [ ] `/api/nutrition/instant-comment` (옵션)

### Phase C
- [ ] `NLInputCard.tsx`, `ParsePreview.tsx`, `ParsedItemRow.tsx`
- [ ] `nutrition/page.tsx` 상단에 NLInputCard 통합
- [ ] `lib/queries.ts` 에 `useParseNutrition`, `useLogConfirmed` 추가
- [ ] TanStack Query invalidate 시 주간 리포트 자동 갱신

### Phase D
- [ ] pytest test_nutrition_parser.py, test_nutrition_log_endpoints.py
- [ ] rate limit 적용
- [ ] 정적 빌드 + Firebase 재배포
- [ ] 모바일 E2E 검증

---

## 8. 사용자 결정이 필요한 지점

1. **LLM 제공자**: Gemini (현재 디폴트, Tool Calling 우수) vs Ollama (로컬, 비용 0)?
   - 권장: Gemini 디폴트 + Ollama 폴백
2. **저장 시점**: 1단계 자동 저장(빠름) vs 2단계 미리보기 후 확정(정확)?
   - 권장: 2단계 (미리보기) — UX 안전
3. **음성 입력**: Web Speech API 추가? (선택, +1h)
4. **즉시 코멘트**: 한 끼 직후 LLM 코멘트 표시? (Phase B-2, +2h)
5. **데이터 정리**: 기존 manual 입력 식사 보존 vs 마이그레이션?
   - 권장: 보존 + `source="manual"` 마킹

---

## 9. 일정 요약

| Phase | 시간 | 핵심 산출물 |
|---|:-:|---|
| A — 백엔드 코어 | 4–5h | parse·resolver·units·3 엔드포인트 |
| B — NLG 통합 | 2–3h | 캐시 invalidation·instant comment(옵션) |
| C — 프런트 | 3–4h | NLInputCard·ParsePreview·통합 |
| D — 테스트+배포 | 2–3h | pytest·재배포·E2E |
| **총** | **12–15h (1.5–2일)** | |

본 계획서 승인 시 즉시 Phase A부터 자율 진행 (auto mode).

---

## 10. 핵심 인사이트 요약

- ✅ **식약처 API 이미 통합됨** → 데이터 소스 변경 불필요
- ✅ **B1/D5 NLP 자산 100% 재활용 가능** → 신규 모델 학습 불필요
- ✅ **DB 스키마(MealHistory) 그대로 사용 가능** → 마이그레이션 부담 거의 없음
- ✅ **하이브리드(LLM Tool Calling + 정규화 + DB 매칭)가 최적** — 정확도·학습 가치·비용 균형
- 🟢 **사용자 편의성 대폭 개선** — 1줄 입력으로 여러 음식 + 양 + 시간 + 영양값 자동 처리

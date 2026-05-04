# 영양 자연어 파서 분리 정확도 + UI UX 개선 — 사전 상세 구현 계획

> **작성일**: 2026-05-01
> **트리거**: 사용자가 "갈비\n공기밥" 입력 → "갈비 공기밥" 단일 항목으로 통합되어 unverified 매칭 실패. 수동 +/- 보정 UI 부재.
> **예상 규모**: 백엔드 ~120 LOC + 프런트 ~180 LOC + 사전 14개 메뉴 추가, 총 3–4시간

---

## 1. 진단된 4가지 근본 이슈

| # | 이슈 | 증상 | 근본 원인 |
|:-:|---|---|---|
| 1 | 공백·줄바꿈 미분리 | "갈비 공기밥" → 1항목 통합 | `_CONNECTOR_RE` 가 공백/줄바꿈 미인식 |
| 2 | 사전 매칭 휴리스틱 회피 | 분리 후에도 통합 유지 | `_split_parts_by_dictionary` 임계값(0.7) 도달 못함 — synonym/표준 메뉴 사전이 부족 |
| 3 | 표준 메뉴 사전 부족 | "공기밥" → "국밥"(0.5) Levenshtein 오매칭 | `_synthetic_menus.py` 에 한식 밥류·갈비 누락 |
| 4 | UI +/- 버튼 부재 | 분석 실패 시 사용자가 직접 보정 불가 | `MealEntryPanel.tsx` 가 분석 결과를 read-only 처럼 표시 |

→ 단일 패치가 아닌 **층위별 통합 개선** 필요.

---

## 2. 브레인스토밍 — 옵션 비교

### 2-1. 자연어 분리 정확도 (Issue 1, 2)

| 접근 | 정확도 | 위험 | 학습 가치 | 평가 |
|---|:-:|:-:|:-:|:-:|
| **A. 줄바꿈/세미콜론만 connector 추가** | 🟢 안전 | 🟢 낮음 | 🟢 | 🥇 즉시 적용 |
| **B. 공백+사전 매칭 휴리스틱** | 🟡 70-80% | 🟡 false-split 위험 | 🟢 | 🥇 임계값 튜닝 시 효과 큼 |
| **C. LLM Tool Calling fallback** | 🟢 95% | 🟡 외부 비용 | 🟢 | 🥈 향후 |
| **D. 음절 단위 BPE 토크나이저** | 🟡 | 🔴 학습 데이터 필요 | 🟡 | ❌ 과잉 |

**선택**: A + B 조합 — 명시적 구분(개행/콤마/세미콜론)은 강제 분리, 공백은 사전 매칭 시에만.

### 2-2. 사전 확장 (Issue 3)

| 접근 | 커버리지 | 유지보수 |
|---|:-:|---|
| **A. `_synthetic_menus.py` 수동 추가** | 🟡 핵심 30종 | 🟢 명시적 |
| **B. 식약처 시드 후 표준명을 자동 추가** | 🟢 | 🟡 동기화 필요 |
| **C. synonym_dict 별칭만 추가** | 🟡 | 🟢 |

**선택**: A + C — 자주 쓰는 한식 기본 메뉴 14개를 표준으로 추가, synonym으로 별칭 보강.

### 2-3. UI UX 설계 (Issue 4)

| 디자인 | UX | 개발 비용 |
|---|---|:-:|
| **A. 인라인 +/- 버튼 (행 우측)** | 🟢 직관적 | 🟢 낮음 |
| **B. 별도 "수동 추가" 모달** | 🟡 클릭 1회 추가 | 🟡 |
| **C. 드래그 앤 드롭 + 자동완성** | 🟢 멋짐 | 🔴 |

**선택**: A — 행 우측 🗑️ + 하단 ➕ "음식 추가" 버튼.

### 2-4. 신뢰도 표시 정책

- 항목별 confidence 뱃지 (`unverified`, `0.55`)
- 영양값 missing 시 placeholder + 직접 입력 가능한 input
- 저장 시 항목당 `source: user_adjusted` 마킹 (이미 구현됨)

---

## 3. 통합 권장 설계

### 3-1. 파서 분리 알고리즘 (3-stage)

```
Stage 1: connector 분리 (강제)
  _CONNECTOR_RE = (\n|;|랑|하고|그리고|및|,|/|+|와|과)
  → "갈비\n공기밥" → ["갈비", "공기밥"]

Stage 2: 공백 사전 매칭 휴리스틱
  for part in parts:
      tokens = part.split()
      if len(tokens) <= 1: keep
      elif all(normalizer.normalize(t).confidence >= 0.7): split
      else: keep as one item

Stage 3: noise stopword 제거
  _strip_noise_tokens (이미 구현됨)
```

### 3-2. 표준 메뉴 사전 확장 (14종)

밥류·갈비·기본 한식 핵심:
- 쌀밥, 잡곡밥, 공기밥, 현미밥
- 갈비, 갈비찜, 양념갈비, 삼겹살구이
- 닭갈비, 부대찌개_라면사리(별칭)
- 컵라면, 김치말이국수, 만두국, 떡만두국

### 3-3. UI 변경 (`MealEntryPanel.tsx`)

```
[분석 결과 카드]
  ┌─ 갈비          🗑️
  │   QTY: 1.0 | KCAL: __ | P: __ | C: __ | F: __
  ├─ 쌀밥          🗑️
  │   QTY: 1.0 | KCAL: __ | P: __ | C: __ | F: __
  └─ ➕ 음식 추가
[🔍 다시 분석] [💾 저장]
```

핵심 기능:
- 행 우측 🗑️ — `setAnalysis` 로 해당 인덱스 항목 삭제
- 하단 ➕ — 새 항목 (raw_name="", quantity=1, unit="serving", source="user_added") 추가
- 빈 항목은 저장 시 자동 제외

---

## 4. 구현 단계 (총 ~4시간)

### Phase A — 백엔드 분리 알고리즘 (1h)
- [A1] `_CONNECTOR_RE` 에 `\n` `;` 추가 (✅ 적용 완료)
- [A2] `_split_parts_by_dictionary` 함수 추가 (✅ 적용 완료)
- [A3] 검증: 회귀 0건 + 신규 케이스 통과
- [A4] 단위 테스트 추가 (test_parser.py): "갈비 공기밥", "갈비\n공기밥", "치킨 마요" 등

### Phase B — 표준 메뉴 사전 확장 (30m)
- [B1] `_synthetic_menus.py` 14종 추가 (밥/갈비)
- [B2] `synonym_dict.json` 별칭 추가 (✅ 일부 완료)
- [B3] nlp-api restart → normalizer 재로드
- [B4] live test: 기본 한식 입력 100% 매칭

### Phase C — 프런트 +/- 버튼 (1h)
- [C1] `MealEntryPanel.tsx` 항목 행에 `<button onClick={() => removeItem(idx)}>🗑️</button>`
- [C2] 항목 리스트 하단 `<button onClick={addItem}>➕ 음식 추가</button>`
- [C3] `addItem`: 빈 항목 push (`raw_name=""`, qty=1, unit="serving", needs_review=true)
- [C4] `removeItem`: filter index out
- [C5] 빈 raw_name 저장 가드: 저장 시 `items.filter(it => it.raw_name.trim())`

### Phase D — UX 폴리싱 (30m)
- [D1] placeholder 가이드 갱신: "예: 갈비, 공기밥 (또는 줄바꿈으로 구분)"
- [D2] 항목 추가 버튼 옆 작은 도움말 ("자연어 분석으로 못 찾은 음식을 직접 추가하세요")
- [D3] 빈 항목 행에 자동 focus (UX)

### Phase E — 검증 + 배포 (30m)
- [E1] nutrition_parser pytest 회귀 (2/2 → 5/5 추가)
- [E2] 정적 빌드 + Firebase 재배포
- [E3] E2E: 화면에서 "갈비 공기밥" 분리 확인 + 수동 항목 추가 동작

---

## 5. 테스트 케이스 매트릭스

| 입력 | 기대 결과 | 분류 |
|---|---|---|
| `갈비, 공기밥` | 2개 | comma split ✓ |
| `갈비\n공기밥` | 2개 | 줄바꿈 split (NEW) |
| `갈비; 공기밥` | 2개 | 세미콜론 split (NEW) |
| `갈비 공기밥` | 2개 | 공백+사전 휴리스틱 (NEW) |
| `김치 찌개` | 1개 ("김치찌개") | normalizer 통합 ✓ |
| `치킨 마요` | 1개 ("치킨 마요") | 사전 미매칭 → 통합 유지 ✓ |
| `갈비 공기밥 맛도리` | 2개 (맛도리 stopword) | stopword + split |
| `오늘 점심 갈비랑 공기밥 4점` | 2개, type=lunch, sat=4 | 메타 + split |

---

## 6. 위험 및 완화

| 위험 | 영향 | 완화 |
|---|:-:|---|
| 공백 분리로 false-split | 🟡 | 임계값 0.7 + matched_name 필수 검증 + 토큰 모두 사전 매칭 시에만 분리 |
| 사전 추가로 기존 매칭 변동 | 🟢 | normalizer pytest로 사전 회귀 검증 |
| 빈 항목 저장 | 🟡 | 클라이언트 필터 + 백엔드 raw_name min-length 검증 |
| 사용자 추가 항목 영양값 없음 | 🟡 | 직접 입력 가능 placeholder, save 시 user_adjusted 마킹 |

---

## 7. 산출물 체크리스트

### 백엔드
- [x] `parser.py` `_CONNECTOR_RE` 줄바꿈/세미콜론 추가
- [x] `parser.py` `_split_parts_by_dictionary` 함수
- [ ] `_synthetic_menus.py` 14종 표준 메뉴 추가
- [x] `synonym_dict.json` 별칭 추가
- [ ] `tests/test_parser.py` 신규 케이스 5개

### 프런트
- [ ] `MealEntryPanel.tsx` 항목별 🗑️ 삭제 버튼
- [ ] `MealEntryPanel.tsx` ➕ "음식 추가" 버튼
- [ ] placeholder 가이드 갱신
- [ ] 빈 항목 저장 가드

### 인프라
- [ ] nlp-api restart (사전 reload)
- [ ] dashboard-web 정적 재빌드 + Firebase 배포
- [ ] E2E live 검증

---

## 8. 즉시 실행 (auto mode)

본 계획서 작성 후:
1. Phase B (사전 14종 추가) → restart
2. 분리 휴리스틱 회귀 검증
3. Phase C (UI +/- 버튼)
4. 빌드 + 재배포
5. E2E

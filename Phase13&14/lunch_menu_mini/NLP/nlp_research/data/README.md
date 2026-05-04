# `nlp_research/data/`

## seed/
50건 hand-written 시드 데이터셋 (Phase 6 dry-run 용).

| 파일 | 모듈 | 행 수 | 포맷 |
|---|---|---|---|
| `absa_seed_50.jsonl` | A2 ABSA | 50 | `{text, aspects: [{aspect, sentiment}]}` |
| `food_ner_seed_50.jsonl` | B2 Food NER | 50 | `{tokens: [str], tags: [BIO]}` |

## splits/
`train.py` 가 `stratified_split()` 으로 자동 생성하는 train/val/test JSONL.
`.gitignore` 에 포함되어 커밋되지 않는다.

## raw/
원시 라벨링 export (Label Studio JSON 등). gitignored.

---

## 추가 데이터 준비 가이드

### A2 ABSA (목표: 1,000+ triple)

1. Phase 5 `reviews` 테이블에서 confidence가 낮은(<0.6) 리뷰를 export
2. Label Studio config: 5 aspect × 3 sentiment 라디오 버튼
3. JSON export → `convert_labelstudio.py` (TODO) 로 JSONL 변환
4. 각 (text, aspect) 조합당 최소 50 샘플 보장 (stratified)

### B2 Food NER (목표: 1,000+ 문장)

1. 음식점 메뉴 description / 리뷰 corpus 수집
2. Label Studio NER tagging interface (13 BIO 태그)
3. JSON → CoNLL → JSONL 변환
4. ALLERGEN 태그는 안전 critical → 별도 검수

### E1 Embedding CF

별도 라벨링 불필요. Phase 5 `meal_history` 테이블에서 자동으로 사용자별
profile text 를 빌드한다. 데이터 없을 시 `MealHistorySource.synthetic()` 사용.

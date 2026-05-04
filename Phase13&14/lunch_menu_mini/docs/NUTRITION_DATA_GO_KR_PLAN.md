# 영양 정보 수집기 — 공공데이터포털 우선 전환 계획

> **작성일**: 2026-05-01
> **결정**: 식약처 식품안전나라 → 공공데이터포털(`apis.data.go.kr`) 우선
> **유지**: 식품안전나라(`openapi.foodsafetykorea.go.kr`)는 폴백으로 보존

---

## 1. 현황

### 1-1. 사용 중인 API (변경 전)
- `openapi.foodsafetykorea.go.kr/api/I2790` (식품안전나라)
- 단일 키 (인코딩/디코딩 구분 없음, 16자 영숫자)
- URL path 에 키 직접 삽입: `/{api_key}/I2790/json/...`

### 1-2. .env 보유 키
| 변수 | 상태 |
|---|:-:|
| `FOOD_SAFETY_API_KEY` | ✅ 채워짐 (식품안전나라) |
| `DATA_GO_KR_API_KEY_ENCODED` | ✅ 채워짐 (공공데이터포털 Encoding) |
| `DATA_GO_KR_API_KEY_DECODED` | ✅ 채워짐 (공공데이터포털 Decoding) |

→ 양쪽 모두 보유. **dual-provider** 구조가 합리적.

---

## 2. 공공데이터포털 식약처 영양 API 후보

`apis.data.go.kr` 의 식약처 영양 관련 API 후보:

| ID | 명칭 | 엔드포인트 (추정) |
|---|---|---|
| 15050015 | 식품영양성분 데이터베이스 | `apis.data.go.kr/1471000/FoodNtrCpntDbInfo01/getFoodNtrCpntDbInq01` |
| 15125405 | 식품영양성분DB 변경분 | `apis.data.go.kr/1471057/FoodNtritionData/...` |
| 15030118 | 통합 식품영양정보 | (사용 비추) |

→ 정확한 API ID/엔드포인트는 사용자가 활용 신청한 것으로 결정.
→ **기본값을 가장 표준적인 `1471000/FoodNtrCpntDbInfo01/getFoodNtrCpntDbInq01` 으로 두되 환경변수로 override 가능하게** 구현.

### 일반적인 공공데이터포털 호출 규약
```
GET https://apis.data.go.kr/{소관기관코드}/{서비스ID}/{오퍼레이션명}
    ?serviceKey={DECODED_KEY}     ← requests params로 자동 인코딩됨
    &pageNo=1
    &numOfRows=20
    &type=json                    ← 일부 API는 dataType 또는 _type
    &FOOD_NM_KR={음식명}          ← 필드명은 API마다 다름
```

---

## 3. 변경 설계

### 3-1. dual-provider 라우팅 (환경변수)
```bash
# .env (신규)
NUTRITION_PROVIDER=data_go_kr      # 'data_go_kr' (기본) | 'food_safety' | 'auto'(폴백)
DATA_GO_KR_NUTRITION_URL=https://apis.data.go.kr/1471000/FoodNtrCpntDbInfo01/getFoodNtrCpntDbInq01
DATA_GO_KR_NUTRITION_NAME_PARAM=FOOD_NM_KR   # 검색 파라미터 키 (API에 따라 변경)
```

### 3-2. 새 collector 클래스 — `DataGoKrNutritionCollector`

`lunch-optimizer/pipeline/collectors/data_go_kr_nutrition_collector.py` (신규):
- 입력: 음식명
- 호출: `requests.get(URL, params={"serviceKey": DECODED_KEY, "pageNo": 1, "numOfRows": 20, "type": "json", PARAM_NAME: name})`
- 응답: JSON 우선 시도 → XML 폴백 (xmltodict 또는 정규식)
- 정규화: 식품안전나라 collector와 동일한 dict 형태 (food_name, calories, carbs, protein, fat, sugar, sodium, serving_size 등)로 매핑

### 3-3. 통합 collector — `nutrition_collector.py` 라우팅 확장
기존 `NutritionCollector` 에 메서드:
```python
def search_by_name(name) -> list[dict]:
    if self.provider == "data_go_kr":
        try:
            return self._dgk.search_by_name(name)
        except Exception:
            if not self.fallback_enabled: raise
    # food_safety 폴백
    return self._fs_search_by_name(name)
```

### 3-4. 시드 스크립트
- 기존 `seed_nutrition_info.py` 가 자동으로 새 라우팅 사용 (provider 파라미터로 라우팅)
- 별도 스크립트 추가 없음

---

## 4. 응답 스키마 정규화

| 정규화 dict 필드 | 식품안전나라 (현재) | 공공데이터포털 (예상) |
|---|---|---|
| `food_code` | `FOOD_CD` | `FOOD_CD` 또는 `NUM` |
| `food_name` | `DESC_KOR` | `FOOD_NM_KR` |
| `serving_size` | `SERVING_SIZE` | `SERVING_SIZE` 또는 100.0 (고정) |
| `calories` | `NUTR_CONT1` | `AMT_NUM1` 또는 `NUTR_CONT1` |
| `carbs` | `NUTR_CONT2` | `NUTR_CONT2` |
| `protein` | `NUTR_CONT3` | `NUTR_CONT3` |
| `fat` | `NUTR_CONT4` | `NUTR_CONT4` |
| `sugar` | `NUTR_CONT5` | `NUTR_CONT5` |
| `sodium` | `NUTR_CONT6` | `NUTR_CONT6` |

→ 필드명이 API마다 미묘하게 다르므로 **다중 키 fallback** 사용:
```python
def _pick(row, keys):
    for k in keys:
        if k in row and row[k]:
            return row[k]
    return None

calories = _pick(row, ("AMT_NUM1", "NUTR_CONT1", "ENERGY", "ENERC"))
```

---

## 5. 구현 단계 (총 ~2시간)

### Phase A — 백엔드 collector (1h)
- [A1] `DataGoKrNutritionCollector` 클래스 신규
- [A2] `NutritionCollector` 에 provider 라우팅 통합
- [A3] settings.py 에 provider 설정 + URL/파라미터 환경변수 추가

### Phase B — .env + Docker compose (15m)
- [B1] `.env.example` 에 `NUTRITION_PROVIDER`, `DATA_GO_KR_NUTRITION_URL`, `DATA_GO_KR_NUTRITION_NAME_PARAM` 추가
- [B2] `docker-compose.yml` 의 lunch-api environment 에 변수 전달

### Phase C — 시드 검증 (30m)
- [C1] 기존 `seed_nutrition_info.py` 실행 → data.go.kr 응답 정상 시 nutrition_info 갱신
- [C2] 응답 실패 시 사용자에게 정확한 API ID/엔드포인트 확인 요청

### Phase D — 회귀 테스트 (15m)
- [D1] `test_nutrition_collector.py` 가 통과해야 함 (식품안전나라 폴백 보존 검증)
- [D2] /api/nutrition/meal-natural/preview 영양값 매칭 정상 동작

---

## 6. 위험 매트릭스

| 위험 | 영향 | 완화 |
|---|:-:|---|
| 정확한 API 엔드포인트/필드명 미상 | 🟡 중 | 환경변수로 endpoint + name_param 주입 가능. 응답 schema는 다중 key fallback |
| 일일 트래픽 한도 초과 | 🟡 중 | data.go.kr 무료 1만/일, 식품안전나라 폴백 자동 |
| XML/JSON 응답 형식 차이 | 🟢 낮 | `_type=json` 우선, XML 들어오면 JSON 시도 |
| 공공데이터포털 인증 실패 | 🟢 낮 | food_safety 자동 폴백 |

---

## 7. 사용자 결정 필요한 지점

1. **활용 신청한 정확한 API ID** — 1471000/FoodNtrCpntDbInfo01 인지 1471057/FoodNtritionData 인지?
   → 명시 안 하면 가장 일반적인 첫 번째로 가정하고 진행
2. **endpoint URL이 다르면** `.env` 의 `DATA_GO_KR_NUTRITION_URL` 만 변경하면 됨 (재배포 불필요)
3. **응답 필드명이 API와 다르면** collector의 `_FIELD_KEYS` 매핑만 추가

---

## 8. 즉시 진행 (auto mode)

- 합리적 기본값(`1471000/FoodNtrCpntDbInfo01/getFoodNtrCpntDbInq01`)으로 구현
- 환경변수로 override 가능
- 식품안전나라 자동 폴백
- 작동 시: 정확
- 미작동 시: 사용자에게 정확한 endpoint URL 요청

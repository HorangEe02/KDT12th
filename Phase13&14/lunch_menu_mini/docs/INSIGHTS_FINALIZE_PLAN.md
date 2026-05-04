# NLP Insights 페이지 완전 마무리 — 사전 상세 구현 계획

> **작성일**: 2026-05-01
> **범위**: 5개 작업으로 /insights 페이지 100% 동작화 (시연 가능 상태)
> **예상 규모**: 백엔드 ~250 LOC + 프런트 ~150 LOC + 시드 ~120 LOC + 모의 리뷰 600행, 총 3–4시간

---

## 1. 진단 요약 (재정리)

| 컴포넌트 | 현재 상태 | 마무리 후 목표 |
|---|---|---|
| HealthStrip | ✅ 동작 | 그대로 (검증만) |
| SentimentOverview | ❌ 데이터 0 | 100+ 식당의 감성 점수 시각화 |
| MenuNormalizerPlayground | 🔴 422 버그 | 인터랙티브 정규화 UI 정상 |
| RAGStatsCard | ✅ 동작 (0건) | 빈 상태 UI 개선 |
| RoadmapCard | ✅ (정적) | 진행 상황 갱신 |

---

## 2. 작업 5단계

### 🥇 #1. MenuNormalizerPlayground 422 fix (5분)

**원인**: 백엔드 `MenuNormalizeIn` 스키마는 `raw_name` 필드 요구, 컴포넌트는 `text` 보냄.

**수정**:
```typescript
// MenuNormalizerPlayground.tsx
- body: JSON.stringify({ text: raw }),
+ body: JSON.stringify({ raw_name: raw }),
```

또는 백엔드를 두 형식 모두 받도록 (alias 추가) — 백엔드 변경이 더 견고:
```python
class MenuNormalizeIn(BaseModel):
    raw_name: Optional[str] = Field(None, alias="text")
    text: Optional[str] = None
```
→ 보수적으로 **프런트 한 줄 변경** 채택.

**검증**: Playground에서 "매콤한 돼지 불백" 입력 → 200 응답 + 정규화 결과.

---

### 🥈 #2. 감성 데이터 시드 (1.5–2h)

#### 2-1. 데이터 소스 선택지

| 옵션 | 출처 | 정확도 | 작업량 |
|---|---|:-:|:-:|
| **A. 모의 리뷰 자동 생성** | 카테고리별 템플릿 (예: 한식 → "맛있어요/조용해요/...") | 🟡 | 🟢 30m |
| **B. Kakao Local API 리뷰** | Kakao 식당 검색 결과의 평점/리뷰 | 🟢 | 🔴 외부 API 미지원 |
| **C. AI 생성** (Gemini로 가짜 리뷰 100건) | LLM | 🟡 | 🟡 비용 |
| **D. 하이브리드 A** | 카테고리 + 평점 분포 기반 합성 + KcELECTRA 분석 | 🟢 | 🟡 1h |

**선택**: **D — 하이브리드 합성**:
- 식당당 3–5개 모의 리뷰 (카테고리·평점 기반)
- KcELECTRA(`/nlp/sentiment/refresh` 엔드포인트 또는 직접 분석)로 감성 점수
- `sentiment_score`, `sentiment_count` 컬럼을 `restaurants` 테이블에 추가

#### 2-2. DB 스키마 확장

```sql
ALTER TABLE restaurants ADD COLUMN sentiment_score FLOAT;       -- -1.0 ~ +1.0
ALTER TABLE restaurants ADD COLUMN sentiment_count INTEGER DEFAULT 0;
ALTER TABLE restaurants ADD COLUMN sentiment_updated_at DATETIME;
```

스크립트: `lunch-optimizer/scripts/migrate_sentiment_columns.py`

#### 2-3. 모의 리뷰 시드 + 분석

`lunch-optimizer/scripts/seed_sentiment.py`:
1. restaurants 100개 샘플 (rating 분포 기준)
2. 카테고리별 템플릿 리뷰 3–5개씩 (rating 5: 긍정 위주, rating 3 이하: 혼합)
3. KcELECTRA 추론 (`/nlp/sentiment/refresh` 또는 NLP 모듈 직접 호출)
4. `sentiment_score = avg(per-review polarity)` 계산
5. raw SQL UPDATE

#### 2-4. /nlp/sentiment/top 엔드포인트 응답 확인

이미 존재하므로 시드 후 자동 활성화. 단, 백엔드가 `sentiment_score` 컬럼을 어떻게 읽는지 확인 필요.

---

### 🥉 #3. 빈 상태 UI 개선 (30m)

#### 3-1. SentimentOverview 개선
- 데이터 0건일 때 친절한 안내 메시지 + "분석 실행" 버튼
- 버튼 클릭 시 `POST /nlp/sentiment/refresh` 호출 → 진행 상태 표시

```tsx
{chartData.length === 0 && (
  <div className="text-center py-8">
    <p className="text-sm text-text-tertiary">
      감성 분석 데이터가 아직 없습니다.
    </p>
    <button onClick={handleRefresh} className="mt-3 ...">
      🔄 감성 분석 실행
    </button>
  </div>
)}
```

#### 3-2. RAGStatsCard 빈 상태 개선
- "아직 챗봇을 사용하지 않았습니다. /concierge 에서 시작하세요." 안내 + 링크

---

### #4. 메뉴 정규화 통계 누적 검증 (30m)

#### 4-1. 진단
- `menu_normalization` 테이블 0건 — 정규화 호출 시 자동 INSERT 안 되는 이유 확인
- 백엔드 menu router의 정규화 로직 점검

#### 4-2. 가능한 fix
A) 정규화 호출마다 캐시 INSERT (현재 미적용) — `normalize()` 메서드에 자동 캐시 로직
B) /menu/stats가 다른 테이블 (예: `meal_items`) 의 normalized_name 카운트로 변경

→ **B 채택**: meal_items 의 `normalized_name` 으로 stats 계산 (이미 데이터 누적됨)

backend 변경:
```python
# routers/menu.py /stats
def stats():
    rows = session.query(MealItem.match_type, func.count()).group_by(MealItem.match_type).all()
    total = sum(c for _, c in rows)
    return {"total": total, "by_method": dict(rows), "hit_rate": ...}
```

또는 menu_normalization 테이블에 자동 캐시 — 정규화 코드에 `INSERT OR IGNORE` 추가.

---

### #5. RoadmapCard 진행 상황 갱신 (15m)

현재 정적 컴포넌트. Phase 13/14 진행 상황 반영:
- ✅ Phase 13: 인증·관리자·데모 배포
- ✅ Phase 14: 자연어 영양 입력
- ✅ Phase 15: 감성 분석 활성화
- 🟡 Phase 16: ABSA·Food NER 학습 (보류)
- ✅ 인프라 운영 (2026-05-04): 외장 SSD → 내장 SSD(`~/Downloads/lunch_menu_mini`) 이동, Cloudflare quick tunnel 자동 갱신 절차 정착

---

## 3. 구현 순서 (3 phase)

### Phase A — UI 즉시 fix (40m)
- [A1] MenuNormalizerPlayground.tsx text→raw_name
- [A2] SentimentOverview.tsx 빈 상태 + "분석 실행" 버튼
- [A3] RAGStatsCard.tsx 빈 상태 안내
- [A4] RoadmapCard.tsx 진행률 갱신

### Phase B — 감성 데이터 시드 (1.5–2h)
- [B1] migrate_sentiment_columns.py 작성 + 적용
- [B2] seed_sentiment.py 작성:
  - 식당 100개 샘플 (rating ≥ 3)
  - 카테고리별 템플릿 리뷰 3–5개씩
  - KcELECTRA 추론 (NLP 모듈 직접 호출)
  - raw SQL UPDATE
- [B3] /nlp/sentiment/top 200건 응답 확인

### Phase C — 통계 누적 (30m)
- [C1] /nlp/menu/stats 가 meal_items 기반으로 동작하도록 백엔드 수정
- [C2] live test

### Phase D — 검증·배포 (30m)
- [D1] 프런트 정적 빌드 + Firebase 재배포
- [D2] /insights 페이지 라이브 검증 (5컴포넌트 모두)

---

## 4. 위험 매트릭스

| 위험 | 가능성 | 영향 | 완화 |
|---|:-:|:-:|---|
| KcELECTRA 모델 로드 시간 | 🟡 | 🟡 | NLP 컨테이너 startup_period 90s 이미 설정 |
| 모의 리뷰 비현실성 | 🟡 | 🟢 | 카테고리·평점 분포 기반 |
| restaurants 8759건 분석 시간 | 🔴 | 🟡 | 100건 샘플로 제한 |
| menu_stats 변경 시 회귀 | 🟢 | 🟢 | 옛 호환 유지 (try/except) |

---

## 5. 산출물 체크리스트

- [ ] 프런트 4 컴포넌트 변경
- [ ] backend nlp routers/menu.py stats 수정
- [ ] scripts/migrate_sentiment_columns.py 신규
- [ ] scripts/seed_sentiment.py 신규
- [ ] /insights live 검증 (5/5 컴포넌트)
- [ ] Firebase 재배포

---

## 6. 즉시 실행 시작

# 📦 Legacy — Phase 1~5 Python/Streamlit 보존

> 이 디렉토리는 **Phase 6 Next.js 마이그레이션 이전** 의 Streamlit 기반 구현을 보존합니다.
> 삭제하지 않는 이유: (1) 학습 레퍼런스, (2) Python 모델·알고리즘 재학습 시 필요,
> (3) 포팅 근거 (`frontend/lib/predict.ts` 가 `src/ai/predict.py` 의 정확 이식임을 증명).

---

## 📂 구조

```
legacy/
├── app.py                   # Streamlit 엔트리 (레거시)
├── Dockerfile               # Cloud Run 배포 이미지 (Phase 5a)
├── .dockerignore
├── requirements.txt         # Python 3.10 의존성 (pandas, streamlit, langchain 등)
│
├── src/                     # Python 소스
│   ├── config.py · data_loader.py · utils.py
│   ├── ai/                  # 승률 모델 · LLM 클라이언트 · 프롬프트 · RAG · Multi-Agent
│   ├── api/                 # Kakao · TourAPI · 기상청 클라이언트
│   ├── db/                  # Firestore · Cloud Storage (Phase 5a)
│   ├── ui/                  # Streamlit 컴포넌트 (5 탭 · 사이드바 · Hero 등)
│   └── viz/                 # Folium · Plotly · popup builder
│
├── models/
│   └── win_rate_model.pkl   # scikit-learn 로지스틱 회귀 (Phase 4)
│                            # (frontend/public/data/model.json 이 이 모델의 직렬화 형태)
│
├── assets/                  # Streamlit CSS (Stadium Editorial 디자인 토큰 원본)
│                            # → frontend/app/globals.css 로 이식됨
│
├── public/                  # Firebase Hosting redirect (Cloud Run 으로 rewrite)
│   └── index.html           # Phase 5a 시절 hosting 진입 HTML
│
├── tests/                   # 스캐폴드 (빈 __init__.py)
│
├── scripts/                 # Python 유지보수 스크립트
│   ├── cache_poi.py         # TourAPI → data/poi_cache/*.json 크롤러
│   ├── seed_dummy_data.py   # 개발용 더미 POI 생성
│   ├── validate_phase2.py ~ validate_phase5.py  # Phase 별 검증 스크립트
│   └── deploy.sh            # Phase 5a Cloud Run + Hosting 일괄 배포
│
└── data_cache/              # Python 런타임 캐시 (크기: 수 MB)
    ├── poi_cache/           # 30 JSON (TourAPI 응답 캐시)
    ├── chroma_db/           # Phase 4 RAG 벡터 DB
    ├── knowledge/           # 구장별 원정 팁 (45 Markdown/JSON)
    └── route_cache/         # Kakao 경로 응답 캐시 (md5 키)
```

---

## 🚫 Phase 6 이후에는 사용하지 않음

- **`frontend/` 가 유일한 프로덕션 앱** (Next.js 16 · Firebase App Hosting 배포)
- 이 디렉토리의 파일들은 **읽기 전용 참고 자료** 로 취급
- 만약 로컬에서 레거시 Streamlit 을 재실행하고 싶다면:
  ```bash
  cd legacy
  pip install -r requirements.txt
  streamlit run app.py
  ```
  단, `src/config.py` 의 경로가 `../data/*.csv` 로 돼 있어야 함 (필요 시 수정).

---

## 🔗 포팅 매핑 (Python → TypeScript)

| Python 원본 | Next.js 이식본 |
|---|---|
| `src/ai/predict.py` | `frontend/lib/predict.ts` |
| `src/ai/tools.py` | `frontend/lib/ai/tools.ts` |
| `src/ai/agents.py` | `frontend/lib/ai/agents.ts` |
| `src/ai/prompts.py` | `frontend/lib/ai/prompts.ts` |
| `src/ai/rag.py` (ChromaDB) | `frontend/lib/ai/rag.ts` (BM25-lite 인메모리) |
| `src/ai/mock_responses.py` | `frontend/lib/ai/mock.ts` |
| `src/api/kakao_map.py` | `frontend/lib/api/{kakao,osrm,haversine,route}.ts` (3-tier 폴백 추가) |
| `src/api/weather_api.py` | `frontend/lib/api/weather.ts` |
| `src/db/firestore_client.py` | `frontend/lib/firebase/{client,admin,visited,shared-plans}.ts` |
| `src/viz/folium_map.py` | `frontend/components/map/leaflet-map.tsx` |
| `src/viz/plotly_charts.py` | `frontend/components/{matches,places}/*.tsx` |
| `assets/css/style.css` | `frontend/app/globals.css` (Tailwind v4 @theme) |

상세 히스토리: [`docs/PHASE6_NEXTJS_MIGRATION.md`](../docs/PHASE6_NEXTJS_MIGRATION.md)

---

*보존 시작: 2026-04-17 Phase 6 종료 시점 · 정리: 2026-04-18*

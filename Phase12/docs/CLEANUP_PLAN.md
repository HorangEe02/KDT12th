# 🧹 Phase12/ 디렉토리 정리 계획

> 작성: 2026-04-17 (Session F 이후, 코드·배포 완료 시점)
> 목적: 6 개 Phase(Python Streamlit → Next.js)를 거치며 쌓인 잔재를 정리하고,
>       신규 기여자가 5초 안에 구조를 파악할 수 있게 만든다.

---

## 1. 현재 상태 진단

### 1-1. 문제점 인벤토리

| 분류 | 항목 | 문제 |
|---|---|---|
| 📁 문서 분산 | `docs/` (11) · `guide/` (7) · `md/` (1) | 같은 프로젝트 문서가 3 곳에 흩어짐 |
| 📁 중복 설정 | 루트 `apphosting.yaml` + `frontend/apphosting.yaml` | 루트 버전은 stripped · 활용처 불명 |
| 📁 혼란스러운 이름 | 루트 `api/` 디렉토리 | 실제는 KBO 공공 API **문서** (코드 아님) |
| 🗑️ 빈 디렉토리 | `secrets/` (0 파일) · `tests/` (빈 `__init__.py`) | 존재만으로 노이즈 |
| 🗑️ .DS_Store | 4개 이상 디렉토리 | macOS 찌꺼기 |
| 🧓 레거시 혼재 | `app.py` · `Dockerfile` · `requirements.txt` · `src/` · `models/*.pkl` · `assets/` · `public/index.html` | Phase 1~5 Python 파일이 Phase 6 Next.js 앱 옆에 평면 배치 |
| 🧓 레거시 캐시 | `data/poi_cache/` · `data/chroma_db/` · `data/knowledge/` | Python 런타임 캐시 · Next.js 빌드엔 불필요 |
| 🔁 duplicates | `fonts/KBO Dia Gothic_TTF` + `fonts/KBO_Dia_Gothic_TTF.zip` | 압축+해제 동시 존재 |
| 📄 정체불명 | `README.pdf` · `미니프로젝트_웹기초_AI...pdf` | 루트에 프로젝트 브리프 2 종 |

### 1-2. 디스크 현황

| 경로 | 크기 | 성격 |
|---|---|---|
| `frontend/` | 1.6 GB | node_modules 포함 — 그대로 유지 |
| `uiux/` | 13 MB | 참고용 목업 — 유지 |
| `fonts/` | 4.6 MB | TTF + zip (중복) |
| `data/` | 1.2 MB | CSV + poi_cache + chroma_db |
| `src/` | 472 KB | Python legacy |
| `guide/` | 248 KB | phase 문서 7 개 |
| `docs/` | 108 KB | 문서 11 개 |
| `scripts/` | 92 KB | Python + shell 혼재 |
| PDFs | 1.3 MB | README.pdf + 브리프 |

---

## 2. 정리 원칙

1. **파괴 최소**: 모든 이동은 `mv` 또는 복사 (삭제는 재생성 가능한 캐시·빈 파일만)
2. **레거시 보존**: Phase 1~5 Python 코드는 **삭제 아닌 아카이브** (`legacy/` 로)
3. **배포 불변**: `frontend/` · `data/*.csv` · `firebase.json` · `firestore.*` 는 위치 고정
4. **경로 참조 동기화**: 이동 후 `CLAUDE.md`, `README.md`, `scripts/export_to_json.py` 의 경로 업데이트
5. **GitHub 반영**: 로컬 + `~/KNU_KDT_12th/Phase12/` 양쪽 동시 정리 + push

---

## 3. 목표 구조 (After)

```
Phase12/
├── 📄 CLAUDE.md                     # AI 에이전트 컨텍스트
├── 📄 README.md                     # 프로젝트 소개 + Live URL
├── 📄 .env / .env.example / .gitignore
├── 📄 firebase.json                 # App Hosting + Firestore
├── 📄 .firebaserc                   # project: mini12-310f5
├── 📄 firestore.rules
├── 📄 firestore.indexes.json
│
├── 📁 frontend/                     # ⭐ Next.js 16 메인 앱 (Production)
│
├── 📁 data/                         # 원본 CSV → scripts/export_to_json.py 로 JSON 변환
│   ├── SCHEMA.md
│   ├── kbo_schedule_2026.csv
│   ├── stadiums.csv
│   └── team_stats_10yr.csv
│
├── 📁 scripts/                      # Phase 6 유지보수 스크립트 (Python · shell)
│   ├── export_to_json.py            # 가장 중요 — CSV → public/data JSON
│   ├── preflight.sh                 # 배포 전 점검 (Session F)
│   └── validate_data.py
│
├── 📁 docs/                         # 📚 모든 문서 1곳
│   ├── ARCHITECTURE.md
│   ├── CLEANUP_PLAN.md              # (이 문서)
│   ├── DEMO_SCRIPT.md
│   ├── DEPLOY_CHECKLIST.md
│   ├── IMPLEMENTATION_PLAN.md       # ← md/ 에서 이동
│   ├── OSM_FALLBACK_PLAN.md
│   ├── PHASE6_NEXTJS_MIGRATION.md
│   ├── PRESENTATION_OUTLINE.md
│   ├── QA_PREP.md
│   ├── SESSION_E_PLAN.md
│   ├── SESSION_F_DEPLOY_RUNBOOK.md
│   ├── VIZ_CONTRACT.md
│   ├── guides/                      # ← guide/ 에서 이동
│   │   ├── INDEX.md
│   │   └── PHASE0_GUIDE.md ~ PHASE5_GUIDE.md
│   ├── reference/                   # ← api/ + fonts/ 이동
│   │   ├── tourapi_ko.md
│   │   ├── weather_short_forecast.md
│   │   ├── weather_medium_forecast.md
│   │   └── fonts/
│   │       └── KBO_Dia_Gothic_TTF.zip  (원본 유지 · 해제본 삭제)
│   └── brief/
│       └── project_brief.pdf        # (한글 파일명 영문으로 개명)
│
├── 📁 uiux/                         # 원본 HTML 목업 (참고용)
│
└── 📁 legacy/                       # 📦 Phase 1~5 Python 보존
    ├── README.md                    # "왜 여기 있는지" 간단 설명
    ├── app.py                       # Streamlit 엔트리
    ├── Dockerfile                   # Streamlit Cloud Run 이미지
    ├── .dockerignore
    ├── requirements.txt
    ├── public/index.html            # Firebase Hosting redirect
    ├── assets/                      # Streamlit CSS/JS
    ├── src/                         # Python 소스 (ai, api, db, ui, viz)
    ├── models/                      # win_rate_model.pkl
    ├── tests/                       # 빈 스캐폴드
    ├── scripts/                     # cache_poi · validate_phase[2-5] · seed_dummy_data · deploy.sh
    └── data_cache/                  # poi_cache/ + chroma_db/ + knowledge/
```

**루트는 13 개 이하로 축소** (현재 37 → 13).

---

## 4. 단계별 실행 계획 (5 Phase)

### Phase 1: Zero-risk cleanup (5분)

**행위**:
- 모든 `.DS_Store` 재귀 삭제
- 빈 `secrets/`, `tests/` 제거 (tests 는 legacy/ 로 이동 대상이라 Phase 4 에서 처리)
- 루트 `apphosting.yaml` 삭제 (frontend/apphosting.yaml 이 실제 사용됨)
- 중복 `fonts/KBO Dia Gothic_TTF/` 해제본 삭제 (zip 유지)

**검증**: `firebase deploy --dry-run` 은 없으므로 `pnpm build` 로 확인

### Phase 2: 문서 통합 (docs 일원화) (3분)

**행위**:
- `md/IMPLEMENTATION_PLAN.md` → `docs/IMPLEMENTATION_PLAN.md`
- `guide/*` → `docs/guides/*`
- 빈 `md/`, `guide/` 디렉토리 제거

**검증**: `docs/` 트리 · 모든 문서 접근 가능

### Phase 3: 참조 콘텐츠 이동 (3분)

**행위**:
- 루트 `api/` → `docs/reference/` (파일명 영문화):
  - `한국관광공사_*.md` → `tourapi_ko.md`
  - `기상청_단기예보*.md` → `weather_short_forecast.md`
  - `기상청_중기예보*.md` → `weather_medium_forecast.md`
  - `api/maps/` → `docs/reference/maps/`
- 루트 `fonts/` → `docs/reference/fonts/`
- `README.pdf` 삭제 (README.md 가 정본)
- `미니프로젝트_웹기초_AI...pdf` → `docs/brief/project_brief.pdf`

**검증**: 이동 후 내용물 확인

### Phase 4: Phase 1~5 Python → `legacy/` 이동 (10분)

**행위**:
- `legacy/` 생성 + `legacy/README.md` 작성 ("Phase 6 이전 Streamlit 버전 보존")
- 이동:
  - `app.py`, `Dockerfile`, `.dockerignore`, `requirements.txt` → `legacy/`
  - `src/` → `legacy/src/`
  - `models/` → `legacy/models/`
  - `assets/` → `legacy/assets/`
  - `public/index.html` + `public/` → `legacy/public/`
  - `tests/` → `legacy/tests/`
  - `data/poi_cache/` → `legacy/data_cache/poi_cache/`
  - `data/chroma_db/` → `legacy/data_cache/chroma_db/`
  - `data/knowledge/` → `legacy/data_cache/knowledge/`
  - `data/route_cache/` → `legacy/data_cache/route_cache/` (Python Kakao fallback 캐시)
- `scripts/` 에서 Python-only 스크립트 → `legacy/scripts/`:
  - `cache_poi.py`, `seed_dummy_data.py`
  - `validate_phase2.py` ~ `validate_phase5.py`
  - `deploy.sh` (Phase 5 Streamlit Cloud Run 배포 스크립트)
- **유지**: `scripts/export_to_json.py` (Phase 6 필수) · `scripts/preflight.sh` · `scripts/validate_data.py` (Phase 6 데이터 검증용)

**검증**:
- `scripts/export_to_json.py` 여전히 동작 (경로가 `data/*.csv` 그대로라 영향 없음)
- `pnpm build` 로 frontend 재검증 (독립적이지만 확인)

### Phase 5: 경로 참조 동기화 (10분)

**행위 — 파일별 업데이트**:
- `CLAUDE.md`:
  - `md/IMPLEMENTATION_PLAN.md` → `docs/IMPLEMENTATION_PLAN.md`
  - `guide/PHASE[0-5]_GUIDE.md` → `docs/guides/PHASE[0-5]_GUIDE.md`
  - `guide/INDEX.md` → `docs/guides/INDEX.md`
  - `src/ui/components/hero.py` 같은 레퍼런스는 `legacy/src/...` 로 업데이트 (주석 · docstring)
  - `app.py` → `legacy/app.py`
  - Phase 6 Session 핸드오프 섹션은 그대로 (frontend/ 경로 그대로)
- `README.md`:
  - `md/IMPLEMENTATION_PLAN.md` → `docs/IMPLEMENTATION_PLAN.md`
  - `guide/INDEX.md` → `docs/guides/INDEX.md`
  - 섹션 4-1-bis (Legacy 스택) 에 `legacy/` 경로 명시
- `frontend/AGENTS.md` · `frontend/CLAUDE.md`: 변경 없음 (frontend-internal)
- `scripts/export_to_json.py`:
  - 출력 경로 `frontend/public/data/` 그대로 (변경 없음)
  - 입력 `data/*.csv` 그대로 (변경 없음)
  - 내부 import 가 `from src.xxx` 로 되어 있으면 `from legacy.src.xxx` 로 변경 (실제 읽어서 확인)
- `scripts/preflight.sh`: `secrets/` 체크 → 제거됨에 따라 optional 처리
- `frontend/lib/ai/prompts.ts` 같이 src/ai/prompts.py 참조하는 주석들: 주석 업데이트 (동작에 영향 없음 · 선택)

### Final: 검증 + GitHub 반영

**로컬 검증**:
```bash
bash scripts/preflight.sh                         # secrets/ 없어서 에러 안 나야 함
cd frontend && pnpm build && cd ..                # 13 routes compile
grep -rE "(md/|guide/|src/|models/)" CLAUDE.md README.md | head  # 구 경로 참조 없어야 함
```

**GitHub 동기화**:
- `~/KNU_KDT_12th/Phase12/` 를 rsync 로 **새 상태** 로 동기화
- `git rm -r <구 경로>` + `git add <새 경로>` + 단일 커밋 (정리 이력 명확)
- `git push origin main`
- App Hosting 자동 롤아웃 확인 (frontend/ 안 바뀌었으니 빌드는 성공해야 함)

---

## 5. 롤백 전략

각 Phase 후 `git status` 로 변경 내역 확인. 문제 발생 시:
- 로컬: Phase 별로 분리 커밋 후 `git reset --hard HEAD~N`
- GitHub: 이전 커밋 hash 로 revert commit 가능

**영향 없는 것 (안전)**:
- 배포된 Next.js 앱 (frontend/ 불변)
- Firestore / Secret Manager
- GitHub repo 의 Phase 1~11 (손 안 댐)

**위험 최소화**:
- 모든 Python 코드는 삭제 아닌 **이동**
- 데이터 캐시는 `legacy/data_cache/` 로 이동 후 gitignore 재확인

---

## 6. 성공 기준

- [ ] Phase12/ 루트 항목 수 ≤ 15
- [ ] 문서 디렉토리 3 → 1 (`docs/` 만)
- [ ] Phase 1~5 Python 자원이 `legacy/` 아래 정돈됨
- [ ] `pnpm build` 성공 (13 routes)
- [ ] `bash scripts/preflight.sh` 통과
- [ ] `CLAUDE.md`, `README.md` 의 모든 경로 참조가 새 구조와 일치
- [ ] GitHub `Phase12/` 도 동일 구조로 업데이트됨
- [ ] App Hosting 자동 롤아웃 성공 (frontend/ 변경 없으므로 빌드 통과)

---

## 7. 예상 소요

| Phase | 작업 | 소요 |
|---|---|---|
| 1 | .DS_Store · 빈 dir · 중복 apphosting 정리 | 5 분 |
| 2 | md/ · guide/ → docs/ | 3 분 |
| 3 | api/ · fonts/ · PDF 이동 | 3 분 |
| 4 | Python legacy → legacy/ | 10 분 |
| 5 | 참조 경로 업데이트 | 10 분 |
| Final | 검증 + GitHub 푸시 | 5 분 |
| **합계** | | **약 36 분** |

---

*작성: 2026-04-17 Session F+*
*다음: 단계별 실행 — Phase 1 부터 순차 진행 · 각 단계 후 검증*

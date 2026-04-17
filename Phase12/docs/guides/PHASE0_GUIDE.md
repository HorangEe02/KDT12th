# 🚀 Phase 0 구현 가이드 — 프로젝트 부트스트랩 with Claude Code

> **목표**: 5일짜리 Streamlit 프로젝트의 시작점을 30분 안에 안전하게 세팅한다.
> **대상 독자**: 프로젝트 팀장 1명 + 팀원 3~4명
> **전제 조건**: [README.md](./README.md) 및 [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md)를 먼저 읽었음

---

## 🎯 0. Phase 0 개요

### 완료 조건
Phase 0이 "끝났다"는 다음 4가지가 모두 참일 때입니다.
1. 팀원 **전원이** `git clone` → `streamlit run app.py` → 브라우저에서 페이지 확인 성공
2. `CLAUDE.md`가 프로젝트 루트에 존재하고, Claude Code 세션 시작 시 자동 인식됨
3. 공공데이터포털 API 키가 팀원 **전원에게** 발급 완료 또는 승인 대기 중
4. 디렉토리 구조가 [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) 명세와 일치

### 실행 주체 범례
- 🧑‍✈️ **팀장만**: 한 번만 수행, 다른 팀원은 pull로 결과물 받음
- 👥 **팀원 전원**: 각자 로컬에서 개별 수행
- 🤖 **Claude Code**: Claude Code 세션 안에서 프롬프트로 수행

### 작업 순서 맵
```
 [1. API 키 신청] 👥 ─┐ (승인 대기 동안 병렬 진행)
                    │
 [2. Git 저장소] 🧑‍✈️ ─┤
                    │
 [3. 로컬 클론] 👥  ─┤
                    ▼
 [4. 가상환경 생성] 👥
                    ▼
 [5. 스캐폴딩] 🧑‍✈️🤖 ← 팀장만 Claude Code로 수행 → git push
                    ▼
 [6. git pull] 👥
                    ▼
 [7. 의존성 설치] 👥
                    ▼
 [8. 환경변수 설정] 👥
                    ▼
 [9. Hello World 검증] 👥
```

---

## 🛠️ 1. 사전 준비 (Prerequisites)

### 1-1. 로컬에 설치되어야 하는 것 👥

| 도구 | 최소 버전 | 확인 명령 |
|---|---|---|
| Python | 3.10 이상 | `python --version` |
| Git | 2.30+ | `git --version` |
| Claude Code | 최신 | `claude --version` |
| VS Code (권장) | 최신 | - |

설치 링크: [Python](https://www.python.org/downloads/) · [Git](https://git-scm.com/) · [Claude Code 설치 가이드](https://docs.claude.com/en/docs/claude-code)

### 1-2. API 키 발급 — **⚠️ 오늘 오전에 반드시 신청하세요** 👥

공공데이터포털 API 승인은 **1시간~반나절** 걸립니다. 이거 하나 안 하면 Phase 1이 통째로 블록됩니다.

| API | 발급처 | 예상 승인 시간 | 비고 |
|---|---|---|---|
| 한국관광공사 TourAPI | [공공데이터포털](https://www.data.go.kr/data/15101578/openapi.do) | 즉시~1시간 | "활용 신청" 버튼 |
| 기상청 단기예보 | [공공데이터포털](https://www.data.go.kr/) | 즉시~1시간 | "단기예보 조회서비스" 검색 |
| 카카오 REST API | [Kakao Developers](https://developers.kakao.com/) | 즉시 | 앱 생성 → REST API 키 복사 |
| 카카오모빌리티 (길찾기) | [Kakao Mobility](https://developers.kakaomobility.com/) | 즉시 | 카카오 계정으로 로그인 |
| OpenAI API (또는 Gemini) | [platform.openai.com](https://platform.openai.com/) | 즉시 (결제 등록 필요) | Gemini는 무료 티어 사용 가능 |

> 💡 **팁**: 팀원 중 1명이 대표로 발급받아 `.env`로 공유하는 방법도 가능하지만, TourAPI는 1일 트래픽 한도가 있어 **팀원별 개별 발급을 권장**합니다.

### 1-3. 계정 준비 👥

- GitHub 계정 (팀장은 Organization 생성 권장)
- OpenAI/Gemini 결제 계정 (AI 담당자만 필수)

---

## 📦 2. Step 1. Git 저장소 생성 🧑‍✈️

**실행 주체**: 팀장 1명

### 목표
원격 저장소를 만들고 팀원 전원을 Collaborator로 초대한다.

### 실행 단계

1. GitHub에서 신규 저장소 생성 (Private 또는 Public)
   - 이름: `away-game-companion`
   - README 추가 체크 ✅
   - Python `.gitignore` 템플릿 선택
   - 라이선스: MIT (선택)

2. 팀원을 Collaborator로 초대
   - Settings → Collaborators → Add people

3. 로컬에 클론
   ```bash
   git clone https://github.com/{your-org}/away-game-companion.git
   cd away-game-companion
   ```

### 검증
```bash
git remote -v
# origin  https://github.com/.../away-game-companion.git (fetch)
# origin  https://github.com/.../away-game-companion.git (push)
```

---

## 🐍 3. Step 2. Python 가상환경 생성 👥

**실행 주체**: 팀원 전원 (각자 로컬)

### 목표
프로젝트 전용 Python 가상환경을 만들어 패키지 버전 충돌을 예방한다.

### 실행 단계

```bash
# 프로젝트 디렉토리 안에서
python -m venv venv

# 활성화 (Mac/Linux)
source venv/bin/activate

# 활성화 (Windows PowerShell)
# .\venv\Scripts\Activate.ps1
```

<details>
<summary>🪟 Windows 사용자 클릭</summary>

Windows cmd:
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

PowerShell에서 실행 정책 오류 발생 시:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
</details>

### 검증
```bash
which python     # Mac/Linux
# → /path/to/project/venv/bin/python

python --version # Python 3.10 이상이어야 함
```

---

## 🏗️ 4. Step 3. Claude Code로 프로젝트 스캐폴딩 🧑‍✈️🤖

**실행 주체**: 팀장 1명, Claude Code 사용

### 목표
[IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md)에 명시된 디렉토리 구조와 빈 파일들을 한 번에 생성한다.

### 사전 작업
프로젝트 루트에서 Claude Code 실행:
```bash
cd away-game-companion
claude
```

### 🤖 Claude Code 프롬프트 (복사해서 그대로 사용)

````
이 프로젝트의 README.md와 IMPLEMENTATION_PLAN.md를 먼저 읽어줘.
그 후 IMPLEMENTATION_PLAN.md의 Phase 0에 명시된 디렉토리 구조를
정확히 따라 빈 파일과 디렉토리를 생성해줘.

생성 규칙:
1. 모든 Python 패키지 디렉토리(src/, src/api/, src/ui/, src/ui/tabs/,
   src/viz/, src/ai/, tests/)에 빈 __init__.py를 추가해줘.
2. app.py는 지금은 비워두지 말고 다음 최소 코드로 채워줘:

```python
import streamlit as st

st.set_page_config(
    page_title="원정 응원 플래너",
    page_icon="⚾",
    layout="wide",
)

st.title("⚾ 원정 응원 플래너")
st.caption("Phase 0 bootstrap — 개발 준비 완료")
st.success("환영합니다! 이 페이지가 보이면 환경 세팅이 성공한 것입니다.")
```

3. requirements.txt에는 다음 패키지만 포함시키고, 버전은 유연하게
   하한선만 지정해줘:

streamlit>=1.40
streamlit-folium>=0.27
folium
pandas
plotly
scikit-learn
requests
httpx
python-dotenv
openai
langchain
chromadb

4. .gitignore에는 Python 표준 + 다음 항목을 추가해줘:
   - venv/
   - .env
   - __pycache__/
   - *.pkl
   - data/poi_cache/*.json
   - .streamlit/secrets.toml
   - models/*.pkl
   - .DS_Store

5. .env.example을 만들고 다음 키 이름들만 빈 값으로 명시해줘
   (실제 키는 적지 말 것):

TOUR_API_KEY=
WEATHER_API_KEY=
KAKAO_REST_API_KEY=
KAKAO_MOBILITY_API_KEY=
OPENAI_API_KEY=

작업이 끝나면 tree 명령으로 전체 구조를 보여줘.
````

### 검증
```bash
tree -I 'venv|__pycache__' -L 3
```

기대 출력:
```
.
├── CLAUDE.md               (아직 없음 → Step 4에서 생성)
├── IMPLEMENTATION_PLAN.md
├── README.md
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── assets/
│   ├── css/
│   └── images/
├── data/
│   └── poi_cache/
├── models/
├── src/
│   ├── __init__.py
│   ├── api/
│   ├── ui/
│   │   └── tabs/
│   ├── viz/
│   └── ai/
└── tests/
    └── __init__.py
```

### 첫 커밋
```bash
git add .
git commit -m "feat(phase-0): initial project scaffolding"
git push origin main
```

---

## 📝 5. Step 4. CLAUDE.md 작성 🧑‍✈️🤖

**실행 주체**: 팀장 1명, Claude Code 사용

### 목표
Claude Code가 매 세션 자동으로 읽을 프로젝트 컨텍스트 문서를 작성한다. 이게 있어야 앞으로의 프롬프트가 짧아진다.

### 🤖 Claude Code 프롬프트

````
/init

이 명령으로 CLAUDE.md를 생성해줘. 단, 자동 생성된 초안을 그대로
두지 말고, 이 프로젝트의 README.md와 IMPLEMENTATION_PLAN.md를
충분히 읽은 뒤 아래 섹션 구조로 다시 작성해줘:

1. 프로젝트 한 줄 요약
2. 기술 스택 (Streamlit / Python / Folium / Plotly / LLM / 카카오API /
   한국관광공사 TourAPI)
3. 디렉토리 맵 (tree 형식, 핵심 파일만)
4. 코딩 컨벤션
5. 실행·테스트 명령어
6. 금지사항 (DO NOT)
7. 현재 진행 중인 Phase

CLAUDE.md의 최종 분량은 150~250줄 사이로 맞춰줘.
각 섹션의 상세 내용은 이 가이드 문서 PHASE0_GUIDE.md의
섹션 10을 참고하되, 그대로 복사하지 말고 이 프로젝트에 맞게
재작성해줘.
````

### 검증
```bash
wc -l CLAUDE.md
# 150~250 사이

# Claude Code를 재시작하고 아무 질문이나 던져봤을 때
# 답변에 프로젝트 맥락이 반영되는지 확인
```

---

## 📥 6. Step 5. 팀원 동기화 & 의존성 설치 👥

**실행 주체**: 팀원 전원

### 목표
팀장이 push한 스캐폴딩을 모든 팀원의 로컬로 가져오고 패키지 설치.

### 실행 단계

```bash
# 1. 최신 변경사항 받기
git pull origin main

# 2. 가상환경 활성화 (Step 2에서 이미 생성했다면)
source venv/bin/activate

# 3. 의존성 설치
pip install --upgrade pip
pip install -r requirements.txt
```

### 검증
```bash
pip list | grep -E "streamlit|folium|pandas|openai"
```

4개 패키지가 모두 리스트에 보여야 합니다.

### 트러블슈팅
- `pip install` 중 **Rust 컴파일 오류** → `chromadb` 설치 시 발생 가능. 해결: `pip install chromadb --no-build-isolation` 또는 Python 버전 3.10~3.11로 맞추기
- **M1/M2 Mac에서 패키지 설치 실패** → `arch -arm64 pip install ...`
- **Windows에서 `Microsoft Visual C++ 14.0 required`** → [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) 설치

---

## 🔐 7. Step 6. 환경변수 설정 👥

**실행 주체**: 팀원 전원

### 목표
개인 API 키를 `.env` 파일에 저장하고, **절대 Git에 올라가지 않도록** 한다.

### 실행 단계

```bash
# 1. .env.example을 복사
cp .env.example .env

# 2. .env 파일을 열어 실제 발급받은 키 입력
# (아직 승인되지 않은 키는 빈 값으로 두거나 주석 처리)
```

`.env` 파일 예시:
```bash
TOUR_API_KEY=ABcd1234%2BEF...실제_발급된_키
WEATHER_API_KEY=XYz9876...
KAKAO_REST_API_KEY=abcd1234efgh5678...
KAKAO_MOBILITY_API_KEY=
OPENAI_API_KEY=sk-proj-...
```

### 검증
```bash
# .env가 git에 추적되지 않는지 확인 (중요!)
git check-ignore .env
# .env  ← 출력되어야 정상 (ignored)

# Python에서 로딩 테스트
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('TOUR_API_KEY loaded:', bool(os.getenv('TOUR_API_KEY')))"
# TOUR_API_KEY loaded: True
```

> ⚠️ **경고**: `.env`를 실수로 커밋했다면 즉시 [GitHub Secret 스캔 가이드](https://docs.github.com/en/code-security/secret-scanning)를 참고해 키를 **재발급**하세요. Git history에서 지워도 이미 노출된 키는 무효 처리해야 안전합니다.

---

## ▶️ 8. Step 7. Hello World 검증 👥

**실행 주체**: 팀원 전원

### 목표
Streamlit 앱이 정상 실행되는지 최종 확인.

### 실행 단계

```bash
streamlit run app.py
```

브라우저가 자동으로 `http://localhost:8501`를 열고, 다음 화면이 나타나야 합니다.

```
⚾ 원정 응원 플래너
Phase 0 bootstrap — 개발 준비 완료

[초록색 성공 박스]
환영합니다! 이 페이지가 보이면 환경 세팅이 성공한 것입니다.
```

### 검증 체크리스트
- [ ] 페이지 제목이 "원정 응원 플래너"로 표시됨
- [ ] 브라우저 탭 아이콘이 야구공(⚾)
- [ ] 초록색 성공 박스 메시지 표시
- [ ] 터미널에 에러 로그 없음

### 트러블슈팅
- **`streamlit: command not found`** → 가상환경 활성화 안 됨. `source venv/bin/activate` 재실행
- **포트 8501 이미 사용 중** → `streamlit run app.py --server.port 8502`
- **ModuleNotFoundError** → `pip install -r requirements.txt` 재실행

---

## ✅ 9. Step 8. 브랜치 전략 확립 🧑‍✈️

**실행 주체**: 팀장 1명

### 목표
Phase 1부터 팀원들이 각자 기능 브랜치에서 작업할 수 있도록 규칙을 정한다.

### 브랜치 네이밍 컨벤션
```
main              # 배포 브랜치 (보호됨)
develop           # 통합 브랜치 (선택)
feat/phase-1-data # 기능 브랜치
feat/phase-3-map
fix/sidebar-bug
```

### 커밋 메시지 컨벤션
```
feat(phase-1): add KBO schedule parser
fix(phase-3): correct folium marker color
docs: update README with deployment URL
chore: upgrade streamlit to 1.41
```

### GitHub 설정 (선택)
- Settings → Branches → Branch protection rules 추가
  - `main` 브랜치: require pull request before merging

---

## 📄 10. CLAUDE.md 전체 템플릿

Step 4에서 Claude Code가 생성한 결과가 마음에 들지 않으면 아래 템플릿을 수동으로 붙여넣어도 됩니다.

```markdown
# CLAUDE.md

이 파일은 Claude Code가 매 세션 자동으로 읽는 프로젝트 컨텍스트 문서입니다.

## 1. 프로젝트 요약

**원정 응원 플래너(Away Game Companion)** — KBO 10개 구단 원정 응원러를 위한
AI 기반 여행 플래너. 경기 선택 → 티켓·교통·맛집·숙소·관광지를 한 번에 제안.

- 주 사용자: MZ세대 프로야구 팬
- 플랫폼: Streamlit 웹 앱 (로컬 실행 + Streamlit Cloud 배포)
- 프로젝트 기간: 5일 (Day 4~5 집중 개발)

## 2. 기술 스택

- **언어**: Python 3.10+
- **프레임워크**: Streamlit 1.40+
- **데이터**: Pandas, scikit-learn
- **시각화**: Plotly, Folium (streamlit-folium)
- **AI/LLM**: OpenAI API (gpt-4o-mini), LangChain, ChromaDB
- **외부 API**:
  - 한국관광공사 TourAPI (관광·맛집·숙박)
  - 카카오 Maps Web API (지도)
  - 카카오모빌리티 (길찾기)
  - 기상청 단기예보
- **배포**: Streamlit Community Cloud

## 3. 디렉토리 맵

app.py                    # Streamlit 엔트리 포인트
src/
├── config.py             # 상수·경로 관리
├── data_loader.py        # CSV/API 통합 로더
├── api/                  # 외부 API 클라이언트
│   ├── tour_api.py
│   ├── kakao_map.py
│   └── weather_api.py
├── ui/
│   ├── sidebar.py
│   ├── hero.py
│   └── tabs/             # 5개 탭 각각 파일 분리
├── viz/
│   ├── folium_map.py
│   └── plotly_charts.py
└── ai/
    ├── agents.py         # Multi-Agent 오케스트레이션
    ├── tools.py          # Function Calling 도구
    ├── rag.py
    └── predict.py        # 승률 예측 모델
data/                     # CSV·POI 캐시
models/                   # 학습된 ML 모델

## 4. 코딩 컨벤션

- 함수·변수명: **snake_case**
- 클래스명: **PascalCase**
- 상수: **UPPER_SNAKE_CASE**
- 한글 주석 OK, docstring은 영어 또는 한국어 모두 허용
- 타입 힌트 적극 사용: `def load_data(path: str) -> pd.DataFrame:`
- 모든 외부 API 호출에는 `try-except` + 타임아웃 10초
- 로깅은 `print` 금지, `import logging` 사용
- Streamlit 데이터 로딩 함수에는 `@st.cache_data(ttl=3600)` 적용

## 5. 실행·테스트 명령

- 앱 실행: `streamlit run app.py`
- 테스트: `pytest tests/`
- 린트 (선택): `ruff check src/`
- 의존성 업데이트: `pip freeze > requirements.txt`

## 6. 금지사항 (DO NOT)

- ❌ API 키를 코드에 하드코딩하지 말 것. 반드시 `os.getenv()` 사용
- ❌ `.env`, `models/*.pkl`, `data/poi_cache/*.json`을 git에 커밋하지 말 것
- ❌ `pandas.read_csv()`를 Streamlit 렌더 함수 안에 직접 쓰지 말 것.
      항상 `@st.cache_data` 래퍼를 거칠 것
- ❌ `time.sleep()`을 UI 스레드에서 사용하지 말 것
- ❌ `st.experimental_*` API는 가급적 피하고 정식 API 사용

## 7. 현재 진행 Phase

**Phase 0 (Bootstrap)** — ✅ 완료

다음 Phase: Phase 1 (데이터 파이프라인 구축)
참고 문서: `IMPLEMENTATION_PLAN.md` Phase 1 섹션
```

---

## 🧾 11. 완료 체크리스트

### 팀장 🧑‍✈️
- [ ] GitHub 저장소 생성 완료
- [ ] 팀원 전원 Collaborator 추가
- [ ] Claude Code로 스캐폴딩 생성 및 push
- [ ] `CLAUDE.md` 작성 완료
- [ ] 브랜치 보호 규칙 설정 (선택)

### 팀원 전원 👥
- [ ] Python 3.10+ 설치 확인
- [ ] Git 설치 확인
- [ ] Claude Code 설치 확인
- [ ] 저장소 clone 완료
- [ ] 가상환경 생성 및 활성화
- [ ] `pip install -r requirements.txt` 성공
- [ ] `.env` 파일 생성 (최소 TourAPI 키 + OpenAI 키)
- [ ] `streamlit run app.py` 성공
- [ ] API 키 5종 전부 발급 또는 승인 대기 중

---

## 🆘 12. 트러블슈팅 FAQ

### Q1. Claude Code가 파일을 생성할 때 권한 오류가 납니다
디렉토리 소유권 문제일 가능성이 큽니다. `sudo chown -R $(whoami) .` 로 소유권을 현재 유저로 변경 후 재시도.

### Q2. 팀장이 push한 뒤 팀원이 pull 해도 파일이 안 보입니다
`git fetch origin && git reset --hard origin/main` 시도. 단, 로컬 변경사항이 날아가므로 주의.

### Q3. `.env` 파일을 실수로 커밋했어요
```bash
# 1. .env를 현재 버전부터 추적 해제
git rm --cached .env
git commit -m "chore: untrack .env"

# 2. 과거 commit에서도 지우려면 git-filter-repo 사용 (고급)
pip install git-filter-repo
git filter-repo --path .env --invert-paths

# 3. 무엇보다 중요: 노출된 API 키를 즉시 재발급
```

### Q4. TourAPI 승인이 안 오는데 먼저 개발을 시작해도 되나요?
Phase 1의 일부는 TourAPI 없이도 진행 가능합니다. KBO 경기일정 CSV와 구장 좌표부터 만들고, TourAPI 호출 부분은 **더미 JSON**으로 먼저 개발 후 나중에 교체하는 전략을 추천합니다. 더미 JSON 예시를 Claude Code에 요청하면 즉시 생성해줍니다.

### Q5. Streamlit 실행 시 방화벽 경고가 뜹니다
로컬 8501 포트를 허용해주세요. 보안상 문제 없습니다.

### Q6. CLAUDE.md는 언제 업데이트하나요?
Phase가 전환될 때마다 섹션 7 "현재 진행 Phase"만 업데이트하세요. 나머지는 구조 변경이 있을 때만.

---

## 🎬 13. 다음 Phase로 넘어가기 전 확인

다음 4가지가 모두 ✅이면 Phase 1 시작 준비 완료입니다.

1. ✅ 팀원 전원이 `streamlit run app.py` 성공
2. ✅ `CLAUDE.md`가 루트에 존재하고 Claude Code가 인식
3. ✅ 팀원 전원이 최소 1개 API 키 발급 완료 (TourAPI 우선)
4. ✅ `main` 브랜치에 Phase 0 스캐폴딩 커밋 완료

### Phase 1로 전환하는 Claude Code 프롬프트

````
Phase 0이 완료됐어. 이제 IMPLEMENTATION_PLAN.md의 Phase 1을 시작하려고 해.
CLAUDE.md의 "현재 진행 Phase"를 Phase 1로 업데이트하고, Phase 1의 첫 번째
작업인 "1-1. KBO 2026 경기일정 수집"을 진행해줘.

구체적 요구사항은 IMPLEMENTATION_PLAN.md Phase 1 섹션을 참고해.
````

---

## 📚 참고

- 프로젝트 전체 계획: [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md)
- 프로젝트 소개: [README.md](./README.md)
- Claude Code 공식 문서: https://docs.claude.com/en/docs/claude-code
- Streamlit 공식 문서: https://docs.streamlit.io/

---

*가이드 마지막 업데이트: 2026-04-17*
*예상 총 소요 시간: 30분 (팀원당 15~20분)*

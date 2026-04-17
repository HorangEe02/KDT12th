# 🎨 Phase 2 구현 가이드 — Streamlit + React 하이브리드 UI 골격

> **목표**: Streamlit 뼈대(사이드바·5개 탭)를 완성하고, 핵심 UI 3곳에 React 컴포넌트를 임베드하여 Streamlit만 쓴 앱과 차별화된 첫인상을 만든다.
> **실제 작업 시간**: 약 2.5시간 (Streamlit 90분 + React 60분)
> **대상 독자**: 프론트/UX 담당(주) + 팀장(React 지원)
> **전제 조건**: [Phase 1 가이드](./PHASE1_GUIDE.md) 완료, `scripts/validate_data.py` PASS

---

## 🎯 0. Phase 2 개요

### 완료 조건 (5가지 모두 참)
1. ✅ `streamlit run app.py` 실행 시 **사이드바 + 5개 탭** 모두 오류 없이 렌더링
2. ✅ 사이드바 필터 변경이 **`st.session_state["filters"]`에 즉시 반영**
3. ✅ React 히어로 섹션이 **선택된 팀 컬러로 동적 변경**
4. ✅ React 뱃지 위젯이 구장 컴플릿 진행률을 **SVG로 표시**
5. ✅ React 팀 로고 셀렉터가 **클릭 시 Streamlit 쿼리 파라미터를 업데이트**

---

## 🏗️ 1. 아키텍처 결정 — 읽고 넘어가기

이 Phase의 가장 중요한 결정은 **"Streamlit과 React를 어떻게 섞을 것인가"**입니다. 브레인스토밍 끝에 다음과 같이 결론이 났습니다.

### 🎯 Streamlit vs React 역할 분리 원칙

> **"데이터와 필터는 Streamlit, 인터랙션과 프레젠테이션은 React"**

| 영역 | 담당 | 이유 |
|---|---|---|
| 사이드바 필터, 버튼, 슬라이더 | Streamlit | `st.slider`, `st.selectbox`가 압도적으로 생산적 |
| 데이터 테이블, 차트 | Streamlit (Plotly) | Python 데이터 → 시각화가 자연스러움 |
| 챗봇 UI | Streamlit | `st.chat_message`로 충분 |
| **히어로 섹션** | **React** | 팀 컬러 애니메이션·그라디언트 |
| **뱃지 진행률 위젯** | **React** | SVG 기반 원형 프로그레스 |
| **팀 로고 셀렉터** | **React** | 로고 그리드 + 호버 인터랙션 |
| 지도 | Folium (Phase 3) | - |

### 🔧 React 통합 방식 — CDN + `st.components.v1.html()`

빌드 프로세스 없이 **단일 HTML 파일**로 React 컴포넌트를 작성합니다.

```html
<!-- assets/react/hero.html -->
<div id="root"></div>
<script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
<script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
<script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
<script type="text/babel">
  // JSX 여기에
</script>
```

**장점**: webpack 없음, npm 없음, JSX·Hooks 그대로 사용 가능.
**단점**: React → Python 실시간 통신은 제한적(쿼리 파라미터로 우회).

### 📁 추가되는 디렉토리 구조

```
assets/
├── css/
│   └── style.css
└── react/                    ← Phase 2에서 신규
    ├── hero.html
    ├── badges.html
    └── team_selector.html
src/ui/
├── components/               ← Phase 2에서 신규
│   ├── react_loader.py       ← React HTML을 Streamlit에 삽입하는 헬퍼
│   ├── hero.py
│   ├── badges.py
│   └── team_selector.py
├── sidebar.py
└── tabs/
    ├── tab1_games.py
    ├── tab2_map.py
    ├── tab3_places.py
    ├── tab4_ai.py
    └── tab5_badges.py
```

---

## 🧱 2. Step 1. app.py 메인 엔트리 리팩토링 (20분)

### 목표
Phase 0에서 만든 Hello World 수준의 `app.py`를 **프로덕션 구조**로 재작성한다.

### 🤖 Claude Code 프롬프트

````
app.py를 다음 구조로 리팩토링해줘. Phase 1의 data_loader와
Phase 2에서 만들 UI 모듈을 연결하는 메인 엔트리야.

### 요구사항

1. 페이지 설정
   - st.set_page_config(
         page_title="원정 응원 플래너",
         page_icon="⚾",
         layout="wide",
         initial_sidebar_state="expanded"
     )

2. CSS 주입
   - assets/css/style.css 파일을 읽어 <style>...</style>로 주입
   - 파일이 없으면 경고 없이 스킵

3. 세션 상태 초기화 (최상단)
   - "filters": {} (사이드바 필터 저장)
   - "selected_team": "LG" (기본값)
   - "messages": [] (Phase 4 챗봇용 미리 선언)
   - "visited_stadiums": [] (Phase 5 뱃지용)

4. 데이터 로딩
   - from src.data_loader import load_schedule, load_stadiums, load_team_stats
   - Phase 1의 @st.cache_data 덕에 자동 캐싱됨

5. 쿼리 파라미터 처리 (React 로고 셀렉터가 ?team=KT로 업데이트)
   - st.query_params에서 team 키 읽어서 st.session_state["selected_team"] 업데이트

6. UI 레이아웃
   - Hero 섹션 (React): src.ui.components.hero.render(selected_team)
   - 사이드바 렌더: src.ui.sidebar.render_sidebar()
   - st.tabs로 5개 탭 생성:
     ["⚾ 경기 & 예측", "🗺️ 동선 지도", "🍽️ 맛집·숙소",
      "🤖 AI 플래너", "🏅 내 뱃지"]
   - 각 탭 내부는 해당 모듈의 render() 함수 호출

7. 풋터
   - 데이터 출처, GitHub 링크, 팀 소개 markdown

### 구조 예시

```python
import streamlit as st
from src.data_loader import load_schedule, load_stadiums, load_team_stats
from src.ui.sidebar import render_sidebar
from src.ui.components import hero
from src.ui.tabs import tab1_games, tab2_map, tab3_places, tab4_ai, tab5_badges

st.set_page_config(...)

# CSS 주입
# 세션 초기화
# 쿼리 파라미터 처리
# Hero
# 사이드바
# 탭 5개

# Footer
```

모든 import는 상단에 정리하고, 각 섹션마다 한글 주석 한 줄로 용도 명시.
작성 후 streamlit run app.py 실행해 빈 탭들이 뜨는지 확인.
````

### 검증
```bash
streamlit run app.py
```

브라우저에서 5개 탭이 모두 보이고 클릭 시 전환되어야 합니다. 각 탭 내용은 아직 비어 있어도 OK.

---

## 🎛️ 3. Step 2. 사이드바 필터 구현 (30분)

### 목표
5종 필터를 Streamlit 위젯으로 구현하고, 결과를 `st.session_state["filters"]`에 dict로 저장한다.

### 🤖 Claude Code 프롬프트

````
src/ui/sidebar.py를 다음 명세로 작성해줘:

### Public 함수

```python
def render_sidebar() -> dict:
    """
    사이드바에 필터 위젯들을 렌더링하고,
    선택된 값을 dict로 반환 + st.session_state["filters"]에 저장.

    Returns:
        {
            "team": "LG",
            "date_range": (date(2026, 4, 17), date(2026, 4, 20)),
            "budget": 30,
            "party": "couple",
            "transport": "ktx",
        }
    """
```

### 위젯 목록

1. 응원팀 선택 (`st.selectbox`)
   - 옵션: src.config.TEAMS 10개
   - 기본값: st.session_state["selected_team"] (URL 쿼리 파라미터 연동)
   - 선택 변경 시 st.session_state["selected_team"] 업데이트

2. 원정 기간 (`st.date_input`)
   - 범위 선택 (value=(today, today+3일))
   - min_value=2026-03-28, max_value=2026-09-30

3. 예산 (`st.slider`)
   - 10~100, step=5, 단위 "만원"
   - 기본값 30

4. 인원 구성 (`st.radio`)
   - 선택지: ["혼자", "커플", "가족", "친구 그룹"]
   - 내부 값은 영어: ["solo", "couple", "family", "friends"]
   - format_func으로 한글 표시

5. 이동수단 (`st.radio`)
   - 선택지: ["🚄 KTX/SRT", "🚗 자차", "🚌 고속버스"]
   - 내부 값: ["train", "car", "bus"]

6. 하단에 "코스 생성" 버튼 (`st.button`, type="primary")
   - 클릭 시 st.session_state["generate_trigger"] = True
   - 이 플래그를 다른 탭에서 감지해 AI 호출 등 트리거

### 스타일링
- st.sidebar.header("🎽 원정 설정") 최상단
- 각 위젯 사이 st.sidebar.divider() 또는 여백

### 세션 저장
함수 마지막에 st.session_state["filters"] = {...}

작성 후 streamlit run app.py 실행해 사이드바 확인.
URL 쿼리 파라미터 ?team=KT로 접속 시 사이드바의 응원팀이 KT로
선택되어 있어야 함.
````

### 검증
- 사이드바에 5개 필터 위젯 + 1개 버튼 표시
- `http://localhost:8501/?team=KT` 접속 시 응원팀이 KT로 미리 선택됨
- 필터 변경 시 메인 영역 상단에 "현재 설정: ..." 확인 문구 표시 (임시)

---

## 📑 4. Step 3. 5개 탭 스캐폴딩 (20분)

### 목표
각 탭 모듈에 `render()` 함수만 정의하고, placeholder 내용으로 채운다. Phase 3·4에서 실제 콘텐츠를 채워 넣을 예정.

### 🤖 Claude Code 프롬프트

````
src/ui/tabs/ 아래 5개 파일에 각각 render(filters: dict) 함수를 구현해줘.
지금은 placeholder 내용이지만 실제 데이터 로딩은 해두고,
실제 UI 구현(지도·차트·챗봇)만 Phase 3/4에서 추가할 예정이야.

### tab1_games.py — 경기 & 예측

```python
def render(filters: dict):
    st.subheader("⚾ 원정 경기 & 승률 예측")
    
    from src.data_loader import load_schedule
    df = load_schedule()
    
    # filters["team"]이 원정팀인 경기만 필터
    away_games = df[df.away_team == filters["team"]]
    
    # date_range로 필터
    start, end = filters["date_range"]
    mask = (away_games.date >= pd.Timestamp(start)) & (away_games.date <= pd.Timestamp(end))
    filtered = away_games[mask]
    
    if len(filtered) == 0:
        st.info("선택한 기간에 원정 경기가 없습니다. 기간을 넓혀보세요.")
        return
    
    # 경기 리스트
    st.dataframe(filtered[["date", "day_of_week", "home_team", "stadium", "start_time"]],
                 use_container_width=True, hide_index=True)
    
    st.caption("📊 승률 예측과 우천 확률은 Phase 4에서 추가됩니다.")
```

### tab2_map.py — 동선 지도

```python
def render(filters: dict):
    st.subheader("🗺️ 원정 동선 지도")
    st.info("Phase 3에서 Folium 지도와 카카오모빌리티 경로가 추가됩니다.")
    
    # 임시로 구장 위치만 표시 예정임을 알림
    from src.data_loader import load_stadiums
    stadiums = load_stadiums()
    st.dataframe(stadiums[["short_name", "city", "lat", "lng"]],
                 use_container_width=True, hide_index=True)
```

### tab3_places.py — 맛집·숙소

```python
def render(filters: dict):
    st.subheader("🍽️ 경기장 주변 맛집·숙소")
    
    from src.data_loader import load_poi
    
    # filters["team"]의 이번 원정지 가정 (실제로는 선택된 경기 기반)
    # 임시로 첫 원정 경기의 stadium 사용
    st.info("선택된 원정 경기의 구장 주변 POI를 표시합니다. Phase 3에서 완성됩니다.")
    
    tabs = st.tabs(["🍽️ 음식점", "🏨 숙박", "🎡 관광지"])
    categories = ["food", "stay", "tour"]
    for tab, cat in zip(tabs, categories):
        with tab:
            st.write(f"{cat} placeholder — Phase 3에서 카드 UI로 구현")
```

### tab4_ai.py — AI 플래너

```python
def render(filters: dict):
    st.subheader("🤖 AI 원정 플래너")
    st.info("Phase 4에서 OpenAI 기반 챗봇과 Multi-Agent 시스템이 추가됩니다.")
    
    # 세션 메시지 미리 보기용 placeholder
    if st.session_state["messages"]:
        for msg in st.session_state["messages"]:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
    else:
        st.caption("아직 대화가 시작되지 않았습니다.")
```

### tab5_badges.py — 내 뱃지

```python
def render(filters: dict):
    st.subheader("🏅 나의 원정 컴플릿 현황")
    st.info("Phase 5에서 React 기반 뱃지 위젯이 추가됩니다.")
    
    from src.ui.components import badges
    badges.render(st.session_state["visited_stadiums"])
```

모든 파일 상단에 필요한 import 추가 (streamlit as st, pandas as pd 등).
작성 후 app.py에서 각 탭이 import되고 클릭 시 render가 호출되는지 확인.
````

### 검증
- 5개 탭 전환 시 오류 없음
- 탭 1: 실제 경기 데이터 표시
- 탭 2: 구장 테이블 표시
- 탭 3, 4, 5: placeholder 메시지 표시

---

## ⚛️ 5. Step 4. React 컴포넌트 1 — 히어로 섹션 (30분)

### 목표
**팀 컬러에 따라 그라디언트 배경이 바뀌는 랜딩 히어로**를 React + JSX로 구현하고 Streamlit에 임베드.

### 🤖 Claude Code 프롬프트 — React 컴포넌트

````
assets/react/hero.html을 만들어줘. 이 파일은 React 18 + Babel Standalone으로
JSX를 런타임 변환하는 단일 HTML 파일이야.

### 요구사항

1. CDN 3개 로드:
   - react@18 umd production
   - react-dom@18 umd production
   - @babel/standalone

2. window.APP_CONFIG 객체 참조:
   - team: "LG" | "KT" | ...
   - teamNameKo: "LG 트윈스"
   - color: "#C30452" (hex)
   - subColor: "#FFCC00"

3. HeroSection 컴포넌트:
   - div 하나, 높이 260px
   - 배경: linear-gradient(135deg, {color} 0%, {subColor} 100%)
   - 왼쪽에 큰 제목 "원정 응원 플래너"
   - 오른쪽 정렬로 선택된 팀명 표시
   - 야구공 이모지 ⚾를 CSS animation으로 좌우로 튀게
   - 전체 폰트: 'Pretendard', 'Noto Sans KR', sans-serif
   - 텍스트 색상: 흰색 또는 #FFFDF5
   - box-shadow와 border-radius로 카드 느낌

4. React Hooks 활용:
   - useState로 야구공 위치 state
   - useEffect로 3초마다 bounce 트리거

5. body { margin: 0; padding: 0; }
   - iframe 내부에서 scroll 방지

### 출력 전체 구조

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.css" rel="stylesheet">
  <style>
    body { margin: 0; padding: 0; font-family: 'Pretendard Variable', sans-serif; }
    .hero { /* ... */ }
    .ball { /* ... */ }
    @keyframes bounce { /* ... */ }
  </style>
</head>
<body>
  <div id="root"></div>
  <script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
  <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
  <script type="text/babel">
    const { useState, useEffect } = React;
    
    function HeroSection() {
      const config = window.APP_CONFIG || { team: "LG", color: "#C30452", ... };
      // ...
      return (
        <div className="hero" style={{ background: `linear-gradient(...)` }}>
          {/* ... */}
        </div>
      );
    }
    
    const root = ReactDOM.createRoot(document.getElementById('root'));
    root.render(<HeroSection />);
  </script>
</body>
</html>
```

### 디자인 가이드
- 미니멀하지만 활기찬 느낌
- 팀 컬러가 두드러지되 가독성 유지 (텍스트는 항상 흰색 + 약한 text-shadow)
- 반응형은 나중 문제, 데스크톱 900px 너비 기준으로만 맞추기

작성 후 브라우저에서 직접 열어 visual 확인 (Streamlit 통합 전).
````

### 🤖 Claude Code 프롬프트 — Streamlit 래퍼

````
src/ui/components/react_loader.py와 src/ui/components/hero.py를 만들어줘.

### src/ui/components/react_loader.py

React HTML 파일을 읽어 window.APP_CONFIG를 주입하고
st.components.v1.html로 렌더링하는 공통 헬퍼.

```python
from pathlib import Path
import json
import streamlit.components.v1 as components

ASSETS_DIR = Path(__file__).parent.parent.parent.parent / "assets" / "react"

def load_react_component(filename: str, config: dict, height: int = 260):
    """
    assets/react/{filename}을 읽어 APP_CONFIG를 주입하고 Streamlit에 렌더링.
    
    Args:
        filename: 예) "hero.html"
        config: React 컴포넌트에 전달할 데이터 dict
        height: iframe 높이 (px)
    """
    html_path = ASSETS_DIR / filename
    if not html_path.exists():
        # 파일이 없을 경우 fallback 메시지
        import streamlit as st
        st.warning(f"React 컴포넌트 {filename}이 아직 없습니다.")
        return
    
    html = html_path.read_text(encoding="utf-8")
    
    # </head> 직전에 APP_CONFIG 주입
    config_json = json.dumps(config, ensure_ascii=False)
    inject = f"<script>window.APP_CONFIG = {config_json};</script>"
    html = html.replace("</head>", f"{inject}</head>", 1)
    
    components.html(html, height=height, scrolling=False)
```

### src/ui/components/hero.py

```python
from src.ui.components.react_loader import load_react_component

# 팀별 컬러 팔레트
TEAM_COLORS = {
    "LG":   {"color": "#C30452", "subColor": "#FFCC00", "nameKo": "LG 트윈스"},
    "KT":   {"color": "#000000", "subColor": "#E5002D", "nameKo": "KT 위즈"},
    "SSG":  {"color": "#CE0E2D", "subColor": "#FFB81C", "nameKo": "SSG 랜더스"},
    "두산": {"color": "#131230", "subColor": "#ED1C24", "nameKo": "두산 베어스"},
    "KIA":  {"color": "#EA002C", "subColor": "#06141F", "nameKo": "KIA 타이거즈"},
    "NC":   {"color": "#315288", "subColor": "#A39161", "nameKo": "NC 다이노스"},
    "삼성": {"color": "#074CA1", "subColor": "#C0C0C0", "nameKo": "삼성 라이온즈"},
    "롯데": {"color": "#041E42", "subColor": "#ED1C24", "nameKo": "롯데 자이언츠"},
    "한화": {"color": "#FF6600", "subColor": "#000000", "nameKo": "한화 이글스"},
    "키움": {"color": "#570514", "subColor": "#B07F4A", "nameKo": "키움 히어로즈"},
}

def render(team: str = "LG"):
    palette = TEAM_COLORS.get(team, TEAM_COLORS["LG"])
    config = {
        "team": team,
        "teamNameKo": palette["nameKo"],
        "color": palette["color"],
        "subColor": palette["subColor"],
    }
    load_react_component("hero.html", config, height=260)
```

app.py에서 히어로 섹션 부분을 이 render 함수 호출로 교체.
작성 후 실행해서 Streamlit 앱 최상단에 팀 컬러 히어로가 뜨는지 확인.
````

### 검증
- 앱 최상단에 컬러풀한 히어로 섹션 표시
- 사이드바에서 팀 변경 → 히어로 배경 그라디언트 색상 변경
- 브라우저 개발자 도구에서 `window.APP_CONFIG` 확인 시 올바른 값 출력

---

## 🏅 6. Step 5. React 컴포넌트 2 — 뱃지 진행률 위젯 (30분)

### 목표
10개 구장 컴플릿 진행률을 **SVG 원형 프로그레스 바**로 시각화. 방문한 구장은 컬러, 미방문은 회색.

### 🤖 Claude Code 프롬프트

````
assets/react/badges.html과 src/ui/components/badges.py를 만들어줘.

### assets/react/badges.html

Hero와 같은 CDN 구조 사용. 다음 컴포넌트를 구현:

1. BadgeGrid 컴포넌트:
   - window.APP_CONFIG.stadiums: 10개 구장 배열
     [{name, short_name, visited: bool, color}]
   - window.APP_CONFIG.totalVisited: 숫자
   - 3열 그리드 (gap 16px)
   - 각 카드:
     - 원형 SVG 100x100
     - visited=true면 팀 컬러로 원 채우고 체크마크 ✓ 표시
     - visited=false면 회색 원 + 구장 이름만
     - 구장 이름 하단 표시
   - 상단에 "전국 원정 달성률: N/10 (N%)" 큰 텍스트
   - 10/10 달성 시 🎉 이모지 + 축하 메시지

2. Hooks 활용:
   - useState로 호버 상태 관리 (hover 시 살짝 scale)
   - useMemo로 달성률 계산

3. SVG 원형 프로그레스:
   - 외곽 원 (회색 stroke)
   - 내부 원 (팀 컬러 fill, visited일 때만)
   - transform: rotate(-90deg)로 12시 방향에서 시작

### src/ui/components/badges.py

```python
from src.ui.components.react_loader import load_react_component
from src.data_loader import load_stadiums
from src.ui.components.hero import TEAM_COLORS

def render(visited_stadiums: list[str]):
    """
    Args:
        visited_stadiums: 방문한 구장 short_name 리스트
                          예: ["잠실", "수원", "문학"]
    """
    stadiums_df = load_stadiums()
    
    stadiums = []
    for _, row in stadiums_df.iterrows():
        # 첫 번째 홈팀의 컬러 사용
        first_team = row["home_team"].split(",")[0]
        color = TEAM_COLORS.get(first_team, {"color": "#888888"})["color"]
        stadiums.append({
            "name": row["stadium_name"],
            "short_name": row["short_name"],
            "visited": row["short_name"] in visited_stadiums,
            "color": color,
        })
    
    config = {
        "stadiums": stadiums,
        "totalVisited": len(visited_stadiums),
    }
    load_react_component("badges.html", config, height=500)
```

### 데모용 초기 데이터
현재 session_state["visited_stadiums"]가 빈 리스트라 전부 회색으로 나올 거야.
tab5_badges.py에서 호출하기 전에 데모용으로 ["잠실", "수원", "문학"]을
임시 주입하는 코드를 추가해서 시각적 확인이 되도록 해.

(나중에 Phase 5에서 실제 사용자 방문 기록으로 교체)

작성 후 "내 뱃지" 탭에서 시각 확인.
````

### 검증
- 탭 5 진입 시 10개 구장 그리드 표시
- 데모 데이터로 3개 구장에 팀 컬러 원형 진행바 + 체크마크
- 나머지 7개는 회색 처리
- 상단에 "3/10 (30%)" 표시

---

## 🎽 7. Step 6. React 컴포넌트 3 — 팀 로고 셀렉터 (30분)

### 목표
`st.selectbox`보다 **시각적으로 풍부한 10개 팀 선택 UI**. 클릭 시 URL 쿼리 파라미터로 선택 상태 전달.

### 🤖 Claude Code 프롬프트

````
assets/react/team_selector.html과 src/ui/components/team_selector.py를 만들어줘.

### assets/react/team_selector.html

### 기능
- 10개 팀 로고 또는 팀 컬러 원형 배지 그리드 (5열 × 2행)
- 각 배지:
  - 크기 80×80
  - 배경: 팀 컬러
  - 중앙에 팀 약칭 (LG, KT, ...)
  - 폰트: 흰색 bold
  - 호버 시 scale(1.1) + box-shadow
- 현재 선택된 팀은 2px 검정 테두리
- 클릭 시:
  - parent.postMessage({ type: "TEAM_SELECTED", team: "KT" }, "*") 전송
  - URL 업데이트: parent.location.href = "?team=KT" (iframe 최상위)
  - Streamlit은 URL 변경 감지해 rerun

### Streamlit 연동 주의사항
iframe 내부에서 parent.location 변경은 보안 정책상 막힐 수 있어.
대안으로 window.top.postMessage + Streamlit의 query_params 설정 우회가 어려우니,
가장 간단하게 앵커 링크 <a href="?team=KT" target="_top">로 처리하자.

### JSX 구조

```jsx
function TeamSelector() {
  const teams = window.APP_CONFIG.teams;  // [{code, nameKo, color}]
  const selected = window.APP_CONFIG.selected;
  
  return (
    <div className="grid">
      {teams.map(t => (
        <a
          key={t.code}
          href={`?team=${t.code}`}
          target="_top"
          className={`badge ${t.code === selected ? 'selected' : ''}`}
          style={{ background: t.color }}
        >
          {t.code}
        </a>
      ))}
    </div>
  );
}
```

### src/ui/components/team_selector.py

```python
from src.ui.components.react_loader import load_react_component
from src.ui.components.hero import TEAM_COLORS
from src.config import TEAMS

def render(selected_team: str = "LG"):
    teams = []
    for code in TEAMS:
        palette = TEAM_COLORS.get(code, {"color": "#888888", "nameKo": code})
        teams.append({
            "code": code,
            "nameKo": palette["nameKo"],
            "color": palette["color"],
        })
    
    config = {
        "teams": teams,
        "selected": selected_team,
    }
    load_react_component("team_selector.html", config, height=220)
```

### 통합
app.py 히어로 섹션과 사이드바 사이에 team_selector.render(selected_team)를 추가.
이렇게 하면 사용자는 두 가지 방법으로 팀 선택 가능:
1. 사이드바 selectbox (Streamlit)
2. 상단 로고 그리드 (React)
둘 다 결과적으로 st.session_state["selected_team"] 업데이트.

작성 후 로고 클릭 시 URL이 ?team=KT로 바뀌고 히어로·사이드바도 함께 갱신되는지 확인.
````

### 검증
- 메인 영역에 10개 팀 로고 그리드 표시
- 로고 클릭 시 URL이 `?team=XX`로 변경되며 페이지 리로드
- 리로드 후 히어로·사이드바·선택된 로고 테두리 모두 동일 팀으로 통일

---

## 🔄 8. Step 7. Streamlit ↔ React 통신 패턴 확립

### 현재까지의 통신 구조

```
┌─────────────────┐  APP_CONFIG (JSON)  ┌──────────────┐
│   Streamlit     │ ─────────────────► │  React (CDN)  │
│   (Python)      │                    │  (JSX)        │
│                 │ ◄───────────────── │               │
└─────────────────┘  URL query params  └──────────────┘
```

### 3가지 통신 시나리오

| 방향 | 방법 | 예시 |
|---|---|---|
| Python → React | `window.APP_CONFIG` 주입 | 팀 컬러 전달 |
| React → Python (상태 변경) | 쿼리 파라미터 + rerun | 팀 로고 클릭 |
| React → Python (단순 이벤트) | 현재 불가 (Custom Component 필요) | - |

### 한계와 대안

양방향 실시간 통신이 필요한 경우(예: React에서 슬라이더 움직임을 Python에 실시간 전달) 이 방식으로는 불가능합니다. 그때는 **Streamlit Custom Component(빌드 필요)** 또는 **Streamlit의 `st.experimental_get_query_params` + JavaScript `history.pushState` 조합**을 쓸 수 있지만, 이 프로젝트에서는 **쿼리 파라미터 수준의 통신으로 충분**합니다.

---

## 🔍 9. Step 8. 검증 & 시연 준비

### 자동 검증 스크립트

`scripts/validate_phase2.py`를 만들어 다음을 확인:

### 🤖 Claude Code 프롬프트

````
scripts/validate_phase2.py를 만들어줘. Phase 2 완료 조건을 자동 체크.

### 검증 항목

1. 파일 존재
   - app.py
   - src/ui/sidebar.py
   - src/ui/tabs/ 5개 파일
   - src/ui/components/react_loader.py
   - src/ui/components/hero.py, badges.py, team_selector.py
   - assets/react/hero.html, badges.html, team_selector.html
   - assets/css/style.css (빈 파일이라도 OK)

2. 정적 분석
   - app.py가 5개 탭 모듈을 모두 import하는지 (AST 파싱)
   - 각 탭 모듈에 render 함수가 정의돼 있는지
   - React HTML 파일들에 window.APP_CONFIG 참조 코드가 있는지

3. 실행 smoke test
   - subprocess로 streamlit run app.py --server.headless true를 짧게 실행
   - 3초 후 kill, 그 사이 에러 로그 있으면 FAIL
   - (선택적, 복잡하면 생략 가능)

### 출력 형식

PHASE 1의 validate_data.py와 동일한 스타일로.
[PASS]/[FAIL] + 마지막에 종합 판정.
````

### 수동 시연 체크리스트

- [ ] 앱 첫 화면: 히어로 섹션 (LG 컬러 자홍/노랑 그라디언트)
- [ ] 팀 로고 셀렉터에서 "KT" 클릭 → 히어로가 검정/빨강으로 변경
- [ ] 사이드바 "응원팀"이 KT로 동기화됨
- [ ] 사이드바 "원정 기간" 변경 → 탭 1의 경기 리스트 갱신
- [ ] 탭 5 "내 뱃지" → 10개 구장 그리드, 3개는 컬러 (데모 데이터)
- [ ] 모든 탭 전환 시 에러 없음

### 스크린샷 촬영
발표 자료용으로 **3종 스크린샷**을 찍어 `assets/screenshots/`에 저장:
1. 전체 화면 (히어로 + 사이드바 + 탭 1)
2. 뱃지 탭 (10구장 그리드)
3. 팀 변경 전/후 비교 (히어로 컬러 전환)

---

## 👥 10. 병렬 작업 가이드

데이터 엔지니어가 Phase 1을 마무리하고 프론트/UX 담당이 Phase 2를 진행하는 동안, 다른 팀원은:

### 🗺️ 지도 / 시각화 담당
- Phase 3 준비: streamlit-folium 튜토리얼 완주, 잠실 구장 마커 하나 찍어보기
- 카카오모빌리티 API 문서 정독 및 샘플 호출 테스트
- Plotly로 `team_stats_10yr.csv`를 읽어 막대그래프 프로토타입

### 🤖 AI / 분석 담당
- `src/ai/predict.py` 초안: scikit-learn 로지스틱 회귀 학습 코드 작성
  - Phase 1의 `team_stats_10yr.csv` 활용
  - 피처: 홈팀 win_rate, 원정팀 win_rate, 홈어드밴티지
- OpenAI API "Hello, 원정 응원" 테스트 호출
- Phase 4 챗봇 system prompt 초안 Markdown 파일로 정리

### 🧑‍✈️ 팀장
- Phase 3·4·5 가이드 문서 초안 작성
- 발표 자료 템플릿 구성 (10장 슬라이드 skeleton)
- Streamlit Community Cloud 계정 생성 및 배포 테스트 (Phase 0 헬로월드 기준)

---

## 🧾 11. 완료 체크리스트

### Streamlit 뼈대 (필수)
- [ ] `app.py` 리팩토링 완료 (페이지 설정·CSS·세션·5개 탭)
- [ ] `src/ui/sidebar.py` 5종 필터 구현
- [ ] `src/ui/tabs/` 5개 탭 스캐폴딩 (render 함수 모두 정의)
- [ ] 쿼리 파라미터 처리 로직 작동

### React 컴포넌트 (우선순위 순)
- [ ] 히어로 섹션 (`hero.html` + `hero.py`) ⭐ 필수
- [ ] 뱃지 위젯 (`badges.html` + `badges.py`) ⭐ 필수
- [ ] 팀 로고 셀렉터 (`team_selector.html` + `team_selector.py`) 권장
- [ ] React ↔ Streamlit 통신 검증 완료

### 공통
- [ ] `react_loader.py` 공통 헬퍼 작성
- [ ] `scripts/validate_phase2.py` 전부 PASS
- [ ] 수동 시연 체크리스트 전부 ✅
- [ ] 스크린샷 3종 촬영 완료
- [ ] Git push 완료

---

## 🆘 12. 트러블슈팅 FAQ

### Q1. React 컴포넌트가 빈 화면으로 뜹니다
**원인 1**: Babel이 JSX를 못 찾음. `<script type="text/babel">` 태그가 맞는지 확인.
**원인 2**: CDN 로딩 실패. 브라우저 DevTools → Network 탭에서 react/react-dom/babel이 200 응답인지 확인.
**원인 3**: `window.APP_CONFIG`가 컴포넌트 실행 시점에 정의 안 됨. `<head>`에 주입했는지 확인.

### Q2. 사이드바의 `selectbox`와 React 로고 셀렉터가 서로 동기화가 안 됩니다
현재 구현은 **URL 쿼리 파라미터를 단일 진실원**으로 사용합니다. 두 컴포넌트 모두 `st.session_state["selected_team"]`을 참조하고, 변경은 `st.query_params["team"] = value`로 통일하세요. 이 규칙을 깨면 동기화가 끊깁니다.

### Q3. React 컴포넌트 높이가 잘립니다
`st.components.v1.html(html, height=HERE)`의 height를 충분히 크게. 콘텐츠가 300px인데 height=200을 주면 스크롤 없이 잘립니다. 반대로 너무 크면 빈 공간이 생기니 콘텐츠 예상 높이 + 20px 정도가 적당합니다.

### Q4. URL 쿼리 파라미터 변경해도 Streamlit이 반응 안 함
`target="_top"`으로 최상위 프레임에서 링크 이동해야 합니다. `target="_self"` 또는 생략하면 iframe 내부만 바뀝니다.

### Q5. 팀 로고 클릭했더니 iframe이 전체 화면을 차지해요
위와 반대 상황. `href="?team=KT"`에서 `?`가 누락되거나, 절대 URL이 들어갔을 수 있습니다. 상대 URL + 쿼리만 주세요.

### Q6. Babel 변환이 느려서 로딩이 오래 걸립니다
개발 중엔 OK지만 배포 시에는 **프로덕션 빌드**로 바꾸는 게 좋습니다. 단, 이번 프로젝트는 시연 위주라 Babel Standalone으로도 충분합니다. 로컬에서 첫 로딩 1~2초 지연은 무시 가능.

### Q7. React 컴포넌트에서 CSS가 Streamlit 전체로 번집니다
`st.components.v1.html()`은 자동으로 **iframe에 격리**되므로 번지지 않습니다. 만약 번진다면 `components.html` 대신 `st.markdown(unsafe_allow_html=True)`를 쓴 건 아닌지 확인.

### Q8. 모바일 브라우저에서 깨져요
이번 프로젝트는 데스크톱 900px 이상 기준입니다. 모바일 대응은 Phase 5 여력이 있으면 진행, 아니면 발표 시 "데스크톱 권장" 고지.

---

## 🎬 13. 다음 Phase로 넘어가기 전 확인

다음 5가지가 ✅이면 Phase 3 시작 준비 완료.

1. ✅ `scripts/validate_phase2.py` 종료 코드 **0**
2. ✅ 시연 체크리스트 모든 항목 작동
3. ✅ React 3개 컴포넌트가 iframe으로 정상 렌더링
4. ✅ 사이드바 필터 값이 `st.session_state["filters"]`에 저장됨을 개발자 도구로 확인
5. ✅ `CLAUDE.md` "현재 진행 Phase"가 **Phase 3**으로 업데이트

### Phase 3로 전환하는 Claude Code 프롬프트

````
Phase 2 Streamlit + React 하이브리드 UI 골격이 완료됐어.
scripts/validate_phase2.py 실행해서 모두 PASS인지 확인.

통과했다면:
1. CLAUDE.md의 "현재 진행 Phase"를 Phase 3으로 업데이트
2. IMPLEMENTATION_PLAN.md Phase 3 섹션 참고
3. 첫 작업 "3-1. Folium 지도 컴포넌트"를 src/viz/folium_map.py에 구현
4. Phase 1의 stadiums.csv와 poi_cache를 활용해
   경기장·맛집·숙소·관광지 4개 레이어 지도를 만들어줘
5. src/ui/tabs/tab2_map.py의 placeholder를 실제 지도 렌더링으로 교체

실패 항목이 있으면 먼저 해결 후 진행.
````

---

## 📚 참고

- 전체 계획: [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) Phase 2 섹션
- 이전 가이드: [PHASE0_GUIDE.md](./PHASE0_GUIDE.md), [PHASE1_GUIDE.md](./PHASE1_GUIDE.md)
- Streamlit Components: https://docs.streamlit.io/library/components
- React CDN 방식 공식 문서: https://react.dev/learn/add-react-to-an-existing-project#using-react-for-a-part-of-your-existing-page
- Babel Standalone: https://babeljs.io/docs/babel-standalone

---

*가이드 마지막 업데이트: 2026-04-17*
*예상 총 소요 시간: 2.5시간 (Streamlit 90분 + React 60분)*

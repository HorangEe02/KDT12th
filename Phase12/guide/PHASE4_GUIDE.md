# 🤖 Phase 4 구현 가이드 — AI 기능 구현 with Claude Code

> **목표**: 승률 예측 ML 모델 + LLM 챗봇 + Function Calling 도구 호출 + Multi-Agent 오케스트레이션 + Agentic RAG를 점진 구현한다.
> **실제 작업 시간**: 약 3시간 (MVP 90분 + 고도화 90분)
> **대상 독자**: AI/분석 담당(주) + 데이터 엔지니어(지원)
> **전제 조건**: [Phase 3 가이드](./PHASE3_GUIDE.md) 완료, OpenAI 또는 Gemini API 키 발급 완료

---

## ⚠️ 시작 전 필독 — 이 Phase가 특별한 이유

Phase 4는 다른 Phase와 **세 가지 근본적 차이**가 있습니다.

**① 비결정성**: LLM은 같은 입력에도 다른 출력을 줍니다. 일관된 시연이 어렵습니다.
**② 비용 누적**: API 호출마다 과금됩니다. 개발 중 부주의하면 $10~30이 쉽게 나갑니다.
**③ 외부 의존성**: 네트워크·API 상태에 시연이 좌우됩니다. 발표 당일 장애 위험.

따라서 이 Phase는 **"구현했다 vs 안정적으로 시연 가능하다"** 사이 간극이 큽니다. 가이드 전체에 안전장치를 다중으로 심어뒀으니, **Step 9 (시연 안전장치)를 반드시 끝까지 읽고 시작하세요.**

---

## 🎯 0. Phase 4 개요 & 우선순위

### ⏰ 시간대별 컷오프 지점 — 어디까지 할지 미리 정하기

```
00:00 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  시작
          [Step 1. 승률 예측 모델] (30분)
00:30 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          [Step 2. LLM 클라이언트] (20분)
00:50 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          [Step 3. 기본 챗봇] (30분)
          [Step 4. 프롬프트 엔지니어링] (10분)
01:30 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ⭐ MVP 완료 체크포인트
          ✅ 여기까지만 해도 과제 요구사항 충족
          [Step 5. Function Calling 도구 5종] (45분)
02:15 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          [Step 6. 도구 호출 시각화 UI] (15분)
02:30 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 🎯 권장 완료 지점
          [Step 7. Multi-Agent 순차 호출] (30분)
03:00 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 🏆 풀 스펙 완료
          [Step 8. Agentic RAG 프로토타입] (30분, 시간 남으면)
03:30 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 완료 조건 우선순위

| 등급 | 완료 조건 | 판정 |
|---|---|---|
| **필수 (MVP)** | 탭 1 경기 카드에 실제 모델 예측 승률 표시 | ☐ |
| **필수 (MVP)** | 탭 4에서 자연어 질문 → LLM 답변 생성 | ☐ |
| **강력 권장** | LLM이 필터 정보 기반으로 맥락 있는 답변 | ☐ |
| **강력 권장** | LLM이 Function Calling으로 도구 최소 2개 호출 | ☐ |
| **권장** | 도구 호출 과정이 UI에 노출 (expander) | ☐ |
| **선택** | 5개 도구 전부 연동 (Multi-Agent 느낌) | ☐ |
| **선택** | RAG로 원정 팁 검색 작동 | ☐ |

---

## 🏗️ 1. 아키텍처 결정 박스 — 읽고 시작

### 🧠 LLM 제공자 선택 — 이중화

```python
# src/ai/llm_client.py의 핵심 로직
try:
    response = call_openai(...)
except (OpenAIError, Timeout):
    logger.warning("OpenAI 실패, Gemini로 전환")
    response = call_gemini(...)
except Exception:
    logger.error("모든 LLM 실패, 규칙 기반 응답")
    response = fallback_response(...)
```

### 💰 비용 관리 원칙

- **기본 모델**: `gpt-4o-mini` ($0.15 / 1M input, $0.60 / 1M output)
- **대화 히스토리**: 최근 **10턴만** 유지 (오래된 건 요약 또는 드롭)
- **시스템 프롬프트**: 300단어 이내
- **개발 단계 예산**: 팀 전체 **$5 이내** (Gemini 무료 티어로 대체 가능)

### 🛡️ 3단계 Fallback

| 레벨 | 조건 | 동작 |
|---|---|---|
| 1차 | OpenAI 타임아웃/에러 | Gemini로 자동 전환 |
| 2차 | 모든 LLM 실패 | 규칙 기반 더미 응답 + 사용자에게 안내 |
| 3차 | 발표 당일 네트워크 장애 | **사전 녹화 영상 재생** |

### 📐 Multi-Agent 현실 타협

> **"LangGraph 공식 Multi-Agent" 대신 "OpenAI tool_use 기반 순차 호출" 패턴 사용**

구현 난이도는 낮추되, 사용자 경험은 동일. 발표 슬라이드에는 LangGraph 아키텍처 다이어그램을 포함하되 실제 구현은 순차 호출.

### 📁 추가되는 파일 구조

```
src/ai/
├── llm_client.py              # OpenAI + Gemini 이중화
├── predict.py                 # 승률 예측 모델 (scikit-learn)
├── prompts.py                 # 시스템 프롬프트 상수
├── tools.py                   # Function Calling 도구 정의
├── agents.py                  # 순차 도구 호출 오케스트레이터
├── rag.py                     # ChromaDB 기반 지식 검색 (선택)
└── mock_responses.py          # 시연 안전장치 — 녹화된 응답

models/
└── win_rate_model.pkl

data/
└── knowledge/                 # RAG용 더미 지식 (선택)
    └── away_game_tips.json
```

---

## 🎯 2. Step 1. 승률 예측 모델 (30분, MVP 필수)

### 목표
`team_stats_10yr.csv`를 학습 데이터로 로지스틱 회귀 모델 학습 → `win_rate_model.pkl` 저장 → Phase 3의 더미 `win_prob` 교체.

### 🤖 Claude Code 프롬프트

````
src/ai/predict.py를 다음 명세로 작성해줘.

### 목적
scikit-learn 로지스틱 회귀로 원정 경기 승률 예측 모델을 학습하고 저장.

### 학습 데이터 구성

data/team_stats_10yr.csv를 로드해 다음 구조의 학습 샘플 생성:

각 행은 "A팀 vs B팀 대결" 가상 샘플:
- 피처:
  - team_win_rate: 예측하려는 팀의 해당 연도 전체 승률
  - opponent_win_rate: 상대팀 해당 연도 전체 승률
  - team_away_win_rate: 예측 팀의 원정 승률
  - opponent_home_win_rate: 상대팀 홈 승률
  - win_rate_diff: team_win_rate - opponent_win_rate
- 타겟:
  - won (0/1): team_away_win_rate > 0.5면 1, 아니면 0
  (이진 분류로 단순화)

연도별 × 팀 쌍을 만들어 약 1,000~5,000개 샘플 생성.

### Public 함수

```python
def train_model(save_path: str = "models/win_rate_model.pkl") -> dict:
    """
    모델 학습 및 저장.
    
    Returns:
        {
            "accuracy": float,
            "n_samples": int,
            "feature_names": list[str],
        }
    """

def load_model(path: str = "models/win_rate_model.pkl"):
    """모델 로드, 파일 없으면 FileNotFoundError"""

def predict_win_rate(
    team: str,
    opponent: str,
    team_stats_df: pd.DataFrame,
    model=None,
) -> float:
    """
    원정 팀 기준 승률 예측.
    
    Args:
        team: 원정 팀 약칭 (예: "LG")
        opponent: 홈 팀 약칭 (예: "KT")
        team_stats_df: load_team_stats() 결과
        model: None이면 load_model() 호출
    
    Returns:
        승률 확률 (0.0 ~ 1.0)
        피처 계산 불가(과거 기록 없음) 시 0.45 반환 (약간 불리한 원정 가정)
    """
```

### 학습 코드 요구사항

1. sklearn.linear_model.LogisticRegression 사용
2. sklearn.preprocessing.StandardScaler로 피처 스케일링
3. Pipeline으로 Scaler + Model 묶어 pkl로 저장
4. train_test_split 80/20, random_state=42
5. accuracy_score로 평가 및 print

### 실행부

```python
if __name__ == "__main__":
    result = train_model()
    print(f"✅ 모델 학습 완료: {result}")
    
    # 테스트 예측
    from src.data_loader import load_team_stats
    stats = load_team_stats()
    prob = predict_win_rate("LG", "KT", stats)
    print(f"LG vs KT 원정 승률: {prob:.2%}")
```

### 주의사항
- 승률 데이터는 확률적 특성이 강해 정확도가 55~65%면 정상
- 과적합 방지를 위해 L2 정규화 활용 (기본값)
- 절대 90%+ 정확도 나오면 데이터 누수 의심하고 점검

작성 후 python -m src.ai.predict 실행해 모델 저장 확인.
````

### Phase 3 `tab1_games.py` 교체

더미 `win_prob` → 실제 예측값으로 교체:

```python
# 기존
import random
random.seed(...)
win_prob = round(random.uniform(0.35, 0.65), 2)

# 신규
from src.ai.predict import load_model, predict_win_rate
model = load_model()
win_prob = predict_win_rate(filters["team"], selected_game.home_team, stats, model)
```

### 검증
```bash
python -m src.ai.predict
# 출력: ✅ 모델 학습 완료: {'accuracy': 0.58, ...}
# LG vs KT 원정 승률: 45.32%

ls -lh models/win_rate_model.pkl   # 파일 생성 확인
```

탭 1에서 게이지 값이 변경되었는지 브라우저에서 확인.

---

## 🔌 3. Step 2. LLM 클라이언트 이중화 (20분)

### 목표
OpenAI·Gemini 어느 쪽이든 동일 인터페이스로 호출할 수 있는 래퍼 모듈 작성. 이게 **이후 Step 3~7 전체의 기반**이 됩니다.

### 🤖 Claude Code 프롬프트

````
src/ai/llm_client.py를 다음 명세로 작성해줘.

### 목적
OpenAI GPT-4o-mini를 기본으로, 실패 시 Google Gemini Flash로 자동 전환.
둘 다 실패하면 규칙 기반 fallback 응답.

### 의존성
```
openai>=1.30
google-generativeai>=0.5
```
requirements.txt에 추가 필요.

### 환경변수
- OPENAI_API_KEY (주)
- GEMINI_API_KEY (보조, 없어도 됨)

### Public 함수

```python
def chat_complete(
    messages: list[dict],
    tools: list[dict] | None = None,
    stream: bool = False,
    temperature: float = 0.7,
    max_tokens: int = 800,
) -> dict:
    """
    OpenAI 호환 메시지 포맷으로 LLM 호출.
    
    Args:
        messages: [{"role": "system"|"user"|"assistant", "content": "..."}]
        tools: OpenAI tool_use 스키마 (Step 5에서 사용)
        stream: True면 제너레이터 반환
        temperature, max_tokens: 표준 파라미터
    
    Returns:
        {
            "content": "생성된 텍스트",
            "tool_calls": [...] | None,   # tools 사용 시
            "model": "gpt-4o-mini" | "gemini-1.5-flash" | "fallback",
            "usage": {"input_tokens": N, "output_tokens": M},
        }
    """
```

### 내부 구현

```python
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_OPENAI_CLIENT = None
_GEMINI_CLIENT = None

def _get_openai():
    global _OPENAI_CLIENT
    if _OPENAI_CLIENT is None:
        from openai import OpenAI
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            return None
        _OPENAI_CLIENT = OpenAI(api_key=key)
    return _OPENAI_CLIENT

def _get_gemini():
    # 동일 패턴
    ...

def _call_openai(messages, tools, stream, temperature, max_tokens) -> dict:
    client = _get_openai()
    if client is None:
        raise RuntimeError("OPENAI_API_KEY 없음")
    
    kwargs = {
        "model": "gpt-4o-mini",
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"
    
    response = client.chat.completions.create(**kwargs, timeout=20)
    msg = response.choices[0].message
    
    return {
        "content": msg.content or "",
        "tool_calls": [
            {
                "id": tc.id,
                "name": tc.function.name,
                "arguments": json.loads(tc.function.arguments),
            }
            for tc in (msg.tool_calls or [])
        ] if msg.tool_calls else None,
        "model": "gpt-4o-mini",
        "usage": {
            "input_tokens": response.usage.prompt_tokens,
            "output_tokens": response.usage.completion_tokens,
        },
    }

def _call_gemini(messages, tools, stream, temperature, max_tokens) -> dict:
    # Gemini API 호출 (tools 미지원 시 단순 텍스트만)
    # 간단 구현: Gemini에 tools 전달 시 텍스트 응답으로 fallback
    ...

def _fallback_response(messages) -> dict:
    """모든 LLM 실패 시 규칙 기반 응답"""
    user_msg = messages[-1]["content"].lower() if messages else ""
    
    responses = {
        "안녕": "안녕하세요! AI 플래너가 잠시 연결 문제를 겪고 있어요. 잠시 후 다시 시도해 주세요.",
        "추천": "죄송해요, AI 서비스가 일시적으로 응답하지 않네요. 좌측 탭에서 직접 경기와 맛집을 탐색해보세요.",
    }
    
    for keyword, resp in responses.items():
        if keyword in user_msg:
            return {"content": resp, "tool_calls": None, "model": "fallback", "usage": {"input_tokens": 0, "output_tokens": 0}}
    
    return {
        "content": "AI 서비스가 일시적으로 응답하지 않습니다. 잠시 후 다시 시도해 주세요.",
        "tool_calls": None, "model": "fallback",
        "usage": {"input_tokens": 0, "output_tokens": 0},
    }

def chat_complete(messages, tools=None, stream=False, temperature=0.7, max_tokens=800):
    # 1차: OpenAI
    try:
        return _call_openai(messages, tools, stream, temperature, max_tokens)
    except Exception as e:
        logger.warning(f"OpenAI 실패: {e}, Gemini로 전환")
    
    # 2차: Gemini
    try:
        return _call_gemini(messages, tools, stream, temperature, max_tokens)
    except Exception as e:
        logger.warning(f"Gemini 실패: {e}, fallback 응답")
    
    # 3차: 규칙 기반
    return _fallback_response(messages)
```

### 테스트
```python
if __name__ == "__main__":
    response = chat_complete([
        {"role": "system", "content": "당신은 KBO 원정 응원 전문가입니다."},
        {"role": "user", "content": "안녕하세요!"},
    ])
    print(f"Model: {response['model']}")
    print(f"Content: {response['content']}")
    print(f"Tokens: {response['usage']}")
```

작성 후 python -m src.ai.llm_client 실행해 Hello World 응답 확인.
Gemini 구현은 기본 텍스트 호출만 지원하는 간소화 버전으로 충분.
````

### 검증
```bash
python -m src.ai.llm_client
# 출력 예시:
# Model: gpt-4o-mini
# Content: 안녕하세요! 원정 응원 계획을 도와드릴게요...
# Tokens: {'input_tokens': 25, 'output_tokens': 18}
```

---

## 💬 4. Step 3. 기본 LLM 챗봇 구현 — **⭐ MVP 컷오프 지점**

### 목표
탭 4에서 `st.chat_input` → LLM 호출 → 스트리밍 응답 표시. 대화 기록 session_state에 유지.

**이 Step 완료 시점이 "MVP 작동"입니다. 시간이 1:30을 넘었다면 여기서 멈추고 시연 준비로 넘어가세요.**

### 🤖 Claude Code 프롬프트

````
src/ui/tabs/tab4_ai.py를 다음 명세로 완성해줘.

### 구조

```python
import streamlit as st
from src.ai.llm_client import chat_complete
from src.ai.prompts import build_system_prompt  # Step 4에서 만들 예정, 지금은 임시

def render(filters: dict):
    st.subheader("🤖 AI 원정 플래너")
    st.caption("자연어로 원정 계획을 물어보세요. 예: '광주 1박 2일, 아이와 함께 갈 건데 추천해줘'")
    
    # 대화 초기화 버튼
    col_reset, col_model = st.columns([3, 1])
    with col_reset:
        if st.button("🗑️ 대화 초기화", type="secondary"):
            st.session_state["messages"] = []
            st.rerun()
    with col_model:
        st.caption(f"Model: {st.session_state.get('last_model', '—')}")
    
    st.divider()
    
    # 기존 대화 렌더링
    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # 사용자 입력
    user_input = st.chat_input("원정 계획을 알려드릴게요!")
    if user_input:
        # 사용자 메시지 추가 및 렌더링
        st.session_state["messages"].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # 시스템 프롬프트 + 최근 10턴만 유지
        system_prompt = build_system_prompt(filters)
        recent = st.session_state["messages"][-10:]
        messages = [{"role": "system", "content": system_prompt}] + recent
        
        # AI 응답 생성
        with st.chat_message("assistant"):
            with st.spinner("AI가 생각 중..."):
                response = chat_complete(messages, temperature=0.7, max_tokens=600)
            
            st.markdown(response["content"])
            
            # 모델 정보 노출
            st.session_state["last_model"] = response["model"]
            if response["model"] == "fallback":
                st.warning("⚠️ AI 서비스 연결 문제로 규칙 기반 응답입니다.")
        
        # 세션에 저장
        st.session_state["messages"].append({
            "role": "assistant",
            "content": response["content"],
        })
        
        st.rerun()
    
    # 빈 대화 시 예시 프롬프트 버튼
    if not st.session_state["messages"]:
        st.markdown("### 💡 예시 질문")
        col1, col2, col3 = st.columns(3)
        examples = [
            "광주 원정 1박 2일, 아이랑 가려는데 추천해줘",
            "이번 주말 부산 맛집 세 곳 알려줘",
            "비 올 확률 높으면 실내 관광지는?",
        ]
        for col, ex in zip([col1, col2, col3], examples):
            with col:
                if st.button(ex, use_container_width=True):
                    st.session_state["messages"].append({"role": "user", "content": ex})
                    st.rerun()
```

### src/ai/prompts.py 임시 구현 (Step 4에서 확장)

```python
def build_system_prompt(filters: dict) -> str:
    team = filters.get("team", "LG")
    budget = filters.get("budget", 30)
    party = filters.get("party", "solo")
    
    return f"""당신은 KBO 원정 응원 전문 플래너입니다.
사용자는 {team} 팬이고, 예산 {budget}만원으로 {party} 구성 원정을 계획 중입니다.

답변 원칙:
1. 친근한 반말 대신 존댓말 사용
2. 구체적인 장소·시간·비용 제시
3. 답변은 3~5문장 이내로 간결하게
4. 모르는 것은 "정확한 정보는 앱 내 지도 탭을 확인해주세요" 안내
"""
```

작성 후 탭 4에서 예시 질문 버튼 클릭 → AI 응답 생성 확인.
엔드투엔드 작동하면 이 Step은 완료.
````

### 검증 (MVP 완료 체크포인트)
- [ ] 탭 4에서 챗봇 UI 표시
- [ ] "안녕하세요" 입력 시 응답 반환 (3~5초 이내)
- [ ] 응답이 LG 팬·예산 30만원 맥락을 반영
- [ ] 대화가 연속적으로 이어짐 (이전 턴 기억)
- [ ] 대화 초기화 버튼 작동

> 🎯 **여기서 90분이 넘었다면**: Step 9 (시연 안전장치)로 바로 가서 Mock 응답 녹화부터 하세요. Function Calling·Multi-Agent·RAG는 MVP가 아닙니다.

---

## ✍️ 5. Step 4. 시스템 프롬프트 엔지니어링 (15분)

### 목표
Step 3의 임시 프롬프트를 **페르소나 + Few-shot + 제약사항**을 갖춘 정교한 프롬프트로 업그레이드.

### 🤖 Claude Code 프롬프트

````
src/ai/prompts.py를 다음 명세로 재작성해줘.

```python
from src.data_loader import load_stadiums

STADIUM_MAP = None  # 지연 로딩

def _get_team_stadium(team: str) -> str:
    """팀의 홈구장 반환"""
    global STADIUM_MAP
    if STADIUM_MAP is None:
        df = load_stadiums()
        STADIUM_MAP = {
            t.strip(): row["stadium_name"]
            for _, row in df.iterrows()
            for t in row["home_team"].split(",")
        }
    return STADIUM_MAP.get(team, "—")


SYSTEM_PROMPT_BASE = """당신은 '원정 응원 플래너'의 AI 어시스턴트입니다.
KBO 리그 10개 구단 원정 응원을 전문으로 돕는 친절한 가이드예요.

## 페르소나
- 야구팬의 감정을 이해하는 베테랑 가이드
- 실용적이고 구체적인 정보 위주로 답변
- 지역 방언 몇 마디는 자연스럽게 (광주→"어이~", 부산→"~예")
- 비꼬거나 부정적인 표현 금지

## 현재 사용자 정보
- 응원팀: {team} (홈구장: {home_stadium})
- 원정 기간: {date_range}
- 예산: {budget}만원
- 인원 구성: {party_ko}
- 이동수단: {transport_ko}

## 답변 원칙
1. 3~5문장 이내 간결하게. 질문이 복잡하면 핵심 3가지로 정리.
2. 구체적 장소명·가격·시간 제시 (일반론 금지)
3. 앱 내 기능 연결 안내 (예: "지도 탭에서 실제 위치 확인 가능")
4. 모르는 정보는 추측하지 말고 "정확한 정보는 확인이 필요합니다"
5. 금액은 "원" 단위, 시간은 "15분"처럼 구체적으로

## 금지사항
- 경쟁팀 비하, 선수 실명 비판
- 도박·승부 예측 단정 (참고용임을 명시)
- 어린이 부적합 식당·장소 추천 (party가 family일 때)

## 예시 응답

Q: "광주 원정 1박 2일, 아이랑 가려는데 추천해줘"
A: "어이~ 광주 원정이시네요! 1박 2일이면 첫날 경기 전에 KIA 챔피언스필드 근처 '1913송정역시장'에서 아이랑 간식 드시고 경기 관람, 저녁은 '영미오리탕' 추천드려요(3만원대, 아이 메뉴 있음). 둘째날 국립아시아문화전당에서 어린이 체험관 3시간 즐기고 상경하시면 됩니다. 지도 탭에서 동선 확인하세요!"

Q: "비 올 확률 높으면 실내 관광지는?"
A: "우천 대비 실내 코스는 지역마다 달라요. 광주는 국립아시아문화전당(성인 5천원), 부산은 부산현대미술관과 롯데월드 부산, 대구는 간송미술관 대구관이 추천드립니다. 경기장별 우천 확률은 지도 탭의 경기장 마커를 클릭하시면 확인 가능합니다."
"""


PARTY_KO = {
    "solo": "혼자",
    "couple": "커플",
    "family": "가족 (어린이 포함)",
    "friends": "친구 그룹",
}

TRANSPORT_KO = {
    "train": "KTX/SRT 등 기차",
    "car": "자차",
    "bus": "고속버스",
}


def build_system_prompt(filters: dict) -> str:
    team = filters.get("team", "LG")
    date_range = filters.get("date_range", ("—", "—"))
    date_str = f"{date_range[0]} ~ {date_range[1]}"
    
    return SYSTEM_PROMPT_BASE.format(
        team=team,
        home_stadium=_get_team_stadium(team),
        date_range=date_str,
        budget=filters.get("budget", 30),
        party_ko=PARTY_KO.get(filters.get("party", "solo"), "혼자"),
        transport_ko=TRANSPORT_KO.get(filters.get("transport", "train"), "기차"),
    )
```

프롬프트는 계속 튜닝 대상이야. 이 파일을 git에 커밋한 후,
시연 중 응답 품질이 아쉬우면 여기만 수정하면 됨.

작성 후 탭 4에서 예시 질문 재실행 → 답변에 지역 방언·구체적 장소·가격이 나오는지 확인.
````

### 검증
- 탭 4에서 "광주 원정 추천해줘" → 응답에 구체적 장소명·가격 포함
- party를 "family"로 설정 → 어린이 친화적 콘텐츠로 변화
- 대화가 존댓말로 일관됨

---

## 🛠️ 6. Step 5. Function Calling 도구 구현 (45분, 강력 권장)

### 목표
LLM이 사용자 질문을 분석해 **외부 도구를 호출**하게 만든다. "내일 부산 승률 알려줘" → LLM이 `predict_win_rate` 호출 → 실제 수치 기반 답변.

### 도구 목록 (5종)

| # | 도구 | 입력 | 출력 | Phase 1~3 연동 |
|---|---|---|---|---|
| 1 | `search_game` | 팀, 날짜 범위 | 경기 리스트 | `data_loader.load_schedule` |
| 2 | `predict_win_rate` | 원정팀, 홈팀 | 승률 float | `ai.predict` |
| 3 | `get_weather` | 좌표, 날짜 | 날씨 dict | `api.weather_api` |
| 4 | `find_places` | 구장, 카테고리 | POI 리스트 | `data_loader.load_poi` |
| 5 | `get_route` | 출발, 도착 | 거리·시간 | `api.kakao_map` |

### 🤖 Claude Code 프롬프트

````
src/ai/tools.py를 다음 명세로 구현해줘.

### OpenAI tool_use 스키마 정의

```python
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_game",
            "description": "특정 팀의 원정 경기를 날짜 범위로 검색",
            "parameters": {
                "type": "object",
                "properties": {
                    "team": {
                        "type": "string",
                        "description": "응원팀 약칭. 예: LG, KT, KIA",
                    },
                    "start_date": {"type": "string", "description": "YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "YYYY-MM-DD"},
                },
                "required": ["team"],
            },
        },
    },
    # predict_win_rate, get_weather, find_places, get_route
    ...
]
```

5개 도구 모두 상세한 description과 required 필드 명시.
LLM이 언제 호출할지 판단할 수 있게 description을 풍부하게 작성.

### 도구 실행 함수

```python
def execute_tool(name: str, arguments: dict) -> dict:
    """
    LLM이 요청한 도구를 실제 실행하고 결과 반환.
    
    Returns:
        {"success": bool, "data": ..., "error": None | str}
    """
    try:
        if name == "search_game":
            return _search_game(**arguments)
        elif name == "predict_win_rate":
            return _predict_win_rate(**arguments)
        # ... 나머지 3개
        else:
            return {"success": False, "error": f"알 수 없는 도구: {name}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _search_game(team: str, start_date: str = None, end_date: str = None) -> dict:
    from src.data_loader import load_schedule
    import pandas as pd
    
    df = load_schedule()
    away = df[df.away_team == team]
    
    if start_date:
        away = away[away.date >= pd.Timestamp(start_date)]
    if end_date:
        away = away[away.date <= pd.Timestamp(end_date)]
    
    games = away.head(10).to_dict("records")
    # JSON 직렬화 가능하게 날짜 변환
    for g in games:
        g["date"] = str(g["date"])
    
    return {
        "success": True,
        "data": {"games": games, "count": len(games)},
    }


def _predict_win_rate(team: str, opponent: str) -> dict:
    from src.ai.predict import load_model, predict_win_rate
    from src.data_loader import load_team_stats
    
    stats = load_team_stats()
    prob = predict_win_rate(team, opponent, stats, load_model())
    
    return {
        "success": True,
        "data": {"team": team, "opponent": opponent, "win_probability": prob},
    }


# 나머지 3개도 유사 패턴
```

### tab4_ai.py 통합 (tools 파라미터 사용)

```python
from src.ai.tools import TOOL_SCHEMAS, execute_tool

# chat_complete 호출 시 tools 전달
response = chat_complete(messages, tools=TOOL_SCHEMAS, temperature=0.5)

if response["tool_calls"]:
    # 도구 호출이 있으면 각각 실행
    tool_messages = []
    for call in response["tool_calls"]:
        result = execute_tool(call["name"], call["arguments"])
        tool_messages.append({
            "role": "tool",
            "tool_call_id": call["id"],
            "content": json.dumps(result, ensure_ascii=False),
        })
    
    # 도구 결과를 포함해 LLM에 재호출
    messages.extend([
        {"role": "assistant", "content": None, "tool_calls": [
            {"id": c["id"], "type": "function", 
             "function": {"name": c["name"], "arguments": json.dumps(c["arguments"])}}
            for c in response["tool_calls"]
        ]},
        *tool_messages,
    ])
    
    final = chat_complete(messages, temperature=0.7)
    st.markdown(final["content"])
else:
    st.markdown(response["content"])
```

작성 후 탭 4에서 "LG 다음 원정 경기 승률 알려줘" 입력 → 
도구가 호출되고 실제 수치 기반 답변 확인.
````

### 검증
- "다음 주 원정 경기 알려줘" → `search_game` 호출
- "KT와의 승률은?" → `predict_win_rate` 호출 후 실제 모델 예측값 기반 답변
- "광주 맛집 추천" → `find_places` 호출 후 실제 POI 데이터 기반 답변

---

## 🔍 7. Step 6. 도구 호출 시각화 UI (15분) — **발표 임팩트**

### 목표
도구 호출 과정을 **Thought-Action-Observation** 패턴으로 시각화. 발표 시연에서 가장 강력한 인상을 남기는 요소.

### 🤖 Claude Code 프롬프트

````
src/ui/tabs/tab4_ai.py에 도구 호출 과정을 시각화하는 로직 추가.

### UI 목표

AI 응답 위에 st.expander로 "🔍 AI가 수행한 작업" 박스 표시.
펼치면 각 도구 호출이 단계별로 보임:

```
💭 Thought: 사용자가 광주 원정 계획을 물어봤어요. 경기 일정과 맛집 정보가 필요합니다.

🔧 Action 1: search_game
   Input: {"team": "LG", "start_date": "2026-04-19", "end_date": "2026-04-20"}
   
📋 Observation 1:
   ✅ 경기 2개 발견:
   - 2026-04-19 KIA vs LG @ 광주
   - 2026-04-20 KIA vs LG @ 광주

🔧 Action 2: find_places
   Input: {"stadium": "광주", "category": "food"}
   
📋 Observation 2:
   ✅ 음식점 15곳 반환
```

### 구현

tool_calls 처리 부분을 다음으로 교체:

```python
if response["tool_calls"]:
    # expander로 도구 호출 과정 표시
    with st.expander("🔍 AI가 수행한 작업", expanded=True):
        st.markdown(f"💭 **Thought**: LLM이 {len(response['tool_calls'])}개의 도구 호출이 필요하다고 판단했습니다.")
        st.divider()
        
        tool_messages = []
        for i, call in enumerate(response["tool_calls"], 1):
            st.markdown(f"### 🔧 Action {i}: `{call['name']}`")
            st.json(call["arguments"])
            
            with st.spinner(f"실행 중..."):
                result = execute_tool(call["name"], call["arguments"])
            
            st.markdown(f"### 📋 Observation {i}")
            if result["success"]:
                # 데이터가 크면 요약만
                data = result["data"]
                if isinstance(data, dict) and "games" in data:
                    st.success(f"✅ 경기 {len(data['games'])}개 발견")
                    st.dataframe(data["games"][:5])
                elif isinstance(data, dict) and "win_probability" in data:
                    st.success(f"✅ 승률 {data['win_probability']*100:.1f}%")
                else:
                    st.json(data)
            else:
                st.error(f"❌ {result['error']}")
            
            tool_messages.append({
                "role": "tool",
                "tool_call_id": call["id"],
                "content": json.dumps(result, ensure_ascii=False),
            })
            
            st.divider()
    
    # LLM에 도구 결과 넣어 최종 답변 생성
    messages.extend([...])  # 기존 로직 유지
    final = chat_complete(messages, temperature=0.7)
    
    # 최종 답변 표시
    st.markdown("### 💬 AI의 답변")
    st.markdown(final["content"])
```

이렇게 하면 발표 시 "AI가 지금 이런 과정을 거쳐서 답을 만들고 있습니다"를
시각적으로 보여줄 수 있어.

작성 후 "광주 원정 맛집 추천해줘" 입력 → expander로 2~3단계 도구 호출 과정 시각화 확인.
````

### 검증
- 도구 호출이 발생하는 질문 입력 시 expander 자동 펼쳐짐
- 각 Action·Observation이 순차적으로 보임
- 최종 답변이 expander 아래에 별도로 렌더링

---

## 🎭 8. Step 7. Multi-Agent 순차 호출 패턴 (30분, 선택)

### 목표
"하나의 LLM이 5개 도구를 자유롭게 호출"하는 Step 5~6에서 **"여러 에이전트가 순차 협업"**하는 구조로 리팩토링. 실제로는 같은 LLM이지만 시스템 프롬프트를 바꿔가며 호출해 **역할 연기**.

### 에이전트 구성

```
Supervisor: 요청 분해 → 계획 수립
    ↓
Schedule Agent: 경기 정보 수집
    ↓
Strategy Agent: 승률 예측 + 전략 해석
    ↓
Place Agent: 맛집·숙소 큐레이션
    ↓
Synthesizer: 최종 답변 통합
```

### 🤖 Claude Code 프롬프트

````
src/ai/agents.py를 다음 명세로 작성해줘. LangGraph는 쓰지 않고
순차 LLM 호출로 Multi-Agent 느낌을 구현.

```python
from src.ai.llm_client import chat_complete
from src.ai.tools import execute_tool, TOOL_SCHEMAS

AGENT_PROMPTS = {
    "supervisor": """당신은 원정 플래너의 총괄 매니저입니다.
사용자 요청을 분석해 어떤 전문가를 호출해야 할지 결정하세요.

사용 가능한 전문가:
- schedule: 경기 일정 전문가
- strategy: 승률·전략 분석가
- place: 맛집·숙소·관광 큐레이터

JSON 형식으로 응답:
{"agents": ["schedule", "place"], "reason": "경기 일정과 맛집이 필요"}
""",
    
    "schedule": """당신은 KBO 경기 일정 전문가입니다.
search_game 도구로 일정을 조회하고 핵심 경기 정보를 요약하세요.
""",
    
    "strategy": """당신은 KBO 승률·전략 분석가입니다.
predict_win_rate와 get_weather 도구로 경기 승률과 변수를 분석해 
관전 포인트를 제시하세요.
""",
    
    "place": """당신은 구장 주변 맛집·숙소·관광 전문가입니다.
find_places 도구를 활용해 사용자 예산과 인원에 맞는 장소를 큐레이션하세요.
""",
    
    "synthesizer": """당신은 최종 응답 작성자입니다.
각 전문가가 수집한 정보를 종합해 3~5문장의 친근한 답변을 작성하세요.
지역 방언 한두 마디 섞어 생동감 있게.
""",
}


def run_multi_agent(user_query: str, filters: dict, progress_callback=None):
    """
    Multi-agent 순차 호출.
    
    progress_callback: 단계마다 호출되는 콜백 (UI 업데이트용)
        callback(stage: str, content: str)
    """
    context = {"query": user_query, "filters": filters, "findings": {}}
    
    # 1. Supervisor: 누가 일할지 결정
    if progress_callback:
        progress_callback("supervisor", "🎬 작업 계획 수립 중...")
    
    plan_resp = chat_complete([
        {"role": "system", "content": AGENT_PROMPTS["supervisor"]},
        {"role": "user", "content": f"질문: {user_query}\n사용자 설정: {filters}"},
    ], temperature=0.3, max_tokens=200)
    
    # JSON 파싱 (실패 시 전체 에이전트 호출)
    try:
        import json, re
        match = re.search(r'\{.*\}', plan_resp["content"], re.DOTALL)
        plan = json.loads(match.group()) if match else {"agents": ["schedule", "strategy", "place"]}
    except:
        plan = {"agents": ["schedule", "strategy", "place"]}
    
    if progress_callback:
        progress_callback("supervisor", f"📋 호출 에이전트: {', '.join(plan['agents'])}")
    
    # 2. 각 에이전트 순차 실행
    for agent in plan["agents"]:
        if progress_callback:
            progress_callback(agent, f"🔎 {agent} 에이전트 작업 중...")
        
        agent_resp = chat_complete([
            {"role": "system", "content": AGENT_PROMPTS[agent]},
            {"role": "user", "content": f"{user_query}\n맥락: {context['findings']}"},
        ], tools=TOOL_SCHEMAS, temperature=0.5, max_tokens=400)
        
        # 도구 호출이 있으면 실행
        if agent_resp.get("tool_calls"):
            tool_results = []
            for call in agent_resp["tool_calls"]:
                result = execute_tool(call["name"], call["arguments"])
                tool_results.append(f"{call['name']}: {result.get('data', result.get('error'))}")
            context["findings"][agent] = "\n".join(tool_results)
        else:
            context["findings"][agent] = agent_resp["content"]
        
        if progress_callback:
            progress_callback(agent, f"✅ {agent} 완료")
    
    # 3. Synthesizer: 최종 답변
    if progress_callback:
        progress_callback("synthesizer", "✍️ 최종 답변 작성 중...")
    
    final_resp = chat_complete([
        {"role": "system", "content": AGENT_PROMPTS["synthesizer"]},
        {"role": "user", "content": 
            f"사용자 질문: {user_query}\n\n"
            f"전문가 분석:\n" + 
            "\n\n".join(f"【{k}】\n{v}" for k, v in context["findings"].items())
        },
    ], temperature=0.7, max_tokens=600)
    
    return final_resp["content"], context["findings"]
```

### tab4_ai.py에 "Multi-Agent 모드" 토글 추가

```python
use_multi_agent = st.toggle("🎭 Multi-Agent 모드", value=False,
                            help="여러 AI 에이전트가 협업해 답변을 생성합니다")

# 사용자 입력 처리 시
if use_multi_agent:
    with st.expander("🎬 에이전트 협업 과정", expanded=True):
        progress_placeholder = st.empty()
        agent_logs = []
        
        def cb(stage, msg):
            agent_logs.append(f"- **{stage}**: {msg}")
            progress_placeholder.markdown("\n".join(agent_logs))
        
        answer, findings = run_multi_agent(user_input, filters, progress_callback=cb)
    
    st.markdown(answer)
else:
    # 기존 단일 LLM + tool_use 경로
    ...
```

작성 후 Multi-Agent 모드 활성화하고 복합 질문 입력 → 
여러 에이전트가 순차 작업하는 로그 확인.
````

### 검증
- Multi-Agent 토글 on → expander에 4~5개 에이전트 로그 순차 표시
- 최종 답변이 단일 LLM보다 풍부한 정보 종합
- 응답 시간이 10~20초로 증가 (정상)

---

## 📚 9. Step 8. Agentic RAG 프로토타입 (30분, 최후 선택)

### 목표
구장별 원정 팁 지식을 **ChromaDB 벡터 DB**에 저장하고, Place Agent가 검색해 답변에 반영. 시간 여유가 있을 때만 진행.

### 🤖 Claude Code 프롬프트

````
data/knowledge/away_game_tips.json을 만들어. 10개 구장 × 구장당 5개 팁
= 50개 지식 항목.

예시:
```json
[
  {
    "stadium": "광주",
    "tip": "광주 챔피언스필드는 3루 쪽 햇빛이 강해 6~8월 오후 경기는 1루 외야 예약 추천",
    "category": "seat"
  },
  {
    "stadium": "광주",
    "tip": "경기 종료 후 KIA 팬들이 모이는 전통 식당 '영미오리탕' — 지하철역 도보 10분",
    "category": "food"
  },
  ...
]
```

10개 구장별로 seat, food, transport, timing, etiquette 카테고리에서 
1~2개씩 작성. 총 50개 정도. Claude가 직접 야구 지식을 활용해 작성해줘.

그리고 src/ai/rag.py를 다음 명세로 작성:

```python
import chromadb
from chromadb.utils import embedding_functions

_COLLECTION = None

def _get_collection():
    global _COLLECTION
    if _COLLECTION is None:
        client = chromadb.PersistentClient(path="data/chroma_db")
        # OpenAI 임베딩 또는 기본 임베딩 사용
        ef = embedding_functions.DefaultEmbeddingFunction()
        _COLLECTION = client.get_or_create_collection(
            name="away_game_tips",
            embedding_function=ef,
        )
    return _COLLECTION


def build_index():
    """JSON을 ChromaDB에 인덱싱"""
    import json
    with open("data/knowledge/away_game_tips.json") as f:
        tips = json.load(f)
    
    col = _get_collection()
    
    ids = [f"tip_{i}" for i in range(len(tips))]
    documents = [t["tip"] for t in tips]
    metadatas = [{"stadium": t["stadium"], "category": t["category"]} for t in tips]
    
    col.upsert(ids=ids, documents=documents, metadatas=metadatas)
    return len(tips)


def search_tips(query: str, stadium: str = None, top_k: int = 3) -> list[dict]:
    """의미 유사도 기반 팁 검색"""
    col = _get_collection()
    
    where = {"stadium": stadium} if stadium else None
    results = col.query(
        query_texts=[query],
        n_results=top_k,
        where=where,
    )
    
    tips = []
    for i, doc in enumerate(results["documents"][0]):
        tips.append({
            "tip": doc,
            "stadium": results["metadatas"][0][i]["stadium"],
            "category": results["metadatas"][0][i]["category"],
            "distance": results["distances"][0][i],
        })
    return tips


if __name__ == "__main__":
    count = build_index()
    print(f"✅ {count}개 팁 인덱싱 완료")
    
    # 테스트 검색
    results = search_tips("어디에 앉는 게 좋을까", stadium="광주")
    for r in results:
        print(f"- [{r['category']}] {r['tip']}")
```

그리고 src/ai/tools.py에 6번째 도구 추가:

```python
{
    "type": "function",
    "function": {
        "name": "search_knowledge",
        "description": "구장별 원정 응원 팁·노하우를 의미 검색으로 조회",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "검색 의도"},
                "stadium": {"type": "string", "description": "구장 필터 (선택)"},
            },
            "required": ["query"],
        },
    },
}

def _search_knowledge(query: str, stadium: str = None) -> dict:
    from src.ai.rag import search_tips
    tips = search_tips(query, stadium=stadium, top_k=3)
    return {"success": True, "data": {"tips": tips}}
```

작성 후:
1. python -m src.ai.rag 실행해 인덱싱
2. 탭 4에서 "광주 경기 앉을 자리 추천해줘" 입력
3. search_knowledge 도구 호출 확인
````

### 검증
- `data/chroma_db/` 디렉토리 생성 확인
- `python -m src.ai.rag` 실행 시 "50개 팁 인덱싱 완료"
- 탭 4에서 노하우 관련 질문 시 `search_knowledge` 자동 호출

---

## 🛡️ 10. Step 9. 검증 & 시연 안전장치 — **필수**

### Mock 응답 녹화 (발표 당일 API 장애 대비)

### 🤖 Claude Code 프롬프트

````
src/ai/mock_responses.py를 만들어줘.
발표 시연에서 사용할 3가지 시나리오의 응답을 사전 녹화.

```python
MOCK_RESPONSES = {
    "광주_1박2일_가족": {
        "query": "광주 원정 1박 2일, 아이랑 가려는데 추천해줘",
        "response": """어이~ 광주 원정이시네요! 
        
1박 2일 가족 코스 추천드려요:

**1일차**
- 오후 2시: KIA 챔피언스필드 도착, 1루 외야석 (햇빛 피할 수 있어요)
- 경기 후: '영미오리탕' 저녁 (어린이 메뉴 있음, 3만원대)
- 숙소: 광주 첨단지구 비즈니스 호텔 (15만원대)

**2일차**
- 오전: 국립아시아문화전당 어린이 체험관 (3시간)
- 점심: 송정역시장 (아이 간식 즐비)
- 오후 상경

예산 30만원 내에서 무난하게 소화 가능합니다!""",
        "tool_calls_shown": ["search_game", "find_places", "search_knowledge"],
    },
    "부산_맛집_세곳": {
        "query": "이번 주말 부산 맛집 세 곳 알려줘",
        "response": """부산 사직구장 근처 추천 세 곳 드릴게예:

1. **할매집** - 돼지국밥 원조 (1만원)
2. **해운대 밀면** - 여름 필수 (9천원)  
3. **광안리 회타운** - 경기 후 회식 (3만원대)

지도 탭에서 정확한 위치 확인 가능합니다!""",
        "tool_calls_shown": ["find_places"],
    },
    "우천_실내관광": {
        "query": "비 올 확률 높으면 실내 관광지는?",
        "response": """우천 대비 실내 코스 드립니다:

- **광주**: 국립아시아문화전당 (성인 5천원)
- **부산**: 부산현대미술관, 롯데월드 부산
- **대구**: 간송미술관 대구관

경기장별 우천 확률은 지도 탭 마커를 클릭하면 확인 가능해요!""",
        "tool_calls_shown": ["get_weather"],
    },
}


def get_mock_response(query: str):
    """쿼리에서 키워드로 가장 유사한 mock 선택"""
    query_lower = query.lower()
    for key, data in MOCK_RESPONSES.items():
        keywords = key.split("_")
        if any(k in query_lower for k in keywords):
            return data
    return None
```

### tab4_ai.py에 "🎬 시연 모드" 토글 추가

```python
demo_mode = st.sidebar.checkbox("🎬 시연 모드", value=False,
                                 help="녹화된 응답 사용 (발표용)")

if demo_mode:
    mock = get_mock_response(user_input)
    if mock:
        # mock 응답을 천천히 스트리밍하는 것처럼 표시
        import time
        placeholder = st.empty()
        for i in range(1, len(mock["response"]) + 1, 5):
            placeholder.markdown(mock["response"][:i])
            time.sleep(0.03)
```
````

### 최종 검증 체크리스트

- [ ] `python -m src.ai.predict` 모델 학습 성공
- [ ] `python -m src.ai.llm_client` 응답 수신 확인
- [ ] 탭 4에서 3종 예시 질문 답변 생성 (2초 이내 시작)
- [ ] Function Calling 작동 (도구 호출 로그 확인)
- [ ] Multi-Agent 모드 토글 동작
- [ ] RAG 검색 작동 (구현한 경우)
- [ ] Mock 응답 시연 모드 작동
- [ ] 3분 발표 시나리오 리허설 1회 이상

### 발표 전날 필수 작업
1. **AI 응답 3종 녹화 영상**: OBS나 QuickTime으로 화면 녹화
2. **Mock 응답 검증**: 시연 모드에서 정확히 원하는 답변이 나오는지
3. **API 키 잔액 확인**: OpenAI Usage 대시보드에서 $5 이하 확인

---

## 👥 11. 병렬 작업 가이드

### 🎨 프론트/UX 담당
- `assets/css/style.css`에 챗봇 UI 스타일링 (말풍선, 아바타)
- 도구 호출 expander의 색상·타이포그래피 다듬기
- Phase 5 배포 준비 (Streamlit Cloud 계정, `secrets.toml` 설정)

### 🗺️ 지도/시각화 담당
- Phase 3에서 만든 지도·차트 폴리싱
- AI 응답에 `st.plotly_chart` 또는 Folium 지도를 인라인 삽입하는 실험
- 발표 데모 영상 녹화 지원

### 🧑‍✈️ 팀장/데이터 엔지니어
- Phase 5 가이드 초안 작성
- 발표 슬라이드 Multi-Agent 아키텍처 다이어그램 (Mermaid)
- 팀 리허설 일정 조율

---

## 🧾 12. 완료 체크리스트

### MVP (필수 — 여기까지만 해도 과제 통과)
- [ ] `src/ai/predict.py` 승률 모델 작동
- [ ] `models/win_rate_model.pkl` 저장됨
- [ ] 탭 1 게이지에 실제 예측값 반영
- [ ] `src/ai/llm_client.py` 이중화 작동
- [ ] `src/ai/prompts.py` 프롬프트 완성
- [ ] 탭 4 챗봇 end-to-end 작동

### 권장 (발표 임팩트)
- [ ] `src/ai/tools.py` 5개 도구 정의
- [ ] Function Calling 실제 호출 확인
- [ ] 도구 호출 시각화 UI 작동

### 선택 (시간 여유)
- [ ] `src/ai/agents.py` Multi-Agent 패턴
- [ ] `src/ai/rag.py` ChromaDB 검색
- [ ] `src/ai/mock_responses.py` 시연 안전장치

---

## 🆘 13. 트러블슈팅 FAQ

### Q1. OpenAI API 호출 시 `RateLimitError`
- 무료 tier는 분당 3회 제한. 유료 계정 (최소 $5 결제)으로 업그레이드 필요
- 또는 Gemini로 전환해 무료 티어 활용

### Q2. 응답이 영어로 나와요
시스템 프롬프트 첫 줄에 "**반드시 한국어로만 응답하세요**"를 명시적으로 추가.

### Q3. 도구 호출이 안 일어나요
- 프롬프트에 "필요하면 도구를 사용하세요"를 명시
- `tool_choice="required"`로 강제할 수 있지만 매번 도구 호출하려 함 (단점)
- `temperature`를 0.3 이하로 낮추면 결정적 행동 증가

### Q4. JSON 파싱 에러 (Multi-Agent supervisor 응답)
LLM이 순수 JSON이 아닌 마크다운으로 감싸서 반환하는 경우 많음. 정규식으로 `\{.*\}` 추출 후 파싱. 실패 시 기본값 fallback.

### Q5. ChromaDB 설치 실패
Python 3.11+ 환경에서 가장 안정적. Apple Silicon Mac에서는 `arch -arm64 pip install chromadb`. 실패 시 Phase 4 Step 8 건너뛰기.

### Q6. 응답 생성이 30초 이상 걸려요
- Multi-Agent 모드는 원래 오래 걸림 (에이전트 5개 순차 호출)
- 개별 호출 지연이면 `max_tokens`를 800→400으로 축소
- 네트워크 문제일 수 있으니 다른 API 테스트로 확인

### Q7. 비용이 $5를 이미 넘었어요
- OpenAI 대시보드에서 월 예산 hard cap 설정 ($10 권장)
- 개발 중 모델을 `gpt-4o-mini` 확실히 사용 중인지 확인
- 시스템 프롬프트 너무 긴 건 아닌지 검토 (500 토큰 넘지 않게)

### Q8. 발표 당일 API가 먹통
**사전 녹화한 영상으로 시연**. Mock 모드 토글도 백업. 절대 당일 디버깅 금지.

---

## 🎬 14. 다음 Phase로 넘어가기 전 확인

다음 5가지가 ✅이면 Phase 5 시작 준비 완료.

1. ✅ 탭 1 게이지가 실제 모델 예측값 반영
2. ✅ 탭 4 챗봇이 최소 MVP 수준으로 작동
3. ✅ Mock 응답 3종 녹화 완료
4. ✅ API 키 잔액 확인 및 예산 한도 설정
5. ✅ `CLAUDE.md` "현재 진행 Phase"가 **Phase 5**로 업데이트

### Phase 5로 전환하는 Claude Code 프롬프트

````
Phase 4 AI 기능이 완료됐어. 탭 4 챗봇이 작동하고 승률 게이지에 
모델 예측값이 들어가는 걸 확인했어.

이제 Phase 5를 시작:
1. CLAUDE.md의 현재 진행 Phase를 Phase 5로 업데이트
2. IMPLEMENTATION_PLAN.md Phase 5 섹션 참고
3. 첫 작업: assets/css/style.css 브랜딩 테마 적용
4. Streamlit Community Cloud 배포 리허설
5. 발표 자료 스켈레톤 PPTX 생성

현재 구현한 AI 기능을 발표 자료의 "기술 아키텍처" 섹션에 
다이어그램으로 포함해 줘.
````

---

## 📚 참고

- 전체 계획: [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) Phase 4 섹션
- 이전 가이드: [PHASE3_GUIDE.md](./PHASE3_GUIDE.md)
- OpenAI Function Calling: https://platform.openai.com/docs/guides/function-calling
- LangGraph Multi-Agent (참고용): https://langchain-ai.github.io/langgraph/tutorials/multi_agent/
- ChromaDB 공식 문서: https://docs.trychroma.com/
- Agentic RAG 개념: https://weaviate.io/blog/what-is-agentic-rag

---

*가이드 마지막 업데이트: 2026-04-17*
*예상 총 소요 시간: 3시간 (AI·분석 담당 1명 기준)*
*최소 MVP 시간: 90분*

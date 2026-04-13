"""
feedback_generator.py
감성 분석 결과 + 운동 기록 + 피드백 모드를 종합하여
AI 동기부여 피드백을 생성합니다.
"""

import json
import time
from dataclasses import dataclass, field
from datetime import datetime

from .feedback_modes import FeedbackMode, get_mode, build_mode_prompt_prefix


@dataclass
class FeedbackResult:
    """피드백 생성 결과"""
    main_message: str
    praise_points: list[str] = field(default_factory=list)
    improvement_suggestions: list[str] = field(default_factory=list)
    next_week_tips: list[str] = field(default_factory=list)
    encouragement_quote: str = ""
    mode: str = "coach"
    mode_name: str = "코치 모드"
    mode_emoji: str = "🏋️"
    model_used: str = ""
    latency_sec: float = 0


# ═══════════════════════════════════════
# 규칙 기반 피드백 (LLM 없이 즉시 생성)
# ═══════════════════════════════════════

# 모드별 어투 변환 템플릿
_MODE_TEMPLATES = {
    "coach": {
        "praise_prefix": "잘하신 점: ",
        "improve_prefix": "개선 포인트: ",
        "tip_prefix": "다음 주 추천: ",
        "completion_high": "목표 달성률이 우수합니다. 현재 페이스를 유지하시면 좋겠습니다.",
        "completion_mid": "꾸준히 하고 계시네요. 조금 더 빈도를 높여보시면 효과가 배가됩니다.",
        "completion_low": "이번 주는 목표 대비 부족했지만, 다음 주에 보완할 수 있습니다. 가벼운 운동부터 시작해보세요.",
        "negative_comfort": "힘든 시기를 지나고 있는 것 같습니다. 운동 강도를 낮추고 일단 꾸준히 출석하는 것에 집중해보세요.",
        "positive_boost": "긍정적인 에너지가 느껴집니다! 이 기세를 유지하시면 곧 눈에 띄는 변화가 올 것입니다.",
    },
    "friend": {
        "praise_prefix": "와 ",
        "improve_prefix": "근데 ",
        "tip_prefix": "다음 주엔 ",
        "completion_high": "야 이번 주 진짜 열심히 했다!! 대단해 👏👏",
        "completion_mid": "오 꾸준히 하고 있네~ 이 페이스 좋은데? ㅎㅎ",
        "completion_low": "에이 괜찮아~ 다음 주에 같이 가자! 💪",
        "negative_comfort": "힘들었지? ㅠㅠ 그래도 그런 날도 있는 거야~ 푹 쉬고 다시 가면 돼!",
        "positive_boost": "오 기분 좋아 보인다ㅋㅋ 이 기세면 몸짱 되는 건 시간문제야! 🔥",
    },
    "drill": {
        "praise_prefix": "좋았다! ",
        "improve_prefix": "하지만! ",
        "tip_prefix": "다음 주 명령: ",
        "completion_high": "이번 주 임무 완수! 훌륭하다. 하지만 방심은 금물이다!",
        "completion_mid": "절반은 했다. 나쁘지 않아. 하지만 넌 더 할 수 있다!",
        "completion_low": "이게 최선이냐?! ...그래도 포기 안 한 건 인정한다. 다시 일어서!",
        "negative_comfort": "지금 힘든 거 안다. 하지만 이걸 이겨내면 넌 강해진다. 포기만 안 하면 된다!",
        "positive_boost": "이 기세 좋다!! 바로 이거야! 그 투지를 잃지 마라!",
    },
    "mammykim": {
        "praise_prefix": "굿 파트너~ ",
        "improve_prefix": "근데 이건 ",
        "tip_prefix": "다음 주엔 ",
        "completion_high": "오 이번 주 다 왔어? 운동 많이 된다. 굿 파트너. 진짜 도움 많이 되고 있어.",
        "completion_mid": "꾸준히 하고 있네. 운동 된다. 대화가 된다.",
        "completion_low": "한 번이라도 온 거 운동 된다. 한 판 쉴래? 근데 남들은 안 쉬어.",
        "negative_comfort": "힘들었지? 괜찮아. 스트레스 받은 것도 운동이야. 자기 전에 생각 많이 날 거야. 내일 와. 운동 많이 될 거야.",
        "positive_boost": "운동 많이 된다. 진짜 도움 많이 되고 있어. 굿 파트너. 이 페이스면 대화가 된다.",
    },
    "marine": {
        "praise_prefix": "필승! ",
        "improve_prefix": "보고합니다! ",
        "tip_prefix": "다음 주 작전: ",
        "completion_high": "필승! 이번 주 앙증맞은 출석률 100% 보고합니다! 이 잔망스러운 근성장이 귀신잡는 해병대 정신입니다! 아쎄이!",
        "completion_mid": "필승! 이번 주 달콤쌉싸름한 출석을 보고합니다. 아련한 의지가 보입니다. 귀신잡는 해병대는 여기서 멈추지 않습니다!",
        "completion_low": "필승! 이번 주 수줍은 출석을 보고합니다... 하지만! 이 얄궂은 피로 속에서도 포기하지 않은 것, 해병이 인정합니다!",
        "negative_comfort": "필승! 이 달콤쌉싸름한 피로감은 더 강해지기 위한 앙증맞은 과정입니다. 귀신잡는 해병대에게 포기란 없습니다! 내일 출동하십시오!",
        "positive_boost": "필승! 이 잔망스러운 에너지가 해병대의 아련한 투지입니다! 귀신도 잡는 이 앙증맞은 파이팅! 아쎄이!",
    },
}


def generate_feedback_rule_based(
    sentiment_data: dict,
    weekly_summary: dict,
    mode_id: str = "coach",
) -> FeedbackResult:
    """
    규칙 기반으로 피드백을 생성합니다 (LLM 없이 즉시).

    Args:
        sentiment_data: analyze_weekly_sentiment()의 결과
        weekly_summary: 주간 요약 데이터
        mode_id: 피드백 모드
    """
    mode = get_mode(mode_id)
    templates = _MODE_TEMPLATES.get(mode_id, _MODE_TEMPLATES["coach"])

    weekly = sentiment_data.get("weekly_sentiment", {})
    dominant = weekly.get("dominant_sentiment", "중립")
    trend = weekly.get("trend", "유지")
    pos_count = weekly.get("positive_count", 0)
    neg_count = weekly.get("negative_count", 0)

    completion_rate = weekly_summary.get("completion_rate", 0)
    total_sessions = weekly_summary.get("total_sessions", 0)
    planned = weekly_summary.get("planned_sessions", 3)

    # 개별 일지 감성도 확인 (일지 1개일 때 대응)
    entries = sentiment_data.get("entries", [])
    single_sentiment = entries[0].get("sentiment", "중립") if len(entries) == 1 else None

    # 메인 메시지 결정 — 감성 우선, 달성률 보조
    # 감성이 명확하면 감성 기반 메시지를 메인으로, 달성률 메시지를 보조로
    if single_sentiment == "긍정" or (dominant == "긍정" and pos_count >= 1):
        # 긍정 감성 → positive_boost를 메인으로
        main = templates["positive_boost"]
        if completion_rate >= 90:
            main += " " + templates["completion_high"]
    elif single_sentiment == "부정" or (dominant == "부정" and neg_count >= 1):
        # 부정 감성 → negative_comfort를 메인으로
        main = templates["negative_comfort"]
        if completion_rate < 50:
            main += " " + templates["completion_low"]
    else:
        # 중립 감성 → 기존 달성률 기반 로직
        if completion_rate >= 90:
            main = templates["completion_high"]
        elif completion_rate >= 50:
            main = templates["completion_mid"]
        else:
            main = templates["completion_low"]

    # 칭찬 포인트
    praise = []
    if total_sessions > 0:
        praise.append(f"{templates['praise_prefix']}이번 주 {total_sessions}회 운동 수행")
    for entry in sentiment_data.get("entries", []):
        if entry.get("sentiment") == "긍정" and entry.get("emotion_detail") == "성취감":
            text = entry.get("text", "")[:30]
            praise.append(f"{templates['praise_prefix']}{text}")

    # 개선 제안
    improvements = []
    if completion_rate < 80:
        improvements.append(f"{templates['improve_prefix']}운동 빈도를 목표({planned}회)에 맞춰보세요")
    for entry in sentiment_data.get("entries", []):
        if entry.get("emotion_detail") == "피로":
            improvements.append(f"{templates['improve_prefix']}수면과 영양 섭취를 점검해보세요")
            break
        if entry.get("emotion_detail") == "통증":
            improvements.append(f"{templates['improve_prefix']}통증 부위는 전문가 상담을 권장합니다")
            break

    # 다음 주 팁
    tips = []
    if trend == "하락":
        tips.append(f"{templates['tip_prefix']}운동 강도를 낮추고 즐거운 운동 위주로 구성")
    elif trend == "상승":
        tips.append(f"{templates['tip_prefix']}이 기세를 유지하며 점진적으로 강도 상승")
    tips.append(f"{templates['tip_prefix']}운동 전 충분한 수분 섭취 (300~500ml)")

    # 명언
    quotes = {
        "coach": "꾸준함은 재능을 이긴다. — 윌 스미스",
        "friend": "같이 가면 멀리 간다! 💪",
        "drill": "고통은 일시적이다. 포기는 영원하다! — 에릭 토마스",
        "mammykim": "운동 많이 된다. 굿 파트너. 🥊",
        "marine": "필승! 해병은 포기하지 않는다! 귀신잡는 해병대! 🫡",
    }

    return FeedbackResult(
        main_message=main,
        praise_points=praise,
        improvement_suggestions=improvements,
        next_week_tips=tips,
        encouragement_quote=quotes.get(mode_id, quotes["coach"]),
        mode=mode_id,
        mode_name=mode.mode_name,
        mode_emoji=mode.emoji,
        model_used="rule_based",
    )


# ═══════════════════════════════════════
# LLM 기반 피드백 (모드별 페르소나 적용)
# ═══════════════════════════════════════

def generate_feedback_with_llm(
    sentiment_data: dict,
    weekly_summary: dict,
    user_profile: dict | None = None,
    mode_id: str = "coach",
    model: str = "exaone3.5",
    ollama_base_url: str = "http://localhost:11434/v1",
) -> FeedbackResult:
    """
    LLM으로 모드별 맞춤 피드백을 생성합니다.

    Args:
        sentiment_data: 감성 분석 결과
        weekly_summary: 주간 요약
        user_profile: Stage 1 프로필 (선택)
        mode_id: 피드백 모드 (coach/friend/drill/cheerleader/scientist)
        model: Ollama 모델
    """
    from openai import OpenAI

    mode = get_mode(mode_id)
    mode_prompt = build_mode_prompt_prefix(mode)

    # 분석 데이터 요약
    weekly = sentiment_data.get("weekly_sentiment", {})
    entries_summary = ""
    for e in sentiment_data.get("entries", []):
        entries_summary += f"  {e['date']}: [{e['sentiment']}({e['emotion_detail']})] \"{e['text'][:40]}\"\n"

    profile_info = ""
    if user_profile:
        nlp = user_profile.get("nlp_analysis", {})
        basic = user_profile.get("basic", {})
        profile_info = f"""
[사용자 프로필]
- {basic.get('age', '?')}세 {basic.get('gender', '?')}, 목표: {nlp.get('goal_type', '?')}
- 경험: {nlp.get('experience_level', '?')}, 제약: {', '.join(nlp.get('constraints', [])) or '없음'}"""

    prompt = f"""{mode_prompt}

아래 이번 주 운동 기록과 감성 분석 결과를 보고 피드백을 생성해주세요.
{profile_info}

[이번 주 기록]
- 운동: {weekly_summary.get('total_sessions', 0)}회 / 계획 {weekly_summary.get('planned_sessions', 3)}회 (달성률 {weekly_summary.get('completion_rate', 0)}%)
- 총 운동 시간: {weekly_summary.get('total_duration_min', 0)}분
- 수행 운동: {', '.join(weekly_summary.get('exercises_performed', []))}
- 주간 감성: 긍정 {weekly.get('positive_count', 0)}회, 부정 {weekly.get('negative_count', 0)}회, 중립 {weekly.get('neutral_count', 0)}회
- 감성 추세: {weekly.get('trend', '유지')}
- 주된 감성: {weekly.get('dominant_sentiment', '중립')}

[일지별 감성]
{entries_summary}

아래 JSON으로 응답해주세요:
{{"main_message": "<핵심 피드백 메시지 (2~3문장)>", "praise_points": ["<칭찬1>", "<칭찬2>"], "improvement_suggestions": ["<개선1>"], "next_week_tips": ["<팁1>", "<팁2>"], "encouragement_quote": "<동기부여 한 줄>"}}"""

    try:
        client = OpenAI(base_url=ollama_base_url, api_key="ollama")
        start = time.time()

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=800,
        )

        latency = round(time.time() - start, 2)
        content = response.choices[0].message.content.strip()

        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        data = json.loads(content.strip())

        return FeedbackResult(
            main_message=data.get("main_message", ""),
            praise_points=data.get("praise_points", []),
            improvement_suggestions=data.get("improvement_suggestions", []),
            next_week_tips=data.get("next_week_tips", []),
            encouragement_quote=data.get("encouragement_quote", ""),
            mode=mode_id,
            mode_name=mode.mode_name,
            mode_emoji=mode.emoji,
            model_used=f"llm_{model}",
            latency_sec=latency,
        )

    except Exception as e:
        # LLM 실패 시 규칙 기반 폴백
        result = generate_feedback_rule_based(sentiment_data, weekly_summary, mode_id)
        result.model_used = f"rule_fallback (LLM error: {str(e)[:30]})"
        return result

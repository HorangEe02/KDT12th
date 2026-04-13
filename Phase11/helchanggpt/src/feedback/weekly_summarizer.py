"""
weekly_summarizer.py
주간 운동 일지를 요약하고 성과를 추출합니다.
"""

from datetime import datetime


def build_weekly_summary(
    diary_entries: list[dict],
    planned_frequency: int = 3,
) -> dict:
    """
    주간 운동 기록을 요약합니다.

    Args:
        diary_entries: [{"date": "...", "text": "...", "exercises_done": [...], "duration_min": N}, ...]
        planned_frequency: 계획된 주당 운동 횟수

    Returns:
        주간 요약 딕셔너리
    """
    total_sessions = len(diary_entries)
    total_duration = sum(e.get("duration_min", 0) for e in diary_entries)

    exercises = set()
    for entry in diary_entries:
        for ex in entry.get("exercises_done", []):
            exercises.add(ex)

    completion_rate = round(total_sessions / max(planned_frequency, 1) * 100, 1)

    # 성과 키워드 추출
    highlights = extract_highlights(diary_entries)

    # 텍스트 요약 생성
    summary_text = _generate_summary_text(
        diary_entries, total_sessions, planned_frequency, total_duration, highlights,
    )

    return {
        "text": summary_text,
        "total_sessions": total_sessions,
        "planned_sessions": planned_frequency,
        "completion_rate": min(completion_rate, 100),
        "total_duration_min": total_duration,
        "avg_duration_min": round(total_duration / max(total_sessions, 1)),
        "exercises_performed": sorted(exercises),
        "highlights": highlights,
        "generated_at": datetime.now().isoformat(),
    }


def extract_highlights(diary_entries: list[dict]) -> list[str]:
    """운동 일지에서 주요 성과를 추출합니다."""
    highlight_patterns = {
        "무게 증가": ["올렸", "늘렸", "무게", "중량", "kg 증가"],
        "기록 갱신": ["신기록", "최고", "처음으로", "성공", "달성"],
        "체중 변화": ["체중", "몸무게", "줄었", "빠졌", "감량"],
        "꾸준한 출석": ["연속", "매일", "빠짐없이", "전부"],
        "새 운동 도전": ["새로운", "처음", "배웠", "도전"],
        "운동 시간 증가": ["오래", "시간 늘", "추가로"],
        "함께 운동": ["같이", "친구", "함께", "파트너"],
        "컨디션 향상": ["늘고", "좋아지", "향상", "체력 느"],
    }

    found = []
    all_text = " ".join(e.get("text", "") for e in diary_entries)

    for highlight, keywords in highlight_patterns.items():
        if any(kw in all_text for kw in keywords):
            found.append(highlight)

    return found


def _generate_summary_text(
    entries: list[dict],
    sessions: int,
    planned: int,
    duration: int,
    highlights: list[str],
) -> str:
    """주간 요약 텍스트를 생성합니다."""
    parts = []

    # 출석률
    if sessions >= planned:
        parts.append(f"이번 주 {sessions}회 운동으로 목표를 완벽히 달성했습니다.")
    elif sessions > 0:
        parts.append(f"이번 주 {sessions}/{planned}회 운동했습니다 (달성률 {round(sessions/planned*100)}%).")
    else:
        parts.append("이번 주는 운동 기록이 없습니다.")

    # 총 시간
    if duration > 0:
        parts.append(f"총 {duration}분 운동, 평균 {round(duration/max(sessions,1))}분/회.")

    # 성과
    if highlights:
        parts.append(f"주요 성과: {', '.join(highlights[:3])}.")

    return " ".join(parts)


def summarize_with_llm(
    diary_entries: list[dict],
    planned_frequency: int = 3,
    model: str = "exaone3.5",
) -> str:
    """LLM으로 주간 기록을 자연어 요약합니다."""
    from openai import OpenAI

    # 일지 텍스트 준비
    lines = [f"이번 주 운동 기록 (계획: 주 {planned_frequency}회)"]
    for entry in diary_entries:
        exercises = ", ".join(entry.get("exercises_done", []))
        duration = entry.get("duration_min", 0)
        text = entry["text"][:60]
        lines.append(f"  {entry.get('date', '?')}: {exercises} {duration}분 — \"{text}\"")

    actual = len(diary_entries)
    rate = round(actual / max(planned_frequency, 1) * 100)
    total_min = sum(e.get("duration_min", 0) for e in diary_entries)
    lines.append(f"  총 {actual}/{planned_frequency}회 ({rate}%), 총 {total_min}분")

    weekly_text = "\n".join(lines)

    prompt = f"""아래 주간 운동 기록을 3~4문장으로 요약해주세요.
달성률, 주요 성과, 아쉬운 점, 전반적인 컨디션 흐름을 포함하세요.

{weekly_text}

요약:"""

    try:
        client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=300,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return _generate_summary_text(
            diary_entries, len(diary_entries), planned_frequency,
            total_min, extract_highlights(diary_entries),
        )

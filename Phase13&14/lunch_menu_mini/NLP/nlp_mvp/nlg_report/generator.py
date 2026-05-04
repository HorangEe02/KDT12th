"""
리포트 생성기 (LLM + 템플릿 fallback + DB).
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

from sqlalchemy import text

from nlp_mvp.nlg_report.fact_extractor import (
    WeeklyFacts,
    extract_weekly_facts,
    get_week_start,
)
from nlp_mvp.nlg_report.prompt import build_report_prompt
from nlp_mvp.shared.db import get_engine, get_session
from nlp_mvp.shared.logger import get_logger

logger = get_logger(__name__)

TEMPLATES_DIR = Path(__file__).parent / "templates"


# =============================================================================
# 스키마
# =============================================================================
REPORTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS nutrition_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    week_start DATE NOT NULL,
    facts JSON NOT NULL,
    nlg_text TEXT NOT NULL,
    generation_method TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, week_start)
);
CREATE INDEX IF NOT EXISTS idx_reports_user ON nutrition_reports(user_id);
"""


def ensure_schema(engine=None) -> None:
    engine = engine or get_engine()
    with engine.begin() as conn:
        for stmt in REPORTS_TABLE_SQL.strip().split(";"):
            stmt = stmt.strip()
            if stmt:
                conn.execute(text(stmt))
    logger.info("nutrition_reports schema ensured")


# =============================================================================
# 품질 검증
# =============================================================================
FORBIDDEN_WORDS = [
    "병", "질병", "진단", "처방", "의사", "약",
    "나쁩니다", "잘못", "위험", "금지",
]

_EMOJI_RE = re.compile(
    "[\U0001F300-\U0001F9FF\U00002600-\U000027BF]"
)


def validate_report(text_str: str) -> dict[str, Any]:
    """
    생성된 리포트의 품질 검증.

    Returns:
        {"valid": bool, "issues": list[str], "length": int, "emoji_count": int}
    """
    issues: list[str] = []

    length = len(text_str)
    if length < 50:
        issues.append(f"too_short: {length}")
    if length > 600:
        issues.append(f"too_long: {length}")

    emoji_count = len(_EMOJI_RE.findall(text_str))
    if emoji_count == 0:
        issues.append("no_emoji")
    if emoji_count > 6:
        issues.append(f"too_many_emoji: {emoji_count}")

    found = [w for w in FORBIDDEN_WORDS if w in text_str]
    if found:
        issues.append(f"forbidden: {found}")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "length": length,
        "emoji_count": emoji_count,
    }


# =============================================================================
# 템플릿 fallback
# =============================================================================
def render_template(facts: WeeklyFacts) -> str:
    """LLM 실패 시 f-string 기반 최소 리포트."""
    if facts.is_empty():
        return (
            f"{facts.user_name}님, 이번 주 식사 기록이 아직 없어요 🍱\n"
            "식사를 기록하시면 더 맞춤 리포트를 드릴 수 있어요 😊"
        )

    if facts.lack:
        lack_message = f"{facts.lack[0]}이(가) 조금 부족했어요. 내일은 더 채워보세요! 💪"
    else:
        lack_message = "영양 균형이 꽤 괜찮았어요! 👍"

    template_path = TEMPLATES_DIR / "fallback.txt"
    if template_path.exists():
        template = template_path.read_text(encoding="utf-8")
    else:
        template = (
            "{user_name}님의 {week_label} 리포트예요 🍱\n\n"
            "이번 주 총 {meal_count}회 식사하셨고, "
            "평균 단백질 {avg_protein:.0f}g 섭취하셨어요.\n"
            "{lack_message}\n"
            "내일은 균형 잡힌 한 끼로 새로운 한 주를 시작해볼까요? ✨"
        )

    return template.format(
        user_name=facts.user_name,
        week_label=facts.week_label,
        meal_count=facts.meal_count,
        avg_protein=facts.avg_protein,
        lack_message=lack_message,
    )


def minimal_message(facts: WeeklyFacts) -> str:
    """최후 fallback."""
    return (
        f"{facts.user_name}님, 이번 주 {facts.meal_count}회 식사하셨어요. "
        "다음 주도 건강한 한 끼 되세요 🍱"
    )


# =============================================================================
# 결과 데이터 클래스
# =============================================================================
@dataclass
class ReportResult:
    report_id: Optional[int]
    user_id: str
    week_start: str
    week_label: str
    facts: dict[str, Any]
    nlg_text: str
    generation_method: str  # "llm" | "template" | "minimal"
    generated_at: str
    validation: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "user_id": self.user_id,
            "week_start": self.week_start,
            "week_label": self.week_label,
            "facts": self.facts,
            "nlg_text": self.nlg_text,
            "generation_method": self.generation_method,
            "generated_at": self.generated_at,
            "validation": self.validation,
        }


# =============================================================================
# 메인 클래스
# =============================================================================
class ReportGenerator:
    """주간 영양 리포트 생성기."""

    def __init__(
        self,
        ollama_client=None,
        max_retries: int = 2,
        temperature: float = 0.5,
        llm_client=None,
    ):
        # Phase 14: 'ollama_client'는 backward-compat 별칭. 우선순위: llm_client > ollama_client > factory.
        client = llm_client or ollama_client
        if client is None:
            from nlp_mvp.shared.llm.factory import get_report_client
            client = get_report_client()
        self.ollama = client
        self.llm = client
        self.max_retries = max_retries
        self.temperature = temperature
        logger.info(f"ReportGenerator initialized (provider={getattr(client, 'provider', '?')})")

    # -------------------------------------------------------------------------
    # 메인 진입점
    # -------------------------------------------------------------------------
    def generate(
        self,
        user_id: str | int,
        week_start: Optional[date] = None,
        save: bool = True,
    ) -> ReportResult:
        if save:
            ensure_schema()
        week_start = week_start or get_week_start()

        facts = extract_weekly_facts(user_id, week_start)
        nlg_text, method, validation = self._generate_with_fallback(facts)

        report_id = None
        if save:
            try:
                report_id = self._save(facts, nlg_text, method)
            except Exception as e:
                logger.warning(f"_save failed: {e}")

        return ReportResult(
            report_id=report_id,
            user_id=str(user_id),
            week_start=facts.week_start,
            week_label=facts.week_label,
            facts=facts.to_dict(),
            nlg_text=nlg_text,
            generation_method=method,
            generated_at=datetime.utcnow().isoformat(),
            validation=validation,
        )

    def get_or_generate(
        self,
        user_id: str | int,
        week_start: Optional[date] = None,
    ) -> ReportResult:
        """캐시 우선, 없으면 생성."""
        ensure_schema()
        week_start = week_start or get_week_start()
        existing = self._fetch_existing(user_id, week_start)
        if existing is not None:
            logger.info(f"Cached report hit: user={user_id}, week={week_start}")
            return existing
        return self.generate(user_id, week_start, save=True)

    # -------------------------------------------------------------------------
    # 3단계 fallback
    # -------------------------------------------------------------------------
    def _generate_with_fallback(
        self,
        facts: WeeklyFacts,
    ) -> tuple[str, str, dict[str, Any]]:
        # 1. LLM 시도
        for attempt in range(1, self.max_retries + 2):
            try:
                messages = build_report_prompt(facts)
                text_out = self.ollama.chat(
                    messages=messages,
                    options={"temperature": self.temperature, "num_predict": 400},
                )
                validation = validate_report(text_out)
                if validation["valid"]:
                    logger.info(f"LLM generate OK (attempt={attempt})")
                    return text_out, "llm", validation
                logger.warning(
                    f"LLM validation failed (attempt={attempt}): {validation['issues']}"
                )
            except Exception as e:
                logger.warning(f"LLM generate failed (attempt={attempt}): {e}")

        # 2. 템플릿 fallback
        try:
            text_out = render_template(facts)
            return text_out, "template", {"valid": True, "issues": [], "fallback": True}
        except Exception as e:
            logger.error(f"Template render failed: {e}")

        # 3. 최소 메시지
        return minimal_message(facts), "minimal", {"valid": True, "issues": [], "fallback": True}

    # -------------------------------------------------------------------------
    # DB 접근
    # -------------------------------------------------------------------------
    def _save(
        self,
        facts: WeeklyFacts,
        nlg_text: str,
        method: str,
    ) -> int:
        with get_session() as session:
            result = session.execute(
                text("""
                    INSERT INTO nutrition_reports
                        (user_id, week_start, facts, nlg_text, generation_method)
                    VALUES (:uid, :ws, :facts, :nlg, :method)
                    ON CONFLICT (user_id, week_start) DO UPDATE SET
                        facts = excluded.facts,
                        nlg_text = excluded.nlg_text,
                        generation_method = excluded.generation_method,
                        created_at = CURRENT_TIMESTAMP
                    RETURNING id
                """),
                {
                    "uid": facts.user_id,
                    "ws": facts.week_start,
                    "facts": json.dumps(facts.to_dict(), ensure_ascii=False),
                    "nlg": nlg_text,
                    "method": method,
                },
            )
            row = result.fetchone()
            session.commit()
            return int(row[0]) if row else -1

    def _fetch_existing(
        self,
        user_id: str | int,
        week_start: date,
    ) -> Optional[ReportResult]:
        try:
            with get_session() as session:
                row = session.execute(
                    text("""
                        SELECT id, facts, nlg_text, generation_method, created_at
                        FROM nutrition_reports
                        WHERE user_id = :uid AND week_start = :ws
                    """),
                    {"uid": str(user_id), "ws": week_start.isoformat()},
                ).fetchone()
            if not row:
                return None
            facts_dict = json.loads(row[1])
            return ReportResult(
                report_id=int(row[0]),
                user_id=str(user_id),
                week_start=week_start.isoformat(),
                week_label=facts_dict.get("week_label", ""),
                facts=facts_dict,
                nlg_text=row[2],
                generation_method=row[3],
                generated_at=str(row[4]),
                validation={"valid": True, "cached": True},
            )
        except Exception as e:
            logger.warning(f"_fetch_existing failed: {e}")
            return None


# =============================================================================
# CLI
# =============================================================================
def main():
    import argparse
    import logging

    parser = argparse.ArgumentParser(description="NLG 리포트 생성기")
    parser.add_argument("--user-id", type=str, required=True)
    parser.add_argument("--week-start", type=str, default=None, help="YYYY-MM-DD")
    parser.add_argument("--force", action="store_true", help="캐시 무시")
    parser.add_argument("--no-save", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    ws = date.fromisoformat(args.week_start) if args.week_start else None
    gen = ReportGenerator()
    if args.force:
        result = gen.generate(args.user_id, ws, save=not args.no_save)
    else:
        result = gen.get_or_generate(args.user_id, ws)

    print("\n" + "=" * 60)
    print(f"📊 {result.week_label} - {result.facts.get('user_name', '')}")
    print("=" * 60)
    print(result.nlg_text)
    print("=" * 60)
    print(f"method: {result.generation_method}")
    print(f"report_id: {result.report_id}")


if __name__ == "__main__":
    main()

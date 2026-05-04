"""
주간 meal_history 집계 → facts dict.
규칙 기반, 100% 정확한 수치만 담당.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta
from typing import Any, Optional

import pandas as pd
from sqlalchemy import text

from nlp_mvp.shared.db import get_engine
from nlp_mvp.shared.logger import get_logger

logger = get_logger(__name__)


# =============================================================================
# 기준값 (성인 기본)
# =============================================================================
DEFAULT_TARGETS = {
    "calories_per_day": 2000,
    "protein_per_day": 60,
    "carbs_per_day": 300,
    "fat_per_day": 55,
    "sodium_per_day": 2000,  # 상한
    "fiber_per_day": 25,
}

LACK_THRESHOLD = 0.8    # 권장의 80% 미만
EXCESS_THRESHOLD = 1.2  # 권장의 120% 이상


# =============================================================================
# 데이터 클래스
# =============================================================================
@dataclass
class WeeklyFacts:
    week_label: str
    week_start: str
    week_end: str
    user_id: str
    user_name: str
    meal_count: int
    total_calories: float
    avg_calories_per_meal: float
    avg_protein: float
    avg_carbs: float
    avg_fat: float
    avg_sodium: float
    target_calories: float
    target_protein: float
    lack: list[str] = field(default_factory=list)
    excess: list[str] = field(default_factory=list)
    best_day: Optional[dict] = None
    worst_day: Optional[dict] = None
    top_categories: list[tuple[str, int]] = field(default_factory=list)
    avg_satisfaction: Optional[float] = None
    has_nutrition_data: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def is_empty(self) -> bool:
        return self.meal_count == 0

    def is_sparse(self) -> bool:
        return 0 < self.meal_count < 3


# =============================================================================
# 주차 유틸
# =============================================================================
def get_week_start(d: Optional[date] = None) -> date:
    """해당 날짜가 속한 주의 월요일."""
    d = d or date.today()
    return d - timedelta(days=d.weekday())


def format_week_label(week_start: date) -> str:
    """'2026년 4월 1주차' 형식."""
    year = week_start.year
    month = week_start.month
    week_of_month = (week_start.day - 1) // 7 + 1
    return f"{year}년 {month}월 {week_of_month}주차"


# =============================================================================
# DB 로딩
# =============================================================================
def _table_columns(table_name: str) -> set[str]:
    engine = get_engine()
    try:
        with engine.connect() as conn:
            rows = conn.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
        return {str(row[1]) for row in rows}
    except Exception as e:
        logger.warning(f"_table_columns({table_name}) failed: {e}")
        return set()


def _load_user_profile(user_id: str | int) -> dict[str, Any]:
    engine = get_engine()
    uid = str(user_id)
    try:
        user_columns = _table_columns("users")
        if {"target_calories", "target_protein"}.issubset(user_columns):
            query = "SELECT name, target_calories, target_protein FROM users WHERE id = :uid"
        else:
            query = "SELECT name FROM users WHERE id = :uid"
        with engine.connect() as conn:
            row = conn.execute(text(query), {"uid": uid}).fetchone()
        if row:
            return {
                "name": row[0] or f"사용자{uid}",
                "target_calories": (
                    row[1] if len(row) > 1 and row[1] is not None
                    else DEFAULT_TARGETS["calories_per_day"]
                ),
                "target_protein": (
                    row[2] if len(row) > 2 and row[2] is not None
                    else DEFAULT_TARGETS["protein_per_day"]
                ),
            }
    except Exception as e:
        logger.warning(f"_load_user_profile failed: {e}")

    return {
        "name": f"사용자{uid}",
        "target_calories": DEFAULT_TARGETS["calories_per_day"],
        "target_protein": DEFAULT_TARGETS["protein_per_day"],
    }


def _load_meals_df(user_id: str | int, week_start: date) -> pd.DataFrame:
    engine = get_engine()
    week_end = week_start + timedelta(days=7)
    meal_columns = _table_columns("meal_history")
    if {"calories", "protein", "carbs", "fat", "sodium", "menu_name"}.issubset(meal_columns):
        needs_review_expr = (
            "COALESCE(mh.needs_review, 0)"
            if "needs_review" in meal_columns else "0"
        )
        source_expr = (
            "mh.nutrition_source"
            if "nutrition_source" in meal_columns else "'direct_columns'"
        )
        query = """
            SELECT mh.meal_date,
                   mh.menu_name AS menu,
                   mh.satisfaction,
                   COALESCE(mh.calories, 0) AS calories,
                   COALESCE(mh.protein, 0)  AS protein,
                   COALESCE(mh.carbs, 0)    AS carbs,
                   COALESCE(mh.fat, 0)      AS fat,
                   COALESCE(mh.sodium, 0)   AS sodium,
                   {needs_review_expr} AS needs_review,
                   {source_expr} AS nutrition_source,
                   r.category
            FROM meal_history mh
            LEFT JOIN restaurants r ON mh.restaurant_id = r.id
            WHERE mh.user_id = :uid
              AND mh.meal_date >= :start
              AND mh.meal_date < :end
            ORDER BY mh.meal_date
        """.format(needs_review_expr=needs_review_expr, source_expr=source_expr)
    else:
        query = """
            SELECT mh.meal_date,
                   mh.menu,
                   mh.satisfaction,
                   COALESCE(ni.calories, 0) AS calories,
                   COALESCE(ni.protein, 0)  AS protein,
                   COALESCE(ni.carbs, 0)    AS carbs,
                   COALESCE(ni.fat, 0)      AS fat,
                   COALESCE(ni.sodium, 0)   AS sodium,
                   0 AS needs_review,
                   'legacy_join' AS nutrition_source,
                   r.category
            FROM meal_history mh
            LEFT JOIN nutrition_info ni ON mh.normalized_menu_id = ni.id
            LEFT JOIN restaurants r ON mh.restaurant_id = r.id
            WHERE mh.user_id = :uid
              AND mh.meal_date >= :start
              AND mh.meal_date < :end
            ORDER BY mh.meal_date
        """
    try:
        with engine.connect() as conn:
            return pd.read_sql(
                text(query),
                conn,
                params={
                    "uid": str(user_id),
                    "start": week_start.isoformat(),
                    "end": week_end.isoformat(),
                },
            )
    except Exception as e:
        logger.warning(f"_load_meals_df failed: {e}")
        return pd.DataFrame()


# =============================================================================
# 점수·판정 유틸
# =============================================================================
def day_balance_score(row) -> float:
    """일일 영양 균형 점수 (0~1)."""
    target = DEFAULT_TARGETS
    values = {
        "calories": row.get("calories", 0) if hasattr(row, "get") else row["calories"],
        "protein": row.get("protein", 0) if hasattr(row, "get") else row["protein"],
        "carbs": row.get("carbs", 0) if hasattr(row, "get") else row["carbs"],
        "fat": row.get("fat", 0) if hasattr(row, "get") else row["fat"],
    }
    deviations = []
    for k, v in values.items():
        t = target[f"{k}_per_day"]
        if t > 0 and v > 0:
            deviations.append(abs(v - t) / t)
    if not deviations:
        return 0.0
    return max(0.0, 1.0 - sum(deviations) / len(deviations))


def detect_lack_excess(
    avg: dict[str, float],
    targets: dict[str, float],
) -> tuple[list[str], list[str]]:
    lack: list[str] = []
    excess: list[str] = []

    if avg["protein"] < targets["target_protein"] * LACK_THRESHOLD:
        lack.append("단백질")

    if avg["calories"] < targets["target_calories"] * LACK_THRESHOLD:
        lack.append("칼로리")
    elif avg["calories"] > targets["target_calories"] * EXCESS_THRESHOLD:
        excess.append("칼로리")

    if avg["sodium"] > DEFAULT_TARGETS["sodium_per_day"] * EXCESS_THRESHOLD:
        excess.append("나트륨")

    if avg["fat"] > DEFAULT_TARGETS["fat_per_day"] * EXCESS_THRESHOLD:
        excess.append("지방")

    return lack, excess


# =============================================================================
# 메인 진입점
# =============================================================================
def extract_weekly_facts(
    user_id: str | int,
    week_start: Optional[date] = None,
) -> WeeklyFacts:
    """주간 meal_history 집계 → WeeklyFacts."""
    week_start = week_start or get_week_start()
    week_end = week_start + timedelta(days=7)

    uid = str(user_id)
    profile = _load_user_profile(uid)
    df = _load_meals_df(uid, week_start)

    facts = WeeklyFacts(
        week_label=format_week_label(week_start),
        week_start=week_start.isoformat(),
        week_end=week_end.isoformat(),
        user_id=uid,
        user_name=profile["name"],
        meal_count=len(df),
        total_calories=0,
        avg_calories_per_meal=0,
        avg_protein=0,
        avg_carbs=0,
        avg_fat=0,
        avg_sodium=0,
        target_calories=profile["target_calories"],
        target_protein=profile["target_protein"],
        has_nutrition_data=False,
    )

    if facts.is_empty():
        return facts

    # 영양 데이터 유효성
    facts.has_nutrition_data = float(df["calories"].sum()) > 0

    facts.total_calories = float(df["calories"].sum())
    facts.avg_calories_per_meal = float(df["calories"].mean())
    facts.avg_protein = float(df["protein"].mean())
    facts.avg_carbs = float(df["carbs"].mean())
    facts.avg_fat = float(df["fat"].mean())
    facts.avg_sodium = float(df["sodium"].mean())

    if "satisfaction" in df.columns:
        sat = df["satisfaction"].dropna()
        if len(sat) > 0:
            facts.avg_satisfaction = float(sat.mean())

    # 부족/과다 판정 (끼당 환산)
    avg = {
        "calories": facts.avg_calories_per_meal,
        "protein": facts.avg_protein,
        "sodium": facts.avg_sodium,
        "fat": facts.avg_fat,
    }
    targets = {
        "target_calories": facts.target_calories / 3,
        "target_protein": facts.target_protein / 3,
    }
    facts.lack, facts.excess = detect_lack_excess(avg, targets)

    # Best/Worst day
    if facts.has_nutrition_data:
        df = df.copy()
        df["balance_score"] = df.apply(day_balance_score, axis=1)
        best_idx = df["balance_score"].idxmax()
        worst_idx = df["balance_score"].idxmin()
        facts.best_day = {
            "date": str(df.loc[best_idx, "meal_date"]),
            "menu": str(df.loc[best_idx, "menu"] or ""),
            "balance_score": float(df.loc[best_idx, "balance_score"]),
            "reason": "가장 균형 잡힌 하루",
        }
        facts.worst_day = {
            "date": str(df.loc[worst_idx, "meal_date"]),
            "menu": str(df.loc[worst_idx, "menu"] or ""),
            "balance_score": float(df.loc[worst_idx, "balance_score"]),
            "reason": "균형이 아쉬웠던 날",
        }

    # Top categories
    if "category" in df.columns:
        cat_counter = Counter(df["category"].dropna().tolist())
        facts.top_categories = cat_counter.most_common(3)

    logger.info(
        f"extract_weekly_facts(user={user_id}, week={facts.week_label}): "
        f"meals={facts.meal_count}, lack={facts.lack}, excess={facts.excess}"
    )
    return facts

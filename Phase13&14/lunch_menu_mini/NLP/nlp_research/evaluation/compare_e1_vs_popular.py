"""
E1 vs Popular vs Random — wraps embedding_cf.evaluate.evaluate_recommenders
and writes the markdown summary.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from nlp_research.models.embedding_cf.evaluate import evaluate_recommenders
from nlp_research.models.embedding_cf.recommender import MealHistorySource


def run_comparison(
    seed_users: int = 8,
    smoke: bool = False,
    use_sbert: bool = False,
    from_db: bool = False,
) -> dict[str, Any]:
    if from_db:
        try:
            source = MealHistorySource.from_db()
        except Exception:
            source = MealHistorySource.synthetic(seed_users)
    else:
        source = MealHistorySource.synthetic(
            n_users=3 if smoke else seed_users
        )
    return evaluate_recommenders(source, top_n=10, use_sbert=use_sbert)


def write_markdown(result: dict, out_path: Path) -> None:
    n = result.get("n_users", 0)
    lines = [
        "# E1 vs Popular vs Random — Leave-One-Out",
        "",
        f"- users: **{n}**",
        "",
        "| System | Hit@5 | Hit@10 | NDCG@10 | MRR | Coverage | Diversity |",
        "|---|---|---|---|---|---|---|",
    ]
    for name in ("random", "popular", "e1"):
        m = result.get(name, {})
        lines.append(
            f"| {name} | "
            f"{m.get('hit@5', 0):.4f} | "
            f"{m.get('hit@10', 0):.4f} | "
            f"{m.get('ndcg@10', 0):.4f} | "
            f"{m.get('mrr', 0):.4f} | "
            f"{m.get('coverage', 0):.4f} | "
            f"{m.get('diversity', 0):.4f} |"
        )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


__all__ = ["run_comparison", "write_markdown"]

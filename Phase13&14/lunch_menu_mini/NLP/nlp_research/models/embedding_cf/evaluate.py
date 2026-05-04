"""
E1 evaluation — Leave-One-Out + Hit@K, NDCG@K, Coverage, Diversity.

For each user, the most-recent meal is held out as ground truth, the remaining
history is used to build the index, and we check whether the held-out menu
appears in the top-K recommendations.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

from nlp_research.evaluation.baselines import (
    PopularRecommender,
    RandomRecommender,
)
from nlp_research.models.embedding_cf.embedder import UserEmbedder
from nlp_research.models.embedding_cf.recommender import (
    EmbeddingCFRecommender,
    MealHistorySource,
)
from nlp_research.training.metrics import (
    compute_coverage,
    compute_diversity,
    compute_ranking_metrics,
)


def leave_one_out_split(source: MealHistorySource) -> tuple[MealHistorySource, dict]:
    """
    Hold out the most-recent meal per user as ground-truth.
    Returns (training_source, {user_id: held_out_menu_name}).
    """
    train_history: dict[Any, list[dict]] = {}
    held_out: dict[Any, str] = {}
    for uid, rows in source.meal_history.items():
        if len(rows) < 2:
            train_history[uid] = list(rows)
            continue
        sorted_rows = sorted(rows, key=lambda r: r.get("meal_date", ""))
        train_history[uid] = sorted_rows[:-1]
        held_out[uid] = sorted_rows[-1].get("menu_name", "")
    return MealHistorySource(train_history), held_out


def evaluate_recommenders(
    source: MealHistorySource,
    top_n: int = 10,
    use_sbert: bool = False,
) -> dict[str, Any]:
    """Run LOO across Random / Popular / E1 and return metric dicts."""
    train_source, held_out = leave_one_out_split(source)
    user_ids = [uid for uid in held_out.keys() if held_out[uid]]
    if not user_ids:
        return {"error": "no users with held-out item"}

    # All menus seen anywhere — used by Coverage
    all_menus = set()
    for rows in source.meal_history.values():
        for r in rows:
            menu = r.get("menu_name")
            if menu:
                all_menus.add(menu)

    rec_e1 = EmbeddingCFRecommender(
        train_source, embedder=UserEmbedder(use_sbert=use_sbert)
    )
    rec_e1.build_index()
    rec_pop = PopularRecommender(train_source)
    rec_rand = RandomRecommender(train_source, seed=42)

    def _call_recommend(rec, uid):
        # E1 uses `top_n_menus`, baselines use `top_n` — try both.
        try:
            return rec.recommend(uid, top_n=top_n)
        except TypeError:
            return rec.recommend(uid, top_n_menus=top_n)

    def _gather(recommender) -> tuple[list, list]:
        preds_per_user = []
        ground = []
        for uid in user_ids:
            recs = _call_recommend(recommender, uid)
            preds_per_user.append([r["menu"] for r in recs])
            ground.append(held_out[uid])
        return preds_per_user, ground

    result: dict[str, Any] = {}
    for name, rec in [
        ("random", rec_rand),
        ("popular", rec_pop),
        ("e1", rec_e1),
    ]:
        preds, ground = _gather(rec)
        metrics = compute_ranking_metrics(preds, ground, k_values=(5, 10))
        metrics["coverage"] = compute_coverage(all_menus, preds)
        metrics["diversity"] = compute_diversity(preds)
        result[name] = metrics

    result["n_users"] = len(user_ids)
    return result


def _write_markdown(result: dict, out_path: Path) -> None:
    n = result.get("n_users", 0)
    lines = [
        "# E1 Embedding CF — Leave-One-Out Evaluation",
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


def main() -> int:
    ap = argparse.ArgumentParser(description="Evaluate E1 Embedding CF (LOO)")
    ap.add_argument("--seed-users", type=int, default=8, help="Synthetic user count")
    ap.add_argument("--from-db", action="store_true", help="Load from mini.db")
    ap.add_argument("--use-sbert", action="store_true", help="Use real Sentence-BERT")
    ap.add_argument(
        "--output",
        type=Path,
        default=Path("report/benchmarks/e1_loo.md"),
    )
    args = ap.parse_args()

    if args.from_db:
        try:
            source = MealHistorySource.from_db()
        except Exception as e:
            print(f"[evaluate] DB load failed ({e}); falling back to synthetic", file=sys.stderr)
            source = MealHistorySource.synthetic(args.seed_users)
    else:
        source = MealHistorySource.synthetic(args.seed_users)

    result = evaluate_recommenders(source, use_sbert=args.use_sbert)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    _write_markdown(result, args.output)
    return 0


__all__ = ["leave_one_out_split", "evaluate_recommenders"]


if __name__ == "__main__":
    raise SystemExit(main())

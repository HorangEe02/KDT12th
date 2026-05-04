"""B2 Food NER evaluation — entity-level precision/recall/F1 + per-type."""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

from nlp_research.models.food_ner.dataset import (
    entities_from_tags,
    load_food_ner_jsonl,
)
from nlp_research.models.food_ner.model import ENTITY_TYPES, LABELS
from nlp_research.training.metrics import compute_ner_metrics


def evaluate_food_ner(
    data_path: str | Path,
    pred_tags: list[list[str]] | None = None,
) -> dict:
    """Compute entity-level metrics + per-type counts. Random fallback if no predictions."""
    rows = load_food_ner_jsonl(data_path)
    if not rows:
        return {"error": "no rows", "overall": {}}

    true_tags = [r["tags"] for r in rows]
    if pred_tags is None:
        rng = random.Random(42)
        pred_tags = [
            [rng.choice(LABELS) for _ in tags] for tags in true_tags
        ]
    if len(pred_tags) != len(true_tags):
        raise ValueError(
            f"prediction length mismatch: {len(pred_tags)} vs {len(true_tags)}"
        )

    overall = compute_ner_metrics(true_tags, pred_tags)

    # Per-type entity counts
    per_type: dict[str, dict[str, int]] = {
        t: {"true": 0, "pred": 0, "match": 0} for t in ENTITY_TYPES
    }
    for tokens_row, true_row, pred_row in zip(
        [r["tokens"] for r in rows], true_tags, pred_tags
    ):
        true_ents = {
            (e["type"], e["value"]) for e in entities_from_tags(tokens_row, true_row)
        }
        pred_ents = {
            (e["type"], e["value"]) for e in entities_from_tags(tokens_row, pred_row)
        }
        for t, _ in true_ents:
            per_type[t]["true"] += 1
        for t, _ in pred_ents:
            per_type[t]["pred"] += 1
        for t, _ in (true_ents & pred_ents):
            per_type[t]["match"] += 1

    return {
        "overall": overall,
        "per_type": per_type,
        "n_samples": len(rows),
    }


def _write_markdown(result: dict, out_path: Path) -> None:
    lines = [
        "# B2 Food NER Evaluation",
        "",
        f"- samples: **{result.get('n_samples', 0)}**",
    ]
    overall = result.get("overall", {})
    if "entity_f1" in overall:
        lines.append(f"- entity F1: **{overall['entity_f1']:.4f}**")
        lines.append(f"- entity precision: **{overall['entity_precision']:.4f}**")
        lines.append(f"- entity recall: **{overall['entity_recall']:.4f}**")
    lines.append("")
    lines.append("## Per-type entity counts")
    lines.append("| Type | True | Pred | Match |")
    lines.append("|---|---|---|---|")
    for t, counts in result.get("per_type", {}).items():
        lines.append(
            f"| {t} | {counts['true']} | {counts['pred']} | {counts['match']} |"
        )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Evaluate B2 Food NER")
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--model", type=Path, default=None)
    ap.add_argument(
        "--output",
        type=Path,
        default=Path("report/benchmarks/food_ner_eval.md"),
    )
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not args.data.exists():
        print(f"[evaluate] data not found: {args.data}", file=sys.stderr)
        return 2
    result = evaluate_food_ner(args.data, pred_tags=None)
    print(json.dumps(
        {k: v for k, v in result.items() if k != "overall"},
        indent=2,
        ensure_ascii=False,
    ))
    _write_markdown(result, args.output)
    return 0


__all__ = ["evaluate_food_ner"]


if __name__ == "__main__":
    raise SystemExit(main())

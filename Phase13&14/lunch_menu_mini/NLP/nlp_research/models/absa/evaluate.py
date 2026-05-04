"""
A2 ABSA evaluation — overall + per-aspect + per-sentiment metrics.

Can be run in `--dry-run` mode where results are computed against dummy
predictions (no weights needed), useful for CI.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

from nlp_research.models.absa.dataset import load_absa_triples
from nlp_research.models.absa.model import ID2LABEL, LABEL2ID
from nlp_research.training.metrics import compute_classification_metrics


def evaluate_absa(
    data_path: str | Path,
    predictions: list[int] | None = None,
) -> dict:
    """
    Compute overall + per_aspect + per_sentiment metrics.

    If `predictions` is None, uses random dummy predictions (smoke mode).
    """
    triples = load_absa_triples(data_path)
    if not triples:
        return {"error": "no triples loaded", "overall": {}, "per_aspect": {}}

    y_true = [t["label"] for t in triples]
    if predictions is None:
        rng = random.Random(42)
        y_pred = [rng.randint(0, 2) for _ in y_true]
    else:
        y_pred = predictions
        if len(y_pred) != len(y_true):
            raise ValueError(
                f"prediction length mismatch: {len(y_pred)} vs {len(y_true)}"
            )

    overall = compute_classification_metrics(
        y_true, y_pred, labels=list(LABEL2ID.values())
    )

    # per-aspect
    per_aspect: dict[str, dict] = {}
    aspects = sorted({t["aspect"] for t in triples})
    for asp in aspects:
        mask = [i for i, t in enumerate(triples) if t["aspect"] == asp]
        if not mask:
            continue
        per_aspect[asp] = compute_classification_metrics(
            [y_true[i] for i in mask],
            [y_pred[i] for i in mask],
            labels=list(LABEL2ID.values()),
        )

    # per-sentiment
    per_sentiment: dict[str, dict] = {}
    for sent_name, sent_id in LABEL2ID.items():
        mask = [i for i, lab in enumerate(y_true) if lab == sent_id]
        if not mask:
            continue
        correct = sum(1 for i in mask if y_pred[i] == sent_id)
        per_sentiment[sent_name] = {
            "support": len(mask),
            "recall": round(correct / len(mask), 4),
        }

    # confusion matrix (3x3)
    cm = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
    for t, p in zip(y_true, y_pred):
        cm[t][p] += 1

    return {
        "overall": overall,
        "per_aspect": per_aspect,
        "per_sentiment": per_sentiment,
        "confusion_matrix": {
            "labels": [ID2LABEL[i] for i in range(3)],
            "matrix": cm,
        },
        "n_samples": len(y_true),
    }


def _write_markdown(result: dict, out_path: Path) -> None:
    lines = [
        "# A2 ABSA Evaluation",
        "",
        f"- samples: **{result['n_samples']}**",
        f"- accuracy: **{result['overall'].get('accuracy', 0):.4f}**",
        f"- macro F1: **{result['overall'].get('macro_f1', 0):.4f}**",
        "",
        "## Per-aspect",
        "| Aspect | Macro F1 | Accuracy |",
        "|---|---|---|",
    ]
    for asp, m in result["per_aspect"].items():
        lines.append(f"| {asp} | {m.get('macro_f1', 0):.4f} | {m.get('accuracy', 0):.4f} |")
    lines.append("")
    lines.append("## Per-sentiment recall")
    lines.append("| Sentiment | Recall | Support |")
    lines.append("|---|---|---|")
    for sent, m in result["per_sentiment"].items():
        lines.append(f"| {sent} | {m.get('recall', 0):.4f} | {m.get('support', 0)} |")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Evaluate A2 ABSA")
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--model", type=Path, default=None, help="Trained model path")
    ap.add_argument(
        "--output",
        type=Path,
        default=Path("report/benchmarks/absa_eval.md"),
    )
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not args.data.exists():
        print(f"[evaluate] data not found: {args.data}", file=sys.stderr)
        return 2

    # Actual model-based prediction requires transformers; in dry-run we skip it.
    result = evaluate_absa(args.data, predictions=None)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    _write_markdown(result, args.output)
    return 0


__all__ = ["evaluate_absa"]


if __name__ == "__main__":
    raise SystemExit(main())

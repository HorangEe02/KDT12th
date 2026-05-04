"""
Metric computation utilities.

All metric functions are pure-Python (no torch) so they can be used from
benchmark.py and evaluate.py without forcing heavy deps. `compute_ner_metrics`
uses seqeval which is a lightweight PyPI package.
"""
from __future__ import annotations

import math
from collections import Counter
from typing import Any, Sequence


# =============================================================================
# Classification
# =============================================================================
def compute_classification_metrics(
    y_true: Sequence[Any],
    y_pred: Sequence[Any],
    labels: Sequence[Any] | None = None,
) -> dict[str, Any]:
    """
    Compute accuracy + per-class precision/recall/F1 + macro F1.

    Pure-Python, no numpy/sklearn dependency.
    """
    if len(y_true) != len(y_pred):
        raise ValueError(f"length mismatch: {len(y_true)} vs {len(y_pred)}")
    total = len(y_true)
    if total == 0:
        return {"accuracy": 0.0, "macro_f1": 0.0, "per_class": {}}

    correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
    accuracy = correct / total

    all_labels = set(y_true) | set(y_pred)
    if labels is not None:
        all_labels = set(labels) | all_labels

    per_class: dict[Any, dict[str, float]] = {}
    f1_sum = 0.0
    for lab in sorted(all_labels, key=str):
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == lab and p == lab)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != lab and p == lab)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == lab and p != lab)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )
        per_class[str(lab)] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "support": sum(1 for t in y_true if t == lab),
        }
        f1_sum += f1

    macro_f1 = f1_sum / max(len(all_labels), 1)
    return {
        "accuracy": round(accuracy, 4),
        "macro_f1": round(macro_f1, 4),
        "per_class": per_class,
    }


# =============================================================================
# NER (seqeval wrapper)
# =============================================================================
def compute_ner_metrics(
    y_true: list[list[str]],
    y_pred: list[list[str]],
) -> dict[str, Any]:
    """
    Entity-level precision/recall/F1 using seqeval.

    If seqeval is not installed, falls back to a naive token-level metric.
    """
    try:
        from seqeval.metrics import (
            classification_report,
            f1_score,
            precision_score,
            recall_score,
        )
    except ImportError:
        # Fallback: flatten and compute token-level
        flat_true = [t for seq in y_true for t in seq]
        flat_pred = [p for seq in y_pred for p in seq]
        return compute_classification_metrics(flat_true, flat_pred)

    return {
        "entity_precision": round(precision_score(y_true, y_pred), 4),
        "entity_recall": round(recall_score(y_true, y_pred), 4),
        "entity_f1": round(f1_score(y_true, y_pred), 4),
        "report": classification_report(y_true, y_pred, digits=4),
    }


# =============================================================================
# Ranking (Hit@K, NDCG@K, MRR)
# =============================================================================
def _dcg(relevances: list[float]) -> float:
    return sum(r / math.log2(i + 2) for i, r in enumerate(relevances))


def compute_ranking_metrics(
    predicted: list[list[Any]],
    ground_truth: list[Any],
    k_values: tuple[int, ...] = (5, 10),
) -> dict[str, float]:
    """
    Ranking metrics: Hit@K, NDCG@K, MRR.

    Args:
        predicted: list of ranked lists (one per query).
        ground_truth: one relevant item per query (single-target leave-one-out).
        k_values: cutoffs for Hit@K and NDCG@K.
    """
    assert len(predicted) == len(ground_truth)
    n = len(predicted)
    if n == 0:
        return {f"hit@{k}": 0.0 for k in k_values} | {
            f"ndcg@{k}": 0.0 for k in k_values
        } | {"mrr": 0.0}

    result: dict[str, float] = {}
    for k in k_values:
        hits = 0
        ndcg_sum = 0.0
        for preds, truth in zip(predicted, ground_truth):
            topk = preds[:k]
            if truth in topk:
                hits += 1
                # single-relevant DCG
                rank = topk.index(truth) + 1
                ideal = 1.0 / math.log2(2)
                dcg = 1.0 / math.log2(rank + 1)
                ndcg_sum += dcg / ideal
        result[f"hit@{k}"] = round(hits / n, 4)
        result[f"ndcg@{k}"] = round(ndcg_sum / n, 4)

    # MRR
    mrr_sum = 0.0
    for preds, truth in zip(predicted, ground_truth):
        if truth in preds:
            rank = preds.index(truth) + 1
            mrr_sum += 1.0 / rank
    result["mrr"] = round(mrr_sum / n, 4)
    return result


def compute_coverage(
    all_items: set[Any],
    recommended: list[list[Any]],
) -> float:
    """Catalog coverage: (distinct recommended items) / (all items)."""
    if not all_items:
        return 0.0
    recommended_set: set[Any] = set()
    for recs in recommended:
        recommended_set.update(recs)
    return round(len(recommended_set & all_items) / len(all_items), 4)


def compute_diversity(
    recommended: list[list[Any]],
    category_fn=None,
) -> float:
    """
    Intra-list diversity: average number of distinct categories per recommendation list.
    If category_fn is None, counts distinct items directly.
    """
    if not recommended:
        return 0.0
    scores = []
    for recs in recommended:
        if not recs:
            continue
        if category_fn is None:
            scores.append(len(set(recs)) / len(recs))
        else:
            cats = {category_fn(r) for r in recs}
            scores.append(len(cats) / len(recs))
    return round(sum(scores) / max(len(scores), 1), 4)


__all__ = [
    "compute_classification_metrics",
    "compute_ner_metrics",
    "compute_ranking_metrics",
    "compute_coverage",
    "compute_diversity",
]

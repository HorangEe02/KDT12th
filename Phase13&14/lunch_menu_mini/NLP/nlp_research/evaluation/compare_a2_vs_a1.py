"""
A2 vs A1 — aspect-based vs single-sentiment comparison.

A1 = Phase 5 SentimentAnalyzer (or DummyA1 in smoke mode)
A2 = nlp_research.models.absa.inference.DummyABSAInferencer (or trained)

Metrics:
- overlap_rate: how often A2's averaged sentiment matches A1's single sentiment
- mixed_sentiment_recall: how often A2 detects 2+ distinct sentiments in one review
- latency_ms: per-call average
"""
from __future__ import annotations

import random
import time
from collections import Counter
from pathlib import Path
from typing import Any

from nlp_research.models.absa.dataset import load_absa_triples
from nlp_research.models.absa.inference import DummyABSAInferencer, load_inferencer


def _dummy_a1(text: str) -> str:
    """Smoke-mode placeholder when nlp_mvp.SentimentAnalyzer isn't usable."""
    seed = sum(ord(c) for c in text) % 3
    return ["positive", "neutral", "negative"][seed]


def _try_a1():
    """Return a callable `(text) -> sentiment_str`. Falls back to dummy."""
    try:
        from nlp_mvp.sentiment.sentiment_pipeline import SentimentAnalyzer
        analyzer = SentimentAnalyzer()
        def predict(text: str) -> str:
            r = analyzer.analyze(text)
            return r.get("label", "neutral")
        return predict
    except Exception:
        return _dummy_a1


def _majority_sentiment(per_aspect: list[dict[str, Any]]) -> str:
    counts = Counter(p["sentiment"] for p in per_aspect)
    return counts.most_common(1)[0][0] if counts else "neutral"


def run_comparison(
    seed_path: str | Path,
    sample_size: int = 50,
    smoke: bool = False,
    a2_model_path: str | Path | None = None,
) -> dict[str, Any]:
    triples = load_absa_triples(seed_path)
    # Group triples by review text
    by_text: dict[str, list[dict]] = {}
    for t in triples:
        by_text.setdefault(t["text"], []).append(t)
    reviews = list(by_text.keys())
    if smoke:
        reviews = reviews[:5]
    else:
        reviews = reviews[:sample_size]

    a1 = _dummy_a1 if smoke else _try_a1()
    a2 = DummyABSAInferencer(seed=42) if smoke else load_inferencer(a2_model_path)

    overlap_hits = 0
    mixed_detect = 0
    mixed_truth = 0
    a1_lat: list[float] = []
    a2_lat: list[float] = []

    for text in reviews:
        # Truth: does this review have multiple distinct sentiments?
        truth = by_text[text]
        truth_sentiments = {t["sentiment"] for t in truth}
        is_mixed_truth = len(truth_sentiments) >= 2
        if is_mixed_truth:
            mixed_truth += 1

        t0 = time.perf_counter()
        a1_label = a1(text)
        a1_lat.append((time.perf_counter() - t0) * 1000)

        t1 = time.perf_counter()
        a2_pred = a2.predict(text)
        a2_lat.append((time.perf_counter() - t1) * 1000)

        a2_majority = _majority_sentiment(a2_pred)
        if a2_majority == a1_label:
            overlap_hits += 1

        if len({p["sentiment"] for p in a2_pred}) >= 2 and is_mixed_truth:
            mixed_detect += 1

    n = len(reviews)
    return {
        "n_reviews": n,
        "overlap_rate": round(overlap_hits / max(n, 1), 4),
        "mixed_sentiment_recall": round(
            mixed_detect / max(mixed_truth, 1), 4
        ),
        "a1_latency_ms": round(sum(a1_lat) / max(len(a1_lat), 1), 2),
        "a2_latency_ms": round(sum(a2_lat) / max(len(a2_lat), 1), 2),
        "smoke": smoke,
    }


def write_markdown(result: dict, out_path: Path) -> None:
    lines = [
        "# A2 vs A1 — Sentiment comparison",
        "",
        f"- reviews: **{result['n_reviews']}**",
        f"- overlap (A2 majority == A1): **{result['overlap_rate']:.4f}**",
        f"- mixed-sentiment recall (A2): **{result['mixed_sentiment_recall']:.4f}**",
        f"- A1 latency: {result['a1_latency_ms']} ms",
        f"- A2 latency: {result['a2_latency_ms']} ms",
        f"- smoke mode: {result['smoke']}",
    ]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


__all__ = ["run_comparison", "write_markdown"]

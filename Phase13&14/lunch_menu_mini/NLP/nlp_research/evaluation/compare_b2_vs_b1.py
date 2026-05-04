"""
B2 (Food NER) vs B1 (Menu Normalizer) — entity extraction comparison.

B1 = nlp_mvp.menu_normalizer.normalizer.MenuNormalizer (matched_name only)
B2 = nlp_research.models.food_ner.inference (rule-based fallback in smoke)

Metrics:
- token_precision / token_recall / token_f1 — DISH token overlap with truth
- allergen_recall — % of seed sentences with ALLERGEN that B2 catches (B1=0)
- latency_ms
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from nlp_research.models.food_ner.dataset import (
    entities_from_tags,
    load_food_ner_jsonl,
)
from nlp_research.models.food_ner.inference import (
    RuleBasedFoodNERInferencer,
    extract_allergens,
    load_inferencer,
)


def _try_b1():
    """Return a callable `(text) -> matched_name | None`."""
    try:
        from nlp_mvp.menu_normalizer.normalizer import MenuNormalizer
        norm = MenuNormalizer(enable_embedding=False)
        def predict(text: str) -> str | None:
            res = norm.normalize(text)
            return res.matched_name
        return predict
    except Exception:
        return None


def run_comparison(
    seed_path: str | Path,
    sample_size: int = 50,
    smoke: bool = False,
    b2_model_path: str | Path | None = None,
) -> dict[str, Any]:
    rows = load_food_ner_jsonl(seed_path)
    if smoke:
        rows = rows[:5]
    else:
        rows = rows[:sample_size]

    b1 = _try_b1()
    b2 = (
        RuleBasedFoodNERInferencer()
        if smoke
        else load_inferencer(b2_model_path)
    )

    # Compute truth: per-row DISH token sets
    truth_dish_tokens: list[set[str]] = []
    truth_allergens: list[set[str]] = []
    texts: list[str] = []
    for r in rows:
        ents = entities_from_tags(r["tokens"], r["tags"])
        truth_dish_tokens.append(
            {e["value"] for e in ents if e["type"] == "DISH"}
        )
        truth_allergens.append(
            {e["value"] for e in ents if e["type"] == "ALLERGEN"}
        )
        texts.append(" ".join(r["tokens"]))

    # B1: matched menu name → single-token "DISH"
    b1_dish_tokens: list[set[str]] = []
    b1_lat: list[float] = []
    for text in texts:
        t0 = time.perf_counter()
        if b1 is None:
            matched = None
        else:
            try:
                matched = b1(text)
            except Exception:
                matched = None
        b1_lat.append((time.perf_counter() - t0) * 1000)
        b1_dish_tokens.append({matched} if matched else set())

    # B2: NER → DISH values
    b2_dish_tokens: list[set[str]] = []
    b2_allergens: list[set[str]] = []
    b2_lat: list[float] = []
    for text in texts:
        t0 = time.perf_counter()
        ents = b2.predict(text)
        b2_lat.append((time.perf_counter() - t0) * 1000)
        b2_dish_tokens.append({e["value"] for e in ents if e["type"] == "DISH"})
        b2_allergens.append({e["value"] for e in ents if e["type"] == "ALLERGEN"})

    def _prf(true_sets, pred_sets):
        tp = fp = fn = 0
        for t, p in zip(true_sets, pred_sets):
            tp += len(t & p)
            fp += len(p - t)
            fn += len(t - p)
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (
            2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        )
        return round(prec, 4), round(rec, 4), round(f1, 4)

    b1_p, b1_r, b1_f1 = _prf(truth_dish_tokens, b1_dish_tokens)
    b2_p, b2_r, b2_f1 = _prf(truth_dish_tokens, b2_dish_tokens)

    n_with_allergen = sum(1 for s in truth_allergens if s)
    b2_allergen_hits = sum(
        1
        for truth, pred in zip(truth_allergens, b2_allergens)
        if truth and (truth & pred)
    )
    b2_allergen_recall = (
        round(b2_allergen_hits / n_with_allergen, 4) if n_with_allergen else 0.0
    )

    return {
        "n_sentences": len(rows),
        "b1": {
            "precision": b1_p,
            "recall": b1_r,
            "f1": b1_f1,
            "latency_ms": round(sum(b1_lat) / max(len(b1_lat), 1), 2),
            "allergen_recall": 0.0,
        },
        "b2": {
            "precision": b2_p,
            "recall": b2_r,
            "f1": b2_f1,
            "latency_ms": round(sum(b2_lat) / max(len(b2_lat), 1), 2),
            "allergen_recall": b2_allergen_recall,
            "n_with_allergen": n_with_allergen,
        },
        "smoke": smoke,
    }


def write_markdown(result: dict, out_path: Path) -> None:
    b1 = result["b1"]
    b2 = result["b2"]
    lines = [
        "# B2 (Food NER) vs B1 (Menu Normalizer) — DISH extraction",
        "",
        f"- sentences: **{result['n_sentences']}**",
        "",
        "| System | Precision | Recall | F1 | Latency (ms) | Allergen recall |",
        "|---|---|---|---|---|---|",
        f"| B1 (rule + Lev) | {b1['precision']:.4f} | {b1['recall']:.4f} | {b1['f1']:.4f} | {b1['latency_ms']} | — |",
        f"| B2 (NER) | {b2['precision']:.4f} | {b2['recall']:.4f} | {b2['f1']:.4f} | {b2['latency_ms']} | {b2['allergen_recall']:.4f} |",
        "",
        f"_Sentences with allergen ground truth: {b2.get('n_with_allergen', 0)}_",
    ]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


__all__ = ["run_comparison", "write_markdown"]

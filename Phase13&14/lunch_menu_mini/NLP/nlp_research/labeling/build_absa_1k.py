"""
Build 1,000-row ABSA dataset = LLM-labeled gold + rule-based silver.

- Gold: `data/labeled/absa/gold_llm.jsonl` (49 rows from Phase 5 DB via exaone3.5)
- Silver: 951 templated rows with aspect-balanced distribution and
  ~25% mixed-sentiment rate.

Output: `data/labeled/absa/v1_1k.jsonl` — each row has a `source` field
("gold_llm" or "silver_rule") so downstream code can weight or filter.
"""
from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from pathlib import Path

from nlp_research.labeling.augment_seed import (
    ABSA_TEMPLATES,
    NEG_SYNS,
    NEU_SYNS,
    POS_SYNS,
    _phrase,
)

ASPECTS = ["taste", "price", "service", "hygiene", "ambience"]
SENTIMENTS = ["positive", "neutral", "negative"]

# Target per-aspect count in the final 1000-row set (approximate)
TARGET_ASPECTS = {
    "taste":    280,   # most common
    "price":    200,
    "service":  200,
    "hygiene":  160,
    "ambience": 160,
}
# Target mixed-sentiment ratio (at least 2 different sentiments in one row)
TARGET_MIXED_RATIO = 0.25


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.open(encoding="utf-8") if l.strip()]


def sentiment_choice(rng: random.Random, bias: str | None = None) -> str:
    """Weighted sentiment sampling. `bias=same` biases toward single-sentiment rows."""
    weights = [0.45, 0.15, 0.40]  # pos, neu, neg — realistic review distribution
    return rng.choices(SENTIMENTS, weights=weights)[0]


def gen_silver_row(
    rng: random.Random,
    want_aspects: list[str],
    force_mixed: bool,
) -> dict:
    """Generate a single silver row with 1-3 aspects."""
    n_aspects = rng.choices([1, 2, 3], weights=[0.3, 0.5, 0.2])[0]
    aspects = rng.sample(want_aspects, min(n_aspects, len(want_aspects)))

    if force_mixed and len(aspects) >= 2:
        # Guarantee two different sentiments
        s1 = rng.choice(["positive", "negative"])
        s2 = "negative" if s1 == "positive" else "positive"
        sentiments = [s1, s2] + [sentiment_choice(rng) for _ in aspects[2:]]
    else:
        base_sent = sentiment_choice(rng)
        # 80% chance all aspects share base sentiment; 20% drift
        sentiments = [
            base_sent if rng.random() < 0.8 else sentiment_choice(rng)
            for _ in aspects
        ]

    phrases = [_phrase(a, s, rng) for a, s in zip(aspects, sentiments)]
    if len(phrases) == 1:
        text = phrases[0] + "."
    elif len(phrases) == 2:
        tmpl = rng.choice(ABSA_TEMPLATES)
        text = tmpl.format(p1=phrases[0], p2=phrases[1])
    else:
        tmpl = rng.choice(ABSA_TEMPLATES)
        text = tmpl.format(p1=phrases[0], p2=phrases[1]) + f" {phrases[2]}."

    return {
        "text": text,
        "aspects": [{"aspect": a, "sentiment": s} for a, s in zip(aspects, sentiments)],
        "source": "silver_rule",
    }


def build_silver(
    n: int,
    existing_aspect_counts: Counter,
    seed: int = 42,
) -> list[dict]:
    rng = random.Random(seed)
    rows: list[dict] = []
    aspect_counts = Counter(existing_aspect_counts)
    mixed_count = 0
    target_mixed = int(n * TARGET_MIXED_RATIO)

    while len(rows) < n:
        # Pick under-represented aspects for this row
        deficits = {
            a: max(TARGET_ASPECTS[a] - aspect_counts[a], 1)
            for a in ASPECTS
        }
        want_aspects = random.choices(
            ASPECTS,
            weights=[deficits[a] for a in ASPECTS],
            k=5,
        )
        # Deduplicate while preserving order
        seen = []
        for a in want_aspects:
            if a not in seen:
                seen.append(a)
        want_aspects = seen

        force_mixed = mixed_count < target_mixed and rng.random() < 0.5
        row = gen_silver_row(rng, want_aspects, force_mixed)

        # Update counters
        sents = {a["sentiment"] for a in row["aspects"]}
        if len(sents) >= 2:
            mixed_count += 1
        for a in row["aspects"]:
            aspect_counts[a["aspect"]] += 1
        rows.append(row)

    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gold", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--total", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    gold = load_jsonl(args.gold)
    print(f"[build] gold rows: {len(gold)}")

    existing = Counter()
    for r in gold:
        for a in r["aspects"]:
            existing[a["aspect"]] += 1

    n_silver = args.total - len(gold)
    silver = build_silver(n_silver, existing, seed=args.seed)
    print(f"[build] silver rows: {len(silver)}")

    all_rows = gold + silver
    random.Random(args.seed).shuffle(all_rows)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        for r in all_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Print final stats
    asp = Counter()
    sent = Counter()
    mixed = 0
    for r in all_rows:
        sents = {a["sentiment"] for a in r["aspects"]}
        if len(sents) >= 2:
            mixed += 1
        for a in r["aspects"]:
            asp[a["aspect"]] += 1
            sent[a["sentiment"]] += 1
    print(f"[build] total: {len(all_rows)}")
    print(f"[build] mixed: {mixed} ({mixed / len(all_rows) * 100:.1f}%)")
    print(f"[build] aspects: {dict(asp)}")
    print(f"[build] sentiments: {dict(sent)}")
    print(f"[build] wrote → {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

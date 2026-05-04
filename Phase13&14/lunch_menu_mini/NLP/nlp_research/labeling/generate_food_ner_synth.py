"""Phase 18 · Synthetic Food NER labeler.

Generates BIO-tagged sentences from `KEYWORD_LEXICON` × hand-written templates
to boost training data for under-represented entity types
(FLAVOR / COOKING / ALLERGEN).

Output: JSONL where each row is {"tokens": [...], "tags": ["B-DISH", ...]}.
Combine with `data/seed/food_ner_seed_aug.jsonl` for a richer training set.

Usage:
    python -m nlp_research.labeling.generate_food_ner_synth \\
        --output data/seed/food_ner_synth_500.jsonl \\
        --n 500 --seed 42
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from nlp_research.models.food_ner.inference import KEYWORD_LEXICON

# Korean particles & connectors that follow entities and stay as O
_PARTICLES = ["랑", "이랑", "와", "과", "을", "를", "이", "가", "도", "은", "는", "에"]


# Templates: each is (slot_pattern, allowed_types_per_slot, optional_suffix)
# slot_pattern uses tokens with `{TYPE}` placeholders. Particles/words appear
# verbatim and get tagged O. Sub-slots are picked uniformly per type.
_TEMPLATES = [
    # FLAVOR-heavy templates
    ["{FLAVOR}", "{DISH}", "주세요"],
    ["{FLAVOR}", "{DISH}", "한", "그릇"],
    ["{FLAVOR}", "{INGREDIENT}", "이", "들어간", "{DISH}"],
    ["{FLAVOR}", "{DISH}", "정말", "맛있어요"],
    ["오늘", "점심은", "{FLAVOR}", "{DISH}"],

    # TEXTURE-heavy
    ["{TEXTURE}", "{DISH}"],
    ["{TEXTURE}", "{INGREDIENT}"],
    ["{TEXTURE}", "{INGREDIENT}", "이", "들어간", "{DISH}"],
    ["겉은", "{TEXTURE}", "속은", "{TEXTURE}", "{DISH}"],

    # COOKING-heavy
    ["{COOKING}", "{INGREDIENT}", "{DISH}"],
    ["{COOKING}", "{DISH}"],
    ["{INGREDIENT}", "을", "{COOKING}", "{DISH}"],
    ["살짝", "{COOKING}", "{DISH}", "추천"],

    # ALLERGEN-heavy (safety critical → diverse contexts)
    ["{ALLERGEN}", "들어간", "{DISH}"],
    ["{ALLERGEN}", "알레르기가", "있어요"],
    ["{ALLERGEN}", "{ALLERGEN}", "들어간", "{DISH}"],
    ["{ALLERGEN}", "을", "뺀", "{DISH}"],
    ["{DISH}", "에", "{ALLERGEN}", "들어가나요"],

    # Mixed / DISH-only / INGREDIENT-only baselines
    ["{DISH}", "한", "그릇"],
    ["{INGREDIENT}", "와", "{INGREDIENT}", "{DISH}"],
    ["{FLAVOR}", "{COOKING}", "{INGREDIENT}", "{DISH}"],
    ["{TEXTURE}", "{COOKING}", "{DISH}"],
]


def _pick(rng: random.Random, kind: str) -> str:
    return rng.choice(KEYWORD_LEXICON[kind])


def _generate_one(rng: random.Random) -> dict:
    """Render one template into tokens + BIO tags."""
    template = rng.choice(_TEMPLATES)
    tokens: list[str] = []
    tags: list[str] = []
    for piece in template:
        if piece.startswith("{") and piece.endswith("}"):
            kind = piece[1:-1]
            value = _pick(rng, kind)
            tokens.append(value)
            tags.append(f"B-{kind}")
        else:
            tokens.append(piece)
            tags.append("O")

    # Optional Korean particle attached as a separate O token
    # (helps the model learn entity boundaries against postpositions)
    if rng.random() < 0.15:
        tokens.append(rng.choice(_PARTICLES))
        tags.append("O")

    return {"tokens": tokens, "tags": tags}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--n", type=int, default=500)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    seen: set[tuple] = set()
    rows: list[dict] = []
    attempts = 0
    while len(rows) < args.n and attempts < args.n * 4:
        attempts += 1
        row = _generate_one(rng)
        key = tuple(row["tokens"])
        if key in seen:
            continue
        seen.add(key)
        rows.append(row)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as fp:
        for r in rows:
            fp.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Class-distribution summary
    from collections import Counter
    cnt: Counter[str] = Counter()
    for r in rows:
        for t in r["tags"]:
            if t != "O":
                cnt[t.split("-", 1)[1]] += 1
    print(f"[synth] wrote {len(rows)} sentences to {args.output}")
    for k, v in sorted(cnt.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

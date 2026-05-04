"""
Label Studio JSON export → training-ready JSONL.

Supports two task types:

    # A2 ABSA
    python -m nlp_research.labeling.convert_labelstudio absa \
        --input  labelstudio_export.json \
        --output data/labeled/absa/v1.jsonl

    # B2 Food NER
    python -m nlp_research.labeling.convert_labelstudio food_ner \
        --input  labelstudio_export.json \
        --output data/labeled/food_ner/v1.jsonl

Label Studio schemas:
    - ABSA: tasks with `annotations[*].result[*].from_name ∈ {taste, price, service, hygiene, ambience}`
    - NER:  tasks with `annotations[*].result[*].from_name == "ner"` and
            each result has `value.start`, `value.end`, `value.labels[0]`
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from nlp_research.models.food_ner.model import LABELS as NER_LABELS


# =============================================================================
# ABSA
# =============================================================================
ASPECT_FIELDS = ("taste", "price", "service", "hygiene", "ambience")
SENTIMENT_VALUES = {"positive", "neutral", "negative"}


def _extract_absa_row(task: dict) -> dict | None:
    """Convert a single Label Studio task → {text, aspects: [{aspect, sentiment}]}."""
    text = task.get("data", {}).get("text", "").strip()
    if not text:
        return None

    annotations = task.get("annotations") or []
    if not annotations:
        return None
    # Use the first non-skipped annotation
    ann = next(
        (a for a in annotations if not a.get("was_cancelled")),
        annotations[0],
    )
    aspects: list[dict[str, str]] = []
    for r in ann.get("result", []):
        name = r.get("from_name")
        if name not in ASPECT_FIELDS:
            continue
        choices = (r.get("value") or {}).get("choices") or []
        if not choices:
            continue
        sentiment = choices[0]
        if sentiment not in SENTIMENT_VALUES:
            continue
        aspects.append({"aspect": name, "sentiment": sentiment})
    if not aspects:
        return None
    return {"text": text, "aspects": aspects}


def convert_absa(tasks: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for task in tasks:
        row = _extract_absa_row(task)
        if row is not None:
            rows.append(row)
    return rows


# =============================================================================
# Food NER
# =============================================================================
_TOKEN_RE = re.compile(r"\S+")


def _tokenize_with_spans(text: str) -> list[tuple[str, int, int]]:
    """Return list of (token, char_start, char_end) — whitespace split."""
    return [(m.group(0), m.start(), m.end()) for m in _TOKEN_RE.finditer(text)]


def _spans_to_bio(
    tokens: list[tuple[str, int, int]],
    entities: list[dict],
) -> list[str]:
    """
    Convert character-level Label Studio entities to BIO tags over whitespace tokens.

    entities: [{start, end, label}]
    """
    tags = ["O"] * len(tokens)
    # Sort entities by start so earlier ones win overlap
    for ent in sorted(entities, key=lambda e: (e["start"], -e["end"])):
        label = ent["label"]
        if f"B-{label}" not in NER_LABELS:
            continue
        started = False
        for i, (tok, tok_start, tok_end) in enumerate(tokens):
            # Token fully or partially inside entity span
            if tok_end <= ent["start"]:
                continue
            if tok_start >= ent["end"]:
                break
            if tags[i] != "O":
                continue  # already tagged by an earlier entity
            tags[i] = ("B-" if not started else "I-") + label
            started = True
    return tags


def _extract_ner_row(task: dict) -> dict | None:
    text = task.get("data", {}).get("text", "").strip()
    if not text:
        return None
    annotations = task.get("annotations") or []
    if not annotations:
        return None
    ann = next(
        (a for a in annotations if not a.get("was_cancelled")),
        annotations[0],
    )
    entities: list[dict] = []
    for r in ann.get("result", []):
        val = r.get("value") or {}
        labels = val.get("labels") or []
        if not labels:
            continue
        entities.append({
            "start": int(val.get("start", 0)),
            "end": int(val.get("end", 0)),
            "label": labels[0],
        })
    tokens = _tokenize_with_spans(text)
    if not tokens:
        return None
    tags = _spans_to_bio(tokens, entities)
    return {
        "tokens": [tok for tok, _, _ in tokens],
        "tags": tags,
    }


def convert_food_ner(tasks: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for task in tasks:
        row = _extract_ner_row(task)
        if row is not None:
            rows.append(row)
    return rows


# =============================================================================
# I/O + stats
# =============================================================================
def _load(path: Path) -> list[dict]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    # Label Studio exports either a list or an object with "tasks"
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict) and "tasks" in raw:
        return raw["tasks"]
    raise ValueError("unexpected Label Studio export format")


def _write_jsonl(rows: Iterable[dict], path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1
    return n


def _absa_stats(rows: list[dict]) -> str:
    aspect_counter: Counter = Counter()
    sent_counter: Counter = Counter()
    mixed = 0
    for r in rows:
        sentiments = {a["sentiment"] for a in r.get("aspects", [])}
        if len(sentiments) >= 2:
            mixed += 1
        for a in r.get("aspects", []):
            aspect_counter[a["aspect"]] += 1
            sent_counter[a["sentiment"]] += 1
    lines = [
        f"  total reviews: {len(rows)}",
        f"  mixed-sentiment: {mixed} ({mixed / max(len(rows), 1) * 100:.1f}%)",
        "  aspects: " + ", ".join(f"{k}={v}" for k, v in aspect_counter.most_common()),
        "  sentiments: " + ", ".join(f"{k}={v}" for k, v in sent_counter.most_common()),
    ]
    return "\n".join(lines)


def _ner_stats(rows: list[dict]) -> str:
    tag_counter: Counter = Counter()
    ent_counter: Counter = Counter()
    for r in rows:
        for t in r.get("tags", []):
            tag_counter[t] += 1
            if t.startswith("B-"):
                ent_counter[t[2:]] += 1
    total_tokens = sum(tag_counter.values())
    non_o = total_tokens - tag_counter.get("O", 0)
    return "\n".join([
        f"  total sentences: {len(rows)}",
        f"  total tokens: {total_tokens}",
        f"  entity tokens: {non_o} ({non_o / max(total_tokens, 1) * 100:.1f}%)",
        "  entities: " + ", ".join(f"{k}={v}" for k, v in ent_counter.most_common()),
    ])


# =============================================================================
# CLI
# =============================================================================
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("task", choices=("absa", "food_ner"))
    ap.add_argument("--input", type=Path, required=True, help="Label Studio JSON export")
    ap.add_argument("--output", type=Path, required=True, help="Destination JSONL")
    args = ap.parse_args()

    if not args.input.exists():
        print(f"[convert] input not found: {args.input}", file=sys.stderr)
        return 2

    tasks = _load(args.input)
    if args.task == "absa":
        rows = convert_absa(tasks)
        stats = _absa_stats(rows)
    else:
        rows = convert_food_ner(tasks)
        stats = _ner_stats(rows)

    written = _write_jsonl(rows, args.output)
    print(f"[convert] wrote {written} rows to {args.output}")
    print(stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

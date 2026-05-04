"""
Data loading helpers for A2 / B2 / E1.

Pure-Python where possible; heavy deps (torch, transformers, datasets) are
imported inside the functions that need them.
"""
from __future__ import annotations

import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


def load_jsonl(path: str | Path) -> list[dict]:
    """Parse a JSON-Lines file into a list of dicts."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"JSONL file not found: {p}")
    items: list[dict] = []
    with p.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON at {p}:{i}: {e}") from e
    return items


def save_jsonl(items: Iterable[dict], path: str | Path) -> int:
    """Write dicts as JSONL. Returns number of rows written."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with p.open("w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
            n += 1
    return n


def stratified_split(
    items: list[dict],
    key: str,
    ratios: tuple[float, float, float] = (0.8, 0.1, 0.1),
    seed: int = 42,
) -> tuple[list[dict], list[dict], list[dict]]:
    """
    Stratified train/val/test split by the given key.

    Each item must contain `key`; items are grouped then shuffled per-group.
    """
    if abs(sum(ratios) - 1.0) > 1e-6:
        raise ValueError(f"ratios must sum to 1.0, got {sum(ratios)}")

    buckets: dict[Any, list[dict]] = defaultdict(list)
    for it in items:
        buckets[it.get(key, "__none__")].append(it)

    rng = random.Random(seed)
    train: list[dict] = []
    val: list[dict] = []
    test: list[dict] = []
    for label, bucket in buckets.items():
        rng.shuffle(bucket)
        n = len(bucket)
        n_train = int(n * ratios[0])
        n_val = int(n * ratios[1])
        train.extend(bucket[:n_train])
        val.extend(bucket[n_train:n_train + n_val])
        test.extend(bucket[n_train + n_val:])

    rng.shuffle(train)
    rng.shuffle(val)
    rng.shuffle(test)
    return train, val, test


def tokenize_with_cache(
    texts: list[str],
    model_name: str,
    max_length: int = 128,
):
    """
    Load a HuggingFace tokenizer (cached) and encode texts.
    Returns the BatchEncoding dict. Imports are lazy.
    """
    try:
        from transformers import AutoTokenizer
    except ImportError as e:
        raise ImportError(
            "tokenize_with_cache requires `transformers`. "
            "Install: pip install transformers"
        ) from e

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    return tokenizer(
        texts,
        padding="max_length",
        truncation=True,
        max_length=max_length,
        return_tensors="pt",
    )


__all__ = [
    "load_jsonl",
    "save_jsonl",
    "stratified_split",
    "tokenize_with_cache",
]

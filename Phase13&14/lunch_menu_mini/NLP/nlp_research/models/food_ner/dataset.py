"""
B2 Food NER dataset utilities.

Seed format (JSONL — one example per line):
    {
      "tokens": ["매운", "김치", "찌개", "에", "들어간", "돼지고기"],
      "tags":   ["B-FLAVOR", "B-DISH", "I-DISH", "O", "O", "B-INGREDIENT"]
    }

Provides:
- load_food_ner_jsonl(path) → list[dict]
- align_labels_with_tokens(...) — subword alignment for HF transformers
- entities_from_tags(tokens, tags) → list of {type, value, start_token, end_token}
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from nlp_research.models.food_ner.model import LABEL2ID, LABELS
from nlp_research.training.data_loader import load_jsonl


def load_food_ner_jsonl(path: str | Path) -> list[dict]:
    rows = load_jsonl(path)
    out: list[dict] = []
    for row in rows:
        tokens = row.get("tokens") or []
        tags = row.get("tags") or []
        if not tokens or len(tokens) != len(tags):
            continue
        for t in tags:
            if t not in LABEL2ID:
                raise ValueError(f"unknown tag {t!r} (allowed: {LABELS})")
        out.append({"tokens": tokens, "tags": tags})
    return out


def entities_from_tags(
    tokens: list[str], tags: list[str]
) -> list[dict[str, Any]]:
    """
    Convert BIO tag sequence to a flat list of entity dicts.

    Returns:
        [{"type": "DISH", "value": "김치찌개", "start_token": 1, "end_token": 3}, ...]
    """
    out: list[dict[str, Any]] = []
    cur_type: str | None = None
    cur_start: int | None = None
    cur_tokens: list[str] = []

    def flush(end_token: int):
        if cur_type is not None and cur_start is not None:
            out.append({
                "type": cur_type,
                "value": "".join(cur_tokens),
                "start_token": cur_start,
                "end_token": end_token,
            })

    for i, (tok, tag) in enumerate(zip(tokens, tags)):
        if tag == "O":
            flush(i)
            cur_type, cur_start, cur_tokens = None, None, []
            continue
        prefix, _, etype = tag.partition("-")
        if prefix == "B" or cur_type != etype:
            flush(i)
            cur_type = etype
            cur_start = i
            cur_tokens = [tok]
        else:
            cur_tokens.append(tok)
    flush(len(tokens))
    return out


def align_labels_with_tokens(
    word_tags: list[str], word_ids: list[int | None]
) -> list[int]:
    """
    Align BIO word-level tags with HF tokenizer's word_ids() output.

    Subword tokens after the first inherit the I- counterpart of the B-tag,
    and special tokens get -100.
    """
    aligned: list[int] = []
    prev_word: int | None = None
    for wid in word_ids:
        if wid is None:
            aligned.append(-100)
        elif wid != prev_word:
            tag = word_tags[wid]
            aligned.append(LABEL2ID.get(tag, LABEL2ID["O"]))
        else:
            tag = word_tags[wid]
            if tag.startswith("B-"):
                tag = "I-" + tag[2:]
            aligned.append(LABEL2ID.get(tag, LABEL2ID["O"]))
        prev_word = wid
    return aligned


def build_hf_dataset(
    rows: list[dict],
    model_name: str,
    max_length: int = 256,
):
    """Build HF Dataset with subword-aligned labels (lazy imports)."""
    try:
        from datasets import Dataset
        from transformers import AutoTokenizer
    except ImportError as e:
        raise ImportError(
            "build_hf_dataset requires `datasets` and `transformers`."
        ) from e

    tokenizer = AutoTokenizer.from_pretrained(model_name)

    def _encode(example: dict) -> dict:
        encoded = tokenizer(
            example["tokens"],
            is_split_into_words=True,
            truncation=True,
            padding="max_length",
            max_length=max_length,
        )
        word_ids = encoded.word_ids()
        encoded["labels"] = align_labels_with_tokens(example["tags"], word_ids)
        return encoded

    ds = Dataset.from_list(rows)
    ds = ds.map(_encode, batched=False, remove_columns=ds.column_names)
    return ds, tokenizer


__all__ = [
    "load_food_ner_jsonl",
    "entities_from_tags",
    "align_labels_with_tokens",
    "build_hf_dataset",
]

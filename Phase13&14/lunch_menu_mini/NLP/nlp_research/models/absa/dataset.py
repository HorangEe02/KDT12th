"""
ABSA dataset — (text, aspect, sentiment) triples.

Seed format (JSONL):
    {
      "text": "김치찌개 맛은 훌륭한데, 가격이 비싸요.",
      "aspects": [
        {"aspect": "taste",  "sentiment": "positive"},
        {"aspect": "price",  "sentiment": "negative"}
      ]
    }

The dataset flattens each row into N triples (one per aspect) and BERT-SPC
encodes them with the aspect as the second segment.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from nlp_research.models.absa.model import LABEL2ID
from nlp_research.training.data_loader import load_jsonl


ASPECT_KO = {
    "taste": "맛",
    "price": "가격",
    "service": "서비스",
    "hygiene": "청결",
    "ambience": "분위기",
}


def flatten_triples(rows: list[dict]) -> list[dict]:
    """Expand nested aspects into (text, aspect, sentiment, label) triples."""
    out: list[dict] = []
    for row in rows:
        text = row.get("text", "").strip()
        for a in row.get("aspects", []):
            aspect = a.get("aspect")
            sentiment = a.get("sentiment")
            if not aspect or sentiment not in LABEL2ID:
                continue
            out.append(
                {
                    "text": text,
                    "aspect": aspect,
                    "aspect_ko": ASPECT_KO.get(aspect, aspect),
                    "sentiment": sentiment,
                    "label": LABEL2ID[sentiment],
                }
            )
    return out


def load_absa_triples(path: str | Path) -> list[dict]:
    """Load a seed JSONL and return flattened triples."""
    rows = load_jsonl(path)
    return flatten_triples(rows)


def build_hf_dataset(
    triples: list[dict],
    model_name: str,
    max_length: int = 128,
):
    """
    Convert triples to a HuggingFace `datasets.Dataset` with BERT-SPC encoding.
    Lazy imports — only needed when actually training.
    """
    try:
        from datasets import Dataset
        from transformers import AutoTokenizer
    except ImportError as e:
        raise ImportError(
            "build_hf_dataset requires `transformers` and `datasets`. "
            "Install: pip install transformers datasets"
        ) from e

    tokenizer = AutoTokenizer.from_pretrained(model_name)

    def _encode(batch: dict) -> dict:
        encoded = tokenizer(
            batch["text"],
            batch["aspect_ko"],
            padding="max_length",
            truncation=True,
            max_length=max_length,
        )
        encoded["labels"] = batch["label"]
        return encoded

    ds = Dataset.from_list(triples)
    ds = ds.map(_encode, batched=True, remove_columns=ds.column_names)
    return ds, tokenizer


__all__ = [
    "flatten_triples",
    "load_absa_triples",
    "build_hf_dataset",
    "ASPECT_KO",
]

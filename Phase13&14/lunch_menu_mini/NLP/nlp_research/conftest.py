"""
pytest shared fixtures and guards for nlp_research.

All heavy model dependencies are lazy — tests that need transformers / torch /
sentence-transformers use the corresponding marker to skip gracefully when the
package is not installed.
"""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import pytest

# Ensure nlp_research is importable from tests
ROOT = Path(__file__).resolve().parent
if str(ROOT.parent) not in sys.path:
    sys.path.insert(0, str(ROOT.parent))


def _has(pkg: str) -> bool:
    return importlib.util.find_spec(pkg) is not None


HAS_TORCH = _has("torch")
HAS_TRANSFORMERS = _has("transformers")
HAS_SBERT = _has("sentence_transformers")
HAS_NUMPY = _has("numpy")


def pytest_collection_modifyitems(config, items):
    skip_torch = pytest.mark.skip(reason="torch not installed")
    skip_tf = pytest.mark.skip(reason="transformers not installed")
    skip_sbert = pytest.mark.skip(reason="sentence-transformers not installed")
    for item in items:
        if "requires_torch" in item.keywords and not HAS_TORCH:
            item.add_marker(skip_torch)
        if "requires_transformers" in item.keywords and not HAS_TRANSFORMERS:
            item.add_marker(skip_tf)
        if "requires_sbert" in item.keywords and not HAS_SBERT:
            item.add_marker(skip_sbert)


@pytest.fixture
def seed_dir() -> Path:
    return ROOT / "data" / "seed"


@pytest.fixture
def tiny_absa_sample():
    return [
        {
            "text": "김치찌개 맛은 훌륭한데, 가격이 비싸요.",
            "aspect": "taste",
            "sentiment": "positive",
        },
        {
            "text": "김치찌개 맛은 훌륭한데, 가격이 비싸요.",
            "aspect": "price",
            "sentiment": "negative",
        },
    ]


@pytest.fixture
def tiny_ner_sample():
    return [
        {
            "tokens": ["매운", "김치", "찌개", "가", "맛있어요"],
            "tags": ["B-FLAVOR", "B-DISH", "I-DISH", "O", "O"],
        }
    ]

"""Smoke tests for A2 ABSA — no heavy model downloads required."""
from __future__ import annotations

from pathlib import Path

import pytest

from nlp_research.models.absa.dataset import (
    ASPECT_KO,
    flatten_triples,
    load_absa_triples,
)
from nlp_research.models.absa.evaluate import evaluate_absa
from nlp_research.models.absa.inference import DummyABSAInferencer, load_inferencer
from nlp_research.models.absa.model import ID2LABEL, LABEL2ID, NUM_LABELS


SEED = Path(__file__).resolve().parents[1] / "data" / "seed" / "absa_seed_50.jsonl"


def test_label_maps_consistent():
    assert len(LABEL2ID) == NUM_LABELS == 3
    assert set(LABEL2ID.keys()) == {"positive", "neutral", "negative"}
    assert all(ID2LABEL[i] == k for k, i in LABEL2ID.items())


def test_aspect_labels_complete():
    assert set(ASPECT_KO.keys()) == {
        "taste", "price", "service", "hygiene", "ambience"
    }


def test_seed_data_round_trip():
    assert SEED.exists(), f"seed file missing: {SEED}"
    triples = load_absa_triples(SEED)
    assert len(triples) >= 40, f"expected ≥40 triples, got {len(triples)}"
    for t in triples:
        assert t["aspect"] in ASPECT_KO
        assert t["sentiment"] in LABEL2ID
        assert t["label"] == LABEL2ID[t["sentiment"]]


def test_flatten_triples_nested_rows():
    rows = [
        {
            "text": "맛있지만 비싸요",
            "aspects": [
                {"aspect": "taste", "sentiment": "positive"},
                {"aspect": "price", "sentiment": "negative"},
            ],
        }
    ]
    triples = flatten_triples(rows)
    assert len(triples) == 2
    assert {t["aspect"] for t in triples} == {"taste", "price"}


def test_evaluate_dummy_predictions():
    """evaluate_absa with None predictions → random but consistent output shape."""
    result = evaluate_absa(SEED, predictions=None)
    assert "overall" in result
    assert "per_aspect" in result
    assert "confusion_matrix" in result
    assert result["n_samples"] > 0
    assert 0.0 <= result["overall"]["accuracy"] <= 1.0
    assert 0.0 <= result["overall"]["macro_f1"] <= 1.0


def test_dummy_inferencer_returns_all_aspects():
    inf = DummyABSAInferencer(seed=1)
    preds = inf.predict("김치찌개 맛있어요")
    assert len(preds) == 5
    aspects = {p["aspect"] for p in preds}
    assert aspects == set(ASPECT_KO.keys())
    for p in preds:
        assert p["sentiment"] in LABEL2ID
        assert 0.0 <= p["confidence"] <= 1.0


def test_load_inferencer_falls_back_to_dummy():
    inf = load_inferencer(model_path=None)
    assert isinstance(inf, DummyABSAInferencer)
    preds = inf.predict("테스트", aspects=["taste"])
    assert len(preds) == 1


@pytest.mark.requires_transformers
@pytest.mark.requires_torch
def test_build_model_shape():
    """Requires torch+transformers installed. Skipped by default in CI."""
    from nlp_research.models.absa.model import build_model

    model = build_model()
    import torch
    batch = {
        "input_ids": torch.randint(0, 100, (2, 16)),
        "attention_mask": torch.ones(2, 16, dtype=torch.long),
    }
    out = model(**batch)
    assert out["logits"].shape == (2, 3)

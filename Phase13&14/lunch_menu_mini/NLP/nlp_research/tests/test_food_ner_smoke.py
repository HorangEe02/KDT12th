"""Smoke tests for B2 Food NER."""
from __future__ import annotations

from pathlib import Path

import pytest

from nlp_research.models.food_ner.dataset import (
    align_labels_with_tokens,
    entities_from_tags,
    load_food_ner_jsonl,
)
from nlp_research.models.food_ner.evaluate import evaluate_food_ner
from nlp_research.models.food_ner.inference import (
    KEYWORD_LEXICON,
    RuleBasedFoodNERInferencer,
    extract_allergens,
    filter_restaurants_by_allergies,
    load_inferencer,
)
from nlp_research.models.food_ner.model import (
    ENTITY_TYPES,
    LABEL2ID,
    LABELS,
    NUM_LABELS,
)


SEED = Path(__file__).resolve().parents[1] / "data" / "seed" / "food_ner_seed_50.jsonl"


def test_label_set_complete():
    assert NUM_LABELS == 13
    assert LABELS[0] == "O"
    for etype in ENTITY_TYPES:
        assert f"B-{etype}" in LABEL2ID
        assert f"I-{etype}" in LABEL2ID


def test_seed_data_round_trip():
    rows = load_food_ner_jsonl(SEED)
    assert len(rows) >= 40
    for r in rows:
        assert len(r["tokens"]) == len(r["tags"])
        assert all(t in LABEL2ID for t in r["tags"])


def test_entities_from_tags_basic():
    tokens = ["매운", "김치", "찌개", "에", "들어간", "돼지고기"]
    tags = ["B-FLAVOR", "B-DISH", "I-DISH", "O", "O", "B-INGREDIENT"]
    ents = entities_from_tags(tokens, tags)
    types = [e["type"] for e in ents]
    values = [e["value"] for e in ents]
    assert types == ["FLAVOR", "DISH", "INGREDIENT"]
    assert values == ["매운", "김치찌개", "돼지고기"]


def test_align_labels_with_tokens_subwords():
    word_tags = ["B-DISH", "I-DISH", "O"]
    word_ids = [None, 0, 0, 1, 2, None]  # 2 subwords for word 0
    aligned = align_labels_with_tokens(word_tags, word_ids)
    # special tokens → -100
    assert aligned[0] == -100
    assert aligned[-1] == -100
    # word 0 first subword: B-DISH; second subword: I-DISH (auto-converted)
    assert aligned[1] == LABEL2ID["B-DISH"]
    assert aligned[2] == LABEL2ID["I-DISH"]


def test_evaluate_dummy():
    result = evaluate_food_ner(SEED, pred_tags=None)
    assert "overall" in result
    assert "per_type" in result
    assert result["n_samples"] > 0


def test_rule_based_inferencer_finds_dish():
    inf = RuleBasedFoodNERInferencer()
    ents = inf.predict("오늘 점심은 김치찌개랑 비빔밥")
    types = {e["type"] for e in ents}
    values = {e["value"] for e in ents}
    assert "DISH" in types
    assert "김치찌개" in values
    assert "비빔밥" in values


def test_extract_allergens():
    text = "이 메뉴엔 땅콩과 새우가 들어 있어요"
    found = extract_allergens(text)
    assert "땅콩" in found
    assert "새우" in found


def test_filter_restaurants_by_allergies():
    restaurants = [
        {"name": "땅콩버거집", "description": "땅콩 소스 사용"},
        {"name": "안전식당", "description": "깨끗한 한식"},
        {"name": "새우튀김집", "description": "새우 듬뿍"},
    ]
    safe = filter_restaurants_by_allergies(restaurants, ["땅콩", "새우"])
    names = [r["name"] for r in safe]
    assert names == ["안전식당"]


def test_load_inferencer_falls_back():
    inf = load_inferencer(model_path=None)
    assert isinstance(inf, RuleBasedFoodNERInferencer)


def test_lexicon_has_all_entity_types():
    for etype in ENTITY_TYPES:
        assert etype in KEYWORD_LEXICON
        assert len(KEYWORD_LEXICON[etype]) > 0


@pytest.mark.requires_transformers
@pytest.mark.requires_torch
def test_build_model_shape():
    from nlp_research.models.food_ner.model import build_model

    model = build_model(use_crf=False)
    import torch
    out = model(
        input_ids=torch.randint(0, 100, (2, 16)),
        attention_mask=torch.ones(2, 16, dtype=torch.long),
    )
    assert out["logits"].shape == (2, 16, NUM_LABELS)

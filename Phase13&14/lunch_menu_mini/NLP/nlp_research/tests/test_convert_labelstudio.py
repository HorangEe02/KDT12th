"""Unit tests for Label Studio JSON → training JSONL converter."""
from __future__ import annotations

from nlp_research.labeling.convert_labelstudio import (
    convert_absa,
    convert_food_ner,
)


# =============================================================================
# ABSA
# =============================================================================
def test_convert_absa_single_aspect():
    tasks = [{
        "data": {"text": "맛있어요"},
        "annotations": [{"result": [
            {"from_name": "taste", "value": {"choices": ["positive"]}},
        ]}],
    }]
    rows = convert_absa(tasks)
    assert len(rows) == 1
    assert rows[0]["text"] == "맛있어요"
    assert rows[0]["aspects"] == [{"aspect": "taste", "sentiment": "positive"}]


def test_convert_absa_multi_aspect():
    tasks = [{
        "data": {"text": "맛은 좋은데 비싸요"},
        "annotations": [{"result": [
            {"from_name": "taste", "value": {"choices": ["positive"]}},
            {"from_name": "price", "value": {"choices": ["negative"]}},
        ]}],
    }]
    rows = convert_absa(tasks)
    assert len(rows) == 1
    aspects = {a["aspect"]: a["sentiment"] for a in rows[0]["aspects"]}
    assert aspects == {"taste": "positive", "price": "negative"}


def test_convert_absa_skips_unannotated():
    tasks = [
        {"data": {"text": "annotated"}, "annotations": [{
            "result": [{"from_name": "taste", "value": {"choices": ["positive"]}}]
        }]},
        {"data": {"text": "empty"}, "annotations": []},
        {"data": {"text": "cancelled"}, "annotations": [{"was_cancelled": True, "result": []}]},
    ]
    rows = convert_absa(tasks)
    # Cancelled annotation still has empty result → skipped (no aspects)
    assert len(rows) == 1
    assert rows[0]["text"] == "annotated"


def test_convert_absa_ignores_invalid_sentiment():
    tasks = [{
        "data": {"text": "test"},
        "annotations": [{"result": [
            {"from_name": "taste", "value": {"choices": ["garbage"]}},
            {"from_name": "price", "value": {"choices": ["neutral"]}},
        ]}],
    }]
    rows = convert_absa(tasks)
    assert len(rows) == 1
    assert rows[0]["aspects"] == [{"aspect": "price", "sentiment": "neutral"}]


# =============================================================================
# Food NER
# =============================================================================
def test_convert_ner_simple():
    tasks = [{
        "data": {"text": "매운 김치찌개"},
        "annotations": [{"result": [
            {"from_name": "ner", "value": {"start": 0, "end": 2, "labels": ["FLAVOR"]}},
            {"from_name": "ner", "value": {"start": 3, "end": 7, "labels": ["DISH"]}},
        ]}],
    }]
    rows = convert_food_ner(tasks)
    assert len(rows) == 1
    assert rows[0]["tokens"] == ["매운", "김치찌개"]
    assert rows[0]["tags"] == ["B-FLAVOR", "B-DISH"]


def test_convert_ner_multi_token_entity():
    tasks = [{
        "data": {"text": "부드러운 소고기 구이"},
        "annotations": [{"result": [
            {"from_name": "ner", "value": {"start": 0, "end": 4, "labels": ["TEXTURE"]}},
            {"from_name": "ner", "value": {"start": 5, "end": 8, "labels": ["INGREDIENT"]}},
            {"from_name": "ner", "value": {"start": 9, "end": 11, "labels": ["COOKING"]}},
        ]}],
    }]
    rows = convert_food_ner(tasks)
    assert rows[0]["tokens"] == ["부드러운", "소고기", "구이"]
    assert rows[0]["tags"] == ["B-TEXTURE", "B-INGREDIENT", "B-COOKING"]


def test_convert_ner_no_annotations_skipped():
    tasks = [
        {"data": {"text": "empty"}, "annotations": []},
        {"data": {"text": ""}, "annotations": [{"result": []}]},
    ]
    rows = convert_food_ner(tasks)
    assert rows == []


def test_convert_ner_unknown_label_dropped():
    tasks = [{
        "data": {"text": "매운 음식"},
        "annotations": [{"result": [
            {"from_name": "ner", "value": {"start": 0, "end": 2, "labels": ["NOT_A_TAG"]}},
            {"from_name": "ner", "value": {"start": 3, "end": 5, "labels": ["DISH"]}},
        ]}],
    }]
    rows = convert_food_ner(tasks)
    # Unknown label skipped; "매운" stays O
    assert rows[0]["tags"] == ["O", "B-DISH"]

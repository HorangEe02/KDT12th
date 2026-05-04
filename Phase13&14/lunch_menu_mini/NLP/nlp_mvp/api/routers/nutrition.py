"""
/nlp/nutrition/* 라우터.

- POST /nlp/nutrition/parse
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from nlp_mvp.api.schemas import NutritionParseIn, NutritionParseOut
from nlp_mvp.nutrition_parser import parse_meal_text
from nlp_mvp.shared.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/nlp/nutrition", tags=["nlp-nutrition"])

_normalizer = None


def get_normalizer():
    """메뉴 정규화기 싱글톤."""
    global _normalizer
    if _normalizer is None:
        from nlp_mvp.menu_normalizer.normalizer import MenuNormalizer
        _normalizer = MenuNormalizer(enable_embedding=False)
    return _normalizer


def set_normalizer(normalizer) -> None:
    global _normalizer
    _normalizer = normalizer


@router.post("/parse", response_model=NutritionParseOut)
def parse(payload: NutritionParseIn) -> NutritionParseOut:
    """사용자 자연어 식단 입력을 저장 전 구조화 후보로 변환한다."""
    try:
        normalizer = get_normalizer()
    except Exception as e:
        logger.warning("nutrition parser normalizer unavailable: %s", e)
        normalizer = None

    try:
        result = parse_meal_text(
            text=payload.text,
            user_id=payload.user_id,
            base_date=payload.base_date,
            normalizer=normalizer,
        )
    except Exception as e:
        logger.exception("nutrition parse failed")
        raise HTTPException(status_code=500, detail=f"nutrition parse failed: {e}")

    return NutritionParseOut(**result)

"""
B2 Food NER inferencer + allergy filter helpers.

A `RuleBasedFoodNERInferencer` is included as a zero-dependency fallback
backed by keyword dictionaries — useful for the v2 router stub and benchmark
smoke mode when no trained model is available.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional

from nlp_research.models.food_ner.dataset import entities_from_tags
from nlp_research.models.food_ner.model import (
    DEFAULT_MODEL_NAME,
    ENTITY_TYPES,
    LABELS,
)


# Lightweight Korean keyword dictionaries — used by the rule-based fallback.
# These are intentionally small; the trained model is the production path.
KEYWORD_LEXICON: dict[str, list[str]] = {
    "DISH": [
        # 찌개·국·탕
        "김치찌개", "된장찌개", "순두부찌개", "부대찌개", "청국장찌개",
        "갈비탕", "설렁탕", "육개장", "삼계탕", "감자탕", "추어탕", "동태탕",
        "국밥", "순댓국", "콩나물국밥", "소머리국밥", "뼈해장국",
        # 밥류
        "비빔밥", "전주비빔밥", "돌솥비빔밥", "회덮밥", "볶음밥",
        "쌀밥", "잡곡밥", "공기밥", "현미밥",
        # 면류
        "냉면", "물냉면", "비빔냉면", "칼국수", "라면", "라멘", "쌀국수",
        "짜장면", "짬뽕", "우동", "스파게티",
        # 분식·간식
        "김밥", "떡볶이", "순대", "튀김", "어묵", "만두", "찐만두",
        # 고기·구이
        "삼겹살", "삼겹살구이", "불고기", "갈비", "갈비찜", "양념갈비",
        "닭갈비", "제육볶음", "제육덮밥", "찜닭", "불족발",
        # 양식·일식
        "돈가스", "돈까스", "햄버거", "피자", "샐러드", "샌드위치",
        "초밥", "회", "장어구이", "오마카세",
        # 치킨·음료
        "치킨", "양념치킨", "후라이드", "닭강정",
        "아메리카노", "라떼", "에스프레소", "카푸치노",
    ],
    "INGREDIENT": [
        "돼지고기", "소고기", "닭고기", "오리고기", "양고기", "양파", "마늘",
        "고추", "청양고추", "대파", "쪽파", "부추",
        "치즈", "두부", "계란", "달걀", "버섯", "표고버섯", "느타리버섯",
        "감자", "당근", "호박", "애호박", "단호박", "오이", "토마토",
        "양배추", "배추", "시금치", "콩나물", "숙주", "미나리",
        "김치", "묵은지", "갓김치", "깍두기", "단무지",
        "오징어", "낙지", "문어", "쭈꾸미", "새우", "꽃게", "조개",
        "고등어", "삼치", "갈치", "꽁치", "참치", "연어", "명태",
        "쌀", "현미", "찹쌀", "보리", "밀가루", "라면사리",
    ],
    "FLAVOR": [
        "매운", "매콤한", "달콤한", "짠", "신", "쓴",
        "고소한", "담백한", "얼큰한", "시원한", "구수한", "진한",
        "달짝지근한", "새콤한", "짭짤한",
    ],
    "TEXTURE": [
        "바삭한", "쫄깃한", "쫄깃쫄깃한", "부드러운", "촉촉한",
        "꾸덕한", "쫀득한", "아삭한", "탱탱한", "꼬들꼬들한",
        "사르르", "녹진한",
    ],
    "COOKING": [
        "구운", "삶은", "튀긴", "찐", "볶은", "끓인", "조림", "조린",
        "무친", "데친", "쪄낸", "익힌", "저민", "다진", "전",
    ],
    "ALLERGEN": [
        "땅콩", "새우", "게", "꽃게", "오징어", "문어", "조개", "전복",
        "우유", "치즈", "버터", "계란", "달걀", "밀", "밀가루", "메밀",
        "콩", "대두", "복숭아", "토마토", "잣", "호두", "아몬드", "캐슈넛",
        "고등어", "꽁치", "삼치", "참치",
    ],
}


# =============================================================================
# Real (model-backed) inferencer
# =============================================================================
class FoodNERInferencer:
    """Trained KoELECTRA inferencer (lazy imports)."""

    def __init__(
        self,
        model_path: str | Path,
        tokenizer_name: str = DEFAULT_MODEL_NAME,
        max_length: int = 256,
        device: str = "auto",
    ):
        try:
            import torch
            from transformers import AutoTokenizer
        except ImportError as e:
            raise ImportError(
                "FoodNERInferencer requires torch + transformers."
            ) from e

        from nlp_research.models.food_ner.model import build_model

        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
        self.model = build_model(tokenizer_name)
        state = _load_state_dict(Path(model_path))
        self.model.load_state_dict(state)
        self.model.eval()
        self.device = self._resolve_device(device)
        self.model.to(self.device)
        self.max_length = max_length

    @staticmethod
    def _resolve_device(device: str) -> str:
        if device != "auto":
            return device
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
        except Exception:
            pass
        return "cpu"

    def predict(self, text: str) -> list[dict[str, Any]]:
        import torch
        tokens = text.split()
        with torch.no_grad():
            enc = self.tokenizer(
                tokens,
                is_split_into_words=True,
                truncation=True,
                padding="max_length",
                max_length=self.max_length,
                return_tensors="pt",
            ).to(self.device)
            out = self.model(input_ids=enc["input_ids"], attention_mask=enc["attention_mask"])
            preds = out["logits"].argmax(dim=-1).tolist()[0]
        word_ids = enc.word_ids()
        word_tags: list[str] = []
        prev = None
        for wid, p in zip(word_ids, preds):
            if wid is None or wid == prev:
                continue
            word_tags.append(LABELS[int(p)])
            prev = wid
        return entities_from_tags(tokens, word_tags[: len(tokens)])


# =============================================================================
# Rule-based fallback (no model required)
# =============================================================================
class RuleBasedFoodNERInferencer:
    """
    Pure-Python keyword matcher. Lower precision/recall than a trained model,
    but available without any deps.
    """

    def __init__(self, lexicon: Optional[dict[str, list[str]]] = None):
        self.lexicon = lexicon or KEYWORD_LEXICON
        # Pre-compile regex per type for whole-word matching
        self._patterns = {
            etype: [(kw, re.compile(re.escape(kw))) for kw in kws]
            for etype, kws in self.lexicon.items()
        }

    def predict(self, text: str) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for etype, patterns in self._patterns.items():
            for kw, pat in patterns:
                for m in pat.finditer(text):
                    out.append({
                        "type": etype,
                        "value": kw,
                        "start_token": m.start(),
                        "end_token": m.end(),
                    })
        return out


# =============================================================================
# Allergen helpers
# =============================================================================
def extract_allergens(text: str, inferencer=None) -> list[str]:
    """Return distinct allergen values found in text."""
    inf = inferencer or RuleBasedFoodNERInferencer()
    ents = inf.predict(text)
    return sorted({e["value"] for e in ents if e["type"] == "ALLERGEN"})


def filter_restaurants_by_allergies(
    restaurants: list[dict],
    user_allergies: list[str],
    description_field: str = "description",
    inferencer=None,
) -> list[dict]:
    """
    Drop restaurants whose menu description contains any user allergen.
    """
    if not user_allergies:
        return list(restaurants)
    inf = inferencer or RuleBasedFoodNERInferencer()
    user_set = {a.strip() for a in user_allergies if a and a.strip()}
    result: list[dict] = []
    for r in restaurants:
        desc = r.get(description_field) or r.get("name") or ""
        found = set(extract_allergens(desc, inf))
        if found & user_set:
            continue
        result.append(r)
    return result


# NLP/nlp_research/models/food_ner/inference.py → parents[2] = NLP/nlp_research/
_NLP_RESEARCH_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_CKPT_DIRS = (
    _NLP_RESEARCH_ROOT / "checkpoints" / "food_ner" / "best",
    _NLP_RESEARCH_ROOT / "checkpoints" / "food_ner" / "v1" / "best",
    _NLP_RESEARCH_ROOT / "checkpoints" / "food_ner" / "v1",
)


def _has_weights(p: Path) -> bool:
    return (p / "pytorch_model.bin").exists() or (p / "model.safetensors").exists()


def _load_state_dict(p: Path):
    """Load a state dict from either legacy .bin or safetensors format."""
    import torch
    bin_path = p / "pytorch_model.bin"
    if bin_path.exists():
        return torch.load(bin_path, map_location="cpu")
    safe_path = p / "model.safetensors"
    if safe_path.exists():
        from safetensors.torch import load_file
        return load_file(str(safe_path), device="cpu")
    raise FileNotFoundError(f"no model.safetensors or pytorch_model.bin in {p}")


def _auto_discover() -> Optional[Path]:
    import os
    env = os.getenv("NLP_V2_NER_CKPT")
    if env and Path(env).exists():
        return Path(env)
    for p in _DEFAULT_CKPT_DIRS:
        if _has_weights(p):
            return p
    return None


def load_inferencer(
    model_path: Optional[str | Path] = None,
) -> "FoodNERInferencer | RuleBasedFoodNERInferencer":
    """Return real inferencer if a checkpoint exists (explicit path,
    $NLP_V2_NER_CKPT, or checkpoints/food_ner/{best,v1/best,v1}/), else rule-based."""
    path = Path(model_path) if model_path else _auto_discover()
    if path and path.exists() and _has_weights(path):
        try:
            return FoodNERInferencer(path)
        except Exception:
            pass
    return RuleBasedFoodNERInferencer()


__all__ = [
    "FoodNERInferencer",
    "RuleBasedFoodNERInferencer",
    "extract_allergens",
    "filter_restaurants_by_allergies",
    "load_inferencer",
    "KEYWORD_LEXICON",
]

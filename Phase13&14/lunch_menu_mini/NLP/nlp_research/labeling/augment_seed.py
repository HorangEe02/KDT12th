"""
Rule-based seed augmentation for ABSA and Food NER.

Goal: expand 50 → ~150 seed rows without hand-labeling, so `train.py --dry-run`
and smoke tests have more realistic volume. Augmentation is conservative:
synonym swaps + sentence templates. Output is written to `data/seed/*_aug.jsonl`
(kept separate from the hand-written originals).

Usage:
    python -m nlp_research.labeling.augment_seed absa
    python -m nlp_research.labeling.augment_seed food_ner
    python -m nlp_research.labeling.augment_seed all
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

SEED_DIR = Path(__file__).resolve().parents[1] / "data" / "seed"

# =============================================================================
# ABSA augmentation — swap sentiment-bearing words with synonyms
# =============================================================================
POS_SYNS = {
    "taste": ["정말 맛있어요", "훌륭해요", "일품이에요", "감탄했어요", "환상적이에요"],
    "price": ["가성비 최고", "정말 저렴해요", "합리적이에요", "가격 착해요", "부담 없어요"],
    "service": ["친절했어요", "응대가 좋아요", "직원분이 상냥해요", "서비스 훌륭", "배려가 느껴져요"],
    "hygiene": ["깨끗해요", "위생 철저", "청결합니다", "정돈되어 있어요", "깔끔해요"],
    "ambience": ["분위기 좋아요", "아늑해요", "인테리어 멋져요", "조용하고 편안", "데이트 장소로 좋아요"],
}
NEG_SYNS = {
    "taste": ["맛이 별로", "싱겁고 밍밍", "실망했어요", "맛없어요", "먹다 말았어요"],
    "price": ["너무 비싸요", "바가지예요", "가격이 아쉬워요", "양에 비해 비싸", "부담스러워요"],
    "service": ["불친절했어요", "무성의해요", "응대가 차가워요", "기분 나빴어요", "서비스 엉망"],
    "hygiene": ["지저분해요", "위생 엉망", "벌레가 보여요", "바닥이 끈적", "청결 상태 최악"],
    "ambience": ["시끄럽고 복잡", "분위기 별로", "자리 좁아요", "답답해요", "인테리어 낡았어요"],
}
NEU_SYNS = {
    "taste": ["맛은 평범해요", "그저 그래요", "특별하진 않아요", "무난해요"],
    "price": ["가격은 적당", "평범한 수준", "보통이에요"],
    "service": ["응대는 보통", "특별한 건 없어요"],
    "hygiene": ["위생은 무난", "그럭저럭 깨끗"],
    "ambience": ["분위기는 보통", "평범한 인테리어"],
}

ABSA_TEMPLATES = [
    "{p1}. 그런데 {p2}.",
    "{p1}이지만 {p2}.",
    "{p1}. {p2}. 다시 올지 고민.",
    "{p1}, {p2}. 종합적으로 괜찮아요.",
    "{p1}. 아쉬운 점은 {p2}.",
]


def _phrase(aspect: str, sentiment: str, rng: random.Random) -> str:
    bank = {"positive": POS_SYNS, "negative": NEG_SYNS, "neutral": NEU_SYNS}[sentiment]
    return rng.choice(bank[aspect])


def augment_absa(n_new: int = 100, seed: int = 42) -> list[dict]:
    """Generate synthetic ABSA rows by combining 2 aspect phrases."""
    rng = random.Random(seed)
    aspects = ["taste", "price", "service", "hygiene", "ambience"]
    sentiments = ["positive", "negative", "neutral"]
    rows: list[dict] = []
    for _ in range(n_new):
        a1, a2 = rng.sample(aspects, 2)
        s1, s2 = rng.choice(sentiments), rng.choice(sentiments)
        tmpl = rng.choice(ABSA_TEMPLATES)
        text = tmpl.format(p1=_phrase(a1, s1, rng), p2=_phrase(a2, s2, rng))
        rows.append({
            "text": text,
            "aspects": [
                {"aspect": a1, "sentiment": s1},
                {"aspect": a2, "sentiment": s2},
            ],
        })
    return rows


# =============================================================================
# Food NER augmentation — slot-fill templates
# =============================================================================
DISHES = ["김치찌개", "된장찌개", "비빔밥", "불고기", "삼겹살", "냉면", "돈까스", "김밥", "떡볶이", "라면", "제육볶음", "설렁탕"]
INGREDIENTS = ["돼지고기", "소고기", "닭고기", "두부", "버섯", "양파", "마늘", "파", "계란", "당면"]
FLAVORS = ["매운", "달콤한", "짭짤한", "얼큰한", "고소한", "새콤한"]
TEXTURES = ["부드러운", "바삭한", "쫄깃한", "촉촉한", "아삭한"]
COOKINGS = ["구운", "튀긴", "볶은", "삶은", "찐"]
ALLERGENS = ["땅콩", "새우", "우유", "계란", "밀가루", "견과류"]

NER_TEMPLATES = [
    # (token pattern, tag pattern) — placeholders: D/I/F/T/C/A
    (["F", "D", "정말", "맛있어요"], ["B-FLAVOR", "B-DISH", "O", "O"]),
    (["T", "D", "최고"], ["B-TEXTURE", "B-DISH", "O"]),
    (["C", "D", "에", "I", "을", "곁들였다"],
     ["B-COOKING", "B-DISH", "O", "B-INGREDIENT", "O", "O"]),
    (["A", "이", "들어간", "D", "는", "주의"],
     ["B-ALLERGEN", "O", "O", "B-DISH", "O", "O"]),
    (["F", "D", "에", "I", "가", "가득"],
     ["B-FLAVOR", "B-DISH", "O", "B-INGREDIENT", "O", "O"]),
    (["T", "I", "이", "들어간", "D"],
     ["B-TEXTURE", "B-INGREDIENT", "O", "O", "B-DISH"]),
    (["C", "I", "와", "F", "D"],
     ["B-COOKING", "B-INGREDIENT", "O", "B-FLAVOR", "B-DISH"]),
]

SLOT_POOLS = {
    "D": DISHES, "I": INGREDIENTS, "F": FLAVORS,
    "T": TEXTURES, "C": COOKINGS, "A": ALLERGENS,
}


def augment_food_ner(n_new: int = 100, seed: int = 42) -> list[dict]:
    rng = random.Random(seed)
    rows: list[dict] = []
    for _ in range(n_new):
        tok_tmpl, tag_tmpl = rng.choice(NER_TEMPLATES)
        tokens = [rng.choice(SLOT_POOLS[t]) if t in SLOT_POOLS else t for t in tok_tmpl]
        rows.append({"tokens": tokens, "tags": list(tag_tmpl)})
    return rows


# =============================================================================
# I/O
# =============================================================================
def _write(rows: list[dict], path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return len(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("task", choices=("absa", "food_ner", "all"))
    ap.add_argument("--n", type=int, default=100, help="Rows to generate")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    tasks = ("absa", "food_ner") if args.task == "all" else (args.task,)
    for t in tasks:
        if t == "absa":
            rows = augment_absa(args.n, args.seed)
            out = SEED_DIR / "absa_seed_aug.jsonl"
        else:
            rows = augment_food_ner(args.n, args.seed)
            out = SEED_DIR / "food_ner_seed_aug.jsonl"
        n = _write(rows, out)
        print(f"[augment] {t}: wrote {n} rows to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

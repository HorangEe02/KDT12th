"""
Data augmentation helpers for A2 / B2 training.

- `eda_*` functions: pure-Python Korean EDA (synonym/insertion/swap/deletion)
- `gpt_augment`: reuses nlp_mvp.shared.ollama_client for LLM paraphrasing
- `filter_by_similarity`: Sentence-BERT quality filter (lazy import)
"""
from __future__ import annotations

import random
from typing import Optional

# Small Korean synonym map — extend as needed.
_KO_SYNONYMS = {
    "맛있다": ["맛나다", "맛좋다", "훌륭하다"],
    "맛있어요": ["맛나요", "좋아요", "훌륭해요"],
    "좋다": ["괜찮다", "훌륭하다"],
    "싸다": ["저렴하다", "착하다"],
    "비싸다": ["고가다", "비용이 많이 든다"],
    "빠르다": ["신속하다"],
    "느리다": ["더디다"],
    "친절": ["다정", "상냥"],
    "불친절": ["무례", "퉁명스러움"],
    "깨끗": ["청결", "깔끔"],
    "더러": ["지저분", "불결"],
}


def eda_synonym_replacement(text: str, n: int = 2, rng: Optional[random.Random] = None) -> str:
    """Replace up to `n` words with synonyms from the built-in map."""
    rng = rng or random.Random()
    words = text.split()
    if not words:
        return text
    indices = [i for i, w in enumerate(words) if _strip_ko_suffix(w) in _KO_SYNONYMS]
    rng.shuffle(indices)
    for idx in indices[:n]:
        base = _strip_ko_suffix(words[idx])
        choices = _KO_SYNONYMS[base]
        words[idx] = rng.choice(choices)
    return " ".join(words)


def eda_random_swap(text: str, n: int = 1, rng: Optional[random.Random] = None) -> str:
    rng = rng or random.Random()
    words = text.split()
    if len(words) < 2:
        return text
    for _ in range(n):
        i, j = rng.sample(range(len(words)), 2)
        words[i], words[j] = words[j], words[i]
    return " ".join(words)


def eda_random_deletion(text: str, p: float = 0.1, rng: Optional[random.Random] = None) -> str:
    rng = rng or random.Random()
    words = text.split()
    if not words:
        return text
    kept = [w for w in words if rng.random() > p]
    return " ".join(kept) if kept else rng.choice(words)


def _strip_ko_suffix(word: str) -> str:
    """Very rough: strip common verbal/polite endings to match synonym keys."""
    for suf in ("습니다", "어요", "아요", "네요", "요", "다"):
        if word.endswith(suf) and len(word) > len(suf):
            return word
    return word


# =============================================================================
# GPT-based augmentation (Ollama via nlp_mvp.shared.ollama_client)
# =============================================================================
def gpt_augment(
    original: str,
    n_variants: int = 3,
    provider: str = "ollama",
    model: Optional[str] = None,
) -> list[str]:
    """
    Generate paraphrases via local Ollama (reuses nlp_mvp OllamaClient).
    Returns `n_variants` variants. Errors return [original].
    """
    if provider != "ollama":
        raise NotImplementedError(f"provider={provider!r} not supported yet")

    try:
        from nlp_mvp.shared.ollama_client import OllamaClient
    except ImportError:
        return [original]

    client = OllamaClient(model=model) if model else OllamaClient()
    system = (
        "당신은 한국어 텍스트 변형기입니다. 다음 문장을 의미는 동일하되 "
        f"표현만 다르게 {n_variants}가지로 변형해주세요. "
        "각 변형은 한 줄에 하나씩 출력하세요. 번호·기호 없이."
    )
    try:
        resp = client.chat(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": original},
            ],
            options={"temperature": 0.7},
        )
    except Exception:
        return [original]
    variants = [ln.strip() for ln in resp.splitlines() if ln.strip()]
    return variants[:n_variants] or [original]


# =============================================================================
# Quality filter (Sentence-BERT similarity)
# =============================================================================
def filter_by_similarity(
    original: str,
    augmented: list[str],
    min_sim: float = 0.75,
    max_sim: float = 0.98,
    model_name: str = "jhgan/ko-sroberta-multitask",
) -> list[str]:
    """
    Drop variants whose semantic similarity to `original` is outside [min_sim, max_sim].
    """
    if not augmented:
        return []
    try:
        from sentence_transformers import SentenceTransformer, util
    except ImportError:
        # No filter — return as-is
        return augmented

    model = SentenceTransformer(model_name)
    orig_vec = model.encode(original, convert_to_tensor=True)
    aug_vecs = model.encode(augmented, convert_to_tensor=True)
    sims = util.cos_sim(orig_vec, aug_vecs).squeeze(0).tolist()
    return [
        a for a, s in zip(augmented, sims)
        if min_sim <= s <= max_sim
    ]


__all__ = [
    "eda_synonym_replacement",
    "eda_random_swap",
    "eda_random_deletion",
    "gpt_augment",
    "filter_by_similarity",
]

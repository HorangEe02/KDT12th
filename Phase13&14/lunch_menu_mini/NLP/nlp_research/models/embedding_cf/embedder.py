"""
E1 — User / Menu embedding helpers (Sentence-BERT).

Profiles are built from `meal_history` rows (Phase 5 schema). The embedder is
lazy-loaded so the module is importable without `sentence-transformers`.

A `HashEmbedder` fallback is provided for tests / smoke benchmarks; it returns
deterministic 768-dim vectors derived from a SHA-256 hash of the input text.
"""
from __future__ import annotations

import hashlib
import math
from typing import Any, Optional


DEFAULT_MODEL = "jhgan/ko-sroberta-multitask"
DEFAULT_DIM = 768


# =============================================================================
# Profile-text builders
# =============================================================================
def build_user_profile_text(
    meal_history: list[dict[str, Any]],
    max_entries: int = 30,
) -> str:
    """
    Build a Korean profile text from a meal_history list.

    Each row should have at least `menu_name` (or `menu`) and `satisfaction`.
    """
    if not meal_history:
        return "식사 이력 없음"
    parts: list[str] = []
    for row in meal_history[:max_entries]:
        menu = row.get("menu_name") or row.get("menu") or "알수없음"
        sat = row.get("satisfaction")
        if sat is None:
            parts.append(f"{menu}")
        else:
            parts.append(f"{menu} 만족 {sat}점")
    return ". ".join(parts) + "."


def build_menu_text(menu: dict[str, Any]) -> str:
    """Compose a menu's natural-language description for embedding."""
    name = menu.get("name") or menu.get("menu_name") or "메뉴"
    cat = menu.get("category") or menu.get("menu_type") or ""
    cal = menu.get("calories")
    protein = menu.get("protein")
    parts = [name]
    if cat:
        parts.append(f"카테고리 {cat}")
    if cal is not None:
        parts.append(f"칼로리 {int(cal)}")
    if protein is not None:
        parts.append(f"단백질 {int(protein)}")
    return " ".join(parts)


# =============================================================================
# Real embedder (Sentence-BERT)
# =============================================================================
class SBertEmbedder:
    """Sentence-BERT wrapper. Lazy import."""

    def __init__(self, model_name: str = DEFAULT_MODEL):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            raise ImportError(
                "SBertEmbedder requires sentence-transformers. "
                "Install: pip install sentence-transformers"
            ) from e
        self.model = SentenceTransformer(model_name)
        self.dim = self.model.get_sentence_embedding_dimension() or DEFAULT_DIM

    def encode(self, texts: list[str]):
        import numpy as np
        vecs = self.model.encode(texts, normalize_embeddings=True)
        return np.asarray(vecs, dtype="float32")

    def encode_one(self, text: str):
        return self.encode([text])[0]


# =============================================================================
# Deterministic fallback (no deps)
# =============================================================================
class HashEmbedder:
    """
    Deterministic vectors based on SHA-256 of the text.

    Used in tests and `benchmark.py --smoke` so the pipeline works end-to-end
    without downloading a Sentence-BERT model and without numpy.

    Returns numpy arrays when numpy is available, else plain Python lists.
    Both forms are accepted by NumpyBruteForceIndex / make_index.
    """

    # Compact default — keeps the smoke benchmark fast and memory-trivial.
    def __init__(self, dim: int = 64):
        self.dim = dim

    def _hash_vector(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        vec = [
            ((digest[j % len(digest)] / 255.0) - 0.5) * 2.0
            for j in range(self.dim)
        ]
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    def encode(self, texts: list[str]):
        rows = [self._hash_vector(t) for t in texts]
        try:
            import numpy as np
            return np.asarray(rows, dtype="float32")
        except ImportError:
            return rows  # list-of-lists fallback

    def encode_one(self, text: str):
        return self._hash_vector(text)


# =============================================================================
# UserEmbedder — wraps either SBert or Hash, provides profile-text helpers
# =============================================================================
class UserEmbedder:
    """
    High-level interface used by recommender.py.

    By default uses HashEmbedder so tests run without network. Pass
    `use_sbert=True` (or call `use_sbert()`) to switch to the real model.
    """

    def __init__(self, use_sbert: bool = False, model_name: str = DEFAULT_MODEL):
        self.backend: SBertEmbedder | HashEmbedder
        if use_sbert:
            self.backend = SBertEmbedder(model_name)
        else:
            self.backend = HashEmbedder()
        self.dim = self.backend.dim

    def embed_text(self, text: str):
        return self.backend.encode_one(text)

    def embed_user_profile(
        self, meal_history: list[dict[str, Any]], max_entries: int = 30
    ):
        text = build_user_profile_text(meal_history, max_entries=max_entries)
        return self.embed_text(text)

    def embed_menu(self, menu: dict[str, Any]):
        return self.embed_text(build_menu_text(menu))


__all__ = [
    "build_user_profile_text",
    "build_menu_text",
    "UserEmbedder",
    "SBertEmbedder",
    "HashEmbedder",
    "DEFAULT_MODEL",
    "DEFAULT_DIM",
]

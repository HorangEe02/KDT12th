"""
Sentence-BERT 기반 의미 유사도 매칭기.

표준 메뉴 임베딩을 사전 캐싱하고, 쿼리 임베딩과 코사인 유사도 계산.
sentence-transformers 미설치 시 명시적 ImportError 를 반환한다.
"""
from __future__ import annotations

import hashlib
import os
import pickle
from pathlib import Path
from typing import Any

from nlp_mvp.shared.logger import get_logger

logger = get_logger(__name__)

DEFAULT_MODEL = os.getenv("EMBEDDING_MODEL", "jhgan/ko-sroberta-multitask")
CACHE_DIR = Path(__file__).parent / ".cache"


class EmbeddingMatcher:
    """표준 메뉴 임베딩 사전 계산 + 코사인 유사도 매칭."""

    def __init__(
        self,
        standard_menus: list[dict[str, Any]],
        model_name: str = DEFAULT_MODEL,
        cache_enabled: bool = True,
    ):
        try:
            from sentence_transformers import SentenceTransformer  # noqa: F401
            import numpy as np  # noqa: F401
        except ImportError as e:
            raise ImportError(
                "EmbeddingMatcher requires `sentence-transformers` and `numpy`. "
                "Install with: pip install sentence-transformers numpy"
            ) from e

        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        self.standard_menus = standard_menus
        self.model = SentenceTransformer(model_name)
        logger.info(f"Loaded embedding model: {model_name}")

        self.embeddings = self._load_or_compute(cache_enabled)

    # ------------------------------------------------------------------
    # 캐시
    # ------------------------------------------------------------------
    def _cache_key(self) -> str:
        names = "|".join(m["name"] for m in self.standard_menus)
        h = hashlib.md5(names.encode("utf-8")).hexdigest()[:8]
        safe_model = self.model_name.replace("/", "_")
        return f"{safe_model}_{len(self.standard_menus)}_{h}.pkl"

    def _load_or_compute(self, cache_enabled: bool):
        import numpy as np  # noqa: F401

        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_path = CACHE_DIR / self._cache_key()

        if cache_enabled and cache_path.exists():
            try:
                logger.info(f"Loading cached embeddings: {cache_path}")
                with open(cache_path, "rb") as f:
                    return pickle.load(f)
            except Exception as e:
                logger.warning(f"Cache load failed ({e}); recomputing")

        logger.info(f"Computing embeddings for {len(self.standard_menus)} menus...")
        names = [m["name"] for m in self.standard_menus]
        embeddings = self.model.encode(
            names,
            batch_size=32,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        if cache_enabled:
            try:
                with open(cache_path, "wb") as f:
                    pickle.dump(embeddings, f)
                logger.info(f"Cached embeddings to {cache_path}")
            except Exception as e:
                logger.warning(f"Cache write failed: {e}")

        return embeddings

    def invalidate_cache(self) -> None:
        cache_path = CACHE_DIR / self._cache_key()
        if cache_path.exists():
            cache_path.unlink()
            logger.info(f"Cache invalidated: {cache_path}")

    # ------------------------------------------------------------------
    # 매칭
    # ------------------------------------------------------------------
    def match(
        self,
        query: str,
        top_k: int = 3,
        threshold: float = 0.85,
    ) -> list[dict[str, Any]]:
        """단일 쿼리 매칭. threshold 미만은 제외."""
        if not query:
            return []

        import numpy as np

        query_emb = self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )[0]

        sims = self.embeddings @ query_emb  # 정규화 벡터 내적 = 코사인 유사도
        top_indices = np.argsort(-sims)[:top_k]

        results = []
        for idx in top_indices:
            i = int(idx)
            score = float(sims[i])
            if score < threshold:
                continue
            results.append({
                "id": self.standard_menus[i]["id"],
                "name": self.standard_menus[i]["name"],
                "score": score,
            })
        return results

    def batch_match(
        self,
        queries: list[str],
        top_k: int = 3,
        threshold: float = 0.85,
        batch_size: int = 32,
    ) -> list[list[dict[str, Any]]]:
        """배치 매칭."""
        if not queries:
            return []

        import numpy as np

        query_embs = self.model.encode(
            queries,
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        results_all = []
        for q_emb in query_embs:
            sims = self.embeddings @ q_emb
            top_indices = np.argsort(-sims)[:top_k]
            results = []
            for idx in top_indices:
                i = int(idx)
                score = float(sims[i])
                if score < threshold:
                    continue
                results.append({
                    "id": self.standard_menus[i]["id"],
                    "name": self.standard_menus[i]["name"],
                    "score": score,
                })
            results_all.append(results)
        return results_all

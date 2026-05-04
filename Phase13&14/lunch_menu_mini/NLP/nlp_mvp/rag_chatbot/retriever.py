"""
ChromaDB 기반 Retriever — 3 컬렉션 병렬 검색.

chromadb 미설치 시 명시적 ImportError.
"""
from __future__ import annotations

from typing import Any, Optional

from nlp_mvp.rag_chatbot.indexer import (
    DEFAULT_CHROMA_PATH,
    DEFAULT_EMBEDDING_MODEL,
    _make_embedding_fn,
)
from nlp_mvp.shared.logger import get_logger

logger = get_logger(__name__)


class Retriever:
    """3 컬렉션 병렬 검색."""

    def __init__(
        self,
        chroma_path: str = DEFAULT_CHROMA_PATH,
        embedding_model_name: str = DEFAULT_EMBEDDING_MODEL,
    ):
        try:
            from chromadb import PersistentClient
        except ImportError as e:
            raise ImportError(
                "Retriever requires `chromadb`. Install with: pip install chromadb"
            ) from e

        self.client = PersistentClient(path=chroma_path)
        self.embedding_fn = _make_embedding_fn(embedding_model_name)
        logger.info(f"Retriever initialized: {chroma_path}")

    def _get_collection(self, name: str):
        try:
            return self.client.get_collection(
                name=name, embedding_function=self.embedding_fn
            )
        except Exception as e:
            logger.warning(f"Collection {name} not found: {e}")
            return None

    def retrieve(
        self,
        query: str,
        user_id: Optional[int] = None,
        top_k_meal: int = 5,
        top_k_nutrition: int = 5,
        top_k_restaurant: int = 5,
    ) -> dict[str, list[dict[str, Any]]]:
        """3 컬렉션 검색."""
        result: dict[str, list[dict[str, Any]]] = {
            "meal_history": [],
            "nutrition_info": [],
            "restaurants": [],
        }

        # meal_history (user_id 필터)
        coll = self._get_collection("meal_history")
        if coll is not None and top_k_meal > 0:
            where = {"user_id": user_id} if user_id is not None else None
            try:
                res = coll.query(
                    query_texts=[query],
                    n_results=top_k_meal,
                    where=where,
                )
                result["meal_history"] = self._flatten(res)
            except Exception as e:
                logger.warning(f"meal_history retrieve failed: {e}")

        # nutrition_info
        coll = self._get_collection("nutrition_info")
        if coll is not None and top_k_nutrition > 0:
            try:
                res = coll.query(query_texts=[query], n_results=top_k_nutrition)
                result["nutrition_info"] = self._flatten(res)
            except Exception as e:
                logger.warning(f"nutrition_info retrieve failed: {e}")

        # restaurants
        coll = self._get_collection("restaurants")
        if coll is not None and top_k_restaurant > 0:
            try:
                res = coll.query(query_texts=[query], n_results=top_k_restaurant)
                result["restaurants"] = self._flatten(res)
            except Exception as e:
                logger.warning(f"restaurants retrieve failed: {e}")

        logger.info(
            f"retrieve({query!r}): "
            f"meal={len(result['meal_history'])}, "
            f"nutrition={len(result['nutrition_info'])}, "
            f"rest={len(result['restaurants'])}"
        )
        return result

    @staticmethod
    def _flatten(chroma_result: dict) -> list[dict]:
        """ChromaDB 결과 → 평탄화된 list[dict]."""
        docs = chroma_result.get("documents") or [[]]
        metas = chroma_result.get("metadatas") or [[]]
        dists = chroma_result.get("distances") or [[]]
        docs0 = docs[0] if docs else []
        metas0 = metas[0] if metas else []
        dists0 = dists[0] if dists else []
        return [
            {"text": d, "metadata": m or {}, "distance": float(dist)}
            for d, m, dist in zip(docs0, metas0, dists0)
        ]

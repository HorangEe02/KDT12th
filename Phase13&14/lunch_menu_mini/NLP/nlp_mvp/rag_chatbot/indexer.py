"""
ChromaDB 기반 RAG 인덱서.

Mini DB 레코드를 자연어 문장으로 변환하여 3개 컬렉션에 저장.
chromadb / sentence-transformers 미설치 시 명시적 ImportError.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

from sqlalchemy import text

from nlp_mvp.shared.db import get_engine
from nlp_mvp.shared.logger import get_logger

logger = get_logger(__name__)

DEFAULT_CHROMA_PATH = os.getenv(
    "CHROMA_DB_PATH",
    str(Path(__file__).parent / "chroma_store"),
)
DEFAULT_EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL", "jhgan/ko-sroberta-multitask"
)


# =============================================================================
# 문장화 템플릿 — 순수 함수 (의존성 없음, 단위 테스트 가능)
# =============================================================================
def format_meal_history_row(row: dict) -> str:
    """meal_history 레코드를 자연어로."""
    date = row.get("meal_date", "")
    menu = row.get("menu", "미상")
    cal = float(row.get("calories", 0) or 0)
    protein = float(row.get("protein", 0) or 0)
    sat = row.get("satisfaction", 0) or 0
    return (
        f"{date}: {menu} "
        f"({cal:.0f}kcal, 단백질 {protein:.0f}g). 만족도 {sat}/5"
    )


def format_nutrition_row(row: dict) -> str:
    """nutrition_info 레코드 → 자연어."""
    name = row.get("food_name", "")
    cal = float(row.get("calories", 0) or 0)
    protein = float(row.get("protein", 0) or 0)
    carbs = float(row.get("carbs", 0) or 0)
    fat = float(row.get("fat", 0) or 0)
    sodium = float(row.get("sodium", 0) or 0)
    return (
        f"{name}은(는) 1인분 기준 약 {cal:.0f}kcal, "
        f"단백질 {protein:.0f}g, 탄수화물 {carbs:.0f}g, 지방 {fat:.0f}g. "
        f"나트륨 {sodium:.0f}mg."
    )


def format_restaurant_row(row: dict) -> str:
    """restaurants 레코드 → 자연어 (sentiment_score 포함)."""
    name = row.get("name", "")
    category = row.get("category", "일반")
    distance = float(row.get("distance_m", 0) or 0)
    rating = float(row.get("rating", 0) or 0)
    sentiment = row.get("sentiment_score")
    menu_type = row.get("menu_type", "")

    sentiment_str = ""
    if sentiment is not None:
        sentiment_str = f", 감성 점수 {float(sentiment):+.2f}"

    return (
        f"{name}은(는) {category} 식당입니다. "
        f"사무실에서 약 {distance:.0f}m, 평점 {rating:.1f}{sentiment_str}. "
        f"대표 메뉴: {menu_type}"
    )


# =============================================================================
# Custom Embedding Function (lazy import)
# =============================================================================
def _make_embedding_fn(model_name: str):
    """sentence-transformers 기반 EmbeddingFunction 인스턴스 생성."""
    try:
        from chromadb.api.types import EmbeddingFunction
        from sentence_transformers import SentenceTransformer
    except ImportError as e:
        raise ImportError(
            "ChromaDBIndexer requires `chromadb` and `sentence-transformers`. "
            "Install with: pip install chromadb sentence-transformers"
        ) from e

    class KoSBertEmbeddingFunction(EmbeddingFunction):
        def __init__(self, name: str):
            self.model_name = name
            self.model = SentenceTransformer(name)
            logger.info(f"KoSBertEmbeddingFunction initialized: {name}")

        def __call__(self, input):  # type: ignore[override]
            return self.model.encode(
                input,
                normalize_embeddings=True,
                show_progress_bar=False,
            ).tolist()

    return KoSBertEmbeddingFunction(model_name)


# =============================================================================
# 인덱서 메인 클래스
# =============================================================================
class ChromaDBIndexer:
    """Mini DB → ChromaDB 3 컬렉션 인덱싱."""

    COLLECTIONS = ["meal_history", "nutrition_info", "restaurants"]

    def __init__(
        self,
        chroma_path: str = DEFAULT_CHROMA_PATH,
        embedding_model_name: str = DEFAULT_EMBEDDING_MODEL,
    ):
        try:
            from chromadb import PersistentClient
        except ImportError as e:
            raise ImportError(
                "ChromaDBIndexer requires `chromadb`. "
                "Install with: pip install chromadb"
            ) from e

        Path(chroma_path).mkdir(parents=True, exist_ok=True)
        self.chroma_path = chroma_path
        self.client = PersistentClient(path=chroma_path)
        self.embedding_fn = _make_embedding_fn(embedding_model_name)
        logger.info(f"ChromaDBIndexer initialized: path={chroma_path}")

    def _get_or_create_collection(self, name: str):
        return self.client.get_or_create_collection(
            name=name,
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )

    # -------------------------------------------------------------------------
    # 컬렉션별 빌더
    # -------------------------------------------------------------------------
    def build_meal_history_collection(
        self,
        user_id: Optional[int] = None,
        days: int = 60,
    ) -> int:
        """meal_history 컬렉션 빌드 (upsert)."""
        query = """
            SELECT id, user_id, meal_date, menu, calories, protein, satisfaction
            FROM meal_history
            WHERE meal_date >= date('now', :offset)
        """
        params: dict[str, Any] = {"offset": f"-{days} days"}
        if user_id is not None:
            query += " AND user_id = :uid"
            params["uid"] = user_id

        engine = get_engine()
        try:
            with engine.connect() as conn:
                rows = conn.execute(text(query), params).mappings().fetchall()
        except Exception as e:
            logger.warning(f"meal_history query failed: {e}")
            return 0

        if not rows:
            logger.info("meal_history: no rows to index")
            return 0

        coll = self._get_or_create_collection("meal_history")
        documents = [format_meal_history_row(dict(r)) for r in rows]
        ids = [f"mh_{r['id']}" for r in rows]
        metadatas = [
            {
                "user_id": r["user_id"],
                "date": str(r["meal_date"]),
                "menu": r["menu"] or "",
            }
            for r in rows
        ]
        coll.upsert(documents=documents, ids=ids, metadatas=metadatas)
        logger.info(f"meal_history: indexed {len(ids)} rows")
        return len(ids)

    def build_nutrition_collection(self) -> int:
        query = """
            SELECT id, food_name, calories, protein, carbs, fat, sodium
            FROM nutrition_info
        """
        engine = get_engine()
        try:
            with engine.connect() as conn:
                rows = conn.execute(text(query)).mappings().fetchall()
        except Exception as e:
            logger.warning(f"nutrition_info query failed: {e}")
            return 0

        if not rows:
            return 0

        coll = self._get_or_create_collection("nutrition_info")
        documents = [format_nutrition_row(dict(r)) for r in rows]
        ids = [f"nu_{r['id']}" for r in rows]
        metadatas = [{"food_name": r["food_name"] or ""} for r in rows]
        coll.upsert(documents=documents, ids=ids, metadatas=metadatas)
        logger.info(f"nutrition_info: indexed {len(ids)} rows")
        return len(ids)

    def build_restaurant_collection(self) -> int:
        query = """
            SELECT id, name, category, distance_m, rating,
                   sentiment_score, menu_type
            FROM restaurants
        """
        engine = get_engine()
        try:
            with engine.connect() as conn:
                rows = conn.execute(text(query)).mappings().fetchall()
        except Exception as e:
            logger.warning(f"restaurants query failed: {e}")
            return 0

        if not rows:
            return 0

        coll = self._get_or_create_collection("restaurants")
        documents = [format_restaurant_row(dict(r)) for r in rows]
        ids = [f"rt_{r['id']}" for r in rows]
        metadatas = [
            {
                "name": r["name"] or "",
                "category": r["category"] or "",
                "distance_m": float(r["distance_m"] or 0),
                "sentiment_score": float(r["sentiment_score"] or 0),
            }
            for r in rows
        ]
        coll.upsert(documents=documents, ids=ids, metadatas=metadatas)
        logger.info(f"restaurants: indexed {len(ids)} rows")
        return len(ids)

    def build_all(self, user_id: Optional[int] = None) -> dict[str, int]:
        return {
            "meal_history": self.build_meal_history_collection(user_id=user_id),
            "nutrition_info": self.build_nutrition_collection(),
            "restaurants": self.build_restaurant_collection(),
        }

    def clear(self, collection_name: Optional[str] = None) -> None:
        if collection_name:
            try:
                self.client.delete_collection(collection_name)
            except Exception as e:
                logger.warning(f"delete_collection({collection_name}) failed: {e}")
        else:
            for c in self.COLLECTIONS:
                try:
                    self.client.delete_collection(c)
                except Exception:
                    pass
        logger.info(f"cleared: {collection_name or 'all'}")


# =============================================================================
# CLI
# =============================================================================
def main():
    import argparse
    import logging

    parser = argparse.ArgumentParser(description="ChromaDB 인덱서")
    parser.add_argument("--user-id", type=int, default=None)
    parser.add_argument("--days", type=int, default=60)
    parser.add_argument("--clear", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    indexer = ChromaDBIndexer()
    if args.clear:
        indexer.clear()
    result = indexer.build_all(user_id=args.user_id)
    print(f"Indexed: {result}")


if __name__ == "__main__":
    main()

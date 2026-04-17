"""Agentic RAG — 구장별 원정 팁을 ChromaDB + bge-m3(Ollama 임베딩)로 검색.

data/knowledge/away_game_tips.json을 인덱싱하고 의미 유사도 검색 제공.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from src import config

log = logging.getLogger(__name__)

_COLLECTION: Any = None
_COLLECTION_NAME = "away_game_tips"


def _embed_with_ollama(texts: list[str]) -> list[list[float]]:
    """Ollama bge-m3로 배치 임베딩 (단순 순회)."""
    from src.ai.ollama_client import embed
    out: list[list[float]] = []
    for t in texts:
        v = embed(t, model=config.OLLAMA_EMBED_MODEL)
        out.append(v)
    return out


def _get_collection():
    """ChromaDB 컬렉션 지연 초기화 — 임베딩은 수동 주입(EmbeddingFunction 우회)."""
    global _COLLECTION
    if _COLLECTION is not None:
        return _COLLECTION
    import chromadb

    config.CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(config.CHROMA_DB_DIR))
    _COLLECTION = client.get_or_create_collection(name=_COLLECTION_NAME)
    return _COLLECTION


def build_index(rebuild: bool = False) -> int:
    """JSON → ChromaDB 인덱싱. 이미 존재하고 rebuild=False면 skip."""
    col = _get_collection()

    if not rebuild and col.count() > 0:
        log.info("기존 인덱스 존재 (%d개), skip", col.count())
        return col.count()

    tips_path = config.KNOWLEDGE_DIR / "away_game_tips.json"
    if not tips_path.exists():
        raise FileNotFoundError(f"지식 파일 없음: {tips_path}")

    tips = json.loads(tips_path.read_text(encoding="utf-8"))
    ids = [f"tip_{i}" for i in range(len(tips))]
    documents = [t["tip"] for t in tips]
    metadatas = [{"stadium": t["stadium"], "category": t["category"]} for t in tips]

    log.info("임베딩 생성 중 (%d개)...", len(documents))
    embeddings = _embed_with_ollama(documents)
    # 빈 벡터가 섞이면 ChromaDB upsert 실패 → 실패 인덱스 스킵
    valid = [(i, d, m, e) for i, d, m, e in zip(ids, documents, metadatas, embeddings) if e]
    if len(valid) < len(documents):
        log.warning("임베딩 실패 %d건 스킵", len(documents) - len(valid))

    if rebuild and col.count() > 0:
        col.delete(ids=ids)

    col.upsert(
        ids=[v[0] for v in valid],
        documents=[v[1] for v in valid],
        metadatas=[v[2] for v in valid],
        embeddings=[v[3] for v in valid],
    )
    return col.count()


def search_tips(query: str, stadium: str | None = None, top_k: int = 3) -> list[dict]:
    """의미 유사도 기반 팁 검색. 실패 시 빈 리스트."""
    try:
        col = _get_collection()
    except Exception as exc:
        log.warning("ChromaDB 초기화 실패: %s", exc)
        return []

    try:
        qvec = _embed_with_ollama([query])
        if not qvec or not qvec[0]:
            log.warning("쿼리 임베딩 실패")
            return []

        where: dict | None = {"stadium": stadium} if stadium else None
        results = col.query(
            query_embeddings=[qvec[0]],
            n_results=top_k,
            where=where,
        )
    except Exception as exc:
        log.warning("RAG 검색 실패: %s", exc)
        return []

    if not results or not results.get("documents") or not results["documents"][0]:
        return []

    tips: list[dict] = []
    docs = results["documents"][0]
    metas = (results.get("metadatas") or [[]])[0]
    dists = (results.get("distances") or [[]])[0]
    for i, doc in enumerate(docs):
        tips.append({
            "tip": doc,
            "stadium": (metas[i] or {}).get("stadium") if i < len(metas) else None,
            "category": (metas[i] or {}).get("category") if i < len(metas) else None,
            "distance": float(dists[i]) if i < len(dists) else None,
        })
    return tips


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    count = build_index(rebuild=True)
    print(f"✅ {count}개 팁 인덱싱 완료 → {config.CHROMA_DB_DIR}")

    queries = [
        ("어디에 앉는 게 좋을까", "광주"),
        ("원정 전 간단한 식사", None),
        ("롯데 응원 팁", "사직"),
    ]
    for q, stadium in queries:
        print(f"\n--- 쿼리: '{q}' (구장: {stadium}) ---")
        results = search_tips(q, stadium=stadium, top_k=3)
        for r in results:
            print(f"  [{r['stadium']}/{r['category']}] {r['tip'][:80]}...")

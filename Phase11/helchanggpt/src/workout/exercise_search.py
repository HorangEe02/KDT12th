"""
exercise_search.py
운동 정보를 BM25 키워드 검색 + 임베딩 의미 검색으로 조회합니다.

BM25: 운동명, 부위, 장비 등 정확한 키워드 매칭
임베딩: "무릎에 부담 적은 하체 운동" 같은 자연어 질의
"""

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SearchResult:
    """운동 검색 결과"""
    name: str
    score: float
    method: str           # "bm25" | "embedding" | "db_filter"
    exercise_data: dict


DATA_DIR = Path(__file__).parent.parent.parent / "data" / "exercises"


def _load_exercise_db() -> list[dict]:
    """운동 DB JSON을 로드합니다."""
    db_path = DATA_DIR / "exercise_db.json"
    if not db_path.exists():
        return []
    with open(db_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("exercises", data) if isinstance(data, dict) else data


# ═══════════════════════════════════════
# 필터 기반 검색 (가장 빠름)
# ═══════════════════════════════════════

def search_by_muscle(muscle: str, difficulty: str | None = None) -> list[SearchResult]:
    """근육군과 난이도로 운동을 검색합니다."""
    exercises = _load_exercise_db()
    results = []

    for ex in exercises:
        target = ex.get("target_muscle", "")
        secondaries = ex.get("secondary_muscles", [])
        all_muscles = [target] + secondaries

        if any(muscle in m for m in all_muscles):
            if difficulty and ex.get("difficulty") != difficulty:
                continue
            results.append(SearchResult(
                name=ex["name"],
                score=1.0 if muscle == target else 0.7,
                method="db_filter",
                exercise_data=ex,
            ))

    results.sort(key=lambda r: r.score, reverse=True)
    return results


def search_by_equipment(equipment: str) -> list[SearchResult]:
    """장비로 운동을 검색합니다."""
    exercises = _load_exercise_db()
    results = []

    for ex in exercises:
        eq = ex.get("equipment", "")
        if equipment in eq or equipment == "맨몸" and "맨몸" in eq:
            results.append(SearchResult(
                name=ex["name"],
                score=1.0,
                method="db_filter",
                exercise_data=ex,
            ))

    return results


def search_safe_exercises(constraints: list[str]) -> list[SearchResult]:
    """제약사항을 고려하여 안전한 운동만 검색합니다."""
    exercises = _load_exercise_db()
    results = []

    for ex in exercises:
        contraindications = ex.get("contraindications", [])
        is_safe = not any(c in " ".join(contraindications) for c in constraints)

        if is_safe:
            results.append(SearchResult(
                name=ex["name"],
                score=1.0,
                method="db_filter",
                exercise_data=ex,
            ))

    return results


# ═══════════════════════════════════════
# BM25 키워드 검색
# ═══════════════════════════════════════

class BM25ExerciseSearch:
    """BM25 기반 운동 키워드 검색."""

    def __init__(self):
        self.exercises = _load_exercise_db()
        self.index = None
        self._build_index()

    def _build_index(self):
        """BM25 인덱스를 생성합니다."""
        try:
            from rank_bm25 import BM25Okapi
        except ImportError:
            self.index = None
            return

        self.corpus = []
        for ex in self.exercises:
            text = (
                f"{ex['name']} {ex.get('name_en', '')} "
                f"{ex.get('target_muscle', '')} {' '.join(ex.get('secondary_muscles', []))} "
                f"{ex.get('category', '')} {ex.get('difficulty', '')} "
                f"{ex.get('equipment', '')} "
                f"{ex.get('description', '')} "
                f"{' '.join(ex.get('common_mistakes', []))} "
                f"{' '.join(ex.get('alternatives', []))}"
            )
            self.corpus.append(text.split())

        self.index = BM25Okapi(self.corpus)

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        """BM25로 운동을 검색합니다."""
        if self.index is None:
            return self._fallback_search(query, top_k)

        tokenized_query = query.split()
        scores = self.index.get_scores(tokenized_query)

        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        results = []

        for idx, score in ranked[:top_k]:
            if score > 0:
                results.append(SearchResult(
                    name=self.exercises[idx]["name"],
                    score=round(score, 3),
                    method="bm25",
                    exercise_data=self.exercises[idx],
                ))

        return results

    def _fallback_search(self, query: str, top_k: int) -> list[SearchResult]:
        """BM25 미설치 시 간단한 키워드 매칭."""
        results = []
        for ex in self.exercises:
            text = f"{ex['name']} {ex.get('target_muscle', '')} {ex.get('description', '')}"
            score = sum(1 for word in query.split() if word in text)
            if score > 0:
                results.append(SearchResult(
                    name=ex["name"], score=score, method="keyword_fallback", exercise_data=ex,
                ))

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]


# ═══════════════════════════════════════
# 임베딩 의미 검색 (Semantic)
# ═══════════════════════════════════════

class EmbeddingExerciseSearch:
    """sentence-transformers + numpy 기반 운동 의미 검색."""

    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        self.exercises = _load_exercise_db()
        self.model = None
        self.embeddings = None
        self.model_name = model_name
        self._build_index()

    def _build_index(self):
        """운동 정보를 임베딩합니다."""
        try:
            from sentence_transformers import SentenceTransformer
            import numpy as np
        except ImportError:
            return

        self.model = SentenceTransformer(self.model_name)

        texts = []
        for ex in self.exercises:
            text = (
                f"{ex['name']} {ex.get('name_en', '')} "
                f"{ex.get('target_muscle', '')} {' '.join(ex.get('secondary_muscles', []))} "
                f"{ex.get('category', '')} {ex.get('difficulty', '')} "
                f"{ex.get('equipment', '')} "
                f"{ex.get('description', '')}"
            )
            texts.append(text)

        self.embeddings = self.model.encode(texts, show_progress_bar=False)

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        """의미 기반 검색을 수행합니다."""
        if self.model is None or self.embeddings is None:
            return []

        import numpy as np

        query_emb = self.model.encode([query])
        # 코사인 유사도
        similarities = np.dot(self.embeddings, query_emb.T).flatten()
        norms = np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_emb)
        scores = similarities / (norms + 1e-8)

        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        results = []

        for idx, score in ranked[:top_k]:
            if score > 0.1:
                results.append(SearchResult(
                    name=self.exercises[idx]["name"],
                    score=round(float(score), 3),
                    method="embedding",
                    exercise_data=self.exercises[idx],
                ))

        return results


# ═══════════════════════════════════════
# 통합 검색
# ═══════════════════════════════════════

def search_exercises(
    query: str,
    method: str = "bm25",
    top_k: int = 5,
    constraints: list[str] | None = None,
) -> list[SearchResult]:
    """
    운동을 검색합니다.

    Args:
        query: 검색 질의 (예: "무릎에 부담 적은 하체 운동")
        method: "bm25" | "embedding" | "filter"
        top_k: 최대 결과 수
        constraints: 제약사항 (해당 부위 운동 제외)
    """
    if method == "embedding":
        searcher = EmbeddingExerciseSearch()
        results = searcher.search(query, top_k)
    elif method == "filter":
        # 근육군명이면 필터 검색
        results = search_by_muscle(query)
        if not results:
            results = search_by_equipment(query)
    else:
        searcher = BM25ExerciseSearch()
        results = searcher.search(query, top_k)

    # 제약사항 필터링
    if constraints:
        filtered = []
        for r in results:
            contras = r.exercise_data.get("contraindications", [])
            is_safe = not any(c in " ".join(contras) for c in constraints)
            if is_safe:
                filtered.append(r)
            else:
                # 대체 운동 표시
                r.exercise_data["_excluded_reason"] = f"제약사항 ({', '.join(constraints)})에 해당"
                r.exercise_data["_use_alternatives"] = r.exercise_data.get("alternatives", [])
        results = filtered

    return results[:top_k]

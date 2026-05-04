"""
3단계 하이브리드 메뉴명 정규화 엔진.

Stage 1: 규칙 전처리 + 동의어 + 정확 일치
Stage 2: Levenshtein 편집거리
Stage 3: Sentence-BERT 임베딩 유사도 (옵션)
"""
from __future__ import annotations

import logging
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import text

from nlp_mvp.menu_normalizer import levenshtein, rules
from nlp_mvp.menu_normalizer.loader import (
    NutritionDBLoader,
    StandardMenuLoader,
    SyntheticMenuLoader,
)
from nlp_mvp.shared.db import get_engine, get_session
from nlp_mvp.shared.logger import get_logger

logger = get_logger(__name__)


# =============================================================================
# 결과 데이터 클래스
# =============================================================================
@dataclass
class NormalizationResult:
    raw: str
    cleaned: str
    matched_id: Optional[str]
    matched_name: Optional[str]
    confidence: float
    method: str  # "rule" | "levenshtein" | "embedding" | "none" | "error"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# =============================================================================
# 스키마 확장
# =============================================================================
MENU_NORM_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS menu_normalization (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_name TEXT NOT NULL,
    normalized_id TEXT,
    normalized_name TEXT,
    confidence REAL NOT NULL DEFAULT 0.0,
    method TEXT NOT NULL,
    source_table TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (raw_name, source_table)
);
CREATE INDEX IF NOT EXISTS idx_menu_norm_raw ON menu_normalization(raw_name);
CREATE INDEX IF NOT EXISTS idx_menu_norm_id ON menu_normalization(normalized_id);
"""


def ensure_schema(engine=None) -> None:
    """menu_normalization 테이블 생성 (멱등)."""
    engine = engine or get_engine()
    with engine.begin() as conn:
        for stmt in MENU_NORM_TABLE_SQL.strip().split(";"):
            stmt = stmt.strip()
            if stmt:
                conn.execute(text(stmt))
    logger.info("menu_normalization schema ensured")


# =============================================================================
# 메인 클래스
# =============================================================================
class MenuNormalizer:
    """3단계 하이브리드 메뉴명 정규화기."""

    def __init__(
        self,
        loader: Optional[StandardMenuLoader] = None,
        synonym_dict_path: Optional[str] = None,
        embedding_model: Optional[str] = None,
        levenshtein_cutoff: Optional[int] = None,
        embedding_threshold: float = 0.85,
        enable_embedding: bool = True,
    ):
        self.loader = loader or SyntheticMenuLoader()
        self.standard_menus = self.loader.load()
        if not self.standard_menus:
            raise ValueError("No standard menus loaded")
        self.standard_name_set = {m["name"] for m in self.standard_menus}
        self.standard_by_name = {m["name"]: m for m in self.standard_menus}

        self.synonym_dict = rules.load_synonym_dict(synonym_dict_path)

        self.levenshtein_cutoff = levenshtein_cutoff  # None → adaptive

        self.enable_embedding = enable_embedding
        self.embedding_threshold = embedding_threshold
        self._embedding_matcher = None
        self._embedding_model_name = embedding_model

        logger.info(
            f"MenuNormalizer initialized: "
            f"{len(self.standard_menus)} menus, "
            f"embedding={'on' if enable_embedding else 'off'}"
        )

    @property
    def embedding_matcher(self):
        """lazy 로딩."""
        if self._embedding_matcher is None:
            if not self.enable_embedding:
                raise RuntimeError("Embedding matching is disabled")
            from nlp_mvp.menu_normalizer.embedding_matcher import EmbeddingMatcher
            self._embedding_matcher = EmbeddingMatcher(
                standard_menus=self.standard_menus,
                model_name=self._embedding_model_name or "jhgan/ko-sroberta-multitask",
            )
        return self._embedding_matcher

    # -------------------------------------------------------------------------
    # 메인 진입점
    # -------------------------------------------------------------------------
    def normalize(self, raw: Any) -> NormalizationResult:
        try:
            if not isinstance(raw, str) or not raw:
                return NormalizationResult(
                    raw=raw if isinstance(raw, str) else "",
                    cleaned="",
                    matched_id=None,
                    matched_name=None,
                    confidence=0.0,
                    method="none",
                )

            cleaned = rules.preprocess_menu_name(raw)
            cleaned = rules.apply_synonyms(cleaned, self.synonym_dict)

            if cleaned in self.standard_name_set:
                menu = self.standard_by_name[cleaned]
                return NormalizationResult(
                    raw=raw,
                    cleaned=cleaned,
                    matched_id=menu["id"],
                    matched_name=menu["name"],
                    confidence=1.0,
                    method="rule",
                )

            lev_candidates = levenshtein.find_candidates(
                cleaned,
                self.standard_menus,
                cutoff=self.levenshtein_cutoff,
            )
            if lev_candidates:
                best = lev_candidates[0]
                return NormalizationResult(
                    raw=raw,
                    cleaned=cleaned,
                    matched_id=best["id"],
                    matched_name=best["name"],
                    confidence=best["confidence"],
                    method="levenshtein",
                )

            if self.enable_embedding:
                emb_candidates = self.embedding_matcher.match(
                    cleaned, threshold=self.embedding_threshold
                )
                if emb_candidates:
                    best = emb_candidates[0]
                    return NormalizationResult(
                        raw=raw,
                        cleaned=cleaned,
                        matched_id=best["id"],
                        matched_name=best["name"],
                        confidence=best["score"],
                        method="embedding",
                    )

            return NormalizationResult(
                raw=raw,
                cleaned=cleaned,
                matched_id=None,
                matched_name=None,
                confidence=0.0,
                method="none",
            )

        except Exception as e:
            logger.exception(f"normalize({raw!r}) failed: {e}")
            return NormalizationResult(
                raw=raw if isinstance(raw, str) else "",
                cleaned="",
                matched_id=None,
                matched_name=None,
                confidence=0.0,
                method="error",
            )

    def normalize_batch(self, raws: list[str]) -> list[NormalizationResult]:
        return [self.normalize(r) for r in raws]

    # -------------------------------------------------------------------------
    # DB 적재
    # -------------------------------------------------------------------------
    def save_result(
        self,
        result: NormalizationResult,
        source_table: str = "restaurants.menu_type",
    ) -> None:
        with get_session() as session:
            session.execute(
                text("""
                    INSERT INTO menu_normalization
                        (raw_name, normalized_id, normalized_name,
                         confidence, method, source_table, updated_at)
                    VALUES (:raw, :nid, :nname, :conf, :method, :src, :ts)
                    ON CONFLICT (raw_name, source_table) DO UPDATE SET
                        normalized_id = excluded.normalized_id,
                        normalized_name = excluded.normalized_name,
                        confidence = excluded.confidence,
                        method = excluded.method,
                        updated_at = excluded.updated_at
                """),
                {
                    "raw": result.raw,
                    "nid": result.matched_id,
                    "nname": result.matched_name,
                    "conf": result.confidence,
                    "method": result.method,
                    "src": source_table,
                    "ts": datetime.utcnow().isoformat(),
                },
            )
            session.commit()


# =============================================================================
# 배치 파이프라인
# =============================================================================
def run_batch_normalization(
    source_query: str = "SELECT DISTINCT menu_type FROM restaurants WHERE menu_type IS NOT NULL",
    source_table: str = "restaurants.menu_type",
    limit: int | None = None,
    dry_run: bool = False,
    normalizer: Optional[MenuNormalizer] = None,
) -> dict[str, Any]:
    """DB 의 원시 메뉴명을 일괄 정규화하여 menu_normalization 에 적재."""
    start = time.time()
    ensure_schema()
    normalizer = normalizer or MenuNormalizer()

    stats: dict[str, Any] = {
        "processed": 0,
        "rule": 0,
        "levenshtein": 0,
        "embedding": 0,
        "none": 0,
        "error": 0,
    }

    try:
        with get_session() as session:
            rows = session.execute(text(source_query)).fetchall()
        raws = [r[0] for r in rows if r[0]]
    except Exception as e:
        logger.warning(f"Source query failed ({e}); falling back to empty list")
        raws = []

    if limit:
        raws = raws[:limit]

    logger.info(f"Normalizing {len(raws)} raw menu names from {source_table}")

    for raw in raws:
        result = normalizer.normalize(raw)
        stats["processed"] += 1
        stats[result.method] = stats.get(result.method, 0) + 1
        if not dry_run:
            try:
                normalizer.save_result(result, source_table=source_table)
            except Exception as e:
                logger.warning(f"save_result failed for {raw!r}: {e}")
                stats["error"] = stats.get("error", 0) + 1

    stats["duration_sec"] = round(time.time() - start, 3)
    matched = stats["processed"] - stats.get("none", 0) - stats.get("error", 0)
    stats["match_rate"] = round(matched / max(1, stats["processed"]), 3)
    logger.info(f"Batch normalization done: {stats}")
    return stats


# =============================================================================
# CLI
# =============================================================================
def main():
    import argparse

    parser = argparse.ArgumentParser(description="Mini B1 Menu Normalizer")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--source",
        choices=["synthetic", "nutrition_db"],
        default="synthetic",
    )
    parser.add_argument("--disable-embedding", action="store_true")
    parser.add_argument(
        "--source-query",
        default="SELECT DISTINCT menu_type FROM restaurants WHERE menu_type IS NOT NULL",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    loader: StandardMenuLoader
    if args.source == "synthetic":
        loader = SyntheticMenuLoader()
    else:
        loader = NutritionDBLoader()

    normalizer = MenuNormalizer(
        loader=loader,
        enable_embedding=not args.disable_embedding,
    )

    stats = run_batch_normalization(
        source_query=args.source_query,
        limit=args.limit,
        dry_run=args.dry_run,
        normalizer=normalizer,
    )
    print(stats)


if __name__ == "__main__":
    main()

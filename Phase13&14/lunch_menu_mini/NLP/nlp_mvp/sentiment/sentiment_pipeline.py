"""
SentimentAnalyzer — KcELECTRA Zero-shot 감성분석.

- 싱글톤 로딩 (`get_default_analyzer()`)
- CPU/GPU 자동 선택 및 배치 사이즈 자동
- id2label 정규화 (모델별 편차 흡수)
- transformers / torch 미설치 시 명시적 ImportError
"""
from __future__ import annotations

import os
import time
from functools import lru_cache
from typing import Any, Optional

from nlp_mvp.shared.logger import get_logger

logger = get_logger(__name__)

# =============================================================================
# 상수
# =============================================================================
DEFAULT_MODEL = os.getenv(
    "SENTIMENT_MODEL",
    "nlp04/korean_sentiment_analysis_kcelectra",
)
FALLBACK_MODEL = "beomi/KcELECTRA-base-v2022"

# 표준 라벨 3종
CANONICAL_LABELS = frozenset({"positive", "neutral", "negative"})

# 모델별 id2label 편차 흡수
LABEL_ALIASES = {
    "긍정": "positive", "positive": "positive", "POS": "positive",
    "pos": "positive", "LABEL_2": "positive",
    "중립": "neutral", "neutral": "neutral", "NEU": "neutral",
    "neu": "neutral", "LABEL_1": "neutral",
    "부정": "negative", "negative": "negative", "NEG": "negative",
    "neg": "negative", "LABEL_0": "negative",
}


# =============================================================================
# SentimentAnalyzer
# =============================================================================
class SentimentAnalyzer:
    """
    사전학습 감성분석 모델 래퍼.

    transformers + torch 가 설치되어 있어야 동작한다.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        device: str = "auto",
    ):
        try:
            import torch  # noqa: F401
            from transformers import (  # noqa: F401
                AutoModelForSequenceClassification, AutoTokenizer
            )
        except ImportError as e:
            raise ImportError(
                "transformers 및 torch 가 필요합니다. "
                "`pip install transformers torch` 후 다시 시도하세요."
            ) from e

        self.model_name = model_name or DEFAULT_MODEL
        self.device = self._resolve_device(device)
        self.default_batch_size = 32 if self.device == "cuda" else 8
        self._load_model()

    # -------------------------------------------------------------------------
    @staticmethod
    def _resolve_device(device: str) -> str:
        if device != "auto":
            return device
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"

    def _load_model(self) -> None:
        from transformers import (
            AutoModelForSequenceClassification, AutoTokenizer
        )
        logger.info(f"Loading sentiment model: {self.model_name} on {self.device}")
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name
            ).to(self.device)
        except Exception as e:
            logger.warning(
                "Primary model %s failed (%s), falling back to %s",
                self.model_name, e, FALLBACK_MODEL,
            )
            self.model_name = FALLBACK_MODEL
            self.tokenizer = AutoTokenizer.from_pretrained(FALLBACK_MODEL)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                FALLBACK_MODEL
            ).to(self.device)

        self.model.eval()
        # id2label 정규화
        raw = self.model.config.id2label
        self.id2label = {
            idx: LABEL_ALIASES.get(lbl, str(lbl).lower())
            for idx, lbl in raw.items()
        }
        logger.info(f"id2label: {self.id2label}")

    # -------------------------------------------------------------------------
    def analyze(self, text: str) -> dict[str, Any]:
        """단건 추론."""
        return self.analyze_batch([text], batch_size=1)[0]

    def analyze_batch(
        self,
        texts: list[str],
        batch_size: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """
        배치 추론.

        Returns:
            [{"label": "positive|neutral|negative", "confidence": float}, ...]
        """
        if not texts:
            return []

        import torch

        batch_size = batch_size or self.default_batch_size
        results: list[dict[str, Any]] = []
        start = time.time()

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            enc = self.tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=256,
                return_tensors="pt",
            ).to(self.device)
            with torch.no_grad():
                logits = self.model(**enc).logits
            probs = torch.softmax(logits, dim=-1)
            confidences, indices = probs.max(dim=-1)
            for conf, idx in zip(confidences.tolist(), indices.tolist()):
                label = self.id2label.get(idx, "neutral")
                if label not in CANONICAL_LABELS:
                    label = "neutral"
                results.append({"label": label, "confidence": float(conf)})

        elapsed = time.time() - start
        if elapsed > 0:
            logger.info(
                "Analyzed %d samples in %.2fs (%.1f/s)",
                len(texts), elapsed, len(texts) / elapsed,
            )
        return results


# =============================================================================
# aggregate — 음식점별 집계
# =============================================================================
def aggregate(
    results: list[dict[str, Any]],
    min_sample: int = 5,
) -> dict[str, Any]:
    """
    리뷰별 감성 분석 결과 → 음식점 단위 집계.

    공식:
        score = (pos_count - neg_count) / total ∈ [-1, +1]

    Returns:
        {
            "score": float | None,          # min_sample 미만이면 None
            "pos_ratio": float,
            "neg_ratio": float,
            "neu_ratio": float,
            "sample_size": int,
            "reason": str | None,
        }
    """
    total = len(results)
    if total < min_sample:
        return {
            "score": None,
            "pos_ratio": 0.0,
            "neg_ratio": 0.0,
            "neu_ratio": 0.0,
            "sample_size": total,
            "reason": "insufficient_samples",
        }

    pos = sum(1 for r in results if r.get("label") == "positive")
    neg = sum(1 for r in results if r.get("label") == "negative")
    neu = sum(1 for r in results if r.get("label") == "neutral")
    return {
        "score": (pos - neg) / total,
        "pos_ratio": pos / total,
        "neg_ratio": neg / total,
        "neu_ratio": neu / total,
        "sample_size": total,
        "reason": None,
    }


# =============================================================================
# 싱글톤
# =============================================================================
@lru_cache(maxsize=1)
def get_default_analyzer() -> SentimentAnalyzer:
    """프로세스당 1회만 초기화되는 analyzer."""
    return SentimentAnalyzer()

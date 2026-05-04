"""
리뷰 데이터 소스 — 플러거블 어댑터.

⚠️ 법적 고지 (Legal Notice)
================================
1. 본 크롤러는 연구·학습 목적의 공개 데이터 수집용입니다.
2. 상업적 재배포 및 대량 크롤링은 카카오·네이버 ToS 위반입니다.
3. 로그인 필요 영역·개인정보 필드에 접근하지 않습니다.
4. 운영 배포 시 공식 파트너 API 교체가 필수입니다.
5. 저작권은 원 작성자·플랫폼에 귀속됩니다.
"""
from __future__ import annotations

import random
import time
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from nlp_mvp.shared.logger import get_logger

logger = get_logger(__name__)


# =============================================================================
# 50건 합성 리뷰 시드 (긍정 20 / 중립 10 / 부정 20)
# 모두 직접 작성한 한국어 문장으로 저작권 문제 없음.
# =============================================================================
_POSITIVE_REVIEWS: tuple[str, ...] = (
    "음식이 정말 맛있고 사장님도 친절해요. 다음에도 올게요!",
    "가격 대비 양도 많고 정말 만족스럽네요.",
    "재료가 신선해서 좋았습니다. 분위기도 좋아요.",
    "분위기가 좋고 음식도 훌륭해요. 데이트 장소로 추천!",
    "최고의 맛집! 주변 사람들에게 추천하고 싶어요.",
    "서비스가 빠르고 친절해요. 음식 맛도 일품입니다.",
    "가성비 최고네요. 재방문 의사 100%.",
    "청결하고 맛있어요. 가족들과 함께 가기 좋아요.",
    "사장님이 정말 친절하시고 음식도 맛있어요.",
    "정성이 느껴지는 한 끼였습니다. 감동입니다.",
    "매운맛이 일품이에요. 속이 뻥 뚫립니다.",
    "국물이 깊고 진해서 정말 좋아요.",
    "반찬까지 하나하나 맛있어요. 대단합니다.",
    "밥이 찰지고 반찬도 깔끔해요.",
    "고기 질이 정말 좋네요. 부드럽고 맛있어요.",
    "디저트까지 완벽한 식사였어요.",
    "매장이 깨끗하고 직원분들이 친절해요.",
    "회식 장소로 딱 좋아요. 다들 만족했어요.",
    "혼밥하기 편한 분위기에요. 음식도 맛있고.",
    "정말 오랜만에 맛있는 한 끼를 먹었네요. 감사합니다.",
)

_NEUTRAL_REVIEWS: tuple[str, ...] = (
    "평범한 맛이에요. 특별하진 않지만 무난합니다.",
    "가격은 적당하고 맛도 그럭저럭이네요.",
    "위치는 좋은데 음식은 보통이에요.",
    "대기 시간이 조금 있었지만 그런대로 먹을 만했어요.",
    "혼자 먹기엔 괜찮은 정도의 맛이에요.",
    "평균적인 한식당입니다.",
    "점심 메뉴로 먹기에 무난해요.",
    "크게 맛있지도 나쁘지도 않아요.",
    "한 번 가볼 만한 곳이에요.",
    "기본은 하는 집이네요.",
)

_NEGATIVE_REVIEWS: tuple[str, ...] = (
    "음식이 너무 짜고 서비스도 최악이었어요.",
    "다시는 안 갈 거예요. 정말 실망.",
    "가격만 비싸고 맛은 형편없어요.",
    "위생 상태가 의심스러워요. 비추천.",
    "주문한지 40분 지나도 음식이 안 나와요.",
    "재료가 신선하지 않아요. 비린 맛이 나요.",
    "사장님이 불친절해서 기분 상했어요.",
    "양이 너무 적어서 배고파서 나왔어요.",
    "음식이 식어서 나왔어요. 맛도 별로.",
    "화장실이 너무 더러웠어요. 기본이 안 됐네요.",
    "소음이 너무 심해서 대화가 안 돼요.",
    "가격 대비 품질이 떨어져요.",
    "매장이 좁고 답답해요. 재방문 안 할래요.",
    "직원들이 바빠서 부를 수가 없었어요.",
    "맛이 너무 자극적이에요. 조미료 맛만 나요.",
    "예약을 했는데도 한참 기다렸어요.",
    "사진과 실제가 너무 달라요. 실망.",
    "반찬이 모자라서 추가 요청했는데 안 줘요.",
    "음식이 덜 익어서 나왔어요. 위험해요.",
    "주차가 너무 어려워요. 편의성이 떨어집니다.",
)

SEED_REVIEWS: tuple[str, ...] = (
    _POSITIVE_REVIEWS + _NEUTRAL_REVIEWS + _NEGATIVE_REVIEWS
)


# =============================================================================
# 추상 인터페이스
# =============================================================================
class ReviewSource(ABC):
    """리뷰 데이터 소스 추상."""

    name: str = "base"

    @abstractmethod
    def fetch(
        self,
        restaurant_id: int,
        max_count: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Returns:
            [
                {
                    "source": str,           # self.name
                    "text": str,             # 원문
                    "external_id": str | None,
                    "fetched_at": str,       # ISO datetime
                },
                ...
            ]
        """


# =============================================================================
# SyntheticSource — 50건 합성 리뷰 (Deterministic)
# =============================================================================
class SyntheticSource(ReviewSource):
    """
    테스트·파이프라인 검증용 합성 리뷰.
    restaurant_id 해시 기반 deterministic 샘플링.
    """
    name = "synthetic"

    def fetch(
        self,
        restaurant_id: int,
        max_count: int = 100,
    ) -> list[dict[str, Any]]:
        rng = random.Random(restaurant_id)
        count = min(max_count, len(SEED_REVIEWS))
        sampled = rng.sample(list(SEED_REVIEWS), count)
        now = datetime.utcnow().isoformat()
        return [
            {
                "source": self.name,
                "text": text,
                "external_id": f"synthetic-{restaurant_id}-{i}",
                "fetched_at": now,
            }
            for i, text in enumerate(sampled)
        ]


# =============================================================================
# AIHubSource — AI-Hub CSV 로더 (선택)
# =============================================================================
class AIHubSource(ReviewSource):
    """
    AI-Hub "한국어 음식 리뷰 데이터셋" CSV 로더.

    사전 준비:
        1. https://aihub.or.kr 에서 데이터셋 다운로드
        2. CSV 를 nlp_mvp/data/raw/aihub_food_reviews.csv 에 저장
        3. 컬럼: review_text (필수)
    """
    name = "aihub"

    def __init__(self, csv_path: Optional[Path] = None):
        self.csv_path = csv_path or Path("nlp_mvp/data/raw/aihub_food_reviews.csv")
        self._df = None

    def _load(self):
        if self._df is not None:
            return self._df
        if not self.csv_path.exists():
            raise FileNotFoundError(
                f"AI-Hub CSV not found: {self.csv_path}. "
                "See GUIDE_NLP_MVP_STEP1_SENTIMENT.md §14.B for download guide."
            )
        import pandas as pd  # lazy import
        self._df = pd.read_csv(self.csv_path)
        return self._df

    def fetch(
        self,
        restaurant_id: int,
        max_count: int = 100,
    ) -> list[dict[str, Any]]:
        df = self._load()
        if "review_text" not in df.columns:
            logger.error("AI-Hub CSV missing 'review_text' column")
            return []
        sample = df.sample(
            n=min(max_count, len(df)),
            random_state=restaurant_id,
        )
        now = datetime.utcnow().isoformat()
        return [
            {
                "source": self.name,
                "text": str(row["review_text"]),
                "external_id": f"aihub-{idx}",
                "fetched_at": now,
            }
            for idx, row in sample.iterrows()
        ]


# =============================================================================
# KakaoPublicSource — 공개 페이지 크롤러 (스켈레톤, 미구현)
# =============================================================================
class KakaoPublicSource(ReviewSource):
    """
    ⚠️ 공개 Place 페이지 크롤러. 연구 목적 한정, ToS 경고 필수.
    본 MVP 에서는 스켈레톤만 제공. 운영 배포 시 공식 파트너 API 사용.
    """
    name = "kakao_public"

    USER_AGENT = "Mini-NLP-MVP/1.0 (research)"
    SLEEP_SEC = 1.5

    def __init__(self, rate_limit_sec: float = SLEEP_SEC):
        self.rate_limit_sec = rate_limit_sec

    def fetch(
        self,
        restaurant_id: int,
        max_count: int = 100,
    ) -> list[dict[str, Any]]:
        # 실제 구현은 Step 1 Day 5+ 옵션. 현재는 빈 리스트 반환.
        logger.warning(
            "KakaoPublicSource is a stub. Use SyntheticSource or AIHubSource."
        )
        time.sleep(self.rate_limit_sec)
        return []


# =============================================================================
# ReviewCrawler — 통합 fallback
# =============================================================================
class ReviewCrawler:
    """
    여러 ReviewSource 를 순차 시도하여 최초 성공 결과를 반환.
    """

    def __init__(self, sources: list[ReviewSource]):
        if not sources:
            raise ValueError("At least one ReviewSource required")
        self.sources = sources

    def fetch_reviews(
        self,
        restaurant_id: int,
        max_count: int = 100,
    ) -> list[dict[str, Any]]:
        for src in self.sources:
            try:
                results = src.fetch(restaurant_id, max_count)
                if results:
                    logger.info(
                        "[%s] restaurant %s: %d reviews fetched",
                        src.name, restaurant_id, len(results),
                    )
                    return results
            except Exception as e:
                logger.warning(
                    "[%s] failed: %s, trying next source", src.name, e
                )
        return []

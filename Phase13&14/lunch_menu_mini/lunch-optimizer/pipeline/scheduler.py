"""
음식점 데이터 파이프라인 오케스트레이터 + 스케줄러.

GUIDE Subtopic 1 §6 의 명세를 구현한다.

Usage:
    # 1회 실행
    python -m pipeline.scheduler --once

    # 스케줄러 모드 (매일 10:00)
    python -m pipeline.scheduler --schedule
"""
from __future__ import annotations

import logging
import signal
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Optional

from config.settings import settings
from database.connection import get_session, init_schema
from pipeline.collectors.air_quality_collector import AirQualityCollector
from pipeline.collectors.restaurant_collector import RestaurantCollector
from pipeline.collectors.vote_collector import VoteManager
from pipeline.collectors.weather_collector import WeatherCollector
from pipeline.loaders.db_loader import (
    NutritionLoader, RestaurantLoader, WeatherLoader
)
from pipeline.transformers.distance_scorer import RestaurantTransformer
from pipeline.transformers.weather_scorer import (
    WeatherDataIntegrator, WeatherMenuScorer
)

logger = logging.getLogger(__name__)


# =============================================================================
# 결과 데이터 클래스
# =============================================================================
@dataclass
class PipelineResult:
    success: bool
    duration_sec: float
    raw_count: int = 0
    transformed_count: int = 0
    inserted: int = 0
    updated: int = 0
    skipped: int = 0
    deactivated: int = 0
    error: Optional[str] = None
    collector_stats: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "duration_sec": round(self.duration_sec, 2),
            "raw_count": self.raw_count,
            "transformed_count": self.transformed_count,
            "inserted": self.inserted,
            "updated": self.updated,
            "skipped": self.skipped,
            "deactivated": self.deactivated,
            "error": self.error,
            "collector_stats": self.collector_stats,
        }


# =============================================================================
# 파이프라인
# =============================================================================
class RestaurantPipeline:
    """
    수집 → 변환 → 점수 → 적재 → 비활성화 의 전체 흐름.
    """

    def __init__(
        self,
        collector: Optional[RestaurantCollector] = None,
        ensure_schema: bool = True,
    ):
        if ensure_schema:
            init_schema()
        self.collector = collector or RestaurantCollector()

    def run_pipeline(self) -> PipelineResult:
        """
        한 번 실행. 에러 시 트랜잭션 롤백.
        """
        start = time.perf_counter()
        result = PipelineResult(success=False, duration_sec=0.0)

        try:
            # Step 1: 수집
            logger.info("=== Pipeline START ===")
            raw_docs = self.collector.collect_all()
            result.raw_count = len(raw_docs)
            result.collector_stats = self.collector.stats.to_dict()

            if not raw_docs:
                logger.warning("No documents collected, skipping transform/load")
                result.success = True
                result.duration_sec = time.perf_counter() - start
                return result

            # Step 2: 변환
            df = RestaurantTransformer.transform(raw_docs)
            df = RestaurantTransformer.enrich_with_scores(df)
            result.transformed_count = len(df)

            # Step 3+4: 적재 + 비활성화 (단일 세션)
            with get_session() as session:
                loader = RestaurantLoader(session)
                upsert_stats = loader.upsert_restaurants(df)
                result.inserted = upsert_stats["inserted"]
                result.updated = upsert_stats["updated"]
                result.skipped = upsert_stats["skipped"]

                active_ids = df["id"].astype(str).tolist()
                result.deactivated = loader.deactivate_missing(active_ids)

            result.success = True
        except Exception as e:
            result.error = str(e)
            logger.exception("Pipeline failed: %s", e)
        finally:
            result.duration_sec = time.perf_counter() - start
            logger.info("=== Pipeline END (%.2fs) — %s ===",
                        result.duration_sec, result.to_dict())

        return result

    # -------------------------------------------------------------------------
    # 스케줄러 모드
    # -------------------------------------------------------------------------
    def start_scheduler(
        self,
        hour: int = 10,
        minute: int = 0,
        run_immediately: bool = False,
    ) -> None:
        """
        APScheduler 로 매일 hour:minute 에 run_pipeline 실행.
        """
        try:
            from apscheduler.schedulers.blocking import BlockingScheduler
            from apscheduler.triggers.cron import CronTrigger
        except ImportError:
            logger.error(
                "apscheduler is not installed. Run: pip install apscheduler"
            )
            sys.exit(1)

        scheduler = BlockingScheduler(timezone="Asia/Seoul")
        trigger = CronTrigger(hour=hour, minute=minute)
        scheduler.add_job(
            self.run_pipeline,
            trigger=trigger,
            id="restaurant_pipeline",
            name="Daily restaurant collection",
            replace_existing=True,
        )

        # 그레이스풀 셧다운
        def _shutdown(*_args):
            logger.info("Shutdown signal received, stopping scheduler...")
            scheduler.shutdown(wait=False)
            sys.exit(0)

        signal.signal(signal.SIGINT, _shutdown)
        signal.signal(signal.SIGTERM, _shutdown)

        logger.info(
            "Scheduler started — daily at %02d:%02d (Asia/Seoul)", hour, minute
        )

        if run_immediately:
            logger.info("Running pipeline once before entering schedule loop")
            self.run_pipeline()

        scheduler.start()


# =============================================================================
# Weather Pipeline (Subtopic 2)
# =============================================================================
@dataclass
class WeatherResult:
    success: bool
    duration_sec: float
    weather: Optional[dict[str, Any]] = None
    log_id: Optional[int] = None
    error: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "duration_sec": round(self.duration_sec, 2),
            "weather": self.weather,
            "log_id": self.log_id,
            "error": self.error,
        }


class WeatherPipeline:
    """
    기상청 + 에어코리아 → 통합 dict → WeatherLog 저장.
    """

    def __init__(
        self,
        weather_collector: Optional[WeatherCollector] = None,
        air_collector: Optional[AirQualityCollector] = None,
        ensure_schema_flag: bool = True,
    ):
        if ensure_schema_flag:
            init_schema()
        self.weather_collector = weather_collector or WeatherCollector()
        self.air_collector = air_collector or AirQualityCollector()

    def run_pipeline(self) -> WeatherResult:
        start = time.perf_counter()
        result = WeatherResult(success=False, duration_sec=0.0)

        try:
            logger.info("=== Weather Pipeline START ===")
            weather_data = self.weather_collector.collect()
            air_data = self.air_collector.get_realtime_data()

            if weather_data is None and air_data is None:
                raise RuntimeError("Both weather and air APIs returned None")

            integrated = WeatherDataIntegrator.integrate(weather_data, air_data)
            result.weather = integrated

            with get_session() as session:
                loader = WeatherLoader(session)
                log = loader.save_weather_log(integrated)
                result.log_id = log.id

            result.success = True
        except Exception as e:
            result.error = str(e)
            logger.exception("WeatherPipeline failed: %s", e)
        finally:
            result.duration_sec = time.perf_counter() - start
            logger.info(
                "=== Weather Pipeline END (%.2fs) ===", result.duration_sec
            )
        return result

    def start_scheduler(self, hour: Optional[int] = None, minute: int = 0) -> None:
        """
        APScheduler: 매시 `minute` 분에 실행 (hour 미지정 시).
        hour 지정 시 해당 시각에만 1회.
        """
        try:
            from apscheduler.schedulers.blocking import BlockingScheduler
            from apscheduler.triggers.cron import CronTrigger
        except ImportError:
            logger.error("apscheduler not installed: pip install apscheduler")
            sys.exit(1)

        scheduler = BlockingScheduler(timezone="Asia/Seoul")
        if hour is not None:
            trigger = CronTrigger(hour=hour, minute=minute)
        else:
            trigger = CronTrigger(minute=minute)  # 매시

        scheduler.add_job(
            self.run_pipeline,
            trigger=trigger,
            id="weather_pipeline",
            name="Hourly weather collection",
            replace_existing=True,
        )

        def _shutdown(*_args):
            logger.info("Shutdown signal received, stopping weather scheduler")
            scheduler.shutdown(wait=False)
            sys.exit(0)

        signal.signal(signal.SIGINT, _shutdown)
        signal.signal(signal.SIGTERM, _shutdown)
        logger.info("Weather scheduler started")
        scheduler.start()


# =============================================================================
# LunchOptimizerPipeline (Subtopic 4 — 최종 오케스트레이터)
# =============================================================================
@dataclass
class LunchPipelineStatus:
    last_daily_run: Optional[str] = None
    last_hourly_run: Optional[str] = None
    last_vote_close_run: Optional[str] = None
    last_daily_result: Optional[dict] = None
    last_hourly_result: Optional[dict] = None
    last_vote_close_result: Optional[dict] = None


class LunchOptimizerPipeline:
    """
    Mini 전체 파이프라인 오케스트레이터.

    - daily (09:30)    : 음식점 + 날씨 + 투표 세션 자동 개시
    - hourly (:05)     : 날씨 갱신
    - vote_close (11:30): 투표 마감 + 결과 확정
    """

    def __init__(self, team_id: Optional[str] = None):
        self.team_id = team_id
        self.status = LunchPipelineStatus()

    # -------------------------------------------------------------------------
    def run_daily_pipeline(self) -> dict[str, Any]:
        """매일 오전 09:30 — 음식점·날씨·투표세션 초기화."""
        start = time.perf_counter()
        result: dict[str, Any] = {"steps": {}, "success": True}

        try:
            init_schema()

            # Step 1: 음식점 갱신
            step1_start = time.perf_counter()
            try:
                rest_result = RestaurantPipeline(ensure_schema=False).run_pipeline()
                result["steps"]["restaurant"] = {
                    **rest_result.to_dict(),
                    "elapsed_sec": round(time.perf_counter() - step1_start, 2),
                }
            except Exception as e:
                result["steps"]["restaurant"] = {"success": False, "error": str(e)}
                result["success"] = False
                logger.exception("daily: restaurant step failed: %s", e)

            # Step 2: 날씨
            step2_start = time.perf_counter()
            try:
                weather_result = WeatherPipeline(ensure_schema_flag=False).run_pipeline()
                result["steps"]["weather"] = {
                    **weather_result.to_dict(),
                    "elapsed_sec": round(time.perf_counter() - step2_start, 2),
                }
            except Exception as e:
                result["steps"]["weather"] = {"success": False, "error": str(e)}
                logger.exception("daily: weather step failed: %s", e)

            # Step 3: 영양 캐시 갱신은 옵션 (수동)
            result["steps"]["nutrition_cache"] = {"skipped": True, "reason": "manual"}

            # Step 4: 투표 세션 개시
            if self.team_id:
                step4_start = time.perf_counter()
                try:
                    with get_session() as session:
                        mgr = VoteManager(session)
                        s = mgr.open_session(self.team_id)
                        result["steps"]["vote_session"] = {
                            "success": True,
                            "session_id": s.id,
                            "elapsed_sec": round(time.perf_counter() - step4_start, 2),
                        }
                except Exception as e:
                    result["steps"]["vote_session"] = {"success": False, "error": str(e)}
                    logger.exception("daily: vote session step failed: %s", e)
            else:
                result["steps"]["vote_session"] = {"skipped": True, "reason": "team_id not provided"}

        finally:
            result["total_duration_sec"] = round(time.perf_counter() - start, 2)
            self.status.last_daily_run = datetime.utcnow().isoformat()
            self.status.last_daily_result = result
            logger.info("=== Daily Pipeline END (%.2fs) ===", result["total_duration_sec"])
        return result

    # -------------------------------------------------------------------------
    def run_hourly_pipeline(self) -> dict[str, Any]:
        """매시 정시 — 날씨 갱신."""
        start = time.perf_counter()
        result: dict[str, Any] = {"success": True}
        try:
            weather_result = WeatherPipeline(ensure_schema_flag=False).run_pipeline()
            result.update(weather_result.to_dict())
        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
            logger.exception("hourly failed: %s", e)
        finally:
            result["total_duration_sec"] = round(time.perf_counter() - start, 2)
            self.status.last_hourly_run = datetime.utcnow().isoformat()
            self.status.last_hourly_result = result
        return result

    # -------------------------------------------------------------------------
    def run_vote_close(self) -> dict[str, Any]:
        """매일 11:30 — 투표 마감."""
        if not self.team_id:
            return {"success": False, "reason": "team_id not provided"}

        start = time.perf_counter()
        result: dict[str, Any] = {"success": True}
        try:
            with get_session() as session:
                mgr = VoteManager(session)
                close_result = mgr.close_session(self.team_id)
                result.update(close_result)
        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
            logger.exception("vote_close failed: %s", e)
        finally:
            result["total_duration_sec"] = round(time.perf_counter() - start, 2)
            self.status.last_vote_close_run = datetime.utcnow().isoformat()
            self.status.last_vote_close_result = result
        return result

    # -------------------------------------------------------------------------
    def start_all_schedulers(self) -> None:
        """3개 스케줄을 BlockingScheduler 에 등록."""
        try:
            from apscheduler.schedulers.blocking import BlockingScheduler
            from apscheduler.triggers.cron import CronTrigger
        except ImportError:
            logger.error("apscheduler not installed")
            sys.exit(1)

        scheduler = BlockingScheduler(timezone="Asia/Seoul")
        scheduler.add_job(
            self.run_daily_pipeline,
            CronTrigger(hour=9, minute=30),
            id="daily", name="Daily (09:30)",
            replace_existing=True,
        )
        scheduler.add_job(
            self.run_hourly_pipeline,
            CronTrigger(minute=5),
            id="hourly", name="Hourly weather",
            replace_existing=True,
        )
        scheduler.add_job(
            self.run_vote_close,
            CronTrigger(hour=11, minute=30),
            id="vote_close", name="Vote close (11:30)",
            replace_existing=True,
        )

        def _shutdown(*_args):
            logger.info("Shutdown signal, stopping schedulers")
            scheduler.shutdown(wait=False)
            sys.exit(0)

        signal.signal(signal.SIGINT, _shutdown)
        signal.signal(signal.SIGTERM, _shutdown)

        logger.info("All schedulers started (daily/hourly/vote_close)")
        scheduler.start()

    # -------------------------------------------------------------------------
    def get_pipeline_status(self) -> dict[str, Any]:
        return {
            "last_daily_run": self.status.last_daily_run,
            "last_hourly_run": self.status.last_hourly_run,
            "last_vote_close_run": self.status.last_vote_close_run,
            "last_daily_result": self.status.last_daily_result,
            "last_hourly_result": self.status.last_hourly_result,
            "last_vote_close_result": self.status.last_vote_close_result,
        }


# =============================================================================
# CLI
# =============================================================================
def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Mini Pipelines")
    parser.add_argument(
        "--target",
        choices=["restaurant", "weather", "daily", "hourly", "vote-close", "all"],
        default="restaurant",
        help="실행할 파이프라인",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--once", action="store_true", help="1회 실행 후 종료")
    mode.add_argument("--schedule", action="store_true", help="스케줄러 모드")
    parser.add_argument("--team-id", type=str, default=None)
    parser.add_argument("--hour", type=int, default=10)
    parser.add_argument("--minute", type=int, default=0)
    parser.add_argument("--run-now", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=settings.logging.level,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    if args.once:
        if args.target == "restaurant":
            print("Restaurant:", RestaurantPipeline().run_pipeline().to_dict())
        elif args.target == "weather":
            print("Weather:", WeatherPipeline().run_pipeline().to_dict())
        elif args.target == "daily":
            print("Daily:", LunchOptimizerPipeline(team_id=args.team_id).run_daily_pipeline())
        elif args.target == "hourly":
            print("Hourly:", LunchOptimizerPipeline().run_hourly_pipeline())
        elif args.target == "vote-close":
            print("Vote close:", LunchOptimizerPipeline(team_id=args.team_id).run_vote_close())
        elif args.target == "all":
            print("Restaurant:", RestaurantPipeline().run_pipeline().to_dict())
            print("Weather:", WeatherPipeline().run_pipeline().to_dict())
        sys.exit(0)
    else:
        if args.target in ("daily", "all"):
            LunchOptimizerPipeline(team_id=args.team_id).start_all_schedulers()
        elif args.target == "weather":
            WeatherPipeline().start_scheduler(minute=args.minute)
        else:
            RestaurantPipeline().start_scheduler(
                hour=args.hour, minute=args.minute, run_immediately=args.run_now
            )


if __name__ == "__main__":
    main()

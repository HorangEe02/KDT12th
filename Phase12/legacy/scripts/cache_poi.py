"""10개 구장 × 3 카테고리 = 30개 POI JSON을 TourAPI로 일괄 캐싱.

TOUR_API_KEY 미설정 시 graceful skip → 더미 데이터 유지.
요청 사이 0.5s sleep, --force 플래그로 기존 캐시 덮어쓰기.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src import config
from src.api.tour_api import get_nearby_places

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)


def cache_one(stadium: dict, category: str, force: bool) -> int:
    out = config.POI_CACHE_DIR / f"{stadium['short_name']}_{category}.json"
    if out.exists() and not force:
        log.info("[skip] %s (이미 존재, --force로 재수집)", out.name)
        try:
            return len(json.loads(out.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            return 0

    ctid = config.CONTENT_TYPE[category]
    places = get_nearby_places(
        lat=float(stadium["lat"]),
        lng=float(stadium["lng"]),
        radius=3000,
        content_type=ctid,
        num_rows=30,
    )
    for p in places:
        p["stadium"] = stadium["short_name"]

    if not places:
        log.warning("[%s/%s] 결과 없음 — 기존 더미 유지", stadium["short_name"], category)
        return 0

    out.write_text(json.dumps(places, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("[%s/%s] %d개 저장", stadium["short_name"], category, len(places))
    return len(places)


def main(force: bool) -> int:
    if not config.TOUR_API_KEY:
        log.warning("TOUR_API_KEY 없음 → 더미 데이터 유지. Phase 1 더미만으로 진행 가능.")
        return 0

    stadiums = pd.read_csv(config.STADIUMS_CSV, encoding="utf-8-sig")
    config.POI_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    total = 0
    files = 0
    for _, row in stadiums.iterrows():
        stadium = row.to_dict()
        for category in config.CONTENT_TYPE.keys():
            cnt = cache_one(stadium, category, force)
            total += cnt
            if cnt > 0:
                files += 1
            time.sleep(0.5)

    print(f"\n=== POI 캐싱 요약 ===\n신규/갱신 파일: {files}\n총 POI: {total}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="기존 캐시 무시하고 재수집")
    args = parser.parse_args()
    sys.exit(main(args.force))

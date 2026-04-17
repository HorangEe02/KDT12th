"""Phase 6 — Python 자산을 Next.js용 JSON으로 변환.

- data/*.csv → frontend/public/data/*.json
- data/poi_cache/*.json → frontend/public/data/poi/*.json (그대로 복사)
- data/knowledge/away_game_tips.json → frontend/public/data/tips.json
- models/win_rate_model.pkl → frontend/public/data/model.json (계수·scaler만)
"""
from __future__ import annotations

import json
import logging
import pickle
import shutil
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src import config

FRONTEND_PUBLIC = PROJECT_ROOT / "frontend" / "public" / "data"

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)


def ensure_dir() -> None:
    FRONTEND_PUBLIC.mkdir(parents=True, exist_ok=True)
    (FRONTEND_PUBLIC / "poi").mkdir(parents=True, exist_ok=True)


def export_schedule() -> None:
    df = pd.read_csv(config.SCHEDULE_CSV, encoding="utf-8-sig", parse_dates=["date"])
    rows = []
    for _, row in df.iterrows():
        rows.append({
            "game_id": str(row["game_id"]),
            "date": row["date"].strftime("%Y-%m-%d"),
            "day_of_week": str(row["day_of_week"]),
            "home_team": str(row["home_team"]),
            "away_team": str(row["away_team"]),
            "stadium": str(row["stadium"]),
            "start_time": str(row["start_time"]),
            "broadcast": str(row.get("broadcast") or ""),
        })
    out = FRONTEND_PUBLIC / "schedule.json"
    out.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    log.info("✅ schedule.json (%d games)", len(rows))


def export_stadiums() -> None:
    df = pd.read_csv(config.STADIUMS_CSV, encoding="utf-8-sig")
    rows = []
    for _, row in df.iterrows():
        rows.append({
            "stadium_name": str(row["stadium_name"]),
            "short_name": str(row["short_name"]),
            "home_team": str(row["home_team"]),
            "city": str(row["city"]),
            "address": str(row.get("address") or ""),
            "lat": float(row["lat"]),
            "lng": float(row["lng"]),
            "capacity": int(row["capacity"]),
            "subway_station": str(row.get("subway_station") or ""),
        })
    out = FRONTEND_PUBLIC / "stadiums.json"
    out.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    log.info("✅ stadiums.json (%d rows)", len(rows))


def export_team_stats() -> None:
    df = pd.read_csv(config.TEAM_STATS_CSV, encoding="utf-8-sig")
    rows = df.to_dict(orient="records")
    # numpy 타입 → python native 변환
    clean = []
    for r in rows:
        clean.append({
            "year": int(r["year"]),
            "team": str(r["team"]),
            "games_played": int(r["games_played"]),
            "wins": int(r["wins"]),
            "losses": int(r["losses"]),
            "draws": int(r["draws"]),
            "win_rate": float(r["win_rate"]),
            "home_win_rate": float(r["home_win_rate"]),
            "away_win_rate": float(r["away_win_rate"]),
            "final_rank": int(r["final_rank"]),
        })
    out = FRONTEND_PUBLIC / "team-stats.json"
    out.write_text(json.dumps(clean, ensure_ascii=False), encoding="utf-8")
    log.info("✅ team-stats.json (%d rows)", len(clean))


def export_poi_cache() -> None:
    src = config.POI_CACHE_DIR
    dst = FRONTEND_PUBLIC / "poi"
    count = 0
    for p in src.glob("*.json"):
        shutil.copy(p, dst / p.name)
        count += 1
    log.info("✅ poi/*.json (%d files)", count)


def export_tips() -> None:
    src = config.KNOWLEDGE_DIR / "away_game_tips.json"
    if not src.exists():
        log.warning("tips 파일 없음: %s", src)
        return
    dst = FRONTEND_PUBLIC / "tips.json"
    shutil.copy(src, dst)
    tips = json.loads(dst.read_text(encoding="utf-8"))
    log.info("✅ tips.json (%d tips)", len(tips))


def export_model() -> None:
    """scikit-learn Pipeline에서 계수·scaler만 JSON으로 추출."""
    if not config.WIN_RATE_MODEL_PATH.exists():
        log.warning("모델 파일 없음: %s", config.WIN_RATE_MODEL_PATH)
        return
    with open(config.WIN_RATE_MODEL_PATH, "rb") as f:
        bundle = pickle.load(f)
    pipeline = bundle["pipeline"]
    scaler = pipeline.named_steps["scaler"]
    clf = pipeline.named_steps["clf"]
    out = {
        "feature_names": bundle.get("feature_names", []),
        "scaler": {
            "mean": scaler.mean_.tolist(),
            "scale": scaler.scale_.tolist(),
        },
        "logreg": {
            "coef": clf.coef_[0].tolist(),
            "intercept": float(clf.intercept_[0]),
            "classes": clf.classes_.tolist(),
        },
    }
    path = FRONTEND_PUBLIC / "model.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info(
        "✅ model.json (features: %d, coefs: %d)",
        len(out["feature_names"]),
        len(out["logreg"]["coef"]),
    )


def export_team_colors() -> None:
    """Phase 2 TEAM_COLORS를 별도 JSON으로."""
    from src.ui.components.hero import TEAM_COLORS
    out = FRONTEND_PUBLIC / "team-colors.json"
    out.write_text(json.dumps(TEAM_COLORS, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("✅ team-colors.json (%d teams)", len(TEAM_COLORS))


def export_kbo_logos() -> None:
    """KBO SVG 로고를 public/logos/로 복사."""
    src_dir = PROJECT_ROOT / "uiux" / "KBO_logo"
    dst_dir = PROJECT_ROOT / "frontend" / "public" / "logos"
    if not src_dir.exists():
        log.warning("KBO 로고 디렉토리 없음")
        return
    dst_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for p in src_dir.glob("*.svg"):
        shutil.copy(p, dst_dir / p.name)
        count += 1
    log.info("✅ logos/*.svg (%d files)", count)


def main() -> None:
    ensure_dir()
    export_schedule()
    export_stadiums()
    export_team_stats()
    export_poi_cache()
    export_tips()
    export_model()
    export_team_colors()
    export_kbo_logos()
    print("\n=== 변환 완료 ===")
    print(f"대상 디렉토리: {FRONTEND_PUBLIC}")


if __name__ == "__main__":
    main()

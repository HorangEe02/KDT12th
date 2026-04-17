"""Phase 1 완료 게이트 — 모든 데이터 산출물 품질 검증.

exit(0): 모든 검증 통과 → Phase 2 진입 가능
exit(1): 하나라도 실패 → 실패 항목을 수정한 뒤 재실행
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src import config


class Report:
    def __init__(self) -> None:
        self.results: list[tuple[str, bool, str]] = []

    def add(self, name: str, ok: bool, detail: str = "") -> None:
        self.results.append((name, ok, detail))

    def summary(self) -> tuple[int, int]:
        passed = sum(1 for _, ok, _ in self.results if ok)
        return passed, len(self.results)

    def print_all(self, verbose: bool) -> None:
        print("=" * 54)
        print("Phase 1 Data Validation Report")
        print("=" * 54)
        for name, ok, detail in self.results:
            tag = "[PASS]" if ok else "[FAIL]"
            line = f"{tag} {name}"
            if detail and (verbose or not ok):
                line += f" — {detail}"
            print(line)
        passed, total = self.summary()
        print()
        print(f"총 검증: {total}개")
        print(f"통과  : {passed}개")
        print(f"실패  : {total - passed}개")
        print()
        if passed == total:
            print("✅ Phase 1 완료. Phase 2 진입 가능.")
        else:
            print("❌ Phase 1 미완료. 위 실패 항목 해결 후 재실행.")


def check_files(r: Report) -> None:
    must = [
        config.SCHEDULE_CSV,
        config.STADIUMS_CSV,
        config.TEAM_STATS_CSV,
        PROJECT_ROOT / "data" / "SCHEMA.md",
        PROJECT_ROOT / "src" / "api" / "tour_api.py",
        PROJECT_ROOT / "src" / "api" / "weather_api.py",
        PROJECT_ROOT / "src" / "data_loader.py",
    ]
    missing = [str(p.relative_to(PROJECT_ROOT)) for p in must if not p.exists()]
    poi_files = sorted(config.POI_CACHE_DIR.glob("*.json"))
    total = len(must) + len(poi_files)
    ok = not missing and len(poi_files) == 30
    detail = (
        f"필수 {len(must)}개 + POI {len(poi_files)}개 = {total}"
        if ok
        else f"누락: {missing or '없음'}, POI {len(poi_files)}/30"
    )
    r.add("파일 존재", ok, detail)


def check_schedule(r: Report) -> None:
    try:
        df = pd.read_csv(config.SCHEDULE_CSV, parse_dates=["date"], encoding="utf-8-sig")
    except Exception as exc:
        r.add("KBO 일정", False, f"로드 실패: {exc}")
        return
    checks = []
    checks.append(("행 수 ≥ 600", len(df) >= 600))
    checks.append(("시즌 시작 == 2026-03-28", df["date"].min().strftime("%Y-%m-%d") == config.SEASON_START))
    checks.append(("시즌 종료 ≤ 2026-09-30", df["date"].max().strftime("%Y-%m-%d") <= config.SEASON_END))
    checks.append(("home_team 표준", set(df["home_team"]).issubset(config.TEAMS)))
    checks.append(("away_team 표준", set(df["away_team"]).issubset(config.TEAMS)))
    checks.append(("game_id 중복 없음", df["game_id"].is_unique))
    ok = all(v for _, v in checks)
    detail = f"{len(df)} games, " + ", ".join(f"{n}={'O' if v else 'X'}" for n, v in checks)
    r.add("KBO 일정", ok, detail)


def check_stadiums(r: Report) -> None:
    try:
        df = pd.read_csv(config.STADIUMS_CSV, encoding="utf-8-sig")
    except Exception as exc:
        r.add("구장 정보", False, f"로드 실패: {exc}")
        return
    checks = [
        ("행 수 == 10", len(df) == 10),
        ("lat ∈ [33,38]", df["lat"].between(33, 38).all()),
        ("lng ∈ [124,132]", df["lng"].between(124, 132).all()),
        ("short_name 유니크", df["short_name"].is_unique),
        ("address 결측 없음", df["address"].notna().all()),
    ]
    ok = all(v for _, v in checks)
    detail = ", ".join(f"{n}={'O' if v else 'X'}" for n, v in checks)
    r.add("구장 정보", ok, detail)


def check_team_stats(r: Report) -> None:
    try:
        df = pd.read_csv(config.TEAM_STATS_CSV, encoding="utf-8-sig")
    except Exception as exc:
        r.add("팀 전적", False, f"로드 실패: {exc}")
        return
    dup = df.duplicated(subset=["year", "team"]).sum()
    wr_ok = df["win_rate"].between(0.30, 0.70).all()
    rank_ok = True
    for yr, grp in df.groupby("year"):
        if sorted(grp["final_rank"].tolist()) != list(range(1, 11)):
            rank_ok = False
            break
    checks = [
        ("행 수 == 110", len(df) == 110),
        ("year×team 중복 없음", dup == 0),
        ("win_rate ∈ [0.3,0.7]", wr_ok),
        ("연도별 rank 1~10", rank_ok),
    ]
    ok = all(v for _, v in checks)
    detail = ", ".join(f"{n}={'O' if v else 'X'}" for n, v in checks)
    r.add("팀 전적", ok, detail)


def check_poi(r: Report) -> None:
    poi_files = sorted(config.POI_CACHE_DIR.glob("*.json"))
    if not poi_files:
        r.add("POI 캐시", False, "POI 파일 없음")
        return
    total = 0
    short_files = []
    bad = []
    for p in poi_files:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            bad.append(f"{p.name}: {exc}")
            continue
        if not isinstance(data, list):
            bad.append(f"{p.name}: 리스트가 아님")
            continue
        if len(data) < 5:
            short_files.append(f"{p.name}({len(data)})")
        for rec in data:
            missing = [k for k in ("content_id", "title", "lat", "lng") if k not in rec]
            if missing:
                bad.append(f"{p.name}: 필드 누락 {missing}")
                break
        total += len(data)
    ok = len(poi_files) == 30 and not bad and not short_files
    detail = f"{len(poi_files)}개 파일, 총 {total}개 POI"
    if bad:
        detail += f", 오류={bad[:3]}"
    if short_files:
        detail += f", 5건 미만={short_files[:3]}"
    r.add("POI 캐시", ok, detail)


def check_fk(r: Report) -> None:
    try:
        sched = pd.read_csv(config.SCHEDULE_CSV, encoding="utf-8-sig")
        stad = pd.read_csv(config.STADIUMS_CSV, encoding="utf-8-sig")
    except Exception as exc:
        r.add("외래키 무결성", False, f"로드 실패: {exc}")
        return
    sched_set = set(sched["stadium"].astype(str).str.strip())
    stad_set = set(stad["short_name"].astype(str).str.strip())
    orphans = sched_set - stad_set
    ok = not orphans
    detail = "schedule.stadium ⊆ stadiums.short_name" if ok else f"고아 stadium: {orphans}"
    r.add("외래키 무결성", ok, detail)


def main(verbose: bool) -> int:
    r = Report()
    check_files(r)
    check_schedule(r)
    check_stadiums(r)
    check_team_stats(r)
    check_poi(r)
    check_fk(r)
    r.print_all(verbose)
    passed, total = r.summary()
    return 0 if passed == total else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    sys.exit(main(args.verbose))

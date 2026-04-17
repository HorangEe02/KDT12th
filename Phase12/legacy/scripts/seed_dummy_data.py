"""Phase 1 — 더미 데이터 생성기.

scripts/seed_dummy_data.py 실행 시:
  - data/kbo_schedule_2026.csv  (약 720경기)
  - data/stadiums.csv           (10행)
  - data/team_stats_10yr.csv    (110행)
  - data/poi_cache/*.json       (30개)
를 생성한다. random.seed(42)로 재현 가능.
"""
from __future__ import annotations

import json
import logging
import random
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src import config

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

STADIUM_ROWS = [
    # (stadium_name, short_name, home_team, city, address, lat, lng, capacity, subway_station)
    ("잠실야구장", "잠실", "LG,두산", "서울", "서울특별시 송파구 올림픽로 25",
     37.5122, 127.0719, 25000, "잠실종합운동장(2,9호선)"),
    ("고척스카이돔", "고척", "키움", "서울", "서울특별시 구로구 경인로 430",
     37.4982, 126.8670, 16744, "구일(1호선)"),
    ("인천SSG랜더스필드", "문학", "SSG", "인천", "인천광역시 미추홀구 매소홀로 618",
     37.4371, 126.6932, 23000, "문학경기장(인천1호선)"),
    ("수원KT위즈파크", "수원", "KT", "수원", "경기도 수원시 장안구 경수대로 893",
     37.2997, 127.0097, 20000, "없음 (버스 환승)"),
    ("한화생명볼파크", "대전", "한화", "대전", "대전광역시 중구 대종로 373",
     36.3171, 127.4293, 20000, "중앙로(1호선)"),
    ("대구삼성라이온즈파크", "대구", "삼성", "대구", "대구광역시 수성구 야구전설로 1",
     35.8411, 128.6816, 24000, "아양교(1호선)"),
    ("광주KIA챔피언스필드", "광주", "KIA", "광주", "광주광역시 북구 서림로 10",
     35.1683, 126.8889, 20500, "없음 (버스)"),
    ("창원NC파크", "창원", "NC", "창원", "경상남도 창원시 마산회원구 삼호로 63",
     35.2222, 128.5820, 22112, "없음 (버스)"),
    ("사직야구장", "사직", "롯데", "부산", "부산광역시 동래구 사직로 45",
     35.1940, 129.0611, 22990, "사직(3호선)"),
    ("한밭야구장", "한밭", "한화(보조)", "대전", "대전광역시 중구 대종로 373",
     36.3262, 127.4171, 9000, "중앙로(1호선)"),
]

FINAL_RANK_2025 = {
    "KT": 1, "한화": 2, "KIA": 3, "삼성": 4, "NC": 5,
    "LG": 6, "두산": 7, "SSG": 8, "롯데": 9, "키움": 10,
}


def seed_stadiums() -> pd.DataFrame:
    df = pd.DataFrame(
        STADIUM_ROWS,
        columns=[
            "stadium_name", "short_name", "home_team", "city", "address",
            "lat", "lng", "capacity", "subway_station",
        ],
    )
    df.to_csv(config.STADIUMS_CSV, index=False, encoding="utf-8-sig")
    log.info("✅ %d stadiums → %s", len(df), config.STADIUMS_CSV.name)
    return df


def seed_schedule(rng: random.Random) -> pd.DataFrame:
    """144경기 × 10팀 규칙 기반 생성 (월요일·올스타 브레이크 제외)."""
    start, end = date(2026, 3, 28), date(2026, 9, 30)
    break_start, break_end = date(2026, 7, 10), date(2026, 7, 15)
    weekday_kr = ["월", "화", "수", "목", "금", "토", "일"]

    teams = config.TEAMS
    matchups: list[tuple[str, str]] = []
    for i, home in enumerate(teams):
        for away in teams:
            if home == away:
                continue
            matchups.extend([(home, away)] * 8)
    rng.shuffle(matchups)

    game_days: list[date] = []
    d = start
    while d <= end:
        if d.weekday() != 0 and not (break_start <= d <= break_end):
            game_days.append(d)
        d += timedelta(days=1)

    total = len(matchups)
    per_day = max(1, total // len(game_days))

    rows = []
    queue = matchups.copy()
    day_idx = 0
    while queue and day_idx < len(game_days):
        d = game_days[day_idx]
        used_teams_today: set[str] = set()
        slots = per_day + (1 if day_idx < total % len(game_days) else 0)
        slots = min(slots, 5)
        taken = 0
        skipped: list[tuple[str, str]] = []
        while queue and taken < slots:
            home, away = queue.pop(0)
            if home in used_teams_today or away in used_teams_today:
                skipped.append((home, away))
                continue
            used_teams_today.update([home, away])

            if d.weekday() in (5, 6):
                start_time = rng.choice(["14:00", "17:00", "18:00"])
            else:
                start_time = "18:30"

            rows.append({
                "game_id": f"{d.strftime('%Y%m%d')}_{away}_{home}",
                "date": d.isoformat(),
                "day_of_week": weekday_kr[d.weekday()],
                "home_team": home,
                "away_team": away,
                "stadium": config.HOME_STADIUM[home],
                "start_time": start_time,
                "broadcast": rng.choice(["KBS", "SBS", "MBC", "TVING", ""]),
            })
            taken += 1
        queue = skipped + queue
        day_idx += 1

    df = pd.DataFrame(rows).drop_duplicates(subset="game_id").reset_index(drop=True)
    df.to_csv(config.SCHEDULE_CSV, index=False, encoding="utf-8-sig")
    log.info("✅ %d games → %s", len(df), config.SCHEDULE_CSV.name)
    return df


def seed_team_stats(rng: random.Random) -> pd.DataFrame:
    rows = []
    for year in range(2015, 2026):
        year_rng = random.Random(year * 31 + 7)
        wr_by_team = {}
        for team in config.TEAMS:
            base = 0.45 + (ord(team[0]) % 7) * 0.015
            wr = max(0.35, min(0.65, base + year_rng.uniform(-0.08, 0.12)))
            wr_by_team[team] = wr

        if year == 2025:
            ranked = sorted(FINAL_RANK_2025.items(), key=lambda x: x[1])
            for rank, (team, _) in enumerate(ranked, start=1):
                wr_by_team[team] = 0.62 - (rank - 1) * 0.03
            ranking = {team: rnk for team, rnk in FINAL_RANK_2025.items()}
        else:
            sorted_teams = sorted(wr_by_team.items(), key=lambda x: -x[1])
            ranking = {team: i + 1 for i, (team, _) in enumerate(sorted_teams)}

        for team in config.TEAMS:
            wr = wr_by_team[team]
            games = 144
            wins = round(games * wr)
            draws = year_rng.randint(0, 6)
            losses = games - wins - draws
            home_wr = min(0.70, wr + year_rng.uniform(0.02, 0.08))
            away_wr = max(0.30, wr - year_rng.uniform(0.02, 0.08))
            rows.append({
                "year": year,
                "team": team,
                "games_played": games,
                "wins": wins,
                "losses": losses,
                "draws": draws,
                "win_rate": round(wr, 3),
                "home_win_rate": round(home_wr, 3),
                "away_win_rate": round(away_wr, 3),
                "final_rank": ranking[team],
            })

    df = pd.DataFrame(rows)
    df.to_csv(config.TEAM_STATS_CSV, index=False, encoding="utf-8-sig")
    log.info("✅ %d team stats → %s", len(df), config.TEAM_STATS_CSV.name)
    return df


FOOD_NAMES = [
    "맛있는집", "할머니국밥", "원조갈비", "중앙시장식당", "형제식당",
    "전통한식당", "스타벅스", "이디야커피", "김밥천국", "맥도날드",
    "이모네돈까스", "삼거리포차", "24시감자탕", "바다횟집", "산들애",
    "명동교자", "본죽", "도쿄등심", "홍콩반점", "교촌치킨",
    "BBQ치킨", "네네치킨", "굽네치킨", "설빙", "파스쿠찌",
    "투썸플레이스", "공차", "떡볶이천국", "한솥도시락", "원할머니보쌈",
]
STAY_NAMES = [
    "그랜드호텔", "프레지던트호텔", "비즈니스인", "모텔로얄", "호텔스카이",
    "더스테이", "하이원리조트", "어반스테이", "메종호텔", "에이스모텔",
    "골든파크호텔", "플라자호텔", "레지던스스테이", "호텔캐슬", "벨라지오",
    "호텔뉴브", "시티호텔", "레이크뷰호텔", "코지하우스", "스테이홈",
    "센트럴호텔", "호텔리베라", "모텔위드", "노보텔", "호텔오크우드",
]
TOUR_NAMES = [
    "중앙공원", "시립박물관", "전망대", "전통시장", "강변산책로",
    "야경명소", "역사유적지", "미술관", "과학관", "문화의거리",
    "조각공원", "호반공원", "야구명예의전당", "향토음식거리", "어린이대공원",
    "대형쇼핑몰", "케이블카", "둘레길", "역사박물관", "전통찻집거리",
    "유람선선착장", "드라이브코스", "명품야시장", "전시관", "한옥마을",
]


def _gen_pois(stadium: dict, category: str, names: list[str], rng: random.Random) -> list[dict]:
    n = rng.randint(22, 30)
    samples = rng.sample(names, min(n, len(names)))
    base_lat, base_lng = stadium["lat"], stadium["lng"]
    pois = []
    for i, name in enumerate(samples):
        jitter_lat = rng.uniform(-0.018, 0.018)
        jitter_lng = rng.uniform(-0.018, 0.018)
        lat = round(base_lat + jitter_lat, 6)
        lng = round(base_lng + jitter_lng, 6)
        dist_m = int(((jitter_lat * 111000) ** 2 + (jitter_lng * 88000) ** 2) ** 0.5)
        pois.append({
            "content_id": f"DUMMY_{stadium['short_name']}_{category}_{i:03d}",
            "title": f"{stadium['short_name']} {name}",
            "category": category,
            "addr": f"{stadium['city']} 근처 {name}",
            "lat": lat,
            "lng": lng,
            "tel": f"0{rng.randint(2, 9)}-{rng.randint(100, 999)}-{rng.randint(1000, 9999)}",
            "first_image": "",
            "dist_m": dist_m,
            "stadium": stadium["short_name"],
        })
    return pois


def seed_poi_cache(stadiums: pd.DataFrame, rng: random.Random) -> int:
    config.POI_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    name_map = {"food": FOOD_NAMES, "stay": STAY_NAMES, "tour": TOUR_NAMES}
    count = 0
    for _, row in stadiums.iterrows():
        stadium = row.to_dict()
        for category, names in name_map.items():
            pois = _gen_pois(stadium, category, names, rng)
            out = config.POI_CACHE_DIR / f"{stadium['short_name']}_{category}.json"
            out.write_text(json.dumps(pois, ensure_ascii=False, indent=2), encoding="utf-8")
            count += 1
    log.info("✅ %d POI cache files → %s", count, config.POI_CACHE_DIR.name)
    return count


def main() -> None:
    rng = random.Random(42)
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)

    stadiums = seed_stadiums()
    schedule = seed_schedule(rng)
    team_stats = seed_team_stats(rng)
    poi_count = seed_poi_cache(stadiums, rng)

    print("\n=== 더미 데이터 생성 요약 ===")
    print(f"경기 일정   : {len(schedule):>4d} 행")
    print(f"구장        : {len(stadiums):>4d} 행")
    print(f"팀 전적     : {len(team_stats):>4d} 행")
    print(f"POI 캐시    : {poi_count:>4d} 파일")


if __name__ == "__main__":
    main()

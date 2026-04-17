"""Phase 3 완료 게이트 — 지도·차트·경로 모듈 정적/런타임 검증."""
from __future__ import annotations

import argparse
import ast
import importlib.util
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class Report:
    def __init__(self) -> None:
        self.results: list[tuple[str, bool, str]] = []

    def add(self, name: str, ok: bool, detail: str = "") -> None:
        self.results.append((name, ok, detail))

    def summary(self) -> tuple[int, int]:
        passed = sum(1 for _, ok, _ in self.results if ok)
        return passed, len(self.results)

    def print_all(self, verbose: bool) -> None:
        print("=" * 60)
        print("Phase 3 Map & Visualization Validation Report")
        print("=" * 60)
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
        print(f"실패  : {total - passed}개\n")
        if passed == total:
            print("✅ Phase 3 완료. Phase 4 진입 가능.")
        else:
            print("❌ Phase 3 미완료. 실패 항목 해결 후 재실행.")


REQUIRED_FILES = [
    "src/viz/folium_map.py",
    "src/viz/plotly_charts.py",
    "src/viz/popup_builder.py",
    "src/api/kakao_map.py",
    "src/ui/components/place_card.py",
    "src/ui/tabs/tab1_games.py",
    "src/ui/tabs/tab2_map.py",
    "src/ui/tabs/tab3_places.py",
    "docs/VIZ_CONTRACT.md",
    "data/route_cache",
]

FUNCTION_CONTRACTS = {
    "src/viz/folium_map.py": ["create_map", "render_map_in_streamlit"],
    "src/viz/plotly_charts.py": ["bar_away_win_rate", "scatter_places", "gauge_win_rate"],
    "src/viz/popup_builder.py": ["stadium_popup_html", "place_popup_html"],
    "src/api/kakao_map.py": ["get_car_route"],
    "src/ui/components/place_card.py": ["render_place_card"],
}


def _parse(path: Path) -> ast.AST | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return None


def check_files(r: Report) -> None:
    missing = [p for p in REQUIRED_FILES if not (PROJECT_ROOT / p).exists()]
    ok = not missing
    detail = f"{len(REQUIRED_FILES) - len(missing)}/{len(REQUIRED_FILES)} 존재"
    if missing:
        detail += f", 누락: {missing}"
    r.add("필수 파일/디렉토리 존재", ok, detail)


def check_function_contracts(r: Report) -> None:
    bad: list[str] = []
    for rel, fns in FUNCTION_CONTRACTS.items():
        tree = _parse(PROJECT_ROOT / rel)
        if tree is None:
            bad.append(f"{rel}:syntax")
            continue
        defined = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
        missing = [f for f in fns if f not in defined]
        if missing:
            bad.append(f"{rel}:{missing}")
    ok = not bad
    total = sum(len(v) for v in FUNCTION_CONTRACTS.values())
    detail = f"{total - len(bad)}/{total} 계약 함수 정의"
    if bad:
        detail += f", 이슈: {bad}"
    r.add("공개 함수 시그니처 계약", ok, detail)


def check_dependencies(r: Report) -> None:
    required = ["folium", "streamlit_folium", "plotly", "httpx", "pandas"]
    missing = [mod for mod in required if importlib.util.find_spec(mod) is None]
    ok = not missing
    detail = f"{len(required) - len(missing)}/{len(required)} 설치됨"
    if missing:
        detail += f", 누락: {missing}"
    r.add("의존성 (folium/streamlit-folium/plotly/httpx/pandas)", ok, detail)


def check_create_map_runtime(r: Report) -> None:
    try:
        from src.viz.folium_map import create_map
        m = create_map(
            center=(37.5122, 127.0719),
            zoom=14,
            stadium={
                "stadium_name": "잠실야구장", "short_name": "잠실",
                "home_team": "LG,두산", "address": "서울특별시 송파구 올림픽로 25",
                "subway_station": "잠실종합운동장(2,9호선)", "capacity": 25000,
                "lat": 37.5122, "lng": 127.0719,
            },
            places={"food": [], "stay": [], "tour": []},
            route=[(37.5547, 126.9707), (37.5122, 127.0719)],
            weather={"sky": "맑음", "precipitation_prob": 10, "temp_min": 8, "temp_max": 18, "rain_expected": False},
        )
        html = m._repr_html_()
        ok = "folium" in html.lower() or "leaflet" in html.lower()
        detail = f"HTML 길이 {len(html)}, folium/leaflet 토큰 {'O' if ok else 'X'}"
    except Exception as exc:
        ok = False
        detail = f"런타임 예외: {type(exc).__name__}: {exc}"
    r.add("create_map 런타임 smoke test", ok, detail)


def check_plotly_runtime(r: Report) -> None:
    try:
        import pandas as pd
        from src.viz.plotly_charts import bar_away_win_rate, scatter_places, gauge_win_rate

        df = pd.DataFrame([
            {"year": 2025, "team": "LG", "away_win_rate": 0.55,
             "win_rate": 0.58, "home_win_rate": 0.61, "games_played": 144,
             "wins": 80, "losses": 60, "draws": 4, "final_rank": 1},
            {"year": 2025, "team": "KT", "away_win_rate": 0.61,
             "win_rate": 0.62, "home_win_rate": 0.63, "games_played": 144,
             "wins": 85, "losses": 55, "draws": 4, "final_rank": 2},
            {"year": 2024, "team": "LG", "away_win_rate": 0.52,
             "win_rate": 0.55, "home_win_rate": 0.58, "games_played": 144,
             "wins": 78, "losses": 62, "draws": 4, "final_rank": 3},
        ])
        f1 = bar_away_win_rate(df, "LG")
        f2 = scatter_places([], (37.5, 127.0))
        f3 = gauge_win_rate(0.62, "LG")
        bar_ok = len(f1.data) >= 1
        scatter_ok = f2 is not None  # 빈 입력에도 Figure 반환
        gauge_ok = len(f3.data) >= 1
        ok = bar_ok and scatter_ok and gauge_ok
        detail = f"bar={bar_ok} scatter={scatter_ok} gauge={gauge_ok}"
    except Exception as exc:
        ok = False
        detail = f"런타임 예외: {type(exc).__name__}: {exc}"
    r.add("Plotly 차트 3종 런타임 smoke test", ok, detail)


def check_route_fallback(r: Report) -> None:
    try:
        from src.api.kakao_map import get_car_route
        result = get_car_route((37.5122, 127.0719), (37.2997, 127.0097))
        required_keys = {"vertexes", "duration_sec", "distance_m", "toll_fare", "fallback"}
        missing = required_keys - set(result.keys())
        vertex_ok = isinstance(result.get("vertexes"), list) and len(result["vertexes"]) >= 2
        ok = not missing and vertex_ok
        detail = (
            f"키 {len(required_keys) - len(missing)}/{len(required_keys)}, "
            f"vertexes={len(result.get('vertexes', []))}, "
            f"fallback={result.get('fallback')}"
        )
        if missing:
            detail += f", 누락: {missing}"
    except Exception as exc:
        ok = False
        detail = f"런타임 예외: {type(exc).__name__}: {exc}"
    r.add("카카오 경로 반환 dict 계약", ok, detail)


def check_popup_html(r: Report) -> None:
    try:
        from src.viz.popup_builder import place_popup_html, stadium_popup_html

        s_html = stadium_popup_html(
            {"stadium_name": "잠실", "home_team": "LG", "address": "서울",
             "subway_station": "잠실", "capacity": 25000},
            {"sky": "맑음", "precipitation_prob": 80, "temp_min": 10, "temp_max": 20,
             "rain_expected": True},
        )
        p_html = place_popup_html(
            {"title": "테스트집", "category": "food", "addr": "송파",
             "tel": "02-1", "first_image": "http://x/y.jpg", "dist_m": 123}
        )
        checks = {
            "stadium HTML": "⚾" in s_html and "잠실" in s_html,
            "stadium 우천": "우산" in s_html or "☔" in s_html,
            "place HTML": "🍽️" in p_html and "테스트집" in p_html,
            "HTTPS 치환": "https://x/y.jpg" in p_html and "http://x" not in p_html,
        }
        failed = [k for k, v in checks.items() if not v]
        ok = not failed
        detail = ", ".join(f"{k}={'O' if v else 'X'}" for k, v in checks.items())
    except Exception as exc:
        ok = False
        detail = f"런타임 예외: {type(exc).__name__}: {exc}"
    r.add("Popup HTML 빌더", ok, detail)


def check_tab_integration(r: Report) -> None:
    tabs_checks: list[str] = []
    tab1 = (PROJECT_ROOT / "src/ui/tabs/tab1_games.py").read_text(encoding="utf-8")
    if "bar_away_win_rate" not in tab1: tabs_checks.append("tab1:no-bar")
    if "gauge_win_rate" not in tab1: tabs_checks.append("tab1:no-gauge")

    tab2 = (PROJECT_ROOT / "src/ui/tabs/tab2_map.py").read_text(encoding="utf-8")
    if "create_map" not in tab2: tabs_checks.append("tab2:no-create_map")
    if "get_car_route" not in tab2: tabs_checks.append("tab2:no-route")
    if "last_object_clicked" not in tab2: tabs_checks.append("tab2:no-click")
    if "render_place_card" not in tab2: tabs_checks.append("tab2:no-place_card")

    tab3 = (PROJECT_ROOT / "src/ui/tabs/tab3_places.py").read_text(encoding="utf-8")
    if "scatter_places" not in tab3: tabs_checks.append("tab3:no-scatter")
    if "render_place_card" not in tab3: tabs_checks.append("tab3:no-place_card")

    ok = not tabs_checks
    detail = "tab1/2/3 통합 OK" if ok else f"누락: {tabs_checks}"
    r.add("탭 통합 (Phase 3 함수 호출)", ok, detail)


def main(verbose: bool) -> int:
    r = Report()
    check_files(r)
    check_function_contracts(r)
    check_dependencies(r)
    check_create_map_runtime(r)
    check_plotly_runtime(r)
    check_route_fallback(r)
    check_popup_html(r)
    check_tab_integration(r)
    r.print_all(verbose)
    passed, total = r.summary()
    return 0 if passed == total else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    sys.exit(main(args.verbose))

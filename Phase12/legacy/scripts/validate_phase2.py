"""Phase 2 완료 게이트 — UI 골격 + Stadium Editorial 리파인 정적 검증.

검증 범위: 파일 존재, import 그래프, render() 정의, React APP_CONFIG 참조,
Stadium Editorial 디자인 시스템 적용, 디바이스 분리(device.py + bottom_nav.py).
"""
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


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
        print("Phase 2 UI Scaffold + Stadium Editorial Validation")
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
            print("✅ Phase 2 완료. Phase 3 진입 가능.")
        else:
            print("❌ Phase 2 미완료. 실패 항목 해결 후 재실행.")


REQUIRED_FILES = [
    "app.py",
    "src/ui/device.py",
    "src/ui/assets.py",
    "src/ui/sidebar.py",
    "src/ui/tabs/tab1_games.py",
    "src/ui/tabs/tab2_map.py",
    "src/ui/tabs/tab3_places.py",
    "src/ui/tabs/tab4_ai.py",
    "src/ui/tabs/tab5_badges.py",
    "src/ui/components/__init__.py",
    "src/ui/components/react_loader.py",
    "src/ui/components/hero.py",
    "src/ui/components/badges.py",
    "src/ui/components/team_selector.py",
    "src/ui/components/bottom_nav.py",
    "assets/react/hero.html",
    "assets/react/badges.html",
    "assets/react/team_selector.html",
    "assets/css/style.css",
    "uiux/KBO_logo/LG.svg",
    "uiux/KBO_logo/KT.svg",
    "uiux/KBO_logo/SAMSUNG.svg",
    "uiux/KBO_logo/DOOSAN.svg",
    "uiux/KBO_logo/KIA.svg",
    "uiux/KBO_logo/NC.svg",
    "uiux/KBO_logo/LOTTE.svg",
    "uiux/KBO_logo/HANWHA.svg",
    "uiux/KBO_logo/KIWOOM.svg",
    "uiux/KBO_logo/SSG.svg",
    "uiux/KBO_logo/KBO_1.svg",
]

TAB_MODULES = [
    "src/ui/tabs/tab1_games.py",
    "src/ui/tabs/tab2_map.py",
    "src/ui/tabs/tab3_places.py",
    "src/ui/tabs/tab4_ai.py",
    "src/ui/tabs/tab5_badges.py",
]

VIEWPORT_COMPONENTS = [
    "src/ui/components/hero.py",
    "src/ui/components/team_selector.py",
    "src/ui/components/badges.py",
]

SE_TOKENS = [
    "--se-primary",
    "--se-secondary",
    "--se-surface-container-low",
    ".se-hero",
    ".se-team-card",
    ".se-badge-card",
    ".se-bottom-nav",
    "Plus Jakarta Sans",
    "Manrope",
]


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
    r.add("필수 파일 존재", ok, detail)


def check_app_imports(r: Report) -> None:
    tree = _parse(PROJECT_ROOT / "app.py")
    if tree is None:
        r.add("app.py 구문", False, "SyntaxError")
        return
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                imported.add(f"{node.module}.{alias.name}")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name)
    required = [
        "src.ui.sidebar.render_sidebar",
        "src.ui.device.render_device_toggle",
        "src.ui.tabs.tab1_games",
        "src.ui.tabs.tab2_map",
        "src.ui.tabs.tab3_places",
        "src.ui.tabs.tab4_ai",
        "src.ui.tabs.tab5_badges",
    ]
    missing = [m for m in required if not any(i.startswith(m) or m.startswith(i) for i in imported)]
    ok = not missing
    detail = f"{len(required)}개 중 {len(required) - len(missing)}개 import OK"
    if missing:
        detail += f", 누락: {missing}"
    r.add("app.py import 그래프", ok, detail)


def check_render_fns(r: Report) -> None:
    bad: list[str] = []
    for rel in TAB_MODULES:
        tree = _parse(PROJECT_ROOT / rel)
        if tree is None:
            bad.append(f"{rel}:syntax")
            continue
        has_render = any(
            isinstance(n, ast.FunctionDef) and n.name == "render" for n in ast.walk(tree)
        )
        if not has_render:
            bad.append(f"{rel}:render-missing")
    ok = not bad
    detail = f"{len(TAB_MODULES)}개 탭 중 {len(TAB_MODULES) - len(bad)}개에 render() 정의"
    if bad:
        detail += f", 이슈: {bad}"
    r.add("탭 render() 정의", ok, detail)


def check_sidebar_contract(r: Report) -> None:
    path = PROJECT_ROOT / "src/ui/sidebar.py"
    tree = _parse(path)
    if tree is None:
        r.add("sidebar.render_sidebar", False, "SyntaxError")
        return
    fn = next(
        (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "render_sidebar"),
        None,
    )
    if fn is None:
        r.add("sidebar.render_sidebar", False, "함수 없음")
        return
    src = path.read_text(encoding="utf-8")
    needed = ["selectbox", "date_input", "slider", "radio", "button", "session_state"]
    missing = [w for w in needed if w not in src]
    ok = not missing
    detail = f"필수 위젯·상태 키워드 {len(needed) - len(missing)}/{len(needed)}"
    if missing:
        detail += f", 누락: {missing}"
    r.add("사이드바 5종 필터+버튼", ok, detail)


def check_react_app_config(r: Report) -> None:
    html_files = [
        "assets/react/hero.html",
        "assets/react/badges.html",
        "assets/react/team_selector.html",
    ]
    bad: list[str] = []
    for rel in html_files:
        p = PROJECT_ROOT / rel
        if not p.exists():
            bad.append(f"{rel}:missing")
            continue
        content = p.read_text(encoding="utf-8")
        checks = {
            "APP_CONFIG": "window.APP_CONFIG" in content,
            "React CDN": "react@18" in content,
            "Babel": "@babel/standalone" in content,
            "root div": 'id="root"' in content,
            "Tailwind CDN": "cdn.tailwindcss.com" in content,
            "se-primary": "se-primary" in content,
        }
        failed = [k for k, v in checks.items() if not v]
        if failed:
            bad.append(f"{rel}:{failed}")
    ok = not bad
    detail = f"{len(html_files)}개 React HTML 중 {len(html_files) - len(bad)}개 OK (Tailwind+SE 토큰 포함)"
    if bad:
        detail += f", 이슈: {bad}"
    r.add("React HTML 구조 (Tailwind)", ok, detail)


def check_react_loader(r: Report) -> None:
    path = PROJECT_ROOT / "src/ui/components/react_loader.py"
    if not path.exists():
        r.add("react_loader 헬퍼", False, "파일 없음")
        return
    src = path.read_text(encoding="utf-8")
    needed = ["components.html", "APP_CONFIG", "json.dumps"]
    missing = [w for w in needed if w not in src]
    ok = not missing
    detail = f"필수 구성요소 {len(needed) - len(missing)}/{len(needed)}"
    if missing:
        detail += f", 누락: {missing}"
    r.add("react_loader 구성", ok, detail)


def check_team_colors(r: Report) -> None:
    path = PROJECT_ROOT / "src/ui/components/hero.py"
    if not path.exists():
        r.add("TEAM_COLORS 팔레트", False, "hero.py 없음")
        return
    src = path.read_text(encoding="utf-8")
    teams = ["LG", "KT", "SSG", "두산", "KIA", "NC", "삼성", "롯데", "한화", "키움"]
    missing = [t for t in teams if f'"{t}"' not in src]
    ok = not missing
    detail = f"10팀 중 {10 - len(missing)}개 정의"
    if missing:
        detail += f", 누락: {missing}"
    r.add("TEAM_COLORS 10개 팀", ok, detail)


def check_device_module(r: Report) -> None:
    path = PROJECT_ROOT / "src/ui/device.py"
    tree = _parse(path)
    if tree is None:
        r.add("device 모듈", False, "SyntaxError 또는 파일 없음")
        return
    src = path.read_text(encoding="utf-8")
    has_fn = any(
        isinstance(n, ast.FunctionDef) and n.name == "render_device_toggle"
        for n in ast.walk(tree)
    )
    needed = ["VIEWPORTS", "query_params", "session_state", '"web"', '"mobile"']
    missing = [w for w in needed if w not in src]
    ok = has_fn and not missing
    detail = (
        f"render_device_toggle={'O' if has_fn else 'X'}, "
        f"토큰 {len(needed) - len(missing)}/{len(needed)}"
    )
    if missing:
        detail += f", 누락: {missing}"
    r.add("디바이스 토글 모듈", ok, detail)


def check_viewport_signature(r: Report) -> None:
    bad: list[str] = []
    for rel in VIEWPORT_COMPONENTS:
        path = PROJECT_ROOT / rel
        tree = _parse(path)
        if tree is None:
            bad.append(f"{rel}:syntax")
            continue
        fn = next(
            (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "render"),
            None,
        )
        if fn is None:
            bad.append(f"{rel}:render-missing")
            continue
        args = [a.arg for a in fn.args.args]
        missing_args = [a for a in ("viewport", "renderer") if a not in args]
        if missing_args:
            bad.append(f"{rel}:{missing_args}")
    ok = not bad
    detail = f"{len(VIEWPORT_COMPONENTS)}개 컴포넌트 중 {len(VIEWPORT_COMPONENTS) - len(bad)}개 OK (viewport+renderer)"
    if bad:
        detail += f", 이슈: {bad}"
    r.add("컴포넌트 render(viewport, renderer) 시그니처", ok, detail)


def check_renderer_toggle(r: Report) -> None:
    path = PROJECT_ROOT / "src/ui/device.py"
    tree = _parse(path)
    if tree is None:
        r.add("렌더러 토글", False, "device.py SyntaxError")
        return
    src = path.read_text(encoding="utf-8")
    has_fn = any(
        isinstance(n, ast.FunctionDef) and n.name == "render_renderer_toggle"
        for n in ast.walk(tree)
    )
    needed = ["RENDERERS", '"streamlit"', '"react"', "query_params"]
    missing = [w for w in needed if w not in src]
    ok = has_fn and not missing
    detail = (
        f"render_renderer_toggle={'O' if has_fn else 'X'}, "
        f"토큰 {len(needed) - len(missing)}/{len(needed)}"
    )
    if missing:
        detail += f", 누락: {missing}"
    r.add("렌더러 토글 (streamlit/react)", ok, detail)


def check_assets_module(r: Report) -> None:
    path = PROJECT_ROOT / "src/ui/assets.py"
    tree = _parse(path)
    if tree is None:
        r.add("KBO 로고 에셋 모듈", False, "assets.py 없음/SyntaxError")
        return
    src = path.read_text(encoding="utf-8")
    needed_fns = ["get_team_logo_data_uri", "get_all_team_logos_data_uri", "get_kbo_logo_data_uri"]
    needed_teams = ["LG", "KT", "SSG", "DOOSAN", "KIA", "NC", "SAMSUNG", "LOTTE", "HANWHA", "KIWOOM"]
    missing_fns = [f for f in needed_fns if f not in src]
    missing_teams = [t for t in needed_teams if f'"{t}' not in src and f'{t}.svg' not in src]
    ok = not missing_fns and not missing_teams
    detail = (
        f"함수 {len(needed_fns) - len(missing_fns)}/{len(needed_fns)}, "
        f"팀 매핑 {len(needed_teams) - len(missing_teams)}/{len(needed_teams)}"
    )
    if missing_fns or missing_teams:
        detail += f", 누락 fn={missing_fns}, 팀={missing_teams}"
    r.add("KBO 로고 에셋 모듈", ok, detail)


def check_stadium_editorial_css(r: Report) -> None:
    path = PROJECT_ROOT / "assets/css/style.css"
    if not path.exists():
        r.add("Stadium Editorial CSS", False, "style.css 없음")
        return
    css = path.read_text(encoding="utf-8")
    missing = [t for t in SE_TOKENS if t not in css]
    ok = not missing
    detail = f"{len(SE_TOKENS) - len(missing)}/{len(SE_TOKENS)} 토큰 존재"
    if missing:
        detail += f", 누락: {missing}"
    r.add("Stadium Editorial 디자인 토큰", ok, detail)


def check_bottom_nav(r: Report) -> None:
    path = PROJECT_ROOT / "src/ui/components/bottom_nav.py"
    tree = _parse(path)
    if tree is None:
        r.add("모바일 하단 네비", False, "SyntaxError 또는 파일 없음")
        return
    src = path.read_text(encoding="utf-8")
    has_fn = any(
        isinstance(n, ast.FunctionDef) and n.name == "render"
        for n in ast.walk(tree)
    )
    needed = ["se-bottom-nav", "material-symbols-outlined", "MATCHES", "BADGES"]
    missing = [w for w in needed if w not in src]
    ok = has_fn and not missing
    detail = (
        f"render={'O' if has_fn else 'X'}, "
        f"토큰 {len(needed) - len(missing)}/{len(needed)}"
    )
    if missing:
        detail += f", 누락: {missing}"
    r.add("모바일 Bottom Nav", ok, detail)


def main(verbose: bool) -> int:
    sys.path.insert(0, str(PROJECT_ROOT))
    r = Report()
    check_files(r)
    check_app_imports(r)
    check_render_fns(r)
    check_sidebar_contract(r)
    check_react_app_config(r)
    check_react_loader(r)
    check_team_colors(r)
    check_device_module(r)
    check_viewport_signature(r)
    check_stadium_editorial_css(r)
    check_bottom_nav(r)
    check_renderer_toggle(r)
    check_assets_module(r)
    r.print_all(verbose)
    passed, total = r.summary()
    return 0 if passed == total else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    sys.exit(main(args.verbose))

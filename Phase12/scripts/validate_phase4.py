"""Phase 4 완료 게이트 — AI 모듈 정적/런타임 검증."""
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
        print("Phase 4 AI Features Validation Report")
        print("=" * 60)
        for name, ok, detail in self.results:
            tag = "[PASS]" if ok else "[FAIL]"
            line = f"{tag} {name}"
            if detail and (verbose or not ok):
                line += f" — {detail}"
            print(line)
        passed, total = self.summary()
        print()
        print(f"총 검증: {total}개 / 통과: {passed} / 실패: {total - passed}\n")
        if passed == total:
            print("✅ Phase 4 완료. Phase 5 진입 가능.")
        else:
            print("❌ Phase 4 미완료. 실패 항목 해결 후 재실행.")


REQUIRED_FILES = [
    "src/ai/predict.py",
    "src/ai/ollama_client.py",
    "src/ai/llm_client.py",
    "src/ai/prompts.py",
    "src/ai/tools.py",
    "src/ai/mock_responses.py",
    "src/ai/agents.py",
    "src/ai/rag.py",
    "src/ui/tabs/tab4_ai.py",
    "data/knowledge/away_game_tips.json",
    "models/win_rate_model.pkl",
]

FUNCTION_CONTRACTS = {
    "src/ai/predict.py": ["train_model", "load_model", "predict_win_rate"],
    "src/ai/ollama_client.py": ["chat", "embed", "health", "has_model"],
    "src/ai/llm_client.py": ["chat_complete"],
    "src/ai/prompts.py": ["build_system_prompt"],
    "src/ai/tools.py": ["execute_tool"],
    "src/ai/mock_responses.py": ["get_mock_response"],
    "src/ai/agents.py": ["run_multi_agent"],
    "src/ai/rag.py": ["build_index", "search_tips"],
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
    r.add("필수 파일 존재", ok, detail)


def check_contracts(r: Report) -> None:
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
    required = ["httpx", "sklearn", "pandas", "chromadb"]
    missing = [m for m in required if importlib.util.find_spec(m) is None]
    ok = not missing
    detail = f"{len(required) - len(missing)}/{len(required)} 설치"
    if missing:
        detail += f", 누락: {missing}"
    r.add("의존성 (httpx/sklearn/pandas/chromadb)", ok, detail)


def check_predict(r: Report) -> None:
    try:
        from src.ai.predict import load_model, predict_win_rate
        from src.data_loader import load_team_stats
        model = load_model()
        stats = load_team_stats()
        prob_lg = predict_win_rate("LG", "KT", stats, model)
        prob_kia = predict_win_rate("KIA", "삼성", stats, model)
        ok = 0.0 <= prob_lg <= 1.0 and 0.0 <= prob_kia <= 1.0 and "pipeline" in model
        detail = f"LG vs KT: {prob_lg:.3f}, KIA vs 삼성: {prob_kia:.3f}"
    except Exception as exc:
        ok = False
        detail = f"런타임 예외: {type(exc).__name__}: {exc}"
    r.add("승률 예측 모델 런타임", ok, detail)


def check_ollama_health(r: Report) -> None:
    try:
        from src.ai.ollama_client import has_model, health, list_models
        from src import config
        up = health()
        if not up:
            r.add("Ollama 서버 상태", False, "서버 응답 없음 (http://localhost:11434)")
            return
        models = list_models()
        chat_ok = has_model(config.OLLAMA_CHAT_MODEL)
        embed_ok = has_model(config.OLLAMA_EMBED_MODEL)
        ok = chat_ok and embed_ok
        detail = (
            f"서버 OK, 모델 {len(models)}개 · "
            f"{config.OLLAMA_CHAT_MODEL}={'O' if chat_ok else 'X'}, "
            f"{config.OLLAMA_EMBED_MODEL}={'O' if embed_ok else 'X'}"
        )
    except Exception as exc:
        ok = False
        detail = f"예외: {type(exc).__name__}: {exc}"
    r.add("Ollama 서버 + 모델 존재", ok, detail)


def check_chat_complete(r: Report) -> None:
    try:
        from src.ai.llm_client import chat_complete
        resp = chat_complete(
            [
                {"role": "system", "content": "반드시 한국어로만 응답하세요. 한 문장."},
                {"role": "user", "content": "안녕하세요!"},
            ],
            temperature=0.5,
            max_tokens=100,
        )
        content = resp.get("content", "")
        has_korean = any("\uac00" <= ch <= "\ud7af" for ch in content)
        ok = resp.get("model") != "fallback" and len(content) >= 5 and has_korean
        detail = f"model={resp.get('model')}, len={len(content)}, 한글={has_korean}"
    except Exception as exc:
        ok = False
        detail = f"예외: {type(exc).__name__}: {exc}"
    r.add("chat_complete 한국어 응답", ok, detail)


def check_tools(r: Report) -> None:
    bad: list[str] = []
    try:
        from src.ai.tools import TOOL_SCHEMAS, execute_tool
        schema_names = {t["function"]["name"] for t in TOOL_SCHEMAS}
        required_names = {"search_game", "predict_win_rate", "get_weather", "find_places", "get_route"}
        missing_schemas = required_names - schema_names
        if missing_schemas:
            bad.append(f"schema 누락: {missing_schemas}")

        test_cases = [
            ("search_game", {"team": "LG", "start_date": "2026-04-18", "end_date": "2026-04-25"}),
            ("predict_win_rate", {"team": "LG", "opponent": "KT"}),
            ("find_places", {"stadium": "광주", "category": "food", "limit": 3}),
            ("get_route", {"origin": "서울역", "destination_stadium": "광주"}),
        ]
        for name, args in test_cases:
            result = execute_tool(name, args)
            if not result.get("success"):
                bad.append(f"{name}: {result.get('error', '실패')}")
        ok = not bad
        detail = f"schema {len(schema_names)}개, smoke {len(test_cases)}개"
        if bad:
            detail += f", 이슈: {bad[:3]}"
    except Exception as exc:
        ok = False
        detail = f"예외: {type(exc).__name__}: {exc}"
    r.add("도구 5종 schema + 실행", ok, detail)


def check_rag(r: Report) -> None:
    try:
        from src.ai.rag import search_tips
        results = search_tips("원정 전 식사 장소", stadium=None, top_k=3)
        ok = isinstance(results, list) and len(results) > 0
        detail = f"검색 결과 {len(results)}건" if results else "결과 없음 (인덱스 미구축?)"
    except Exception as exc:
        ok = False
        detail = f"예외: {type(exc).__name__}: {exc}"
    r.add("RAG 검색 (bge-m3)", ok, detail)


def check_mock(r: Report) -> None:
    try:
        from src.ai.mock_responses import get_mock_response
        m1 = get_mock_response("광주 가족 원정")
        m2 = get_mock_response("부산 맛집 추천")
        m3 = get_mock_response("비 올까? 실내 관광")
        matched = sum(1 for m in (m1, m2, m3) if m is not None)
        ok = matched == 3
        detail = f"3개 시나리오 중 {matched}개 매칭"
    except Exception as exc:
        ok = False
        detail = f"예외: {type(exc).__name__}: {exc}"
    r.add("Mock 응답 매칭", ok, detail)


def check_tab_integration(r: Report) -> None:
    bad: list[str] = []
    tab1 = (PROJECT_ROOT / "src/ui/tabs/tab1_games.py").read_text(encoding="utf-8")
    if "predict_win_rate" not in tab1 and "_real_or_dummy_win_prob" not in tab1:
        bad.append("tab1:predict-not-integrated")

    tab4 = (PROJECT_ROOT / "src/ui/tabs/tab4_ai.py").read_text(encoding="utf-8")
    for token in ("chat_complete", "TOOL_SCHEMAS", "execute_tool", "build_system_prompt", "run_multi_agent"):
        if token not in tab4:
            bad.append(f"tab4:{token}")

    sidebar = (PROJECT_ROOT / "src/ui/sidebar.py").read_text(encoding="utf-8")
    if "demo_mode" not in sidebar:
        bad.append("sidebar:demo-mode-toggle")

    ok = not bad
    detail = "tab1 predict 연동 + tab4 AI 통합 + sidebar 시연 토글 OK" if ok else f"이슈: {bad}"
    r.add("UI 통합 (tab1/tab4/sidebar)", ok, detail)


def main(verbose: bool) -> int:
    r = Report()
    check_files(r)
    check_contracts(r)
    check_dependencies(r)
    check_predict(r)
    check_ollama_health(r)
    check_chat_complete(r)
    check_tools(r)
    check_rag(r)
    check_mock(r)
    check_tab_integration(r)
    r.print_all(verbose)
    passed, total = r.summary()
    return 0 if passed == total else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    sys.exit(main(args.verbose))

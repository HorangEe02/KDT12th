"""Phase 5 완료 게이트 — 배포 에셋 + Firebase/GCP 클라이언트 정적·런타임 검증."""
from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class Report:
    def __init__(self):
        self.results: list[tuple[str, bool, str]] = []

    def add(self, name, ok, detail=""):
        self.results.append((name, ok, detail))

    def summary(self):
        passed = sum(1 for _, ok, _ in self.results if ok)
        return passed, len(self.results)

    def print_all(self, verbose: bool):
        print("=" * 60)
        print("Phase 5 Deployment Readiness Validation")
        print("=" * 60)
        for name, ok, detail in self.results:
            tag = "[PASS]" if ok else "[FAIL]"
            line = f"{tag} {name}"
            if detail and (verbose or not ok):
                line += f" — {detail}"
            print(line)
        passed, total = self.summary()
        print(f"\n총 검증: {total}개 / 통과: {passed} / 실패: {total - passed}\n")
        if passed == total:
            print("✅ Phase 5 배포 준비 완료.")
        else:
            print("❌ Phase 5 미완료. 실패 항목 해결 후 재실행.")


REQUIRED_FILES = [
    "Dockerfile",
    ".dockerignore",
    "firebase.json",
    ".firebaserc",
    "firestore.rules",
    "firestore.indexes.json",
    "public/index.html",
    "src/ai/gemini_client.py",
    "src/ai/llm_client.py",
    "src/db/__init__.py",
    "src/db/firestore_client.py",
    "src/db/storage_client.py",
    "src/ui/plan_share.py",
    "scripts/deploy.sh",
    "docs/ARCHITECTURE.md",
    "docs/PRESENTATION_OUTLINE.md",
    "docs/DEMO_SCRIPT.md",
    "docs/DEPLOY_CHECKLIST.md",
    "docs/QA_PREP.md",
]


def _parse(path: Path) -> ast.AST | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return None


def check_files(r: Report) -> None:
    missing = [p for p in REQUIRED_FILES if not (PROJECT_ROOT / p).exists()]
    ok = not missing
    detail = f"{len(REQUIRED_FILES) - len(missing)}/{len(REQUIRED_FILES)}"
    if missing:
        detail += f", 누락: {missing}"
    r.add("필수 파일 존재", ok, detail)


def check_firebase_json(r: Report) -> None:
    path = PROJECT_ROOT / "firebase.json"
    try:
        cfg = json.loads(path.read_text(encoding="utf-8"))
        hosting = cfg.get("hosting") or {}
        rewrites = hosting.get("rewrites") or []
        ok = any(
            rw.get("run", {}).get("serviceId") == "away-game-companion"
            and rw.get("run", {}).get("region")
            for rw in rewrites
        )
        detail = f"rewrites: {len(rewrites)}, serviceId 매칭: {ok}"
    except Exception as exc:
        ok = False
        detail = f"파싱 실패: {exc}"
    r.add("firebase.json Cloud Run rewrite", ok, detail)


def check_firebaserc(r: Report) -> None:
    path = PROJECT_ROOT / ".firebaserc"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        default = data.get("projects", {}).get("default")
        ok = default == "mini12-310f5"
        detail = f"default project: {default}"
    except Exception as exc:
        ok = False
        detail = f"파싱 실패: {exc}"
    r.add(".firebaserc 프로젝트 ID", ok, detail)


def check_dockerfile(r: Report) -> None:
    path = PROJECT_ROOT / "Dockerfile"
    content = path.read_text(encoding="utf-8")
    checks = {
        "FROM python:3.11-slim": "python:3.11-slim" in content,
        "EXPOSE 8080": "EXPOSE 8080" in content,
        "streamlit run": "streamlit run" in content,
        "PORT env": "PORT" in content,
    }
    failed = [k for k, v in checks.items() if not v]
    ok = not failed
    detail = f"{len(checks) - len(failed)}/{len(checks)} 통과"
    if failed:
        detail += f", 누락: {failed}"
    r.add("Dockerfile 핵심 디렉티브", ok, detail)


def check_dependencies(r: Report) -> None:
    required = ["google.genai", "firebase_admin", "google.cloud.storage"]
    missing = []
    for mod in required:
        if importlib.util.find_spec(mod) is None:
            missing.append(mod)
    ok = not missing
    detail = f"{len(required) - len(missing)}/{len(required)} 설치"
    if missing:
        detail += f", 누락: {missing}"
    r.add("배포 SDK 설치 (google-genai/firebase-admin/google-cloud-storage)", ok, detail)


def check_gemini_runtime(r: Report) -> None:
    try:
        from src.ai import gemini_client
        if not gemini_client.health():
            r.add("Gemini API 런타임", False, "API 키 없음 또는 SDK 미설치")
            return
        resp = gemini_client.chat(
            [
                {"role": "system", "content": "한국어 한 문장."},
                {"role": "user", "content": "인사"},
            ],
            temperature=0.3,
            num_predict=50,
        )
        has_content = bool(resp.get("content"))
        model = resp.get("model", "")
        has_korean = any("\uac00" <= ch <= "\ud7af" for ch in resp.get("content", ""))
        ok = has_content and has_korean and "error" not in model and "unavailable" not in model
        detail = f"model={model}, len={len(resp.get('content',''))}, 한글={has_korean}"
    except Exception as exc:
        ok = False
        detail = f"예외: {type(exc).__name__}: {exc}"
    r.add("Gemini API 런타임 (한국어)", ok, detail)


def check_llm_client_fallback(r: Report) -> None:
    """Cloud Run 환경(K_SERVICE 있음) 시뮬 → Gemini로 자동 라우팅 확인."""
    import os
    old = os.environ.get("K_SERVICE")
    os.environ["K_SERVICE"] = "test"
    # src.* 전체 모듈을 pop해 clean reload 보장
    to_pop = [m for m in list(sys.modules.keys()) if m == "src" or m.startswith("src.")]
    for m in to_pop:
        sys.modules.pop(m, None)
    try:
        from src.ai.llm_client import chat_complete
        resp = chat_complete(
            [
                {"role": "system", "content": "한국어 한 문장."},
                {"role": "user", "content": "인사"},
            ],
            temperature=0.3,
            max_tokens=50,
        )
        model = resp.get("model", "")
        ok = "gemini" in model.lower()
        detail = f"Cloud Run 시뮬 → 선택 모델: {model}"
    except Exception as exc:
        ok = False
        detail = f"예외: {type(exc).__name__}: {exc}"
    finally:
        if old is None:
            os.environ.pop("K_SERVICE", None)
        else:
            os.environ["K_SERVICE"] = old
        to_pop = [m for m in list(sys.modules.keys()) if m == "src" or m.startswith("src.")]
        for m in to_pop:
            sys.modules.pop(m, None)
    r.add("llm_client Cloud Run → Gemini 라우팅", ok, detail)


def check_firestore_module(r: Report) -> None:
    """Firestore 모듈 import + 헬스 상태 (서비스 계정 키 없으면 False OK)."""
    try:
        from src.db import firestore_client as fs
        # 모듈 구조 확인
        has_fns = all(hasattr(fs, name) for name in (
            "get_or_create_user_id", "save_visited_stadiums",
            "load_visited_stadiums", "save_shared_plan", "load_shared_plan",
        ))
        health = fs.health()
        # 서비스 계정 키가 없으면 health=False여도 모듈 자체는 정상
        detail = f"함수 정의: {'O' if has_fns else 'X'}, health: {health} (키 없으면 False OK)"
        ok = has_fns
    except Exception as exc:
        ok = False
        detail = f"예외: {type(exc).__name__}: {exc}"
    r.add("Firestore 모듈 구조", ok, detail)


def check_ui_integration(r: Report) -> None:
    bad: list[str] = []
    app_py = (PROJECT_ROOT / "app.py").read_text(encoding="utf-8")
    if "apply_shared_plan_from_query" not in app_py:
        bad.append("app.py:plan_share-hook")

    sidebar = (PROJECT_ROOT / "src/ui/sidebar.py").read_text(encoding="utf-8")
    if "render_share_button" not in sidebar:
        bad.append("sidebar:share-button")

    tab5 = (PROJECT_ROOT / "src/ui/tabs/tab5_badges.py").read_text(encoding="utf-8")
    for token in ("firestore_client", "save_visited_stadiums", "load_visited_stadiums"):
        if token not in tab5:
            bad.append(f"tab5:{token}")

    ok = not bad
    detail = "app/sidebar/tab5 Firebase 통합 OK" if ok else f"이슈: {bad}"
    r.add("UI Firebase 통합", ok, detail)


def check_docker_installed(r: Report) -> None:
    import shutil
    dk = shutil.which("docker") is not None
    fb = shutil.which("firebase") is not None
    gc = shutil.which("gcloud") is not None
    # docker/firebase는 필수, gcloud는 배포 당일까지 설치하면 OK (경고만)
    detail = f"docker={'O' if dk else 'X'} firebase={'O' if fb else 'X'} gcloud={'O' if gc else 'X (배포 전 설치 필요)'}"
    r.add("배포 CLI (docker/firebase 필수)", dk and fb, detail)


def main(verbose: bool) -> int:
    r = Report()
    check_files(r)
    check_firebase_json(r)
    check_firebaserc(r)
    check_dockerfile(r)
    check_dependencies(r)
    check_gemini_runtime(r)
    check_llm_client_fallback(r)
    check_firestore_module(r)
    check_ui_integration(r)
    check_docker_installed(r)
    r.print_all(verbose)
    passed, total = r.summary()
    return 0 if passed == total else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    sys.exit(main(args.verbose))

"""
run_all.py
모든 데이터 수집 스크립트를 순차 실행합니다.

사용법:
    python scripts/run_all.py          # 데모 모드 (API 키 불필요)
    python scripts/run_all.py --live    # 실제 API 호출
"""

import argparse
import subprocess
import sys
from pathlib import Path


SCRIPTS_DIR = Path(__file__).parent

SCRIPTS = [
    {
        "name": "식품 영양성분 수집",
        "file": "fetch_nutrition_api.py",
        "demo_args": ["--demo"],
        "live_args": ["--fitness-foods"],
    },
    {
        "name": "국민체력100 데이터 수집",
        "file": "fetch_fitness100_api.py",
        "demo_args": ["--demo"],
        "live_args": [],
    },
    {
        "name": "KNHANES 데이터 처리",
        "file": "process_knhanes.py",
        "demo_args": ["--demo"],
        "live_args": ["--demo"],  # 원시자료는 별도 다운로드 필요
    },
    {
        "name": "운동 DB 구축",
        "file": "build_exercise_db.py",
        "demo_args": [],
        "live_args": [],
    },
    {
        "name": "학습 데이터 준비",
        "file": "prepare_training_data.py",
        "demo_args": [],
        "live_args": [],
    },
]


def main():
    parser = argparse.ArgumentParser(description="전체 데이터 수집 실행")
    parser.add_argument("--live", action="store_true", help="실제 API 호출 (API 키 필요)")
    args = parser.parse_args()

    mode = "live" if args.live else "demo"

    print("=" * 60)
    print(f"🚀 헬창지피티 데이터 수집 전체 실행 ({mode} 모드)")
    print("=" * 60)

    results = []

    for i, script in enumerate(SCRIPTS, 1):
        print(f"\n{'─' * 60}")
        print(f"[{i}/{len(SCRIPTS)}] {script['name']}")
        print(f"{'─' * 60}")

        script_path = SCRIPTS_DIR / script["file"]
        extra_args = script["live_args"] if args.live else script["demo_args"]

        try:
            result = subprocess.run(
                [sys.executable, str(script_path)] + extra_args,
                capture_output=False,
                timeout=300,
            )
            status = "✅ 성공" if result.returncode == 0 else f"❌ 실패 (코드: {result.returncode})"
        except subprocess.TimeoutExpired:
            status = "⏰ 타임아웃"
        except Exception as e:
            status = f"❌ 오류: {e}"

        results.append((script["name"], status))

    print(f"\n{'=' * 60}")
    print("📊 실행 결과 요약")
    print(f"{'=' * 60}")

    for name, status in results:
        print(f"  {status}  {name}")

    # 생성된 파일 확인
    print(f"\n📁 생성된 데이터 파일:")
    data_dir = SCRIPTS_DIR.parent / "data"
    for p in sorted(data_dir.rglob("*.json")):
        size_kb = p.stat().st_size / 1024
        print(f"  {p.relative_to(data_dir)}  ({size_kb:.1f}KB)")

    print(f"\n✨ 전체 데이터 수집 완료!")
    print(f"   다음 단계: API 키를 발급받아 --live 모드로 실제 데이터를 수집하세요.")


if __name__ == "__main__":
    main()

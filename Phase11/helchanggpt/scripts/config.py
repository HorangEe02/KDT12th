"""
config.py
데이터 수집 스크립트 공통 설정.

.env 파일에서 API 키를 로드하고, 공통 경로를 관리합니다.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# .env 파일 로드
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)

# ── 프로젝트 경로 ──
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
NUTRITION_DIR = DATA_DIR / "nutrition"
EXERCISES_DIR = DATA_DIR / "exercises"
USER_SAMPLES_DIR = DATA_DIR / "user_samples"
DIARY_SAMPLES_DIR = DATA_DIR / "diary_samples"

# ── API 키 ──
FOOD_SAFETY_API_KEY = os.getenv("FOOD_SAFETY_API_KEY", "")           # COOKRCP01
FOOD_SAFETY_I2790_KEY = os.getenv("FOOD_SAFETY_I2790_KEY", "")       # I2790 식품영양성분
FOOD_SAFETY_HEALTH_FUNC_KEY = os.getenv("FOOD_SAFETY_HEALTH_FUNC_KEY", "")  # 건강기능식품
DATA_GO_KR_API_KEY = os.getenv("DATA_GO_KR_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# ── API 엔드포인트 ──
# 식품안전나라 식품영양성분 DB (I2790)
FOOD_SAFETY_API_BASE = "http://openapi.foodsafetykorea.go.kr/api"
FOOD_SAFETY_SERVICE_ID = "COOKRCP01"  # 조리식품 레시피+영양성분 (기본키로 접근 가능)

# 공공데이터포털 국민체력100 (이미지 상세정보 기준)
# 엔드포인트: https://apis.data.go.kr/B551014/SRVC_NFA_TEST_RESULT
# ※ 2026-04-10 기준 서버 500 에러 발생 중 — 추후 재시도 필요
FITNESS100_API_BASE = "https://apis.data.go.kr/B551014/SRVC_NFA_TEST_RESULT"

# ── 출력 파일 경로 ──
OUTPUT_FILES = {
    "nutrition_foods": NUTRITION_DIR / "foods.json",
    "nutrition_foods_csv": NUTRITION_DIR / "foods.csv",
    "nutrition_summary": NUTRITION_DIR / "summary.json",
    "fitness100": USER_SAMPLES_DIR / "fitness100.json",
    "knhanes_stats": USER_SAMPLES_DIR / "knhanes_body_stats.json",
    "exercise_db": EXERCISES_DIR / "exercise_db.json",
    "exercise_met": EXERCISES_DIR / "exercise_met.json",
    "training_goal_classification": USER_SAMPLES_DIR / "goal_classification_train.json",
    "training_diary_samples": DIARY_SAMPLES_DIR / "diary_samples.json",
}


def ensure_dirs():
    """데이터 디렉토리들이 존재하는지 확인합니다."""
    for d in [NUTRITION_DIR, EXERCISES_DIR, USER_SAMPLES_DIR, DIARY_SAMPLES_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def check_api_key(key_name: str, key_value: str) -> bool:
    """API 키가 설정되었는지 확인합니다."""
    if not key_value or key_value.startswith("your_"):
        print(f"⚠️  {key_name}가 설정되지 않았습니다.")
        print(f"   scripts/.env 파일에 {key_name}를 입력해주세요.")
        print(f"   (.env.example을 .env로 복사 후 수정)")
        return False
    return True

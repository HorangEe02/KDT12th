"""
user_history.py
사용자별 인바디 측정 이력을 JSON 파일로 관리합니다.

저장 구조:
  data/user_profiles/{user_id}/
    ├── profile.json          # 최신 프로필
    ├── history.json          # 측정 이력 배열
    └── reports/              # 생성된 보고서
        ├── 2025-05-05_report.pdf
        └── 2025-05-05_report.xlsx
"""

import json
from datetime import datetime
from pathlib import Path

from .inbody_parser import InBodyData


PROFILES_DIR = Path(__file__).parent.parent.parent / "data" / "user_profiles"


def _user_dir(user_id: str) -> Path:
    d = PROFILES_DIR / user_id
    d.mkdir(parents=True, exist_ok=True)
    (d / "reports").mkdir(exist_ok=True)
    return d


def save_measurement(user_id: str, inbody: InBodyData) -> dict:
    """새 인바디 측정 결과를 저장합니다."""
    user_dir = _user_dir(user_id)
    history_path = user_dir / "history.json"

    # 기존 히스토리 로드
    if history_path.exists():
        with open(history_path, "r", encoding="utf-8") as f:
            history = json.load(f)
    else:
        history = {"user_id": user_id, "measurements": []}

    # 새 측정 추가
    entry = {
        "recorded_at": datetime.now().isoformat(),
        "test_date": inbody.basic_info.get("test_date", ""),
        "parse_method": inbody.parse_method,
        "data": inbody.raw,
        "inbody_score": inbody.inbody_score,
    }
    history["measurements"].append(entry)

    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    # 최신 프로필 업데이트
    profile_path = user_dir / "profile.json"
    profile = {
        "user_id": user_id,
        "latest_measurement": entry,
        "total_measurements": len(history["measurements"]),
        "updated_at": datetime.now().isoformat(),
    }
    with open(profile_path, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)

    return {
        "user_id": user_id,
        "measurement_index": len(history["measurements"]) - 1,
        "total_measurements": len(history["measurements"]),
    }


def get_history(user_id: str) -> dict:
    """사용자의 측정 이력을 반환합니다."""
    history_path = _user_dir(user_id) / "history.json"
    if not history_path.exists():
        return {"user_id": user_id, "measurements": []}
    with open(history_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_latest_profile(user_id: str) -> dict | None:
    """사용자의 최신 프로필을 반환합니다."""
    profile_path = _user_dir(user_id) / "profile.json"
    if not profile_path.exists():
        return None
    with open(profile_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_trend_data(user_id: str) -> dict:
    """측정 이력에서 변화 추이 데이터를 추출합니다."""
    history = get_history(user_id)
    measurements = history.get("measurements", [])

    trend = {"dates": [], "weight": [], "smm": [], "bfp": [], "score": []}

    for m in measurements:
        data = m.get("data", {})
        bc = data.get("body_composition", {})
        mfa = data.get("muscle_fat_analysis", {})
        oa = data.get("obesity_analysis", {})

        trend["dates"].append(m.get("test_date", m.get("recorded_at", "")))
        trend["weight"].append(bc.get("weight_kg"))
        trend["smm"].append(mfa.get("skeletal_muscle_mass_kg"))
        trend["bfp"].append(oa.get("body_fat_percent"))
        trend["score"].append(m.get("inbody_score"))

    return trend


def list_users() -> list[str]:
    """저장된 사용자 목록을 반환합니다."""
    if not PROFILES_DIR.exists():
        return []
    return [d.name for d in PROFILES_DIR.iterdir() if d.is_dir()]

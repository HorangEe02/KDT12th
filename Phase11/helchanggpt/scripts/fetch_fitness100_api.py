"""
fetch_fitness100_api.py
공공데이터포털 국민체력100 체력측정 결과 API에서 데이터를 수집합니다.

API 정보: https://www.data.go.kr/data/15108938/openapi.do
서비스명: 국민체력100 체력인증센터 측정결과 정보

사전 준비:
    1. https://www.data.go.kr 회원가입
    2. 위 API 페이지에서 "활용신청" → 인증키 발급 (1~2일)
    3. scripts/.env 파일에 DATA_GO_KR_API_KEY 입력

사용법:
    python scripts/fetch_fitness100_api.py
    python scripts/fetch_fitness100_api.py --demo
    python scripts/fetch_fitness100_api.py --age-group 30

출력:
    data/user_samples/fitness100.json — 체력측정 데이터
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
from config import (
    DATA_GO_KR_API_KEY,
    FITNESS100_API_BASE,
    OUTPUT_FILES,
    ensure_dirs,
    check_api_key,
)


def fetch_fitness100_data(
    api_key: str,
    num_of_rows: int = 100,
    page_no: int = 1,
) -> dict | None:
    """
    국민체력100 API에서 데이터를 가져옵니다.

    엔드포인트: https://apis.data.go.kr/B551014/SRVC_NFA_TEST_RESULT
    ※ 2026-04-10 기준 API 서버가 500 에러를 반환하는 상태입니다.
       서버 복구 후 자동으로 작동합니다.
    """
    params = {
        "serviceKey": api_key,
        "numOfRows": num_of_rows,
        "pageNo": page_no,
        "type": "json",
    }

    try:
        # 엔드포인트 직접 호출 (오퍼레이션 없이)
        resp = requests.get(
            FITNESS100_API_BASE,
            params=params,
            timeout=30,
        )

        # 500 에러 시 명확한 안내
        if resp.status_code == 500:
            print(f"  ⚠️ API 서버 500 에러 — data.go.kr 서버 측 문제 (키 문제 아님)")
            print(f"  💡 --demo 옵션으로 기준 데이터를 생성할 수 있습니다.")
            return None

        resp.raise_for_status()

        # JSON 파싱 시도
        try:
            return resp.json()
        except Exception:
            # XML 응답일 수 있음
            print(f"  ⚠️ JSON이 아닌 응답: {resp.text[:150]}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"  ❌ API 요청 실패: {e}")
        return None


def generate_demo_fitness_data() -> list[dict]:
    """API 키 없이 한국인 체력 기준 데모 데이터를 생성합니다."""
    print("📦 데모 모드: 연령대별 체력 기준 데이터를 생성합니다.")

    # 국민체력100 측정 항목 기준 (한국체육과학원 기준치 참고)
    demo_data = {
        "measurement_items": {
            "grip_strength_kg": "악력 (kg)",
            "sit_ups_count": "윗몸일으키기 (회/60초)",
            "flexibility_cm": "앉아 윗몸 앞으로 굽히기 (cm)",
            "shuttle_run_count": "왕복오래달리기 (회)",
            "bmi": "BMI (kg/m²)",
            "body_fat_percent": "체지방률 (%)",
        },
        "age_gender_standards": [
            # 남성 기준치 (보통 수준)
            {"age_group": "19-24", "gender": "남성", "grip_strength_avg": 43.5,
             "sit_ups_avg": 42, "flexibility_avg": 12.5, "shuttle_run_avg": 55,
             "bmi_avg": 23.5, "body_fat_avg": 17.5, "weight_avg": 72.3, "height_avg": 174.2},
            {"age_group": "25-29", "gender": "남성", "grip_strength_avg": 44.2,
             "sit_ups_avg": 39, "flexibility_avg": 11.8, "shuttle_run_avg": 50,
             "bmi_avg": 24.8, "body_fat_avg": 20.2, "weight_avg": 76.1, "height_avg": 174.5},
            {"age_group": "30-34", "gender": "남성", "grip_strength_avg": 43.8,
             "sit_ups_avg": 35, "flexibility_avg": 10.5, "shuttle_run_avg": 45,
             "bmi_avg": 25.3, "body_fat_avg": 22.1, "weight_avg": 77.5, "height_avg": 174.0},
            {"age_group": "35-39", "gender": "남성", "grip_strength_avg": 43.0,
             "sit_ups_avg": 32, "flexibility_avg": 9.8, "shuttle_run_avg": 40,
             "bmi_avg": 25.5, "body_fat_avg": 23.5, "weight_avg": 78.0, "height_avg": 173.5},
            {"age_group": "40-44", "gender": "남성", "grip_strength_avg": 42.0,
             "sit_ups_avg": 28, "flexibility_avg": 8.5, "shuttle_run_avg": 35,
             "bmi_avg": 25.2, "body_fat_avg": 24.0, "weight_avg": 76.5, "height_avg": 172.8},
            {"age_group": "45-49", "gender": "남성", "grip_strength_avg": 40.5,
             "sit_ups_avg": 25, "flexibility_avg": 7.8, "shuttle_run_avg": 30,
             "bmi_avg": 25.0, "body_fat_avg": 24.5, "weight_avg": 74.8, "height_avg": 172.0},
            {"age_group": "50-54", "gender": "남성", "grip_strength_avg": 38.5,
             "sit_ups_avg": 22, "flexibility_avg": 7.0, "shuttle_run_avg": 25,
             "bmi_avg": 24.8, "body_fat_avg": 25.0, "weight_avg": 73.0, "height_avg": 171.0},
            {"age_group": "55-59", "gender": "남성", "grip_strength_avg": 36.0,
             "sit_ups_avg": 18, "flexibility_avg": 6.0, "shuttle_run_avg": 22,
             "bmi_avg": 24.5, "body_fat_avg": 25.5, "weight_avg": 71.0, "height_avg": 170.0},
            {"age_group": "60-64", "gender": "남성", "grip_strength_avg": 33.5,
             "sit_ups_avg": 15, "flexibility_avg": 5.5, "shuttle_run_avg": 18,
             "bmi_avg": 24.2, "body_fat_avg": 26.0, "weight_avg": 69.0, "height_avg": 168.5},

            # 여성 기준치 (보통 수준)
            {"age_group": "19-24", "gender": "여성", "grip_strength_avg": 24.5,
             "sit_ups_avg": 22, "flexibility_avg": 16.5, "shuttle_run_avg": 30,
             "bmi_avg": 21.5, "body_fat_avg": 25.0, "weight_avg": 56.8, "height_avg": 162.3},
            {"age_group": "25-29", "gender": "여성", "grip_strength_avg": 25.0,
             "sit_ups_avg": 20, "flexibility_avg": 15.8, "shuttle_run_avg": 28,
             "bmi_avg": 22.0, "body_fat_avg": 26.5, "weight_avg": 58.0, "height_avg": 162.0},
            {"age_group": "30-34", "gender": "여성", "grip_strength_avg": 25.2,
             "sit_ups_avg": 18, "flexibility_avg": 14.5, "shuttle_run_avg": 25,
             "bmi_avg": 22.5, "body_fat_avg": 27.8, "weight_avg": 59.2, "height_avg": 161.5},
            {"age_group": "35-39", "gender": "여성", "grip_strength_avg": 25.0,
             "sit_ups_avg": 16, "flexibility_avg": 13.8, "shuttle_run_avg": 22,
             "bmi_avg": 23.0, "body_fat_avg": 29.0, "weight_avg": 60.0, "height_avg": 161.0},
            {"age_group": "40-44", "gender": "여성", "grip_strength_avg": 24.5,
             "sit_ups_avg": 14, "flexibility_avg": 12.5, "shuttle_run_avg": 20,
             "bmi_avg": 23.5, "body_fat_avg": 30.0, "weight_avg": 60.5, "height_avg": 160.0},
            {"age_group": "45-49", "gender": "여성", "grip_strength_avg": 23.8,
             "sit_ups_avg": 12, "flexibility_avg": 11.5, "shuttle_run_avg": 18,
             "bmi_avg": 24.0, "body_fat_avg": 31.5, "weight_avg": 61.0, "height_avg": 159.0},
            {"age_group": "50-54", "gender": "여성", "grip_strength_avg": 22.5,
             "sit_ups_avg": 10, "flexibility_avg": 10.8, "shuttle_run_avg": 15,
             "bmi_avg": 24.2, "body_fat_avg": 33.0, "weight_avg": 60.5, "height_avg": 158.0},
            {"age_group": "55-59", "gender": "여성", "grip_strength_avg": 21.0,
             "sit_ups_avg": 8, "flexibility_avg": 10.0, "shuttle_run_avg": 12,
             "bmi_avg": 24.5, "body_fat_avg": 34.0, "weight_avg": 60.0, "height_avg": 157.0},
            {"age_group": "60-64", "gender": "여성", "grip_strength_avg": 19.5,
             "sit_ups_avg": 6, "flexibility_avg": 9.0, "shuttle_run_avg": 10,
             "bmi_avg": 24.8, "body_fat_avg": 35.0, "weight_avg": 59.5, "height_avg": 155.5},
        ],
        "generated_at": datetime.now().isoformat(),
        "source": "국민체력100 기준치 참고 (데모 데이터)",
    }

    return demo_data


def main():
    parser = argparse.ArgumentParser(description="국민체력100 체력측정 데이터 수집")
    parser.add_argument("--demo", action="store_true", help="데모 데이터 생성")
    parser.add_argument("--max-pages", type=int, default=10, help="최대 페이지 수")
    args = parser.parse_args()

    ensure_dirs()

    print("=" * 60)
    print("🏃 국민체력100 체력측정 데이터 수집")
    print("=" * 60)

    if args.demo:
        data = generate_demo_fitness_data()
    else:
        if not check_api_key("DATA_GO_KR_API_KEY", DATA_GO_KR_API_KEY):
            print("\n💡 --demo 옵션으로 기준치 데이터를 생성할 수 있습니다.")
            return

        all_items = []
        for page in range(1, args.max_pages + 1):
            print(f"  페이지 {page} 수집 중...")
            result = fetch_fitness100_data(DATA_GO_KR_API_KEY, num_of_rows=100, page_no=page)
            if not result:
                break

            body = result.get("response", {}).get("body", {})
            items = body.get("items", {}).get("item", [])
            if not items:
                break

            all_items.extend(items)
            total = body.get("totalCount", 0)
            print(f"    → {len(items)}건 (전체 {total}건)")

            if len(all_items) >= total:
                break
            time.sleep(0.5)

        data = {
            "items": all_items,
            "total_count": len(all_items),
            "collected_at": datetime.now().isoformat(),
            "source": "공공데이터포털 국민체력100 API",
        }

    output_path = OUTPUT_FILES["fitness100"]
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 저장 완료: {output_path}")
    print("✨ 국민체력100 데이터 수집 완료!")


if __name__ == "__main__":
    main()

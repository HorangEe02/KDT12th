"""
process_knhanes.py
KNHANES(국민건강영양조사) 원시자료를 전처리하여
연령/성별별 신체 통계 테이블을 생성합니다.

KNHANES 원시자료 다운로드:
    1. https://knhanes.kdca.go.kr 회원가입
    2. 건강설문조사 > 원시자료 이용안내 > 다운로드 신청
    3. 승인 후 CSV/SAS/SPSS 파일 다운로드
    4. CSV 파일을 data/knhanes/ 폴더에 저장

사용법:
    python scripts/process_knhanes.py --input data/knhanes/HN_ALL.csv
    python scripts/process_knhanes.py --demo  # 원시자료 없이 통계 테이블 생성

출력:
    data/user_samples/knhanes_body_stats.json — 연령/성별별 신체 통계

이 데이터는 Stage 1 프로필 분석에서 "같은 연령대 대비 백분위" 기능에 사용됩니다.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config import OUTPUT_FILES, ensure_dirs


# ═══════════════════════════════════════
# KNHANES 변수명 매핑
# ═══════════════════════════════════════

# 건강검진 원시자료 주요 변수 (기수에 따라 변수명이 다를 수 있음)
KNHANES_COLUMNS = {
    "HE_age": "age",                    # 만나이
    "sex": "gender",                     # 성별 (1=남, 2=여)
    "HE_ht": "height_cm",              # 신장 (cm)
    "HE_wt": "weight_kg",              # 체중 (kg)
    "HE_BMI": "bmi",                    # BMI
    "HE_wc": "waist_cm",               # 허리둘레 (cm)
    "HE_sbp": "systolic_bp",           # 수축기 혈압
    "HE_dbp": "diastolic_bp",          # 이완기 혈압
    "HE_glu": "fasting_glucose",       # 공복혈당
    "HE_chol": "total_cholesterol",    # 총콜레스테롤
    "HE_HDL_st2": "hdl_cholesterol",   # HDL 콜레스테롤
    "HE_TG": "triglyceride",           # 중성지방
    "HE_HbA1c": "hba1c",              # 당화혈색소
}

AGE_GROUPS = [
    (19, 24, "19-24"),
    (25, 29, "25-29"),
    (30, 34, "30-34"),
    (35, 39, "35-39"),
    (40, 44, "40-44"),
    (45, 49, "45-49"),
    (50, 54, "50-54"),
    (55, 59, "55-59"),
    (60, 64, "60-64"),
    (65, 69, "65-69"),
    (70, 100, "70+"),
]


def process_knhanes_csv(csv_path: str) -> dict:
    """
    KNHANES CSV 원시자료를 처리하여 연령/성별별 통계를 산출합니다.

    Args:
        csv_path: KNHANES CSV 파일 경로

    Returns:
        연령/성별별 통계 딕셔너리
    """
    import pandas as pd
    import numpy as np

    print(f"  📂 파일 로드 중: {csv_path}")
    df = pd.read_csv(csv_path, encoding="cp949", low_memory=False)
    print(f"  → {len(df)}행 x {len(df.columns)}열 로드")

    # 변수명 매핑 (존재하는 컬럼만)
    rename_map = {}
    for orig, new in KNHANES_COLUMNS.items():
        if orig in df.columns:
            rename_map[orig] = new
    df = df.rename(columns=rename_map)

    # 성별 변환
    if "gender" in df.columns:
        df["gender"] = df["gender"].map({1: "남성", 2: "여성"})

    # 성인만 필터링 (19세 이상)
    if "age" in df.columns:
        df = df[df["age"] >= 19].copy()

    # 연령대 그룹 생성
    def _get_age_group(age):
        for low, high, label in AGE_GROUPS:
            if low <= age <= high:
                return label
        return None

    df["age_group"] = df["age"].apply(_get_age_group)

    # 통계 산출 대상 변수
    stat_cols = ["height_cm", "weight_kg", "bmi", "waist_cm",
                 "systolic_bp", "diastolic_bp", "fasting_glucose",
                 "total_cholesterol", "hdl_cholesterol", "triglyceride"]
    stat_cols = [c for c in stat_cols if c in df.columns]

    stats = {}
    for gender in ["남성", "여성"]:
        stats[gender] = {}
        df_gender = df[df["gender"] == gender]

        for _, (low, high, age_label) in enumerate(AGE_GROUPS):
            df_group = df_gender[df_gender["age_group"] == age_label]
            if len(df_group) < 10:
                continue

            group_stats = {"sample_size": len(df_group)}
            for col in stat_cols:
                series = df_group[col].dropna()
                if len(series) < 5:
                    continue
                group_stats[col] = {
                    "mean": round(float(series.mean()), 1),
                    "std": round(float(series.std()), 1),
                    "median": round(float(series.median()), 1),
                    "p25": round(float(series.quantile(0.25)), 1),
                    "p75": round(float(series.quantile(0.75)), 1),
                    "p10": round(float(series.quantile(0.10)), 1),
                    "p90": round(float(series.quantile(0.90)), 1),
                    "min": round(float(series.min()), 1),
                    "max": round(float(series.max()), 1),
                }

            stats[gender][age_label] = group_stats

    return {
        "statistics": stats,
        "source": f"KNHANES 원시자료 ({csv_path})",
        "processed_at": datetime.now().isoformat(),
        "total_records": len(df),
        "stat_columns": stat_cols,
    }


def generate_demo_knhanes_stats() -> dict:
    """
    KNHANES 원시자료 없이 한국인 신체 통계 데모 데이터를 생성합니다.
    (대한비만학회, 질병관리청 공개 통계 기반 추정치)
    """
    print("📦 데모 모드: 한국인 연령/성별별 신체 통계를 생성합니다.")

    stats = {
        "남성": {
            "19-24": {"sample_size": 500, "height_cm": {"mean": 174.2, "std": 5.8, "p25": 170.5, "p75": 178.0},
                      "weight_kg": {"mean": 72.3, "std": 12.5, "p25": 64.0, "p75": 80.0},
                      "bmi": {"mean": 23.8, "std": 3.8, "p25": 21.2, "p75": 26.0},
                      "waist_cm": {"mean": 80.5, "std": 9.8, "p25": 74.0, "p75": 87.0}},
            "25-29": {"sample_size": 480, "height_cm": {"mean": 174.5, "std": 5.6, "p25": 170.8, "p75": 178.2},
                      "weight_kg": {"mean": 76.1, "std": 13.2, "p25": 67.0, "p75": 84.0},
                      "bmi": {"mean": 25.0, "std": 4.0, "p25": 22.3, "p75": 27.2},
                      "waist_cm": {"mean": 84.2, "std": 10.5, "p25": 77.0, "p75": 91.0}},
            "30-34": {"sample_size": 520, "height_cm": {"mean": 174.0, "std": 5.5, "p25": 170.5, "p75": 177.5},
                      "weight_kg": {"mean": 77.5, "std": 12.8, "p25": 69.0, "p75": 85.0},
                      "bmi": {"mean": 25.6, "std": 3.9, "p25": 23.0, "p75": 27.8},
                      "waist_cm": {"mean": 86.0, "std": 10.2, "p25": 79.0, "p75": 93.0}},
            "35-39": {"sample_size": 510, "height_cm": {"mean": 173.5, "std": 5.5, "p25": 170.0, "p75": 177.0},
                      "weight_kg": {"mean": 78.0, "std": 12.0, "p25": 70.0, "p75": 85.0},
                      "bmi": {"mean": 25.9, "std": 3.5, "p25": 23.5, "p75": 28.0},
                      "waist_cm": {"mean": 87.5, "std": 9.8, "p25": 81.0, "p75": 94.0}},
            "40-44": {"sample_size": 490, "height_cm": {"mean": 172.8, "std": 5.6, "p25": 169.0, "p75": 176.5},
                      "weight_kg": {"mean": 76.5, "std": 11.5, "p25": 69.0, "p75": 83.0},
                      "bmi": {"mean": 25.6, "std": 3.3, "p25": 23.5, "p75": 27.5},
                      "waist_cm": {"mean": 87.0, "std": 9.5, "p25": 80.5, "p75": 93.0}},
            "45-49": {"sample_size": 500, "height_cm": {"mean": 172.0, "std": 5.7, "p25": 168.5, "p75": 175.5},
                      "weight_kg": {"mean": 74.8, "std": 11.0, "p25": 67.5, "p75": 81.5},
                      "bmi": {"mean": 25.3, "std": 3.2, "p25": 23.2, "p75": 27.2},
                      "waist_cm": {"mean": 86.5, "std": 9.0, "p25": 80.0, "p75": 92.5}},
            "50-54": {"sample_size": 480, "height_cm": {"mean": 171.0, "std": 5.8, "p25": 167.5, "p75": 174.5},
                      "weight_kg": {"mean": 73.0, "std": 10.5, "p25": 66.0, "p75": 79.5},
                      "bmi": {"mean": 24.9, "std": 3.0, "p25": 23.0, "p75": 26.8},
                      "waist_cm": {"mean": 86.0, "std": 8.8, "p25": 80.0, "p75": 92.0}},
            "55-59": {"sample_size": 470, "height_cm": {"mean": 170.0, "std": 5.9, "p25": 166.5, "p75": 173.5},
                      "weight_kg": {"mean": 71.0, "std": 10.2, "p25": 64.0, "p75": 77.5},
                      "bmi": {"mean": 24.6, "std": 3.0, "p25": 22.8, "p75": 26.5},
                      "waist_cm": {"mean": 85.5, "std": 8.5, "p25": 79.5, "p75": 91.0}},
            "60-64": {"sample_size": 460, "height_cm": {"mean": 168.5, "std": 6.0, "p25": 165.0, "p75": 172.0},
                      "weight_kg": {"mean": 69.0, "std": 10.0, "p25": 62.5, "p75": 75.0},
                      "bmi": {"mean": 24.3, "std": 3.0, "p25": 22.5, "p75": 26.2},
                      "waist_cm": {"mean": 85.0, "std": 8.5, "p25": 79.0, "p75": 90.5}},
        },
        "여성": {
            "19-24": {"sample_size": 520, "height_cm": {"mean": 162.3, "std": 5.2, "p25": 159.0, "p75": 165.5},
                      "weight_kg": {"mean": 56.8, "std": 9.5, "p25": 50.0, "p75": 62.0},
                      "bmi": {"mean": 21.6, "std": 3.5, "p25": 19.5, "p75": 23.5},
                      "waist_cm": {"mean": 72.0, "std": 8.5, "p25": 66.0, "p75": 77.0}},
            "25-29": {"sample_size": 500, "height_cm": {"mean": 162.0, "std": 5.3, "p25": 158.8, "p75": 165.2},
                      "weight_kg": {"mean": 58.0, "std": 10.0, "p25": 51.5, "p75": 63.5},
                      "bmi": {"mean": 22.1, "std": 3.7, "p25": 19.8, "p75": 24.2},
                      "waist_cm": {"mean": 73.5, "std": 9.0, "p25": 67.0, "p75": 79.0}},
            "30-34": {"sample_size": 510, "height_cm": {"mean": 161.5, "std": 5.2, "p25": 158.5, "p75": 164.5},
                      "weight_kg": {"mean": 59.2, "std": 10.5, "p25": 52.0, "p75": 65.0},
                      "bmi": {"mean": 22.7, "std": 3.8, "p25": 20.2, "p75": 25.0},
                      "waist_cm": {"mean": 75.0, "std": 9.5, "p25": 68.5, "p75": 81.0}},
            "35-39": {"sample_size": 500, "height_cm": {"mean": 161.0, "std": 5.1, "p25": 158.0, "p75": 164.0},
                      "weight_kg": {"mean": 60.0, "std": 10.0, "p25": 53.0, "p75": 66.0},
                      "bmi": {"mean": 23.1, "std": 3.6, "p25": 20.8, "p75": 25.5},
                      "waist_cm": {"mean": 76.5, "std": 9.2, "p25": 70.0, "p75": 82.5}},
            "40-44": {"sample_size": 490, "height_cm": {"mean": 160.0, "std": 5.2, "p25": 157.0, "p75": 163.0},
                      "weight_kg": {"mean": 60.5, "std": 9.8, "p25": 54.0, "p75": 66.5},
                      "bmi": {"mean": 23.6, "std": 3.5, "p25": 21.2, "p75": 26.0},
                      "waist_cm": {"mean": 78.0, "std": 9.0, "p25": 72.0, "p75": 84.0}},
            "45-49": {"sample_size": 500, "height_cm": {"mean": 159.0, "std": 5.3, "p25": 156.0, "p75": 162.0},
                      "weight_kg": {"mean": 61.0, "std": 9.5, "p25": 54.5, "p75": 67.0},
                      "bmi": {"mean": 24.1, "std": 3.4, "p25": 21.8, "p75": 26.5},
                      "waist_cm": {"mean": 79.5, "std": 9.0, "p25": 73.0, "p75": 85.5}},
            "50-54": {"sample_size": 480, "height_cm": {"mean": 158.0, "std": 5.4, "p25": 155.0, "p75": 161.0},
                      "weight_kg": {"mean": 60.5, "std": 9.0, "p25": 54.0, "p75": 66.5},
                      "bmi": {"mean": 24.2, "std": 3.3, "p25": 22.0, "p75": 26.5},
                      "waist_cm": {"mean": 80.5, "std": 8.8, "p25": 74.5, "p75": 86.0}},
            "55-59": {"sample_size": 470, "height_cm": {"mean": 157.0, "std": 5.5, "p25": 154.0, "p75": 160.0},
                      "weight_kg": {"mean": 60.0, "std": 9.0, "p25": 54.0, "p75": 66.0},
                      "bmi": {"mean": 24.3, "std": 3.2, "p25": 22.2, "p75": 26.5},
                      "waist_cm": {"mean": 81.0, "std": 8.5, "p25": 75.0, "p75": 86.5}},
            "60-64": {"sample_size": 460, "height_cm": {"mean": 155.5, "std": 5.6, "p25": 152.5, "p75": 158.5},
                      "weight_kg": {"mean": 59.5, "std": 9.0, "p25": 53.5, "p75": 65.0},
                      "bmi": {"mean": 24.6, "std": 3.2, "p25": 22.5, "p75": 26.8},
                      "waist_cm": {"mean": 82.0, "std": 8.5, "p25": 76.0, "p75": 87.5}},
        },
    }

    return {
        "statistics": stats,
        "source": "KNHANES 공개 보고서 기반 추정치 (데모 데이터)",
        "note": "실제 분석에는 knhanes.kdca.go.kr에서 원시자료 다운로드 필요",
        "processed_at": datetime.now().isoformat(),
        "usage": {
            "percentile_lookup": "특정 사용자의 키/체중/BMI가 같은 연령대에서 어디에 위치하는지 계산",
            "example": "30대 남성이 BMI 26이면 → p25(23.0)~p75(27.8) 범위 내 → '평균 범위'",
        },
    }


def get_percentile_position(value: float, stats: dict) -> str:
    """
    특정 값이 분포에서 어디에 위치하는지 설명합니다.

    Args:
        value: 측정값
        stats: {"mean", "std", "p10", "p25", "p75", "p90"} 딕셔너리

    Returns:
        위치 설명 문자열
    """
    if "p10" in stats and value <= stats["p10"]:
        return "하위 10% 이내"
    elif "p25" in stats and value <= stats["p25"]:
        return "하위 25% 이내"
    elif "p75" in stats and value <= stats["p75"]:
        return "평균 범위 (25~75%)"
    elif "p90" in stats and value <= stats["p90"]:
        return "상위 25% 이내"
    else:
        return "상위 10% 이내"


def main():
    parser = argparse.ArgumentParser(description="KNHANES 원시자료 전처리")
    parser.add_argument("--input", type=str, help="KNHANES CSV 파일 경로")
    parser.add_argument("--demo", action="store_true", help="데모 통계 데이터 생성")
    args = parser.parse_args()

    ensure_dirs()

    print("=" * 60)
    print("📊 KNHANES 국민건강영양조사 데이터 처리")
    print("=" * 60)

    if args.demo or not args.input:
        if not args.demo and not args.input:
            print("⚠️ --input 또는 --demo 옵션을 지정해주세요.")
            print("   --demo: 통계 기준 데모 데이터 생성")
            print("   --input data/knhanes/HN_ALL.csv: 원시자료 처리")
            print("\n💡 KNHANES 원시자료 다운로드: https://knhanes.kdca.go.kr")
        data = generate_demo_knhanes_stats()
    else:
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"❌ 파일을 찾을 수 없습니다: {input_path}")
            print("   KNHANES 원시자료를 다운로드하여 해당 경로에 저장해주세요.")
            return
        data = process_knhanes_csv(str(input_path))

    output_path = OUTPUT_FILES["knhanes_stats"]
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 저장 완료: {output_path}")
    print("✨ KNHANES 데이터 처리 완료!")


if __name__ == "__main__":
    main()

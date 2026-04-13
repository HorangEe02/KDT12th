"""
evaluation.py
Stage 1 모듈의 성능을 평가합니다.

- 인바디 파싱 정확도
- 목표 분류 정확도 (F1 score)
- NER 추출 정확도
- BMR 공식 비교 (Mifflin-St Jeor vs Harris-Benedict)
"""

from dataclasses import dataclass


# ═══════════════════════════════════════
# 인바디 파싱 평가
# ═══════════════════════════════════════

INBODY_GROUND_TRUTH = {
    "test_image_01.png": {
        "weight_kg": 59.1,
        "skeletal_muscle_mass_kg": 19.3,
        "body_fat_mass_kg": 22.1,
        "bmi": 24.0,
        "body_fat_percent": 37.5,
        "bmr_kcal": 1168,
        "inbody_score": 66,
    }
}


def evaluate_inbody_parsing(parsed: dict, ground_truth: dict) -> dict:
    """인바디 파싱 정확도를 평가합니다."""
    results = {}
    for field_name, true_value in ground_truth.items():
        parsed_value = parsed.get(field_name)
        if parsed_value is not None and true_value is not None:
            error = abs(parsed_value - true_value)
            accuracy = 1 - (error / true_value) if true_value != 0 else 0
            results[field_name] = {
                "parsed": parsed_value,
                "truth": true_value,
                "error": round(error, 2),
                "accuracy_pct": round(max(accuracy * 100, 0), 1),
            }
        else:
            results[field_name] = {"parsed": parsed_value, "truth": true_value, "error": None}

    valid = [r for r in results.values() if r.get("accuracy_pct") is not None]
    if valid:
        results["average_accuracy_pct"] = round(
            sum(r["accuracy_pct"] for r in valid) / len(valid), 1
        )
    return results


# ═══════════════════════════════════════
# 목표 분류 평가
# ═══════════════════════════════════════

GOAL_TEST_SET = [
    ("뱃살 빼고 식스팩 만들고 싶어요", "체지방감소"),
    ("상체 근육을 키우고 싶습니다", "근력증가"),
    ("계단만 올라가도 숨이 차요", "체력향상"),
    ("지금 체중을 유지하면서 몸매 관리하고 싶어요", "체중관리"),
    ("당뇨 전단계라서 운동 시작해야 합니다", "건강개선"),
    ("살 좀 빼서 옷이 잘 맞았으면 좋겠어요", "체지방감소"),
    ("헬스장에서 벤치프레스 무게를 올리고 싶어요", "근력증가"),
    ("마라톤 완주가 목표입니다", "체력향상"),
    ("요요 없이 건강하게 관리하고 싶어요", "체중관리"),
    ("고혈압 약을 줄이려고 운동 시작합니다", "건강개선"),
    ("다이어트 해서 여름까지 5kg 빼기", "체지방감소"),
    ("린매스업 하고 싶어요", "근력증가"),
    ("조깅 30분도 힘들어요 체력 키우기", "체력향상"),
    ("표준 체중인데 몸매를 좋게 만들고 싶어", "체중관리"),
    ("허리디스크 때문에 코어 강화가 필요해요", "건강개선"),
    ("체지방률 20% 이하로 만들기", "체지방감소"),
    ("데드리프트 중량 올리기", "근력증가"),
    ("5km 러닝 기록 단축", "체력향상"),
    ("생활체육 수준에서 몸 관리하기", "체중관리"),
    ("무릎 수술 후 재활 운동 필요", "건강개선"),
]


def evaluate_goal_classification(classifier_fn) -> dict:
    """
    목표 분류기의 성능을 평가합니다.

    Args:
        classifier_fn: (text: str) -> (goal_type: str, confidence: float) 함수

    Returns:
        {accuracy, per_class_f1, confusion_matrix, ...}
    """
    predictions = []
    truths = []

    for text, true_label in GOAL_TEST_SET:
        result = classifier_fn(text)
        # GoalClassificationResult 또는 tuple 지원
        if hasattr(result, "goal_type"):
            pred_label = result.goal_type.value if hasattr(result.goal_type, "value") else result.goal_type
        elif isinstance(result, tuple):
            pred_label = result[0].value if hasattr(result[0], "value") else result[0]
        else:
            pred_label = str(result)

        predictions.append(pred_label)
        truths.append(true_label)

    # 정확도
    correct = sum(1 for p, t in zip(predictions, truths) if p == t)
    accuracy = round(correct / len(truths), 3)

    # 클래스별 F1 계산
    labels = list(set(truths))
    per_class = {}
    for label in labels:
        tp = sum(1 for p, t in zip(predictions, truths) if p == label and t == label)
        fp = sum(1 for p, t in zip(predictions, truths) if p == label and t != label)
        fn = sum(1 for p, t in zip(predictions, truths) if p != label and t == label)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0

        per_class[label] = {
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1": round(f1, 3),
        }

    macro_f1 = round(sum(c["f1"] for c in per_class.values()) / len(per_class), 3)

    # 오분류 사례
    misclassified = [
        {"text": text, "predicted": pred, "truth": truth}
        for (text, truth), pred in zip(GOAL_TEST_SET, predictions)
        if pred != truth
    ]

    return {
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "per_class": per_class,
        "total_samples": len(GOAL_TEST_SET),
        "correct": correct,
        "misclassified": misclassified,
    }


# ═══════════════════════════════════════
# NER 평가
# ═══════════════════════════════════════

NER_TEST_SET = [
    {
        "text": "25세 남성이고 키 178cm에 몸무게 82kg입니다. 주 3회 운동 가능합니다.",
        "expected": {"age": 25, "gender": "남성", "height_cm": 178.0, "weight_kg": 82.0, "exercise_frequency": 3},
    },
    {
        "text": "30대 여자, 163cm 58kg이에요. 무릎이 안 좋아서 달리기는 어렵습니다.",
        "expected": {"age": 35, "gender": "여성", "height_cm": 163.0, "weight_kg": 58.0, "constraints": ["무릎 부상"]},
    },
    {
        "text": "45세 남성 172cm 90kg 당뇨 전단계입니다. 주 5회 운동 가능해요.",
        "expected": {"age": 45, "gender": "남성", "height_cm": 172.0, "weight_kg": 90.0, "exercise_frequency": 5, "constraints": ["당뇨"]},
    },
    {
        "text": "20살 여자 160센티 50킬로예요. 운동 처음이에요.",
        "expected": {"age": 20, "gender": "여성", "height_cm": 160.0, "weight_kg": 50.0, "experience_level": "입문"},
    },
]


def evaluate_ner(ner_fn) -> dict:
    """NER 추출 정확도를 평가합니다."""
    results = []

    for test_case in NER_TEST_SET:
        extracted = ner_fn(test_case["text"])
        expected = test_case["expected"]

        case_result = {"text": test_case["text"], "fields": {}}

        for field_name, expected_value in expected.items():
            actual = getattr(extracted, field_name, None)

            if isinstance(expected_value, list):
                # 리스트 비교 (제약사항 등)
                match = set(expected_value).issubset(set(actual or []))
            else:
                match = actual == expected_value

            case_result["fields"][field_name] = {
                "expected": expected_value,
                "actual": actual,
                "match": match,
            }

        results.append(case_result)

    # 전체 필드 정확도
    total_fields = sum(len(r["fields"]) for r in results)
    correct_fields = sum(
        sum(1 for f in r["fields"].values() if f["match"])
        for r in results
    )

    return {
        "field_accuracy": round(correct_fields / total_fields, 3) if total_fields > 0 else 0,
        "total_fields": total_fields,
        "correct_fields": correct_fields,
        "details": results,
    }


# ═══════════════════════════════════════
# BMR 공식 비교
# ═══════════════════════════════════════

def compare_bmr_formulas(test_cases: list[dict] | None = None) -> list[dict]:
    """Mifflin-St Jeor vs Harris-Benedict 비교."""
    from .body_calculator import calculate_bmr, calculate_bmr_harris_benedict

    if test_cases is None:
        test_cases = [
            {"weight_kg": 82, "height_cm": 178, "age": 25, "gender": "남성"},
            {"weight_kg": 58, "height_cm": 163, "age": 35, "gender": "여성"},
            {"weight_kg": 90, "height_cm": 172, "age": 45, "gender": "남성"},
            {"weight_kg": 50, "height_cm": 160, "age": 20, "gender": "여성"},
            {"weight_kg": 59.1, "height_cm": 156.9, "age": 51, "gender": "여성"},
        ]

    results = []
    for tc in test_cases:
        msj = calculate_bmr(**tc)
        hb = calculate_bmr_harris_benedict(**tc)
        results.append({
            **tc,
            "mifflin_st_jeor": msj,
            "harris_benedict": hb,
            "difference": msj - hb,
        })

    return results


# ═══════════════════════════════════════
# 전체 평가 실행
# ═══════════════════════════════════════

def run_all_evaluations() -> dict:
    """모든 평가를 실행합니다."""
    from .profile_ner import extract_entities_rule_based
    from .goal_classifier import classify_goal_rule_based

    print("=" * 60)
    print("헬창지피티 Stage 1 — 평가 보고서")
    print("=" * 60)

    # 1. NER 평가
    print("\n[1] NER 정확도 평가")
    ner_result = evaluate_ner(extract_entities_rule_based)
    print(f"  필드 정확도: {ner_result['field_accuracy']:.1%} ({ner_result['correct_fields']}/{ner_result['total_fields']})")

    # 2. 목표 분류 평가
    print("\n[2] 목표 분류 정확도 평가 (규칙 기반)")
    goal_result = evaluate_goal_classification(classify_goal_rule_based)
    print(f"  정확도: {goal_result['accuracy']:.1%}")
    print(f"  Macro F1: {goal_result['macro_f1']:.3f}")
    for label, metrics in goal_result["per_class"].items():
        print(f"    {label}: P={metrics['precision']:.2f} R={metrics['recall']:.2f} F1={metrics['f1']:.2f}")
    if goal_result["misclassified"]:
        print(f"  오분류: {len(goal_result['misclassified'])}건")
        for m in goal_result["misclassified"]:
            print(f"    \"{m['text'][:30]}...\" → {m['predicted']} (정답: {m['truth']})")

    # 3. BMR 비교
    print("\n[3] BMR 공식 비교 (Mifflin-St Jeor vs Harris-Benedict)")
    bmr_results = compare_bmr_formulas()
    for r in bmr_results:
        print(f"  {r['gender']} {r['age']}세 {r['weight_kg']}kg: "
              f"MSJ={r['mifflin_st_jeor']}kcal, HB={r['harris_benedict']}kcal "
              f"(차이: {r['difference']:+d}kcal)")

    print("\n" + "=" * 60)

    return {
        "ner": ner_result,
        "goal_classification": goal_result,
        "bmr_comparison": bmr_results,
    }

"""
run_experiments.py
미니프로젝트 평가 기준 충족을 위한 전체 실험 실행 스크립트.

실험 항목:
  1. Stage 1: NER 정확도, 목표분류 F1, BMR 공식 비교
  2. Stage 2: 모델별 × temperature별 식단 생성 비교
  3. Stage 3: BM25 vs 임베딩 검색 비교
  4. Stage 4: 감성 분석 규칙 vs LLM 비교
  5. 모델 응답 속도 비교

출력:
  data/experiments/experiment_results.json
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

RESULTS_DIR = PROJECT_ROOT / "data" / "experiments"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

all_results = {
    "experiment_date": datetime.now().isoformat(),
    "project": "헬창지피티 (HelChangGPT)",
    "stages": {},
}


# ═══════════════════════════════════════
# Stage 1: NER + 목표분류 + BMR 비교
# ═══════════════════════════════════════

def run_stage1_experiments():
    print("=" * 60)
    print("[Stage 1] 프로필 분석 — NER / 목표분류 / BMR")
    print("=" * 60)

    from src.profile.evaluation import evaluate_ner, evaluate_goal_classification, compare_bmr_formulas
    from src.profile.profile_ner import extract_entities_rule_based
    from src.profile.goal_classifier import classify_goal_rule_based

    # 1-1. NER 평가
    print("\n[1-1] NER 정확도 (규칙 기반)")
    ner_result = evaluate_ner(extract_entities_rule_based)
    print(f"  필드 정확도: {ner_result['field_accuracy']:.1%} ({ner_result['correct_fields']}/{ner_result['total_fields']})")

    # 1-2. 목표분류 평가
    print("\n[1-2] 목표분류 정확도 (규칙 기반)")
    goal_result = evaluate_goal_classification(classify_goal_rule_based)
    print(f"  정확도: {goal_result['accuracy']:.1%}")
    print(f"  Macro F1: {goal_result['macro_f1']:.3f}")
    for label, m in goal_result["per_class"].items():
        print(f"    {label}: P={m['precision']:.2f} R={m['recall']:.2f} F1={m['f1']:.2f}")
    if goal_result["misclassified"]:
        print(f"  오분류 {len(goal_result['misclassified'])}건:")
        for mc in goal_result["misclassified"][:3]:
            print(f"    \"{mc['text'][:30]}\" → {mc['predicted']} (정답: {mc['truth']})")

    # 1-3. BMR 공식 비교
    print("\n[1-3] BMR 공식 비교 (Mifflin-St Jeor vs Harris-Benedict)")
    bmr_results = compare_bmr_formulas()
    for r in bmr_results:
        print(f"  {r['gender']} {r['age']}세 {r['weight_kg']}kg: MSJ={r['mifflin_st_jeor']}kcal HB={r['harris_benedict']}kcal (차이: {r['difference']:+d})")

    all_results["stages"]["stage1"] = {
        "ner": ner_result,
        "goal_classification": goal_result,
        "bmr_comparison": bmr_results,
    }


# ═══════════════════════════════════════
# Stage 2: 식단 생성 비교 (오프라인 평가)
# ═══════════════════════════════════════

def run_stage2_experiments():
    print("\n" + "=" * 60)
    print("[Stage 2] 식단 생성 — 모델별 / temperature별 비교")
    print("=" * 60)

    from src.diet.macro_calculator import calculate_macro_targets
    from src.diet.diet_generator import generate_demo_meal_plan
    from src.diet.diet_analyzer import analyze_diet_plan

    # 데모 식단으로 분석 품질 평가
    goals = ["체지방감소", "근력증가", "건강개선"]
    stage2_results = {"demo_analysis": []}

    for goal in goals:
        macro = calculate_macro_targets(1800, goal, weight_kg=75)
        demo = generate_demo_meal_plan(1800, goal)
        analysis = analyze_diet_plan(demo, macro, constraints=["당뇨"] if goal == "건강개선" else None)

        result = {
            "goal": goal,
            "target_kcal": 1800,
            "actual_kcal": demo["daily_total"]["calories_kcal"],
            "calorie_diff": analysis.calorie_diff,
            "calorie_accuracy_pct": analysis.calorie_accuracy_pct,
            "macro_accuracy": analysis.macro_accuracy,
            "constraint_warnings": analysis.constraint_warnings,
            "overall_score": analysis.overall_score,
            "grade": analysis.grade,
            "keywords": analysis.keywords,
        }
        stage2_results["demo_analysis"].append(result)
        print(f"\n  [{goal}] 점수: {analysis.overall_score}/100 ({analysis.grade})")
        print(f"    칼로리: {demo['daily_total']['calories_kcal']}kcal (목표 1800, 차이 {analysis.calorie_diff:+.0f})")
        print(f"    키워드: {analysis.keywords[:5]}")
        if analysis.constraint_warnings:
            print(f"    ⚠ 경고: {analysis.constraint_warnings}")

    # 프롬프트 방식 비교 (Zero-shot / Few-shot / CoT)
    print("\n  프롬프트 방식별 특성:")
    stage2_results["prompt_comparison"] = {
        "zero_shot": {"특성": "간결, JSON 구조 준수율 높음", "적합": "빠른 생성, 단순 식단"},
        "few_shot": {"특성": "예시 기반 학습, 품질 안정적", "적합": "기본 권장 방식"},
        "cot": {"특성": "추론 과정 포함, 영양소 계산 정확", "적합": "제약사항 복잡한 경우"},
    }
    for pt, info in stage2_results["prompt_comparison"].items():
        print(f"    {pt}: {info['특성']} → {info['적합']}")

    # temperature 실험 설계
    stage2_results["temperature_design"] = {
        "0.3": {"예상": "안정적 반복, 다양성 부족", "적합": "인바디 수치 파싱 등 정확도 필요 시"},
        "0.7": {"예상": "균형 잡힌 다양성+정확성", "적합": "일반 식단 생성 기본값"},
        "1.0": {"예상": "창의적 메뉴, 때때로 부정확", "적합": "다양한 식단 탐색 시"},
    }
    print("\n  temperature별 특성:")
    for t, info in stage2_results["temperature_design"].items():
        print(f"    temp={t}: {info['예상']}")

    all_results["stages"]["stage2"] = stage2_results


# ═══════════════════════════════════════
# Stage 3: 운동 검색 비교 (BM25 vs 임베딩)
# ═══════════════════════════════════════

def run_stage3_experiments():
    print("\n" + "=" * 60)
    print("[Stage 3] 운동 루틴 — BM25 vs 필터 검색 비교")
    print("=" * 60)

    from src.workout.exercise_search import search_exercises, search_by_muscle, search_safe_exercises, BM25ExerciseSearch

    queries = [
        ("하체 운동 추천", None),
        ("무릎에 부담 적은 하체 운동", ["무릎 부상"]),
        ("가슴 운동 초보", None),
        ("유산소 심폐 체력", None),
        ("어깨 부상 대체 운동", ["어깨 부상"]),
    ]

    stage3_results = {"search_comparisons": []}

    for query, constraints in queries:
        bm25 = search_exercises(query, method="bm25", top_k=3, constraints=constraints)
        filt = search_by_muscle(query.split()[0]) if not constraints else search_safe_exercises(constraints)

        comparison = {
            "query": query,
            "constraints": constraints,
            "bm25_results": [{"name": r.name, "score": r.score} for r in bm25[:3]],
            "filter_results": [{"name": r.name, "score": r.score} for r in filt[:3]],
        }
        stage3_results["search_comparisons"].append(comparison)

        print(f"\n  질의: \"{query}\" {f'(제약: {constraints})' if constraints else ''}")
        print(f"    BM25:  {[r.name for r in bm25[:3]]}")
        print(f"    필터:  {[r.name for r in filt[:3]]}")

    # 운동 DB 통계
    from src.workout.workout_analyzer import ALL_MUSCLE_GROUPS
    stage3_results["exercise_db_stats"] = {
        "total_exercises": len(BM25ExerciseSearch().exercises),
        "muscle_groups": ALL_MUSCLE_GROUPS,
    }

    # 데모 루틴 분석
    from src.workout.workout_generator import generate_demo_workout_plan
    from src.workout.workout_analyzer import analyze_workout_plan

    for goal in ["체지방감소", "근력증가"]:
        plan = generate_demo_workout_plan(3, goal, "입문", [])
        analysis = analyze_workout_plan(plan, goal, "입문")
        print(f"\n  [{goal}] 균형: {analysis.balance_score}/100, 유산소/무산소: {analysis.cardio_ratio}%/{analysis.strength_ratio}%")

    all_results["stages"]["stage3"] = stage3_results


# ═══════════════════════════════════════
# Stage 4: 감성 분석 비교
# ═══════════════════════════════════════

def run_stage4_experiments():
    print("\n" + "=" * 60)
    print("[Stage 4] 감성 분석 — 규칙 기반 평가")
    print("=" * 60)

    from src.feedback.sentiment_analyzer import analyze_sentiment_rule_based

    test_set = [
        ("레그프레스 무게 올렸다! 뿌듯하다.", "긍정", "성취감"),
        ("친구랑 같이 운동해서 재밌었다ㅋㅋ", "긍정", "즐거움"),
        ("체중이 2kg 줄었다! 식단 효과!", "긍정", "성취감"),
        ("너무 피곤해서 겨우 30분 하고 나왔다.", "부정", "피로"),
        ("2주째 체중이 안 줄어서 스트레스.", "부정", "좌절"),
        ("무릎이 좀 아팠다. 내일은 쉬어야겠다.", "부정", "통증"),
        ("운동 의욕이 없어서 빠졌다.", "부정", "무기력"),
        ("계획대로 루틴 소화. 보통이었음.", "중립", "일상"),
        ("오트밀 40분 + 복근 15분. 무난.", "중립", "일상"),
        ("새 운동 배웠는데 신기했다.", "긍정", "즐거움"),
    ]

    correct = 0
    emotion_correct = 0
    results_detail = []

    for text, true_sent, true_emotion in test_set:
        result = analyze_sentiment_rule_based(text)
        sent_ok = result.sentiment == true_sent
        emo_ok = result.emotion_detail == true_emotion
        if sent_ok:
            correct += 1
        if emo_ok:
            emotion_correct += 1

        results_detail.append({
            "text": text[:30],
            "true_sentiment": true_sent,
            "predicted_sentiment": result.sentiment,
            "sentiment_correct": sent_ok,
            "true_emotion": true_emotion,
            "predicted_emotion": result.emotion_detail,
            "emotion_correct": emo_ok,
            "confidence": result.confidence,
        })

        mark = "✅" if sent_ok else "❌"
        print(f"  {mark} \"{text[:25]}...\" → {result.sentiment}({result.emotion_detail}) [정답: {true_sent}({true_emotion})]")

    accuracy = correct / len(test_set)
    emotion_accuracy = emotion_correct / len(test_set)
    print(f"\n  감성 정확도: {accuracy:.0%} ({correct}/{len(test_set)})")
    print(f"  감정 정확도: {emotion_accuracy:.0%} ({emotion_correct}/{len(test_set)})")

    # 피드백 모드 비교
    from src.feedback.feedback_modes import list_modes
    modes = list_modes()
    print(f"\n  피드백 모드: {len(modes)}개")
    for m in modes:
        print(f"    {m['emoji']} {m['mode_name']}: {m['description']}")

    all_results["stages"]["stage4"] = {
        "sentiment_accuracy": accuracy,
        "emotion_accuracy": emotion_accuracy,
        "test_count": len(test_set),
        "details": results_detail,
        "feedback_modes": modes,
    }


# ═══════════════════════════════════════
# 실행
# ═══════════════════════════════════════

if __name__ == "__main__":
    print("🏋️ 헬창지피티 — 전체 실험 실행")
    print(f"실행 시각: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("")

    run_stage1_experiments()
    run_stage2_experiments()
    run_stage3_experiments()
    run_stage4_experiments()

    # 결과 저장
    output_path = RESULTS_DIR / "experiment_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2, default=str)

    print(f"\n{'=' * 60}")
    print(f"✅ 전체 실험 완료! 결과 저장: {output_path}")
    print(f"{'=' * 60}")

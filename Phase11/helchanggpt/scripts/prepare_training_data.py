"""
prepare_training_data.py
NLP 모델 학습 데이터를 포맷 변환하고 분할합니다.

1. 목표 분류 학습 데이터 → HuggingFace Dataset 형식 변환
2. 운동 일지 감성 분석 샘플 생성
3. Train/Validation/Test 분할
4. 클래스 분포 검증

사용법:
    python scripts/prepare_training_data.py
    python scripts/prepare_training_data.py --split-ratio 0.8 0.1 0.1
    python scripts/prepare_training_data.py --stats-only

출력:
    data/user_samples/goal_classification_train.json
    data/user_samples/goal_classification_val.json
    data/user_samples/goal_classification_test.json
    data/diary_samples/diary_samples.json
"""

import argparse
import json
import random
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config import OUTPUT_FILES, ensure_dirs


# ═══════════════════════════════════════
# 운동 일지 감성 샘플 데이터
# ═══════════════════════════════════════

DIARY_SAMPLES = [
    # ── 긍정 (30개) ──
    {"text": "오늘 레그프레스 4세트 했는데 생각보다 잘 됐다! 무릎도 안 아프고 무게도 조금 올렸다.", "sentiment": "긍정", "emotion": "성취감"},
    {"text": "친구랑 같이 운동했더니 재밌었다. 푸쉬업 15개 연속 성공! 점점 체력이 느는 것 같다.", "sentiment": "긍정", "emotion": "자신감"},
    {"text": "벤치프레스 60kg 성공! 한 달 전만 해도 50kg이 한계였는데 확실히 늘고 있다.", "sentiment": "긍정", "emotion": "성취감"},
    {"text": "런닝 30분 완주했다. 처음 시작했을 때는 10분도 힘들었는데 이제 숨이 덜 찬다.", "sentiment": "긍정", "emotion": "성취감"},
    {"text": "오늘 운동 끝나고 거울 보니까 어깨가 좀 넓어진 것 같아서 기분 좋았다.", "sentiment": "긍정", "emotion": "자신감"},
    {"text": "식단도 잘 지키고 운동도 열심히 했다. 이번 주는 완벽한 주간이었다!", "sentiment": "긍정", "emotion": "만족"},
    {"text": "데드리프트 자세를 교정했더니 훨씬 안정감 있게 들 수 있었다.", "sentiment": "긍정", "emotion": "성취감"},
    {"text": "요가 수업 다녀왔는데 유연성이 많이 좋아진 게 느껴진다.", "sentiment": "긍정", "emotion": "만족"},
    {"text": "체중이 2kg 줄었다! 식단 관리 효과가 드디어 나타나기 시작했다.", "sentiment": "긍정", "emotion": "성취감"},
    {"text": "같이 운동하는 형이 근육 많이 붙었다고 칭찬해줬다. 뿌듯하다.", "sentiment": "긍정", "emotion": "자신감"},
    {"text": "오늘 HIIT 마지막 세트까지 포기 안 하고 완주했다. 나 자신이 대견하다.", "sentiment": "긍정", "emotion": "자부심"},
    {"text": "스쿼트 자세가 많이 안정됐다. 거울로 보면서 하니까 확실히 다르다.", "sentiment": "긍정", "emotion": "성취감"},
    {"text": "아침 운동 습관이 생겨서 컨디션이 하루 종일 좋다.", "sentiment": "긍정", "emotion": "활력"},
    {"text": "수영 1km 완주! 처음으로 쉬지 않고 끝까지 갔다.", "sentiment": "긍정", "emotion": "성취감"},
    {"text": "운동 시작한 지 3개월, 인바디 점수가 10점 올랐다.", "sentiment": "긍정", "emotion": "성취감"},

    # ── 부정 (30개) ──
    {"text": "너무 피곤해서 운동 의욕이 없었다. 겨우 30분 하고 나왔다.", "sentiment": "부정", "emotion": "피로"},
    {"text": "오늘 무릎이 좀 아팠다. 스쿼트를 하려다가 포기하고 상체만 했다.", "sentiment": "부정", "emotion": "좌절"},
    {"text": "체중이 안 줄어서 스트레스 받는다. 식단도 지키고 있는데 왜 안 빠지지.", "sentiment": "부정", "emotion": "좌절"},
    {"text": "헬스장 가기 싫었는데 억지로 갔다. 집중도 안 되고 대충 하고 나왔다.", "sentiment": "부정", "emotion": "무기력"},
    {"text": "벤치프레스 하다가 어깨가 결렸다. 자세가 잘못된 것 같은데 어떻게 해야 할지 모르겠다.", "sentiment": "부정", "emotion": "불안"},
    {"text": "식단을 깨고 야식 먹어버렸다. 자기 통제가 안 되니까 자괴감 든다.", "sentiment": "부정", "emotion": "자괴감"},
    {"text": "2주째 체중 변화가 없다. 이러다 포기할 것 같다.", "sentiment": "부정", "emotion": "좌절"},
    {"text": "다른 사람들은 금방 몸 좋아지던데 나는 왜 이렇게 느리지.", "sentiment": "부정", "emotion": "비교"},
    {"text": "오늘 컨디션 최악이었다. 평소 하던 무게도 못 들었다.", "sentiment": "부정", "emotion": "피로"},
    {"text": "허리가 계속 뻐근하다. 운동하면 안 되는 건가 걱정된다.", "sentiment": "부정", "emotion": "불안"},
    {"text": "운동 시작한 지 한 달인데 아무 변화가 없는 것 같다.", "sentiment": "부정", "emotion": "실망"},
    {"text": "비 오고 날씨 우중충해서 그냥 쉬었다. 자책감이 든다.", "sentiment": "부정", "emotion": "자괴감"},
    {"text": "목 디스크가 재발한 것 같다. 당분간 운동 쉬어야 할 듯.", "sentiment": "부정", "emotion": "좌절"},
    {"text": "야근 때문에 또 운동을 빠졌다. 이번 주 3번 째 빠짐.", "sentiment": "부정", "emotion": "무기력"},
    {"text": "식단 맞추느라 맛없는 것만 먹으니까 스트레스가 쌓인다.", "sentiment": "부정", "emotion": "스트레스"},

    # ── 중립 (20개) ──
    {"text": "오늘은 상체 위주로 운동했다. 벤치프레스, 랫풀다운, 바이셉컬.", "sentiment": "중립", "emotion": "일상"},
    {"text": "40분 정도 러닝하고 스트레칭 10분 했다.", "sentiment": "중립", "emotion": "일상"},
    {"text": "하체 데이. 스쿼트 4세트, 레그프레스 3세트, 런지 3세트 했다.", "sentiment": "중립", "emotion": "일상"},
    {"text": "점심에 닭가슴살 200g, 현미밥, 브로콜리 먹었다.", "sentiment": "중립", "emotion": "일상"},
    {"text": "유산소 30분 + 복근 운동 15분으로 마무리했다.", "sentiment": "중립", "emotion": "일상"},
    {"text": "오늘 운동 시간이 부족해서 30분만 빡세게 했다.", "sentiment": "중립", "emotion": "일상"},
    {"text": "새로운 운동 영상 보고 따라해봤다. 내일 근육통이 올 것 같다.", "sentiment": "중립", "emotion": "기대"},
    {"text": "친구가 같이 운동하자고 해서 일정 조율 중이다.", "sentiment": "중립", "emotion": "일상"},
    {"text": "프로틴 다 떨어져서 주문했다. 초코맛으로 바꿔봤다.", "sentiment": "중립", "emotion": "일상"},
    {"text": "내일부터 새로운 루틴으로 바꿔볼 예정이다.", "sentiment": "중립", "emotion": "일상"},
]


def load_goal_classification_data() -> list[dict]:
    """goal_classifier_bert.py의 시드 데이터를 로드합니다."""
    # 직접 import 대신 하드코딩된 경로에서 로드 시도
    seed_path = OUTPUT_FILES["training_goal_classification"]
    if seed_path.exists():
        with open(seed_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # 없으면 goal_classifier_bert.py에서 import
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        from profile.goal_classifier_bert import TRAINING_SAMPLES, LABEL_TO_ID
        return [
            {"text": text, "label": label, "label_id": LABEL_TO_ID[label]}
            for text, label in TRAINING_SAMPLES
        ]
    except ImportError:
        print("⚠️ 시드 데이터를 찾을 수 없습니다.")
        return []


def split_dataset(
    data: list[dict],
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    test_ratio: float = 0.1,
    seed: int = 42,
) -> tuple[list, list, list]:
    """데이터를 train/val/test로 분할합니다."""
    random.seed(seed)
    shuffled = data.copy()
    random.shuffle(shuffled)

    n = len(shuffled)
    train_end = int(n * train_ratio)
    val_end = train_end + int(n * val_ratio)

    return shuffled[:train_end], shuffled[train_end:val_end], shuffled[val_end:]


def print_class_distribution(data: list[dict], label_key: str = "label"):
    """클래스 분포를 출력합니다."""
    counter = Counter(item[label_key] for item in data)
    total = sum(counter.values())
    for label, count in sorted(counter.items()):
        pct = round(count / total * 100, 1)
        bar = "█" * int(pct / 2)
        print(f"    {label:12s}: {count:4d} ({pct:5.1f}%) {bar}")


def main():
    parser = argparse.ArgumentParser(description="학습 데이터 준비")
    parser.add_argument("--split-ratio", nargs=3, type=float, default=[0.8, 0.1, 0.1],
                        help="train/val/test 비율 (기본: 0.8 0.1 0.1)")
    parser.add_argument("--stats-only", action="store_true", help="통계만 출력")
    parser.add_argument("--seed", type=int, default=42, help="랜덤 시드")
    args = parser.parse_args()

    ensure_dirs()

    print("=" * 60)
    print("📚 NLP 학습 데이터 준비")
    print("=" * 60)

    # ── 1. 목표 분류 데이터 ──
    print("\n[1] 운동 목표 분류 데이터")
    goal_data = load_goal_classification_data()

    if goal_data:
        print(f"  총 {len(goal_data)}개 샘플")
        print("  클래스 분포:")
        print_class_distribution(goal_data)

        if not args.stats_only:
            train, val, test = split_dataset(
                goal_data,
                train_ratio=args.split_ratio[0],
                val_ratio=args.split_ratio[1],
                test_ratio=args.split_ratio[2],
                seed=args.seed,
            )

            splits = {
                "train": (train, OUTPUT_FILES["training_goal_classification"]),
                "val": (val, OUTPUT_FILES["training_goal_classification"].parent / "goal_classification_val.json"),
                "test": (test, OUTPUT_FILES["training_goal_classification"].parent / "goal_classification_test.json"),
            }

            for split_name, (split_data, path) in splits.items():
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(split_data, f, ensure_ascii=False, indent=2)
                print(f"  ✅ {split_name}: {len(split_data)}개 → {path.name}")
    else:
        print("  ⚠️ 데이터 없음 — 먼저 goal_classifier_bert.py의 시드 데이터를 생성해주세요.")

    # ── 2. 운동 일지 감성 분석 데이터 ──
    print(f"\n[2] 운동 일지 감성 분석 데이터")
    print(f"  총 {len(DIARY_SAMPLES)}개 샘플")
    print("  감성 분포:")
    print_class_distribution(DIARY_SAMPLES, "sentiment")
    print("  세부 감정 분포:")
    print_class_distribution(DIARY_SAMPLES, "emotion")

    if not args.stats_only:
        diary_output = {
            "samples": DIARY_SAMPLES,
            "total_count": len(DIARY_SAMPLES),
            "sentiment_distribution": dict(Counter(d["sentiment"] for d in DIARY_SAMPLES)),
            "emotion_distribution": dict(Counter(d["emotion"] for d in DIARY_SAMPLES)),
            "generated_at": datetime.now().isoformat(),
            "usage": "Stage 4 감성 분석 학습/평가 데이터",
        }

        with open(OUTPUT_FILES["training_diary_samples"], "w", encoding="utf-8") as f:
            json.dump(diary_output, f, ensure_ascii=False, indent=2)
        print(f"  ✅ 저장: {OUTPUT_FILES['training_diary_samples']}")

    # ── 3. 데이터 품질 요약 ──
    print(f"\n{'=' * 60}")
    print("📊 데이터 품질 요약")
    print(f"{'=' * 60}")
    print(f"  목표 분류 데이터:  {len(goal_data)}개 (권장: 500개 이상)")
    print(f"  운동 일지 데이터:  {len(DIARY_SAMPLES)}개 (권장: 200개 이상)")

    if len(goal_data) < 500:
        deficit = 500 - len(goal_data)
        print(f"\n  💡 목표 분류 데이터 {deficit}개 추가 필요:")
        print(f"     → goal_classifier_bert.py의 TRAINING_SAMPLES에 데이터 추가")
        print(f"     → 또는 data/user_samples/goal_classification_train.json 직접 편집")

    if len(DIARY_SAMPLES) < 200:
        deficit = 200 - len(DIARY_SAMPLES)
        print(f"  💡 운동 일지 데이터 {deficit}개 추가 필요:")
        print(f"     → 이 스크립트의 DIARY_SAMPLES에 데이터 추가")

    print("\n✨ 학습 데이터 준비 완료!")


if __name__ == "__main__":
    main()

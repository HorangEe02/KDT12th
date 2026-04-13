"""
goal_classifier_bert.py
KcBERT 기반 운동 목표 분류기.

KcBERT(beomi/KcBERT-base)를 5개 운동 목표 클래스로 파인튜닝합니다.
구어체/비격식체 입력에 강점이 있어 사용자 입력 분류에 적합합니다.

사용법:
    1. 학습: train_goal_classifier() 함수로 모델 학습
    2. 추론: KcBERTGoalClassifier 클래스로 분류
"""

import json
from dataclasses import dataclass
from pathlib import Path

from .goal_classifier import GoalType, GoalClassificationResult


@dataclass
class TrainingConfig:
    """파인튜닝 설정"""
    model_name: str = "beomi/KcBERT-base"
    num_labels: int = 5
    max_length: int = 128
    batch_size: int = 16
    learning_rate: float = 2e-5
    num_epochs: int = 5
    warmup_ratio: float = 0.1
    weight_decay: float = 0.01
    output_dir: str = "./models/goal_classifier"


# 라벨 매핑
LABEL_MAP = {
    0: GoalType.FAT_LOSS,
    1: GoalType.MUSCLE_GAIN,
    2: GoalType.FITNESS,
    3: GoalType.WEIGHT_MGMT,
    4: GoalType.HEALTH,
}

LABEL_TO_ID = {v.value: k for k, v in LABEL_MAP.items()}


# ═══════════════════════════════════════
# 학습 데이터 샘플 (팀원이 확장해야 함)
# ═══════════════════════════════════════

TRAINING_SAMPLES = [
    # 체지방감소 (20개 시드 데이터)
    ("뱃살 빼고 식스팩 만들고 싶어요", "체지방감소"),
    ("살 좀 빼서 옷이 잘 맞았으면 좋겠어요", "체지방감소"),
    ("다이어트 하려고 운동 시작합니다", "체지방감소"),
    ("체지방률 20% 이하로 만들고 싶어요", "체지방감소"),
    ("군살 없는 탄탄한 몸을 만들고 싶어요", "체지방감소"),
    ("출산 후 살이 너무 쪄서 다이어트 해야돼요", "체지방감소"),
    ("뱃살이 너무 나와서 줄이고 싶어요", "체지방감소"),
    ("체중 10kg 감량이 목표입니다", "체지방감소"),
    ("얼굴살 빼고 싶어요 턱선 만들고 싶어", "체지방감소"),
    ("쪄서 바지가 안 맞아요 살빼야해요", "체지방감소"),
    ("커팅 시작하려고요 체지방 줄이기", "체지방감소"),
    ("하체 살이 많아서 빼고 싶어요", "체지방감소"),
    ("옆구리 살 좀 빼는 방법 알려주세요", "체지방감소"),
    ("웨딩 앞두고 다이어트 중입니다", "체지방감소"),
    ("몸무게 70에서 60으로 줄이고 싶어요", "체지방감소"),
    ("날씬해지고 싶어서 운동 시작했어요", "체지방감소"),
    ("뚱뚱한게 너무 싫어요 살빼고싶어", "체지방감소"),
    ("지방을 태우는 운동 알려주세요", "체지방감소"),
    ("체지방 30%에서 20%로 줄이기", "체지방감소"),
    ("여름까지 배 나온 거 없애고 싶어요", "체지방감소"),

    # 근력증가 (20개)
    ("상체 근육을 키우고 싶습니다", "근력증가"),
    ("벤치프레스 100kg이 목표예요", "근력증가"),
    ("벌크업 중인데 식단 조언 부탁드려요", "근력증가"),
    ("근비대를 위한 운동 프로그램 짜주세요", "근력증가"),
    ("팔뚝 두꺼워지고 싶어요", "근력증가"),
    ("어깨가 넓어지면 좋겠어요", "근력증가"),
    ("덩치를 좀 키우고 싶습니다", "근력증가"),
    ("헬스장에서 무게 올리는 게 목표예요", "근력증가"),
    ("근육량 늘려서 몸 좀 만들고 싶어", "근력증가"),
    ("스쿼트 중량 올리고 싶습니다", "근력증가"),
    ("웨이트 트레이닝으로 몸 키우기", "근력증가"),
    ("마른 체형이라 좀 키우고 싶어요", "근력증가"),
    ("데드리프트 자세 잡고 무게 올리기", "근력증가"),
    ("근손실 없이 벌크업하고 싶어요", "근력증가"),
    ("가슴근육 키우는 운동 추천해주세요", "근력증가"),
    ("3개월 안에 눈에 띄게 몸 키우기", "근력증가"),
    ("보디빌딩 시작하려고 합니다", "근력증가"),
    ("프로틴 먹으면서 근육 키우기", "근력증가"),
    ("상체 하체 밸런스 맞추면서 키우기", "근력증가"),
    ("린매스업 하고 싶어요", "근력증가"),

    # 체력향상 (20개)
    ("계단만 올라가도 숨이 차요", "체력향상"),
    ("마라톤 완주가 목표입니다", "체력향상"),
    ("기초 체력을 올리고 싶어요", "체력향상"),
    ("오래 달릴 수 있는 체력을 만들고 싶어", "체력향상"),
    ("운동하면 금방 지쳐요 체력 키우기", "체력향상"),
    ("스태미나를 높이고 싶습니다", "체력향상"),
    ("일상에서 활력이 부족해요", "체력향상"),
    ("에너지가 없어서 쉽게 피곤해져요", "체력향상"),
    ("5km 러닝 기록 단축이 목표", "체력향상"),
    ("조깅 30분도 힘들어요", "체력향상"),
    ("지구력 키워서 등산 잘 하고 싶어", "체력향상"),
    ("축구 90분 뛸 체력이 필요해요", "체력향상"),
    ("출퇴근만 해도 녹초가 돼요", "체력향상"),
    ("컨디션 관리를 잘 하고 싶어요", "체력향상"),
    ("하루 종일 서서 일하는데 체력이 부족", "체력향상"),
    ("운동 능력 전반적으로 올리기", "체력향상"),
    ("수영 1km 완주가 목표입니다", "체력향상"),
    ("놀이공원 하루 돌아다닐 체력도 없어요", "체력향상"),
    ("등산 정상까지 안 힘들게 올라가기", "체력향상"),
    ("기초체력 테스트 통과해야해요", "체력향상"),

    # 체중관리 (20개)
    ("지금 체중을 유지하면서 몸매를 다듬고 싶어요", "체중관리"),
    ("요요 없이 건강하게 관리하고 싶어요", "체중관리"),
    ("적정 체중인데 몸매를 좋게 만들고 싶어", "체중관리"),
    ("현재 상태 유지하면서 탄력 있는 몸", "체중관리"),
    ("살 빼기보다는 몸매 관리 목적이에요", "체중관리"),
    ("표준 체중인데 더 좋은 몸을 만들고 싶어", "체중관리"),
    ("몸무게는 괜찮은데 체형이 마음에 안 들어요", "체중관리"),
    ("건강한 상태를 꾸준히 유지하고 싶어요", "체중관리"),
    ("생활체육 수준에서 몸 관리하기", "체중관리"),
    ("다이어트 성공 후 유지 중입니다", "체중관리"),
    ("몸매 유지하면서 건강하게 먹고 싶어", "체중관리"),
    ("지금 체중 적당한데 탄탄하게 만들기", "체중관리"),
    ("꾸준히 운동하면서 현재 상태 유지", "체중관리"),
    ("몸무게 변동 없이 안정적으로 관리", "체중관리"),
    ("라인 예쁘게 만들고 싶어요", "체중관리"),
    ("특별히 살 빼거나 키울 건 아닌데 관리", "체중관리"),
    ("운동 습관 들이면서 건강 유지하기", "체중관리"),
    ("노화 방지 차원에서 몸 관리하기", "체중관리"),
    ("균형 잡힌 몸을 만들고 싶습니다", "체중관리"),
    ("적당히 운동하면서 살 안 찌게 관리", "체중관리"),

    # 건강개선 (20개)
    ("당뇨 전단계라서 운동 시작해야 합니다", "건강개선"),
    ("고혈압 약을 줄이려고 운동 시작합니다", "건강개선"),
    ("무릎 수술 후 재활 운동 필요해요", "건강개선"),
    ("허리디스크 때문에 코어 강화가 필요합니다", "건강개선"),
    ("건강검진에서 콜레스테롤 높다고 나왔어요", "건강개선"),
    ("혈당 관리를 위해 운동하려고 해요", "건강개선"),
    ("관절이 약해서 강화 운동이 필요합니다", "건강개선"),
    ("만성 피로를 개선하고 싶어요", "건강개선"),
    ("의사가 운동하라고 해서 시작합니다", "건강개선"),
    ("수술 후 체력 회복이 필요합니다", "건강개선"),
    ("어깨가 자주 아파서 재활 필요해요", "건강개선"),
    ("혈압약 먹는데 운동으로 줄이고 싶어", "건강개선"),
    ("건강 문제로 운동 시작하려고 합니다", "건강개선"),
    ("폐활량이 약해서 심폐 기능 개선 필요", "건강개선"),
    ("골밀도 낮다고 해서 운동 해야 합니다", "건강개선"),
    ("통풍 있는데 운동 어떻게 해야 하나요", "건강개선"),
    ("당뇨약 먹는 중인데 운동 병행하려고요", "건강개선"),
    ("허리 아파서 일상생활도 힘들어요", "건강개선"),
    ("회전근개 손상 후 재활 운동이요", "건강개선"),
    ("건강이 나빠져서 운동으로 회복하고 싶어요", "건강개선"),
]


class KcBERTGoalClassifier:
    """
    KcBERT 기반 운동 목표 분류기.

    사전 학습된 모델이 있으면 로드하고,
    없으면 rule-based 분류로 폴백합니다.
    """

    def __init__(self, model_path: str | None = None):
        self.model = None
        self.tokenizer = None
        self.model_path = model_path

        if model_path and Path(model_path).exists():
            self._load_model(model_path)

    def _load_model(self, model_path: str) -> None:
        """학습된 모델을 로드합니다."""
        try:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
            self.model.eval()
        except Exception:
            self.model = None
            self.tokenizer = None

    def classify(self, text: str) -> GoalClassificationResult:
        """
        운동 목표를 분류합니다.
        모델이 없으면 rule-based로 폴백합니다.
        """
        if self.model is None or self.tokenizer is None:
            from .goal_classifier import classify_goal_rule_based
            return classify_goal_rule_based(text)

        import torch

        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=128,
        )

        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1)[0]

        pred_idx = probs.argmax().item()
        goal_type = LABEL_MAP[pred_idx]
        confidence = round(probs[pred_idx].item(), 3)

        return GoalClassificationResult(
            goal_type=goal_type,
            confidence=confidence,
            method="kcbert",
            reason=f"KcBERT 분류 (확률: {confidence:.1%})",
        )


def create_training_dataset(
    samples: list[tuple[str, str]] | None = None,
    output_path: str = "./data/user_samples/goal_classification_train.json",
) -> None:
    """
    학습 데이터를 JSON 파일로 저장합니다.

    Args:
        samples: (텍스트, 라벨) 튜플 리스트. None이면 기본 샘플 사용
        output_path: 저장 경로
    """
    if samples is None:
        samples = TRAINING_SAMPLES

    data = [
        {"text": text, "label": label, "label_id": LABEL_TO_ID[label]}
        for text, label in samples
    ]

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"학습 데이터 저장 완료: {output_path} ({len(data)}개)")


def train_goal_classifier(
    training_data_path: str = "./data/user_samples/goal_classification_train.json",
    config: TrainingConfig | None = None,
) -> str:
    """
    KcBERT를 운동 목표 분류기로 파인튜닝합니다.

    Args:
        training_data_path: 학습 데이터 JSON 경로
        config: 학습 설정

    Returns:
        학습된 모델 저장 경로

    Note:
        Google Colab에서 실행 권장 (GPU 필요)
    """
    if config is None:
        config = TrainingConfig()

    try:
        import torch
        from transformers import (
            AutoTokenizer,
            AutoModelForSequenceClassification,
            TrainingArguments,
            Trainer,
        )
        from torch.utils.data import Dataset
    except ImportError:
        raise ImportError(
            "transformers, torch 패키지가 필요합니다.\n"
            "pip install transformers torch"
        )

    # 데이터 로드
    with open(training_data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 토크나이저 & 모델
    tokenizer = AutoTokenizer.from_pretrained(config.model_name)
    model = AutoModelForSequenceClassification.from_pretrained(
        config.model_name, num_labels=config.num_labels
    )

    # 커스텀 Dataset
    class GoalDataset(Dataset):
        def __init__(self, items):
            self.items = items
            self.encodings = tokenizer(
                [item["text"] for item in items],
                padding=True,
                truncation=True,
                max_length=config.max_length,
                return_tensors="pt",
            )

        def __len__(self):
            return len(self.items)

        def __getitem__(self, idx):
            item = {k: v[idx] for k, v in self.encodings.items()}
            item["labels"] = torch.tensor(self.items[idx]["label_id"])
            return item

    # 80/20 분할
    split_idx = int(len(data) * 0.8)
    train_dataset = GoalDataset(data[:split_idx])
    eval_dataset = GoalDataset(data[split_idx:])

    # 학습 설정
    training_args = TrainingArguments(
        output_dir=config.output_dir,
        num_train_epochs=config.num_epochs,
        per_device_train_batch_size=config.batch_size,
        per_device_eval_batch_size=config.batch_size,
        learning_rate=config.learning_rate,
        warmup_ratio=config.warmup_ratio,
        weight_decay=config.weight_decay,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
    )

    trainer.train()
    trainer.save_model(config.output_dir)
    tokenizer.save_pretrained(config.output_dir)

    print(f"모델 저장 완료: {config.output_dir}")
    return config.output_dir

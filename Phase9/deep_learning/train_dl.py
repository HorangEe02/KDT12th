"""딥러닝 모델 학습 모듈.

CustomCNN, ResNet-18 fine-tune/feature extractor 모델의 학습,
평가, 실험 실행을 담당한다.
Adam + CosineAnnealingLR + Early Stopping 기반 학습 루프를 제공.
"""

import os
import sys
import copy
import time
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.optim import Adam
from torch.optim.lr_scheduler import CosineAnnealingLR
from typing import Optional, Callable

# 프로젝트 루트를 path에 추가
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


def get_device() -> torch.device:
    """사용 가능한 최적 디바이스 반환.

    MPS(Apple Silicon) > CUDA > CPU 순서로 탐색.

    Returns:
        torch.device 객체.
    """
    if torch.backends.mps.is_available() and torch.backends.mps.is_built():
        device = torch.device("mps")
        print(f"[Device] Apple MPS 가속 사용")
    elif torch.cuda.is_available():
        device = torch.device("cuda")
        print(f"[Device] CUDA 가속 사용: {torch.cuda.get_device_name(0)}")
    else:
        device = torch.device("cpu")
        print(f"[Device] CPU 사용")
    return device


def _to_device_safe(tensor: torch.Tensor, device: torch.device) -> torch.Tensor:
    """MPS 호환성을 고려한 안전한 디바이스 전송."""
    try:
        return tensor.to(device)
    except RuntimeError:
        # MPS에서 지원하지 않는 연산은 CPU로 폴백
        return tensor.to("cpu")


def train_one_epoch(
    model: nn.Module,
    loader,
    criterion: nn.Module,
    optimizer,
    device: torch.device,
    mixup_fn: Optional[Callable] = None,
) -> tuple[float, float]:
    """한 에포크 학습.

    Args:
        model: 학습할 모델.
        loader: 학습 DataLoader.
        criterion: 손실 함수.
        optimizer: 옵티마이저.
        device: 디바이스.
        mixup_fn: Mixup/CutMix 함수 (optional).

    Returns:
        (평균 손실, 정확도) 튜플.
    """
    model.train()
    total_loss = 0.0
    correct = 0
    total = 0

    for images, labels in loader:
        images = images.to(device)
        labels = labels.to(device)

        if mixup_fn is not None:
            images, soft_labels = mixup_fn(images, labels, num_classes=6)
            outputs = model(images)
            # 소프트 라벨에 대한 크로스엔트로피
            log_probs = torch.nn.functional.log_softmax(outputs, dim=1)
            loss = -(soft_labels * log_probs).sum(dim=1).mean()
            # 정확도는 원래 hard label 기준 (soft_labels에서 argmax)
            _, predicted = outputs.max(1)
            _, hard_labels = soft_labels.max(1)
            correct += predicted.eq(hard_labels).sum().item()
        else:
            outputs = model(images)
            loss = criterion(outputs, labels)
            _, predicted = outputs.max(1)
            correct += predicted.eq(labels).sum().item()

        total += labels.size(0)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * labels.size(0)

    avg_loss = total_loss / total
    accuracy = correct / total
    return avg_loss, accuracy


@torch.no_grad()
def evaluate_model(
    model: nn.Module,
    loader,
    criterion: nn.Module,
    device: torch.device,
) -> tuple[float, float, np.ndarray, np.ndarray, np.ndarray]:
    """모델 평가.

    Args:
        model: 평가할 모델.
        loader: 테스트 DataLoader.
        criterion: 손실 함수.
        device: 디바이스.

    Returns:
        (평균 손실, 정확도, y_true, y_pred, y_prob) 튜플.
        y_prob는 (N, num_classes) 확률 배열.
    """
    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0
    all_labels = []
    all_preds = []
    all_probs = []

    for images, labels in loader:
        images = images.to(device)
        labels = labels.to(device)

        outputs = model(images)
        loss = criterion(outputs, labels)

        # MPS에서 softmax가 문제될 수 있으므로 CPU로 이동
        probs = torch.softmax(outputs, dim=1).cpu().numpy()
        _, predicted = outputs.max(1)

        total_loss += loss.item() * labels.size(0)
        correct += predicted.eq(labels).sum().item()
        total += labels.size(0)

        all_labels.append(labels.cpu().numpy())
        all_preds.append(predicted.cpu().numpy())
        all_probs.append(probs)

    avg_loss = total_loss / total
    accuracy = correct / total
    y_true = np.concatenate(all_labels)
    y_pred = np.concatenate(all_preds)
    y_prob = np.concatenate(all_probs)

    return avg_loss, accuracy, y_true, y_pred, y_prob


def train_model(
    model: nn.Module,
    train_loader,
    test_loader,
    epochs: int = 50,
    lr: float = 1e-3,
    weight_decay: float = 1e-4,
    patience: int = 10,
    save_path: Optional[str] = None,
    model_name: str = "model",
    device: Optional[torch.device] = None,
    mixup_fn: Optional[Callable] = None,
) -> dict:
    """모델 학습 전체 루프.

    Adam + CosineAnnealingLR + Early Stopping 기반.

    Args:
        model: 학습할 모델.
        train_loader: 학습 DataLoader.
        test_loader: 검증 DataLoader.
        epochs: 최대 에포크 수.
        lr: 학습률.
        weight_decay: L2 정규화 강도.
        patience: Early Stopping 인내 에포크 수.
        save_path: 체크포인트 저장 경로. None이면 저장하지 않음.
        model_name: 모델 이름 (로깅용).
        device: 디바이스. None이면 자동 탐지.
        mixup_fn: Mixup/CutMix 함수 (optional).

    Returns:
        학습 히스토리 및 결과를 담은 딕셔너리:
        - history: {train_loss, val_loss, train_acc, val_acc} 리스트
        - best_accuracy: 최고 검증 정확도
        - best_epoch: 최고 정확도 달성 에포크
        - total_time: 총 학습 시간 (초)
        - y_true, y_pred, y_prob: 최종 평가 결과
    """
    if device is None:
        device = get_device()

    model = model.to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = Adam(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=lr,
        weight_decay=weight_decay,
    )
    scheduler = CosineAnnealingLR(optimizer, T_max=epochs, eta_min=lr * 0.01)

    # 학습 히스토리
    history = {
        "train_loss": [],
        "val_loss": [],
        "train_acc": [],
        "val_acc": [],
    }

    best_acc = 0.0
    best_epoch = 0
    best_state = None
    patience_counter = 0

    print(f"\n{'='*60}")
    print(f"학습 시작: {model_name}")
    print(f"{'='*60}")
    print(f"디바이스: {device}")
    print(f"에포크: {epochs}, LR: {lr}, Weight Decay: {weight_decay}")
    print(f"Early Stopping Patience: {patience}")
    print(f"{'='*60}")

    start_time = time.time()

    for epoch in range(1, epochs + 1):
        # 학습
        train_loss, train_acc = train_one_epoch(
            model, train_loader, criterion, optimizer, device, mixup_fn
        )

        # 검증
        val_loss, val_acc, _, _, _ = evaluate_model(
            model, test_loader, criterion, device
        )

        # 스케줄러 업데이트
        scheduler.step()

        # 히스토리 기록
        history["train_loss"].append(train_loss)
        history["val_loss"].append(val_loss)
        history["train_acc"].append(train_acc)
        history["val_acc"].append(val_acc)

        # 로깅
        current_lr = optimizer.param_groups[0]["lr"]
        print(
            f"[{epoch:3d}/{epochs}] "
            f"Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.4f} | "
            f"Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.4f} | "
            f"LR: {current_lr:.6f}"
        )

        # Best model 저장
        if val_acc > best_acc:
            best_acc = val_acc
            best_epoch = epoch
            best_state = copy.deepcopy(model.state_dict())
            patience_counter = 0
            print(f"  -> Best model 갱신! (Acc: {best_acc:.4f})")
        else:
            patience_counter += 1

        # Early Stopping 체크
        if patience_counter >= patience:
            print(f"\nEarly Stopping at epoch {epoch} (patience={patience})")
            break

    total_time = time.time() - start_time
    print(f"\n학습 완료: {total_time:.1f}초")
    print(f"최고 검증 정확도: {best_acc:.4f} (epoch {best_epoch})")

    # Best 모델 로드
    if best_state is not None:
        model.load_state_dict(best_state)

    # 최종 평가
    val_loss, val_acc, y_true, y_pred, y_prob = evaluate_model(
        model, test_loader, criterion, device
    )

    # 체크포인트 저장
    if save_path is not None:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        checkpoint = {
            "model_state_dict": model.state_dict(),
            "model_name": model_name,
            "best_accuracy": best_acc,
            "best_epoch": best_epoch,
            "history": history,
            "total_time": total_time,
        }
        torch.save(checkpoint, save_path)
        print(f"체크포인트 저장: {save_path}")

    return {
        "history": history,
        "best_accuracy": best_acc,
        "best_epoch": best_epoch,
        "total_time": total_time,
        "y_true": y_true,
        "y_pred": y_pred,
        "y_prob": y_prob,
        "model": model,
    }


def run_dl_experiments(
    data_dir: str,
    output_dir: str = "outputs/deep_learning",
) -> pd.DataFrame:
    """5가지 딥러닝 실험을 순차 실행.

    실험 목록:
        1. CustomCNN (scratch, no augmentation)
        2. ResNet-18 fine-tune (all layers)
        3. ResNet-18 feature extractor (frozen backbone)
        4. ResNet-18 fine-tune + OpenCV preprocessing
        5. ResNet-18 fine-tune + augmentation (flip, rotate, brightness)

    Args:
        data_dir: NEU-DET 데이터 디렉토리 경로.
        output_dir: 결과 저장 디렉토리.

    Returns:
        실험 결과 요약 DataFrame.
    """
    from deep_learning.datasets import get_dataloaders
    from deep_learning.augmentation import (
        get_train_transforms,
        get_test_transforms,
    )
    from deep_learning.models.custom_cnn import CustomCNN
    from deep_learning.models.resnet_transfer import (
        get_resnet18_finetune,
        get_resnet18_feature_extractor,
    )
    from sklearn.metrics import (
        accuracy_score, f1_score, precision_score, recall_score,
    )

    os.makedirs(output_dir, exist_ok=True)
    device = get_device()

    # --- 실험 정의 ---
    experiments = [
        {
            "name": "CustomCNN_scratch",
            "description": "CustomCNN (처음부터 학습, 증강 없음)",
            "model_fn": lambda: CustomCNN(num_classes=6),
            "num_channels": 1,
            "augment": False,
            "opencv_preprocess": False,
            "epochs": 50,
            "lr": 1e-3,
        },
        {
            "name": "ResNet18_finetune",
            "description": "ResNet-18 Fine-tune (전체 레이어 학습)",
            "model_fn": lambda: get_resnet18_finetune(num_classes=6),
            "num_channels": 3,
            "augment": False,
            "opencv_preprocess": False,
            "epochs": 30,
            "lr": 1e-4,
        },
        {
            "name": "ResNet18_feature_extractor",
            "description": "ResNet-18 Feature Extractor (백본 동결)",
            "model_fn": lambda: get_resnet18_feature_extractor(num_classes=6),
            "num_channels": 3,
            "augment": False,
            "opencv_preprocess": False,
            "epochs": 30,
            "lr": 1e-3,
        },
        {
            "name": "ResNet18_finetune_opencv",
            "description": "ResNet-18 Fine-tune + OpenCV 전처리",
            "model_fn": lambda: get_resnet18_finetune(num_classes=6),
            "num_channels": 3,
            "augment": False,
            "opencv_preprocess": True,
            "epochs": 30,
            "lr": 1e-4,
        },
        {
            "name": "ResNet18_finetune_augment",
            "description": "ResNet-18 Fine-tune + 데이터 증강",
            "model_fn": lambda: get_resnet18_finetune(num_classes=6),
            "num_channels": 3,
            "augment": True,
            "opencv_preprocess": False,
            "epochs": 30,
            "lr": 1e-4,
        },
    ]

    results = []

    for i, exp in enumerate(experiments, 1):
        print(f"\n{'#'*60}")
        print(f"# 실험 {i}/{len(experiments)}: {exp['description']}")
        print(f"{'#'*60}")

        # 변환 파이프라인 생성
        transform_train = get_train_transforms(
            augment=exp["augment"],
            opencv_preprocess=exp["opencv_preprocess"],
            num_channels=exp["num_channels"],
        )
        transform_test = get_test_transforms(num_channels=exp["num_channels"])

        # 데이터로더 생성
        train_loader, test_loader, class_names = get_dataloaders(
            data_dir=data_dir,
            batch_size=32,
            test_size=0.2,
            transform_train=transform_train,
            transform_test=transform_test,
            num_channels=exp["num_channels"],
        )

        # 모델 생성
        model = exp["model_fn"]()

        # 학습
        save_path = os.path.join(output_dir, f"{exp['name']}_best.pt")
        result = train_model(
            model=model,
            train_loader=train_loader,
            test_loader=test_loader,
            epochs=exp["epochs"],
            lr=exp["lr"],
            weight_decay=1e-4,
            patience=10,
            save_path=save_path,
            model_name=exp["name"],
            device=device,
        )

        # 메트릭 계산
        y_true = result["y_true"]
        y_pred = result["y_pred"]

        accuracy = accuracy_score(y_true, y_pred)
        f1_macro = f1_score(y_true, y_pred, average="macro")
        precision_macro = precision_score(y_true, y_pred, average="macro")
        recall_macro = recall_score(y_true, y_pred, average="macro")

        results.append({
            "experiment": exp["name"],
            "description": exp["description"],
            "accuracy": accuracy,
            "f1_macro": f1_macro,
            "precision_macro": precision_macro,
            "recall_macro": recall_macro,
            "best_epoch": result["best_epoch"],
            "total_time_sec": result["total_time"],
        })

        print(f"\n  Accuracy: {accuracy:.4f}")
        print(f"  F1 Macro: {f1_macro:.4f}")
        print(f"  Precision Macro: {precision_macro:.4f}")
        print(f"  Recall Macro: {recall_macro:.4f}")

    # 결과 요약
    summary_df = pd.DataFrame(results).set_index("experiment")

    # CSV 저장
    csv_path = os.path.join(output_dir, "experiment_summary.csv")
    summary_df.to_csv(csv_path)
    print(f"\n실험 요약 저장: {csv_path}")
    print("\n" + summary_df.to_string())

    return summary_df


if __name__ == "__main__":
    print("=" * 60)
    print("train_dl.py 스모크 테스트")
    print("=" * 60)

    # 디바이스 확인
    device = get_device()

    # 더미 데이터로 학습 루프 테스트
    from deep_learning.models.custom_cnn import CustomCNN

    model = CustomCNN(num_classes=6)

    # 더미 DataLoader 생성
    dummy_images = torch.randn(48, 1, 200, 200)
    dummy_labels = torch.randint(0, 6, (48,))
    dummy_dataset = torch.utils.data.TensorDataset(dummy_images, dummy_labels)
    train_loader = torch.utils.data.DataLoader(dummy_dataset, batch_size=16, shuffle=True)
    test_loader = torch.utils.data.DataLoader(dummy_dataset, batch_size=16, shuffle=False)

    # 짧은 학습 테스트
    result = train_model(
        model=model,
        train_loader=train_loader,
        test_loader=test_loader,
        epochs=3,
        lr=1e-3,
        patience=5,
        model_name="CustomCNN_test",
        device=device,
    )

    print(f"\n학습 결과:")
    print(f"  Best Accuracy: {result['best_accuracy']:.4f}")
    print(f"  Best Epoch: {result['best_epoch']}")
    print(f"  History 길이: {len(result['history']['train_loss'])}")
    print(f"  y_true shape: {result['y_true'].shape}")
    print(f"  y_pred shape: {result['y_pred'].shape}")
    print(f"  y_prob shape: {result['y_prob'].shape}")

    print("\ntrain_dl.py 스모크 테스트 완료")

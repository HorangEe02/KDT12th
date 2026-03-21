"""
Severstal DL 학습 — Stage 1 (이진) + Stage 2 (4종)

ResNet-18 전이 학습 및 Custom CNN 학습 파이프라인.
- 이진 분류: 정상(0) vs 비정상(1)
- 4종 분류: PS(0) / LS(1) / SS(2) / RD(3)
"""

import os
import sys
import time
import copy
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_device():
    """MPS > CUDA > CPU 자동 선택."""
    if torch.backends.mps.is_available():
        return torch.device("mps")
    elif torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


# ──────────────────────────────────────────────
# 학습 루프
# ──────────────────────────────────────────────
def train_one_epoch(model, loader, criterion, optimizer, device):
    model.train()
    total_loss = 0
    correct = 0
    total = 0

    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * images.size(0)
        _, preds = outputs.max(1)
        correct += preds.eq(labels).sum().item()
        total += images.size(0)

    return total_loss / total, correct / total


def evaluate(model, loader, criterion, device):
    model.eval()
    total_loss = 0
    correct = 0
    total = 0
    all_preds = []
    all_labels = []
    all_probs = []

    with torch.no_grad():
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            loss = criterion(outputs, labels)

            total_loss += loss.item() * images.size(0)
            probs = torch.softmax(outputs, dim=1)
            _, preds = outputs.max(1)
            correct += preds.eq(labels).sum().item()
            total += images.size(0)

            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
            all_probs.extend(probs.cpu().numpy())

    return (
        total_loss / total,
        correct / total,
        np.array(all_preds),
        np.array(all_labels),
        np.array(all_probs),
    )


def train_model(
    model,
    train_loader: DataLoader,
    test_loader: DataLoader,
    num_epochs: int = 30,
    lr: float = 0.001,
    patience: int = 7,
    save_path: Optional[str] = None,
    model_name: str = "model",
    device=None,
) -> Dict:
    """모델 학습 + Early Stopping + 체크포인트."""
    if device is None:
        device = get_device()

    model = model.to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=num_epochs)

    best_acc = 0
    best_model_state = None
    patience_counter = 0
    history = {"train_loss": [], "train_acc": [], "val_loss": [], "val_acc": []}

    print(f"\n{'='*60}")
    print(f"[{model_name}] 학습 시작 — device: {device}")
    print(f"  Epochs: {num_epochs}, LR: {lr}, Patience: {patience}")
    print(f"{'='*60}")

    t_start = time.time()

    for epoch in range(num_epochs):
        train_loss, train_acc = train_one_epoch(
            model, train_loader, criterion, optimizer, device
        )
        val_loss, val_acc, _, _, _ = evaluate(model, test_loader, criterion, device)
        scheduler.step()

        history["train_loss"].append(train_loss)
        history["train_acc"].append(train_acc)
        history["val_loss"].append(val_loss)
        history["val_acc"].append(val_acc)

        print(
            f"  Epoch {epoch+1:>3d}/{num_epochs} | "
            f"Train Loss: {train_loss:.4f} Acc: {train_acc:.4f} | "
            f"Val Loss: {val_loss:.4f} Acc: {val_acc:.4f}"
        )

        if val_acc > best_acc:
            best_acc = val_acc
            best_model_state = copy.deepcopy(model.state_dict())
            patience_counter = 0
            if save_path:
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                torch.save(best_model_state, save_path)
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"  ⚡ Early stopping at epoch {epoch+1}")
                break

    total_time = time.time() - t_start

    # Best 모델로 최종 평가
    if best_model_state:
        model.load_state_dict(best_model_state)
    _, final_acc, y_pred, y_true, y_prob = evaluate(
        model, test_loader, criterion, device
    )

    print(f"\n  최종 결과: Accuracy={final_acc:.4f}, 학습시간={total_time:.1f}s")

    return {
        "model_name": model_name,
        "model": model,
        "best_accuracy": best_acc,
        "final_accuracy": final_acc,
        "y_pred": y_pred,
        "y_true": y_true,
        "y_prob": y_prob,
        "history": history,
        "total_time": total_time,
    }


# ──────────────────────────────────────────────
# 실험 실행
# ──────────────────────────────────────────────
def run_binary_dl_experiments(
    patch_dir: str,
    save_dir: str,
    max_per_class: int = 5000,
    num_epochs: int = 20,
    batch_size: int = 32,
) -> Dict[str, Dict]:
    """Stage 1 이진 분류 DL 실험."""
    from deep_learning.datasets_severstal import get_binary_dataloaders
    from deep_learning.models.resnet_transfer import (
        get_resnet18_finetune,
        get_resnet18_feature_extractor,
    )

    device = get_device()
    results = {}

    print(f"\n{'#'*60}")
    print(f"Stage 1: 정상 vs 비정상 이진 분류 — DL 실험")
    print(f"{'#'*60}")

    # DataLoader
    train_loader, test_loader, class_names = get_binary_dataloaders(
        patch_dir, max_per_class=max_per_class, batch_size=batch_size,
        target_size=224, to_rgb=True,
    )

    # 실험 1: ResNet-18 Fine-tune
    model_ft = get_resnet18_finetune(num_classes=2)
    r = train_model(
        model_ft, train_loader, test_loader,
        num_epochs=num_epochs, lr=0.0001, patience=5,
        save_path=os.path.join(save_dir, "binary_resnet18_finetune.pt"),
        model_name="ResNet-18 Fine-tune (Binary)", device=device,
    )
    results["ResNet18_Finetune"] = r

    # 실험 2: ResNet-18 Feature Extractor
    model_fe = get_resnet18_feature_extractor(num_classes=2)
    r = train_model(
        model_fe, train_loader, test_loader,
        num_epochs=num_epochs, lr=0.001, patience=5,
        save_path=os.path.join(save_dir, "binary_resnet18_feature_extractor.pt"),
        model_name="ResNet-18 Feature Extractor (Binary)", device=device,
    )
    results["ResNet18_FeatureExtractor"] = r

    # 결과 요약
    print(f"\n{'='*60}")
    print(f"{'모델':>35s} | {'Best Acc':>8s}")
    print(f"{'-'*60}")
    for name, r in results.items():
        print(f"{r['model_name']:>35s} | {r['best_accuracy']:>8.4f}")
    print(f"{'='*60}")

    return results


def run_defect4_dl_experiments(
    patch_dir: str,
    save_dir: str,
    max_per_class: Optional[int] = None,
    num_epochs: int = 30,
    batch_size: int = 32,
) -> Dict[str, Dict]:
    """Stage 2 4종 결함 분류 DL 실험."""
    from deep_learning.datasets_severstal import get_defect4_dataloaders
    from deep_learning.models.resnet_transfer import (
        get_resnet18_finetune,
        get_resnet18_feature_extractor,
    )

    device = get_device()
    results = {}

    print(f"\n{'#'*60}")
    print(f"Stage 2: 비정상 → 4종 결함 분류 — DL 실험")
    print(f"{'#'*60}")

    train_loader, test_loader, class_names = get_defect4_dataloaders(
        patch_dir, max_per_class=max_per_class, batch_size=batch_size,
        target_size=224, to_rgb=True,
    )

    # 실험 1: ResNet-18 Fine-tune
    model_ft = get_resnet18_finetune(num_classes=4)
    r = train_model(
        model_ft, train_loader, test_loader,
        num_epochs=num_epochs, lr=0.0001, patience=7,
        save_path=os.path.join(save_dir, "defect4_resnet18_finetune.pt"),
        model_name="ResNet-18 Fine-tune (Defect4)", device=device,
    )
    results["ResNet18_Finetune"] = r

    # 실험 2: ResNet-18 Feature Extractor
    model_fe = get_resnet18_feature_extractor(num_classes=4)
    r = train_model(
        model_fe, train_loader, test_loader,
        num_epochs=num_epochs, lr=0.001, patience=7,
        save_path=os.path.join(save_dir, "defect4_resnet18_feature_extractor.pt"),
        model_name="ResNet-18 Feature Extractor (Defect4)", device=device,
    )
    results["ResNet18_FeatureExtractor"] = r

    # 결과 요약
    print(f"\n{'='*60}")
    print(f"{'모델':>40s} | {'Best Acc':>8s}")
    print(f"{'-'*60}")
    for name, r in results.items():
        print(f"{r['model_name']:>40s} | {r['best_accuracy']:>8.4f}")
    print(f"{'='*60}")

    return results


# ──────────────────────────────────────────────
if __name__ == "__main__":
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    patch_dir = os.path.join(base, "data", "severstal_patches")
    save_dir = os.path.join(base, "outputs", "models_severstal")

    # Stage 1: 이진 분류
    binary_results = run_binary_dl_experiments(
        patch_dir,
        os.path.join(save_dir, "binary_dl"),
        max_per_class=3000,
        num_epochs=15,
    )

    # Stage 2: 4종 분류
    defect4_results = run_defect4_dl_experiments(
        patch_dir,
        os.path.join(save_dir, "defect4_dl"),
        num_epochs=20,
    )

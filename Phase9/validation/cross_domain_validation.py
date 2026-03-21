"""
교차 도메인 검증: NEU-DET → Severstal Stage 1 모델

검증①: NEU 1,800장 전체를 Stage 1(정상/비정상) 모델에 투입
        → 모두 "비정상"으로 탐지되어야 함 (Recall 측정)

검증②: NEU 6종 독립 분류
        → 동일 모델 아키텍처(ResNet-18)로 NEU 6종 학습/평가
        → Severstal 성능과 비교
"""

import os
import sys
import numpy as np
import cv2
import time
import torch
import torch.nn as nn
import joblib
from typing import Dict, List, Optional, Tuple
from sklearn.metrics import (
    accuracy_score,
    recall_score,
    precision_score,
    f1_score,
    confusion_matrix,
    classification_report,
)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ──────────────────────────────────────────────
# 검증①: NEU → Stage 1 교차 검증
# ──────────────────────────────────────────────
def validate_neu_on_stage1_ml(
    neu_dir: str,
    model_path: str,
    scaler_path: str,
) -> Dict:
    """NEU 이미지를 ML Stage 1 모델에 투입하여 비정상 탐지율 측정.

    NEU는 100% 결함 이미지이므로, 모두 "비정상(1)"으로 예측되어야 함.
    Recall = TP / (TP + FN) = 비정상을 비정상으로 맞춘 비율
    """
    from utils.data_loader import NEUDataLoader
    from features.feature_pipeline import FeaturePipeline

    print(f"\n{'#'*60}")
    print(f"검증①: NEU-DET → Stage 1 ML 교차 검증")
    print(f"{'#'*60}")

    # NEU 데이터 로드
    loader = NEUDataLoader(neu_dir)
    images, labels, class_names = loader.load_all_images()
    print(f"  NEU 이미지: {len(images)}장 ({len(set(labels))} 클래스)")

    # 특징 추출
    pipeline = FeaturePipeline()
    X, _ = pipeline.extract_batch(images)
    print(f"  특징 벡터: {X.shape}")

    # 스케일링
    scaler = joblib.load(scaler_path)
    X_scaled = scaler.transform(X)

    # 모델 로드 및 예측
    model = joblib.load(model_path)
    model_name = os.path.basename(model_path).replace("binary_", "").replace(".joblib", "")

    t0 = time.time()
    y_pred = model.predict(X_scaled)
    pred_time = time.time() - t0

    # NEU는 전부 결함 → 기대값 = 전부 1(비정상)
    y_true = np.ones(len(images), dtype=int)

    recall = recall_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, zero_division=0)
    acc = accuracy_score(y_true, y_pred)

    # 클래스별 탐지율
    unique_labels = sorted(set(labels))
    class_recalls = {}
    for lbl in unique_labels:
        mask = labels == lbl
        cls_pred = y_pred[mask]
        cls_recall = (cls_pred == 1).mean()
        cls_name = class_names[lbl] if lbl < len(class_names) else f"Class_{lbl}"
        class_recalls[cls_name] = cls_recall

    print(f"\n  모델: {model_name}")
    print(f"  전체 Recall (비정상 탐지율): {recall:.4f} ({recall*100:.1f}%)")
    print(f"  전체 Accuracy: {acc:.4f}")
    print(f"  추론 시간: {pred_time:.2f}s ({pred_time/len(images)*1000:.2f}ms/장)")

    print(f"\n  [NEU 클래스별 비정상 탐지율]")
    for cls_name, cls_recall in class_recalls.items():
        status = "✅" if cls_recall >= 0.9 else "⚠️" if cls_recall >= 0.7 else "❌"
        print(f"    {status} {cls_name}: {cls_recall:.4f} ({cls_recall*100:.1f}%)")

    return {
        "model_name": model_name,
        "total_images": len(images),
        "recall": recall,
        "precision": precision,
        "accuracy": acc,
        "class_recalls": class_recalls,
        "y_pred": y_pred,
        "pred_time": pred_time,
    }


def validate_neu_on_stage1_dl(
    neu_dir: str,
    model_path: str,
    num_classes: int = 2,
    target_size: int = 224,
) -> Dict:
    """NEU 이미지를 DL Stage 1 모델에 투입하여 비정상 탐지율 측정."""
    from utils.data_loader import NEUDataLoader
    from deep_learning.models.resnet_transfer import get_resnet18_finetune

    print(f"\n{'#'*60}")
    print(f"검증①: NEU-DET → Stage 1 DL 교차 검증")
    print(f"{'#'*60}")

    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

    # NEU 데이터 로드
    loader = NEUDataLoader(neu_dir)
    images, labels, class_names = loader.load_all_images()
    print(f"  NEU 이미지: {len(images)}장")

    # 모델 로드
    model = get_resnet18_finetune(num_classes=num_classes)
    model.load_state_dict(torch.load(model_path, map_location=device, weights_only=True))
    model = model.to(device)
    model.eval()

    # 예측
    y_pred = []
    batch_size = 32

    t0 = time.time()
    with torch.no_grad():
        for i in range(0, len(images), batch_size):
            batch_imgs = images[i : i + batch_size]
            tensors = []
            for img in batch_imgs:
                img_resized = cv2.resize(img, (target_size, target_size))
                img_float = img_resized.astype(np.float32) / 255.0
                img_3ch = np.stack([img_float] * 3, axis=0)
                # ImageNet normalization
                mean = np.array([0.485, 0.456, 0.406]).reshape(3, 1, 1)
                std = np.array([0.229, 0.224, 0.225]).reshape(3, 1, 1)
                img_norm = (img_3ch - mean) / std
                tensors.append(torch.from_numpy(img_norm).float())

            batch_tensor = torch.stack(tensors).to(device)
            outputs = model(batch_tensor)
            _, preds = outputs.max(1)
            y_pred.extend(preds.cpu().numpy())

    pred_time = time.time() - t0
    y_pred = np.array(y_pred)
    y_true = np.ones(len(images), dtype=int)

    recall = recall_score(y_true, y_pred)
    acc = accuracy_score(y_true, y_pred)

    # 클래스별 탐지율
    class_recalls = {}
    for lbl in sorted(set(labels)):
        mask = labels == lbl
        cls_recall = (y_pred[mask] == 1).mean()
        cls_name = class_names[lbl] if lbl < len(class_names) else f"Class_{lbl}"
        class_recalls[cls_name] = cls_recall

    model_name = os.path.basename(model_path).replace(".pt", "")
    print(f"\n  모델: {model_name}")
    print(f"  전체 Recall: {recall:.4f} ({recall*100:.1f}%)")
    print(f"  추론 시간: {pred_time:.2f}s")

    print(f"\n  [NEU 클래스별 비정상 탐지율]")
    for cls_name, cls_recall in class_recalls.items():
        status = "✅" if cls_recall >= 0.9 else "⚠️" if cls_recall >= 0.7 else "❌"
        print(f"    {status} {cls_name}: {cls_recall:.4f}")

    return {
        "model_name": model_name,
        "total_images": len(images),
        "recall": recall,
        "accuracy": acc,
        "class_recalls": class_recalls,
        "y_pred": y_pred,
        "pred_time": pred_time,
    }


# ──────────────────────────────────────────────
# 검증②: NEU 6종 독립 분류
# ──────────────────────────────────────────────
def run_neu_independent_classification(
    neu_dir: str,
    save_dir: str,
    num_epochs: int = 20,
    batch_size: int = 32,
) -> Dict:
    """NEU 6종 독립 분류 — 동일 ResNet-18 아키텍처 사용.

    Severstal 결과와 비교하기 위한 독립 실험.
    """
    from utils.data_loader import NEUDataLoader
    from deep_learning.datasets import NEUTorchDataset
    from deep_learning.models.resnet_transfer import get_resnet18_finetune
    from deep_learning.train_dl_severstal import train_model, get_device
    from torch.utils.data import DataLoader
    from sklearn.model_selection import train_test_split

    print(f"\n{'#'*60}")
    print(f"검증②: NEU-DET 6종 독립 분류 실험")
    print(f"{'#'*60}")

    device = get_device()

    # NEU 데이터 로드
    loader = NEUDataLoader(neu_dir)
    images, labels, class_names = loader.load_all_images()

    X_train, X_test, y_train, y_test = train_test_split(
        images, labels, test_size=0.2, stratify=labels, random_state=42
    )

    # PyTorch Dataset
    class SimpleDataset(torch.utils.data.Dataset):
        def __init__(self, imgs, lbls, size=224):
            self.imgs = imgs
            self.lbls = lbls
            self.size = size

        def __len__(self):
            return len(self.imgs)

        def __getitem__(self, idx):
            img = cv2.resize(self.imgs[idx], (self.size, self.size))
            img = img.astype(np.float32) / 255.0
            img = np.stack([img] * 3, axis=0)
            mean = np.array([0.485, 0.456, 0.406]).reshape(3, 1, 1)
            std = np.array([0.229, 0.224, 0.225]).reshape(3, 1, 1)
            img = (img - mean) / std
            return torch.from_numpy(img).float(), int(self.lbls[idx])

    train_ds = SimpleDataset(X_train, y_train)
    test_ds = SimpleDataset(X_test, y_test)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False)

    print(f"  Train: {len(train_ds)}장, Test: {len(test_ds)}장")
    print(f"  클래스: {class_names}")

    # ResNet-18 Fine-tune
    model = get_resnet18_finetune(num_classes=6)
    result = train_model(
        model, train_loader, test_loader,
        num_epochs=num_epochs, lr=0.0001, patience=7,
        save_path=os.path.join(save_dir, "neu_resnet18_6class.pt"),
        model_name="ResNet-18 Fine-tune (NEU 6종)", device=device,
    )

    # 상세 리포트
    report = classification_report(
        result["y_true"], result["y_pred"],
        target_names=class_names[:6] if len(class_names) >= 6 else class_names,
    )
    print(f"\n{report}")

    result["classification_report"] = report
    result["class_names"] = class_names

    return result


# ──────────────────────────────────────────────
if __name__ == "__main__":
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    neu_dir = os.path.join(base, "data", "NEU-DET")
    save_dir = os.path.join(base, "outputs", "models_severstal")

    # 검증②부터 (모델이 없을 수 있으므로)
    neu_result = run_neu_independent_classification(
        neu_dir, save_dir, num_epochs=15
    )

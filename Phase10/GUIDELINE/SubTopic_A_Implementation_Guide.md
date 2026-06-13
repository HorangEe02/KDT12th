# 🏭 소주제 A. 주조 제품 불량/정상 자동 분류 — 상세 구현 가이드라인

> **Claude Code에서 단계별로 실행할 수 있는 구현 명세서**
>
> 핵심 기술: CNN 전이학습 (ResNet50 / VGG16 / EfficientNet-B0) + Grad-CAM 시각화

---

## 목차

1. [환경 설정](#1-환경-설정)
2. [데이터 다운로드 및 탐색](#2-데이터-다운로드-및-탐색)
3. [데이터 전처리 및 DataLoader 구성](#3-데이터-전처리-및-dataloader-구성)
4. [모델 구현 — 3종 비교](#4-모델-구현--3종-비교)
5. [학습 루프 구현](#5-학습-루프-구현)
6. [평가 및 성능 분석](#6-평가-및-성능-분석)
7. [Grad-CAM 시각화](#7-grad-cam-시각화)
8. [결과 저장 및 정리](#8-결과-저장-및-정리)

---

## 1. 환경 설정

### 1.1 프로젝트 디렉토리 생성

```bash
mkdir -p SubTopic_A_Casting_Classification/{data,notebooks,models,results}
cd SubTopic_A_Casting_Classification
```

### 1.2 필수 패키지 설치

```bash
pip install torch torchvision matplotlib seaborn scikit-learn pillow tqdm grad-cam opencv-python
```

### 1.3 requirements.txt

```text
torch>=2.0.0
torchvision>=0.15.0
matplotlib>=3.7.0
seaborn>=0.12.0
scikit-learn>=1.3.0
Pillow>=10.0.0
tqdm>=4.65.0
grad-cam>=1.5.0
opencv-python>=4.8.0
```

### 1.4 GPU 확인 코드

```python
import torch
print(f"PyTorch 버전: {torch.__version__}")
print(f"CUDA 사용 가능: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU 이름: {torch.cuda.get_device_name(0)}")
    print(f"GPU 메모리: {torch.cuda.get_device_properties(0).total_mem / 1e9:.1f} GB")
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"사용 디바이스: {device}")
```

---

## 2. 데이터 다운로드 및 탐색

### 2.1 데이터셋 정보

| 항목         | 내용                                                                                          |
| ------------ | --------------------------------------------------------------------------------------------- |
| 데이터셋명   | Casting Product Image Data for Quality Inspection                                             |
| 출처         | https://www.kaggle.com/datasets/ravirajsinh45/real-life-industrial-dataset-of-casting-product |
| 총 이미지 수 | 7,348장                                                                                       |
| 이미지 크기  | 300×300 픽셀 (그레이스케일)                                                                  |
| 클래스       | 2개 (def_front = 불량, ok_front = 정상)                                                       |
| 폴더 구조    | train/test로 사전 분리                                                                        |

### 2.2 다운로드 방법

Kaggle API를 사용하는 경우:

```bash
# Kaggle API 토큰 설정 후
kaggle datasets download -d ravirajsinh45/real-life-industrial-dataset-of-casting-product
unzip real-life-industrial-dataset-of-casting-product.zip -d data/
```

수동 다운로드 시 아래 구조로 배치:

```
data/
├── casting_data/
│   ├── train/
│   │   ├── def_front/    ← 불량 이미지 (약 3,758장)
│   │   └── ok_front/     ← 정상 이미지 (약 2,875장)
│   └── test/
│       ├── def_front/    ← 불량 이미지 (약 453장)
│       └── ok_front/     ← 정상 이미지 (약 262장)
```

### 2.3 데이터 탐색 (EDA)

```python
import os
from pathlib import Path
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np

# === 데이터 경로 설정 ===
DATA_ROOT = Path("data/casting_data")
TRAIN_DIR = DATA_ROOT / "train"
TEST_DIR = DATA_ROOT / "test"

# === 클래스별 이미지 수 확인 ===
for split_name, split_dir in [("Train", TRAIN_DIR), ("Test", TEST_DIR)]:
    print(f"\n[{split_name}]")
    for class_name in sorted(os.listdir(split_dir)):
        class_dir = split_dir / class_name
        if class_dir.is_dir():
            count = len(list(class_dir.glob("*.jpeg")) + list(class_dir.glob("*.png")))
            print(f"  {class_name}: {count}장")

# === 샘플 이미지 시각화 ===
fig, axes = plt.subplots(2, 5, figsize=(15, 6))
fig.suptitle("주조 제품 샘플 이미지", fontsize=14, fontweight='bold')

for row, class_name in enumerate(["ok_front", "def_front"]):
    label = "정상 (OK)" if class_name == "ok_front" else "불량 (Defective)"
    class_dir = TRAIN_DIR / class_name
    images = list(class_dir.glob("*"))[:5]
    for col, img_path in enumerate(images):
        img = Image.open(img_path)
        axes[row, col].imshow(img, cmap='gray')
        axes[row, col].set_title(label if col == 0 else "", fontsize=10)
        axes[row, col].axis('off')

plt.tight_layout()
plt.savefig("results/01_sample_images.png", dpi=150, bbox_inches='tight')
plt.show()

# === 이미지 크기 분포 확인 ===
sizes = []
for img_path in TRAIN_DIR.rglob("*"):
    if img_path.suffix.lower() in ['.jpeg', '.jpg', '.png']:
        img = Image.open(img_path)
        sizes.append(img.size)

sizes = np.array(sizes)
print(f"\n이미지 크기 통계:")
print(f"  너비 - 최소: {sizes[:,0].min()}, 최대: {sizes[:,0].max()}, 평균: {sizes[:,0].mean():.0f}")
print(f"  높이 - 최소: {sizes[:,1].min()}, 최대: {sizes[:,1].max()}, 평균: {sizes[:,1].mean():.0f}")

# === 클래스 불균형 시각화 ===
train_ok = len(list((TRAIN_DIR / "ok_front").glob("*")))
train_def = len(list((TRAIN_DIR / "def_front").glob("*")))

fig, ax = plt.subplots(figsize=(6, 4))
bars = ax.bar(["정상 (OK)", "불량 (Defective)"], [train_ok, train_def],
              color=["#2ecc71", "#e74c3c"])
ax.set_title("학습 데이터 클래스 분포", fontweight='bold')
ax.set_ylabel("이미지 수")
for bar, val in zip(bars, [train_ok, train_def]):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 30,
            str(val), ha='center', fontweight='bold')
plt.tight_layout()
plt.savefig("results/02_class_distribution.png", dpi=150, bbox_inches='tight')
plt.show()
```

---

## 3. 데이터 전처리 및 DataLoader 구성

### 3.1 핵심 설계 결정

| 항목      | 설정값            | 이유                                    |
| --------- | ----------------- | --------------------------------------- |
| 입력 크기 | 224×224          | ImageNet 사전학습 모델의 표준 입력 크기 |
| 채널 수   | 3 (RGB 변환)      | 사전학습 모델이 3채널 입력을 기대       |
| 배치 크기 | 32                | GPU 메모리와 학습 안정성 균형           |
| 정규화    | ImageNet mean/std | 사전학습 가중치와 동일한 분포 유지      |

### 3.2 데이터 변환(Transform) 정의

```python
import torchvision.transforms as transforms

# === 학습용 변환 (데이터 증강 포함) ===
train_transform = transforms.Compose([
    transforms.Resize((224, 224)),                    # 사전학습 모델 표준 크기
    transforms.RandomHorizontalFlip(p=0.5),           # 좌우 반전 (50% 확률)
    transforms.RandomVerticalFlip(p=0.3),             # 상하 반전 (30% 확률)
    transforms.RandomRotation(degrees=15),            # ±15도 랜덤 회전
    transforms.ColorJitter(                           # 밝기/대비 변화
        brightness=0.2, contrast=0.2
    ),
    transforms.ToTensor(),                            # [0,255] → [0,1] 텐서 변환
    transforms.Normalize(                             # ImageNet 정규화
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    ),
])

# === 검증/테스트용 변환 (증강 없음) ===
test_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    ),
])
```

### 3.3 Dataset 및 DataLoader 생성

```python
from torchvision.datasets import ImageFolder
from torch.utils.data import DataLoader, random_split

# === Dataset 생성 ===
# ImageFolder: 폴더명을 자동으로 클래스 라벨로 사용
# def_front → 0 (불량), ok_front → 1 (정상)
full_train_dataset = ImageFolder(root=str(TRAIN_DIR), transform=train_transform)
test_dataset = ImageFolder(root=str(TEST_DIR), transform=test_transform)

# 클래스 매핑 확인
print(f"클래스 매핑: {full_train_dataset.class_to_idx}")
# 출력: {'def_front': 0, 'ok_front': 1}

CLASS_NAMES = ['Defective (불량)', 'OK (정상)']

# === Train / Validation 분리 (8:2) ===
train_size = int(0.8 * len(full_train_dataset))
val_size = len(full_train_dataset) - train_size
train_dataset, val_dataset = random_split(
    full_train_dataset, [train_size, val_size],
    generator=torch.Generator().manual_seed(42)  # 재현성 보장
)

# Validation에는 증강 없는 transform 적용
# (random_split은 Subset을 반환하므로 transform 교체가 필요)
val_dataset_clean = ImageFolder(root=str(TRAIN_DIR), transform=test_transform)
val_indices = val_dataset.indices
val_dataset = torch.utils.data.Subset(val_dataset_clean, val_indices)

print(f"Train: {len(train_dataset)}장")
print(f"Validation: {len(val_dataset)}장")
print(f"Test: {len(test_dataset)}장")

# === DataLoader 생성 ===
BATCH_SIZE = 32
NUM_WORKERS = 2  # Colab에서는 2 권장

train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE,
                          shuffle=True, num_workers=NUM_WORKERS, pin_memory=True)
val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE,
                        shuffle=False, num_workers=NUM_WORKERS, pin_memory=True)
test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE,
                         shuffle=False, num_workers=NUM_WORKERS, pin_memory=True)

# === 배치 형태 확인 ===
images, labels = next(iter(train_loader))
print(f"\n배치 형태: {images.shape}")   # torch.Size([32, 3, 224, 224])
print(f"라벨 형태: {labels.shape}")     # torch.Size([32])
print(f"라벨 값: {labels[:10]}")
```

---

## 4. 모델 구현 — 3종 비교

### 4.1 공통 함수: 사전학습 모델 로드 및 분류층 교체

```python
import torchvision.models as models
import torch.nn as nn

def build_model(model_name, num_classes=2, freeze_backbone=True):
    """
    사전학습 모델을 로드하고 분류층을 교체하는 함수

    Args:
        model_name: 'resnet50', 'vgg16', 'efficientnet_b0' 중 선택
        num_classes: 출력 클래스 수 (불량/정상 = 2)
        freeze_backbone: True면 백본 동결 (특성 추출기 모드)

    Returns:
        수정된 모델
    """

    if model_name == 'resnet50':
        # ResNet50: ImageNet 사전학습 가중치 로드
        model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V1)

        # 백본 동결 (선택)
        if freeze_backbone:
            for param in model.parameters():
                param.requires_grad = False

        # 마지막 FC 층 교체 (2048 → num_classes)
        model.fc = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(model.fc.in_features, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, num_classes)
        )
        # 교체된 층은 학습 가능
        for param in model.fc.parameters():
            param.requires_grad = True

    elif model_name == 'vgg16':
        # VGG16: ImageNet 사전학습 가중치 로드
        model = models.vgg16(weights=models.VGG16_Weights.IMAGENET1K_V1)

        if freeze_backbone:
            for param in model.features.parameters():
                param.requires_grad = False

        # 분류층 교체 (4096 → num_classes)
        model.classifier[-1] = nn.Linear(4096, num_classes)

    elif model_name == 'efficientnet_b0':
        # EfficientNet-B0: ImageNet 사전학습 가중치 로드
        model = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.IMAGENET1K_V1)

        if freeze_backbone:
            for param in model.features.parameters():
                param.requires_grad = False

        # 분류층 교체 (1280 → num_classes)
        model.classifier = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(model.classifier[1].in_features, num_classes)
        )

    else:
        raise ValueError(f"지원하지 않는 모델: {model_name}")

    return model


def count_parameters(model):
    """학습 가능/전체 파라미터 수 계산"""
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    frozen = total - trainable
    print(f"  전체 파라미터: {total:,}개")
    print(f"  학습 가능:    {trainable:,}개")
    print(f"  동결(Frozen): {frozen:,}개")
    return trainable
```

### 4.2 각 모델 생성 및 파라미터 확인

```python
# 3개 모델 생성 및 비교
MODEL_NAMES = ['resnet50', 'vgg16', 'efficientnet_b0']

for name in MODEL_NAMES:
    print(f"\n{'='*50}")
    print(f"모델: {name}")
    print(f"{'='*50}")
    model = build_model(name, num_classes=2, freeze_backbone=True)
    count_parameters(model)
```

---

## 5. 학습 루프 구현

### 5.1 학습 함수

```python
from tqdm import tqdm
import time

def train_one_epoch(model, loader, criterion, optimizer, device):
    """한 에폭 학습 수행"""
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    for images, labels in tqdm(loader, desc="  Training", leave=False):
        images, labels = images.to(device), labels.to(device)

        # 순전파
        outputs = model(images)
        loss = criterion(outputs, labels)

        # 역전파
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        # 통계 기록
        running_loss += loss.item() * images.size(0)
        _, predicted = outputs.max(1)
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()

    epoch_loss = running_loss / total
    epoch_acc = correct / total
    return epoch_loss, epoch_acc


def evaluate(model, loader, criterion, device):
    """검증/테스트 수행"""
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():
        for images, labels in tqdm(loader, desc="  Evaluating", leave=False):
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            loss = criterion(outputs, labels)

            running_loss += loss.item() * images.size(0)
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()

    epoch_loss = running_loss / total
    epoch_acc = correct / total
    return epoch_loss, epoch_acc
```

### 5.2 전체 학습 파이프라인

```python
def train_model(model_name, num_epochs=15, lr=1e-3, freeze_backbone=True):
    """
    모델 학습 전체 파이프라인

    Args:
        model_name: 'resnet50', 'vgg16', 'efficientnet_b0'
        num_epochs: 학습 에폭 수
        lr: 학습률
        freeze_backbone: 백본 동결 여부

    Returns:
        학습된 모델, 학습 기록 딕셔너리
    """

    print(f"\n{'#'*60}")
    print(f"# 모델 학습 시작: {model_name}")
    print(f"# Epochs: {num_epochs}, LR: {lr}, Freeze: {freeze_backbone}")
    print(f"{'#'*60}")

    # 모델 생성
    model = build_model(model_name, num_classes=2, freeze_backbone=freeze_backbone)
    model = model.to(device)

    # 손실 함수 & 옵티마이저
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=lr, weight_decay=1e-4
    )
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', factor=0.5, patience=3, verbose=True
    )

    # 학습 기록
    history = {
        'train_loss': [], 'train_acc': [],
        'val_loss': [], 'val_acc': []
    }
    best_val_acc = 0.0
    start_time = time.time()

    for epoch in range(num_epochs):
        print(f"\nEpoch [{epoch+1}/{num_epochs}]")

        # 학습
        train_loss, train_acc = train_one_epoch(
            model, train_loader, criterion, optimizer, device
        )
        # 검증
        val_loss, val_acc = evaluate(model, val_loader, criterion, device)

        # 스케줄러 업데이트
        scheduler.step(val_loss)

        # 기록 저장
        history['train_loss'].append(train_loss)
        history['train_acc'].append(train_acc)
        history['val_loss'].append(val_loss)
        history['val_acc'].append(val_acc)

        print(f"  Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.4f}")
        print(f"  Val   Loss: {val_loss:.4f} | Val   Acc: {val_acc:.4f}")

        # 최고 성능 모델 저장
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), f"models/best_{model_name}.pth")
            print(f"  ★ Best 모델 저장! (Val Acc: {val_acc:.4f})")

    elapsed = time.time() - start_time
    print(f"\n학습 완료! 총 소요 시간: {elapsed/60:.1f}분")
    print(f"최고 Validation Accuracy: {best_val_acc:.4f}")

    # Best 모델 로드
    model.load_state_dict(torch.load(f"models/best_{model_name}.pth"))

    return model, history
```

### 5.3 3개 모델 순차 학습

```python
# === 3개 모델 학습 실행 ===
results = {}

for model_name in MODEL_NAMES:
    model, history = train_model(
        model_name=model_name,
        num_epochs=15,
        lr=1e-3,
        freeze_backbone=True
    )
    results[model_name] = {'model': model, 'history': history}
```

---

## 6. 평가 및 성능 분석

### 6.1 학습 곡선 시각화

```python
def plot_training_curves(results, save_path="results/03_training_curves.png"):
    """3개 모델의 학습 곡선을 한 그래프에 비교"""

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    colors = {'resnet50': '#e74c3c', 'vgg16': '#3498db', 'efficientnet_b0': '#2ecc71'}

    for name, res in results.items():
        h = res['history']
        epochs = range(1, len(h['train_loss']) + 1)

        # Loss 그래프
        axes[0].plot(epochs, h['train_loss'], '--', color=colors[name], alpha=0.5)
        axes[0].plot(epochs, h['val_loss'], '-', color=colors[name], label=f'{name} (val)')

        # Accuracy 그래프
        axes[1].plot(epochs, h['train_acc'], '--', color=colors[name], alpha=0.5)
        axes[1].plot(epochs, h['val_acc'], '-', color=colors[name], label=f'{name} (val)')

    axes[0].set_title('Loss', fontweight='bold')
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('Loss')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    axes[1].set_title('Accuracy', fontweight='bold')
    axes[1].set_xlabel('Epoch')
    axes[1].set_ylabel('Accuracy')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.suptitle('모델별 학습 곡선 비교', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()

plot_training_curves(results)
```

### 6.2 테스트 셋 최종 평가

```python
from sklearn.metrics import (
    classification_report, confusion_matrix,
    precision_score, recall_score, f1_score, accuracy_score
)

def evaluate_on_test(model, model_name, test_loader, device):
    """테스트 셋에서 최종 성능 평가"""

    model.eval()
    all_preds = []
    all_labels = []
    all_probs = []

    with torch.no_grad():
        for images, labels in test_loader:
            images = images.to(device)
            outputs = model(images)
            probs = torch.softmax(outputs, dim=1)
            _, predicted = outputs.max(1)

            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(labels.numpy())
            all_probs.extend(probs.cpu().numpy())

    all_preds = np.array(all_preds)
    all_labels = np.array(all_labels)
    all_probs = np.array(all_probs)

    # 성능 지표 계산
    acc = accuracy_score(all_labels, all_preds)
    prec = precision_score(all_labels, all_preds, average='binary')
    rec = recall_score(all_labels, all_preds, average='binary')
    f1 = f1_score(all_labels, all_preds, average='binary')

    print(f"\n{'='*50}")
    print(f"[{model_name}] 테스트 셋 최종 성능")
    print(f"{'='*50}")
    print(f"  Accuracy:  {acc:.4f} ({acc*100:.1f}%)")
    print(f"  Precision: {prec:.4f}")
    print(f"  Recall:    {rec:.4f}")
    print(f"  F1-Score:  {f1:.4f}")
    print(f"\n{classification_report(all_labels, all_preds, target_names=CLASS_NAMES)}")

    return {
        'accuracy': acc, 'precision': prec,
        'recall': rec, 'f1': f1,
        'preds': all_preds, 'labels': all_labels, 'probs': all_probs
    }

# === 3개 모델 테스트 평가 ===
test_results = {}
for name in MODEL_NAMES:
    model = results[name]['model']
    test_results[name] = evaluate_on_test(model, name, test_loader, device)
```

### 6.3 혼동행렬(Confusion Matrix) 시각화

```python
def plot_confusion_matrices(test_results, save_path="results/04_confusion_matrices.png"):
    """3개 모델의 혼동행렬 비교"""

    fig, axes = plt.subplots(1, 3, figsize=(16, 4.5))

    for idx, (name, res) in enumerate(test_results.items()):
        cm = confusion_matrix(res['labels'], res['preds'])
        im = axes[idx].imshow(cm, cmap='Blues', interpolation='nearest')

        # 숫자 표시
        for i in range(2):
            for j in range(2):
                color = 'white' if cm[i,j] > cm.max()/2 else 'black'
                axes[idx].text(j, i, f'{cm[i,j]}', ha='center', va='center',
                              fontsize=16, fontweight='bold', color=color)

        axes[idx].set_title(f'{name}\nAcc: {res["accuracy"]:.1%}', fontweight='bold')
        axes[idx].set_xlabel('Predicted')
        axes[idx].set_ylabel('Actual')
        axes[idx].set_xticks([0, 1])
        axes[idx].set_yticks([0, 1])
        axes[idx].set_xticklabels(['Defective', 'OK'], fontsize=8)
        axes[idx].set_yticklabels(['Defective', 'OK'], fontsize=8)

    plt.suptitle('모델별 혼동행렬 비교', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()

plot_confusion_matrices(test_results)
```

### 6.4 모델 성능 비교 표

```python
def print_comparison_table(test_results):
    """3개 모델 성능 비교 테이블 출력"""

    print(f"\n{'='*70}")
    print(f"{'모델별 최종 성능 비교':^70}")
    print(f"{'='*70}")
    print(f"{'모델':<20} {'Accuracy':>10} {'Precision':>10} {'Recall':>10} {'F1-Score':>10}")
    print(f"{'-'*70}")

    for name, res in test_results.items():
        print(f"{name:<20} {res['accuracy']:>10.4f} {res['precision']:>10.4f} "
              f"{res['recall']:>10.4f} {res['f1']:>10.4f}")

    print(f"{'='*70}")

    # 최고 성능 모델 선정
    best_model = max(test_results, key=lambda x: test_results[x]['f1'])
    print(f"\n🏆 최고 성능 모델: {best_model} (F1: {test_results[best_model]['f1']:.4f})")

print_comparison_table(test_results)
```

---

## 7. Grad-CAM 시각화

### 7.1 Grad-CAM이란?

```
Grad-CAM (Gradient-weighted Class Activation Mapping):
  모델이 이미지의 "어디를 보고" 판단했는지 시각화하는 기법

  작동 원리:
  1. 특정 클래스에 대한 출력의 기울기를 마지막 합성곱 층으로 역전파
  2. 기울기를 글로벌 평균 풀링 → 각 채널의 중요도(가중치) 계산
  3. 특성 맵에 가중치를 곱하고 합산 → 히트맵 생성
  4. ReLU 적용 → 양의 영향만 시각화

  결과: 모델이 주목한 영역이 빨갛게(hot), 무시한 영역이 파랗게(cold) 표시
```

### 7.2 Grad-CAM 구현 (pytorch-grad-cam 라이브러리 사용)

```python
from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.image import show_cam_on_image
from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget
import cv2

def get_target_layer(model, model_name):
    """모델별 Grad-CAM 대상 층 반환"""
    if model_name == 'resnet50':
        return [model.layer4[-1]]           # ResNet의 마지막 Bottleneck
    elif model_name == 'vgg16':
        return [model.features[-1]]          # VGG의 마지막 합성곱 층
    elif model_name == 'efficientnet_b0':
        return [model.features[-1]]          # EfficientNet의 마지막 블록
    else:
        raise ValueError(f"지원하지 않는 모델: {model_name}")


def visualize_gradcam(model, model_name, test_dataset, device,
                      num_samples=8, save_path="results/05_gradcam.png"):
    """
    Grad-CAM 히트맵 시각화

    정상/불량 샘플 각각에 대해 모델이 주목하는 영역을 보여줌
    """

    model.eval()
    target_layers = get_target_layer(model, model_name)
    cam = GradCAM(model=model, target_layers=target_layers)

    # 정상/불량 샘플 인덱스 수집
    ok_indices = [i for i, (_, label) in enumerate(test_dataset) if label == 1][:num_samples//2]
    def_indices = [i for i, (_, label) in enumerate(test_dataset) if label == 0][:num_samples//2]
    sample_indices = def_indices + ok_indices

    fig, axes = plt.subplots(3, num_samples, figsize=(num_samples * 2.5, 8))
    row_titles = ['원본 이미지', 'Grad-CAM 히트맵', '오버레이']

    for col, idx in enumerate(sample_indices):
        img_tensor, label = test_dataset[idx]
        input_tensor = img_tensor.unsqueeze(0).to(device)

        # 원본 이미지 복원 (정규화 해제)
        img_np = img_tensor.permute(1, 2, 0).numpy()
        img_np = img_np * np.array([0.229, 0.224, 0.225]) + np.array([0.485, 0.456, 0.406])
        img_np = np.clip(img_np, 0, 1)

        # Grad-CAM 계산
        grayscale_cam = cam(input_tensor=input_tensor,
                           targets=[ClassifierOutputTarget(label)])[0]

        # 오버레이 생성
        visualization = show_cam_on_image(img_np, grayscale_cam, use_rgb=True)

        # 예측 결과
        with torch.no_grad():
            output = model(input_tensor)
            pred = output.argmax(1).item()
            prob = torch.softmax(output, dim=1).max().item()

        actual = CLASS_NAMES[label]
        predicted = CLASS_NAMES[pred]
        is_correct = "✓" if label == pred else "✗"

        # 시각화
        axes[0, col].imshow(img_np)
        axes[0, col].set_title(f'{actual}\n{is_correct} pred: {predicted}\n({prob:.1%})',
                               fontsize=8, fontweight='bold',
                               color='green' if label == pred else 'red')
        axes[0, col].axis('off')

        axes[1, col].imshow(grayscale_cam, cmap='jet')
        axes[1, col].axis('off')

        axes[2, col].imshow(visualization)
        axes[2, col].axis('off')

    for row, title in enumerate(row_titles):
        axes[row, 0].set_ylabel(title, fontsize=11, fontweight='bold', rotation=90,
                                labelpad=15, va='center')

    plt.suptitle(f'Grad-CAM 시각화 — {model_name}\n'
                 f'"AI가 어디를 보고 불량/정상을 판단했는가?"',
                 fontsize=13, fontweight='bold')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()

    cam.close()  # 리소스 해제


# === 최고 성능 모델로 Grad-CAM 실행 ===
best_model_name = max(test_results, key=lambda x: test_results[x]['f1'])
best_model = results[best_model_name]['model']

visualize_gradcam(
    model=best_model,
    model_name=best_model_name,
    test_dataset=test_dataset,
    device=device,
    num_samples=8,
    save_path=f"results/05_gradcam_{best_model_name}.png"
)
```

---

## 8. 결과 저장 및 정리

### 8.1 최종 결과 요약 저장

```python
import json

# === 결과 요약 딕셔너리 ===
summary = {
    "project": "주조 제품 불량/정상 자동 분류",
    "dataset": "Casting Product Image Data (7,348장)",
    "models": {}
}

for name in MODEL_NAMES:
    tr = test_results[name]
    summary["models"][name] = {
        "accuracy": round(tr["accuracy"], 4),
        "precision": round(tr["precision"], 4),
        "recall": round(tr["recall"], 4),
        "f1_score": round(tr["f1"], 4),
    }

# JSON 저장
with open("results/06_final_summary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)

print("결과 저장 완료: results/06_final_summary.json")
```

### 8.2 최종 출력 파일 목록

```
results/
├── 01_sample_images.png           ← 정상/불량 샘플 이미지
├── 02_class_distribution.png      ← 클래스 분포 그래프
├── 03_training_curves.png         ← 3모델 학습 곡선 비교
├── 04_confusion_matrices.png      ← 3모델 혼동행렬 비교
├── 05_gradcam_resnet50.png        ← Grad-CAM 시각화 (최고 모델)
└── 06_final_summary.json          ← 성능 지표 JSON

models/
├── best_resnet50.pth              ← 최고 성능 ResNet50 가중치
├── best_vgg16.pth                 ← 최고 성능 VGG16 가중치
└── best_efficientnet_b0.pth       ← 최고 성능 EfficientNet 가중치
```

---

## 부록: Claude Code 실행 순서 요약

Claude Code에서 이 가이드를 실행할 때는 다음 순서를 따릅니다.

```
[Step 1] 환경 설정
  → 디렉토리 생성, 패키지 설치, GPU 확인

[Step 2] 데이터 준비
  → 다운로드, 폴더 구조 확인, EDA 시각화

[Step 3] DataLoader 구성
  → Transform 정의, Train/Val/Test 분리, 배치 확인

[Step 4] 모델 3종 생성
  → ResNet50, VGG16, EfficientNet-B0 (전이학습)

[Step 5] 순차 학습
  → 각 모델 15 에폭 학습, Best 모델 저장

[Step 6] 테스트 평가
  → Accuracy/Precision/Recall/F1, 혼동행렬

[Step 7] Grad-CAM 시각화
  → 최고 성능 모델의 주목 영역 히트맵

[Step 8] 결과 저장
  → JSON 요약, 그래프 이미지 저장
```

### 예상 소요 시간

| 단계                    |    GPU (Colab T4)    |       CPU Only       |
| ----------------------- | :------------------: | :------------------: |
| 데이터 준비 + EDA       |         5분         |         5분         |
| 모델 1개 학습 (15 에폭) |        5~8분        |       40~60분       |
| 모델 3개 학습 합계      |       15~25분       |       2~3시간       |
| 평가 + Grad-CAM         |         5분         |         10분         |
| **총 소요 시간**  | **약 30~40분** | **약 3~4시간** |

### 목표 성능 기준

| 지표      | 최소 기준 | 우수 기준 |
| --------- | :-------: | :-------: |
| Accuracy  |  ≥ 93%  |  ≥ 97%  |
| Precision |  ≥ 90%  |  ≥ 95%  |
| Recall    |  ≥ 95%  |  ≥ 98%  |
| F1-Score  |  ≥ 92%  |  ≥ 96%  |

> Recall을 Precision보다 높게 설정한 이유: 불량 제품을 정상으로 놓치는 것(FN)이 정상 제품을 불량으로 잘못 판정하는 것(FP)보다 실제 제조 현장에서 훨씬 치명적이기 때문입니다.

# 🏭 소주제 B. 철강 표면 결함 영역 세그먼테이션 — 상세 구현 가이드라인

> **Claude Code에서 단계별로 실행할 수 있는 구현 명세서**
>
> 핵심 기술: U-Net (인코더-디코더 + Skip Connection) + Dice Loss + RLE 마스크 디코딩

---

## 목차

1. [환경 설정](#1-환경-설정)
2. [데이터 다운로드 및 탐색](#2-데이터-다운로드-및-탐색)
3. [RLE 마스크 디코딩 및 전처리](#3-rle-마스크-디코딩-및-전처리)
4. [커스텀 Dataset 및 DataLoader](#4-커스텀-dataset-및-dataloader)
5. [U-Net 모델 구현](#5-u-net-모델-구현)
6. [손실 함수 구현 — Dice Loss + BCE](#6-손실-함수-구현--dice-loss--bce)
7. [학습 루프 구현](#7-학습-루프-구현)
8. [평가 및 시각화](#8-평가-및-시각화)
9. [결과 저장 및 정리](#9-결과-저장-및-정리)

---

## 1. 환경 설정

### 1.1 프로젝트 디렉토리 생성

```bash
mkdir -p SubTopic_B_Steel_Segmentation/{data,notebooks,models,results}
cd SubTopic_B_Steel_Segmentation
```

### 1.2 필수 패키지 설치

```bash
pip install torch torchvision matplotlib seaborn scikit-learn pillow tqdm pandas albumentations opencv-python
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
pandas>=2.0.0
albumentations>=1.3.0
opencv-python>=4.8.0
```

### 1.4 GPU 확인 및 시드 고정

```python
import torch
import numpy as np
import random

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
torch.cuda.manual_seed_all(SEED)
torch.backends.cudnn.deterministic = True

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"PyTorch: {torch.__version__}")
print(f"Device: {device}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"Memory: {torch.cuda.get_device_properties(0).total_mem / 1e9:.1f} GB")
```

---

## 2. 데이터 다운로드 및 탐색

### 2.1 데이터셋 정보

| 항목        | 내용                                                      |
| ----------- | --------------------------------------------------------- |
| 데이터셋명  | Severstal: Steel Defect Detection                         |
| 출처        | https://www.kaggle.com/c/severstal-steel-defect-detection |
| 이미지 수   | 12,568장 (train)                                          |
| 이미지 크기 | 256×1600 픽셀 (그레이스케일, 가로로 긴 철강 표면)        |
| 결함 클래스 | 4종 (ClassId 1, 2, 3, 4)                                  |
| 어노테이션  | RLE (Run-Length Encoding) 형식                            |
| 특이사항    | 결함이 없는 이미지가 대다수 (클래스 불균형 심각)          |

### 2.2 다운로드 방법

```bash
# Kaggle API
kaggle competitions download -c severstal-steel-defect-detection
unzip severstal-steel-defect-detection.zip -d data/
```

다운로드 후 폴더 구조:

```
data/
├── train_images/          ← 학습 이미지 12,568장 (.jpg)
├── test_images/           ← 테스트 이미지 (라벨 없음)
├── train.csv              ← RLE 마스크 어노테이션
└── sample_submission.csv
```

### 2.3 train.csv 구조 분석

```python
import pandas as pd
from pathlib import Path

DATA_DIR = Path("data")
TRAIN_IMG_DIR = DATA_DIR / "train_images"

# === CSV 로드 ===
df = pd.read_csv(DATA_DIR / "train.csv")
print(f"전체 행 수: {len(df)}")
print(f"\n컬럼: {df.columns.tolist()}")
print(f"\n처음 10행:")
print(df.head(10))

# ===================================================
# train.csv 구조 설명:
# ===================================================
# ImageId_ClassId : "이미지파일명_결함클래스번호" 형식
#   예: "0002cc93b.jpg_1" → 0002cc93b.jpg 이미지의 결함 1번
# EncodedPixels   : RLE 인코딩된 마스크 (NaN이면 해당 결함 없음)
# ===================================================
```

### 2.4 데이터 분포 분석 (EDA)

```python
import matplotlib.pyplot as plt
import seaborn as sns

# === ImageId와 ClassId 분리 ===
df['ImageId'] = df['ImageId_ClassId'].apply(lambda x: x.split('_')[0])
df['ClassId'] = df['ImageId_ClassId'].apply(lambda x: int(x.split('_')[1]))
df['has_defect'] = df['EncodedPixels'].notna().astype(int)

# === 결함 유무 통계 ===
total_images = df['ImageId'].nunique()
defect_images = df[df['has_defect'] == 1]['ImageId'].nunique()
no_defect_images = total_images - defect_images

print(f"\n=== 데이터 통계 ===")
print(f"전체 이미지 수: {total_images}")
print(f"결함 있는 이미지: {defect_images} ({defect_images/total_images*100:.1f}%)")
print(f"결함 없는 이미지: {no_defect_images} ({no_defect_images/total_images*100:.1f}%)")

# === 클래스별 결함 분포 ===
class_counts = df[df['has_defect'] == 1].groupby('ClassId').size()
print(f"\n클래스별 결함 이미지 수:")
for cls_id, count in class_counts.items():
    print(f"  Class {cls_id}: {count}장")

# === 시각화 ===
fig, axes = plt.subplots(1, 2, figsize=(12, 4))

axes[0].pie([defect_images, no_defect_images],
            labels=[f'결함 있음\n({defect_images})', f'결함 없음\n({no_defect_images})'],
            colors=['#e74c3c', '#2ecc71'], autopct='%1.1f%%',
            startangle=90, textprops={'fontsize': 10})
axes[0].set_title('결함 유무 분포', fontweight='bold')

colors = ['#e74c3c', '#f39c12', '#3498db', '#9b59b6']
bars = axes[1].bar([f'Class {i}' for i in range(1, 5)],
                   [class_counts.get(i, 0) for i in range(1, 5)], color=colors)
axes[1].set_title('결함 클래스별 분포', fontweight='bold')
axes[1].set_ylabel('이미지 수')
for bar, val in zip(bars, [class_counts.get(i, 0) for i in range(1, 5)]):
    axes[1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 20,
                 str(val), ha='center', fontweight='bold')

plt.tight_layout()
plt.savefig("results/01_data_distribution.png", dpi=150, bbox_inches='tight')
plt.show()
```

---

## 3. RLE 마스크 디코딩 및 전처리

### 3.1 RLE(Run-Length Encoding)란?

```
RLE은 세그먼테이션 마스크를 압축 저장하는 형식입니다.

원리:
  마스크 이미지를 1차원으로 펼친 후,
  "시작 위치"와 "연속 길이"를 쌍으로 기록

예시:
  EncodedPixels = "29102 12 29346 24 29602 24"
  → 픽셀 29102번부터 12개 연속 = 결함
  → 픽셀 29346번부터 24개 연속 = 결함
  → 픽셀 29602번부터 24개 연속 = 결함

주의: Kaggle의 RLE은 "열 우선(column-major)" 순서입니다.
  → reshape 시 order='F' (Fortran order) 사용 필수
```

### 3.2 RLE 디코딩/인코딩 함수

```python
def rle_decode(rle_string, shape=(256, 1600)):
    """
    RLE 문자열 → 2D 바이너리 마스크 변환

    Args:
        rle_string: "start1 length1 start2 length2 ..." 형식
        shape: (height, width) 튜플

    Returns:
        np.ndarray: shape 크기의 바이너리 마스크 (0 또는 1)
    """
    if pd.isna(rle_string) or rle_string == '':
        return np.zeros(shape, dtype=np.uint8)

    s = list(map(int, rle_string.split()))
    starts = s[0::2]     # 홀수 인덱스: 시작 위치 (1-indexed)
    lengths = s[1::2]    # 짝수 인덱스: 연속 길이

    mask_flat = np.zeros(shape[0] * shape[1], dtype=np.uint8)
    for start, length in zip(starts, lengths):
        start -= 1  # 1-indexed → 0-indexed
        mask_flat[start:start + length] = 1

    # Kaggle RLE은 column-major → Fortran order
    mask = mask_flat.reshape(shape, order='F')
    return mask


def rle_encode(mask):
    """2D 바이너리 마스크 → RLE 문자열 변환 (제출용)"""
    pixels = mask.flatten(order='F')
    pixels = np.concatenate([[0], pixels, [0]])
    runs = np.where(pixels[1:] != pixels[:-1])[0] + 1
    runs[1::2] -= runs[::2]
    return ' '.join(str(x) for x in runs)
```

### 3.3 RLE 디코딩 검증 시각화

```python
from PIL import Image
import cv2

def visualize_defect_samples(df, train_img_dir, num_samples=4,
                              save_path="results/02_defect_samples.png"):
    """결함 이미지와 마스크를 시각화"""

    defect_df = df[df['has_defect'] == 1].copy()
    sample_images = defect_df['ImageId'].unique()[:num_samples]

    fig, axes = plt.subplots(num_samples, 3, figsize=(18, 4 * num_samples))
    colors_map = {1: [1, 0, 0], 2: [1, 0.6, 0], 3: [0, 0.5, 1], 4: [0.6, 0.2, 0.8]}

    for row, img_id in enumerate(sample_images):
        img = np.array(Image.open(train_img_dir / img_id))
        img_rows = df[df['ImageId'] == img_id]
        combined_mask = np.zeros((*img.shape[:2], 3), dtype=np.float32)
        class_labels = []

        for _, row_data in img_rows.iterrows():
            if row_data['has_defect'] == 1:
                cls_id = row_data['ClassId']
                mask = rle_decode(row_data['EncodedPixels'], shape=img.shape[:2])
                color = colors_map[cls_id]
                for c in range(3):
                    combined_mask[:, :, c] += mask * color[c]
                class_labels.append(f"Class {cls_id}")

        if len(img.shape) == 2:
            img_rgb = np.stack([img]*3, axis=-1) / 255.0
        else:
            img_rgb = img / 255.0

        overlay = img_rgb.copy()
        mask_area = combined_mask.sum(axis=-1) > 0
        overlay[mask_area] = overlay[mask_area] * 0.5 + combined_mask[mask_area] * 0.5

        axes[row, 0].imshow(img, cmap='gray')
        axes[row, 0].set_title(f'원본: {img_id}', fontsize=9)
        axes[row, 0].axis('off')
        axes[row, 1].imshow(combined_mask)
        axes[row, 1].set_title(f'마스크: {", ".join(class_labels)}', fontsize=9)
        axes[row, 1].axis('off')
        axes[row, 2].imshow(overlay)
        axes[row, 2].set_title('오버레이', fontsize=9)
        axes[row, 2].axis('off')

    plt.suptitle('철강 표면 결함 — 원본 / 마스크 / 오버레이', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()

visualize_defect_samples(df, TRAIN_IMG_DIR)
```

---

## 4. 커스텀 Dataset 및 DataLoader

### 4.1 핵심 설계 결정

| 항목      | 설정값                       | 이유                                                 |
| --------- | ---------------------------- | ---------------------------------------------------- |
| 입력 크기 | 256×256                     | 원본(256×1600)은 메모리 부담, 정사각형으로 리사이즈 |
| 채널 수   | 3 (그레이스케일 → RGB 복사) | 사전학습 인코더 호환                                 |
| 출력 채널 | 4 (클래스별 독립 마스크)     | 멀티레이블: 한 픽셀에 여러 결함 가능                 |
| 배치 크기 | 16                           | U-Net의 메모리 사용량이 크므로 작게 설정             |

### 4.2 커스텀 Dataset 클래스

```python
from torch.utils.data import Dataset, DataLoader
import albumentations as A
from albumentations.pytorch import ToTensorV2

class SteelDataset(Dataset):
    """
    Severstal 철강 결함 세그먼테이션 데이터셋

    각 이미지에 대해 4개 클래스의 바이너리 마스크를 반환
    출력 마스크 shape: (4, H, W)
    """

    def __init__(self, df, img_dir, img_size=256, transform=None):
        self.df = df
        self.img_dir = Path(img_dir)
        self.img_size = img_size
        self.transform = transform

        # 결함이 있는 이미지만 필터링
        self.image_ids = df[df['has_defect'] == 1]['ImageId'].unique()
        print(f"Dataset 생성: {len(self.image_ids)}장 (결함 이미지만)")

    def __len__(self):
        return len(self.image_ids)

    def __getitem__(self, idx):
        img_id = self.image_ids[idx]

        # 이미지 로드
        img_path = self.img_dir / img_id
        image = cv2.imread(str(img_path))
        if image is None:
            raise FileNotFoundError(f"이미지 없음: {img_path}")
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        orig_h, orig_w = image.shape[:2]

        # 4클래스 마스크 생성
        masks = np.zeros((orig_h, orig_w, 4), dtype=np.float32)
        img_df = self.df[self.df['ImageId'] == img_id]
        for _, row in img_df.iterrows():
            if row['has_defect'] == 1:
                cls_idx = row['ClassId'] - 1  # 0-indexed
                masks[:, :, cls_idx] = rle_decode(
                    row['EncodedPixels'], shape=(orig_h, orig_w)
                )

        # 데이터 증강
        if self.transform:
            augmented = self.transform(image=image, mask=masks)
            image = augmented['image']
            masks = augmented['mask']
        else:
            image = cv2.resize(image, (self.img_size, self.img_size))
            masks = cv2.resize(masks, (self.img_size, self.img_size))
            image = torch.from_numpy(image).permute(2, 0, 1).float() / 255.0
            masks = torch.from_numpy(masks)

        # masks: (H, W, 4) → (4, H, W)
        if isinstance(masks, np.ndarray):
            masks = torch.from_numpy(masks)
        if masks.dim() == 3 and masks.shape[-1] == 4:
            masks = masks.permute(2, 0, 1).float()

        return image, masks
```

### 4.3 데이터 증강 및 DataLoader 생성

```python
from sklearn.model_selection import train_test_split

IMG_SIZE = 256

train_aug = A.Compose([
    A.Resize(IMG_SIZE, IMG_SIZE),
    A.HorizontalFlip(p=0.5),
    A.VerticalFlip(p=0.3),
    A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=0.5),
    A.ShiftScaleRotate(shift_limit=0.05, scale_limit=0.1, rotate_limit=15, p=0.5),
    A.GaussNoise(var_limit=(10, 50), p=0.3),
    A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ToTensorV2(),
])

val_aug = A.Compose([
    A.Resize(IMG_SIZE, IMG_SIZE),
    A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ToTensorV2(),
])

# Train / Val 분리 (8:2)
defect_image_ids = df[df['has_defect'] == 1]['ImageId'].unique()
train_ids, val_ids = train_test_split(defect_image_ids, test_size=0.2, random_state=SEED)
train_df = df[df['ImageId'].isin(train_ids)]
val_df = df[df['ImageId'].isin(val_ids)]
print(f"Train: {len(train_ids)}장 / Val: {len(val_ids)}장")

train_dataset = SteelDataset(train_df, TRAIN_IMG_DIR, IMG_SIZE, transform=train_aug)
val_dataset = SteelDataset(val_df, TRAIN_IMG_DIR, IMG_SIZE, transform=val_aug)

BATCH_SIZE = 16
train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE,
                          shuffle=True, num_workers=2, pin_memory=True)
val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE,
                        shuffle=False, num_workers=2, pin_memory=True)

# 배치 확인
images, masks = next(iter(train_loader))
print(f"이미지 배치: {images.shape}")   # (16, 3, 256, 256)
print(f"마스크 배치: {masks.shape}")     # (16, 4, 256, 256)
```

---

## 5. U-Net 모델 구현

### 5.1 아키텍처

```
  입력 (3, 256, 256)
    │
    ▼ DoubleConv(3→64) ────── Skip ──────→ DoubleConv + Conv1x1 → 출력(4, 256, 256)
    ▼ MaxPool → DoubleConv(64→128) ─ Skip ─→ Up + DoubleConv
    ▼ MaxPool → DoubleConv(128→256) ─ Skip ─→ Up + DoubleConv
    ▼ MaxPool → DoubleConv(256→512) ─ Skip ─→ Up + DoubleConv
    ▼ MaxPool → DoubleConv(512→1024) ─ Bottleneck ─┘
```

### 5.2 코드 구현

```python
import torch.nn as nn
import torch.nn.functional as F

class DoubleConv(nn.Module):
    """U-Net 기본 블록: Conv → BN → ReLU × 2"""
    def __init__(self, in_ch, out_ch):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
        )
    def forward(self, x):
        return self.block(x)


class UNet(nn.Module):
    """
    U-Net 세그먼테이션 모델

    인코더: 이미지를 점점 압축하며 "무엇이 있는지" 파악
    디코더: 다시 복원하며 "어디에 있는지" 위치 복원
    Skip Connection: 인코더 위치 정보를 디코더에 직접 전달
    """
    def __init__(self, in_ch=3, out_ch=4, features=[64, 128, 256, 512]):
        super().__init__()
        self.encoders = nn.ModuleList()
        self.decoders = nn.ModuleList()
        self.upconvs = nn.ModuleList()
        self.pool = nn.MaxPool2d(2, 2)

        # 인코더
        ch = in_ch
        for f in features:
            self.encoders.append(DoubleConv(ch, f))
            ch = f

        # Bottleneck
        self.bottleneck = DoubleConv(features[-1], features[-1] * 2)

        # 디코더
        for f in reversed(features):
            self.upconvs.append(nn.ConvTranspose2d(f * 2, f, 2, stride=2))
            self.decoders.append(DoubleConv(f * 2, f))

        # 최종 1×1 Conv
        self.final = nn.Conv2d(features[0], out_ch, 1)

    def forward(self, x):
        skips = []
        for enc in self.encoders:
            x = enc(x)
            skips.append(x)
            x = self.pool(x)

        x = self.bottleneck(x)

        for idx in range(len(self.decoders)):
            x = self.upconvs[idx](x)
            skip = skips[-(idx + 1)]
            if x.shape != skip.shape:
                x = F.interpolate(x, size=skip.shape[2:], mode='bilinear', align_corners=True)
            x = torch.cat([skip, x], dim=1)
            x = self.decoders[idx](x)

        return self.final(x)


model = UNet(in_ch=3, out_ch=4).to(device)

total_params = sum(p.numel() for p in model.parameters())
print(f"U-Net 파라미터: {total_params:,}개")

dummy = torch.randn(1, 3, 256, 256).to(device)
print(f"입력: {dummy.shape} → 출력: {model(dummy).shape}")
```

---

## 6. 손실 함수 구현 — Dice Loss + BCE

### 6.1 왜 결합 손실이 필요한가

```
철강 이미지에서 결함 영역 = 전체 픽셀의 1~5%
→ "전부 배경"으로 예측해도 Accuracy 95%+
→ CrossEntropy만 쓰면 "항상 배경" 전략을 학습

해결: BCE + Dice Loss
  BCE  → 픽셀 단위 정확도 보장
  Dice → 영역 단위 겹침(overlap) 최적화
```

### 6.2 구현

```python
class DiceLoss(nn.Module):
    def __init__(self, smooth=1.0):
        super().__init__()
        self.smooth = smooth

    def forward(self, pred, target):
        pred = torch.sigmoid(pred)
        pred_flat = pred.contiguous().view(-1)
        target_flat = target.contiguous().view(-1)
        intersection = (pred_flat * target_flat).sum()
        union = pred_flat.sum() + target_flat.sum()
        dice = (2.0 * intersection + self.smooth) / (union + self.smooth)
        return 1.0 - dice


class CombinedLoss(nn.Module):
    """BCE(픽셀 정밀도) + Dice(영역 겹침) 결합"""
    def __init__(self, bce_w=0.5, dice_w=0.5):
        super().__init__()
        self.bce = nn.BCEWithLogitsLoss()
        self.dice = DiceLoss()
        self.bce_w = bce_w
        self.dice_w = dice_w

    def forward(self, pred, target):
        return self.bce_w * self.bce(pred, target) + self.dice_w * self.dice(pred, target)

criterion = CombinedLoss()
```

---

## 7. 학습 루프 구현

### 7.1 지표 함수

```python
def compute_dice(pred, target, threshold=0.5):
    pred = (torch.sigmoid(pred) > threshold).float()
    smooth = 1.0
    inter = (pred.view(-1) * target.view(-1)).sum()
    return (2 * inter + smooth) / (pred.view(-1).sum() + target.view(-1).sum() + smooth)

def compute_iou(pred, target, threshold=0.5):
    pred = (torch.sigmoid(pred) > threshold).float()
    smooth = 1.0
    inter = (pred.view(-1) * target.view(-1)).sum()
    union = pred.view(-1).sum() + target.view(-1).sum() - inter
    return (inter + smooth) / (union + smooth)
```

### 7.2 학습/검증 루프

```python
from tqdm import tqdm
import time

def train_one_epoch(model, loader, criterion, optimizer, device):
    model.train()
    total_loss, total_dice, count = 0, 0, 0
    for images, masks in tqdm(loader, desc="  Train", leave=False):
        images, masks = images.to(device), masks.to(device)
        outputs = model(images)
        loss = criterion(outputs, masks)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * images.size(0)
        total_dice += compute_dice(outputs, masks).item() * images.size(0)
        count += images.size(0)
    return total_loss / count, total_dice / count

def evaluate(model, loader, criterion, device):
    model.eval()
    total_loss, total_dice, total_iou, count = 0, 0, 0, 0
    with torch.no_grad():
        for images, masks in tqdm(loader, desc="  Val", leave=False):
            images, masks = images.to(device), masks.to(device)
            outputs = model(images)
            loss = criterion(outputs, masks)
            total_loss += loss.item() * images.size(0)
            total_dice += compute_dice(outputs, masks).item() * images.size(0)
            total_iou += compute_iou(outputs, masks).item() * images.size(0)
            count += images.size(0)
    return total_loss / count, total_dice / count, total_iou / count
```

### 7.3 전체 학습 실행

```python
def train_unet(model, train_loader, val_loader, criterion, num_epochs=25, lr=1e-4):
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='max', factor=0.5, patience=5, verbose=True
    )

    history = {'train_loss': [], 'train_dice': [],
               'val_loss': [], 'val_dice': [], 'val_iou': []}
    best_dice = 0.0
    start = time.time()

    for epoch in range(num_epochs):
        print(f"\nEpoch [{epoch+1}/{num_epochs}]")
        tl, td = train_one_epoch(model, train_loader, criterion, optimizer, device)
        vl, vd, vi = evaluate(model, val_loader, criterion, device)
        scheduler.step(vd)

        history['train_loss'].append(tl)
        history['train_dice'].append(td)
        history['val_loss'].append(vl)
        history['val_dice'].append(vd)
        history['val_iou'].append(vi)

        print(f"  Train — Loss: {tl:.4f} | Dice: {td:.4f}")
        print(f"  Val   — Loss: {vl:.4f} | Dice: {vd:.4f} | IoU: {vi:.4f}")

        if vd > best_dice:
            best_dice = vd
            torch.save(model.state_dict(), "models/best_unet.pth")
            print(f"  ★ Best 저장! (Dice: {vd:.4f})")

    print(f"\n완료! {(time.time()-start)/60:.1f}분 소요 | Best Dice: {best_dice:.4f}")
    model.load_state_dict(torch.load("models/best_unet.pth"))
    return model, history

model, history = train_unet(model, train_loader, val_loader, criterion, num_epochs=25, lr=1e-4)
```

---

## 8. 평가 및 시각화

### 8.1 학습 곡선

```python
def plot_curves(history, save_path="results/03_training_curves.png"):
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.5))
    ep = range(1, len(history['train_loss']) + 1)

    axes[0].plot(ep, history['train_loss'], 'b--', alpha=0.7, label='Train')
    axes[0].plot(ep, history['val_loss'], 'r-', label='Val')
    axes[0].set_title('Loss (BCE + Dice)', fontweight='bold')
    axes[0].legend(); axes[0].grid(True, alpha=0.3)

    axes[1].plot(ep, history['train_dice'], 'b--', alpha=0.7, label='Train')
    axes[1].plot(ep, history['val_dice'], 'r-', label='Val')
    axes[1].set_title('Dice Coefficient', fontweight='bold')
    axes[1].legend(); axes[1].grid(True, alpha=0.3)

    axes[2].plot(ep, history['val_iou'], 'g-', label='Val IoU')
    axes[2].set_title('IoU (Val)', fontweight='bold')
    axes[2].legend(); axes[2].grid(True, alpha=0.3)

    plt.suptitle('U-Net 학습 곡선', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()

plot_curves(history)
```

### 8.2 예측 결과 시각화

```python
def visualize_predictions(model, val_dataset, device, num_samples=6,
                           save_path="results/04_predictions.png"):
    model.eval()
    colors = {0: [1,0,0], 1: [1,0.6,0], 2: [0,0.5,1], 3: [0.6,0.2,0.8]}

    fig, axes = plt.subplots(num_samples, 4, figsize=(20, 4 * num_samples))
    col_titles = ['원본 이미지', '정답 마스크 (GT)', '예측 마스크 (Pred)', '오버레이 비교']
    indices = np.random.choice(len(val_dataset), num_samples, replace=False)

    for row, idx in enumerate(indices):
        image, gt_mask = val_dataset[idx]
        with torch.no_grad():
            pred_logits = model(image.unsqueeze(0).to(device))
            pred_mask = (torch.sigmoid(pred_logits) > 0.5).float().cpu().squeeze(0)

        # 이미지 역정규화
        img_np = image.permute(1, 2, 0).numpy()
        img_np = img_np * np.array([0.229, 0.224, 0.225]) + np.array([0.485, 0.456, 0.406])
        img_np = np.clip(img_np, 0, 1)

        def to_color(m):
            h, w = m.shape[1], m.shape[2]
            c = np.zeros((h, w, 3))
            for ch in range(4):
                mc = m[ch].numpy() if isinstance(m[ch], torch.Tensor) else m[ch]
                for rgb in range(3):
                    c[:, :, rgb] += mc * colors[ch][rgb]
            return np.clip(c, 0, 1)

        gt_c = to_color(gt_mask)
        pr_c = to_color(pred_mask)

        # 오버레이: 노랑=정확, 초록=놓침(FN), 빨강=오탐(FP)
        overlay = img_np.copy()
        gt_a = gt_c.sum(-1) > 0
        pr_a = pr_c.sum(-1) > 0
        overlay[gt_a & pr_a] = [1, 1, 0]
        overlay[gt_a & ~pr_a] = [0, 1, 0]
        overlay[~gt_a & pr_a] = [1, 0, 0]

        sample_dice = compute_dice(pred_logits.cpu().squeeze(0).unsqueeze(0),
                                   gt_mask.unsqueeze(0)).item()

        axes[row, 0].imshow(img_np); axes[row, 0].axis('off')
        axes[row, 1].imshow(gt_c); axes[row, 1].axis('off')
        axes[row, 2].imshow(pr_c); axes[row, 2].set_title(f'Dice: {sample_dice:.3f}', fontsize=9); axes[row, 2].axis('off')
        axes[row, 3].imshow(overlay); axes[row, 3].set_title('노랑=정확 / 초록=놓침 / 빨강=오탐', fontsize=7); axes[row, 3].axis('off')

    for c, t in enumerate(col_titles):
        axes[0, c].set_title(t, fontsize=10, fontweight='bold')

    plt.suptitle('U-Net 세그먼테이션 예측 결과', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()

visualize_predictions(model, val_dataset, device)
```

### 8.3 클래스별 Dice / IoU 분석

```python
def evaluate_per_class(model, val_loader, device, save_path="results/05_per_class_metrics.png"):
    model.eval()
    class_dice = {i: [] for i in range(4)}
    class_iou = {i: [] for i in range(4)}

    with torch.no_grad():
        for images, masks in tqdm(val_loader, desc="클래스별 평가"):
            images = images.to(device)
            preds = (torch.sigmoid(model(images)) > 0.5).float().cpu()
            masks = masks.cpu()

            for c in range(4):
                for b in range(preds.shape[0]):
                    if masks[b, c].sum() > 0:
                        smooth = 1.0
                        inter = (preds[b, c] * masks[b, c]).sum()
                        d = (2 * inter + smooth) / (preds[b, c].sum() + masks[b, c].sum() + smooth)
                        u = (inter + smooth) / (preds[b, c].sum() + masks[b, c].sum() - inter + smooth)
                        class_dice[c].append(d.item())
                        class_iou[c].append(u.item())

    names = [f'Class {i+1}' for i in range(4)]
    avg_d = [np.mean(class_dice[c]) if class_dice[c] else 0 for c in range(4)]
    avg_i = [np.mean(class_iou[c]) if class_iou[c] else 0 for c in range(4)]

    print(f"\n{'='*55}")
    print(f"{'클래스별 성능':^55}")
    print(f"{'='*55}")
    print(f"{'클래스':<12} {'샘플수':>8} {'Dice':>10} {'IoU':>10}")
    print(f"{'-'*55}")
    for c in range(4):
        print(f"{names[c]:<12} {len(class_dice[c]):>8} {avg_d[c]:>10.4f} {avg_i[c]:>10.4f}")
    print(f"{'전체 평균':<12} {'':>8} {np.mean(avg_d):>10.4f} {np.mean(avg_i):>10.4f}")

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    clrs = ['#e74c3c', '#f39c12', '#3498db', '#9b59b6']
    for ax, vals, title in [(axes[0], avg_d, 'Dice'), (axes[1], avg_i, 'IoU')]:
        ax.bar(range(4), vals, color=clrs)
        ax.set_xticks(range(4)); ax.set_xticklabels(names)
        ax.set_title(f'클래스별 {title}', fontweight='bold'); ax.set_ylim(0, 1)
        for i, v in enumerate(vals):
            ax.text(i, v + 0.02, f'{v:.3f}', ha='center', fontweight='bold')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()
    return avg_d, avg_i

avg_dices, avg_ious = evaluate_per_class(model, val_loader, device)
```

---

## 9. 결과 저장 및 정리

### 9.1 결과 JSON

```python
import json

summary = {
    "project": "철강 표면 결함 세그먼테이션",
    "model": "U-Net (Vanilla)",
    "dataset": "Severstal Steel Defect Detection",
    "input_size": f"{IMG_SIZE}x{IMG_SIZE}",
    "num_classes": 4,
    "loss": "BCE(0.5) + Dice(0.5)",
    "overall_dice": round(float(np.mean(avg_dices)), 4),
    "overall_iou": round(float(np.mean(avg_ious)), 4),
    "per_class": {
        f"class_{i+1}": {"dice": round(float(avg_dices[i]), 4), "iou": round(float(avg_ious[i]), 4)}
        for i in range(4)
    }
}

with open("results/06_final_summary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)
print("저장 완료: results/06_final_summary.json")
```

### 9.2 최종 출력 파일 목록

```
results/
├── 01_data_distribution.png       ← 결함 유무/클래스별 분포
├── 02_defect_samples.png          ← 원본/마스크/오버레이 샘플
├── 03_training_curves.png         ← Loss/Dice/IoU 학습 곡선
├── 04_predictions.png             ← GT vs Pred 비교 시각화
├── 05_per_class_metrics.png       ← 클래스별 Dice/IoU 막대그래프
└── 06_final_summary.json          ← 성능 지표 JSON

models/
└── best_unet.pth                  ← 최고 성능 U-Net 가중치
```

---

## 부록: Claude Code 실행 순서 요약

```
[Step 1] 환경 설정        → 디렉토리, 패키지, GPU/시드
[Step 2] 데이터 탐색      → CSV 파싱, EDA, 분포 시각화
[Step 3] RLE 유틸리티     → rle_decode / rle_encode + 검증
[Step 4] Dataset/Loader   → SteelDataset, 증강, Train/Val 분리
[Step 5] U-Net 구현       → DoubleConv → Encoder → Bottleneck → Decoder
[Step 6] 손실 함수        → DiceLoss + BCEWithLogitsLoss 결합
[Step 7] 학습 (25 에폭)   → Adam, ReduceLROnPlateau, Best 저장
[Step 8] 평가/시각화      → 학습 곡선, 예측 비교, 클래스별 분석
[Step 9] 결과 저장        → JSON, 그래프 이미지
```

### 예상 소요 시간

| 단계                   |    GPU (Colab T4)    |       CPU Only       |
| ---------------------- | :------------------: | :------------------: |
| 데이터 준비 + EDA      |         5분         |         5분         |
| U-Net 학습 (25 에폭)   |       20~30분       |       3~5시간       |
| 평가 + 시각화          |         5분         |         15분         |
| **총 소요 시간** | **약 35~45분** | **약 4~6시간** |

### 목표 성능 기준

| 지표         | 최소 기준 | 우수 기준 |
| ------------ | :-------: | :-------: |
| Overall Dice |  ≥ 0.55  |  ≥ 0.75  |
| Overall IoU  |  ≥ 0.45  |  ≥ 0.65  |
| Class 3 Dice |  ≥ 0.65  |  ≥ 0.80  |
| Class 4 Dice |  ≥ 0.70  |  ≥ 0.85  |

### 소주제 A와의 핵심 차이점

| 비교 항목   |         A (분류)         |      B (세그먼테이션)      |
| ----------- | :----------------------: | :------------------------: |
| 과제 유형   |    이미지 → 라벨 1개    |  이미지 → 픽셀별 마스크  |
| 출력 형태   |       (B, 2) 벡터       |    (B, 4, H, W) 마스크    |
| 손실 함수   |     CrossEntropyLoss     |      BCE + Dice Loss      |
| 평가 지표   |       Accuracy, F1       |         Dice, IoU         |
| 모델        | 사전학습 CNN (분류 헤드) |   U-Net (인코더-디코더)   |
| 데이터 포맷 |      폴더 기반 라벨      |     RLE 인코딩 마스크     |
| 핵심 난이도 |        모델 비교        | 클래스 불균형 + RLE 디코딩 |

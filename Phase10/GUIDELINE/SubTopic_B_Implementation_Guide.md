# 🏭 소주제 B. 산업 시설 표면 균열 세그먼테이션 — 상세 구현 가이드라인

> **Claude Code에서 단계별로 실행할 수 있는 구현 명세서**
>
> 핵심 기술: U-Net (인코더-디코더 + Skip Connection) + Dice Loss + 바이너리 마스크 세그먼테이션

---

## 목차

1. [환경 설정](#1-환경-설정)
2. [데이터 다운로드 및 탐색](#2-데이터-다운로드-및-탐색)
3. [데이터 전처리 및 DataLoader](#3-데이터-전처리-및-dataloader)
4. [U-Net 모델 구현](#4-u-net-모델-구현)
5. [손실 함수 구현 — Dice Loss + BCE](#5-손실-함수-구현--dice-loss--bce)
6. [학습 루프 구현](#6-학습-루프-구현)
7. [평가 및 시각화](#7-평가-및-시각화)
8. [추가 실험 — ResNet 백본 U-Net 비교](#8-추가-실험--resnet-백본-u-net-비교)
9. [결과 저장 및 정리](#9-결과-저장-및-정리)

---

## 1. 환경 설정

### 1.1 프로젝트 디렉토리 생성

```bash
mkdir -p SubTopic_B_Crack_Segmentation/{data,notebooks,models,results}
cd SubTopic_B_Crack_Segmentation
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
import os

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

| 항목 | 내용 |
|------|------|
| 데이터셋명 | Crack Segmentation Dataset |
| 출처 | https://www.kaggle.com/datasets/lakshaymiddha/crack-segmentation-dataset |
| 이미지 수 | 약 11,200장 (12개 공개 데이터셋 통합) |
| 이미지 크기 | 448×448 픽셀 (정사각형, 통일) |
| 마스크 형식 | 바이너리 PNG (0=배경, 255=균열) — RLE 디코딩 불필요 |
| 분류 | 이진 세그먼테이션 (균열 vs 배경) |
| 대상 | 콘크리트, 포장도로, 교량, 공장 바닥 등 산업 구조물 |
| 폴더 구조 | Train/Test 사전 분리 완료 (images/ + masks/) |
| 특이사항 | "noncrack*" 패턴의 무결함 이미지 포함 (필터링 가능) |

### 2.2 기존 Severstal 데이터셋과의 차이

```
┌────────────────────────────────────────────────────────────────┐
│  왜 Crack Segmentation Dataset으로 변경했는가?                    │
├──────────────┬──────────────────────┬──────────────────────────┤
│ 항목          │ Severstal (기존)     │ Crack Segmentation (변경) │
├──────────────┼──────────────────────┼──────────────────────────┤
│ 이전 사용     │ ✗ 미니프로젝트 사용   │ ✓ 새로운 데이터           │
│ 이미지 크기   │ 256×1600 (비정형)    │ 448×448 (정사각형)        │
│ 마스크 형식   │ RLE 인코딩 (변환필요) │ PNG 바이너리 (즉시사용)    │
│ 클래스 수     │ 4종 (멀티레이블)      │ 1종 (이진: 균열/배경)     │
│ 전처리 부담   │ RLE 디코딩 필요      │ 거의 없음                │
│ 데이터 양     │ ~6,000장 (결함)      │ ~11,200장                │
│ 스마트팩토리   │ 철강 생산 라인       │ 시설 구조물 안전관리       │
└──────────────┴──────────────────────┴──────────────────────────┘
→ U-Net 모델 구현과 학습 자체에 더 집중할 수 있음!
```

### 2.3 다운로드

```bash
# Kaggle API
kaggle datasets download -d lakshaymiddha/crack-segmentation-dataset
unzip crack-segmentation-dataset.zip -d data/
```

다운로드 후 폴더 구조:
```
data/
├── train/
│   ├── images/     ← 학습 이미지 (~9,500장, .jpg)
│   └── masks/      ← 바이너리 마스크 (~9,500장, .png)
├── test/
│   ├── images/     ← 테스트 이미지 (~1,700장, .jpg)
│   └── masks/      ← 바이너리 마스크 (~1,700장, .png)
├── images/         ← 전체 이미지 (train+test 합본)
└── masks/          ← 전체 마스크 (train+test 합본)
```

### 2.4 데이터 탐색 (EDA)

```python
import matplotlib.pyplot as plt
from pathlib import Path
from PIL import Image
import cv2

DATA_DIR = Path("data")
TRAIN_IMG_DIR = DATA_DIR / "train" / "images"
TRAIN_MASK_DIR = DATA_DIR / "train" / "masks"
TEST_IMG_DIR = DATA_DIR / "test" / "images"
TEST_MASK_DIR = DATA_DIR / "test" / "masks"

# === 파일 수 확인 ===
train_images = sorted(list(TRAIN_IMG_DIR.glob("*")))
train_masks = sorted(list(TRAIN_MASK_DIR.glob("*")))
test_images = sorted(list(TEST_IMG_DIR.glob("*")))
test_masks = sorted(list(TEST_MASK_DIR.glob("*")))

print(f"=== 데이터 통계 ===")
print(f"Train 이미지: {len(train_images)}장")
print(f"Train 마스크: {len(train_masks)}장")
print(f"Test 이미지: {len(test_images)}장")
print(f"Test 마스크: {len(test_masks)}장")

# === 무결함(noncrack) 이미지 확인 ===
noncrack_train = [f for f in train_images if 'noncrack' in f.name.lower()]
crack_train = [f for f in train_images if 'noncrack' not in f.name.lower()]
print(f"\n무결함(noncrack) 이미지: {len(noncrack_train)}장")
print(f"균열(crack) 이미지: {len(crack_train)}장")

# === 이미지 크기 확인 ===
sample_img = Image.open(train_images[0])
sample_mask = Image.open(train_masks[0])
print(f"\n이미지 크기: {sample_img.size}")  # (448, 448)
print(f"마스크 크기: {sample_mask.size}")   # (448, 448)
print(f"이미지 모드: {sample_img.mode}")    # RGB
print(f"마스크 모드: {sample_mask.mode}")   # L (그레이스케일)

# === 마스크 값 분포 확인 ===
mask_np = np.array(sample_mask)
print(f"\n마스크 고유값: {np.unique(mask_np)}")  # [0, 255] 또는 [0, 128, 255]
print(f"마스크 형태: {mask_np.shape}")
```

### 2.5 샘플 이미지 시각화

```python
def visualize_samples(img_dir, mask_dir, num_samples=8,
                       save_path="results/01_sample_images.png"):
    """원본 이미지 + 마스크 + 오버레이 시각화"""

    img_files = sorted(list(img_dir.glob("*")))
    # 균열이 있는 이미지만 선택 (noncrack 제외)
    crack_files = [f for f in img_files if 'noncrack' not in f.name.lower()]
    selected = crack_files[:num_samples]

    fig, axes = plt.subplots(num_samples, 3, figsize=(12, 4 * num_samples))
    col_titles = ['원본 이미지', '균열 마스크 (GT)', '오버레이']

    for row, img_path in enumerate(selected):
        # 이미지 로드
        img = cv2.imread(str(img_path))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # 대응하는 마스크 찾기
        mask_path = mask_dir / img_path.name
        # 확장자가 다를 수 있으므로 stem으로 매칭
        if not mask_path.exists():
            mask_candidates = list(mask_dir.glob(f"{img_path.stem}.*"))
            mask_path = mask_candidates[0] if mask_candidates else None

        if mask_path and mask_path.exists():
            mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
            # 이진화 (128 이상 → 1)
            mask_binary = (mask > 128).astype(np.uint8)
        else:
            mask_binary = np.zeros(img.shape[:2], dtype=np.uint8)

        # 오버레이 생성 (균열 부분을 빨간색으로 표시)
        overlay = img.copy()
        overlay[mask_binary == 1] = overlay[mask_binary == 1] * 0.5 + np.array([255, 0, 0]) * 0.5

        # 균열 비율 계산
        crack_ratio = mask_binary.sum() / mask_binary.size * 100

        # 표시
        axes[row, 0].imshow(img)
        axes[row, 0].set_title(img_path.name[:25], fontsize=8)
        axes[row, 0].axis('off')

        axes[row, 1].imshow(mask_binary, cmap='gray')
        axes[row, 1].set_title(f'균열 비율: {crack_ratio:.1f}%', fontsize=9)
        axes[row, 1].axis('off')

        axes[row, 2].imshow(overlay.astype(np.uint8))
        axes[row, 2].set_title('오버레이', fontsize=9)
        axes[row, 2].axis('off')

    for col, title in enumerate(col_titles):
        axes[0, col].set_title(title + '\n' + axes[0, col].get_title(),
                               fontsize=10, fontweight='bold')

    plt.suptitle('산업 시설 표면 균열 — 샘플 이미지', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()

visualize_samples(TRAIN_IMG_DIR, TRAIN_MASK_DIR)
```

### 2.6 균열 비율 분포 분석

```python
def analyze_crack_distribution(img_dir, mask_dir,
                                save_path="results/02_crack_distribution.png"):
    """전체 데이터의 균열 비율 분포 분석"""

    crack_ratios = []
    img_files = sorted(list(img_dir.glob("*")))

    for img_path in img_files:
        mask_path = mask_dir / img_path.name
        if not mask_path.exists():
            mask_candidates = list(mask_dir.glob(f"{img_path.stem}.*"))
            if mask_candidates:
                mask_path = mask_candidates[0]
            else:
                continue

        mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
        if mask is not None:
            ratio = (mask > 128).sum() / mask.size * 100
            crack_ratios.append(ratio)

    crack_ratios = np.array(crack_ratios)

    fig, axes = plt.subplots(1, 3, figsize=(16, 4.5))

    # 1) 균열 비율 히스토그램
    axes[0].hist(crack_ratios, bins=50, color='#e74c3c', alpha=0.7, edgecolor='black')
    axes[0].set_xlabel('균열 비율 (%)')
    axes[0].set_ylabel('이미지 수')
    axes[0].set_title('균열 영역 비율 분포', fontweight='bold')
    axes[0].axvline(crack_ratios.mean(), color='blue', linestyle='--',
                    label=f'평균: {crack_ratios.mean():.1f}%')
    axes[0].legend()

    # 2) 균열 유무 분포
    has_crack = (crack_ratios > 0).sum()
    no_crack = (crack_ratios == 0).sum()
    axes[1].pie([has_crack, no_crack],
                labels=[f'균열 있음\n({has_crack})', f'균열 없음\n({no_crack})'],
                colors=['#e74c3c', '#2ecc71'], autopct='%1.1f%%', startangle=90)
    axes[1].set_title('균열 유무 분포', fontweight='bold')

    # 3) 균열 비율별 구간 분포
    bins = [0, 1, 5, 10, 20, 50, 100]
    labels = ['0~1%', '1~5%', '5~10%', '10~20%', '20~50%', '50%+']
    counts = np.histogram(crack_ratios[crack_ratios > 0], bins=bins)[0]
    axes[2].bar(labels, counts, color='#3498db')
    axes[2].set_title('균열 비율 구간별 분포', fontweight='bold')
    axes[2].set_ylabel('이미지 수')
    for i, v in enumerate(counts):
        axes[2].text(i, v + 5, str(v), ha='center', fontweight='bold', fontsize=8)

    plt.suptitle('균열 세그먼테이션 데이터 분석', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()

    print(f"\n=== 균열 비율 통계 ===")
    print(f"  전체 이미지: {len(crack_ratios)}장")
    print(f"  균열 있음: {(crack_ratios > 0).sum()}장 ({(crack_ratios > 0).mean()*100:.1f}%)")
    print(f"  평균 균열 비율: {crack_ratios[crack_ratios > 0].mean():.2f}%")
    print(f"  최대 균열 비율: {crack_ratios.max():.2f}%")

analyze_crack_distribution(TRAIN_IMG_DIR, TRAIN_MASK_DIR)
```

---

## 3. 데이터 전처리 및 DataLoader

### 3.1 핵심 설계 결정

| 항목 | 설정값 | 이유 |
|------|--------|------|
| 입력 크기 | 256×256 | 원본 448에서 축소하여 학습 속도/메모리 효율 향상 |
| 채널 수 | 3 (RGB) | 사전학습 인코더 호환 |
| 출력 채널 | 1 (이진 세그먼테이션) | 균열(1) vs 배경(0) |
| 배치 크기 | 16 | U-Net 메모리 사용량 고려 |
| noncrack 제외 | 균열 있는 이미지만 사용 | 학습 효율성 (빈 마스크 제거) |

### 3.2 커스텀 Dataset 클래스

```python
from torch.utils.data import Dataset, DataLoader
import albumentations as A
from albumentations.pytorch import ToTensorV2

class CrackDataset(Dataset):
    """
    산업 시설 균열 세그먼테이션 데이터셋

    특징:
      - 바이너리 마스크 직접 로드 (RLE 디코딩 불필요!)
      - 이진 세그먼테이션: 균열(1) vs 배경(0)
      - noncrack 이미지 필터링 옵션
    """

    def __init__(self, img_dir, mask_dir, img_size=256, transform=None,
                 filter_noncrack=True):
        """
        Args:
            img_dir: 이미지 폴더 경로
            mask_dir: 마스크 폴더 경로
            img_size: 리사이즈 크기
            transform: albumentations 변환
            filter_noncrack: True면 무결함 이미지 제외
        """
        self.img_dir = Path(img_dir)
        self.mask_dir = Path(mask_dir)
        self.img_size = img_size
        self.transform = transform

        # 이미지-마스크 쌍 매칭
        self.pairs = self._match_pairs(filter_noncrack)
        print(f"Dataset 생성: {len(self.pairs)}장"
              f"{' (noncrack 제외)' if filter_noncrack else ''}")

    def _match_pairs(self, filter_noncrack):
        """이미지와 마스크를 파일명으로 매칭"""
        pairs = []
        img_files = sorted(list(self.img_dir.glob("*")))

        for img_path in img_files:
            # noncrack 필터링
            if filter_noncrack and 'noncrack' in img_path.name.lower():
                continue

            # 대응 마스크 찾기 (확장자 무관하게 stem으로 매칭)
            mask_path = self.mask_dir / img_path.name
            if not mask_path.exists():
                candidates = list(self.mask_dir.glob(f"{img_path.stem}.*"))
                mask_path = candidates[0] if candidates else None

            if mask_path and mask_path.exists():
                pairs.append((img_path, mask_path))

        return pairs

    def __len__(self):
        return len(self.pairs)

    def __getitem__(self, idx):
        img_path, mask_path = self.pairs[idx]

        # === 이미지 로드 (RGB) ===
        image = cv2.imread(str(img_path))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # === 마스크 로드 (그레이스케일 → 이진화) ===
        mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
        mask = (mask > 128).astype(np.float32)  # 0 또는 1로 이진화

        # === 데이터 증강 (albumentations) ===
        if self.transform:
            augmented = self.transform(image=image, mask=mask)
            image = augmented['image']    # (C, H, W) 텐서
            mask = augmented['mask']      # (H, W) 텐서
        else:
            image = cv2.resize(image, (self.img_size, self.img_size))
            mask = cv2.resize(mask, (self.img_size, self.img_size))
            image = torch.from_numpy(image).permute(2, 0, 1).float() / 255.0
            mask = torch.from_numpy(mask).float()

        # mask: (H, W) → (1, H, W) — 채널 차원 추가
        if mask.dim() == 2:
            mask = mask.unsqueeze(0)

        return image, mask
```

### 3.3 데이터 증강 정의

```python
IMG_SIZE = 256

# === 학습용 증강 ===
train_aug = A.Compose([
    A.Resize(IMG_SIZE, IMG_SIZE),
    A.HorizontalFlip(p=0.5),
    A.VerticalFlip(p=0.3),
    A.RandomRotate90(p=0.5),
    A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=0.5),
    A.ShiftScaleRotate(shift_limit=0.05, scale_limit=0.1, rotate_limit=15, p=0.4),
    A.GaussNoise(var_limit=(10, 50), p=0.3),
    A.OneOf([
        A.ElasticTransform(alpha=120, sigma=120*0.05, p=0.3),
        A.GridDistortion(p=0.3),
    ], p=0.3),
    A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ToTensorV2(),
])

# === 검증용 (증강 없음) ===
val_aug = A.Compose([
    A.Resize(IMG_SIZE, IMG_SIZE),
    A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ToTensorV2(),
])
```

### 3.4 Train / Validation 분리 및 DataLoader

```python
from sklearn.model_selection import train_test_split

# === 기존 Train 셋에서 Validation 분리 (8:2) ===
full_dataset = CrackDataset(TRAIN_IMG_DIR, TRAIN_MASK_DIR, IMG_SIZE,
                             transform=None, filter_noncrack=True)
all_pairs = full_dataset.pairs

train_pairs, val_pairs = train_test_split(all_pairs, test_size=0.2, random_state=SEED)
print(f"Train: {len(train_pairs)}장 / Val: {len(val_pairs)}장")

# === 분리된 쌍으로 Dataset 재생성 ===
class CrackDatasetFromPairs(Dataset):
    """이미지-마스크 쌍 리스트로부터 Dataset 생성"""
    def __init__(self, pairs, img_size=256, transform=None):
        self.pairs = pairs
        self.img_size = img_size
        self.transform = transform

    def __len__(self):
        return len(self.pairs)

    def __getitem__(self, idx):
        img_path, mask_path = self.pairs[idx]
        image = cv2.imread(str(img_path))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
        mask = (mask > 128).astype(np.float32)

        if self.transform:
            augmented = self.transform(image=image, mask=mask)
            image = augmented['image']
            mask = augmented['mask']
        else:
            image = cv2.resize(image, (self.img_size, self.img_size))
            mask = cv2.resize(mask, (self.img_size, self.img_size))
            image = torch.from_numpy(image).permute(2, 0, 1).float() / 255.0
            mask = torch.from_numpy(mask).float()

        if mask.dim() == 2:
            mask = mask.unsqueeze(0)
        return image, mask

train_dataset = CrackDatasetFromPairs(train_pairs, IMG_SIZE, transform=train_aug)
val_dataset = CrackDatasetFromPairs(val_pairs, IMG_SIZE, transform=val_aug)
test_dataset = CrackDataset(TEST_IMG_DIR, TEST_MASK_DIR, IMG_SIZE,
                             transform=val_aug, filter_noncrack=True)

BATCH_SIZE = 16
train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE,
                          shuffle=True, num_workers=2, pin_memory=True)
val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE,
                        shuffle=False, num_workers=2, pin_memory=True)
test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE,
                         shuffle=False, num_workers=2, pin_memory=True)

# === 배치 형태 확인 ===
images, masks = next(iter(train_loader))
print(f"\n이미지 배치: {images.shape}")   # (16, 3, 256, 256)
print(f"마스크 배치: {masks.shape}")      # (16, 1, 256, 256)
print(f"마스크 값 범위: {masks.min():.1f} ~ {masks.max():.1f}")
print(f"균열 픽셀 비율: {masks.mean()*100:.2f}%")
```

---

## 4. U-Net 모델 구현

### 4.1 아키텍처

```
이진 세그먼테이션 U-Net (출력 채널 = 1):

  입력 (3, 256, 256)
    │
    ▼ DoubleConv(3→64) ────── Skip ──────→ DoubleConv + Conv1x1 → 출력(1, 256, 256)
    ▼ MaxPool → DoubleConv(64→128) ─ Skip ─→ Up + DoubleConv
    ▼ MaxPool → DoubleConv(128→256) ─ Skip ─→ Up + DoubleConv
    ▼ MaxPool → DoubleConv(256→512) ─ Skip ─→ Up + DoubleConv
    ▼ MaxPool → DoubleConv(512→1024) ─ Bottleneck ─┘

  최종 출력: (1, 256, 256) — Sigmoid → 0~1 확률 → 0.5 임계값 → 이진 마스크
```

### 4.2 코드 구현

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
    U-Net 이진 세그먼테이션 모델

    인코더: 이미지를 점점 압축 → "무엇이 있는지" 파악
    디코더: 다시 복원 → "어디에 있는지" 위치 복원
    Skip Connection: 인코더 위치 정보 → 디코더에 직접 전달

    Args:
        in_ch: 입력 채널 (RGB = 3)
        out_ch: 출력 채널 (이진 세그먼테이션 = 1)
    """
    def __init__(self, in_ch=3, out_ch=1, features=[64, 128, 256, 512]):
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

        # 최종 1×1 Conv (이진 출력)
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
                x = F.interpolate(x, size=skip.shape[2:],
                                  mode='bilinear', align_corners=True)
            x = torch.cat([skip, x], dim=1)
            x = self.decoders[idx](x)

        return self.final(x)  # (B, 1, H, W) — 로짓 출력


# === 모델 생성 ===
model = UNet(in_ch=3, out_ch=1).to(device)
total_params = sum(p.numel() for p in model.parameters())
print(f"U-Net 파라미터: {total_params:,}개")

dummy = torch.randn(1, 3, 256, 256).to(device)
print(f"입력: {dummy.shape} → 출력: {model(dummy).shape}")
# 입력: (1, 3, 256, 256) → 출력: (1, 1, 256, 256)
```

---

## 5. 손실 함수 구현 — Dice Loss + BCE

### 5.1 왜 결합 손실이 필요한가

```
균열은 전체 이미지 픽셀의 1~10%에 불과합니다.
→ "전부 배경"으로 예측해도 Accuracy 90%+
→ BCE만 쓰면 "항상 배경" 전략을 학습할 위험

해결: BCE + Dice Loss 결합
  BCE  → 각 픽셀을 정확히 맞추도록 학습
  Dice → 균열 영역의 "겹침 비율"을 직접 최적화
```

### 5.2 구현

```python
class DiceLoss(nn.Module):
    """Dice Loss: 1 - (2·|pred ∩ target|) / (|pred| + |target|)"""
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
    """
    BCE + Dice Loss 결합

    BCE:  픽셀 단위 정밀도 → "각 픽셀을 정확히 맞추자"
    Dice: 영역 단위 겹침   → "균열 영역을 전체적으로 잘 잡자"
    """
    def __init__(self, bce_w=0.5, dice_w=0.5):
        super().__init__()
        self.bce = nn.BCEWithLogitsLoss()
        self.dice = DiceLoss()
        self.bce_w = bce_w
        self.dice_w = dice_w

    def forward(self, pred, target):
        return self.bce_w * self.bce(pred, target) + self.dice_w * self.dice(pred, target)


criterion = CombinedLoss(bce_w=0.5, dice_w=0.5)
```

---

## 6. 학습 루프 구현

### 6.1 평가 지표 함수

```python
def compute_dice(pred, target, threshold=0.5):
    """Dice 계수 계산"""
    pred = (torch.sigmoid(pred) > threshold).float()
    smooth = 1.0
    inter = (pred.view(-1) * target.view(-1)).sum()
    return ((2 * inter + smooth) /
            (pred.view(-1).sum() + target.view(-1).sum() + smooth)).item()

def compute_iou(pred, target, threshold=0.5):
    """IoU 계산"""
    pred = (torch.sigmoid(pred) > threshold).float()
    smooth = 1.0
    inter = (pred.view(-1) * target.view(-1)).sum()
    union = pred.view(-1).sum() + target.view(-1).sum() - inter
    return ((inter + smooth) / (union + smooth)).item()

def compute_pixel_acc(pred, target, threshold=0.5):
    """픽셀 정확도 계산"""
    pred = (torch.sigmoid(pred) > threshold).float()
    correct = (pred == target).float().sum()
    total = target.numel()
    return (correct / total).item()
```

### 6.2 학습/검증 루프

```python
from tqdm import tqdm
import time

def train_one_epoch(model, loader, criterion, optimizer, device):
    model.train()
    total_loss, total_dice, total_iou, count = 0, 0, 0, 0
    for images, masks in tqdm(loader, desc="  Train", leave=False):
        images, masks = images.to(device), masks.to(device)
        outputs = model(images)
        loss = criterion(outputs, masks)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * images.size(0)
        total_dice += compute_dice(outputs, masks) * images.size(0)
        total_iou += compute_iou(outputs, masks) * images.size(0)
        count += images.size(0)
    return total_loss / count, total_dice / count, total_iou / count

def evaluate(model, loader, criterion, device):
    model.eval()
    total_loss, total_dice, total_iou, total_acc, count = 0, 0, 0, 0, 0
    with torch.no_grad():
        for images, masks in tqdm(loader, desc="  Val", leave=False):
            images, masks = images.to(device), masks.to(device)
            outputs = model(images)
            loss = criterion(outputs, masks)
            total_loss += loss.item() * images.size(0)
            total_dice += compute_dice(outputs, masks) * images.size(0)
            total_iou += compute_iou(outputs, masks) * images.size(0)
            total_acc += compute_pixel_acc(outputs, masks) * images.size(0)
            count += images.size(0)
    return (total_loss / count, total_dice / count,
            total_iou / count, total_acc / count)
```

### 6.3 전체 학습 실행

```python
def train_unet(model, train_loader, val_loader, criterion,
               num_epochs=30, lr=1e-4, model_name="unet"):
    """U-Net 학습 전체 파이프라인"""

    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='max', factor=0.5, patience=5, verbose=True
    )

    history = {'train_loss': [], 'train_dice': [], 'train_iou': [],
               'val_loss': [], 'val_dice': [], 'val_iou': [], 'val_acc': []}
    best_dice = 0.0
    start = time.time()

    for epoch in range(num_epochs):
        print(f"\nEpoch [{epoch+1}/{num_epochs}]")

        tl, td, ti = train_one_epoch(model, train_loader, criterion, optimizer, device)
        vl, vd, vi, va = evaluate(model, val_loader, criterion, device)
        scheduler.step(vd)

        history['train_loss'].append(tl); history['train_dice'].append(td)
        history['train_iou'].append(ti)
        history['val_loss'].append(vl); history['val_dice'].append(vd)
        history['val_iou'].append(vi); history['val_acc'].append(va)

        print(f"  Train — Loss: {tl:.4f} | Dice: {td:.4f} | IoU: {ti:.4f}")
        print(f"  Val   — Loss: {vl:.4f} | Dice: {vd:.4f} | IoU: {vi:.4f} | Acc: {va:.4f}")

        if vd > best_dice:
            best_dice = vd
            torch.save(model.state_dict(), f"models/best_{model_name}.pth")
            print(f"  ★ Best 저장! (Dice: {vd:.4f})")

    elapsed = time.time() - start
    print(f"\n완료! {elapsed/60:.1f}분 소요 | Best Dice: {best_dice:.4f}")
    model.load_state_dict(torch.load(f"models/best_{model_name}.pth"))
    return model, history


# === 학습 실행 ===
model, history = train_unet(
    model, train_loader, val_loader, criterion,
    num_epochs=30, lr=1e-4, model_name="unet_vanilla"
)
```

---

## 7. 평가 및 시각화

### 7.1 학습 곡선

```python
def plot_curves(history, save_path="results/03_training_curves.png"):
    fig, axes = plt.subplots(1, 4, figsize=(20, 4.5))
    ep = range(1, len(history['train_loss']) + 1)

    # Loss
    axes[0].plot(ep, history['train_loss'], 'b--', alpha=0.7, label='Train')
    axes[0].plot(ep, history['val_loss'], 'r-', label='Val')
    axes[0].set_title('Loss (BCE + Dice)', fontweight='bold')
    axes[0].legend(); axes[0].grid(True, alpha=0.3)

    # Dice
    axes[1].plot(ep, history['train_dice'], 'b--', alpha=0.7, label='Train')
    axes[1].plot(ep, history['val_dice'], 'r-', label='Val')
    axes[1].set_title('Dice Coefficient', fontweight='bold')
    axes[1].legend(); axes[1].grid(True, alpha=0.3)

    # IoU
    axes[2].plot(ep, history['train_iou'], 'b--', alpha=0.7, label='Train')
    axes[2].plot(ep, history['val_iou'], 'g-', label='Val')
    axes[2].set_title('IoU', fontweight='bold')
    axes[2].legend(); axes[2].grid(True, alpha=0.3)

    # Pixel Accuracy
    axes[3].plot(ep, history['val_acc'], 'purple', label='Val Pixel Acc')
    axes[3].set_title('Pixel Accuracy (Val)', fontweight='bold')
    axes[3].legend(); axes[3].grid(True, alpha=0.3)

    plt.suptitle('U-Net 균열 세그먼테이션 학습 곡선', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()

plot_curves(history)
```

### 7.2 예측 결과 시각화

```python
def visualize_predictions(model, dataset, device, num_samples=6,
                           save_path="results/04_predictions.png"):
    """검증 데이터에서 예측 결과 시각화"""
    model.eval()

    fig, axes = plt.subplots(num_samples, 4, figsize=(18, 4 * num_samples))
    col_titles = ['원본 이미지', '정답 마스크 (GT)', '예측 마스크 (Pred)', '오버레이 비교']
    indices = np.random.choice(len(dataset), num_samples, replace=False)

    for row, idx in enumerate(indices):
        image, gt_mask = dataset[idx]

        with torch.no_grad():
            pred_logits = model(image.unsqueeze(0).to(device))
            pred_mask = (torch.sigmoid(pred_logits) > 0.5).float().cpu().squeeze()

        # 이미지 역정규화
        img_np = image.permute(1, 2, 0).numpy()
        img_np = img_np * np.array([0.229, 0.224, 0.225]) + np.array([0.485, 0.456, 0.406])
        img_np = np.clip(img_np, 0, 1)

        gt_np = gt_mask.squeeze().numpy()
        pred_np = pred_mask.numpy()

        # 오버레이: 노랑=정확, 초록=놓침(FN), 빨강=오탐(FP)
        overlay = img_np.copy()
        both = (gt_np > 0.5) & (pred_np > 0.5)      # True Positive
        only_gt = (gt_np > 0.5) & (pred_np < 0.5)    # False Negative
        only_pred = (gt_np < 0.5) & (pred_np > 0.5)  # False Positive

        overlay[both] = [1, 1, 0]       # 노랑: 정확한 예측
        overlay[only_gt] = [0, 1, 0]    # 초록: 놓친 균열 (FN)
        overlay[only_pred] = [1, 0, 0]  # 빨강: 잘못 예측 (FP)

        # Dice 계산
        sample_dice = compute_dice(
            pred_logits.cpu().squeeze().unsqueeze(0).unsqueeze(0),
            gt_mask.unsqueeze(0)
        )

        axes[row, 0].imshow(img_np); axes[row, 0].axis('off')
        axes[row, 1].imshow(gt_np, cmap='gray'); axes[row, 1].axis('off')
        axes[row, 2].imshow(pred_np, cmap='gray')
        axes[row, 2].set_title(f'Dice: {sample_dice:.3f}', fontsize=9)
        axes[row, 2].axis('off')
        axes[row, 3].imshow(overlay)
        axes[row, 3].set_title('노랑=정확 | 초록=놓침 | 빨강=오탐', fontsize=7)
        axes[row, 3].axis('off')

    for c, t in enumerate(col_titles):
        axes[0, c].set_title(t, fontsize=10, fontweight='bold')

    plt.suptitle('U-Net 균열 세그먼테이션 예측 결과', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()

visualize_predictions(model, val_dataset, device)
```

### 7.3 테스트 셋 최종 평가

```python
def final_test_evaluation(model, test_loader, criterion, device,
                           save_path="results/05_test_metrics.png"):
    """테스트 셋 최종 성능 평가"""
    vl, vd, vi, va = evaluate(model, test_loader, criterion, device)

    print(f"\n{'='*50}")
    print(f"{'테스트 셋 최종 성능':^50}")
    print(f"{'='*50}")
    print(f"  Loss:           {vl:.4f}")
    print(f"  Dice:           {vd:.4f}")
    print(f"  IoU:            {vi:.4f}")
    print(f"  Pixel Accuracy: {va:.4f} ({va*100:.1f}%)")

    # 막대그래프
    fig, ax = plt.subplots(figsize=(8, 5))
    metrics = {'Dice': vd, 'IoU': vi, 'Pixel Acc': va}
    bars = ax.bar(metrics.keys(), metrics.values(),
                  color=['#e74c3c', '#3498db', '#2ecc71'])
    ax.set_ylim(0, 1.05)
    ax.set_title('U-Net 테스트 셋 최종 성능', fontweight='bold')
    for bar, val in zip(bars, metrics.values()):
        ax.text(bar.get_x() + bar.get_width()/2, val + 0.02,
                f'{val:.4f}', ha='center', fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()

    return {'loss': vl, 'dice': vd, 'iou': vi, 'pixel_acc': va}

test_metrics = final_test_evaluation(model, test_loader, criterion, device)
```

---

## 8. 추가 실험 — ResNet 백본 U-Net 비교

### 8.1 ResNet34 인코더 U-Net

```python
import torchvision.models as models

class ResNetUNet(nn.Module):
    """ResNet34 백본 인코더 U-Net (전이학습)"""
    def __init__(self, out_ch=1):
        super().__init__()
        resnet = models.resnet34(weights=models.ResNet34_Weights.IMAGENET1K_V1)

        self.enc1 = nn.Sequential(resnet.conv1, resnet.bn1, resnet.relu)  # (64)
        self.pool1 = resnet.maxpool
        self.enc2 = resnet.layer1  # (64)
        self.enc3 = resnet.layer2  # (128)
        self.enc4 = resnet.layer3  # (256)
        self.enc5 = resnet.layer4  # (512)

        self.up4 = nn.ConvTranspose2d(512, 256, 2, stride=2)
        self.dec4 = DoubleConv(512, 256)
        self.up3 = nn.ConvTranspose2d(256, 128, 2, stride=2)
        self.dec3 = DoubleConv(256, 128)
        self.up2 = nn.ConvTranspose2d(128, 64, 2, stride=2)
        self.dec2 = DoubleConv(128, 64)
        self.up1 = nn.ConvTranspose2d(64, 64, 2, stride=2)
        self.dec1 = DoubleConv(128, 64)
        self.up0 = nn.ConvTranspose2d(64, 32, 2, stride=2)
        self.dec0 = DoubleConv(32, 32)
        self.final = nn.Conv2d(32, out_ch, 1)

    def forward(self, x):
        e1 = self.enc1(x)
        e2 = self.enc2(self.pool1(e1))
        e3 = self.enc3(e2)
        e4 = self.enc4(e3)
        e5 = self.enc5(e4)

        d4 = self.dec4(torch.cat([self.up4(e5), e4], dim=1))
        d3 = self.dec3(torch.cat([self.up3(d4), e3], dim=1))
        d2 = self.dec2(torch.cat([self.up2(d3), e2], dim=1))
        d1 = self.dec1(torch.cat([self.up1(d2), e1], dim=1))
        d0 = self.dec0(self.up0(d1))
        return self.final(d0)


# === ResNet U-Net 학습 ===
resnet_unet = ResNetUNet(out_ch=1).to(device)
resnet_params = sum(p.numel() for p in resnet_unet.parameters())
print(f"ResNet U-Net 파라미터: {resnet_params:,}개")

resnet_model, resnet_history = train_unet(
    resnet_unet, train_loader, val_loader, criterion,
    num_epochs=20, lr=1e-4, model_name="unet_resnet34"
)
```

### 8.2 Vanilla U-Net vs ResNet U-Net 비교

```python
def compare_models(histories, names, save_path="results/06_model_comparison.png"):
    """2개 모델 성능 비교"""

    # Dice/IoU 학습 곡선 비교
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    colors = ['#e74c3c', '#3498db']

    for idx, (hist, name) in enumerate(zip(histories, names)):
        ep = range(1, len(hist['val_dice']) + 1)
        axes[0].plot(ep, hist['val_dice'], color=colors[idx], label=name)
        axes[1].plot(ep, hist['val_iou'], color=colors[idx], label=name)
        axes[2].plot(ep, hist['val_loss'], color=colors[idx], label=name)

    axes[0].set_title('Val Dice', fontweight='bold')
    axes[1].set_title('Val IoU', fontweight='bold')
    axes[2].set_title('Val Loss', fontweight='bold')
    for ax in axes:
        ax.legend(); ax.grid(True, alpha=0.3); ax.set_xlabel('Epoch')

    plt.suptitle('Vanilla U-Net vs ResNet34 U-Net', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()

    # 최종 성능 비교 테이블
    print(f"\n{'='*55}")
    print(f"{'모델 비교 (Best Validation)':^55}")
    print(f"{'='*55}")
    print(f"{'모델':<20} {'Best Dice':>12} {'Best IoU':>12}")
    print(f"{'-'*55}")
    for hist, name in zip(histories, names):
        bd = max(hist['val_dice'])
        bi = max(hist['val_iou'])
        print(f"{name:<20} {bd:>12.4f} {bi:>12.4f}")

compare_models([history, resnet_history], ['Vanilla U-Net', 'ResNet34 U-Net'])
```

---

## 9. 결과 저장 및 정리

### 9.1 결과 JSON

```python
import json

# 최고 모델 판정
vanilla_best = max(history['val_dice'])
resnet_best = max(resnet_history['val_dice'])
best_name = "Vanilla U-Net" if vanilla_best >= resnet_best else "ResNet34 U-Net"

summary = {
    "project": "산업 시설 표면 균열 세그먼테이션",
    "dataset": "Crack Segmentation Dataset (11,200장, 바이너리 마스크)",
    "input_size": f"{IMG_SIZE}x{IMG_SIZE}",
    "task": "이진 세그먼테이션 (균열 vs 배경)",
    "loss": "BCE(0.5) + Dice(0.5)",
    "models": {
        "vanilla_unet": {
            "best_dice": round(vanilla_best, 4),
            "best_iou": round(max(history['val_iou']), 4),
            "test": {k: round(v, 4) for k, v in test_metrics.items()} if 'test_metrics' in dir() else {}
        },
        "resnet34_unet": {
            "best_dice": round(resnet_best, 4),
            "best_iou": round(max(resnet_history['val_iou']), 4),
        }
    },
    "best_model": best_name
}

with open("results/07_final_summary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)
print("저장 완료: results/07_final_summary.json")
```

### 9.2 최종 출력 파일 목록

```
results/
├── 01_sample_images.png           ← 원본/마스크/오버레이 샘플
├── 02_crack_distribution.png      ← 균열 비율 분포 분석
├── 03_training_curves.png         ← Loss/Dice/IoU/PixelAcc 학습 곡선
├── 04_predictions.png             ← GT vs Pred 시각화 (노랑/초록/빨강)
├── 05_test_metrics.png            ← 테스트 셋 최종 성능 막대그래프
├── 06_model_comparison.png        ← Vanilla vs ResNet U-Net 비교
└── 07_final_summary.json          ← 성능 지표 JSON

models/
├── best_unet_vanilla.pth          ← Vanilla U-Net 가중치
└── best_unet_resnet34.pth         ← ResNet34 U-Net 가중치
```

---

## 부록: Claude Code 실행 순서 요약

```
[Step 1] 환경 설정
  → 디렉토리, 패키지, GPU/시드

[Step 2] 데이터 탐색
  → 이미지/마스크 매칭 확인, 균열 비율 분포, 샘플 시각화

[Step 3] Dataset + DataLoader
  → CrackDataset (바이너리 마스크 직접 로드), 증강, Train/Val 분리

[Step 4] U-Net 구현
  → DoubleConv → Encoder → Bottleneck → Decoder → 1채널 출력

[Step 5] 손실 함수
  → DiceLoss + BCEWithLogitsLoss 결합

[Step 6] 학습 (30 에폭)
  → Adam, ReduceLROnPlateau, Dice/IoU/PixelAcc 추적

[Step 7] 평가 및 시각화
  → 학습 곡선, 예측 비교 (GT vs Pred), 테스트 성능

[Step 8] 추가 실험
  → ResNet34 백본 U-Net 학습 → Vanilla 대비 성능 비교

[Step 9] 결과 저장
  → JSON 요약, 그래프 이미지
```

### 예상 소요 시간

| 단계 | GPU (Colab T4) | CPU Only |
|------|:-:|:-:|
| 데이터 준비 + EDA | 5분 | 5분 |
| Vanilla U-Net 학습 (30 에폭) | 20~30분 | 3~5시간 |
| ResNet34 U-Net 학습 (20 에폭) | 15~20분 | 2~3시간 |
| 평가 + 시각화 | 5분 | 10분 |
| **총 소요 시간 (1모델)** | **약 30~40분** | **약 4시간** |
| **총 소요 시간 (2모델)** | **약 50~60분** | **약 6~8시간** |

### 목표 성능 기준

| 지표 | 최소 기준 | 우수 기준 |
|------|:-:|:-:|
| Dice Coefficient | ≥ 0.60 | ≥ 0.78 |
| IoU | ≥ 0.50 | ≥ 0.65 |
| Pixel Accuracy | ≥ 90% | ≥ 95% |

### 기존 Severstal 가이드 대비 변경 사항 요약

| 항목 | Severstal (기존) | Crack (변경 후) |
|------|:-:|:-:|
| 데이터 로드 | RLE 디코딩 함수 필요 | **PNG 직접 로드 (2줄)** |
| 출력 채널 | 4 (멀티레이블) | **1 (이진)** |
| Dataset 복잡도 | CSV 파싱 + RLE + 4채널 마스크 | **이미지/마스크 폴더 매칭** |
| 클래스별 분석 | 4종 결함별 Dice/IoU | **전체 Dice/IoU (이진)** |
| 추가 실험 | 없음 | **ResNet34 백본 비교 추가** |
| 시각화 | 4색 컬러 마스크 | **이진 흑백 + 3색 오버레이** |

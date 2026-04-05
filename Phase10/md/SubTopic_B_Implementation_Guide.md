# 🏭 소주제 B. 자석 타일 표면 결함 세그먼테이션 — 상세 구현 가이드라인

> **Claude Code에서 단계별로 실행할 수 있는 구현 명세서**
>
> 핵심 기술: U-Net / Attention U-Net (인코더-디코더 + Attention Gate) + Focal Tversky Loss + TTA
>
> 데이터: Magnetic Tile Surface Defects (영구자석 모터 부품 제조 공정)

---

## 목차

1. [환경 설정](#1-환경-설정)
2. [데이터 다운로드 및 탐색](#2-데이터-다운로드-및-탐색)
3. [데이터 전처리 및 DataLoader](#3-데이터-전처리-및-dataloader)
4. [U-Net 모델 구현](#4-u-net-모델-구현)
5. [Attention U-Net 구현](#5-attention-u-net-구현)
6. [손실 함수 — Dice Loss + BCE + Focal Tversky](#6-손실-함수--dice-loss--bce--focal-tversky)
7. [학습 루프 구현](#7-학습-루프-구현)
8. [평가 및 시각화 + TTA](#8-평가-및-시각화--tta)
9. [추가 실험 — ResNet34 백본 + 3모델 비교](#9-추가-실험--resnet34-백본--3모델-비교)
10. [결과 저장 및 정리](#10-결과-저장-및-정리)

---

## 1. 환경 설정

### 1.1 프로젝트 디렉토리

```bash
mkdir -p SubTopic_B_MagneticTile_Segmentation/{data,notebooks,models,results}
cd SubTopic_B_MagneticTile_Segmentation
```

### 1.2 패키지 설치

```bash
pip install torch torchvision matplotlib seaborn scikit-learn pillow tqdm pandas albumentations opencv-python
```

### 1.3 GPU 및 시드 고정

```python
import torch, numpy as np, random, os, cv2
from pathlib import Path
from PIL import Image
import matplotlib.pyplot as plt

SEED = 42
random.seed(SEED); np.random.seed(SEED)
torch.manual_seed(SEED); torch.cuda.manual_seed_all(SEED)
torch.backends.cudnn.deterministic = True

device = torch.device('cuda' if torch.cuda.is_available() else
                       'mps'  if torch.backends.mps.is_available() else 'cpu')
print(f"PyTorch: {torch.__version__} | Device: {device}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
```

---

## 2. 데이터 다운로드 및 탐색

### 2.1 데이터셋 정보

| 항목 | 내용 |
|------|------|
| 데이터셋명 | Magnetic Tile Surface Defects |
| 출처 | https://www.kaggle.com/datasets/alex000kim/magnetic-tile-surface-defects |
| 원본 출처 | https://github.com/abin24/Magnetic-tile-defect-datasets |
| 이미지 수 | 1,344장 (결함 392장 + 정상 952장) |
| 이미지 형식 | 그레이스케일, 크기 다양 (리사이즈 필요) |
| 마스크 | 픽셀 레벨 세그먼테이션 마스크 제공 |
| 결함 유형 | 5종 (Blowhole, Break, Crack, Fray, Uneven) + Free(정상) |
| 산업 맥락 | 영구자석 모터 핵심 부품 — 제조 공정 품질관리 직접 연결 |

### 2.2 결함 유형 설명

```
┌──────────────────────────────────────────────────────────────┐
│  자석 타일 표면 결함 5종 (영구자석 모터 제조)                    │
├──────────────┬───────────────────────────────────────────────┤
│ Blowhole     │ 기공(블로홀) — 제조 시 가스에 의한 구멍 (115장) │
│ Break        │ 파손/깨짐 — 물리적 충격에 의한 균열 (85장)      │
│ Crack        │ 균열 — 미세한 표면 갈라짐 (57장)               │
│ Fray         │ 마모/탈락 — 가장자리 닳아짐 (32장)              │
│ Uneven       │ 연삭 불균일 — 연마 공정의 불균일 (103장)        │
│ Free         │ 정상 — 결함 없음 (952장)                       │
└──────────────┴───────────────────────────────────────────────┘
→ 결함 이미지 총 392장 — 데이터 증강이 핵심!
→ Crack/Fray는 각각 57/32장 → Attention Gate + Focal Tversky로 대응
```

### 2.3 다운로드

```bash
kaggle datasets download -d alex000kim/magnetic-tile-surface-defects
unzip magnetic-tile-surface-defects.zip -d data/
```

폴더 구조:
```
data/Magnetic-tile-defect-datasets./
├── Blowhole/
│   ├── Imgs/          ← 이미지 (.jpg)
│   └── Masks/         ← 세그먼테이션 마스크 (.png)
├── Break/
│   ├── Imgs/
│   └── Masks/
├── Crack/
│   ├── Imgs/
│   └── Masks/
├── Fray/
│   ├── Imgs/
│   └── Masks/
├── Uneven/
│   ├── Imgs/
│   └── Masks/
└── Free/
    └── Imgs/          ← 정상 이미지 (마스크 없음)
```

### 2.4 데이터 탐색 (EDA)

```python
DATA_ROOT = Path("data/Magnetic-tile-defect-datasets.")
DEFECT_TYPES = ['Blowhole', 'Break', 'Crack', 'Fray', 'Uneven']

# === 클래스별 이미지 수 확인 ===
print("=== 데이터 통계 ===")
total_defect = 0
for defect in DEFECT_TYPES:
    img_dir = DATA_ROOT / defect / "Imgs"
    count = len(list(img_dir.glob("*"))) if img_dir.exists() else 0
    total_defect += count
    print(f"  {defect:<12s}: {count}장")

free_dir = DATA_ROOT / "Free" / "Imgs"
free_count = len(list(free_dir.glob("*"))) if free_dir.exists() else 0
print(f"  {'Free':<12s}: {free_count}장 (정상)")
print(f"\n  결함 합계: {total_defect}장 / 정상: {free_count}장 / 총: {total_defect + free_count}장")

# === 이미지 크기 분포 확인 ===
sizes = []
for defect in DEFECT_TYPES:
    img_dir = DATA_ROOT / defect / "Imgs"
    for img_path in img_dir.glob("*"):
        img = Image.open(img_path)
        sizes.append(img.size)

sizes = np.array(sizes)
print(f"\n=== 이미지 크기 ===")
print(f"  너비: {sizes[:,0].min()} ~ {sizes[:,0].max()} (평균: {sizes[:,0].mean():.0f})")
print(f"  높이: {sizes[:,1].min()} ~ {sizes[:,1].max()} (평균: {sizes[:,1].mean():.0f})")
print(f"  → 크기가 다양! → 통일 리사이즈 필요")

# === 클래스 분포 시각화 ===
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

defect_counts = []
for d in DEFECT_TYPES:
    img_dir = DATA_ROOT / d / "Imgs"
    defect_counts.append(len(list(img_dir.glob("*"))))

colors = ['#e74c3c', '#f39c12', '#3498db', '#9b59b6', '#1abc9c']
bars = axes[0].bar(DEFECT_TYPES, defect_counts, color=colors)
axes[0].set_title('결함 유형별 이미지 수', fontweight='bold')
axes[0].set_ylabel('이미지 수')
for bar, val in zip(bars, defect_counts):
    axes[0].text(bar.get_x() + bar.get_width()/2, val + 2, str(val),
                 ha='center', fontweight='bold')

axes[1].pie([total_defect, free_count],
            labels=[f'결함\n({total_defect})', f'정상\n({free_count})'],
            colors=['#e74c3c', '#2ecc71'], autopct='%1.1f%%', startangle=90)
axes[1].set_title('결함 vs 정상 분포', fontweight='bold')

plt.tight_layout()
plt.savefig("results/01_data_distribution.png", dpi=150, bbox_inches='tight')
plt.show()
```

### 2.5 샘플 이미지 + 마스크 시각화

```python
def visualize_defect_samples(data_root, save_path="results/02_sample_images.png"):
    """각 결함 유형별 이미지 + 마스크 + 오버레이"""

    fig, axes = plt.subplots(5, 3, figsize=(12, 18))
    col_titles = ['원본 이미지', '결함 마스크 (GT)', '오버레이']

    for row, defect in enumerate(DEFECT_TYPES):
        img_dir = data_root / defect / "Imgs"
        mask_dir = data_root / defect / "Masks"

        img_files = sorted(list(img_dir.glob("*")))
        if not img_files:
            continue
        img_path = img_files[0]

        img = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)

        mask_files = sorted(list(mask_dir.glob("*")))
        mask = cv2.imread(str(mask_files[0]), cv2.IMREAD_GRAYSCALE) if mask_files else np.zeros_like(img)
        mask_binary = (mask > 128).astype(np.uint8)

        img_rgb = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        overlay = img_rgb.copy()
        overlay[mask_binary == 1] = overlay[mask_binary == 1] * 0.5 + np.array([255, 50, 50]) * 0.5

        defect_ratio = mask_binary.sum() / mask_binary.size * 100

        axes[row, 0].imshow(img, cmap='gray')
        axes[row, 0].set_ylabel(defect, fontsize=12, fontweight='bold', rotation=0, labelpad=60)
        axes[row, 0].axis('off')

        axes[row, 1].imshow(mask_binary, cmap='gray')
        axes[row, 1].set_title(f'결함: {defect_ratio:.1f}%', fontsize=9)
        axes[row, 1].axis('off')

        axes[row, 2].imshow(overlay.astype(np.uint8))
        axes[row, 2].axis('off')

    for c, t in enumerate(col_titles):
        axes[0, c].set_title(t, fontsize=11, fontweight='bold')

    plt.suptitle('자석 타일 표면 결함 5종 — 샘플', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()

visualize_defect_samples(DATA_ROOT)
```

---

## 3. 데이터 전처리 및 DataLoader

### 3.1 핵심 설계

| 항목 | 설정값 | 이유 |
|------|--------|------|
| 입력 크기 | 224×224 | 이미지가 작으므로 224로 통일 |
| 채널 | 그레이스케일→3ch 복사 | 사전학습 인코더 호환 |
| 출력 채널 | 1 (이진 세그먼테이션) | 결함/배경 이진 분할 (5종 통합) |
| 배치 크기 | 16 | 데이터 적으므로 작게 설정 |
| 데이터 증강 | 강하게 적용 | **결함 이미지 392장** → 증강 필수 |
| Free 제외 | 결함 있는 이미지만 | 마스크가 있는 이미지로 학습 |

### 3.2 이미지-마스크 쌍 수집

```python
def collect_pairs(data_root, defect_types):
    """모든 결함 유형의 이미지-마스크 쌍 수집"""
    pairs = []
    labels = []

    for defect in defect_types:
        img_dir = data_root / defect / "Imgs"
        mask_dir = data_root / defect / "Masks"

        if not img_dir.exists() or not mask_dir.exists():
            continue

        img_files = sorted(list(img_dir.glob("*")))
        mask_files = sorted(list(mask_dir.glob("*")))

        for img_path, mask_path in zip(img_files, mask_files):
            pairs.append((img_path, mask_path))
            labels.append(defect)

    print(f"총 이미지-마스크 쌍: {len(pairs)}개")
    for d in defect_types:
        count = labels.count(d)
        print(f"  {d}: {count}쌍")

    return pairs, labels

all_pairs, all_labels = collect_pairs(DATA_ROOT, DEFECT_TYPES)
```

### 3.3 Dataset 클래스

```python
from torch.utils.data import Dataset, DataLoader
import albumentations as A
from albumentations.pytorch import ToTensorV2

class MagneticTileDataset(Dataset):
    """
    자석 타일 결함 세그먼테이션 데이터셋

    특징:
      - 그레이스케일 → 3ch 복사 (사전학습 호환)
      - 바이너리 마스크 직접 로드
      - 강한 데이터 증강 (392장 보완)
    """

    def __init__(self, pairs, img_size=224, transform=None):
        self.pairs = pairs
        self.img_size = img_size
        self.transform = transform

    def __len__(self):
        return len(self.pairs)

    def __getitem__(self, idx):
        img_path, mask_path = self.pairs[idx]

        img = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)  # (H, W, 3)

        mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
        mask = (mask > 128).astype(np.float32)  # 0 또는 1

        if self.transform:
            augmented = self.transform(image=img, mask=mask)
            img = augmented['image']
            mask = augmented['mask']
        else:
            img = cv2.resize(img, (self.img_size, self.img_size))
            mask = cv2.resize(mask, (self.img_size, self.img_size))
            img = torch.from_numpy(img).permute(2, 0, 1).float() / 255.0
            mask = torch.from_numpy(mask).float()

        if mask.dim() == 2:
            mask = mask.unsqueeze(0)

        return img, mask
```

### 3.4 데이터 증강 (강한 증강 — 소량 데이터 보완)

```python
IMG_SIZE = 224

# === 학습용 — 강한 증강 (392장 보완) ===
train_aug = A.Compose([
    A.Resize(IMG_SIZE, IMG_SIZE),
    A.HorizontalFlip(p=0.5),
    A.VerticalFlip(p=0.5),
    A.RandomRotate90(p=0.5),
    A.ShiftScaleRotate(shift_limit=0.1, scale_limit=0.15, rotate_limit=30, p=0.6),
    A.RandomBrightnessContrast(brightness_limit=0.3, contrast_limit=0.3, p=0.5),
    A.GaussNoise(var_limit=(10, 80), p=0.4),
    A.OneOf([
        A.ElasticTransform(alpha=120, sigma=120*0.05, p=0.3),
        A.GridDistortion(num_steps=5, distort_limit=0.3, p=0.3),
        A.OpticalDistortion(distort_limit=0.2, shift_limit=0.1, p=0.3),
    ], p=0.4),
    A.CoarseDropout(max_holes=8, max_height=20, max_width=20, p=0.3),
    A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ToTensorV2(),
])

# === 검증용 ===
val_aug = A.Compose([
    A.Resize(IMG_SIZE, IMG_SIZE),
    A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ToTensorV2(),
])
```

### 3.5 Train / Validation 분리

```python
from sklearn.model_selection import train_test_split

train_pairs, val_pairs = train_test_split(
    all_pairs, test_size=0.2, random_state=SEED,
    stratify=all_labels
)
print(f"Train: {len(train_pairs)}쌍 / Val: {len(val_pairs)}쌍")

train_dataset = MagneticTileDataset(train_pairs, IMG_SIZE, transform=train_aug)
val_dataset   = MagneticTileDataset(val_pairs,   IMG_SIZE, transform=val_aug)

BATCH_SIZE = 16
train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE,
                          shuffle=True,  num_workers=0, pin_memory=True)
val_loader   = DataLoader(val_dataset,   batch_size=BATCH_SIZE,
                          shuffle=False, num_workers=0, pin_memory=True)

images, masks = next(iter(train_loader))
print(f"이미지: {images.shape} | 마스크: {masks.shape}")
print(f"결함 픽셀 비율: {masks.mean()*100:.2f}%")
```

---

## 4. U-Net 모델 구현

### 4.1 Vanilla U-Net

```python
import torch.nn as nn
import torch.nn.functional as F

class DoubleConv(nn.Module):
    def __init__(self, in_ch, out_ch):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch), nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch), nn.ReLU(inplace=True),
        )
    def forward(self, x): return self.block(x)


class UNet(nn.Module):
    """U-Net 이진 세그먼테이션 (결함 vs 배경)"""
    def __init__(self, in_ch=3, out_ch=1, features=[64, 128, 256, 512]):
        super().__init__()
        self.encoders  = nn.ModuleList()
        self.decoders  = nn.ModuleList()
        self.upconvs   = nn.ModuleList()
        self.pool      = nn.MaxPool2d(2, 2)

        ch = in_ch
        for f in features:
            self.encoders.append(DoubleConv(ch, f)); ch = f

        self.bottleneck = DoubleConv(features[-1], features[-1] * 2)

        for f in reversed(features):
            self.upconvs.append(nn.ConvTranspose2d(f * 2, f, 2, stride=2))
            self.decoders.append(DoubleConv(f * 2, f))

        self.final = nn.Conv2d(features[0], out_ch, 1)

    def forward(self, x):
        skips = []
        for enc in self.encoders:
            x = enc(x); skips.append(x); x = self.pool(x)
        x = self.bottleneck(x)
        for idx in range(len(self.decoders)):
            x = self.upconvs[idx](x)
            skip = skips[-(idx + 1)]
            if x.shape != skip.shape:
                x = F.interpolate(x, size=skip.shape[2:], mode='bilinear', align_corners=True)
            x = torch.cat([skip, x], dim=1)
            x = self.decoders[idx](x)
        return self.final(x)

model = UNet(in_ch=3, out_ch=1).to(device)
print(f"Vanilla U-Net 파라미터: {sum(p.numel() for p in model.parameters()):,}개")
print(f"입력: (1,3,224,224) → 출력: {model(torch.randn(1,3,224,224).to(device)).shape}")
```

---

## 5. Attention U-Net 구현

> **핵심 아이디어**: Skip Connection에 Attention Gate를 추가하여 디코더가
> "어디를 봐야 할지"를 스스로 학습하게 한다.
> Crack(57장) · Fray(32장)처럼 작고 불규칙한 결함에 특히 효과적.

### 5.1 Attention Gate 원리

```
기존 U-Net Skip:
  디코더 피처 ──────────────────── cat ──▶ DoubleConv
  인코더 피처 ─────────────────────┘

Attention U-Net:
  디코더 피처(gating signal) ─▶ W_g ─▶
                                        ⊕ ─▶ ReLU ─▶ W_ψ ─▶ σ ─▶ α(attention map)
  인코더 피처 ──────────────▶ W_x ─▶         (0~1 soft mask)
                                                    ↓
  인코더 피처 ──────────────────── × α ──▶ cat ──▶ DoubleConv

→ α 가 낮은 영역(배경) 의 피처를 자동으로 억제
```

### 5.2 AttentionGate 구현

```python
class AttentionGate(nn.Module):
    """
    Attention Gate (Oktay et al., "Attention U-Net", MIDL 2018)

    Args:
        F_g  : 디코더(gating signal) 채널 수
        F_l  : 인코더(skip)          채널 수
        F_int: 중간 채널 수 (보통 F_l // 2)
    """
    def __init__(self, F_g, F_l, F_int):
        super().__init__()
        # gating signal 변환
        self.W_g = nn.Sequential(
            nn.Conv2d(F_g, F_int, kernel_size=1, bias=False),
            nn.BatchNorm2d(F_int)
        )
        # skip connection 변환
        self.W_x = nn.Sequential(
            nn.Conv2d(F_l, F_int, kernel_size=1, bias=False),
            nn.BatchNorm2d(F_int)
        )
        # attention coefficient 생성
        self.psi = nn.Sequential(
            nn.Conv2d(F_int, 1, kernel_size=1, bias=False),
            nn.BatchNorm2d(1),
            nn.Sigmoid()
        )
        self.relu = nn.ReLU(inplace=True)

    def forward(self, g, x):
        """
        g : 디코더에서 올라온 gating signal  (N, F_g, H/2, W/2)
        x : 인코더 skip connection 피처      (N, F_l, H,   W  )
        returns: x * attention_map            (N, F_l, H,   W  )
        """
        # g를 x와 같은 해상도로 upsample
        g_up = F.interpolate(self.W_g(g), size=x.shape[2:],
                             mode='bilinear', align_corners=True)
        x_t  = self.W_x(x)
        alpha = self.psi(self.relu(g_up + x_t))   # (N, 1, H, W)
        return x * alpha                            # broadcast multiplication
```

### 5.3 Attention U-Net 전체 아키텍처

```python
class AttentionUNet(nn.Module):
    """
    Attention U-Net — Skip Connection마다 AttentionGate 삽입
    출력 구조는 Vanilla U-Net과 동일 (in_ch=3, out_ch=1)
    """
    def __init__(self, in_ch=3, out_ch=1, features=[64, 128, 256, 512]):
        super().__init__()
        self.pool     = nn.MaxPool2d(2, 2)
        self.encoders = nn.ModuleList()
        self.upconvs  = nn.ModuleList()
        self.att_gates= nn.ModuleList()
        self.decoders = nn.ModuleList()

        # ── 인코더 ──────────────────────────────────────
        ch = in_ch
        for f in features:
            self.encoders.append(DoubleConv(ch, f))
            ch = f

        # ── 보틀넥 ──────────────────────────────────────
        self.bottleneck = DoubleConv(features[-1], features[-1] * 2)

        # ── 디코더 + AttentionGate ──────────────────────
        for f in reversed(features):
            # Transposed Conv: (f*2) → f
            self.upconvs.append(nn.ConvTranspose2d(f * 2, f, kernel_size=2, stride=2))
            # AttentionGate: F_g=f (디코더), F_l=f (인코더), F_int=f//2
            self.att_gates.append(AttentionGate(F_g=f, F_l=f, F_int=f // 2))
            # Decoder DoubleConv: cat 후 채널 f*2 → f
            self.decoders.append(DoubleConv(f * 2, f))

        self.final = nn.Conv2d(features[0], out_ch, kernel_size=1)

    def forward(self, x):
        # 인코더
        skips = []
        for enc in self.encoders:
            x = enc(x)
            skips.append(x)
            x = self.pool(x)

        # 보틀넥
        x = self.bottleneck(x)

        # 디코더 (with Attention)
        for i in range(len(self.decoders)):
            g    = self.upconvs[i](x)                    # upsample (gating signal)
            skip = skips[-(i + 1)]                        # 해당 레벨 skip
            skip = self.att_gates[i](g=g, x=skip)         # attention 적용
            if g.shape != skip.shape:
                g = F.interpolate(g, size=skip.shape[2:],
                                  mode='bilinear', align_corners=True)
            x = torch.cat([skip, g], dim=1)
            x = self.decoders[i](x)

        return self.final(x)


# 모델 확인
att_model = AttentionUNet(in_ch=3, out_ch=1).to(device)
print(f"Attention U-Net 파라미터: {sum(p.numel() for p in att_model.parameters()):,}개")
dummy = torch.randn(1, 3, 224, 224).to(device)
print(f"입력: (1,3,224,224) → 출력: {att_model(dummy).shape}")
```

---

## 6. 손실 함수 — Dice Loss + BCE + Focal Tversky

### 6.1 Dice Loss (기본)

```python
class DiceLoss(nn.Module):
    """픽셀 겹침 기반 손실 — 배경/결함 불균형에 강함"""
    def __init__(self, smooth=1.0):
        super().__init__()
        self.smooth = smooth

    def forward(self, pred, target):
        pred = torch.sigmoid(pred)
        p    = pred.contiguous().view(-1)
        t    = target.contiguous().view(-1)
        inter = (p * t).sum()
        return 1 - (2 * inter + self.smooth) / (p.sum() + t.sum() + self.smooth)
```

### 6.2 Combined Loss (BCE + Dice)

```python
class CombinedLoss(nn.Module):
    """
    BCE : 픽셀 단위 정밀도 (클래스 불균형에 취약)
    Dice: 영역 겹침 비율 (불균형에 강함)
    → 두 손실의 상호 보완
    """
    def __init__(self, bce_w=0.5, dice_w=0.5):
        super().__init__()
        self.bce    = nn.BCEWithLogitsLoss()
        self.dice   = DiceLoss()
        self.bce_w  = bce_w
        self.dice_w = dice_w

    def forward(self, pred, target):
        return self.bce_w * self.bce(pred, target) + self.dice_w * self.dice(pred, target)
```

### 6.3 Focal Tversky Loss ✨ (추가)

> **Tversky Loss**: Dice의 일반화 — FP/FN에 비대칭 가중치를 부여.
> **Focal Tversky**: 어려운 샘플(결함 픽셀 적은 이미지)에 집중.
> Crack(57장) · Fray(32장)처럼 결함 영역이 극히 작을 때 FN을 줄이는 데 탁월.

```
Tversky Index:
    TI = (TP + smooth) / (TP + α·FP + β·FN + smooth)

    α = 0.3 : FP 패널티 낮게  (배경을 결함으로 잘못 예측)
    β = 0.7 : FN 패널티 높게  (결함을 놓치는 것을 크게 패널티)
    → α + β = 1 로 유지

Focal Tversky Loss:
    FTL = (1 - TI)^γ
    γ = 0.75 : 어려운 배치(결함 픽셀 적음)에 더 집중
```

```python
class FocalTverskyLoss(nn.Module):
    """
    Focal Tversky Loss
    (Abraham & Khan, "A Novel Focal Tversky Loss Function", ISBI 2019)

    Args:
        alpha (float): FP 패널티 가중치 (기본 0.3)
        beta  (float): FN 패널티 가중치 (기본 0.7) — alpha + beta = 1
        gamma (float): Focal 지수 (기본 0.75) — 어려운 샘플 집중
        smooth(float): 분모 0 방지 (기본 1.0)
    """
    def __init__(self, alpha=0.3, beta=0.7, gamma=0.75, smooth=1.0):
        super().__init__()
        self.alpha  = alpha
        self.beta   = beta
        self.gamma  = gamma
        self.smooth = smooth

    def forward(self, pred, target):
        pred   = torch.sigmoid(pred)
        p      = pred.contiguous().view(-1)
        t      = target.contiguous().view(-1)

        TP = (p * t).sum()
        FP = ((1 - t) * p).sum()
        FN = (t * (1 - p)).sum()

        tversky = (TP + self.smooth) / (TP + self.alpha * FP + self.beta * FN + self.smooth)
        return (1 - tversky) ** self.gamma


class CombinedFocalTverskyLoss(nn.Module):
    """
    BCE + Focal Tversky 결합 손실

    Vanilla 모델    : CombinedLoss (BCE + Dice)
    Attention 모델  : CombinedFocalTverskyLoss (BCE + FocalTversky)
    → Focal Tversky는 소수 결함(Crack, Fray)에 집중하는 효과
    """
    def __init__(self, bce_w=0.4, ftl_w=0.6,
                 alpha=0.3, beta=0.7, gamma=0.75):
        super().__init__()
        self.bce   = nn.BCEWithLogitsLoss()
        self.ftl   = FocalTverskyLoss(alpha=alpha, beta=beta, gamma=gamma)
        self.bce_w = bce_w
        self.ftl_w = ftl_w

    def forward(self, pred, target):
        return self.bce_w * self.bce(pred, target) + self.ftl_w * self.ftl(pred, target)


# 손실 함수 인스턴스 생성
criterion_vanilla = CombinedLoss()               # Vanilla U-Net 용
criterion_attn    = CombinedFocalTverskyLoss()   # Attention U-Net 용
criterion_resnet  = CombinedFocalTverskyLoss()   # ResNet34 U-Net 용 (동일 적용)
```

### 6.4 손실 함수 비교 요약

| 손실 함수 | FP 처리 | FN 처리 | 소수 결함 대응 | 적용 모델 |
|-----------|:-------:|:-------:|:--------------:|:---------:|
| BCE | 동등 | 동등 | ✗ | — |
| Dice | 비율 기반 | 비율 기반 | △ | — |
| **BCE + Dice** | 보통 | 보통 | △ | Vanilla U-Net |
| Tversky (α=0.3) | 낮은 패널티 | 높은 패널티 | ○ | — |
| **BCE + Focal Tversky** | 낮은 패널티 | 높은 패널티 + Focal | **◎** | Attention / ResNet34 |

---

## 7. 학습 루프 구현

### 7.1 지표 함수

```python
def compute_dice(pred, target, threshold=0.5):
    pred  = (torch.sigmoid(pred) > threshold).float()
    smooth = 1.0
    inter = (pred.view(-1) * target.view(-1)).sum()
    return ((2 * inter + smooth) /
            (pred.view(-1).sum() + target.view(-1).sum() + smooth)).item()

def compute_iou(pred, target, threshold=0.5):
    pred  = (torch.sigmoid(pred) > threshold).float()
    smooth = 1.0
    inter = (pred.view(-1) * target.view(-1)).sum()
    union = pred.view(-1).sum() + target.view(-1).sum() - inter
    return ((inter + smooth) / (union + smooth)).item()
```

### 7.2 학습/검증 함수

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
        optimizer.zero_grad(); loss.backward(); optimizer.step()
        total_loss += loss.item() * images.size(0)
        total_dice += compute_dice(outputs, masks) * images.size(0)
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
            total_dice += compute_dice(outputs, masks) * images.size(0)
            total_iou  += compute_iou(outputs, masks)  * images.size(0)
            count += images.size(0)
    return total_loss / count, total_dice / count, total_iou / count
```

### 7.3 전체 학습 함수

```python
def train_segmentation(model, train_loader, val_loader, criterion,
                        num_epochs=40, lr=1e-4, model_name="unet"):
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='max', factor=0.5, patience=5
    )

    history = {'train_loss': [], 'train_dice': [],
               'val_loss':   [], 'val_dice':   [], 'val_iou': []}
    best_dice = 0.0
    start = time.time()

    for epoch in range(num_epochs):
        print(f"\nEpoch [{epoch+1}/{num_epochs}]")
        tl, td = train_one_epoch(model, train_loader, criterion, optimizer, device)
        vl, vd, vi = evaluate(model, val_loader, criterion, device)
        scheduler.step(vd)

        history['train_loss'].append(tl); history['train_dice'].append(td)
        history['val_loss'].append(vl);   history['val_dice'].append(vd)
        history['val_iou'].append(vi)

        print(f"  Train — Loss: {tl:.4f} | Dice: {td:.4f}")
        print(f"  Val   — Loss: {vl:.4f} | Dice: {vd:.4f} | IoU: {vi:.4f}")

        if vd > best_dice:
            best_dice = vd
            torch.save(model.state_dict(), f"models/best_{model_name}.pth")
            print(f"  ★ Best 저장! (Dice: {vd:.4f})")

    elapsed = (time.time() - start) / 60
    print(f"\n완료! {elapsed:.1f}분 | Best Dice: {best_dice:.4f}")
    model.load_state_dict(torch.load(f"models/best_{model_name}.pth",
                                      map_location=device))
    return model, history


# ── Vanilla U-Net 학습 (40 에폭, BCE + Dice) ─────────────────
print("=" * 55)
print("  [1/3] Vanilla U-Net 학습")
print("=" * 55)
model, history_vanilla = train_segmentation(
    model, train_loader, val_loader, criterion_vanilla,
    num_epochs=40, lr=1e-4, model_name="unet_vanilla"
)

# ── Attention U-Net 학습 (40 에폭, BCE + Focal Tversky) ──────
print("\n" + "=" * 55)
print("  [2/3] Attention U-Net 학습")
print("=" * 55)
att_model, history_attn = train_segmentation(
    att_model, train_loader, val_loader, criterion_attn,
    num_epochs=40, lr=1e-4, model_name="unet_attention"
)
```

---

## 8. 평가 및 시각화 + TTA

### 8.1 학습 곡선

```python
def plot_curves(history, title="U-Net", save_path="results/03_training_curves.png"):
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.5))
    ep = range(1, len(history['train_loss']) + 1)

    axes[0].plot(ep, history['train_loss'], 'b--', alpha=0.7, label='Train')
    axes[0].plot(ep, history['val_loss'],   'r-',  label='Val')
    axes[0].set_title('Loss', fontweight='bold')
    axes[0].legend(); axes[0].grid(True, alpha=0.3)

    axes[1].plot(ep, history['train_dice'], 'b--', alpha=0.7, label='Train')
    axes[1].plot(ep, history['val_dice'],   'r-',  label='Val')
    axes[1].set_title('Dice Coefficient', fontweight='bold')
    axes[1].legend(); axes[1].grid(True, alpha=0.3)

    axes[2].plot(ep, history['val_iou'], 'g-', label='Val IoU')
    axes[2].set_title('IoU (Val)', fontweight='bold')
    axes[2].legend(); axes[2].grid(True, alpha=0.3)

    plt.suptitle(f'{title} — 학습 곡선', fontsize=13, fontweight='bold')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()

plot_curves(history_vanilla, "Vanilla U-Net",  "results/03_vanilla_curves.png")
plot_curves(history_attn,    "Attention U-Net", "results/04_attention_curves.png")
```

### 8.2 Test-Time Augmentation (TTA) ✨ (추가)

> **TTA 원리**: 추론 시 원본 + 여러 증강 버전을 모델에 통과시켜
> 예측 결과를 평균 내면 단일 예측 대비 Dice 1~3% 향상.
> 추가 학습 없이 코드 추가만으로 성능 향상이 가능한 실용적 기법.

```
TTA 적용 흐름:
  원본 이미지
     ├─▶ 원본           ─▶ 모델 ─▶ pred₀
     ├─▶ 수평 플립       ─▶ 모델 ─▶ pred₁ ─▶ 역플립
     ├─▶ 수직 플립       ─▶ 모델 ─▶ pred₂ ─▶ 역플립
     └─▶ 수평+수직 플립  ─▶ 모델 ─▶ pred₃ ─▶ 역플립
                                    ↓
                             평균 (pred₀+pred₁+pred₂+pred₃) / 4
                                    ↓
                             최종 예측 마스크 (threshold=0.5)
```

```python
def predict_tta(model, image_tensor, device, threshold=0.5):
    """
    Test-Time Augmentation 예측

    Args:
        model        : 학습된 세그먼테이션 모델
        image_tensor : (1, 3, H, W) 정규화된 텐서
        device       : 연산 장치
        threshold    : 이진화 임계값 (기본 0.5)

    Returns:
        pred_mask  : (1, 1, H, W) 이진 마스크 텐서
        pred_proba : (1, 1, H, W) 확률 텐서 (앙상블 평균)
    """
    model.eval()
    image_tensor = image_tensor.to(device)

    preds = []
    with torch.no_grad():
        # ① 원본
        preds.append(torch.sigmoid(model(image_tensor)))

        # ② 수평 플립 (좌우) → 예측 후 역변환
        img_hflip = torch.flip(image_tensor, dims=[3])
        pred_hflip = torch.sigmoid(model(img_hflip))
        preds.append(torch.flip(pred_hflip, dims=[3]))

        # ③ 수직 플립 (상하) → 예측 후 역변환
        img_vflip = torch.flip(image_tensor, dims=[2])
        pred_vflip = torch.sigmoid(model(img_vflip))
        preds.append(torch.flip(pred_vflip, dims=[2]))

        # ④ 수평 + 수직 플립 → 예측 후 역변환
        img_hvflip = torch.flip(image_tensor, dims=[2, 3])
        pred_hvflip = torch.sigmoid(model(img_hvflip))
        preds.append(torch.flip(pred_hvflip, dims=[2, 3]))

    # 4가지 예측 평균
    pred_proba = torch.stack(preds, dim=0).mean(dim=0)   # (1, 1, H, W)
    pred_mask  = (pred_proba > threshold).float()

    return pred_mask, pred_proba


def evaluate_with_tta(model, loader, device, threshold=0.5):
    """DataLoader 전체에 TTA 적용 후 Dice/IoU 산출"""
    model.eval()
    total_dice, total_iou, count = 0, 0, 0

    for images, masks in tqdm(loader, desc="  TTA 평가"):
        masks = masks.to(device)
        for i in range(images.size(0)):
            img_single = images[i].unsqueeze(0)          # (1, 3, H, W)
            msk_single = masks[i].unsqueeze(0)            # (1, 1, H, W)
            pred_mask, pred_proba = predict_tta(model, img_single, device, threshold)
            # Dice/IoU 계산 (logit 대신 proba 사용 → 이미 sigmoid 적용됨)
            p = pred_proba.view(-1); t = msk_single.view(-1)
            smooth = 1.0
            inter = (p * t).sum()
            total_dice += ((2 * inter + smooth) / (p.sum() + t.sum() + smooth)).item()
            union = p.sum() + t.sum() - inter
            total_iou  += ((inter + smooth) / (union + smooth)).item()
            count += 1

    return total_dice / count, total_iou / count


# TTA 평가 실행
print("\n[TTA 평가 — Vanilla U-Net]")
dice_tta_v, iou_tta_v = evaluate_with_tta(model,     val_loader, device)

print("\n[TTA 평가 — Attention U-Net]")
dice_tta_a, iou_tta_a = evaluate_with_tta(att_model, val_loader, device)

print(f"\n{'='*50}")
print(f"  TTA 적용 전후 비교 (Val 기준)")
print(f"{'='*50}")
print(f"  Vanilla   — TTA 미적용: Dice={max(history_vanilla['val_dice']):.4f} "
      f"| TTA 적용: Dice={dice_tta_v:.4f} (+{dice_tta_v - max(history_vanilla['val_dice']):.4f})")
print(f"  Attention — TTA 미적용: Dice={max(history_attn['val_dice']):.4f} "
      f"| TTA 적용: Dice={dice_tta_a:.4f} (+{dice_tta_a - max(history_attn['val_dice']):.4f})")
```

### 8.3 예측 결과 시각화 (TTA 포함)

```python
def visualize_predictions(model, dataset, device, num_samples=8,
                           use_tta=True, save_path="results/05_predictions.png"):
    model.eval()
    fig, axes = plt.subplots(num_samples, 5, figsize=(20, 3.5 * num_samples))
    col_titles = ['원본', '정답 (GT)', 'Pred (기본)', 'Pred (TTA)', '비교 오버레이']
    indices = np.random.choice(len(dataset), num_samples, replace=False)

    for row, idx in enumerate(indices):
        image, gt_mask = dataset[idx]
        img_input = image.unsqueeze(0).to(device)

        # 기본 예측
        with torch.no_grad():
            pred_logits = model(img_input)
            pred_basic  = (torch.sigmoid(pred_logits) > 0.5).float().cpu().squeeze()

        # TTA 예측
        pred_mask_tta, _ = predict_tta(model, img_input, device)
        pred_tta = pred_mask_tta.cpu().squeeze()

        # 이미지 역정규화
        img_np = image.permute(1, 2, 0).numpy()
        img_np = img_np * np.array([0.229, 0.224, 0.225]) + np.array([0.485, 0.456, 0.406])
        img_np = np.clip(img_np, 0, 1)

        gt_np    = gt_mask.squeeze().numpy()
        pred_b   = pred_basic.numpy()
        pred_t   = pred_tta.numpy()

        # 오버레이 (TTA 기준): 노랑=TP, 초록=FN, 빨강=FP
        overlay = img_np.copy()
        overlay[(gt_np > 0.5) & (pred_t > 0.5)] = [1, 1, 0]   # TP (노랑)
        overlay[(gt_np > 0.5) & (pred_t < 0.5)] = [0, 1, 0]   # FN (초록)
        overlay[(gt_np < 0.5) & (pred_t > 0.5)] = [1, 0, 0]   # FP (빨강)

        dice_basic = compute_dice(pred_logits.cpu(), gt_mask.unsqueeze(0))
        dice_tta_s, _ = predict_tta(model, img_input, device)
        d_tta = dice_tta_s.view(-1); g = gt_mask.view(-1)
        inter = (d_tta * g.to(device)).sum(); sm = 1.0
        dice_tta_val = ((2*inter + sm) / (d_tta.sum() + g.sum().to(device) + sm)).item()

        axes[row, 0].imshow(img_np);                   axes[row, 0].axis('off')
        axes[row, 1].imshow(gt_np, cmap='gray');       axes[row, 1].axis('off')
        axes[row, 2].imshow(pred_b, cmap='gray')
        axes[row, 2].set_title(f'Dice: {dice_basic:.3f}', fontsize=9)
        axes[row, 2].axis('off')
        axes[row, 3].imshow(pred_t, cmap='gray')
        axes[row, 3].set_title(f'TTA Dice: {dice_tta_val:.3f}', fontsize=9)
        axes[row, 3].axis('off')
        axes[row, 4].imshow(overlay)
        axes[row, 4].set_title('노랑=TP|초록=FN|빨강=FP', fontsize=7)
        axes[row, 4].axis('off')

    for c, t in enumerate(col_titles):
        axes[0, c].set_title(t, fontsize=10, fontweight='bold')

    plt.suptitle('예측 결과 (기본 vs TTA)', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()

visualize_predictions(att_model, val_dataset, device,
                      use_tta=True, save_path="results/05_attention_predictions.png")
```

### 8.4 결함 유형별 성능 분석

```python
def evaluate_per_defect(model, data_root, defect_types, device,
                         img_size=224, use_tta=True,
                         save_path="results/06_per_defect_metrics.png"):
    """결함 유형별 Dice/IoU 개별 평가 (TTA 옵션)"""
    model.eval()
    results = {}
    MEAN = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
    STD  = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)

    for defect in defect_types:
        img_dir  = data_root / defect / "Imgs"
        mask_dir = data_root / defect / "Masks"
        img_files  = sorted(list(img_dir.glob("*")))
        mask_files = sorted(list(mask_dir.glob("*")))

        dices, ious = [], []
        for img_path, mask_path in zip(img_files, mask_files):
            img = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
            img = cv2.resize(img, (img_size, img_size))
            img_t = (torch.from_numpy(img).permute(2, 0, 1).float() / 255.0 - MEAN) / STD

            mask   = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
            mask   = cv2.resize(mask, (img_size, img_size))
            mask_t = torch.from_numpy((mask > 128).astype(np.float32)).unsqueeze(0)

            if use_tta:
                pred_mask, pred_proba = predict_tta(model, img_t.unsqueeze(0), device)
                p = pred_proba.cpu().view(-1); t = mask_t.view(-1)
            else:
                with torch.no_grad():
                    pred = model(img_t.unsqueeze(0).to(device))
                p = torch.sigmoid(pred).cpu().view(-1); t = mask_t.view(-1)

            smooth = 1.0
            inter  = (p * t).sum()
            dices.append(((2 * inter + smooth) / (p.sum() + t.sum() + smooth)).item())
            union  = p.sum() + t.sum() - inter
            ious.append(((inter + smooth) / (union + smooth)).item())

        results[defect] = {'dice': np.mean(dices), 'iou': np.mean(ious), 'count': len(dices)}

    print(f"\n{'='*55}")
    print(f"{'결함 유형별 성능 (TTA=' + str(use_tta) + ')':^55}")
    print(f"{'='*55}")
    print(f"{'유형':<12} {'샘플수':>8} {'Dice':>10} {'IoU':>10}")
    print(f"{'-'*55}")
    for d, r in results.items():
        print(f"{d:<12} {r['count']:>8} {r['dice']:>10.4f} {r['iou']:>10.4f}")

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    colors = ['#e74c3c', '#f39c12', '#3498db', '#9b59b6', '#1abc9c']
    for ax, metric in [(axes[0], 'dice'), (axes[1], 'iou')]:
        vals = [results[d][metric] for d in defect_types]
        ax.bar(defect_types, vals, color=colors)
        ax.set_title(f'결함 유형별 {metric.upper()} (TTA={use_tta})',
                     fontweight='bold')
        ax.set_ylim(0, 1)
        for i, v in enumerate(vals):
            ax.text(i, v + 0.02, f'{v:.3f}', ha='center', fontweight='bold')

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()
    return results

defect_results = evaluate_per_defect(att_model, DATA_ROOT, DEFECT_TYPES, device,
                                      use_tta=True,
                                      save_path="results/06_per_defect_metrics.png")
```

---

## 9. 추가 실험 — ResNet34 백본 + 3모델 비교

### 9.1 ResNet34 U-Net

```python
import torchvision.models as models

class ResNetUNet(nn.Module):
    """ResNet34 백본 U-Net (전이학습 + Focal Tversky Loss)"""
    def __init__(self, out_ch=1):
        super().__init__()
        resnet = models.resnet34(weights=models.ResNet34_Weights.IMAGENET1K_V1)
        self.enc1 = nn.Sequential(resnet.conv1, resnet.bn1, resnet.relu)
        self.pool1 = resnet.maxpool
        self.enc2  = resnet.layer1
        self.enc3  = resnet.layer2
        self.enc4  = resnet.layer3
        self.enc5  = resnet.layer4

        self.up4  = nn.ConvTranspose2d(512, 256, 2, stride=2)
        self.dec4 = DoubleConv(512, 256)
        self.up3  = nn.ConvTranspose2d(256, 128, 2, stride=2)
        self.dec3 = DoubleConv(256, 128)
        self.up2  = nn.ConvTranspose2d(128, 64, 2, stride=2)
        self.dec2 = DoubleConv(128, 64)
        self.up1  = nn.ConvTranspose2d(64, 64, 2, stride=2)
        self.dec1 = DoubleConv(128, 64)
        self.up0  = nn.ConvTranspose2d(64, 32, 2, stride=2)
        self.dec0 = DoubleConv(32, 32)
        self.final = nn.Conv2d(32, out_ch, 1)

    def forward(self, x):
        e1 = self.enc1(x)
        e2 = self.enc2(self.pool1(e1))
        e3 = self.enc3(e2)
        e4 = self.enc4(e3)
        e5 = self.enc5(e4)

        d4 = self.dec4(torch.cat([self.up4(e5), e4], 1))
        d3 = self.dec3(torch.cat([self.up3(d4), e3], 1))
        d2 = self.dec2(torch.cat([self.up2(d3), e2], 1))
        d1 = self.dec1(torch.cat([self.up1(d2), e1], 1))
        d0 = self.dec0(self.up0(d1))
        return self.final(d0)


# ResNet34 U-Net 학습 (30 에폭, BCE + Focal Tversky)
print("=" * 55)
print("  [3/3] ResNet34 U-Net 학습")
print("=" * 55)
resnet_unet = ResNetUNet(out_ch=1).to(device)
resnet_model, history_resnet = train_segmentation(
    resnet_unet, train_loader, val_loader, criterion_resnet,
    num_epochs=30, lr=1e-4, model_name="unet_resnet34"
)
```

### 9.2 3모델 최종 비교 (TTA 포함)

```python
# TTA 평가 — ResNet34
print("\n[TTA 평가 — ResNet34 U-Net]")
dice_tta_r, iou_tta_r = evaluate_with_tta(resnet_model, val_loader, device)

# ── 결과 통합 출력 ─────────────────────────────────────────────
print(f"\n{'='*70}")
print(f"{'3모델 최종 비교 (Validation Set)':^70}")
print(f"{'='*70}")
print(f"{'모델':<20} {'손실함수':<22} {'Dice':>8} {'TTA Dice':>10} {'IoU':>8} {'TTA IoU':>9}")
print(f"{'-'*70}")

rows = [
    ("Vanilla U-Net",   "BCE+Dice",          max(history_vanilla['val_dice']), dice_tta_v,
     max(history_vanilla['val_iou']),   iou_tta_v),
    ("Attention U-Net", "BCE+FocalTversky",   max(history_attn['val_dice']),    dice_tta_a,
     max(history_attn['val_iou']),      iou_tta_a),
    ("ResNet34 U-Net",  "BCE+FocalTversky",   max(history_resnet['val_dice']),  dice_tta_r,
     max(history_resnet['val_iou']),    iou_tta_r),
]
for name, loss, d, dt, i, it in rows:
    print(f"{name:<20} {loss:<22} {d:>8.4f} {dt:>10.4f} {i:>8.4f} {it:>9.4f}")
print(f"{'='*70}")


# ── 시각화: 3모델 Dice 비교 막대 그래프 ──────────────────────
def plot_model_comparison(rows, save_path="results/07_model_comparison.png"):
    names  = [r[0] for r in rows]
    dice_n = [r[2] for r in rows]
    dice_t = [r[3] for r in rows]
    iou_n  = [r[4] for r in rows]
    iou_t  = [r[5] for r in rows]

    x = np.arange(len(names)); width = 0.2
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    for ax, metric, vals_n, vals_t, ylabel in [
        (axes[0], 'Dice', dice_n, dice_t, 'Dice Coefficient'),
        (axes[1], 'IoU',  iou_n,  iou_t,  'IoU'),
    ]:
        b1 = ax.bar(x - width/2, vals_n, width, label='기본',    color='#3498db', alpha=0.85)
        b2 = ax.bar(x + width/2, vals_t, width, label='TTA 적용', color='#e74c3c', alpha=0.85)
        ax.set_xticks(x); ax.set_xticklabels(names, fontsize=9)
        ax.set_ylabel(ylabel, fontweight='bold')
        ax.set_title(f'모델별 {metric} 비교', fontweight='bold')
        ax.set_ylim(0, 1.05)
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        for b, v in [(b1, vals_n), (b2, vals_t)]:
            for bar, val in zip(b, v):
                ax.text(bar.get_x() + bar.get_width()/2,
                        bar.get_height() + 0.01,
                        f'{val:.3f}', ha='center', fontsize=8, fontweight='bold')

    plt.suptitle('3모델 + TTA 성능 비교', fontsize=13, fontweight='bold')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()

plot_model_comparison(rows)
```

---

## 10. 결과 저장 및 정리

### 10.1 결과 JSON

```python
import json

summary = {
    "project": "자석 타일 표면 결함 세그먼테이션",
    "dataset": "Magnetic Tile Surface Defects (1,344장, 5종 결함)",
    "dataset_url": "https://www.kaggle.com/datasets/alex000kim/magnetic-tile-surface-defects",
    "task": "이진 세그먼테이션 (결함 vs 배경)",
    "models": {
        "vanilla_unet": {
            "loss":         "BCE(0.5) + Dice(0.5)",
            "best_dice":    round(max(history_vanilla['val_dice']), 4),
            "best_iou":     round(max(history_vanilla['val_iou']),  4),
            "tta_dice":     round(dice_tta_v, 4),
            "tta_iou":      round(iou_tta_v,  4),
        },
        "attention_unet": {
            "loss":         "BCE(0.4) + FocalTversky(0.6, α=0.3, β=0.7, γ=0.75)",
            "best_dice":    round(max(history_attn['val_dice']), 4),
            "best_iou":     round(max(history_attn['val_iou']),  4),
            "tta_dice":     round(dice_tta_a, 4),
            "tta_iou":      round(iou_tta_a,  4),
        },
        "resnet34_unet": {
            "loss":         "BCE(0.4) + FocalTversky(0.6, α=0.3, β=0.7, γ=0.75)",
            "best_dice":    round(max(history_resnet['val_dice']), 4),
            "best_iou":     round(max(history_resnet['val_iou']),  4),
            "tta_dice":     round(dice_tta_r, 4),
            "tta_iou":      round(iou_tta_r,  4),
        },
    },
    "per_defect_tta": {
        d: {"dice": round(r['dice'], 4), "iou": round(r['iou'], 4)}
        for d, r in defect_results.items()
    },
    "key_techniques": [
        "Attention Gate (skip connection 어텐션)",
        "Focal Tversky Loss (FN 패널티 강화)",
        "Test-Time Augmentation (4방향 플립 앙상블)",
        "Albumentations 강한 증강 (392장 보완)",
    ]
}

with open("results/08_final_summary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)
print("최종 결과 저장 완료!")
```

### 10.2 출력 파일 목록

```
results/
├── 01_data_distribution.png       ← 결함 유형별 분포
├── 02_sample_images.png           ← 5종 결함 샘플 (원본/마스크/오버레이)
├── 03_vanilla_curves.png          ← Vanilla U-Net 학습 곡선
├── 04_attention_curves.png        ← Attention U-Net 학습 곡선
├── 05_attention_predictions.png   ← GT vs Pred(기본) vs Pred(TTA) 비교
├── 06_per_defect_metrics.png      ← 결함 유형별 Dice/IoU (TTA 적용)
├── 07_model_comparison.png        ← 3모델 + TTA 성능 비교
└── 08_final_summary.json          ← 성능 지표 JSON

models/
├── best_unet_vanilla.pth
├── best_unet_attention.pth
└── best_unet_resnet34.pth
```

---

## 부록: Claude Code 실행 순서

```
[Step 1]  환경 설정          → 디렉토리, 패키지, GPU/시드
[Step 2]  데이터 탐색        → 5종 결함 분포, 이미지 크기, 샘플 시각화
[Step 3]  Dataset/Loader     → 이미지-마스크 쌍 수집, 강한 증강, 층화 분리
[Step 4]  Vanilla U-Net      → DoubleConv → Encoder → Bottleneck → Decoder
[Step 5]  Attention U-Net    → AttentionGate → Skip Attention
[Step 6]  손실 함수          → DiceLoss + BCEWithLogitsLoss + FocalTverskyLoss
[Step 7a] 학습 (Vanilla, 40) → BCE+Dice, Adam, ReduceLROnPlateau
[Step 7b] 학습 (Attention,40)→ BCE+FocalTversky, Adam, ReduceLROnPlateau
[Step 8]  TTA + 시각화       → 4방향 플립 앙상블, GT vs Pred 비교
[Step 9]  ResNet34 비교 (30) → 전이학습 + FocalTversky → 3모델 비교
[Step 10] 결과 저장          → 8개 PNG + JSON
```

### 예상 소요 시간

| 단계 | GPU (Colab T4) | CPU Only |
|------|:-:|:-:|
| 데이터 준비 + EDA | 3분 | 3분 |
| Vanilla U-Net (40 에폭) | 10~15분 | 1~2시간 |
| Attention U-Net (40 에폭) | 12~18분 | 1~2시간 |
| ResNet34 U-Net (30 에폭) | 10~15분 | 1~2시간 |
| TTA 평가 + 시각화 | 5~8분 | 15분 |
| **총 소요 시간 (3모델)** | **약 45~60분** | **약 4~6시간** |

### 목표 성능 기준

| 지표 | 최소 기준 | 우수 기준 |
|------|:-:|:-:|
| Overall Dice (기본) | ≥ 0.55 | ≥ 0.75 |
| Overall Dice (TTA)  | ≥ 0.57 | ≥ 0.77 |
| Overall IoU  (기본) | ≥ 0.45 | ≥ 0.65 |
| Blowhole Dice | ≥ 0.60 | ≥ 0.80 |
| Crack Dice    | ≥ 0.40 | ≥ 0.65 |
| Fray Dice     | ≥ 0.35 | ≥ 0.60 |

> **참고**: Crack(57장) · Fray(32장)은 데이터가 극히 적고 결함 영역도 작아
> Dice가 낮을 수 있습니다. Attention Gate + Focal Tversky Loss + TTA 조합이
> 이들 소수 클래스에 가장 큰 효과를 발휘합니다.

### 추가 기법별 기대 효과 요약

| 기법 | 핵심 원리 | 기대 효과 | 구현 난이도 |
|------|-----------|:---------:|:-----------:|
| **Attention Gate** | Skip Connection에 소프트 어텐션 마스크 적용 | Dice +3~8% (소규모 결함) | ★★☆ |
| **Focal Tversky Loss** | FN 패널티 강화 + 어려운 샘플 집중 | Crack/Fray Dice +5~10% | ★★☆ |
| **TTA (4-flip)** | 추론 시 4가지 증강 앙상블 | Dice +1~3% | ★☆☆ |

### 이 데이터셋이 스마트 팩토리에 직접 연결되는 이유

영구자석 모터는 전기차, 산업용 로봇, 가전제품의 핵심 부품이며, 자석 타일의 표면 품질은 모터 성능에 직접적으로 영향을 미칩니다. 저장성 성 최대 자석 타일 생산 기지에서는 전체 인력의 약 75%가 수작업 품질 검사에 투입되고 있어, AI 기반 자동 검사의 경제적 효과가 매우 큽니다.

- **Attention U-Net**: "어디에 결함이 있는지" 모델이 스스로 집중 → 검사 정확도 ↑
- **Focal Tversky Loss**: 작은 결함(Crack, Fray)을 놓치지 않음 → 불량품 유출 ↓
- **TTA**: 실시간 라인에서도 활용 가능한 간단한 성능 향상 → 추가 비용 없는 품질 개선

"""
=======================================================================
SubTopic B: 자석 타일 표면 결함 세그먼테이션
=======================================================================
Dataset : Magnetic Tile Surface Defects (1,344장, 5종 결함)
          https://www.kaggle.com/datasets/alex000kim/magnetic-tile-surface-defects

Models  : ① Vanilla U-Net       (BCE + Dice, 40 epochs)
          ② Attention U-Net     (BCE + Focal Tversky, 40 epochs)
          ③ ResNet34 U-Net      (BCE + Focal Tversky, 30 epochs)

Extras  : Attention Gate, Focal Tversky Loss, TTA (4-flip ensemble)

Output  : results/ 폴더에 9개 PNG + 1개 JSON
          models/  폴더에 3개 .pth
=======================================================================
"""

# ===================================================================
# Section 0: 환경 설정 & 전역 상수
# ===================================================================

import os
import sys
import json
import time
import random
import warnings
from pathlib import Path

import numpy as np
import cv2
import matplotlib
matplotlib.use('Agg')          # 서버/비대화형 환경 대응
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns

import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as tv_models
from torch.utils.data import Dataset, DataLoader

from sklearn.model_selection import train_test_split
import albumentations as A
from albumentations.pytorch import ToTensorV2
from tqdm import tqdm

warnings.filterwarnings('ignore')

# ── 경로 ─────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent
# 실제 데이터 경로: mini_10/data/Magnetic Tile Surface Defects/
DATA_ROOT   = BASE_DIR.parent / "data" / "Magnetic Tile Surface Defects"
MODELS_DIR  = BASE_DIR / "models"
RESULTS_DIR = BASE_DIR / "results"

# ── 결함 유형 ─────────────────────────────────────────────────────────
# DEFECT_TYPES  : 표시용 이름 (Blowhole, Break ...)
# FOLDER_MAP    : 실제 폴더명 매핑 (Blowhole → MT_Blowhole)
# FREE_FOLDER   : 정상 이미지 폴더 (all-zero 마스크 .png 포함)
#
# 폴더 구조:
#   MT_Blowhole/Imgs/  ← *.jpg (이미지) + *.png (마스크) 동일 폴더 내 존재
#   MT_Break/Imgs/
#   MT_Crack/Imgs/
#   MT_Fray/Imgs/
#   MT_Uneven/Imgs/
#   MT_Free/Imgs/      ← *.jpg (이미지) + *.png (all-zero 마스크)
DEFECT_TYPES  = ['Blowhole', 'Break', 'Crack', 'Fray', 'Uneven']
FOLDER_MAP    = {d: f'MT_{d}' for d in DEFECT_TYPES}   # 예: Blowhole → MT_Blowhole
FREE_FOLDER   = 'MT_Free'
DEFECT_COLORS = ['#e74c3c', '#f39c12', '#3498db', '#9b59b6', '#1abc9c']

# ── 하이퍼파라미터 ────────────────────────────────────────────────────
SEED         = 42
IMG_SIZE     = 224
BATCH_SIZE   = 16
NUM_WORKERS  = 0          # macOS 안전값 (spawn 방식)

EPOCHS_VANILLA = 40
EPOCHS_ATTN    = 40
EPOCHS_RESNET  = 30
LR             = 1e-4
WEIGHT_DECAY   = 1e-5

# ── 디바이스 ──────────────────────────────────────────────────────────
device = (torch.device('cuda')  if torch.cuda.is_available()  else
          torch.device('mps')   if torch.backends.mps.is_available() else
          torch.device('cpu'))


# ===================================================================
# Section 1-A: 유틸리티
# ===================================================================

def setup_seed(seed: int = SEED) -> None:
    """재현성을 위한 시드 고정"""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def setup_font() -> None:
    """한글 폰트 설정 (macOS / Linux 자동 감지)"""
    import platform
    if platform.system() == 'Darwin':
        plt.rcParams['font.family'] = 'AppleGothic'
    else:
        try:
            plt.rcParams['font.family'] = 'NanumGothic'
        except Exception:
            pass
    plt.rcParams['axes.unicode_minus'] = False


def setup_dirs() -> None:
    """results/, models/ 디렉토리 자동 생성"""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def save_fig(fname: str, dpi: int = 150) -> None:
    """results/ 폴더에 그래프 저장 후 닫기"""
    path = RESULTS_DIR / fname
    plt.savefig(path, dpi=dpi, bbox_inches='tight')
    plt.close()
    print(f"  → 저장: {path.name}")


# ===================================================================
# Section 1-B: 데이터 수집 & 증강 & Dataset
# ===================================================================

def collect_pairs(data_root: Path, defect_types: list,
                  folder_map: dict = None):
    """
    실제 데이터 구조에 맞는 이미지-마스크 쌍 수집

    폴더 구조:
        data_root / MT_{defect} / Imgs / *.jpg  ← 원본 이미지
        data_root / MT_{defect} / Imgs / *.png  ← 동일 이름의 마스크

    Parameters
    ----------
    data_root   : 데이터 루트 (Magnetic Tile Surface Defects/)
    defect_types: 표시용 결함 이름 목록 ['Blowhole', 'Break', ...]
    folder_map  : {표시명 → 실제 폴더명} 매핑. None이면 전역 FOLDER_MAP 사용

    Returns
    -------
    pairs  : List[(jpg_path, png_path)]  ← (이미지, 마스크)
    labels : List[str]                   ← stratify 용
    """
    if folder_map is None:
        folder_map = FOLDER_MAP

    pairs, labels = [], []

    for defect in defect_types:
        folder   = folder_map.get(defect, defect)
        imgs_dir = data_root / folder / "Imgs"

        if not imgs_dir.exists():
            print(f"  [WARN] {folder}/Imgs: 폴더 없음 → 건너뜀")
            continue

        # .jpg = 원본 이미지, 동일 stem + .png = 마스크
        jpg_files = sorted(imgs_dir.glob("*.jpg"))

        if len(jpg_files) == 0:
            print(f"  [WARN] {folder}/Imgs: .jpg 파일 없음 → 건너뜀")
            continue

        matched = 0
        for jpg_path in jpg_files:
            png_path = jpg_path.with_suffix('.png')
            if not png_path.exists():
                continue           # 마스크 없는 파일은 제외
            pairs.append((jpg_path, png_path))
            labels.append(defect)
            matched += 1

        if matched == 0:
            print(f"  [WARN] {folder}: jpg-png 매칭 쌍 없음 → 건너뜀")

    print(f"\n총 이미지-마스크 쌍: {len(pairs)}개")
    for d in defect_types:
        cnt = labels.count(d)
        print(f"  {d:<12s} (MT_{d}): {cnt}쌍")

    return pairs, labels


def get_transforms(mode: str = 'train') -> A.Compose:
    """
    albumentations 증강 파이프라인

    mode = 'train' : 강한 증강 (소량 데이터 보완)
    mode = 'val'   : 리사이즈 + 정규화만
    """
    normalize = A.Normalize(mean=[0.485, 0.456, 0.406],
                             std =[0.229, 0.224, 0.225])
    if mode == 'train':
        return A.Compose([
            A.Resize(IMG_SIZE, IMG_SIZE),
            A.HorizontalFlip(p=0.5),
            A.VerticalFlip(p=0.5),
            A.RandomRotate90(p=0.5),
            A.ShiftScaleRotate(shift_limit=0.1, scale_limit=0.15,
                               rotate_limit=30, p=0.6),
            A.RandomBrightnessContrast(brightness_limit=0.3,
                                       contrast_limit=0.3, p=0.5),
            A.GaussNoise(var_limit=(10, 80), p=0.4),
            A.OneOf([
                A.ElasticTransform(alpha=120, sigma=6, p=0.3),
                A.GridDistortion(num_steps=5, distort_limit=0.3, p=0.3),
                A.OpticalDistortion(distort_limit=0.2, p=0.3),
            ], p=0.4),
            A.CoarseDropout(max_holes=8, max_height=20, max_width=20, p=0.3),
            normalize,
            ToTensorV2(),
        ])
    else:
        return A.Compose([
            A.Resize(IMG_SIZE, IMG_SIZE),
            normalize,
            ToTensorV2(),
        ])


class MagneticTileDataset(Dataset):
    """
    자석 타일 결함 세그먼테이션 Dataset

    - 그레이스케일 → RGB 3채널 복사 (사전학습 인코더 호환)
    - 마스크 : (pixel > 128) → float32 이진 마스크
    - 반환   : image (3, H, W), mask (1, H, W)
    """

    MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    STD  = np.array([0.229, 0.224, 0.225], dtype=np.float32)

    def __init__(self, pairs: list, img_size: int = IMG_SIZE,
                 transform: A.Compose = None):
        self.pairs     = pairs
        self.img_size  = img_size
        self.transform = transform

    def __len__(self) -> int:
        return len(self.pairs)

    def __getitem__(self, idx: int):
        img_path, mask_path = self.pairs[idx]

        # 이미지 : Gray → RGB
        img = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise FileNotFoundError(f"이미지 로드 실패: {img_path}")
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)  # (H, W, 3) uint8

        # 마스크 : 이진화 → float32
        mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
        if mask is None:
            mask = np.zeros(img.shape[:2], dtype=np.float32)
        else:
            mask = (mask > 128).astype(np.float32)  # 0 or 1

        # 증강
        if self.transform is not None:
            augmented = self.transform(image=img, mask=mask)
            img  = augmented['image']   # FloatTensor (3, H, W)
            mask = augmented['mask']    # FloatTensor (H, W)
        else:
            img  = cv2.resize(img,  (self.img_size, self.img_size))
            mask = cv2.resize(mask, (self.img_size, self.img_size),
                              interpolation=cv2.INTER_NEAREST)
            # 정규화 + 텐서 변환
            img  = (img.astype(np.float32) / 255.0 - self.MEAN) / self.STD
            img  = torch.from_numpy(img).permute(2, 0, 1)   # (3, H, W)
            mask = torch.from_numpy(mask)                    # (H, W)

        # mask 차원 통일: (H, W) → (1, H, W)
        if mask.dim() == 2:
            mask = mask.unsqueeze(0)

        return img.float(), mask.float()


# ===================================================================
# Section 2: 모델 아키텍처
# ===================================================================

# ── 2-1. 공통 블록 ────────────────────────────────────────────────────

class DoubleConv(nn.Module):
    """Conv-BN-ReLU × 2 (U-Net 기본 블록)"""

    def __init__(self, in_ch: int, out_ch: int):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.block(x)


# ── 2-2. Vanilla U-Net ───────────────────────────────────────────────

class UNet(nn.Module):
    """
    Vanilla U-Net (이진 세그먼테이션)

    Encoder  : DoubleConv × 4 + MaxPool
    Bottleneck: DoubleConv(512, 1024)
    Decoder  : ConvTranspose2d + DoubleConv × 4
    Output   : 1채널 logit (BCEWithLogitsLoss 사용)
    """

    def __init__(self, in_ch: int = 3, out_ch: int = 1,
                 features: list = [64, 128, 256, 512]):
        super().__init__()
        self.pool     = nn.MaxPool2d(2, 2)
        self.encoders = nn.ModuleList()
        self.upconvs  = nn.ModuleList()
        self.decoders = nn.ModuleList()

        # 인코더
        ch = in_ch
        for f in features:
            self.encoders.append(DoubleConv(ch, f))
            ch = f

        # 보틀넥
        self.bottleneck = DoubleConv(features[-1], features[-1] * 2)

        # 디코더
        for f in reversed(features):
            self.upconvs.append(
                nn.ConvTranspose2d(f * 2, f, kernel_size=2, stride=2)
            )
            self.decoders.append(DoubleConv(f * 2, f))

        self.final = nn.Conv2d(features[0], out_ch, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        skips = []
        for enc in self.encoders:
            x = enc(x)
            skips.append(x)
            x = self.pool(x)

        x = self.bottleneck(x)

        for idx in range(len(self.decoders)):
            x    = self.upconvs[idx](x)
            skip = skips[-(idx + 1)]
            # 크기 불일치 안전 처리
            if x.shape[2:] != skip.shape[2:]:
                x = F.interpolate(x, size=skip.shape[2:],
                                  mode='bilinear', align_corners=True)
            x = torch.cat([skip, x], dim=1)
            x = self.decoders[idx](x)

        return self.final(x)


# ── 2-3. Attention Gate ──────────────────────────────────────────────

class AttentionGate(nn.Module):
    """
    Attention Gate
    (Oktay et al., "Attention U-Net: Learning Where to Look for the Pancreas",
     MIDL 2018)

    Skip Connection 피처에 소프트 어텐션 마스크(α ∈ [0,1])를 곱하여
    관련 없는 배경 피처를 억제하고 결함 영역에 집중하게 함.

    Parameters
    ----------
    F_g  : gating signal (디코더) 채널 수
    F_l  : skip connection (인코더) 채널 수
    F_int: 중간 채널 수 (보통 F_l // 2)
    """

    def __init__(self, F_g: int, F_l: int, F_int: int):
        super().__init__()
        # gating signal 투영
        self.W_g = nn.Sequential(
            nn.Conv2d(F_g,  F_int, kernel_size=1, bias=False),
            nn.BatchNorm2d(F_int),
        )
        # skip connection 투영
        self.W_x = nn.Sequential(
            nn.Conv2d(F_l,  F_int, kernel_size=1, bias=False),
            nn.BatchNorm2d(F_int),
        )
        # attention coefficient 출력 (sigmoid → 0~1)
        self.psi = nn.Sequential(
            nn.Conv2d(F_int, 1, kernel_size=1, bias=False),
            nn.BatchNorm2d(1),
            nn.Sigmoid(),
        )
        self.relu = nn.ReLU(inplace=True)

    def forward(self, g: torch.Tensor, x: torch.Tensor) -> torch.Tensor:
        """
        g : (N, F_g, H, W) — 디코더 gating signal (upsampled)
        x : (N, F_l, H, W) — 인코더 skip connection
        → x * α             (N, F_l, H, W)
        """
        # g를 x와 동일 해상도로 맞춤 (크기 다를 경우 안전 처리)
        g_proj = self.W_g(g)
        if g_proj.shape[2:] != x.shape[2:]:
            g_proj = F.interpolate(g_proj, size=x.shape[2:],
                                   mode='bilinear', align_corners=True)
        x_proj = self.W_x(x)
        alpha  = self.psi(self.relu(g_proj + x_proj))  # (N, 1, H, W)
        return x * alpha                                 # broadcast


# ── 2-4. Attention U-Net ─────────────────────────────────────────────

class AttentionUNet(nn.Module):
    """
    Attention U-Net — 모든 Skip Connection에 AttentionGate 삽입

    Crack(57장) · Fray(32장) 같은 작은 결함에 특히 효과적.
    파라미터는 Vanilla U-Net 대비 약 +1M 증가.
    """

    def __init__(self, in_ch: int = 3, out_ch: int = 1,
                 features: list = [64, 128, 256, 512]):
        super().__init__()
        self.pool      = nn.MaxPool2d(2, 2)
        self.encoders  = nn.ModuleList()
        self.upconvs   = nn.ModuleList()
        self.att_gates = nn.ModuleList()
        self.decoders  = nn.ModuleList()

        # 인코더
        ch = in_ch
        for f in features:
            self.encoders.append(DoubleConv(ch, f))
            ch = f

        # 보틀넥
        self.bottleneck = DoubleConv(features[-1], features[-1] * 2)

        # 디코더 (+ AttentionGate)
        for f in reversed(features):
            self.upconvs.append(
                nn.ConvTranspose2d(f * 2, f, kernel_size=2, stride=2)
            )
            # F_g = F_l = f,  F_int = f // 2
            self.att_gates.append(
                AttentionGate(F_g=f, F_l=f, F_int=max(f // 2, 1))
            )
            self.decoders.append(DoubleConv(f * 2, f))

        self.final = nn.Conv2d(features[0], out_ch, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # 인코더
        skips = []
        for enc in self.encoders:
            x = enc(x)
            skips.append(x)
            x = self.pool(x)

        # 보틀넥
        x = self.bottleneck(x)

        # 디코더 with Attention
        for i in range(len(self.decoders)):
            g    = self.upconvs[i](x)                  # upsample → gating signal
            skip = skips[-(i + 1)]                      # 인코더 skip
            skip = self.att_gates[i](g=g, x=skip)       # attention 적용
            # 크기 불일치 안전 처리
            if g.shape[2:] != skip.shape[2:]:
                g = F.interpolate(g, size=skip.shape[2:],
                                  mode='bilinear', align_corners=True)
            x = torch.cat([skip, g], dim=1)
            x = self.decoders[i](x)

        return self.final(x)


# ── 2-5. ResNet34 U-Net ──────────────────────────────────────────────

class ResNetUNet(nn.Module):
    """
    ResNet34 백본 U-Net (ImageNet pretrained 전이학습)

    인코더 채널 흐름 (Input 224×224):
      enc1 (conv1,s=2)  → [64,  112, 112]
      pool1 (maxpool)   → [64,   56,  56]
      enc2 (layer1)     → [64,   56,  56]
      enc3 (layer2,s=2) → [128,  28,  28]
      enc4 (layer3,s=2) → [256,  14,  14]
      enc5 (layer4,s=2) → [512,   7,   7]
    """

    def __init__(self, out_ch: int = 1):
        super().__init__()
        resnet = tv_models.resnet34(
            weights=tv_models.ResNet34_Weights.IMAGENET1K_V1
        )

        # 인코더 (ResNet34 레이어 재사용)
        self.enc1  = nn.Sequential(resnet.conv1, resnet.bn1, resnet.relu)
        self.pool1 = resnet.maxpool
        self.enc2  = resnet.layer1   # out: 64
        self.enc3  = resnet.layer2   # out: 128
        self.enc4  = resnet.layer3   # out: 256
        self.enc5  = resnet.layer4   # out: 512

        # 디코더 (512→256→128→64→64→32)
        self.up4  = nn.ConvTranspose2d(512, 256, kernel_size=2, stride=2)
        self.dec4 = DoubleConv(512, 256)   # cat(up4=256, e4=256) → 512

        self.up3  = nn.ConvTranspose2d(256, 128, kernel_size=2, stride=2)
        self.dec3 = DoubleConv(256, 128)   # cat(up3=128, e3=128) → 256

        self.up2  = nn.ConvTranspose2d(128, 64, kernel_size=2, stride=2)
        self.dec2 = DoubleConv(128, 64)    # cat(up2=64,  e2=64)  → 128

        self.up1  = nn.ConvTranspose2d(64, 64, kernel_size=2, stride=2)
        self.dec1 = DoubleConv(128, 64)    # cat(up1=64,  e1=64)  → 128

        self.up0  = nn.ConvTranspose2d(64, 32, kernel_size=2, stride=2)
        self.dec0 = DoubleConv(32, 32)     # no skip at this level

        self.final = nn.Conv2d(32, out_ch, kernel_size=1)

    def _cat(self, a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
        """크기 불일치 안전 cat"""
        if a.shape[2:] != b.shape[2:]:
            a = F.interpolate(a, size=b.shape[2:],
                              mode='bilinear', align_corners=True)
        return torch.cat([a, b], dim=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        e1 = self.enc1(x)               # [64, 112, 112]
        e2 = self.enc2(self.pool1(e1))  # [64,  56,  56]
        e3 = self.enc3(e2)              # [128, 28,  28]
        e4 = self.enc4(e3)              # [256, 14,  14]
        e5 = self.enc5(e4)              # [512,  7,   7]

        d4 = self.dec4(self._cat(self.up4(e5), e4))  # [256, 14, 14]
        d3 = self.dec3(self._cat(self.up3(d4), e3))  # [128, 28, 28]
        d2 = self.dec2(self._cat(self.up2(d3), e2))  # [ 64, 56, 56]
        d1 = self.dec1(self._cat(self.up1(d2), e1))  # [ 64,112,112]
        d0 = self.dec0(self.up0(d1))                  # [ 32,224,224]

        return self.final(d0)


def count_params(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters())


# ===================================================================
# Section 3: 손실 함수
# ===================================================================

class DiceLoss(nn.Module):
    """픽셀 겹침 기반 손실 (배경/결함 불균형에 강함)"""

    def __init__(self, smooth: float = 1.0):
        super().__init__()
        self.smooth = smooth

    def forward(self, pred: torch.Tensor,
                target: torch.Tensor) -> torch.Tensor:
        pred  = torch.sigmoid(pred)
        p     = pred.contiguous().view(-1)
        t     = target.contiguous().view(-1)
        inter = (p * t).sum()
        return 1.0 - (2.0 * inter + self.smooth) / (
            p.sum() + t.sum() + self.smooth
        )


class CombinedLoss(nn.Module):
    """
    BCE (0.5) + Dice (0.5)
    → Vanilla U-Net 전용
    BCE : 픽셀 단위 정밀도
    Dice: 영역 겹침 비율
    """

    def __init__(self, bce_w: float = 0.5, dice_w: float = 0.5):
        super().__init__()
        self.bce    = nn.BCEWithLogitsLoss()
        self.dice   = DiceLoss()
        self.bce_w  = bce_w
        self.dice_w = dice_w

    def forward(self, pred: torch.Tensor,
                target: torch.Tensor) -> torch.Tensor:
        return self.bce_w * self.bce(pred, target) + \
               self.dice_w * self.dice(pred, target)


class FocalTverskyLoss(nn.Module):
    """
    Focal Tversky Loss
    (Abraham & Khan, "A Novel Focal Tversky Loss Function", ISBI 2019)

    Tversky Index:
        TI = (TP + smooth) / (TP + α·FP + β·FN + smooth)

    Parameters
    ----------
    alpha : FP 패널티 (낮게 → 오탐 관대)
    beta  : FN 패널티 (높게 → 미탐 엄격)  ← Crack/Fray 핵심
    gamma : Focal 지수 (어려운 샘플 집중)
    """

    def __init__(self, alpha: float = 0.3, beta: float = 0.7,
                 gamma: float = 0.75, smooth: float = 1.0):
        super().__init__()
        self.alpha  = alpha
        self.beta   = beta
        self.gamma  = gamma
        self.smooth = smooth

    def forward(self, pred: torch.Tensor,
                target: torch.Tensor) -> torch.Tensor:
        pred = torch.sigmoid(pred)
        p    = pred.contiguous().view(-1)
        t    = target.contiguous().view(-1)

        TP = (p * t).sum()
        FP = ((1.0 - t) * p).sum()
        FN = (t * (1.0 - p)).sum()

        tversky = (TP + self.smooth) / (
            TP + self.alpha * FP + self.beta * FN + self.smooth
        )
        return (1.0 - tversky) ** self.gamma


class CombinedFocalTverskyLoss(nn.Module):
    """
    BCE (0.4) + Focal Tversky (0.6)
    → Attention U-Net / ResNet34 U-Net 전용
    소수 결함 픽셀(Crack, Fray)에 특화
    """

    def __init__(self, bce_w: float = 0.4, ftl_w: float = 0.6,
                 alpha: float = 0.3, beta: float = 0.7, gamma: float = 0.75):
        super().__init__()
        self.bce   = nn.BCEWithLogitsLoss()
        self.ftl   = FocalTverskyLoss(alpha=alpha, beta=beta, gamma=gamma)
        self.bce_w = bce_w
        self.ftl_w = ftl_w

    def forward(self, pred: torch.Tensor,
                target: torch.Tensor) -> torch.Tensor:
        return self.bce_w * self.bce(pred, target) + \
               self.ftl_w * self.ftl(pred, target)


# ===================================================================
# Section 4: 학습 & 평가 유틸리티
# ===================================================================

# ── 4-1. 평가 지표 ────────────────────────────────────────────────────

def compute_dice(pred: torch.Tensor, target: torch.Tensor,
                 threshold: float = 0.5) -> float:
    """Dice Coefficient (F1 Score of segmentation)"""
    pred   = (torch.sigmoid(pred) > threshold).float()
    smooth = 1.0
    inter  = (pred.view(-1) * target.view(-1)).sum()
    return (
        (2.0 * inter + smooth) /
        (pred.view(-1).sum() + target.view(-1).sum() + smooth)
    ).item()


def compute_iou(pred: torch.Tensor, target: torch.Tensor,
                threshold: float = 0.5) -> float:
    """Intersection over Union"""
    pred   = (torch.sigmoid(pred) > threshold).float()
    smooth = 1.0
    inter  = (pred.view(-1) * target.view(-1)).sum()
    union  = pred.view(-1).sum() + target.view(-1).sum() - inter
    return ((inter + smooth) / (union + smooth)).item()


# ── 4-2. 1에폭 학습 / 검증 ───────────────────────────────────────────

def train_one_epoch(model: nn.Module, loader: DataLoader,
                    criterion: nn.Module,
                    optimizer: torch.optim.Optimizer) -> tuple:
    model.train()
    total_loss, total_dice, n = 0.0, 0.0, 0

    for images, masks in tqdm(loader, desc="  Train", leave=False):
        images, masks = images.to(device), masks.to(device)
        preds = model(images)
        loss  = criterion(preds, masks)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        bs = images.size(0)
        total_loss += loss.item() * bs
        total_dice += compute_dice(preds.detach(), masks) * bs
        n += bs

    return total_loss / n, total_dice / n


def evaluate(model: nn.Module, loader: DataLoader,
             criterion: nn.Module) -> tuple:
    model.eval()
    total_loss, total_dice, total_iou, n = 0.0, 0.0, 0.0, 0

    with torch.no_grad():
        for images, masks in tqdm(loader, desc="  Val  ", leave=False):
            images, masks = images.to(device), masks.to(device)
            preds = model(images)
            loss  = criterion(preds, masks)

            bs = images.size(0)
            total_loss += loss.item() * bs
            total_dice += compute_dice(preds, masks) * bs
            total_iou  += compute_iou(preds,  masks) * bs
            n += bs

    return total_loss / n, total_dice / n, total_iou / n


# ── 4-3. 전체 학습 루프 ───────────────────────────────────────────────

def train_segmentation(model: nn.Module,
                       train_loader: DataLoader,
                       val_loader: DataLoader,
                       criterion: nn.Module,
                       num_epochs: int,
                       lr: float,
                       model_name: str) -> tuple:
    """
    전체 학습 루프

    Returns
    -------
    model   : best val Dice 기준 복원된 모델
    history : dict  (train_loss, train_dice, val_loss, val_dice, val_iou)
    """
    optimizer = torch.optim.Adam(model.parameters(),
                                 lr=lr, weight_decay=WEIGHT_DECAY)
    # ReduceLROnPlateau — verbose 파라미터 제거 (PyTorch 2.10 호환)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='max', factor=0.5, patience=5
    )

    history  = {'train_loss': [], 'train_dice': [],
                'val_loss':   [], 'val_dice':   [], 'val_iou': []}
    best_dice = 0.0
    save_path = MODELS_DIR / f"best_{model_name}.pth"
    t0 = time.time()

    for epoch in range(num_epochs):
        print(f"\n  Epoch [{epoch+1}/{num_epochs}]", flush=True)

        tl, td = train_one_epoch(model, train_loader, criterion, optimizer)
        vl, vd, vi = evaluate(model, val_loader, criterion)
        scheduler.step(vd)

        history['train_loss'].append(tl)
        history['train_dice'].append(td)
        history['val_loss'].append(vl)
        history['val_dice'].append(vd)
        history['val_iou'].append(vi)

        cur_lr = optimizer.param_groups[0]['lr']
        print(f"  Train — Loss: {tl:.4f} | Dice: {td:.4f}")
        print(f"  Val   — Loss: {vl:.4f} | Dice: {vd:.4f} | IoU: {vi:.4f} | LR: {cur_lr:.2e}")

        if vd > best_dice:
            best_dice = vd
            torch.save(model.state_dict(), save_path)
            print(f"  ★ Best 저장! (Dice: {vd:.4f})")

    elapsed = (time.time() - t0) / 60
    print(f"\n  완료! {elapsed:.1f}분 | Best Dice: {best_dice:.4f}")

    # best 가중치 복원
    model.load_state_dict(
        torch.load(save_path, map_location=device, weights_only=True)
    )
    return model, history


# ── 4-4. TTA (Test-Time Augmentation) ────────────────────────────────

def predict_tta(model: nn.Module,
                image_tensor: torch.Tensor,
                threshold: float = 0.5) -> tuple:
    """
    4-flip TTA 예측

    원본 + 수평플립 + 수직플립 + 수평·수직플립 4개 예측을 sigmoid 후 평균.

    Parameters
    ----------
    model        : 학습된 모델 (eval 모드)
    image_tensor : (1, 3, H, W) 정규화된 FloatTensor (CPU or device)
    threshold    : 이진화 임계값

    Returns
    -------
    pred_mask  : (1, 1, H, W) 이진 마스크 (FloatTensor, CPU)
    pred_proba : (1, 1, H, W) 확률 (FloatTensor, CPU)
    """
    model.eval()
    # 모델이 올라가 있는 device를 자동 감지 (CPU / MPS / CUDA 모두 대응)
    model_device = next(model.parameters()).device
    img = image_tensor.to(model_device)  # (1, 3, H, W)
    preds = []

    with torch.no_grad():
        # ① 원본
        preds.append(torch.sigmoid(model(img)).cpu())

        # ② 수평 플립 (좌우)
        img_h = torch.flip(img, dims=[3])
        preds.append(torch.flip(torch.sigmoid(model(img_h)), dims=[3]).cpu())

        # ③ 수직 플립 (상하)
        img_v = torch.flip(img, dims=[2])
        preds.append(torch.flip(torch.sigmoid(model(img_v)), dims=[2]).cpu())

        # ④ 수평 + 수직 플립
        img_hv = torch.flip(img, dims=[2, 3])
        preds.append(
            torch.flip(torch.sigmoid(model(img_hv)), dims=[2, 3]).cpu()
        )

    pred_proba = torch.stack(preds, dim=0).mean(dim=0)   # (1, 1, H, W)
    pred_mask  = (pred_proba > threshold).float()
    return pred_mask, pred_proba


def evaluate_with_tta(model: nn.Module,
                      loader: DataLoader) -> tuple:
    """DataLoader 전체에 TTA 적용 후 평균 Dice / IoU 반환"""
    model.eval()
    total_dice, total_iou, n = 0.0, 0.0, 0
    smooth = 1.0

    for images, masks in tqdm(loader, desc="  TTA 평가", leave=False):
        for i in range(images.size(0)):
            img_s  = images[i].unsqueeze(0)   # (1, 3, H, W)
            msk_s  = masks[i].view(-1)         # (H*W,)
            _, proba = predict_tta(model, img_s)
            p = proba.view(-1)

            inter = (p * msk_s).sum()
            total_dice += (
                (2.0 * inter + smooth) / (p.sum() + msk_s.sum() + smooth)
            ).item()
            union = p.sum() + msk_s.sum() - inter
            total_iou  += ((inter + smooth) / (union + smooth)).item()
            n += 1

    return total_dice / n, total_iou / n


# ===================================================================
# Section 5: EDA & 시각화
# ===================================================================

def visualize_eda(data_root: Path, defect_types: list,
                  folder_map: dict = None) -> None:
    """
    01_data_distribution.png
    결함 유형별 이미지 수 막대 그래프 + 결함 vs 정상 파이 차트
    (.jpg 파일만 카운트 — .png는 마스크이므로 제외)
    """
    if folder_map is None:
        folder_map = FOLDER_MAP

    counts = []
    for d in defect_types:
        img_dir = data_root / folder_map.get(d, d) / "Imgs"
        counts.append(len(list(img_dir.glob("*.jpg"))) if img_dir.exists() else 0)

    free_dir   = data_root / FREE_FOLDER / "Imgs"
    free_count = len(list(free_dir.glob("*.jpg"))) if free_dir.exists() else 0
    total_defect = sum(counts)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle('자석 타일 표면 결함 데이터 분포', fontsize=14, fontweight='bold')

    # 막대 그래프
    bars = axes[0].bar(defect_types, counts, color=DEFECT_COLORS, edgecolor='white')
    axes[0].set_title('결함 유형별 이미지 수', fontweight='bold')
    axes[0].set_ylabel('이미지 수')
    axes[0].set_ylim(0, max(counts) * 1.2)
    for bar, val in zip(bars, counts):
        axes[0].text(bar.get_x() + bar.get_width() / 2,
                     bar.get_height() + 2, str(val),
                     ha='center', fontweight='bold', fontsize=11)

    # 파이 차트
    axes[1].pie(
        [total_defect, free_count],
        labels=[f'결함\n({total_defect}장)', f'정상(Free)\n({free_count}장)'],
        colors=['#e74c3c', '#2ecc71'],
        autopct='%1.1f%%', startangle=90,
        textprops={'fontsize': 11}
    )
    axes[1].set_title('결함 vs 정상 분포', fontweight='bold')

    plt.tight_layout()
    save_fig("01_data_distribution.png")


def visualize_samples(data_root: Path, defect_types: list,
                      folder_map: dict = None) -> None:
    """
    02_sample_images.png
    5종 결함 × 3열 (원본 / 마스크 / 오버레이)
    (.jpg = 이미지, 동일 이름 .png = 마스크)
    """
    if folder_map is None:
        folder_map = FOLDER_MAP

    fig, axes = plt.subplots(5, 3, figsize=(12, 18))
    col_titles = ['원본 이미지', '결함 마스크 (GT)', '오버레이']

    for row, defect in enumerate(defect_types):
        imgs_dir  = data_root / folder_map.get(defect, defect) / "Imgs"
        jpg_files = sorted(imgs_dir.glob("*.jpg")) if imgs_dir.exists() else []

        if not jpg_files:
            for c in range(3):
                axes[row, c].set_visible(False)
            continue

        jpg_path = jpg_files[0]
        png_path = jpg_path.with_suffix('.png')   # 동일 이름 .png = 마스크

        img  = cv2.imread(str(jpg_path), cv2.IMREAD_GRAYSCALE)
        mask = (cv2.imread(str(png_path), cv2.IMREAD_GRAYSCALE) > 128
                ).astype(np.uint8) if png_path.exists() else np.zeros_like(img)

        img_rgb = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB).astype(np.float32) / 255.0
        overlay = img_rgb.copy()
        overlay[mask == 1] = overlay[mask == 1] * 0.5 + np.array([1.0, 0.2, 0.2]) * 0.5
        overlay = np.clip(overlay, 0, 1)

        defect_ratio = mask.sum() / mask.size * 100

        axes[row, 0].imshow(img, cmap='gray')
        axes[row, 0].set_ylabel(defect, fontsize=12, fontweight='bold',
                                 rotation=0, labelpad=65)
        axes[row, 1].imshow(mask, cmap='gray')
        axes[row, 1].set_title(f'결함 비율: {defect_ratio:.2f}%', fontsize=9)
        axes[row, 2].imshow(overlay)

        for c in range(3):
            axes[row, c].axis('off')

    for c, t in enumerate(col_titles):
        axes[0, c].set_title(t, fontsize=11, fontweight='bold')

    plt.suptitle('자석 타일 표면 결함 5종 — 샘플', fontsize=14, fontweight='bold')
    plt.tight_layout()
    save_fig("02_sample_images.png")


def plot_curves(history: dict, model_title: str, fname: str) -> None:
    """
    03/04/05_*_curves.png
    Loss · Dice · IoU 3개 서브플롯 학습 곡선
    """
    ep = range(1, len(history['train_loss']) + 1)
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.5))

    # Loss
    axes[0].plot(ep, history['train_loss'], 'b--', alpha=0.7, label='Train')
    axes[0].plot(ep, history['val_loss'],   'r-',  label='Val')
    axes[0].set_title('Loss', fontweight='bold')
    axes[0].set_xlabel('Epoch'); axes[0].legend(); axes[0].grid(alpha=0.3)

    # Dice
    axes[1].plot(ep, history['train_dice'], 'b--', alpha=0.7, label='Train')
    axes[1].plot(ep, history['val_dice'],   'r-',  label='Val')
    axes[1].set_title('Dice Coefficient', fontweight='bold')
    axes[1].set_xlabel('Epoch'); axes[1].legend(); axes[1].grid(alpha=0.3)

    # IoU
    axes[2].plot(ep, history['val_iou'], 'g-', label='Val IoU')
    axes[2].set_title('IoU (Val)', fontweight='bold')
    axes[2].set_xlabel('Epoch'); axes[2].legend(); axes[2].grid(alpha=0.3)

    plt.suptitle(f'{model_title} — 학습 곡선', fontsize=13, fontweight='bold')
    plt.tight_layout()
    save_fig(fname)


def visualize_predictions(model: nn.Module,
                           val_dataset: MagneticTileDataset,
                           num_samples: int = 8) -> None:
    """
    06_predictions.png
    8행 × 5열 (원본 / GT / 기본 예측 / TTA 예측 / 오버레이)
    노랑=TP · 초록=FN · 빨강=FP
    """
    model.eval()
    MEAN = np.array([0.485, 0.456, 0.406])
    STD  = np.array([0.229, 0.224, 0.225])

    indices = np.random.choice(len(val_dataset), num_samples, replace=False)
    fig, axes = plt.subplots(num_samples, 5, figsize=(20, 3.5 * num_samples))
    col_titles = ['원본', '정답 (GT)', 'Pred (기본)', 'Pred (TTA)', '오버레이']

    for row, idx in enumerate(indices):
        image, gt_mask = val_dataset[idx]
        img_t = image.unsqueeze(0)   # (1,3,H,W)

        # 기본 예측 (모델 device 자동 감지)
        model_dev = next(model.parameters()).device
        with torch.no_grad():
            logit = model(img_t.to(model_dev))
            pred_basic = (torch.sigmoid(logit) > 0.5).float().cpu().squeeze().numpy()

        # TTA 예측
        pred_mask_tta, _ = predict_tta(model, img_t)
        pred_tta = pred_mask_tta.squeeze().numpy()

        # 역정규화
        img_np = image.permute(1, 2, 0).numpy()
        img_np = np.clip(img_np * STD + MEAN, 0, 1)

        gt_np = gt_mask.squeeze().numpy()

        # 오버레이 (TTA 기준) — 노랑=TP, 초록=FN, 빨강=FP
        overlay = img_np.copy()
        overlay[(gt_np > 0.5) & (pred_tta > 0.5)] = [1.0, 1.0, 0.0]  # TP
        overlay[(gt_np > 0.5) & (pred_tta < 0.5)] = [0.0, 1.0, 0.0]  # FN
        overlay[(gt_np < 0.5) & (pred_tta > 0.5)] = [1.0, 0.0, 0.0]  # FP
        overlay = np.clip(overlay, 0, 1)

        # Dice 계산
        dice_b = compute_dice(logit.cpu(), gt_mask.unsqueeze(0))

        smooth = 1.0
        p_tta  = pred_mask_tta.view(-1)
        g_tta  = gt_mask.view(-1)
        inter  = (p_tta * g_tta).sum()
        dice_t = ((2.0 * inter + smooth) /
                  (p_tta.sum() + g_tta.sum() + smooth)).item()

        axes[row, 0].imshow(img_np);                          axes[row, 0].axis('off')
        axes[row, 1].imshow(gt_np, cmap='gray');              axes[row, 1].axis('off')
        axes[row, 2].imshow(pred_basic, cmap='gray')
        axes[row, 2].set_title(f'Dice: {dice_b:.3f}', fontsize=9)
        axes[row, 2].axis('off')
        axes[row, 3].imshow(pred_tta, cmap='gray')
        axes[row, 3].set_title(f'TTA Dice: {dice_t:.3f}', fontsize=9)
        axes[row, 3].axis('off')
        axes[row, 4].imshow(overlay);                         axes[row, 4].axis('off')

    for c, t in enumerate(col_titles):
        axes[0, c].set_title(t, fontsize=10, fontweight='bold')

    # 범례
    patches = [
        mpatches.Patch(color=[1,1,0], label='TP (정확)'),
        mpatches.Patch(color=[0,1,0], label='FN (놓침)'),
        mpatches.Patch(color=[1,0,0], label='FP (오탐)'),
    ]
    fig.legend(handles=patches, loc='lower center', ncol=3,
               fontsize=10, bbox_to_anchor=(0.5, -0.01))

    plt.suptitle('예측 결과 비교 (기본 vs TTA)',
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    save_fig("06_predictions.png")


def evaluate_per_defect(model: nn.Module, data_root: Path,
                         defect_types: list,
                         folder_map: dict = None) -> dict:
    """
    07_per_defect_metrics.png
    결함 유형별 Dice / IoU (TTA 적용) 개별 평가

    .jpg = 원본 이미지, 동일 stem .png = 마스크 (같은 Imgs/ 폴더)
    """
    if folder_map is None:
        folder_map = FOLDER_MAP

    model.eval()
    MEAN_T = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
    STD_T  = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
    results = {}

    for defect in defect_types:
        folder   = folder_map.get(defect, defect)
        imgs_dir = data_root / folder / "Imgs"
        if not imgs_dir.exists():
            print(f"  [WARN] {folder}/Imgs 없음 → 건너뜀")
            continue

        jpg_files = sorted(imgs_dir.glob("*.jpg"))
        # (jpg_path, png_path) 쌍 필터링
        pairs = [(jp, jp.with_suffix('.png'))
                 for jp in jpg_files if jp.with_suffix('.png').exists()]

        if not pairs:
            print(f"  [WARN] {folder}: jpg-png 쌍 없음 → 건너뜀")
            continue

        dices, ious, smooth = [], [], 1.0
        for jp, mp in pairs:
            img  = cv2.imread(str(jp), cv2.IMREAD_GRAYSCALE)
            img  = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
            img  = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
            img_t = (torch.from_numpy(img).permute(2, 0, 1).float() / 255.0
                     - MEAN_T) / STD_T

            mask = cv2.imread(str(mp), cv2.IMREAD_GRAYSCALE)
            mask = cv2.resize(mask, (IMG_SIZE, IMG_SIZE),
                              interpolation=cv2.INTER_NEAREST)
            mask_t = torch.from_numpy(
                (mask > 128).astype(np.float32)
            ).view(-1)

            _, proba = predict_tta(model, img_t.unsqueeze(0))
            p = proba.view(-1)

            inter = (p * mask_t).sum()
            dices.append(
                ((2.0 * inter + smooth) / (p.sum() + mask_t.sum() + smooth)).item()
            )
            union = p.sum() + mask_t.sum() - inter
            ious.append(((inter + smooth) / (union + smooth)).item())

        results[defect] = {
            'dice':  float(np.mean(dices)) if dices else 0.0,
            'iou':   float(np.mean(ious))  if ious  else 0.0,
            'count': len(pairs),
        }

    # 출력
    print(f"\n{'='*55}")
    print(f"{'결함 유형별 성능 (TTA 적용)':^55}")
    print(f"{'='*55}")
    print(f"{'유형':<14} {'샘플수':>6} {'Dice':>10} {'IoU':>10}")
    print(f"{'-'*55}")
    for d, r in results.items():
        print(f"{d:<14} {r['count']:>6} {r['dice']:>10.4f} {r['iou']:>10.4f}")

    # 시각화
    valid_types = [d for d in defect_types if d in results]
    colors = DEFECT_COLORS[:len(valid_types)]

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    for ax, metric, title in [
        (axes[0], 'dice', 'Dice Coefficient (TTA)'),
        (axes[1], 'iou',  'IoU (TTA)'),
    ]:
        vals = [results[d][metric] for d in valid_types]
        bars = ax.bar(valid_types, vals, color=colors, edgecolor='white')
        ax.set_title(title, fontweight='bold')
        ax.set_ylim(0, 1.1)
        ax.grid(axis='y', alpha=0.3)
        for bar, v in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.02,
                    f'{v:.3f}', ha='center', fontsize=10, fontweight='bold')

    plt.suptitle('결함 유형별 세그먼테이션 성능 (TTA 적용)',
                 fontsize=13, fontweight='bold')
    plt.tight_layout()
    save_fig("07_per_defect_metrics.png")
    return results


def plot_model_comparison(hist_v: dict, hist_a: dict, hist_r: dict,
                           dice_tta_v: float, dice_tta_a: float, dice_tta_r: float,
                           iou_tta_v:  float, iou_tta_a:  float, iou_tta_r:  float
                           ) -> None:
    """
    08_model_comparison.png
    3모델 × 기본/TTA — Dice & IoU 나란히 비교
    """
    names  = ['Vanilla\nU-Net', 'Attention\nU-Net', 'ResNet34\nU-Net']
    dice_b = [max(hist_v['val_dice']), max(hist_a['val_dice']), max(hist_r['val_dice'])]
    dice_t = [dice_tta_v,  dice_tta_a,  dice_tta_r]
    iou_b  = [max(hist_v['val_iou']),  max(hist_a['val_iou']),  max(hist_r['val_iou'])]
    iou_t  = [iou_tta_v,   iou_tta_a,   iou_tta_r]

    x     = np.arange(len(names))
    width = 0.3

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
    for ax, b_vals, t_vals, ylabel, title in [
        (axes[0], dice_b, dice_t, 'Dice Coefficient', 'Dice 비교'),
        (axes[1], iou_b,  iou_t,  'IoU',              'IoU 비교'),
    ]:
        b1 = ax.bar(x - width / 2, b_vals, width,
                    label='기본 예측', color='#3498db', alpha=0.85, edgecolor='white')
        b2 = ax.bar(x + width / 2, t_vals, width,
                    label='TTA 적용', color='#e74c3c', alpha=0.85, edgecolor='white')
        ax.set_xticks(x); ax.set_xticklabels(names, fontsize=10)
        ax.set_ylabel(ylabel, fontweight='bold')
        ax.set_title(title, fontweight='bold')
        ax.set_ylim(0, 1.1)
        ax.legend(fontsize=9)
        ax.grid(axis='y', alpha=0.3)
        for bars, vals in [(b1, b_vals), (b2, t_vals)]:
            for bar, v in zip(bars, vals):
                ax.text(bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + 0.01,
                        f'{v:.3f}', ha='center', fontsize=9, fontweight='bold')

    plt.suptitle('3모델 + TTA 최종 성능 비교', fontsize=14, fontweight='bold')
    plt.tight_layout()
    save_fig("08_model_comparison.png")


def save_results(hist_v: dict, hist_a: dict, hist_r: dict,
                 dice_tta_v: float, dice_tta_a: float, dice_tta_r: float,
                 iou_tta_v:  float, iou_tta_a:  float, iou_tta_r:  float,
                 defect_results: dict) -> None:
    """09_final_summary.json 저장"""
    summary = {
        "project":     "자석 타일 표면 결함 세그먼테이션",
        "dataset":     "Magnetic Tile Surface Defects (1,344장, 5종 결함)",
        "dataset_url": "https://www.kaggle.com/datasets/alex000kim/magnetic-tile-surface-defects",
        "task":        "이진 세그먼테이션 (결함 vs 배경)",
        "img_size":    IMG_SIZE,
        "batch_size":  BATCH_SIZE,
        "models": {
            "vanilla_unet": {
                "loss":       "BCE(0.5) + Dice(0.5)",
                "epochs":     EPOCHS_VANILLA,
                "best_dice":  round(max(hist_v['val_dice']), 4),
                "best_iou":   round(max(hist_v['val_iou']),  4),
                "tta_dice":   round(dice_tta_v, 4),
                "tta_iou":    round(iou_tta_v,  4),
            },
            "attention_unet": {
                "loss":       "BCE(0.4) + FocalTversky(0.6, α=0.3, β=0.7, γ=0.75)",
                "epochs":     EPOCHS_ATTN,
                "best_dice":  round(max(hist_a['val_dice']), 4),
                "best_iou":   round(max(hist_a['val_iou']),  4),
                "tta_dice":   round(dice_tta_a, 4),
                "tta_iou":    round(iou_tta_a,  4),
            },
            "resnet34_unet": {
                "loss":       "BCE(0.4) + FocalTversky(0.6, α=0.3, β=0.7, γ=0.75)",
                "epochs":     EPOCHS_RESNET,
                "best_dice":  round(max(hist_r['val_dice']), 4),
                "best_iou":   round(max(hist_r['val_iou']),  4),
                "tta_dice":   round(dice_tta_r, 4),
                "tta_iou":    round(iou_tta_r,  4),
            },
        },
        "per_defect_tta": {
            d: {"dice": round(r['dice'], 4), "iou": round(r['iou'], 4)}
            for d, r in defect_results.items()
        },
        "key_techniques": [
            "Attention Gate — Skip Connection 소프트 어텐션",
            "Focal Tversky Loss — FN 패널티 강화 (α=0.3, β=0.7, γ=0.75)",
            "TTA (Test-Time Augmentation) — 4방향 플립 앙상블",
            "Albumentations — 강한 증강 (392장 보완)",
        ],
    }

    out_path = RESULTS_DIR / "09_final_summary.json"
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"  → 저장: {out_path.name}")


# ===================================================================
# Section 6: main()
# ===================================================================

def main() -> None:
    print("=" * 65)
    print("  SubTopic B: 자석 타일 표면 결함 세그먼테이션")
    print("=" * 65)
    print(f"  Device : {device}")
    print(f"  PyTorch: {torch.__version__}")

    # ── Step 1: 초기화 ───────────────────────────────────────────────
    print("\n[Step 1] 초기화")
    setup_seed()
    setup_font()
    setup_dirs()

    # ── Step 2: 데이터 로드 & EDA ────────────────────────────────────
    print("\n[Step 2] 데이터 로드 & EDA")
    if not DATA_ROOT.exists():
        print(f"\n  [ERROR] 데이터 경로를 찾을 수 없습니다: {DATA_ROOT}")
        print("  Kaggle에서 데이터를 다운로드하고 data/ 폴더에 압축 해제 후 재실행하세요.")
        print("  명령어: kaggle datasets download -d alex000kim/magnetic-tile-surface-defects")
        sys.exit(1)

    all_pairs, all_labels = collect_pairs(DATA_ROOT, DEFECT_TYPES, FOLDER_MAP)
    if len(all_pairs) == 0:
        print("  [ERROR] 이미지-마스크 쌍을 찾을 수 없습니다.")
        print(f"  데이터 경로 확인: {DATA_ROOT}")
        sys.exit(1)

    print("\n  EDA 시각화 생성 중...")
    visualize_eda(DATA_ROOT, DEFECT_TYPES, FOLDER_MAP)
    visualize_samples(DATA_ROOT, DEFECT_TYPES, FOLDER_MAP)

    # ── Step 3: Dataset / DataLoader ─────────────────────────────────
    print("\n[Step 3] Dataset / DataLoader 구성")
    train_pairs, val_pairs = train_test_split(
        all_pairs, test_size=0.2, random_state=SEED, stratify=all_labels
    )
    print(f"  Train: {len(train_pairs)}쌍 / Val: {len(val_pairs)}쌍")

    train_dataset = MagneticTileDataset(train_pairs, IMG_SIZE, get_transforms('train'))
    val_dataset   = MagneticTileDataset(val_pairs,   IMG_SIZE, get_transforms('val'))

    train_loader = DataLoader(
        train_dataset, batch_size=BATCH_SIZE,
        shuffle=True,  num_workers=NUM_WORKERS, pin_memory=True
    )
    val_loader = DataLoader(
        val_dataset, batch_size=BATCH_SIZE,
        shuffle=False, num_workers=NUM_WORKERS, pin_memory=True
    )

    # 배치 확인
    sample_imgs, sample_masks = next(iter(train_loader))
    print(f"  배치 shape — 이미지: {sample_imgs.shape} | 마스크: {sample_masks.shape}")
    print(f"  결함 픽셀 비율: {sample_masks.mean() * 100:.2f}%")

    # ── Step 4: [1/3] Vanilla U-Net ──────────────────────────────────
    print("\n" + "=" * 65)
    print("  [Step 4 / 1/3] Vanilla U-Net 학습")
    print("  손실 함수: BCE(0.5) + Dice(0.5)")
    print("=" * 65)

    vanilla_model = UNet(in_ch=3, out_ch=1).to(device)
    print(f"  파라미터 수: {count_params(vanilla_model):,}개")

    criterion_v = CombinedLoss()
    vanilla_model, hist_v = train_segmentation(
        vanilla_model, train_loader, val_loader,
        criterion_v, EPOCHS_VANILLA, LR, "unet_vanilla"
    )
    plot_curves(hist_v, "Vanilla U-Net", "03_vanilla_curves.png")

    # ── Step 5: [2/3] Attention U-Net ────────────────────────────────
    print("\n" + "=" * 65)
    print("  [Step 5 / 2/3] Attention U-Net 학습")
    print("  손실 함수: BCE(0.4) + Focal Tversky(0.6)")
    print("=" * 65)

    attn_model = AttentionUNet(in_ch=3, out_ch=1).to(device)
    print(f"  파라미터 수: {count_params(attn_model):,}개")

    criterion_a = CombinedFocalTverskyLoss()
    attn_model, hist_a = train_segmentation(
        attn_model, train_loader, val_loader,
        criterion_a, EPOCHS_ATTN, LR, "unet_attention"
    )
    plot_curves(hist_a, "Attention U-Net", "04_attention_curves.png")

    # ── Step 6: TTA 평가 (Vanilla & Attention) ───────────────────────
    print("\n[Step 6] TTA 평가")
    print("  [TTA] Vanilla U-Net 평가 중...")
    dice_tta_v, iou_tta_v = evaluate_with_tta(vanilla_model, val_loader)
    print(f"  Vanilla  → TTA Dice: {dice_tta_v:.4f} | TTA IoU: {iou_tta_v:.4f}")

    print("  [TTA] Attention U-Net 평가 중...")
    dice_tta_a, iou_tta_a = evaluate_with_tta(attn_model, val_loader)
    print(f"  Attention → TTA Dice: {dice_tta_a:.4f} | TTA IoU: {iou_tta_a:.4f}")

    print(f"\n  TTA 전후 비교:")
    print(f"  Vanilla   기본: {max(hist_v['val_dice']):.4f} → TTA: {dice_tta_v:.4f} "
          f"(+{dice_tta_v - max(hist_v['val_dice']):.4f})")
    print(f"  Attention 기본: {max(hist_a['val_dice']):.4f} → TTA: {dice_tta_a:.4f} "
          f"(+{dice_tta_a - max(hist_a['val_dice']):.4f})")

    # ── Step 7: 예측 시각화 (TTA 포함) ──────────────────────────────
    print("\n[Step 7] 예측 시각화 (기본 vs TTA)")
    visualize_predictions(attn_model, val_dataset, num_samples=8)

    # ── Step 8: 결함 유형별 성능 분석 ────────────────────────────────
    print("\n[Step 8] 결함 유형별 성능 분석 (TTA 적용)")
    defect_results = evaluate_per_defect(attn_model, DATA_ROOT, DEFECT_TYPES, FOLDER_MAP)

    # ── Step 9: [3/3] ResNet34 U-Net ─────────────────────────────────
    print("\n" + "=" * 65)
    print("  [Step 9 / 3/3] ResNet34 U-Net 학습")
    print("  손실 함수: BCE(0.4) + Focal Tversky(0.6)")
    print("=" * 65)

    resnet_model = ResNetUNet(out_ch=1).to(device)
    print(f"  파라미터 수: {count_params(resnet_model):,}개")

    criterion_r = CombinedFocalTverskyLoss()
    resnet_model, hist_r = train_segmentation(
        resnet_model, train_loader, val_loader,
        criterion_r, EPOCHS_RESNET, LR, "unet_resnet34"
    )
    plot_curves(hist_r, "ResNet34 U-Net", "05_resnet34_curves.png")

    print("  [TTA] ResNet34 U-Net 평가 중...")
    dice_tta_r, iou_tta_r = evaluate_with_tta(resnet_model, val_loader)
    print(f"  ResNet34 → TTA Dice: {dice_tta_r:.4f} | TTA IoU: {iou_tta_r:.4f}")

    # ── Step 10: 3모델 비교 & 결과 저장 ─────────────────────────────
    print("\n[Step 10] 3모델 비교 & 결과 저장")
    plot_model_comparison(
        hist_v, hist_a, hist_r,
        dice_tta_v, dice_tta_a, dice_tta_r,
        iou_tta_v,  iou_tta_a,  iou_tta_r,
    )
    save_results(
        hist_v, hist_a, hist_r,
        dice_tta_v, dice_tta_a, dice_tta_r,
        iou_tta_v,  iou_tta_a,  iou_tta_r,
        defect_results,
    )

    # ── 최종 요약 출력 ───────────────────────────────────────────────
    print("\n" + "=" * 65)
    print(f"  {'3모델 최종 비교 (Validation Set)':^61}")
    print("=" * 65)
    print(f"  {'모델':<18} {'손실함수':<24} {'Dice':>7} {'TTA':>8} {'IoU':>7} {'TTA':>8}")
    print(f"  {'-'*61}")
    rows = [
        ("Vanilla U-Net",   "BCE+Dice",
         max(hist_v['val_dice']), dice_tta_v,
         max(hist_v['val_iou']),  iou_tta_v),
        ("Attention U-Net", "BCE+FocalTversky",
         max(hist_a['val_dice']), dice_tta_a,
         max(hist_a['val_iou']),  iou_tta_a),
        ("ResNet34 U-Net",  "BCE+FocalTversky",
         max(hist_r['val_dice']), dice_tta_r,
         max(hist_r['val_iou']),  iou_tta_r),
    ]
    for name, loss, d, dt, i, it in rows:
        print(f"  {name:<18} {loss:<24} {d:>7.4f} {dt:>8.4f} {i:>7.4f} {it:>8.4f}")
    print("=" * 65)

    print("\n  생성된 파일 목록:")
    for f in sorted(RESULTS_DIR.iterdir()):
        print(f"    results/{f.name}")
    for f in sorted(MODELS_DIR.iterdir()):
        print(f"    models/{f.name}")

    print("\n  완료! 모든 결과가 저장되었습니다.")


# ===================================================================
# 실행 진입점
# ===================================================================

if __name__ == '__main__':
    main()

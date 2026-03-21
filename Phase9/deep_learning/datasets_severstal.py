"""
Severstal PyTorch Dataset

256×256 패치를 PyTorch Dataset/DataLoader로 변환.
- SeverstalBinaryDataset: 이진 분류 (정상=0, 비정상=1)
- SeverstalDefect4Dataset: 4종 결함 분류 (ClassId 1~4 → 0~3)
"""

import os
import sys
import numpy as np
import cv2
import torch
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.severstal_loader import CLASS_NAMES_KR, CLASS_NAMES_EN, CLASS_ABBR


class SeverstalBinaryDataset(Dataset):
    """Severstal 이진 분류 PyTorch Dataset."""

    def __init__(
        self,
        images: np.ndarray,
        labels: np.ndarray,
        transform=None,
        to_rgb: bool = True,
        target_size: int = 224,
    ):
        """
        Parameters
        ----------
        images : (N, H, W) uint8 그레이스케일 또는 (N, H, W, 3) 컬러
        labels : (N,) — 0=정상, 1=비정상
        to_rgb : True이면 그레이스케일 → 3채널 변환 (ResNet 등)
        target_size : 리사이즈 크기
        """
        self.images = images
        self.labels = labels
        self.transform = transform
        self.to_rgb = to_rgb
        self.target_size = target_size

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        img = self.images[idx].copy()
        label = int(self.labels[idx])

        # 리사이즈
        if img.shape[0] != self.target_size or img.shape[1] != self.target_size:
            img = cv2.resize(img, (self.target_size, self.target_size))

        # 정규화 (0~1)
        img = img.astype(np.float32) / 255.0

        if self.to_rgb:
            if img.ndim == 2:
                img = np.stack([img] * 3, axis=0)  # (3, H, W)
            else:
                img = img.transpose(2, 0, 1)  # (3, H, W)

            # ImageNet 정규화
            mean = np.array([0.485, 0.456, 0.406]).reshape(3, 1, 1)
            std = np.array([0.229, 0.224, 0.225]).reshape(3, 1, 1)
            img = (img - mean) / std
        else:
            if img.ndim == 2:
                img = img[np.newaxis, ...]  # (1, H, W)

        img_tensor = torch.from_numpy(img).float()
        return img_tensor, label


class SeverstalDefect4Dataset(Dataset):
    """Severstal 4종 결함 분류 PyTorch Dataset.

    ClassId 1~4 → 내부 인덱스 0~3으로 변환.
    """

    CLASS_MAP = {1: 0, 2: 1, 3: 2, 4: 3}
    INV_CLASS_MAP = {0: 1, 1: 2, 2: 3, 3: 4}

    def __init__(
        self,
        images: np.ndarray,
        labels: np.ndarray,
        transform=None,
        to_rgb: bool = True,
        target_size: int = 224,
    ):
        self.images = images
        # ClassId 1~4 → 0~3
        self.labels = np.array([self.CLASS_MAP[l] for l in labels])
        self.original_labels = labels
        self.transform = transform
        self.to_rgb = to_rgb
        self.target_size = target_size

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        img = self.images[idx].copy()
        label = int(self.labels[idx])

        if img.shape[0] != self.target_size or img.shape[1] != self.target_size:
            img = cv2.resize(img, (self.target_size, self.target_size))

        img = img.astype(np.float32) / 255.0

        if self.to_rgb:
            if img.ndim == 2:
                img = np.stack([img] * 3, axis=0)
            else:
                img = img.transpose(2, 0, 1)
            mean = np.array([0.485, 0.456, 0.406]).reshape(3, 1, 1)
            std = np.array([0.229, 0.224, 0.225]).reshape(3, 1, 1)
            img = (img - mean) / std
        else:
            if img.ndim == 2:
                img = img[np.newaxis, ...]

        return torch.from_numpy(img).float(), label

    @staticmethod
    def idx_to_classid(idx: int) -> int:
        return SeverstalDefect4Dataset.INV_CLASS_MAP[idx]

    @staticmethod
    def idx_to_name(idx: int, lang: str = "kr") -> str:
        cid = SeverstalDefect4Dataset.INV_CLASS_MAP[idx]
        if lang == "kr":
            return CLASS_NAMES_KR[cid]
        return CLASS_NAMES_EN[cid]


# ──────────────────────────────────────────────
# DataLoader 생성 유틸리티
# ──────────────────────────────────────────────
def get_binary_dataloaders(
    patch_dir: str,
    max_per_class: int = 5000,
    batch_size: int = 32,
    test_size: float = 0.2,
    target_size: int = 224,
    to_rgb: bool = True,
    seed: int = 42,
    num_workers: int = 0,
) -> Tuple[DataLoader, DataLoader, List[str]]:
    """이진 분류 DataLoader 생성."""
    from utils.severstal_preprocessor import PatchDataLoader

    loader = PatchDataLoader(patch_dir)
    images, labels = loader.load_binary(
        max_per_class=max_per_class, resize=None, grayscale=True
    )

    X_train, X_test, y_train, y_test = train_test_split(
        images, labels, test_size=test_size, stratify=labels, random_state=seed
    )

    train_ds = SeverstalBinaryDataset(X_train, y_train, to_rgb=to_rgb, target_size=target_size)
    test_ds = SeverstalBinaryDataset(X_test, y_test, to_rgb=to_rgb, target_size=target_size)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=num_workers)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False, num_workers=num_workers)

    class_names = ["정상 (Normal)", "비정상 (Abnormal)"]

    print(f"[Binary DataLoaders]")
    print(f"  Train: {len(train_ds)} (정상 {(y_train==0).sum()} / 비정상 {(y_train==1).sum()})")
    print(f"  Test:  {len(test_ds)} (정상 {(y_test==0).sum()} / 비정상 {(y_test==1).sum()})")

    return train_loader, test_loader, class_names


def get_defect4_dataloaders(
    patch_dir: str,
    max_per_class: Optional[int] = None,
    batch_size: int = 32,
    test_size: float = 0.2,
    target_size: int = 224,
    to_rgb: bool = True,
    seed: int = 42,
    num_workers: int = 0,
) -> Tuple[DataLoader, DataLoader, List[str]]:
    """4종 결함 분류 DataLoader 생성."""
    from utils.severstal_preprocessor import PatchDataLoader

    loader = PatchDataLoader(patch_dir)
    images, labels = loader.load_defect4(
        max_per_class=max_per_class, resize=None, grayscale=True
    )

    X_train, X_test, y_train, y_test = train_test_split(
        images, labels, test_size=test_size, stratify=labels, random_state=seed
    )

    train_ds = SeverstalDefect4Dataset(X_train, y_train, to_rgb=to_rgb, target_size=target_size)
    test_ds = SeverstalDefect4Dataset(X_test, y_test, to_rgb=to_rgb, target_size=target_size)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=num_workers)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False, num_workers=num_workers)

    class_names = [f"{CLASS_ABBR[i]} ({CLASS_NAMES_KR[i]})" for i in [1, 2, 3, 4]]

    print(f"[Defect4 DataLoaders]")
    print(f"  Train: {len(train_ds)}")
    # labels are original (1-4), y_train too
    for cid in [1, 2, 3, 4]:
        cnt = (y_train == cid).sum()
        print(f"    {CLASS_ABBR[cid]}: {cnt}")
    print(f"  Test:  {len(test_ds)}")

    return train_loader, test_loader, class_names


# ──────────────────────────────────────────────
if __name__ == "__main__":
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    patch_dir = os.path.join(base, "data", "severstal_patches")

    print("=== 이진 분류 DataLoader 테스트 ===")
    train_loader, test_loader, names = get_binary_dataloaders(
        patch_dir, max_per_class=1000, batch_size=16
    )
    batch = next(iter(train_loader))
    print(f"  배치 shape: {batch[0].shape}, labels: {batch[1][:8]}")

    print("\n=== 4종 분류 DataLoader 테스트 ===")
    train_loader, test_loader, names = get_defect4_dataloaders(
        patch_dir, max_per_class=200, batch_size=16
    )
    batch = next(iter(train_loader))
    print(f"  배치 shape: {batch[0].shape}, labels: {batch[1][:8]}")
    print(f"  클래스 이름: {names}")

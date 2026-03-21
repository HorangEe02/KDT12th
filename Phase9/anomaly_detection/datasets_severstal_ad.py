"""
Severstal 이상탐지용 데이터셋

정상 패치만으로 학습하고, 테스트 시 정상+결함 패치를 사용.
- 학습: 정상 패치만 (One-Class Learning)
- 테스트: 정상 + 결함 혼합
"""

import os
import sys
import numpy as np
import cv2
import torch
from torch.utils.data import Dataset, DataLoader
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class SeverstalAnomalyDataset(Dataset):
    """이상탐지용 PyTorch Dataset.

    정상=0, 비정상=1.
    """

    def __init__(
        self,
        images: np.ndarray,
        labels: np.ndarray,
        image_size: int = 200,
        in_channels: int = 1,
    ):
        self.images = images
        self.labels = labels
        self.image_size = image_size
        self.in_channels = in_channels

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        img = self.images[idx].copy()
        label = int(self.labels[idx])

        # 리사이즈
        img = cv2.resize(img, (self.image_size, self.image_size))
        img = img.astype(np.float32) / 255.0

        if self.in_channels == 1:
            if img.ndim == 2:
                img = img[np.newaxis, ...]
            elif img.ndim == 3:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)[np.newaxis, ...]
        elif self.in_channels == 3:
            if img.ndim == 2:
                img = np.stack([img] * 3, axis=0)
            else:
                img = img.transpose(2, 0, 1)

        return torch.from_numpy(img).float(), label


def get_anomaly_dataloaders(
    patch_dir: str,
    train_normal: int = 5000,
    test_normal: int = 1000,
    test_defect: int = 1000,
    image_size: int = 200,
    in_channels: int = 1,
    batch_size: int = 32,
    seed: int = 42,
) -> Tuple[DataLoader, DataLoader]:
    """이상탐지 DataLoader 생성.

    Returns
    -------
    train_loader : 정상 이미지만
    test_loader : 정상 + 결함 혼합
    """
    from utils.severstal_preprocessor import PatchDataLoader

    rng = np.random.RandomState(seed)
    loader = PatchDataLoader(patch_dir)

    # 정상 이미지 로드
    normal_files = loader._list_files(loader.normal_dir)
    rng.shuffle(normal_files)

    train_files = normal_files[:train_normal]
    test_normal_files = normal_files[train_normal : train_normal + test_normal]

    # 학습 데이터 (정상만)
    train_images = []
    for f in train_files:
        img = cv2.imread(
            os.path.join(loader.normal_dir, f), cv2.IMREAD_GRAYSCALE
        )
        if img is not None:
            train_images.append(img)
    train_images = np.array(train_images)
    train_labels = np.zeros(len(train_images), dtype=np.int64)

    # 테스트 정상
    test_images = []
    test_labels = []
    for f in test_normal_files:
        img = cv2.imread(
            os.path.join(loader.normal_dir, f), cv2.IMREAD_GRAYSCALE
        )
        if img is not None:
            test_images.append(img)
            test_labels.append(0)

    # 테스트 결함
    defect_per_class = test_defect // 4
    for cid, d in loader.defect_dirs.items():
        files = loader._list_files(d)
        rng.shuffle(files)
        for f in files[:defect_per_class]:
            img = cv2.imread(os.path.join(d, f), cv2.IMREAD_GRAYSCALE)
            if img is not None:
                test_images.append(img)
                test_labels.append(1)

    test_images = np.array(test_images)
    test_labels = np.array(test_labels, dtype=np.int64)

    print(f"[Anomaly DataLoaders]")
    print(f"  Train (정상만): {len(train_images):,}장")
    print(f"  Test: {len(test_images):,}장 (정상 {(test_labels==0).sum()} / 결함 {(test_labels==1).sum()})")

    train_ds = SeverstalAnomalyDataset(
        train_images, train_labels, image_size=image_size, in_channels=in_channels
    )
    test_ds = SeverstalAnomalyDataset(
        test_images, test_labels, image_size=image_size, in_channels=in_channels
    )

    train_loader = DataLoader(
        train_ds, batch_size=batch_size, shuffle=True, num_workers=0
    )
    test_loader = DataLoader(
        test_ds, batch_size=batch_size, shuffle=False, num_workers=0
    )

    return train_loader, test_loader


if __name__ == "__main__":
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    patch_dir = os.path.join(base, "data", "severstal_patches")

    train_loader, test_loader = get_anomaly_dataloaders(
        patch_dir, train_normal=2000, test_normal=500, test_defect=500
    )

    batch = next(iter(train_loader))
    print(f"Train batch: shape={batch[0].shape}, labels={batch[1][:8]}")

    batch = next(iter(test_loader))
    print(f"Test batch: shape={batch[0].shape}, labels={batch[1][:8]}")

"""PyTorch 데이터셋 및 데이터로더.

NEU 데이터셋을 PyTorch Dataset/DataLoader로 래핑하여
딥러닝 학습에 사용할 수 있도록 한다.
"""

import os
import sys
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from torchvision import transforms
from typing import Optional, Callable

# 프로젝트 루트를 path에 추가
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from utils.data_loader import NEUDataLoader


class NEUTorchDataset(Dataset):
    """NEU 금속 표면 결함 데이터셋의 PyTorch Dataset 래퍼.

    Args:
        images: (N, 200, 200) uint8 numpy 배열.
        labels: (N,) int numpy 배열.
        transform: torchvision 변환 파이프라인.
        num_channels: 출력 채널 수 (1=CustomCNN용, 3=ResNet용).
    """

    def __init__(
        self,
        images: np.ndarray,
        labels: np.ndarray,
        transform: Optional[Callable] = None,
        num_channels: int = 3,
    ):
        self.images = images  # (N, 200, 200) uint8
        self.labels = labels  # (N,) int
        self.transform = transform
        self.num_channels = num_channels

    def __len__(self) -> int:
        return len(self.labels)

    def __getitem__(self, idx: int):
        image = self.images[idx]  # (200, 200) uint8
        label = int(self.labels[idx])

        # PIL-like 변환을 위해 (H, W) -> (H, W, C) 로 확장
        if self.num_channels == 3:
            # 그레이스케일 -> 3채널 반복
            image = np.stack([image, image, image], axis=-1)  # (200, 200, 3)
        else:
            # 1채널 유지: (200, 200, 1)
            image = image[:, :, np.newaxis]

        # PIL Image로 변환하지 않고 numpy -> tensor 변환
        if self.transform is not None:
            from PIL import Image
            # transforms가 PIL을 기대하므로 PIL 변환
            if self.num_channels == 3:
                pil_img = Image.fromarray(image, mode="RGB")
            else:
                pil_img = Image.fromarray(image.squeeze(), mode="L")
            image = self.transform(pil_img)
        else:
            # 수동 텐서 변환: (H, W, C) -> (C, H, W), [0, 255] -> [0, 1]
            image = image.transpose(2, 0, 1).astype(np.float32) / 255.0
            image = torch.from_numpy(image)

        label = torch.tensor(label, dtype=torch.long)
        return image, label


def get_dataloaders(
    data_dir: str,
    batch_size: int = 32,
    test_size: float = 0.2,
    transform_train: Optional[Callable] = None,
    transform_test: Optional[Callable] = None,
    num_channels: int = 3,
    random_state: int = 42,
    num_workers: int = 0,
) -> tuple:
    """NEU 데이터셋을 로드하여 train/test DataLoader를 반환.

    Args:
        data_dir: NEU-DET 데이터 디렉토리 경로.
        batch_size: 배치 크기.
        test_size: 테스트 세트 비율 (0~1).
        transform_train: 학습용 변환 파이프라인.
        transform_test: 테스트용 변환 파이프라인.
        num_channels: 출력 채널 수 (1 또는 3).
        random_state: 랜덤 시드.
        num_workers: DataLoader 워커 수.

    Returns:
        (train_loader, test_loader, class_names) 튜플.
    """
    loader = NEUDataLoader(data_dir)
    images, labels, class_names = loader.load_all_images()

    # Stratified train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        images, labels,
        test_size=test_size,
        random_state=random_state,
        stratify=labels,
    )

    print(f"[DataLoader] Train: {len(X_train)}장, Test: {len(X_test)}장")
    print(f"[DataLoader] 채널 수: {num_channels}, 배치 크기: {batch_size}")

    train_dataset = NEUTorchDataset(
        X_train, y_train,
        transform=transform_train,
        num_channels=num_channels,
    )
    test_dataset = NEUTorchDataset(
        X_test, y_test,
        transform=transform_test,
        num_channels=num_channels,
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=True,
        drop_last=False,
    )
    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True,
        drop_last=False,
    )

    return train_loader, test_loader, class_names


if __name__ == "__main__":
    print("=" * 60)
    print("NEUTorchDataset 스모크 테스트")
    print("=" * 60)

    # 더미 데이터로 테스트
    dummy_images = np.random.randint(0, 255, (60, 200, 200), dtype=np.uint8)
    dummy_labels = np.array([i % 6 for i in range(60)], dtype=np.int32)

    # 3채널 테스트 (ResNet용)
    ds3 = NEUTorchDataset(dummy_images, dummy_labels, num_channels=3)
    img, lbl = ds3[0]
    print(f"3채널 출력 shape: {img.shape}, label: {lbl.item()}")
    assert img.shape == (3, 200, 200), f"Expected (3,200,200), got {img.shape}"

    # 1채널 테스트 (CustomCNN용)
    ds1 = NEUTorchDataset(dummy_images, dummy_labels, num_channels=1)
    img, lbl = ds1[0]
    print(f"1채널 출력 shape: {img.shape}, label: {lbl.item()}")
    assert img.shape == (1, 200, 200), f"Expected (1,200,200), got {img.shape}"

    # transforms 적용 테스트
    tf = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    ds_tf = NEUTorchDataset(dummy_images, dummy_labels, transform=tf, num_channels=3)
    img, lbl = ds_tf[0]
    print(f"Transform 적용 shape: {img.shape}, dtype: {img.dtype}")
    assert img.shape == (3, 224, 224), f"Expected (3,224,224), got {img.shape}"

    # DataLoader 래핑 테스트
    from torch.utils.data import DataLoader
    dl = DataLoader(ds3, batch_size=8, shuffle=True)
    batch_imgs, batch_lbls = next(iter(dl))
    print(f"배치 shape: images={batch_imgs.shape}, labels={batch_lbls.shape}")

    print("\ndatasets.py 스모크 테스트 완료")

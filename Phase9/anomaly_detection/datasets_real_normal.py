"""
진짜 정상 데이터 기반 이상 탐지 데이터셋

이전: pitted_surface를 pseudo-normal로 사용 (부정확)
현재: NEU bbox에서 크롭한 결함-없는 패치를 정상 데이터로 사용 (정확)

구성:
  - 학습 셋: 정상 패치만 (크롭된 깨끗한 영역)
  - 테스트 셋: 정상 패치 일부 + NEU 결함 이미지 전체 6종
"""

import os
import cv2
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from typing import Tuple, Optional

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from anomaly_detection.datasets_normal_patches import NormalDataManager
from utils.data_loader import NEUDataLoader


class RealNormalAnomalyDataset(Dataset):
    """
    진짜 정상/결함 이상 탐지 데이터셋

    label: 0 = 정상 (결함 없는 금속 표면)
    label: 1 = 이상 (6종 결함 중 하나)
    """

    def __init__(self, images: list, labels: list, defect_types: list = None,
                 image_size: int = 200, transform=None):
        self.images = images
        self.labels = labels
        self.defect_types = defect_types or ["unknown"] * len(images)
        self.image_size = image_size
        self.transform = transform

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        img = self.images[idx]
        label = self.labels[idx]

        if img.shape[:2] != (self.image_size, self.image_size):
            img = cv2.resize(img, (self.image_size, self.image_size))

        img_tensor = torch.FloatTensor(img).unsqueeze(0) / 255.0

        if self.transform:
            img_tensor = self.transform(img_tensor)

        return img_tensor, label

    def get_defect_type(self, idx):
        return self.defect_types[idx]


def get_real_normal_dataloaders(
    data_dir: str,
    normal_dir: str = None,
    batch_size: int = 16,
    image_size: int = 200,
    test_normal_ratio: float = 0.2,
    max_normal_train: int = 300,
    max_defect_test: int = 50,
) -> Tuple[DataLoader, DataLoader, dict]:
    """
    진짜 정상 데이터 기반 DataLoader 생성

    Args:
        data_dir: NEU-DET 경로
        normal_dir: 정상 패치 경로
        batch_size: 배치 크기
        test_normal_ratio: 테스트에 사용할 정상 비율
        max_normal_train: 학습용 정상 이미지 최대 수
        max_defect_test: 클래스당 테스트용 결함 이미지 최대 수

    Returns:
        (train_loader, test_loader, info_dict)
    """
    # 1. 정상 데이터 로드
    if normal_dir is None:
        normal_dir = os.path.join(os.path.dirname(data_dir), "normal_patches")

    mgr = NormalDataManager(data_dir, normal_dir)
    mgr.prepare()

    all_normals = mgr.load_normal_images(max_images=1200)
    np.random.seed(42)
    np.random.shuffle(all_normals)

    # Train/Test 분할
    n_test = int(len(all_normals) * test_normal_ratio)
    n_test = min(n_test, 100)  # 테스트 정상 최대 100장
    n_train = min(len(all_normals) - n_test, max_normal_train)

    normal_train = all_normals[:n_train]
    normal_test = all_normals[n_train:n_train + n_test]

    # 2. 결함 데이터 로드 (테스트용)
    loader = NEUDataLoader(data_dir)
    defect_images, defect_labels, class_names = loader.load_all_images()

    # 클래스당 최대 수 제한
    test_defects = []
    test_defect_types = []
    for cls_idx, cls_name in enumerate(class_names):
        cls_mask = defect_labels == cls_idx
        cls_imgs = defect_images[cls_mask]
        n_use = min(len(cls_imgs), max_defect_test)
        for i in range(n_use):
            test_defects.append(cls_imgs[i])
            test_defect_types.append(cls_name)

    # 3. 학습 셋 구성 (정상만)
    train_images = list(normal_train)
    train_labels = [0] * len(train_images)
    train_types = ["normal"] * len(train_images)

    # 4. 테스트 셋 구성 (정상 + 결함)
    test_images = list(normal_test) + test_defects
    test_labels = [0] * len(normal_test) + [1] * len(test_defects)
    test_types = ["normal"] * len(normal_test) + test_defect_types

    train_dataset = RealNormalAnomalyDataset(
        train_images, train_labels, train_types, image_size
    )
    test_dataset = RealNormalAnomalyDataset(
        test_images, test_labels, test_types, image_size
    )

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    info = {
        "train_normal": len(normal_train),
        "test_normal": len(normal_test),
        "test_defect": len(test_defects),
        "test_total": len(test_images),
        "class_names": class_names,
        "defect_distribution": {},
    }
    for t in test_defect_types:
        info["defect_distribution"][t] = info["defect_distribution"].get(t, 0) + 1

    return train_loader, test_loader, info


if __name__ == "__main__":
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "NEU-DET")
    train_loader, test_loader, info = get_real_normal_dataloaders(DATA_DIR)

    print("=== 진짜 정상 데이터 기반 이상 탐지 데이터셋 ===")
    print(f"학습: {info['train_normal']}장 (정상만)")
    print(f"테스트: {info['test_normal']}장 (정상) + {info['test_defect']}장 (결함)")
    print(f"테스트 결함 분포:")
    for cls, cnt in sorted(info["defect_distribution"].items()):
        print(f"  {cls}: {cnt}장")

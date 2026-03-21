"""NEU 데이터셋을 이상 탐지(Anomaly Detection) 형태로 래핑하는 모듈.

하나의 클래스를 '정상(normal)'으로, 나머지를 '이상(anomaly)'으로 분류하여
이상 탐지 실험을 수행할 수 있도록 한다.
기본 정상 클래스: pitted_surface (외관이 가장 일관성 있음).
"""

import os
import glob
from typing import Optional, Tuple

import numpy as np
import cv2
import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from sklearn.model_selection import train_test_split


NEU_CLASSES = [
    "crazing", "inclusion", "patches",
    "pitted_surface", "rolled-in_scale", "scratches",
]


class NEUAnomalyDataset(Dataset):
    """NEU 데이터셋을 이상 탐지용으로 래핑.

    Args:
        image_paths: 이미지 파일 경로 리스트.
        labels: 라벨 리스트 (0=정상, 1=이상).
        original_classes: 원래 클래스명 리스트.
        image_size: 리사이즈 크기 (정방). None이면 원본(200) 유지.
        transform: 추가 torchvision transform.
    """

    def __init__(
        self,
        image_paths: list,
        labels: list,
        original_classes: list,
        image_size: Optional[int] = None,
        transform: Optional[transforms.Compose] = None,
    ) -> None:
        self.image_paths = image_paths
        self.labels = labels
        self.original_classes = original_classes
        self.image_size = image_size

        if transform is not None:
            self.transform = transform
        else:
            t_list = []
            if image_size is not None:
                t_list.append(transforms.Resize((image_size, image_size)))
            t_list.append(transforms.ToTensor())
            self.transform = transforms.Compose(t_list)

    def __len__(self) -> int:
        return len(self.image_paths)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int, str]:
        """
        Returns:
            (image_tensor, label, original_class_name)
            - image_tensor: (1, H, W) float32 (그레이스케일)
            - label: 0=정상, 1=이상
            - original_class_name: 원래 NEU 클래스명
        """
        img_path = self.image_paths[idx]
        label = self.labels[idx]
        orig_class = self.original_classes[idx]

        # 그레이스케일 로드
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise FileNotFoundError(f"이미지 로드 실패: {img_path}")

        # PIL Image로 변환 (torchvision transform 호환)
        from PIL import Image
        img_pil = Image.fromarray(img)
        img_tensor = self.transform(img_pil)

        return img_tensor, label, orig_class


def _collect_neu_paths(
    data_dir: str,
    normal_class: str = "pitted_surface",
) -> Tuple[list, list, list]:
    """NEU 이미지 경로와 이상 탐지 라벨을 수집한다.

    Args:
        data_dir: NEU-DET 루트 디렉토리 (train/images/ 하위에 클래스 폴더 존재).
        normal_class: 정상으로 간주할 클래스.

    Returns:
        (image_paths, labels, original_classes) 튜플.
    """
    if normal_class not in NEU_CLASSES:
        raise ValueError(f"알 수 없는 클래스: {normal_class}. 가능: {NEU_CLASSES}")

    image_dir = os.path.join(data_dir, "train", "images")
    if not os.path.isdir(image_dir):
        # flat 구조 시도
        image_dir = data_dir

    image_paths = []
    labels = []
    original_classes = []
    exts = ("*.jpg", "*.jpeg", "*.bmp", "*.png")

    for cls_name in NEU_CLASSES:
        cls_dir = os.path.join(image_dir, cls_name)
        if not os.path.isdir(cls_dir):
            continue

        paths = []
        for ext in exts:
            paths.extend(glob.glob(os.path.join(cls_dir, ext)))
        paths = sorted(paths)

        is_normal = (cls_name == normal_class)
        for p in paths:
            image_paths.append(p)
            labels.append(0 if is_normal else 1)
            original_classes.append(cls_name)

    if not image_paths:
        raise FileNotFoundError(f"이미지를 찾을 수 없습니다: {image_dir}")

    n_normal = labels.count(0)
    n_anomaly = labels.count(1)
    print(f"[NEU Anomaly] 정상 클래스: {normal_class}")
    print(f"[NEU Anomaly] 정상: {n_normal}장, 이상: {n_anomaly}장")

    return image_paths, labels, original_classes


def get_neu_anomaly_dataloaders(
    data_dir: str,
    normal_class: str = "pitted_surface",
    batch_size: int = 16,
    image_size: Optional[int] = None,
    test_size: float = 0.3,
    random_state: int = 42,
    num_workers: int = 0,
) -> Tuple[DataLoader, DataLoader]:
    """NEU 이상 탐지용 DataLoader를 반환한다.

    - train_loader: 정상(normal) 이미지만 포함 (오토인코더 학습용).
    - test_loader: 정상 + 이상 이미지 혼합 (평가용).

    Args:
        data_dir: NEU-DET 루트 디렉토리.
        normal_class: 정상으로 간주할 클래스.
        batch_size: 배치 크기.
        image_size: 리사이즈 크기. None이면 200 유지.
        test_size: 정상 이미지 중 테스트에 사용할 비율.
        random_state: 랜덤 시드.
        num_workers: DataLoader worker 수.

    Returns:
        (train_loader_normal_only, test_loader_mixed) 튜플.
    """
    image_paths, labels, original_classes = _collect_neu_paths(data_dir, normal_class)

    # 정상 / 이상 분리
    normal_paths, normal_classes = [], []
    anomaly_paths, anomaly_labels, anomaly_classes = [], [], []

    for p, lbl, cls in zip(image_paths, labels, original_classes):
        if lbl == 0:
            normal_paths.append(p)
            normal_classes.append(cls)
        else:
            anomaly_paths.append(p)
            anomaly_labels.append(1)
            anomaly_classes.append(cls)

    # 정상 이미지를 train/test 분할
    norm_train_paths, norm_test_paths, norm_train_cls, norm_test_cls = train_test_split(
        normal_paths, normal_classes,
        test_size=test_size,
        random_state=random_state,
    )

    # Train: 정상만
    train_labels = [0] * len(norm_train_paths)

    # Test: 정상 test + 전체 이상
    test_paths = norm_test_paths + anomaly_paths
    test_labels = [0] * len(norm_test_paths) + anomaly_labels
    test_classes = norm_test_cls + anomaly_classes

    print(f"[NEU Anomaly] Train (정상만): {len(norm_train_paths)}장")
    print(f"[NEU Anomaly] Test (혼합): 정상 {len(norm_test_paths)}장 + 이상 {len(anomaly_paths)}장 = {len(test_paths)}장")

    # Dataset 생성
    train_dataset = NEUAnomalyDataset(
        norm_train_paths, train_labels, norm_train_cls,
        image_size=image_size,
    )
    test_dataset = NEUAnomalyDataset(
        test_paths, test_labels, test_classes,
        image_size=image_size,
    )

    def _collate_fn(batch):
        images = torch.stack([item[0] for item in batch])
        labels_t = torch.tensor([item[1] for item in batch], dtype=torch.long)
        classes = [item[2] for item in batch]
        return images, labels_t, classes

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        collate_fn=_collate_fn,
        pin_memory=True,
    )
    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        collate_fn=_collate_fn,
        pin_memory=True,
    )

    return train_loader, test_loader


# ---------------------------------------------------------------------------
# 스모크 테스트
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("NEU Anomaly Dataset 스모크 테스트")
    print("=" * 60)

    # 프로젝트 루트 기준 데이터 경로
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(project_root, "data", "NEU-DET")

    if not os.path.isdir(data_dir):
        print(f"[SKIP] 데이터 경로가 없습니다: {data_dir}")
        print("[INFO] 더미 데이터로 테스트합니다.")

        # 더미 데이터 생성
        import tempfile
        import shutil
        data_dir = tempfile.mkdtemp()
        img_dir = os.path.join(data_dir, "train", "images")
        for cls in NEU_CLASSES:
            cls_dir = os.path.join(img_dir, cls)
            os.makedirs(cls_dir, exist_ok=True)
            for i in range(10):
                dummy = np.random.randint(0, 255, (200, 200), dtype=np.uint8)
                cv2.imwrite(os.path.join(cls_dir, f"{i:03d}.bmp"), dummy)

        try:
            train_loader, test_loader = get_neu_anomaly_dataloaders(
                data_dir, normal_class="pitted_surface", batch_size=8,
            )
            for imgs, lbls, classes in train_loader:
                print(f"\nTrain batch - images: {imgs.shape}, labels: {lbls}, unique labels: {lbls.unique()}")
                break
            for imgs, lbls, classes in test_loader:
                print(f"Test batch - images: {imgs.shape}, labels: {lbls}, unique labels: {lbls.unique()}")
                break
            print("\n[PASS] 더미 데이터 테스트 완료")
        finally:
            shutil.rmtree(data_dir, ignore_errors=True)
    else:
        train_loader, test_loader = get_neu_anomaly_dataloaders(
            data_dir, normal_class="pitted_surface", batch_size=16,
        )
        for imgs, lbls, classes in train_loader:
            print(f"\nTrain batch - images: {imgs.shape}, labels: {lbls.tolist()[:5]}...")
            break
        for imgs, lbls, classes in test_loader:
            print(f"Test batch - images: {imgs.shape}, labels: {lbls.tolist()[:8]}...")
            print(f"  classes: {classes[:8]}")
            break
        print("\n[PASS] NEU Anomaly Dataset 테스트 완료")

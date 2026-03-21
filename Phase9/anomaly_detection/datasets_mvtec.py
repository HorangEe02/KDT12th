"""MVTec AD Metal Nut 데이터셋 로더.

MVTec Anomaly Detection 데이터셋의 metal_nut 카테고리를 다운로드하고
PyTorch Dataset/DataLoader로 제공한다.
- Training: 정상(good) 이미지만 사용
- Testing: 정상 + 결함(bent, color, flip, scratch) 이미지 사용
"""

import os
import tarfile
import urllib.request
from typing import Optional, Tuple

import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image
import glob


# ---------------------------------------------------------------------------
# MVTec AD metal_nut 다운로드
# ---------------------------------------------------------------------------

MVTEC_URL = "https://www.mydrive.ch/shares/38536/3830184030e49fe74747669442f0f282/download/420938166-1629953099/metal_nut.tar.xz"
MVTEC_MIRROR_URL = "ftp://guest:GU.205" "dldo@ftp.softronics.ch/mvtec_anomaly_detection/metal_nut.tar.xz"


def download_mvtec_metal_nut(data_dir: str = "data/MVTec-AD") -> str:
    """MVTec AD metal_nut 카테고리를 다운로드한다.

    이미 존재하면 다운로드를 건너뛴다.

    Args:
        data_dir: 데이터를 저장할 상위 디렉토리.

    Returns:
        metal_nut 데이터 경로 (예: data/MVTec-AD/metal_nut).
    """
    metal_nut_dir = os.path.join(data_dir, "metal_nut")

    # 이미 존재하면 스킵
    if os.path.isdir(metal_nut_dir):
        train_dir = os.path.join(metal_nut_dir, "train", "good")
        if os.path.isdir(train_dir) and len(os.listdir(train_dir)) > 0:
            print(f"[MVTec] 이미 존재합니다: {metal_nut_dir}")
            return metal_nut_dir

    os.makedirs(data_dir, exist_ok=True)
    tar_path = os.path.join(data_dir, "metal_nut.tar.xz")

    # 다운로드
    if not os.path.isfile(tar_path):
        print(f"[MVTec] metal_nut 다운로드 시작...")
        print(f"[MVTec] URL: {MVTEC_URL}")
        try:
            urllib.request.urlretrieve(MVTEC_URL, tar_path, _download_progress)
            print()
        except Exception as e:
            print(f"\n[MVTec] 기본 URL 다운로드 실패: {e}")
            print(f"[MVTec] 수동 다운로드가 필요할 수 있습니다.")
            print(f"[MVTec] 1) https://www.mvtec.com/company/research/datasets/mvtec-ad 에서 다운로드")
            print(f"[MVTec] 2) metal_nut 폴더를 {data_dir}/ 에 배치하세요.")
            raise FileNotFoundError(
                f"MVTec AD metal_nut 다운로드 실패. 수동으로 {metal_nut_dir}에 배치하세요."
            ) from e

    # 압축 해제
    print(f"[MVTec] 압축 해제 중: {tar_path}")
    with tarfile.open(tar_path, "r:xz") as tar:
        tar.extractall(path=data_dir)
    print(f"[MVTec] 압축 해제 완료: {metal_nut_dir}")

    # tar 파일 삭제 (옵션)
    if os.path.isfile(tar_path):
        os.remove(tar_path)
        print(f"[MVTec] 임시 파일 삭제: {tar_path}")

    return metal_nut_dir


def _download_progress(block_num: int, block_size: int, total_size: int) -> None:
    """다운로드 진행 콜백."""
    downloaded = block_num * block_size
    if total_size > 0:
        pct = min(100, downloaded * 100 // total_size)
        mb_down = downloaded / (1024 * 1024)
        mb_total = total_size / (1024 * 1024)
        print(f"\r  [{pct:3d}%] {mb_down:.1f}/{mb_total:.1f} MB", end="", flush=True)
    else:
        mb_down = downloaded / (1024 * 1024)
        print(f"\r  {mb_down:.1f} MB downloaded", end="", flush=True)


# ---------------------------------------------------------------------------
# MVTec Metal Nut PyTorch Dataset
# ---------------------------------------------------------------------------

DEFECT_TYPES = ["bent", "color", "flip", "scratch"]


class MVTecMetalNutDataset(Dataset):
    """MVTec AD metal_nut 데이터셋.

    Args:
        data_dir: metal_nut 루트 디렉토리 경로.
        split: "train" 또는 "test".
        image_size: 리사이즈할 이미지 크기.
        transform: 추가 torchvision transform (None이면 기본 transform 사용).
    """

    def __init__(
        self,
        data_dir: str,
        split: str = "train",
        image_size: int = 256,
        transform: Optional[transforms.Compose] = None,
    ) -> None:
        assert split in ("train", "test"), f"split은 'train' 또는 'test'여야 합니다: {split}"

        self.data_dir = data_dir
        self.split = split
        self.image_size = image_size

        if transform is not None:
            self.transform = transform
        else:
            self.transform = transforms.Compose([
                transforms.Resize((image_size, image_size)),
                transforms.ToTensor(),
            ])

        self.mask_transform = transforms.Compose([
            transforms.Resize((image_size, image_size), interpolation=transforms.InterpolationMode.NEAREST),
            transforms.ToTensor(),
        ])

        # 이미지 경로 및 라벨 수집
        self.image_paths: list[str] = []
        self.labels: list[int] = []        # 0=정상, 1=결함
        self.defect_types: list[str] = []  # "good", "bent", "color", ...
        self.mask_paths: list[Optional[str]] = []

        split_dir = os.path.join(data_dir, split)
        gt_dir = os.path.join(data_dir, "ground_truth")

        if not os.path.isdir(split_dir):
            raise FileNotFoundError(f"디렉토리를 찾을 수 없습니다: {split_dir}")

        # 정상 이미지 로드
        good_dir = os.path.join(split_dir, "good")
        if os.path.isdir(good_dir):
            good_paths = sorted(glob.glob(os.path.join(good_dir, "*.png")))
            for p in good_paths:
                self.image_paths.append(p)
                self.labels.append(0)
                self.defect_types.append("good")
                self.mask_paths.append(None)

        # 테스트 시 결함 이미지도 로드
        if split == "test":
            for defect in DEFECT_TYPES:
                defect_dir = os.path.join(split_dir, defect)
                if not os.path.isdir(defect_dir):
                    continue
                defect_paths = sorted(glob.glob(os.path.join(defect_dir, "*.png")))
                for p in defect_paths:
                    self.image_paths.append(p)
                    self.labels.append(1)
                    self.defect_types.append(defect)

                    # 대응하는 마스크 찾기
                    fname = os.path.basename(p)
                    mask_name = fname.replace(".png", "_mask.png")
                    mask_path = os.path.join(gt_dir, defect, mask_name)
                    if os.path.isfile(mask_path):
                        self.mask_paths.append(mask_path)
                    else:
                        self.mask_paths.append(None)

        print(f"[MVTecMetalNutDataset] split={split}, 총 {len(self)} 이미지 로드")
        if split == "test":
            n_good = self.labels.count(0)
            n_defect = self.labels.count(1)
            print(f"  정상: {n_good}, 결함: {n_defect}")

    def __len__(self) -> int:
        return len(self.image_paths)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int, Optional[torch.Tensor], str]:
        """
        Returns:
            (image_tensor, label, mask_tensor_or_None, defect_type_str)
        """
        img_path = self.image_paths[idx]
        label = self.labels[idx]
        defect_type = self.defect_types[idx]

        # 이미지 로드
        image = Image.open(img_path).convert("RGB")
        image_tensor = self.transform(image)

        # 마스크 로드
        mask_tensor = None
        mask_path = self.mask_paths[idx]
        if mask_path is not None and os.path.isfile(mask_path):
            mask = Image.open(mask_path).convert("L")
            mask_tensor = self.mask_transform(mask)
            mask_tensor = (mask_tensor > 0.5).float()

        return image_tensor, label, mask_tensor, defect_type


def get_mvtec_dataloaders(
    data_dir: str,
    batch_size: int = 16,
    image_size: int = 256,
    num_workers: int = 0,
) -> Tuple[DataLoader, DataLoader]:
    """MVTec metal_nut train/test DataLoader를 반환한다.

    Args:
        data_dir: metal_nut 루트 디렉토리 경로.
        batch_size: 배치 크기.
        image_size: 이미지 리사이즈 크기.
        num_workers: DataLoader worker 수.

    Returns:
        (train_loader, test_loader) 튜플.
    """
    def _collate_fn(batch):
        """mask가 None인 경우를 처리하는 커스텀 collate 함수."""
        images = torch.stack([item[0] for item in batch])
        labels = torch.tensor([item[1] for item in batch], dtype=torch.long)
        masks = [item[2] for item in batch]
        defect_types = [item[3] for item in batch]

        # 마스크: None이 있으면 리스트로 유지
        has_masks = any(m is not None for m in masks)
        if has_masks:
            # None을 0 텐서로 대체
            h, w = image_size, image_size
            processed_masks = []
            for m in masks:
                if m is not None:
                    processed_masks.append(m)
                else:
                    processed_masks.append(torch.zeros(1, h, w))
            masks_tensor = torch.stack(processed_masks)
        else:
            masks_tensor = None

        return images, labels, masks_tensor, defect_types

    train_dataset = MVTecMetalNutDataset(data_dir, split="train", image_size=image_size)
    test_dataset = MVTecMetalNutDataset(data_dir, split="test", image_size=image_size)

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
    import sys

    print("=" * 60)
    print("MVTec Metal Nut Dataset 스모크 테스트")
    print("=" * 60)

    # 더미 디렉토리 구조 생성으로 테스트
    test_dir = "/tmp/mvtec_test/metal_nut"
    for sub in ["train/good", "test/good", "test/bent", "test/scratch"]:
        os.makedirs(os.path.join(test_dir, sub), exist_ok=True)

    # 더미 이미지 생성
    dummy_img = Image.fromarray(np.random.randint(0, 255, (300, 300, 3), dtype=np.uint8))
    for i in range(5):
        dummy_img.save(os.path.join(test_dir, "train", "good", f"{i:03d}.png"))
        dummy_img.save(os.path.join(test_dir, "test", "good", f"{i:03d}.png"))
    for i in range(3):
        dummy_img.save(os.path.join(test_dir, "test", "bent", f"{i:03d}.png"))
        dummy_img.save(os.path.join(test_dir, "test", "scratch", f"{i:03d}.png"))

    # Dataset 테스트
    train_ds = MVTecMetalNutDataset(test_dir, split="train", image_size=256)
    test_ds = MVTecMetalNutDataset(test_dir, split="test", image_size=256)

    print(f"\nTrain 크기: {len(train_ds)}")
    print(f"Test 크기: {len(test_ds)}")

    # 아이템 접근 테스트
    img, lbl, mask, dtype = train_ds[0]
    print(f"\nTrain 샘플 - image: {img.shape}, label: {lbl}, mask: {mask}, defect: {dtype}")

    img, lbl, mask, dtype = test_ds[len(test_ds) - 1]
    print(f"Test 샘플 - image: {img.shape}, label: {lbl}, mask: {mask}, defect: {dtype}")

    # DataLoader 테스트
    train_loader, test_loader = get_mvtec_dataloaders(test_dir, batch_size=4, image_size=256)
    for batch in train_loader:
        imgs, lbls, masks, dtypes = batch
        print(f"\nTrain batch - images: {imgs.shape}, labels: {lbls.shape}")
        break
    for batch in test_loader:
        imgs, lbls, masks, dtypes = batch
        print(f"Test batch - images: {imgs.shape}, labels: {lbls.shape}, masks: {masks.shape if masks is not None else None}")
        break

    # 정리
    import shutil
    shutil.rmtree("/tmp/mvtec_test", ignore_errors=True)

    print("\n[PASS] MVTec Metal Nut Dataset 스모크 테스트 완료")

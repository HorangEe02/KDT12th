"""
Severstal 이미지 전처리기

256×1600 와이드 스트립 이미지를 256×256 패치로 크롭하고,
결함 마스크와 교차 검증하여 정상/결함 패치를 분류 저장.

슬라이딩 윈도우 방식 (v6.0):
  - 윈도우 크기: 256×256
  - 스트라이드: 128 (50% 오버랩)
  - 이미지당 최대 12개 패치 (정규 11 + 끝단 정렬 1)
  - 패치 경계에 걸친 결함까지 포착하는 오버랩 전략
  - 결함 마스크 교차 → 결함 포함 패치 = 해당 ClassId, 미포함 = normal
"""

import os
import sys
import numpy as np
import cv2
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

# 상위 디렉토리 import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.severstal_loader import SeverstalDataLoader, rle_to_mask


class SeverstalPreprocessor:
    """256×1600 → 256×256 패치 크롭 및 분류 (50% 오버랩)."""

    PATCH_SIZE = 256
    STRIDE = 128  # v6.0: 50% 오버랩 (경계 결함 포착)
    MIN_DEFECT_RATIO = 0.01  # 패치 내 결함 면적 최소 1%

    def __init__(self, loader: SeverstalDataLoader, output_dir: str):
        self.loader = loader
        self.output_dir = output_dir

        self.normal_dir = os.path.join(output_dir, "normal")
        self.defect_dirs = {
            1: os.path.join(output_dir, "defect", "class_1_PS"),
            2: os.path.join(output_dir, "defect", "class_2_LS"),
            3: os.path.join(output_dir, "defect", "class_3_SS"),
            4: os.path.join(output_dir, "defect", "class_4_RD"),
        }

        # 디렉토리 생성
        os.makedirs(self.normal_dir, exist_ok=True)
        for d in self.defect_dirs.values():
            os.makedirs(d, exist_ok=True)

    def _crop_patches(self, image: np.ndarray) -> List[np.ndarray]:
        """256×1600 → 256×256 패치 리스트 (오버랩 + 끝단 정렬)."""
        h, w = image.shape[:2]
        patches = []
        for x_start in range(0, w - self.PATCH_SIZE + 1, self.STRIDE):
            patch = image[:, x_start : x_start + self.PATCH_SIZE]
            patches.append(patch)

        # 끝단 정렬 패치: 마지막 정규 패치가 이미지 끝에 도달하지 못하면 추가
        last_regular_end = (len(patches) - 1) * self.STRIDE + self.PATCH_SIZE if patches else 0
        if w > last_regular_end:
            x_end_align = w - self.PATCH_SIZE
            patch = image[:, x_end_align : x_end_align + self.PATCH_SIZE]
            patches.append(patch)

        return patches

    def _crop_mask_patches(self, mask: np.ndarray) -> List[np.ndarray]:
        """마스크도 동일하게 크롭."""
        return self._crop_patches(mask)

    def _get_patch_class(
        self, mask_patches: Dict[int, List[np.ndarray]], patch_idx: int
    ) -> int:
        """패치의 대표 결함 클래스 결정.

        결함 면적이 MIN_DEFECT_RATIO 이상인 클래스 중 가장 큰 면적.
        없으면 0 (정상).
        """
        max_area = 0
        best_class = 0
        total_pixels = self.PATCH_SIZE * self.PATCH_SIZE

        for cid, patches in mask_patches.items():
            if patch_idx < len(patches):
                area = patches[patch_idx].sum()
                ratio = area / total_pixels
                if ratio >= self.MIN_DEFECT_RATIO and area > max_area:
                    max_area = area
                    best_class = cid

        return best_class

    def process_single_image(
        self, image_id: str, grayscale: bool = True
    ) -> Dict[int, int]:
        """단일 이미지 → 패치 크롭 및 저장.

        Returns
        -------
        class_counts : {class_id: count} 저장된 패치 수
        """
        img = self.loader.load_image(image_id, grayscale=grayscale)
        if img is None:
            return {}

        patches = self._crop_patches(img)

        # 결함 마스크 크롭
        masks = self.loader.get_defect_masks(image_id)
        mask_patches = {}
        for cid, mask in masks.items():
            mask_patches[cid] = self._crop_mask_patches(mask)

        base_name = os.path.splitext(image_id)[0]
        class_counts = defaultdict(int)

        for i, patch in enumerate(patches):
            if masks:
                patch_class = self._get_patch_class(mask_patches, i)
            else:
                patch_class = 0  # 정상 이미지의 모든 패치는 정상

            # 저장
            if patch_class == 0:
                save_dir = self.normal_dir
            else:
                save_dir = self.defect_dirs[patch_class]

            filename = f"{base_name}_p{i}.jpg"
            cv2.imwrite(os.path.join(save_dir, filename), patch)
            class_counts[patch_class] += 1

        return dict(class_counts)

    def process_all(
        self,
        max_images: Optional[int] = None,
        grayscale: bool = True,
        verbose: bool = True,
    ) -> Dict[int, int]:
        """전체 이미지 처리.

        Parameters
        ----------
        max_images : 처리할 최대 이미지 수 (None=전체)
        grayscale : 그레이스케일로 저장
        verbose : 진행 상황 출력

        Returns
        -------
        total_counts : {class_id: total_patch_count}
        """
        all_ids = self.loader.all_image_files
        if max_images:
            all_ids = all_ids[:max_images]

        total_counts = defaultdict(int)
        n = len(all_ids)

        for idx, img_id in enumerate(all_ids):
            counts = self.process_single_image(img_id, grayscale=grayscale)
            for cid, cnt in counts.items():
                total_counts[cid] += cnt

            if verbose and (idx + 1) % 500 == 0:
                print(f"  [{idx+1}/{n}] 처리 중... 현재 패치 수: {dict(total_counts)}")

        if verbose:
            print(f"\n[완료] 총 {n}장 처리")
            print(f"  정상 패치: {total_counts.get(0, 0):,}장")
            for cid in [1, 2, 3, 4]:
                name = self.loader.get_class_name(cid)
                print(f"  ClassId {cid} ({name}): {total_counts.get(cid, 0):,}장")

        return dict(total_counts)

    def get_patch_stats(self) -> Dict:
        """저장된 패치 통계."""
        stats = {}

        # 정상 패치 수
        if os.path.exists(self.normal_dir):
            normal_files = [
                f for f in os.listdir(self.normal_dir) if f.endswith(".jpg")
            ]
            stats[0] = len(normal_files)

        # 결함 패치 수
        for cid, d in self.defect_dirs.items():
            if os.path.exists(d):
                defect_files = [f for f in os.listdir(d) if f.endswith(".jpg")]
                stats[cid] = len(defect_files)

        return stats


class PatchDataLoader:
    """크롭된 패치를 로드하는 데이터 로더."""

    def __init__(self, patch_dir: str):
        self.patch_dir = patch_dir
        self.normal_dir = os.path.join(patch_dir, "normal")
        self.defect_dirs = {
            1: os.path.join(patch_dir, "defect", "class_1_PS"),
            2: os.path.join(patch_dir, "defect", "class_2_LS"),
            3: os.path.join(patch_dir, "defect", "class_3_SS"),
            4: os.path.join(patch_dir, "defect", "class_4_RD"),
        }

    def _list_files(self, directory: str) -> List[str]:
        if not os.path.exists(directory):
            return []
        return sorted([f for f in os.listdir(directory) if f.endswith(".jpg")])

    def load_binary(
        self,
        max_per_class: Optional[int] = None,
        resize: Optional[Tuple[int, int]] = None,
        grayscale: bool = True,
        seed: int = 42,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """이진 분류 데이터 로드 (정상=0, 비정상=1).

        Parameters
        ----------
        max_per_class : 클래스당 최대 샘플 수 (균형 맞춤)
        resize : 리사이즈 크기 (H, W)
        """
        rng = np.random.RandomState(seed)

        # 정상 패치
        normal_files = self._list_files(self.normal_dir)

        # 비정상 패치 (4종 합산)
        defect_files = []
        for cid, d in self.defect_dirs.items():
            files = self._list_files(d)
            defect_files.extend([(d, f) for f in files])

        # 균형 맞춤
        if max_per_class:
            if len(normal_files) > max_per_class:
                normal_files = rng.choice(
                    normal_files, max_per_class, replace=False
                ).tolist()
            if len(defect_files) > max_per_class:
                indices = rng.choice(
                    len(defect_files), max_per_class, replace=False
                )
                defect_files = [defect_files[i] for i in indices]

        images = []
        labels = []

        for f in normal_files:
            path = os.path.join(self.normal_dir, f)
            flag = cv2.IMREAD_GRAYSCALE if grayscale else cv2.IMREAD_COLOR
            img = cv2.imread(path, flag)
            if img is None:
                continue
            if resize:
                img = cv2.resize(img, resize)
            images.append(img)
            labels.append(0)

        for d, f in defect_files:
            path = os.path.join(d, f)
            flag = cv2.IMREAD_GRAYSCALE if grayscale else cv2.IMREAD_COLOR
            img = cv2.imread(path, flag)
            if img is None:
                continue
            if resize:
                img = cv2.resize(img, resize)
            images.append(img)
            labels.append(1)

        return np.array(images), np.array(labels)

    def load_defect4(
        self,
        max_per_class: Optional[int] = None,
        resize: Optional[Tuple[int, int]] = None,
        grayscale: bool = True,
        seed: int = 42,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """4종 결함 분류 데이터 로드 (ClassId 1~4).

        정상 패치는 제외.
        """
        rng = np.random.RandomState(seed)
        images = []
        labels = []

        for cid, d in self.defect_dirs.items():
            files = self._list_files(d)
            if max_per_class and len(files) > max_per_class:
                files = rng.choice(files, max_per_class, replace=False).tolist()

            for f in files:
                path = os.path.join(d, f)
                flag = cv2.IMREAD_GRAYSCALE if grayscale else cv2.IMREAD_COLOR
                img = cv2.imread(path, flag)
                if img is None:
                    continue
                if resize:
                    img = cv2.resize(img, resize)
                images.append(img)
                labels.append(cid)

        return np.array(images), np.array(labels)

    def print_stats(self):
        """패치 통계 출력."""
        print("\n" + "=" * 50)
        print("Severstal 크롭 패치 — 통계")
        print("=" * 50)

        normal = self._list_files(self.normal_dir)
        print(f"정상 패치: {len(normal):,}장")

        total_defect = 0
        for cid, d in self.defect_dirs.items():
            files = self._list_files(d)
            total_defect += len(files)
            from utils.severstal_loader import SeverstalDataLoader

            name = SeverstalDataLoader.get_class_name(cid)
            print(f"ClassId {cid} ({name}): {len(files):,}장")

        print(f"\n총 비정상 패치: {total_defect:,}장")
        print(f"총 패치: {len(normal) + total_defect:,}장")
        print("=" * 50)


# ──────────────────────────────────────────────
# 메인 실행
# ──────────────────────────────────────────────
if __name__ == "__main__":
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base, "data", "Severstal_Steel Defect Detection")
    output_dir = os.path.join(base, "data", "severstal_patches")

    loader = SeverstalDataLoader(data_dir)
    preprocessor = SeverstalPreprocessor(loader, output_dir)

    print("\n[패치 크롭 시작]")
    total = preprocessor.process_all(grayscale=True, verbose=True)

    print("\n[패치 통계 확인]")
    patch_loader = PatchDataLoader(output_dir)
    patch_loader.print_stats()

"""
Severstal Steel Defect Detection 데이터 로더

Kaggle Severstal 대회 데이터를 로드하고 관리하는 클래스.
- train.csv 파싱 (ImageId, ClassId, EncodedPixels)
- RLE 디코딩 → 세그멘테이션 마스크
- 정상/비정상 분리
- 슬라이딩 윈도우 크롭

ClassId 직관적 명칭 (형태적 특징 분석 기반):
  1 → 점상 결함 (Pitting Spot, PS)
  2 → 선형 긁힘 (Linear Scratch, LS)
  3 → 표면 변색 (Surface Stain, SS)
  4 → 압연 압흔 (Rolling Dent, RD)
"""

import os
import numpy as np
import pandas as pd
import cv2
from typing import Dict, List, Optional, Tuple


# ──────────────────────────────────────────────
# 클래스 명칭 매핑
# ──────────────────────────────────────────────
CLASS_NAMES_EN = {
    0: "Normal",
    1: "Pitting Spot",
    2: "Linear Scratch",
    3: "Surface Stain",
    4: "Rolling Dent",
}

CLASS_NAMES_KR = {
    0: "정상",
    1: "점상 결함 (PS)",
    2: "선형 긁힘 (LS)",
    3: "표면 변색 (SS)",
    4: "압연 압흔 (RD)",
}

CLASS_ABBR = {0: "NM", 1: "PS", 2: "LS", 3: "SS", 4: "RD"}

# 이진 분류용
BINARY_NAMES_EN = {0: "Normal", 1: "Abnormal"}
BINARY_NAMES_KR = {0: "정상", 1: "비정상"}


# ──────────────────────────────────────────────
# RLE 디코딩
# ──────────────────────────────────────────────
def rle_to_mask(rle_string: str, shape: Tuple[int, int] = (256, 1600)) -> np.ndarray:
    """Run-Length Encoding → 바이너리 마스크 변환.

    Severstal RLE은 column-major (Fortran) 순서.
    """
    if not isinstance(rle_string, str) or rle_string.strip() == "":
        return np.zeros(shape, dtype=np.uint8)

    numbers = list(map(int, rle_string.split()))
    starts = numbers[0::2]
    lengths = numbers[1::2]

    mask = np.zeros(shape[0] * shape[1], dtype=np.uint8)
    for s, l in zip(starts, lengths):
        mask[s - 1 : s - 1 + l] = 1

    return mask.reshape(shape, order="F")  # column-major


# ──────────────────────────────────────────────
# SeverstalDataLoader
# ──────────────────────────────────────────────
class SeverstalDataLoader:
    """Severstal Steel Defect Detection 데이터 관리 클래스."""

    def __init__(self, data_dir: str):
        """
        Parameters
        ----------
        data_dir : str
            'data/Severstal_Steel Defect Detection/' 경로
        """
        self.data_dir = data_dir
        self.train_dir = os.path.join(data_dir, "train_images")
        self.csv_path = os.path.join(data_dir, "train.csv")

        assert os.path.exists(self.train_dir), f"train_images 없음: {self.train_dir}"
        assert os.path.exists(self.csv_path), f"train.csv 없음: {self.csv_path}"

        # CSV 로드
        self.df = pd.read_csv(self.csv_path)

        # 전체 이미지 목록
        self.all_image_files = sorted(
            [f for f in os.listdir(self.train_dir) if f.endswith(".jpg")]
        )

        # 결함 이미지 ID 집합
        self.defect_image_ids = set(
            self.df[self.df["EncodedPixels"].notna()]["ImageId"].unique()
        )

        # 정상 이미지 ID 집합
        self.normal_image_ids = set(self.all_image_files) - self.defect_image_ids

        print(f"[SeverstalDataLoader] 로드 완료")
        print(f"  전체 이미지: {len(self.all_image_files)}장")
        print(f"  정상: {len(self.normal_image_ids)}장 ({len(self.normal_image_ids)/len(self.all_image_files)*100:.1f}%)")
        print(f"  비정상: {len(self.defect_image_ids)}장 ({len(self.defect_image_ids)/len(self.all_image_files)*100:.1f}%)")

    # ──────── 통계 ────────
    def get_stats(self) -> Dict:
        """데이터셋 통계 반환."""
        defect_df = self.df[self.df["EncodedPixels"].notna()]
        class_dist = defect_df.groupby("ClassId")["ImageId"].nunique().to_dict()

        # 단일/다중 결함
        defect_counts = defect_df.groupby("ImageId")["ClassId"].count()
        single = (defect_counts == 1).sum()
        multi = (defect_counts > 1).sum()

        return {
            "total_images": len(self.all_image_files),
            "normal_images": len(self.normal_image_ids),
            "defect_images": len(self.defect_image_ids),
            "class_distribution": class_dist,
            "single_defect_images": int(single),
            "multi_defect_images": int(multi),
        }

    # ──────── 이미지 로드 ────────
    def load_image(self, image_id: str, grayscale: bool = False) -> np.ndarray:
        """단일 이미지 로드."""
        path = os.path.join(self.train_dir, image_id)
        if grayscale:
            return cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        return cv2.imread(path)

    def get_defect_masks(self, image_id: str) -> Dict[int, np.ndarray]:
        """이미지의 ClassId별 결함 마스크 반환."""
        rows = self.df[
            (self.df["ImageId"] == image_id) & (self.df["EncodedPixels"].notna())
        ]
        masks = {}
        for _, row in rows.iterrows():
            cid = int(row["ClassId"])
            masks[cid] = rle_to_mask(row["EncodedPixels"])
        return masks

    def get_combined_mask(self, image_id: str) -> np.ndarray:
        """모든 결함을 합친 바이너리 마스크 (정상=0, 결함=1)."""
        masks = self.get_defect_masks(image_id)
        combined = np.zeros((256, 1600), dtype=np.uint8)
        for mask in masks.values():
            combined = np.maximum(combined, mask)
        return combined

    def get_primary_class(self, image_id: str) -> int:
        """이미지의 대표 결함 클래스 반환 (가장 큰 면적 기준).

        정상 이미지는 0 반환.
        """
        if image_id not in self.defect_image_ids:
            return 0

        masks = self.get_defect_masks(image_id)
        if not masks:
            return 0

        # 가장 큰 면적의 클래스
        max_area = 0
        primary_class = list(masks.keys())[0]
        for cid, mask in masks.items():
            area = mask.sum()
            if area > max_area:
                max_area = area
                primary_class = cid

        return primary_class

    # ──────── 정상/비정상 분리 ────────
    def get_normal_ids(self) -> List[str]:
        """정상 이미지 ID 리스트."""
        return sorted(list(self.normal_image_ids))

    def get_defect_ids(self) -> List[str]:
        """비정상 이미지 ID 리스트."""
        return sorted(list(self.defect_image_ids))

    def get_defect_ids_by_class(self, class_id: int) -> List[str]:
        """특정 ClassId의 이미지 ID 리스트 (단일 결함만)."""
        defect_df = self.df[self.df["EncodedPixels"].notna()]
        single = defect_df.groupby("ImageId").filter(lambda x: len(x) == 1)
        return sorted(
            single[single["ClassId"] == class_id]["ImageId"].unique().tolist()
        )

    # ──────── 이진 분류 데이터 로드 ────────
    def load_binary_dataset(
        self,
        max_normal: Optional[int] = None,
        max_defect: Optional[int] = None,
        grayscale: bool = True,
        resize: Optional[Tuple[int, int]] = None,
        seed: int = 42,
    ) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """이진 분류용 데이터 로드 (정상=0, 비정상=1).

        Returns
        -------
        images : (N, H, W) or (N, H, W, 3)
        labels : (N,) — 0=정상, 1=비정상
        image_ids : 원본 파일명 리스트
        """
        rng = np.random.RandomState(seed)

        normal_ids = self.get_normal_ids()
        defect_ids = self.get_defect_ids()

        if max_normal and max_normal < len(normal_ids):
            normal_ids = rng.choice(normal_ids, max_normal, replace=False).tolist()
        if max_defect and max_defect < len(defect_ids):
            defect_ids = rng.choice(defect_ids, max_defect, replace=False).tolist()

        images = []
        labels = []
        ids = []

        for img_id in normal_ids:
            img = self.load_image(img_id, grayscale=grayscale)
            if img is None:
                continue
            if resize:
                img = cv2.resize(img, resize)
            images.append(img)
            labels.append(0)
            ids.append(img_id)

        for img_id in defect_ids:
            img = self.load_image(img_id, grayscale=grayscale)
            if img is None:
                continue
            if resize:
                img = cv2.resize(img, resize)
            images.append(img)
            labels.append(1)
            ids.append(img_id)

        return np.array(images), np.array(labels), ids

    # ──────── 4종 결함 분류 데이터 로드 ────────
    def load_defect4_dataset(
        self,
        single_only: bool = True,
        grayscale: bool = True,
        resize: Optional[Tuple[int, int]] = None,
    ) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """4종 결함 분류용 데이터 로드.

        Parameters
        ----------
        single_only : bool
            True이면 단일 결함 이미지만 사용 (6,239장)
            False이면 다중 결함도 포함 (대표 클래스 사용, 6,666장)

        Returns
        -------
        images : (N, H, W) or (N, H, W, 3)
        labels : (N,) — 1~4 (ClassId)
        image_ids : 원본 파일명 리스트
        """
        defect_df = self.df[self.df["EncodedPixels"].notna()]

        if single_only:
            # 단일 결함 이미지만
            single_ids = (
                defect_df.groupby("ImageId")
                .filter(lambda x: len(x) == 1)["ImageId"]
                .unique()
            )
            target_ids = sorted(single_ids.tolist())
        else:
            target_ids = sorted(defect_df["ImageId"].unique().tolist())

        images = []
        labels = []
        ids = []

        for img_id in target_ids:
            img = self.load_image(img_id, grayscale=grayscale)
            if img is None:
                continue
            if resize:
                img = cv2.resize(img, resize)

            if single_only:
                cid = int(
                    defect_df[defect_df["ImageId"] == img_id]["ClassId"].values[0]
                )
            else:
                cid = self.get_primary_class(img_id)

            images.append(img)
            labels.append(cid)
            ids.append(img_id)

        return np.array(images), np.array(labels), ids

    # ──────── 유틸리티 ────────
    @staticmethod
    def get_class_name(class_id: int, lang: str = "kr") -> str:
        """ClassId → 직관적 명칭."""
        if lang == "kr":
            return CLASS_NAMES_KR.get(class_id, f"Unknown({class_id})")
        return CLASS_NAMES_EN.get(class_id, f"Unknown({class_id})")

    @staticmethod
    def get_class_abbr(class_id: int) -> str:
        """ClassId → 약어."""
        return CLASS_ABBR.get(class_id, "??")

    def print_stats(self):
        """데이터셋 통계 출력."""
        stats = self.get_stats()
        print("\n" + "=" * 50)
        print("Severstal Steel Defect Detection — 데이터 통계")
        print("=" * 50)
        print(f"전체 이미지: {stats['total_images']:,}장")
        print(f"정상 이미지: {stats['normal_images']:,}장")
        print(f"비정상 이미지: {stats['defect_images']:,}장")
        print(f"  단일 결함: {stats['single_defect_images']:,}장")
        print(f"  다중 결함: {stats['multi_defect_images']:,}장")
        print("\n[결함 클래스 분포]")
        for cid, count in sorted(stats["class_distribution"].items()):
            name = self.get_class_name(cid, "kr")
            abbr = self.get_class_abbr(cid)
            print(f"  ClassId {cid} ({abbr}) {name}: {count}장")
        print("=" * 50)


# ──────────────────────────────────────────────
# 테스트
# ──────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base, "data", "Severstal_Steel Defect Detection")

    loader = SeverstalDataLoader(data_dir)
    loader.print_stats()

    # 샘플 이미지 로드 테스트
    normal_ids = loader.get_normal_ids()
    defect_ids = loader.get_defect_ids()

    print(f"\n[샘플 테스트]")
    img = loader.load_image(normal_ids[0])
    print(f"  정상 이미지: {normal_ids[0]}, shape={img.shape}")

    img = loader.load_image(defect_ids[0])
    masks = loader.get_defect_masks(defect_ids[0])
    print(f"  비정상 이미지: {defect_ids[0]}, shape={img.shape}")
    for cid, mask in masks.items():
        print(f"    ClassId {cid} ({loader.get_class_name(cid)}): 면적={mask.sum()}")

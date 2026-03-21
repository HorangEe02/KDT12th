"""NEU Metal Surface Defects Dataset 로더.

NEU 금속 표면 결함 데이터셋을 로드하고 분석하기 위한 유틸리티 모듈.
6종 결함(Crazing, Inclusion, Patches, Pitted Surface, Rolled-in Scale, Scratches)
이미지를 numpy 배열로 로드하며, train/test 분할 및 기본 통계를 제공한다.
"""

import os
import glob
import numpy as np
import cv2
import pandas as pd
from typing import Optional, Union
from sklearn.model_selection import train_test_split


class NEUDataLoader:
    """NEU Metal Surface Defects 데이터셋 로더.

    Args:
        data_dir: NEU-DET 데이터 디렉토리 경로.
            train/images/ 하위에 클래스별 폴더가 있는 구조를 기대한다.
            예: data_dir/train/images/crazing/, data_dir/validation/images/crazing/

    Attributes:
        data_dir: 데이터 루트 디렉토리 경로.
        class_names: 탐지된 클래스명 리스트 (영문, 정렬).
        class_name_kr: 영문→한글 클래스명 매핑 딕셔너리.
        class_to_label: 클래스명→정수 라벨 매핑.
        label_to_class: 정수 라벨→클래스명 매핑.
    """

    CLASS_NAME_KR = {
        "crazing": "균열",
        "inclusion": "개재물",
        "patches": "패치",
        "pitted_surface": "구멍",
        "rolled-in_scale": "압연스케일",
        "scratches": "스크래치",
    }

    def __init__(self, data_dir: str) -> None:
        if not os.path.isdir(data_dir):
            raise FileNotFoundError(f"데이터 디렉토리를 찾을 수 없습니다: {data_dir}")

        self.data_dir = data_dir

        # 실제 폴더 구조 자동 탐지
        self._train_img_dir: Optional[str] = None
        self._val_img_dir: Optional[str] = None
        self._flat_mode = False

        train_path = os.path.join(data_dir, "train", "images")
        val_path = os.path.join(data_dir, "validation", "images")

        if os.path.isdir(train_path):
            self._train_img_dir = train_path
            if os.path.isdir(val_path):
                self._val_img_dir = val_path
        else:
            # Flat 구조: data_dir 바로 아래에 클래스 폴더가 있는 경우
            self._train_img_dir = data_dir
            self._flat_mode = True

        # 클래스명 자동 탐지
        self.class_names = self._detect_classes()
        self.class_name_kr = {
            cn: self.CLASS_NAME_KR.get(cn, cn) for cn in self.class_names
        }
        self.class_to_label = {cn: i for i, cn in enumerate(self.class_names)}
        self.label_to_class = {i: cn for cn, i in self.class_to_label.items()}

        print(f"[NEUDataLoader] 데이터 경로: {data_dir}")
        print(f"[NEUDataLoader] 탐지된 클래스 ({len(self.class_names)}개): {self.class_names}")
        print(f"[NEUDataLoader] 한글 매핑: {self.class_name_kr}")

    def _detect_classes(self) -> list[str]:
        """클래스 폴더명을 자동 탐지하여 정렬된 리스트로 반환."""
        entries = sorted(os.listdir(self._train_img_dir))
        classes = [
            e for e in entries
            if os.path.isdir(os.path.join(self._train_img_dir, e))
            and not e.startswith(".")
        ]
        if not classes:
            raise FileNotFoundError(
                f"클래스 폴더를 찾을 수 없습니다: {self._train_img_dir}"
            )
        return classes

    def _get_image_paths(self, class_name: str, split: str = "all") -> list[str]:
        """특정 클래스의 이미지 파일 경로 리스트를 반환.

        Args:
            class_name: 클래스 폴더명.
            split: "train", "validation", "all" 중 택 1.

        Returns:
            이미지 파일 경로 리스트.
        """
        paths: list[str] = []
        exts = ("*.jpg", "*.jpeg", "*.bmp", "*.png")

        if split in ("train", "all") and self._train_img_dir:
            class_dir = os.path.join(self._train_img_dir, class_name)
            if os.path.isdir(class_dir):
                for ext in exts:
                    paths.extend(glob.glob(os.path.join(class_dir, ext)))

        if split in ("validation", "all") and self._val_img_dir:
            class_dir = os.path.join(self._val_img_dir, class_name)
            if os.path.isdir(class_dir):
                for ext in exts:
                    paths.extend(glob.glob(os.path.join(class_dir, ext)))

        return sorted(paths)

    def load_all_images(
        self, split: str = "all"
    ) -> tuple[np.ndarray, np.ndarray, list[str]]:
        """전체 이미지를 numpy 배열로 로드.

        Args:
            split: "train", "validation", "all" 중 택 1.

        Returns:
            (images, labels, class_names) 튜플.
            - images: (N, 200, 200) uint8 그레이스케일 배열.
            - labels: (N,) int 라벨 배열 (0~5).
            - class_names: 클래스명 리스트.
        """
        all_images: list[np.ndarray] = []
        all_labels: list[int] = []

        total_count = 0
        for cn in self.class_names:
            total_count += len(self._get_image_paths(cn, split))

        print(f"[로드 시작] 총 {total_count}장 ({split})")

        loaded = 0
        for cn in self.class_names:
            label = self.class_to_label[cn]
            paths = self._get_image_paths(cn, split)

            for p in paths:
                img = cv2.imread(p, cv2.IMREAD_GRAYSCALE)
                if img is None:
                    print(f"  ⚠️ 로드 실패: {p}")
                    continue
                # 200x200이 아닌 경우 리사이즈
                if img.shape != (200, 200):
                    img = cv2.resize(img, (200, 200))
                all_images.append(img)
                all_labels.append(label)
                loaded += 1

                if loaded % 300 == 0 or loaded == total_count:
                    print(f"  진행: {loaded}/{total_count} ({loaded*100//total_count}%)")

        images = np.array(all_images, dtype=np.uint8)
        labels = np.array(all_labels, dtype=np.int32)

        print(f"[로드 완료] images: {images.shape}, labels: {labels.shape}")
        for cn in self.class_names:
            count = np.sum(labels == self.class_to_label[cn])
            print(f"  {cn} ({self.class_name_kr[cn]}): {count}장")

        return images, labels, self.class_names

    def load_class_images(
        self,
        class_name: str,
        n_samples: Optional[int] = None,
        split: str = "all",
    ) -> np.ndarray:
        """특정 클래스의 이미지만 로드.

        Args:
            class_name: 로드할 클래스명.
            n_samples: 지정하면 랜덤 샘플링. None이면 전체 로드.
            split: "train", "validation", "all".

        Returns:
            (N, 200, 200) uint8 그레이스케일 배열.
        """
        if class_name not in self.class_names:
            raise ValueError(
                f"알 수 없는 클래스: {class_name}. 가능: {self.class_names}"
            )

        paths = self._get_image_paths(class_name, split)
        if n_samples is not None and n_samples < len(paths):
            rng = np.random.default_rng(42)
            indices = rng.choice(len(paths), size=n_samples, replace=False)
            paths = [paths[i] for i in sorted(indices)]

        images = []
        for p in paths:
            img = cv2.imread(p, cv2.IMREAD_GRAYSCALE)
            if img is not None:
                if img.shape != (200, 200):
                    img = cv2.resize(img, (200, 200))
                images.append(img)

        return np.array(images, dtype=np.uint8)

    def get_sample_images(
        self, n_per_class: int = 5, split: str = "all"
    ) -> dict[str, np.ndarray]:
        """각 클래스별 n_per_class장씩 랜덤 샘플링.

        Args:
            n_per_class: 클래스당 샘플 수.
            split: "train", "validation", "all".

        Returns:
            {클래스명: (n_per_class, 200, 200) 배열} 딕셔너리.
        """
        samples: dict[str, np.ndarray] = {}
        for cn in self.class_names:
            samples[cn] = self.load_class_images(cn, n_samples=n_per_class, split=split)
        return samples

    def split_data(
        self,
        test_size: float = 0.2,
        random_state: int = 42,
        split: str = "all",
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """데이터를 train/test로 분할.

        Args:
            test_size: 테스트 비율 (0~1).
            random_state: 랜덤 시드.
            split: 원본 데이터 로드 시 split 옵션.

        Returns:
            (X_train, X_test, y_train, y_test) 튜플.
        """
        images, labels, _ = self.load_all_images(split=split)
        X_train, X_test, y_train, y_test = train_test_split(
            images, labels,
            test_size=test_size,
            random_state=random_state,
            stratify=labels,
        )
        print(f"[Split] Train: {X_train.shape[0]}장, Test: {X_test.shape[0]}장")
        return X_train, X_test, y_train, y_test

    def get_dataset_stats(self, split: str = "all") -> pd.DataFrame:
        """클래스별 통계를 DataFrame으로 반환.

        Returns:
            클래스별 이미지 수, 평균 밝기, 표준편차, 최소/최대 픽셀값을 포함하는 DataFrame.
        """
        images, labels, _ = self.load_all_images(split=split)

        rows = []
        for cn in self.class_names:
            label = self.class_to_label[cn]
            class_imgs = images[labels == label]
            rows.append({
                "클래스(EN)": cn,
                "클래스(KR)": self.class_name_kr[cn],
                "이미지 수": len(class_imgs),
                "평균 밝기": round(float(class_imgs.mean()), 2),
                "밝기 표준편차": round(float(class_imgs.std()), 2),
                "최소 픽셀": int(class_imgs.min()),
                "최대 픽셀": int(class_imgs.max()),
            })

        return pd.DataFrame(rows)


if __name__ == "__main__":
    import sys
    # 프로젝트 루트 기준 상대 경로
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(project_root, "data", "NEU-DET")

    print("=" * 60)
    print("NEUDataLoader 테스트")
    print("=" * 60)

    loader = NEUDataLoader(data_dir)

    # 전체 데이터 로드
    images, labels, class_names = loader.load_all_images()
    print(f"\n전체 이미지 shape: {images.shape}")
    print(f"라벨 shape: {labels.shape}")
    print(f"라벨 분포: {dict(zip(*np.unique(labels, return_counts=True)))}")

    # 샘플 이미지
    samples = loader.get_sample_images(n_per_class=3)
    for cn, imgs in samples.items():
        print(f"  {cn}: {imgs.shape}")

    # Split
    X_train, X_test, y_train, y_test = loader.split_data()

    # 통계
    print("\n[데이터셋 통계]")
    stats = loader.get_dataset_stats()
    print(stats.to_string(index=False))

"""통합 특징 추출 파이프라인.

HOG, LBP, 픽셀 통계, 윤곽선, 에지 특징을 조합하여
ML 분류용 최종 특징 행렬을 생성한다.
"""

import numpy as np
import warnings
from typing import Optional, Callable
from sklearn.preprocessing import StandardScaler, MinMaxScaler

from features.hog_features import extract_hog
from features.lbp_features import extract_lbp_histogram
from features.pixel_stats import extract_pixel_feature_vector
from features.contour_features import extract_contour_feature_vector
from features.edge_features import extract_edge_feature_vector


class FeaturePipeline:
    """통합 특징 추출 파이프라인.

    Args:
        use_hog: HOG 특징 사용 여부.
        use_lbp: LBP 특징 사용 여부.
        use_pixel_stats: 픽셀 통계 특징 사용 여부.
        use_contour: 윤곽선 특징 사용 여부.
        use_edge: 에지 특징 사용 여부.
        hog_params: HOG 파라미터 딕셔너리.
        lbp_params: LBP 파라미터 딕셔너리.
        preprocess_fn: 전처리 함수. None이면 원본 사용.
        scaler: 스케일링 방법 ("standard", "minmax", "none").
    """

    def __init__(
        self,
        use_hog: bool = True,
        use_lbp: bool = True,
        use_pixel_stats: bool = True,
        use_contour: bool = True,
        use_edge: bool = True,
        hog_params: dict = None,
        lbp_params: dict = None,
        preprocess_fn: Optional[Callable] = None,
        scaler: str = "standard",
    ):
        self.use_hog = use_hog
        self.use_lbp = use_lbp
        self.use_pixel_stats = use_pixel_stats
        self.use_contour = use_contour
        self.use_edge = use_edge
        self.hog_params = hog_params or {}
        self.lbp_params = lbp_params or {}
        self.preprocess_fn = preprocess_fn

        if scaler == "standard":
            self._scaler = StandardScaler()
        elif scaler == "minmax":
            self._scaler = MinMaxScaler()
        else:
            self._scaler = None

        self._fitted = False
        self._feature_dim = None

    def extract_single(self, image: np.ndarray) -> np.ndarray:
        """단일 이미지에서 특징 벡터 추출."""
        img = self.preprocess_fn(image) if self.preprocess_fn else image.copy()

        parts = []
        if self.use_hog:
            parts.append(extract_hog(img, **self.hog_params))
        if self.use_lbp:
            parts.append(extract_lbp_histogram(img, **self.lbp_params))
        if self.use_pixel_stats:
            parts.append(extract_pixel_feature_vector(img))
        if self.use_contour:
            parts.append(extract_contour_feature_vector(img))
        if self.use_edge:
            parts.append(extract_edge_feature_vector(img))

        vec = np.concatenate(parts)
        return np.nan_to_num(vec, nan=0.0, posinf=0.0, neginf=0.0)

    def extract_batch(
        self, images: np.ndarray, labels: np.ndarray = None
    ) -> tuple[np.ndarray, Optional[np.ndarray]]:
        """배치 이미지에서 특징 행렬 추출 + scaler fit.

        Returns:
            (특징 행렬, 라벨).
        """
        n = len(images)
        first = self.extract_single(images[0])
        self._feature_dim = len(first)
        matrix = np.zeros((n, self._feature_dim), dtype=np.float64)
        matrix[0] = first

        for i in range(1, n):
            matrix[i] = self.extract_single(images[i])
            if (i + 1) % 200 == 0 or i == n - 1:
                print(f"  특징 추출: {i+1}/{n} ({(i+1)*100//n}%)")

        if self._scaler is not None:
            matrix = self._scaler.fit_transform(matrix)
            self._fitted = True

        return matrix, labels

    def transform(self, images: np.ndarray) -> np.ndarray:
        """학습 시 fit된 scaler로 transform만 (테스트 데이터용)."""
        n = len(images)
        matrix = np.zeros((n, self._feature_dim), dtype=np.float64)
        for i in range(n):
            matrix[i] = self.extract_single(images[i])
            if (i + 1) % 200 == 0 or i == n - 1:
                print(f"  특징 변환: {i+1}/{n} ({(i+1)*100//n}%)")

        if self._scaler is not None and self._fitted:
            matrix = self._scaler.transform(matrix)
        return matrix

    def get_feature_names(self) -> list[str]:
        """전체 특징 이름 리스트 (선택된 특징만)."""
        names = []
        if self.use_hog:
            dim = len(extract_hog(np.zeros((200, 200), dtype=np.uint8), **self.hog_params))
            names += [f"hog_{i}" for i in range(dim)]
        if self.use_lbp:
            dim = len(extract_lbp_histogram(np.zeros((200, 200), dtype=np.uint8), **self.lbp_params))
            names += [f"lbp_{i}" for i in range(dim)]
        if self.use_pixel_stats:
            from features.pixel_stats import get_pixel_feature_names
            names += get_pixel_feature_names()
        if self.use_contour:
            from features.contour_features import get_contour_feature_names
            names += get_contour_feature_names()
        if self.use_edge:
            from features.edge_features import get_edge_feature_names
            names += get_edge_feature_names()
        return names

    def get_feature_dim(self) -> int:
        """전체 특징 벡터 차원."""
        if self._feature_dim:
            return self._feature_dim
        return len(self.extract_single(np.zeros((200, 200), dtype=np.uint8)))

    def get_feature_group_indices(self) -> dict[str, tuple[int, int]]:
        """각 특징 그룹의 시작/끝 인덱스."""
        dummy = np.zeros((200, 200), dtype=np.uint8)
        groups = {}
        offset = 0
        if self.use_hog:
            dim = len(extract_hog(dummy, **self.hog_params))
            groups["hog"] = (offset, offset + dim)
            offset += dim
        if self.use_lbp:
            dim = len(extract_lbp_histogram(dummy, **self.lbp_params))
            groups["lbp"] = (offset, offset + dim)
            offset += dim
        if self.use_pixel_stats:
            dim = len(extract_pixel_feature_vector(dummy))
            groups["pixel_stats"] = (offset, offset + dim)
            offset += dim
        if self.use_contour:
            dim = len(extract_contour_feature_vector(dummy))
            groups["contour"] = (offset, offset + dim)
            offset += dim
        if self.use_edge:
            dim = len(extract_edge_feature_vector(dummy))
            groups["edge"] = (offset, offset + dim)
            offset += dim
        return groups


def create_experiment_configs() -> list[dict]:
    """README에 정의된 실험 조건 목록."""
    return [
        {"name": "Baseline_HOG_raw", "use_hog": True, "use_lbp": False,
         "use_pixel_stats": False, "use_contour": False, "use_edge": False, "preprocess": False},
        {"name": "HOG_preprocessed", "use_hog": True, "use_lbp": False,
         "use_pixel_stats": False, "use_contour": False, "use_edge": False, "preprocess": True},
        {"name": "HOG_LBP_preprocessed", "use_hog": True, "use_lbp": True,
         "use_pixel_stats": False, "use_contour": False, "use_edge": False, "preprocess": True},
        {"name": "HOG_LBP_Stats_preprocessed", "use_hog": True, "use_lbp": True,
         "use_pixel_stats": True, "use_contour": False, "use_edge": False, "preprocess": True},
        {"name": "All_features_preprocessed", "use_hog": True, "use_lbp": True,
         "use_pixel_stats": True, "use_contour": True, "use_edge": True, "preprocess": True},
    ]


if __name__ == "__main__":
    import os, sys
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    sys.path.insert(0, project_root)

    print("\n=== feature_pipeline.py 테스트 ===")
    configs = create_experiment_configs()
    for cfg in configs:
        pipe = FeaturePipeline(
            use_hog=cfg["use_hog"], use_lbp=cfg["use_lbp"],
            use_pixel_stats=cfg["use_pixel_stats"],
            use_contour=cfg["use_contour"], use_edge=cfg["use_edge"],
        )
        dim = pipe.get_feature_dim()
        groups = pipe.get_feature_group_indices()
        print(f"  {cfg['name']:35s}: dim={dim:6d}  groups={list(groups.keys())}")
    print("✅ feature_pipeline.py 테스트 완료")

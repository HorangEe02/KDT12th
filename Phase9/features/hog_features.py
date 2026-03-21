"""HOG(Histogram of Oriented Gradients) 특징 추출 모듈.

결함의 경계와 형태 패턴을 효과적으로 캡처하는 HOG 기술자를 제공한다.
"""

import numpy as np
import cv2
import warnings
from typing import Union
from skimage.feature import hog


def _to_float(image: np.ndarray) -> np.ndarray:
    if image is None:
        raise ValueError("입력 이미지가 None입니다.")
    img = image.copy()
    if img.ndim == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return img.astype(np.float64) / 255.0


def extract_hog(
    image: np.ndarray,
    orientations: int = 9,
    pixels_per_cell: tuple = (8, 8),
    cells_per_block: tuple = (2, 2),
    visualize: bool = False,
) -> Union[np.ndarray, tuple[np.ndarray, np.ndarray]]:
    """HOG 특징 벡터 추출.

    Args:
        image: 그레이스케일 입력 이미지.
        orientations: 방향 빈 수.
        pixels_per_cell: 셀당 픽셀 수.
        cells_per_block: 블록당 셀 수.
        visualize: True이면 HOG 시각화 이미지도 반환.

    Returns:
        feature_vector 또는 (feature_vector, hog_image).
    """
    img = _to_float(image)
    result = hog(
        img,
        orientations=orientations,
        pixels_per_cell=pixels_per_cell,
        cells_per_block=cells_per_block,
        block_norm="L2-Hys",
        visualize=visualize,
        feature_vector=True,
    )
    if visualize:
        return result[0], result[1]
    return result


def extract_hog_multiscale(
    image: np.ndarray,
    cell_sizes: list[tuple] = None,
) -> np.ndarray:
    """멀티스케일 HOG: 여러 셀 크기에서 추출하고 concatenate.

    Args:
        image: 그레이스케일 입력 이미지.
        cell_sizes: 셀 크기 리스트. 기본 [(4,4), (8,8), (16,16)].

    Returns:
        concatenated feature vector.
    """
    if cell_sizes is None:
        cell_sizes = [(4, 4), (8, 8), (16, 16)]
    parts = [extract_hog(image, pixels_per_cell=cs) for cs in cell_sizes]
    return np.concatenate(parts)


def extract_hog_compact(
    image: np.ndarray, target_dim: int = 512, pca_model=None
) -> tuple[np.ndarray, object]:
    """차원 축소된 HOG 특징 추출.

    Args:
        image: 그레이스케일 입력 이미지.
        target_dim: 목표 차원.
        pca_model: 기존 PCA 모델. None이면 fit 불가(배치용).

    Returns:
        (축소된 특징 벡터, pca_model).
    """
    feat = extract_hog(image)
    if len(feat) <= target_dim:
        return feat, None
    if pca_model is not None:
        return pca_model.transform(feat.reshape(1, -1)).flatten(), pca_model
    return feat[:target_dim], None  # 단일 이미지에서는 PCA fit 불가


def batch_extract_hog(
    images: np.ndarray,
    orientations: int = 9,
    pixels_per_cell: tuple = (8, 8),
    cells_per_block: tuple = (2, 2),
) -> np.ndarray:
    """여러 이미지에 대해 일괄 HOG 추출.

    Args:
        images: (N, H, W) 배열.

    Returns:
        (N, feature_dim) 특징 행렬.
    """
    n = len(images)
    first = extract_hog(images[0], orientations, pixels_per_cell, cells_per_block)
    dim = len(first)
    features = np.zeros((n, dim), dtype=np.float64)
    features[0] = first

    for i in range(1, n):
        features[i] = extract_hog(images[i], orientations, pixels_per_cell, cells_per_block)
        if (i + 1) % 300 == 0 or i == n - 1:
            print(f"  HOG 추출: {i+1}/{n} ({(i+1)*100//n}%)")
    return features


def get_hog_feature_dim(
    image_shape: tuple = (200, 200),
    orientations: int = 9,
    pixels_per_cell: tuple = (8, 8),
    cells_per_block: tuple = (2, 2),
) -> int:
    """파라미터에 따른 HOG 특징 차원 계산."""
    dummy = np.zeros(image_shape, dtype=np.float64)
    return len(extract_hog(dummy, orientations, pixels_per_cell, cells_per_block))


if __name__ == "__main__":
    import os, sys
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    from utils.data_loader import NEUDataLoader

    loader = NEUDataLoader(os.path.join(project_root, "data", "NEU-DET"))
    samples = loader.get_sample_images(n_per_class=1)

    print("\n=== hog_features.py 테스트 ===")
    dim = get_hog_feature_dim()
    print(f"기본 HOG 차원: {dim}")

    for cn in loader.class_names:
        feat = extract_hog(samples[cn][0])
        print(f"  {cn:20s}: shape={feat.shape}")

    feat_vis, hog_img = extract_hog(samples["scratches"][0], visualize=True)
    print(f"\nvisualize=True: feat={feat_vis.shape}, hog_img={hog_img.shape}")
    print("✅ hog_features.py 테스트 완료")

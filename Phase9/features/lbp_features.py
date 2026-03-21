"""LBP(Local Binary Pattern) 특징 추출 모듈.

결함 표면의 텍스처 패턴을 캡처하는 LBP 기술자를 제공한다.
"""

import numpy as np
import cv2
import warnings
from typing import Optional
from skimage.feature import local_binary_pattern


def _validate_gray(image: np.ndarray) -> np.ndarray:
    if image is None:
        raise ValueError("입력 이미지가 None입니다.")
    if image.ndim == 3:
        return cv2.cvtColor(image.copy(), cv2.COLOR_BGR2GRAY)
    return image.copy()


def extract_lbp(
    image: np.ndarray, n_points: int = 24, radius: int = 3, method: str = "uniform"
) -> np.ndarray:
    """LBP 패턴 맵 생성.

    Returns:
        LBP 패턴 맵 (image와 동일 shape, 각 픽셀의 LBP 코드값).
    """
    gray = _validate_gray(image)
    return local_binary_pattern(gray, n_points, radius, method=method)


def extract_lbp_histogram(
    image: np.ndarray, n_points: int = 24, radius: int = 3, method: str = "uniform"
) -> np.ndarray:
    """LBP 히스토그램 (특징 벡터).

    Returns:
        (n_points+2,) shape의 L2 정규화된 히스토그램.
    """
    lbp = extract_lbp(image, n_points, radius, method)
    n_bins = n_points + 2
    hist, _ = np.histogram(lbp.ravel(), bins=n_bins, range=(0, n_bins))
    hist = hist.astype(np.float64)
    norm = np.linalg.norm(hist) + 1e-7
    return hist / norm


def extract_lbp_spatial(
    image: np.ndarray, grid_size: int = 4, n_points: int = 24, radius: int = 3
) -> np.ndarray:
    """공간 분할 LBP 히스토그램 (Spatial LBP).

    Returns:
        (grid_size² × (n_points+2),) shape 벡터.
    """
    gray = _validate_gray(image)
    lbp = extract_lbp(gray, n_points, radius)
    h, w = gray.shape
    n_bins = n_points + 2

    rows = np.array_split(np.arange(h), grid_size)
    cols = np.array_split(np.arange(w), grid_size)

    hists = []
    for r_range in rows:
        for c_range in cols:
            block = lbp[r_range[0]:r_range[-1]+1, c_range[0]:c_range[-1]+1]
            hist, _ = np.histogram(block.ravel(), bins=n_bins, range=(0, n_bins))
            hist = hist.astype(np.float64)
            norm = np.linalg.norm(hist) + 1e-7
            hists.append(hist / norm)

    return np.concatenate(hists)


def extract_lbp_multiscale(
    image: np.ndarray,
    radii: list[int] = None,
    n_points_list: list[int] = None,
) -> np.ndarray:
    """멀티스케일 LBP.

    Args:
        radii: 반경 리스트. 기본 [1, 3, 5].
        n_points_list: 포인트 수 리스트. 기본 [8, 24, 40].

    Returns:
        concatenated feature vector.
    """
    if radii is None:
        radii = [1, 3, 5]
    if n_points_list is None:
        n_points_list = [8, 24, 40]
    if len(radii) != len(n_points_list):
        raise ValueError("radii와 n_points_list 길이가 일치해야 합니다.")

    parts = [extract_lbp_histogram(image, np, r) for np, r in zip(n_points_list, radii)]
    return np.concatenate(parts)


def batch_extract_lbp(
    images: np.ndarray, mode: str = "histogram", **kwargs
) -> np.ndarray:
    """여러 이미지에 대해 일괄 LBP 특징 추출.

    Args:
        images: (N, H, W) 배열.
        mode: "histogram", "spatial", "multiscale".

    Returns:
        (N, feature_dim) 특징 행렬.
    """
    funcs = {
        "histogram": lambda img: extract_lbp_histogram(img, **kwargs),
        "spatial": lambda img: extract_lbp_spatial(img, **kwargs),
        "multiscale": lambda img: extract_lbp_multiscale(img, **kwargs),
    }
    if mode not in funcs:
        raise ValueError(f"지원하지 않는 mode: {mode}")

    fn = funcs[mode]
    n = len(images)
    first = fn(images[0])
    features = np.zeros((n, len(first)), dtype=np.float64)
    features[0] = first

    for i in range(1, n):
        features[i] = fn(images[i])
        if (i + 1) % 300 == 0 or i == n - 1:
            print(f"  LBP 추출: {i+1}/{n} ({(i+1)*100//n}%)")
    return features


def visualize_lbp_pattern(
    image: np.ndarray, n_points: int = 24, radius: int = 3
) -> np.ndarray:
    """LBP 패턴 맵을 시각화용으로 0~255 정규화.

    Returns:
        uint8 이미지.
    """
    lbp = extract_lbp(image, n_points, radius)
    mn, mx = lbp.min(), lbp.max()
    if mx - mn == 0:
        return np.zeros_like(image, dtype=np.uint8)
    return ((lbp - mn) / (mx - mn) * 255).astype(np.uint8)


if __name__ == "__main__":
    import os, sys
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    from utils.data_loader import NEUDataLoader

    loader = NEUDataLoader(os.path.join(project_root, "data", "NEU-DET"))
    samples = loader.get_sample_images(n_per_class=1)

    print("\n=== lbp_features.py 테스트 ===")
    for cn in loader.class_names:
        hist = extract_lbp_histogram(samples[cn][0])
        spatial = extract_lbp_spatial(samples[cn][0], grid_size=4)
        multi = extract_lbp_multiscale(samples[cn][0])
        print(f"  {cn:20s}: hist={hist.shape}  spatial={spatial.shape}  multi={multi.shape}")
    print("✅ lbp_features.py 테스트 완료")

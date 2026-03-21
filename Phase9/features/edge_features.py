"""에지 기반 특징 추출 모듈.

에지 밀도 맵, 방향 히스토그램, 강도 통계, 텍스처 특징, 그래디언트 특징을
추출하여 ML 분류의 특징 벡터로 활용한다.
"""

import cv2
import numpy as np
import warnings
import math
from typing import Optional


def _validate_gray(image: np.ndarray) -> np.ndarray:
    if image is None:
        raise ValueError("입력 이미지가 None입니다.")
    if image.ndim == 3:
        return cv2.cvtColor(image.copy(), cv2.COLOR_BGR2GRAY)
    if image.ndim != 2:
        raise ValueError(f"ndim={image.ndim}")
    return image.copy()


def compute_edge_density_map(
    image: np.ndarray, grid_size: int = 4, edge_method: str = "canny"
) -> np.ndarray:
    """이미지를 grid로 분할하고 각 셀의 에지 밀도를 계산.

    Returns:
        (grid_size, grid_size) shape의 에지 밀도 맵 (0.0~1.0).
    """
    gray = _validate_gray(image)
    h, w = gray.shape

    if edge_method == "canny":
        med = float(np.median(gray))
        lo, hi = max(0, int(0.67 * med)), min(255, int(1.33 * med))
        edges = cv2.Canny(gray, lo, hi)
    elif edge_method == "sobel":
        sx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        edges = np.clip(np.sqrt(sx**2 + sy**2), 0, 255).astype(np.uint8)
    else:
        edges = cv2.convertScaleAbs(cv2.Laplacian(gray, cv2.CV_64F))

    density = np.zeros((grid_size, grid_size), dtype=np.float64)
    rows = np.array_split(np.arange(h), grid_size)
    cols = np.array_split(np.arange(w), grid_size)

    for r_idx, r_range in enumerate(rows):
        for c_idx, c_range in enumerate(cols):
            cell = edges[r_range[0]:r_range[-1]+1, c_range[0]:c_range[-1]+1]
            density[r_idx, c_idx] = np.mean(cell > 0)

    return density


def compute_edge_direction_histogram(
    image: np.ndarray, n_bins: int = 8
) -> np.ndarray:
    """에지 방향 히스토그램 (magnitude 가중, L2 정규화).

    Returns:
        (n_bins,) shape의 정규화된 방향 히스토그램.
    """
    gray = _validate_gray(image)
    sx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    sy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    magnitude = np.sqrt(sx**2 + sy**2)
    direction = np.degrees(np.arctan2(sy, sx)) % 360  # 0~360

    # magnitude threshold
    thresh = magnitude.mean() + magnitude.std()
    mask = magnitude > thresh

    if not mask.any():
        return np.zeros(n_bins, dtype=np.float64)

    dirs = direction[mask]
    mags = magnitude[mask]
    bin_edges = np.linspace(0, 360, n_bins + 1)
    hist = np.zeros(n_bins, dtype=np.float64)

    for i in range(n_bins):
        in_bin = (dirs >= bin_edges[i]) & (dirs < bin_edges[i + 1])
        hist[i] = mags[in_bin].sum()

    # L2 정규화
    norm = np.linalg.norm(hist)
    if norm > 0:
        hist /= norm
    return hist


def compute_edge_intensity_stats(image: np.ndarray) -> dict[str, float]:
    """에지 강도(Sobel magnitude)의 통계 특징.

    Returns:
        평균, 표준편차, 최대값, 왜도, 첨도, 에너지, 강한 에지 비율.
    """
    gray = _validate_gray(image)
    sx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    sy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    magnitude = np.sqrt(sx**2 + sy**2)

    # 에지 픽셀만
    thresh = magnitude.mean()
    edge_vals = magnitude[magnitude > thresh]

    if len(edge_vals) == 0:
        return {"edge_mean": 0, "edge_std": 0, "edge_max": 0,
                "edge_skewness": 0, "edge_kurtosis": 0, "edge_energy": 0,
                "strong_edge_ratio": 0}

    from scipy.stats import skew, kurtosis
    mean_v = float(edge_vals.mean())
    std_v = float(edge_vals.std())

    return {
        "edge_mean": mean_v,
        "edge_std": std_v,
        "edge_max": float(edge_vals.max()),
        "edge_skewness": float(skew(edge_vals)),
        "edge_kurtosis": float(kurtosis(edge_vals)),
        "edge_energy": float(np.mean(magnitude**2)),
        "strong_edge_ratio": float(np.mean(magnitude > mean_v + 2 * std_v)),
    }


def compute_edge_texture_features(
    image: np.ndarray, grid_size: int = 4
) -> dict[str, float]:
    """에지 밀도 맵의 텍스처 특징.

    Returns:
        밀도 통계 (평균, 표준편차, 범위, 집중도, 중심/테두리 비, 대칭도).
    """
    density = compute_edge_density_map(image, grid_size)

    d_mean = float(density.mean())
    d_std = float(density.std())
    d_max = float(density.max())
    d_min = float(density.min())

    # 상위 25% 셀의 밀도 합 / 전체
    flat = density.flatten()
    total = flat.sum()
    sorted_d = np.sort(flat)[::-1]
    top25 = sorted_d[: max(1, len(sorted_d) // 4)]
    concentration = float(top25.sum() / total) if total > 0 else 0.0

    # 중앙 vs 테두리
    g = grid_size
    if g >= 4:
        center = density[1:g-1, 1:g-1]
        border_mask = np.ones_like(density, dtype=bool)
        border_mask[1:g-1, 1:g-1] = False
        border = density[border_mask]
        center_mean = float(center.mean()) if center.size > 0 else 0
        border_mean = float(border.mean()) if border.size > 0 else 0
        cvb = center_mean / border_mean if border_mean > 0 else 1.0
    else:
        cvb = 1.0

    # 좌/우 대칭
    left = density[:, :g//2]
    right = density[:, g//2:][:, ::-1]
    min_w = min(left.shape[1], right.shape[1])
    h_sym = 1.0 - float(np.mean(np.abs(left[:, :min_w] - right[:, :min_w])))

    # 상/하 대칭
    top = density[:g//2, :]
    bot = density[g//2:, :][::-1, :]
    min_h = min(top.shape[0], bot.shape[0])
    v_sym = 1.0 - float(np.mean(np.abs(top[:min_h, :] - bot[:min_h, :])))

    return {
        "density_mean": d_mean,
        "density_std": d_std,
        "density_max": d_max,
        "density_min": d_min,
        "density_range": d_max - d_min,
        "density_concentration": concentration,
        "center_vs_border": cvb,
        "horizontal_symmetry": h_sym,
        "vertical_symmetry": v_sym,
    }


def compute_gradient_features(image: np.ndarray) -> dict[str, float]:
    """그래디언트 기반 특징 추출.

    Returns:
        magnitude/direction의 평균, 표준편차, 주방향, 방향 엔트로피.
    """
    gray = _validate_gray(image)
    sx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    sy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    magnitude = np.sqrt(sx**2 + sy**2)
    direction = np.degrees(np.arctan2(sy, sx)) % 360

    # circular mean/std
    rad = np.radians(direction.flatten())
    sin_mean = np.mean(np.sin(rad))
    cos_mean = np.mean(np.cos(rad))
    circ_mean = np.degrees(np.arctan2(sin_mean, cos_mean)) % 360
    R = np.sqrt(sin_mean**2 + cos_mean**2)
    circ_std = np.degrees(np.sqrt(-2 * np.log(R + 1e-10))) if R < 1 else 0.0

    # 주방향 (히스토그램 피크)
    hist, bin_edges = np.histogram(direction.flatten(), bins=36, range=(0, 360))
    dominant = float(bin_edges[np.argmax(hist)] + 5)  # bin 중앙

    # 방향 엔트로피
    hist_norm = hist.astype(np.float64) / (hist.sum() + 1e-10)
    entropy = -np.sum(hist_norm * np.log2(hist_norm + 1e-10))

    return {
        "gradient_mean_magnitude": float(magnitude.mean()),
        "gradient_std_magnitude": float(magnitude.std()),
        "gradient_mean_direction": circ_mean,
        "gradient_std_direction": circ_std,
        "gradient_dominant_direction": dominant,
        "gradient_direction_entropy": float(entropy),
    }


def get_edge_feature_names(grid_size: int = 4, n_direction_bins: int = 8) -> list[str]:
    """에지 특징 벡터의 특징명 리스트를 반환."""
    names = []
    for r in range(grid_size):
        for c in range(grid_size):
            names.append(f"edge_density_{r}_{c}")
    for i in range(n_direction_bins):
        names.append(f"edge_dir_bin_{i}")
    names += ["edge_mean", "edge_std", "edge_max", "edge_skewness",
              "edge_kurtosis", "edge_energy", "strong_edge_ratio"]
    names += ["density_mean", "density_std", "density_max", "density_min",
              "density_range", "density_concentration", "center_vs_border",
              "horizontal_symmetry", "vertical_symmetry"]
    names += ["gradient_mean_magnitude", "gradient_std_magnitude",
              "gradient_mean_direction", "gradient_std_direction",
              "gradient_dominant_direction", "gradient_direction_entropy"]
    return names


def extract_edge_feature_vector(
    image: np.ndarray, grid_size: int = 4, n_direction_bins: int = 8
) -> np.ndarray:
    """ML 분류용 최종 에지 특징 벡터 추출.

    Returns:
        np.ndarray (shape: (46,) 기본 설정 기준).
    """
    density_map = compute_edge_density_map(image, grid_size).flatten()
    dir_hist = compute_edge_direction_histogram(image, n_direction_bins)
    intensity = compute_edge_intensity_stats(image)
    texture = compute_edge_texture_features(image, grid_size)
    gradient = compute_gradient_features(image)

    vec = np.concatenate([
        density_map,
        dir_hist,
        np.array([intensity["edge_mean"], intensity["edge_std"], intensity["edge_max"],
                   intensity["edge_skewness"], intensity["edge_kurtosis"],
                   intensity["edge_energy"], intensity["strong_edge_ratio"]]),
        np.array([texture["density_mean"], texture["density_std"], texture["density_max"],
                   texture["density_min"], texture["density_range"],
                   texture["density_concentration"], texture["center_vs_border"],
                   texture["horizontal_symmetry"], texture["vertical_symmetry"]]),
        np.array([gradient["gradient_mean_magnitude"], gradient["gradient_std_magnitude"],
                   gradient["gradient_mean_direction"], gradient["gradient_std_direction"],
                   gradient["gradient_dominant_direction"], gradient["gradient_direction_entropy"]]),
    ])

    # NaN/Inf 안전 처리
    vec = np.nan_to_num(vec, nan=0.0, posinf=0.0, neginf=0.0)
    return vec


def batch_extract_edge_features(
    images: np.ndarray, grid_size: int = 4, n_direction_bins: int = 8
) -> np.ndarray:
    """여러 이미지에 대해 일괄 에지 특징 추출.

    Args:
        images: (N, H, W) shape 배열.

    Returns:
        (N, feature_dim) shape 특징 행렬.
    """
    n = len(images)
    first = extract_edge_feature_vector(images[0], grid_size, n_direction_bins)
    dim = len(first)
    features = np.zeros((n, dim), dtype=np.float64)
    features[0] = first

    for i in range(1, n):
        features[i] = extract_edge_feature_vector(images[i], grid_size, n_direction_bins)
        if (i + 1) % 300 == 0 or i == n - 1:
            print(f"  에지 특징 추출: {i+1}/{n} ({(i+1)*100//n}%)")

    return features


if __name__ == "__main__":
    import os, sys
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    from utils.data_loader import NEUDataLoader

    loader = NEUDataLoader(os.path.join(project_root, "data", "NEU-DET"))
    samples = loader.get_sample_images(n_per_class=1)

    print("\n=== edge_features.py 테스트 ===")
    names = get_edge_feature_names()
    print(f"특징 이름 수: {len(names)}")

    for cn in loader.class_names:
        vec = extract_edge_feature_vector(samples[cn][0])
        grad = compute_gradient_features(samples[cn][0])
        print(f"  {cn:20s}: vec_dim={vec.shape[0]}  entropy={grad['gradient_direction_entropy']:.3f}  "
              f"dominant_dir={grad['gradient_dominant_direction']:.0f}°")

    print("✅ edge_features.py 테스트 완료")

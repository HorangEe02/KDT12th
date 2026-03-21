"""픽셀 통계 특징 추출 모듈.

이미지의 전역적 밝기 분포, GLCM 텍스처, 공간 분할 통계를 수치화한다.
"""

import numpy as np
import cv2
import warnings
from scipy.stats import skew, kurtosis
from skimage.feature import graycomatrix, graycoprops


def _validate_gray(image: np.ndarray) -> np.ndarray:
    if image is None:
        raise ValueError("입력 이미지가 None입니다.")
    if image.ndim == 3:
        return cv2.cvtColor(image.copy(), cv2.COLOR_BGR2GRAY)
    return image.copy()


def extract_basic_stats(image: np.ndarray) -> dict[str, float]:
    """기본 픽셀 통계.

    Returns:
        mean, std, median, min, max, range, skewness, kurtosis, energy, entropy.
    """
    gray = _validate_gray(image).astype(np.float64)
    pixels = gray.flatten()

    # 엔트로피
    hist, _ = np.histogram(pixels, bins=256, range=(0, 256))
    p = hist.astype(np.float64) / (hist.sum() + 1e-10)
    entropy = -np.sum(p * np.log2(p + 1e-10))

    return {
        "mean": float(pixels.mean()),
        "std": float(pixels.std()),
        "median": float(np.median(pixels)),
        "min": float(pixels.min()),
        "max": float(pixels.max()),
        "range": float(pixels.max() - pixels.min()),
        "skewness": float(skew(pixels)),
        "kurtosis": float(kurtosis(pixels)),
        "energy": float(np.mean(pixels ** 2)),
        "entropy": float(entropy),
    }


def extract_histogram_features(image: np.ndarray, n_bins: int = 32) -> np.ndarray:
    """밝기 히스토그램을 특징 벡터로 사용. L1 정규화.

    Returns:
        (n_bins,) shape의 정규화된 히스토그램.
    """
    gray = _validate_gray(image)
    hist, _ = np.histogram(gray.ravel(), bins=n_bins, range=(0, 256))
    hist = hist.astype(np.float64)
    total = hist.sum()
    return hist / total if total > 0 else hist


def extract_glcm_features(
    image: np.ndarray,
    distances: list[int] = None,
    angles: list[float] = None,
) -> dict[str, float]:
    """GLCM 기반 텍스처 특징.

    Returns:
        contrast, dissimilarity, homogeneity, energy, correlation, ASM.
    """
    if distances is None:
        distances = [1, 3]
    if angles is None:
        angles = [0, np.pi / 4, np.pi / 2, 3 * np.pi / 4]

    gray = _validate_gray(image)
    # 64 레벨로 양자화
    n_levels = 64
    quantized = (gray / (256 / n_levels)).astype(np.uint8)
    quantized = np.clip(quantized, 0, n_levels - 1)

    glcm = graycomatrix(quantized, distances=distances, angles=angles,
                         levels=n_levels, symmetric=True, normed=True)

    props = {}
    for prop in ["contrast", "dissimilarity", "homogeneity", "energy", "correlation", "ASM"]:
        vals = graycoprops(glcm, prop)
        props[f"glcm_{prop}"] = float(vals.mean())

    return props


def extract_spatial_stats(image: np.ndarray, grid_size: int = 4) -> np.ndarray:
    """공간 분할 통계 특징.

    Returns:
        (grid_size² × 2,) shape 벡터 (각 블록의 mean, std).
    """
    gray = _validate_gray(image).astype(np.float64)
    h, w = gray.shape
    rows = np.array_split(np.arange(h), grid_size)
    cols = np.array_split(np.arange(w), grid_size)

    stats = []
    for r_range in rows:
        for c_range in cols:
            block = gray[r_range[0]:r_range[-1]+1, c_range[0]:c_range[-1]+1]
            stats.extend([float(block.mean()), float(block.std())])

    return np.array(stats, dtype=np.float64)


def extract_pixel_feature_vector(image: np.ndarray) -> np.ndarray:
    """ML 분류용 최종 픽셀 통계 특징 벡터.

    구성: basic_stats(10) + histogram(32) + glcm(6) + spatial(32) = 80차원.

    Returns:
        np.ndarray (shape: (80,)).
    """
    basic = extract_basic_stats(image)
    hist = extract_histogram_features(image, n_bins=32)
    glcm = extract_glcm_features(image)
    spatial = extract_spatial_stats(image, grid_size=4)

    vec = np.concatenate([
        np.array([basic["mean"], basic["std"], basic["median"], basic["min"],
                   basic["max"], basic["range"], basic["skewness"], basic["kurtosis"],
                   basic["energy"], basic["entropy"]]),
        hist,
        np.array([glcm["glcm_contrast"], glcm["glcm_dissimilarity"],
                   glcm["glcm_homogeneity"], glcm["glcm_energy"],
                   glcm["glcm_correlation"], glcm["glcm_ASM"]]),
        spatial,
    ])
    return np.nan_to_num(vec, nan=0.0, posinf=0.0, neginf=0.0)


def get_pixel_feature_names() -> list[str]:
    """특징명 리스트 반환 (80개)."""
    names = ["px_mean", "px_std", "px_median", "px_min", "px_max", "px_range",
             "px_skewness", "px_kurtosis", "px_energy", "px_entropy"]
    names += [f"hist_bin_{i}" for i in range(32)]
    names += ["glcm_contrast", "glcm_dissimilarity", "glcm_homogeneity",
              "glcm_energy", "glcm_correlation", "glcm_ASM"]
    names += [f"spatial_{i//2}_{'mean' if i%2==0 else 'std'}" for i in range(32)]
    return names


def batch_extract_pixel_features(images: np.ndarray) -> np.ndarray:
    """여러 이미지에 대해 일괄 픽셀 통계 추출.

    Returns:
        (N, 80) 특징 행렬.
    """
    n = len(images)
    first = extract_pixel_feature_vector(images[0])
    features = np.zeros((n, len(first)), dtype=np.float64)
    features[0] = first

    for i in range(1, n):
        features[i] = extract_pixel_feature_vector(images[i])
        if (i + 1) % 300 == 0 or i == n - 1:
            print(f"  픽셀통계 추출: {i+1}/{n} ({(i+1)*100//n}%)")
    return features


if __name__ == "__main__":
    import os, sys
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    from utils.data_loader import NEUDataLoader

    loader = NEUDataLoader(os.path.join(project_root, "data", "NEU-DET"))
    samples = loader.get_sample_images(n_per_class=1)

    print("\n=== pixel_stats.py 테스트 ===")
    names = get_pixel_feature_names()
    print(f"특징 이름 수: {len(names)}")

    for cn in loader.class_names:
        vec = extract_pixel_feature_vector(samples[cn][0])
        basic = extract_basic_stats(samples[cn][0])
        print(f"  {cn:20s}: dim={vec.shape[0]}  mean={basic['mean']:.1f}  entropy={basic['entropy']:.2f}")
    print("✅ pixel_stats.py 테스트 완료")

"""임계값 처리 모듈.

그레이스케일 이미지를 이진(흑/백) 이미지로 변환하는 다양한 임계값 기법을 제공한다.
에지 검출과 윤곽선 분석의 전단계로, 결함 영역과 배경을 분리하는 데 핵심적 역할.
"""

import cv2
import numpy as np
import warnings
from typing import Any


def _validate_gray(image: np.ndarray) -> np.ndarray:
    if image is None:
        raise ValueError("입력 이미지가 None입니다.")
    if image.ndim == 3:
        warnings.warn("컬러→그레이스케일 변환.")
        return cv2.cvtColor(image.copy(), cv2.COLOR_BGR2GRAY)
    if image.ndim != 2:
        raise ValueError(f"ndim={image.ndim}")
    return image.copy()


def _ensure_odd(k: int, minimum: int = 3) -> int:
    k = max(k, minimum)
    return k if k % 2 == 1 else k + 1


def global_threshold(
    image: np.ndarray,
    thresh_value: int = 127,
    max_value: int = 255,
    thresh_type: int = cv2.THRESH_BINARY,
) -> tuple[np.ndarray, int]:
    """전역 고정 임계값 이진화.

    Returns:
        (이진화 이미지, 사용된 임계값).
    """
    img = _validate_gray(image)
    ret, binary = cv2.threshold(img, thresh_value, max_value, thresh_type)
    return binary, int(ret)


def otsu_threshold(
    image: np.ndarray, max_value: int = 255
) -> tuple[np.ndarray, int]:
    """Otsu 자동 임계값 결정.

    Returns:
        (이진화 이미지, Otsu가 결정한 임계값).
    """
    img = _validate_gray(image)
    ret, binary = cv2.threshold(img, 0, max_value, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary, int(ret)


def adaptive_threshold_mean(
    image: np.ndarray,
    max_value: int = 255,
    block_size: int = 11,
    C: int = 2,
) -> np.ndarray:
    """적응형 임계값 (평균 기반)."""
    img = _validate_gray(image)
    bs = _ensure_odd(block_size)
    return cv2.adaptiveThreshold(
        img, max_value, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, bs, C
    )


def adaptive_threshold_gaussian(
    image: np.ndarray,
    max_value: int = 255,
    block_size: int = 11,
    C: int = 2,
) -> np.ndarray:
    """적응형 임계값 (가우시안 가중 기반)."""
    img = _validate_gray(image)
    bs = _ensure_odd(block_size)
    return cv2.adaptiveThreshold(
        img, max_value, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, bs, C
    )


def multi_threshold(
    image: np.ndarray, thresholds: list[int] = None
) -> np.ndarray:
    """다중 임계값 (이미지를 여러 단계로 분할).

    Args:
        image: 그레이스케일 입력 이미지.
        thresholds: 임계값 리스트. 기본 [64, 128, 192].

    Returns:
        다중 레벨 이미지 (uint8).
    """
    if thresholds is None:
        thresholds = [64, 128, 192]
    img = _validate_gray(image)
    n_levels = len(thresholds) + 1
    levels = np.linspace(0, 255, n_levels + 1)[1:].astype(np.uint8)  # 구간 대표값
    indices = np.digitize(img, thresholds)
    result = np.zeros_like(img)
    for i in range(n_levels):
        result[indices == i] = levels[i] if i < len(levels) else 255
    return result


def triangle_threshold(
    image: np.ndarray, max_value: int = 255
) -> tuple[np.ndarray, int]:
    """삼각형 알고리즘 기반 임계값. 히스토그램이 한쪽으로 치우친 경우 효과적.

    Returns:
        (이진화 이미지, 결정된 임계값).
    """
    img = _validate_gray(image)
    ret, binary = cv2.threshold(img, 0, max_value, cv2.THRESH_BINARY + cv2.THRESH_TRIANGLE)
    return binary, int(ret)


def compare_thresholds(
    image: np.ndarray, block_size: int = 11
) -> dict[str, np.ndarray]:
    """모든 임계값 방법의 결과를 한번에 비교.

    Returns:
        방법명→결과 이미지 딕셔너리.
    """
    img = _validate_gray(image)
    otsu_img, _ = otsu_threshold(img)
    tri_img, _ = triangle_threshold(img)
    return {
        "original": img,
        "global_127": global_threshold(img, 127)[0],
        "otsu": otsu_img,
        "triangle": tri_img,
        "adaptive_mean": adaptive_threshold_mean(img, block_size=block_size),
        "adaptive_gaussian": adaptive_threshold_gaussian(img, block_size=block_size),
        "multi_3level": multi_threshold(img),
    }


def find_optimal_threshold(image: np.ndarray) -> dict[str, Any]:
    """이미지 특성에 따른 최적 임계값 방법 추천.

    Returns:
        추천 방법, Otsu/Triangle 임계값, 조명 균일도, 이봉성 등 분석 결과.
    """
    img = _validate_gray(image)
    _, otsu_val = otsu_threshold(img)
    _, tri_val = triangle_threshold(img)

    # 히스토그램 이봉성(bimodality) 측정
    hist = cv2.calcHist([img], [0], None, [256], [0, 256]).flatten()
    hist_norm = hist / hist.sum()
    mean = np.sum(np.arange(256) * hist_norm)
    var = np.sum(((np.arange(256) - mean) ** 2) * hist_norm)
    from scipy.stats import skew as scipy_skew, kurtosis as scipy_kurtosis
    pixels = img.flatten().astype(np.float64)
    skewness = float(scipy_skew(pixels))
    kurt = float(scipy_kurtosis(pixels))
    # 이봉성 계수 (Sarle's bimodality coefficient)
    n = len(pixels)
    bimodality = (skewness ** 2 + 1) / (kurt + 3 * (n - 1) ** 2 / ((n - 2) * (n - 3)))

    # 조명 균일도 (4등분 평균 밝기 차이)
    h, w = img.shape
    quadrants = [
        img[: h // 2, : w // 2], img[: h // 2, w // 2 :],
        img[h // 2 :, : w // 2], img[h // 2 :, w // 2 :],
    ]
    q_means = [float(q.mean()) for q in quadrants]
    uniformity = 1.0 - (max(q_means) - min(q_means)) / 255.0

    # 추천
    if bimodality > 0.555:
        recommended = "otsu"
    elif abs(skewness) > 1.0:
        recommended = "triangle"
    elif uniformity < 0.85:
        recommended = "adaptive_gaussian"
    else:
        recommended = "otsu"

    return {
        "recommended_method": recommended,
        "otsu_threshold": otsu_val,
        "triangle_threshold": tri_val,
        "illumination_uniformity": round(uniformity, 4),
        "histogram_bimodality": round(bimodality, 4),
        "skewness": round(skewness, 4),
    }


if __name__ == "__main__":
    import os, sys
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    from utils.data_loader import NEUDataLoader

    loader = NEUDataLoader(os.path.join(project_root, "data", "NEU-DET"))
    samples = loader.get_sample_images(n_per_class=1)

    print("\n=== thresholding.py 테스트 ===")
    for cn in loader.class_names:
        info = find_optimal_threshold(samples[cn][0])
        print(f"  {cn:20s}: 추천={info['recommended_method']:18s} otsu={info['otsu_threshold']:3d}  bimodal={info['histogram_bimodality']:.4f}  uniform={info['illumination_uniformity']:.4f}")
    print("✅ thresholding.py 테스트 완료")

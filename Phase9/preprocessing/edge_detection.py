"""에지 검출 모듈.

Canny, Sobel, Laplacian, Scharr, LoG 등 다양한 에지 검출 방법과
멀티스케일 에지, 에지 방향 맵, 에지 결합 기능을 제공한다.
"""

import cv2
import numpy as np
import warnings
import math
from typing import Union


def _validate_gray(image: np.ndarray) -> np.ndarray:
    if image is None:
        raise ValueError("입력 이미지가 None입니다.")
    if image.ndim == 3:
        return cv2.cvtColor(image.copy(), cv2.COLOR_BGR2GRAY)
    if image.ndim != 2:
        raise ValueError(f"ndim={image.ndim}")
    return image.copy()


def canny_edge(
    image: np.ndarray,
    low_threshold: int = 50,
    high_threshold: int = 150,
    aperture_size: int = 3,
) -> np.ndarray:
    """Canny 에지 검출.

    Returns:
        에지 이진 이미지 (0 또는 255).
    """
    img = _validate_gray(image)
    return cv2.Canny(img, low_threshold, high_threshold, apertureSize=aperture_size)


def auto_canny(
    image: np.ndarray, sigma: float = 0.33
) -> tuple[np.ndarray, int, int]:
    """자동 임계값 Canny 에지 검출.

    이미지 중앙값 기반으로 최적 임계값을 자동 결정.

    Returns:
        (에지 이미지, low_threshold, high_threshold).
    """
    img = _validate_gray(image)
    median = float(np.median(img))
    low = max(0, int((1.0 - sigma) * median))
    high = min(255, int((1.0 + sigma) * median))
    edges = cv2.Canny(img, low, high)
    return edges, low, high


def sobel_edge(
    image: np.ndarray,
    dx: int = 1,
    dy: int = 1,
    ksize: int = 3,
    combine_method: str = "magnitude",
) -> Union[np.ndarray, tuple[np.ndarray, np.ndarray]]:
    """Sobel 에지 검출 (방향성 에지).

    Args:
        combine_method: "magnitude", "x_only", "y_only", "both_separate".

    Returns:
        에지 이미지 (0~255). "both_separate"이면 (sobel_x, sobel_y) 튜플.
    """
    img = _validate_gray(image)
    sobel_x = cv2.Sobel(img, cv2.CV_64F, 1, 0, ksize=ksize)
    sobel_y = cv2.Sobel(img, cv2.CV_64F, 0, 1, ksize=ksize)

    if combine_method == "x_only":
        return cv2.convertScaleAbs(sobel_x)
    elif combine_method == "y_only":
        return cv2.convertScaleAbs(sobel_y)
    elif combine_method == "both_separate":
        return cv2.convertScaleAbs(sobel_x), cv2.convertScaleAbs(sobel_y)
    else:  # magnitude
        magnitude = np.sqrt(sobel_x ** 2 + sobel_y ** 2)
        return np.clip(magnitude, 0, 255).astype(np.uint8)


def laplacian_edge(image: np.ndarray, ksize: int = 3) -> np.ndarray:
    """라플라시안 에지 검출 (2차 미분, 방향성 없음).

    Returns:
        0~255 정규화된 에지 이미지.
    """
    img = _validate_gray(image)
    lap = cv2.Laplacian(img, cv2.CV_64F, ksize=ksize)
    return cv2.convertScaleAbs(lap)


def scharr_edge(
    image: np.ndarray, combine_method: str = "magnitude"
) -> np.ndarray:
    """Scharr 에지 검출 (Sobel 개선 버전).

    Returns:
        0~255 정규화된 에지 이미지.
    """
    img = _validate_gray(image)
    scharr_x = cv2.Scharr(img, cv2.CV_64F, 1, 0)
    scharr_y = cv2.Scharr(img, cv2.CV_64F, 0, 1)

    if combine_method == "x_only":
        return cv2.convertScaleAbs(scharr_x)
    elif combine_method == "y_only":
        return cv2.convertScaleAbs(scharr_y)
    else:
        magnitude = np.sqrt(scharr_x ** 2 + scharr_y ** 2)
        return np.clip(magnitude, 0, 255).astype(np.uint8)


def log_edge(
    image: np.ndarray, sigma: float = 1.0, threshold: int = 0
) -> np.ndarray:
    """Laplacian of Gaussian (LoG) 에지 검출.

    Returns:
        에지 이진 이미지.
    """
    img = _validate_gray(image)
    ksize = int(6 * sigma + 1)
    if ksize % 2 == 0:
        ksize += 1
    blurred = cv2.GaussianBlur(img, (ksize, ksize), sigma)
    lap = cv2.Laplacian(blurred, cv2.CV_64F)
    result = cv2.convertScaleAbs(lap)
    if threshold > 0:
        _, result = cv2.threshold(result, threshold, 255, cv2.THRESH_BINARY)
    return result


def multi_scale_edge(
    image: np.ndarray,
    method: str = "canny",
    scales: list[float] = None,
) -> dict[float, np.ndarray]:
    """멀티스케일 에지 검출.

    Args:
        method: "canny" (auto_canny 사용).
        scales: 블러 sigma 리스트. 기본 [0.5, 1.0, 2.0].

    Returns:
        {scale: edge_image} 딕셔너리.
    """
    if scales is None:
        scales = [0.5, 1.0, 2.0]
    img = _validate_gray(image)
    results = {}
    for s in scales:
        ksize = max(3, int(6 * s + 1))
        if ksize % 2 == 0:
            ksize += 1
        blurred = cv2.GaussianBlur(img, (ksize, ksize), s)
        if method == "canny":
            edge, _, _ = auto_canny(blurred)
        else:
            edge = sobel_edge(blurred)
        results[s] = edge
    return results


def edge_direction_map(
    image: np.ndarray, ksize: int = 3
) -> tuple[np.ndarray, np.ndarray]:
    """에지 방향 맵 생성.

    Returns:
        (magnitude_map, direction_map_degrees).
        direction은 0~360도.
    """
    img = _validate_gray(image)
    sobel_x = cv2.Sobel(img, cv2.CV_64F, 1, 0, ksize=ksize)
    sobel_y = cv2.Sobel(img, cv2.CV_64F, 0, 1, ksize=ksize)
    magnitude = np.sqrt(sobel_x ** 2 + sobel_y ** 2)
    direction = np.degrees(np.arctan2(sobel_y, sobel_x)) % 360
    return magnitude, direction


def combine_edges(
    edge_images: list[np.ndarray], method: str = "union"
) -> np.ndarray:
    """여러 에지 검출 결과를 결합.

    Args:
        method: "union" (OR), "intersection" (AND), "weighted" (가중 평균).

    Returns:
        결합된 에지 이미지.
    """
    if not edge_images:
        raise ValueError("빈 리스트입니다.")

    if method == "union":
        result = edge_images[0].copy()
        for e in edge_images[1:]:
            result = cv2.bitwise_or(result, e)
        return result
    elif method == "intersection":
        result = edge_images[0].copy()
        for e in edge_images[1:]:
            result = cv2.bitwise_and(result, e)
        return result
    elif method == "weighted":
        acc = np.zeros_like(edge_images[0], dtype=np.float64)
        for e in edge_images:
            acc += e.astype(np.float64)
        acc /= len(edge_images)
        _, result = cv2.threshold(
            np.clip(acc, 0, 255).astype(np.uint8), 127, 255, cv2.THRESH_BINARY
        )
        return result
    else:
        raise ValueError(f"지원하지 않는 method: {method}")


def compare_edge_methods(image: np.ndarray) -> dict[str, np.ndarray]:
    """모든 에지 검출 방법의 결과를 한번에 비교.

    Returns:
        방법명→결과 이미지 딕셔너리.
    """
    img = _validate_gray(image)
    auto_edge, _, _ = auto_canny(img)
    return {
        "original": img,
        "canny_auto": auto_edge,
        "canny_tight": canny_edge(img, 100, 200),
        "canny_wide": canny_edge(img, 30, 100),
        "sobel_magnitude": sobel_edge(img, combine_method="magnitude"),
        "sobel_x": sobel_edge(img, combine_method="x_only"),
        "sobel_y": sobel_edge(img, combine_method="y_only"),
        "laplacian": laplacian_edge(img),
        "scharr": scharr_edge(img),
        "log_sigma1": log_edge(img, sigma=1.0),
        "log_sigma2": log_edge(img, sigma=2.0),
    }


def evaluate_edge_quality(
    original: np.ndarray, edge: np.ndarray
) -> dict[str, float]:
    """에지 검출 결과의 품질 평가.

    Returns:
        에지 밀도, 연속성, 개수, 평균 강도, 균일도 등.
    """
    orig = _validate_gray(original)
    e = edge.copy()

    # 에지 밀도
    edge_density = float(np.mean(e > 0))

    # 윤곽선 기반 연속성
    binary = (e > 0).astype(np.uint8) * 255
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    edge_count = len(contours)
    if contours:
        lengths = [cv2.arcLength(c, False) for c in contours]
        edge_continuity = float(np.mean(lengths))
    else:
        edge_continuity = 0.0

    # 에지 부분 Sobel magnitude 평균
    mag, _ = edge_direction_map(orig)
    edge_mask = e > 0
    mean_strength = float(mag[edge_mask].mean()) if edge_mask.any() else 0.0

    # 공간 균일도 (4분면)
    h, w = e.shape
    quads = [
        e[: h // 2, : w // 2], e[: h // 2, w // 2 :],
        e[h // 2 :, : w // 2], e[h // 2 :, w // 2 :],
    ]
    q_densities = [float(np.mean(q > 0)) for q in quads]
    max_d = max(q_densities)
    edge_uniformity = min(q_densities) / max_d if max_d > 0 else 1.0

    return {
        "edge_density": edge_density,
        "edge_continuity": edge_continuity,
        "edge_count": edge_count,
        "mean_edge_strength": mean_strength,
        "edge_uniformity": edge_uniformity,
    }


if __name__ == "__main__":
    import os, sys
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    from utils.data_loader import NEUDataLoader

    loader = NEUDataLoader(os.path.join(project_root, "data", "NEU-DET"))
    samples = loader.get_sample_images(n_per_class=1)

    print("\n=== edge_detection.py 테스트 ===")
    img = samples["scratches"][0]

    results = compare_edge_methods(img)
    for name, r in results.items():
        d = float(np.mean(r > 0)) if name != "original" else 0
        print(f"  {name:16s}: shape={r.shape}  density={d:.4f}")

    auto_e, lo, hi = auto_canny(img)
    print(f"\nauto_canny: low={lo}, high={hi}")

    q = evaluate_edge_quality(img, auto_e)
    print(f"quality: {q}")

    mag, dirn = edge_direction_map(img)
    print(f"direction_map: mag_mean={mag.mean():.1f}, dir_mean={dirn.mean():.1f}")

    print("✅ edge_detection.py 테스트 완료")

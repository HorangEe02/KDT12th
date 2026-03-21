"""윤곽선 기반 특징 추출 모듈.

이진화된 이미지에서 윤곽선을 검출하고, 면적/둘레/원형도/종횡비/볼록도 등
수치적 특징을 추출하여 ML 분류의 특징 벡터로 활용한다.
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


def find_contours(
    image: np.ndarray,
    threshold_method: str = "otsu",
    min_area: int = 5,
) -> tuple[list, np.ndarray]:
    """이미지에서 윤곽선 검출.

    Args:
        image: 그레이스케일 입력 이미지.
        threshold_method: "otsu", "adaptive_mean", "adaptive_gaussian", "canny".
        min_area: 최소 윤곽선 면적 (이하 필터링).

    Returns:
        (contours 리스트, 사용된 이진 이미지).
    """
    gray = _validate_gray(image)

    if threshold_method == "otsu":
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    elif threshold_method == "adaptive_mean":
        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 2)
    elif threshold_method == "adaptive_gaussian":
        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    elif threshold_method == "canny":
        median = float(np.median(gray))
        lo = max(0, int(0.67 * median))
        hi = min(255, int(1.33 * median))
        binary = cv2.Canny(gray, lo, hi)
    else:
        raise ValueError(f"지원하지 않는 method: {threshold_method}")

    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = [c for c in contours if cv2.contourArea(c) >= min_area]
    return contours, binary


def compute_contour_stats(contour: np.ndarray) -> dict[str, float]:
    """단일 윤곽선의 기하학적 특징 계산.

    Returns:
        면적, 둘레, 원형도, 종횡비, extent, 볼록도, 등가지름, 방향, bbox, Hu Moments.
    """
    area = cv2.contourArea(contour)
    perimeter = cv2.arcLength(contour, True)

    circularity = (4 * math.pi * area / (perimeter ** 2)) if perimeter > 0 else 0.0

    x, y, w, h = cv2.boundingRect(contour)
    aspect_ratio = float(w) / h if h > 0 else 0.0
    extent = area / (w * h) if w * h > 0 else 0.0

    hull = cv2.convexHull(contour)
    hull_area = cv2.contourArea(hull)
    solidity = area / hull_area if hull_area > 0 else 0.0

    equiv_diameter = math.sqrt(4 * area / math.pi) if area > 0 else 0.0

    orientation = 0.0
    if len(contour) >= 5:
        try:
            _, _, angle = cv2.fitEllipse(contour)
            orientation = angle
        except cv2.error:
            pass

    moments = cv2.moments(contour)
    hu = cv2.HuMoments(moments).flatten()

    return {
        "area": float(area),
        "perimeter": float(perimeter),
        "circularity": circularity,
        "aspect_ratio": aspect_ratio,
        "extent": extent,
        "solidity": solidity,
        "equiv_diameter": equiv_diameter,
        "orientation": orientation,
        "bounding_rect": (x, y, w, h),
        "hu_moments": hu,
    }


def compute_image_contour_features(
    image: np.ndarray,
    threshold_method: str = "otsu",
    min_area: int = 5,
    top_n: int = 10,
) -> dict[str, float]:
    """이미지 전체의 윤곽선 기반 통합 특징 벡터 추출.

    Returns:
        윤곽선 수, 총면적, 면적비, 평균/표준편차(면적, 둘레, 원형도, 종횡비, 볼록도, extent),
        윤곽선 밀도, 가장 큰 윤곽선의 Hu Moments.
    """
    contours, _ = find_contours(image, threshold_method, min_area)

    img_area = image.shape[0] * image.shape[1]

    if len(contours) == 0:
        return {
            "contour_count": 0, "total_contour_area": 0.0,
            "contour_area_ratio": 0.0,
            "mean_area": 0.0, "std_area": 0.0, "max_area": 0.0,
            "mean_perimeter": 0.0, "std_perimeter": 0.0,
            "mean_circularity": 0.0, "std_circularity": 0.0,
            "mean_aspect_ratio": 0.0, "std_aspect_ratio": 0.0,
            "mean_solidity": 0.0, "std_solidity": 0.0,
            "mean_extent": 0.0,
            "contour_density": 0.0,
            "largest_contour_hu_moments": np.zeros(7),
        }

    # 면적 기준 정렬, top_n 선택
    contours_sorted = sorted(contours, key=cv2.contourArea, reverse=True)[:top_n]
    stats = [compute_contour_stats(c) for c in contours_sorted]

    areas = [s["area"] for s in stats]
    perimeters = [s["perimeter"] for s in stats]
    circularities = [s["circularity"] for s in stats]
    aspect_ratios = [s["aspect_ratio"] for s in stats]
    solidities = [s["solidity"] for s in stats]
    extents = [s["extent"] for s in stats]

    return {
        "contour_count": len(contours),
        "total_contour_area": sum(areas),
        "contour_area_ratio": sum(areas) / img_area,
        "mean_area": float(np.mean(areas)),
        "std_area": float(np.std(areas)),
        "max_area": float(max(areas)),
        "mean_perimeter": float(np.mean(perimeters)),
        "std_perimeter": float(np.std(perimeters)),
        "mean_circularity": float(np.mean(circularities)),
        "std_circularity": float(np.std(circularities)),
        "mean_aspect_ratio": float(np.mean(aspect_ratios)),
        "std_aspect_ratio": float(np.std(aspect_ratios)),
        "mean_solidity": float(np.mean(solidities)),
        "std_solidity": float(np.std(solidities)),
        "mean_extent": float(np.mean(extents)),
        "contour_density": len(contours) / img_area * 1000,
        "largest_contour_hu_moments": stats[0]["hu_moments"],
    }


def visualize_contours(
    image: np.ndarray, contours: list, top_n: int = 10
) -> np.ndarray:
    """윤곽선을 원본 이미지 위에 컬러로 시각화.

    Returns:
        윤곽선이 표시된 BGR 컬러 이미지.
    """
    gray = _validate_gray(image)
    vis = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    contours_sorted = sorted(contours, key=cv2.contourArea, reverse=True)[:top_n]

    colors = [
        (0, 255, 0), (255, 0, 0), (0, 0, 255), (255, 255, 0),
        (255, 0, 255), (0, 255, 255), (128, 255, 0), (255, 128, 0),
        (128, 0, 255), (0, 128, 255),
    ]

    for i, c in enumerate(contours_sorted):
        color = colors[i % len(colors)]
        cv2.drawContours(vis, [c], -1, color, 1)

    # 가장 큰 윤곽선 bbox
    if contours_sorted:
        x, y, w, h = cv2.boundingRect(contours_sorted[0])
        cv2.rectangle(vis, (x, y), (x + w, y + h), (0, 0, 255), 2)

    return vis


def contour_hierarchy_analysis(
    image: np.ndarray, threshold_method: str = "otsu"
) -> dict[str, int]:
    """윤곽선 계층 구조 분석.

    Returns:
        총 윤곽선 수, 외곽선 수, 내부 윤곽선 수, 최대 중첩 깊이, 내부/외부 비율.
    """
    gray = _validate_gray(image)
    if threshold_method == "otsu":
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    else:
        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

    contours, hierarchy = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    if hierarchy is None or len(contours) == 0:
        return {"total_contours": 0, "external_contours": 0, "internal_contours": 0,
                "max_hierarchy_depth": 0, "hierarchy_ratio": 0.0}

    h = hierarchy[0]  # shape: (N, 4) — [next, prev, child, parent]
    external = sum(1 for i in range(len(h)) if h[i][3] == -1)
    internal = len(h) - external

    # 최대 깊이 계산
    depths = []
    for i in range(len(h)):
        depth = 0
        parent = h[i][3]
        while parent != -1:
            depth += 1
            parent = h[parent][3]
        depths.append(depth)
    max_depth = max(depths) if depths else 0

    return {
        "total_contours": len(contours),
        "external_contours": external,
        "internal_contours": internal,
        "max_hierarchy_depth": max_depth,
        "hierarchy_ratio": internal / external if external > 0 else 0.0,
    }


def get_contour_feature_names() -> list[str]:
    """윤곽선 특징 벡터의 특징명 리스트를 반환."""
    names = [
        "contour_count", "total_contour_area", "contour_area_ratio",
        "mean_area", "std_area", "max_area",
        "mean_perimeter", "std_perimeter",
        "mean_circularity", "std_circularity",
        "mean_aspect_ratio", "std_aspect_ratio",
        "mean_solidity", "std_solidity", "mean_extent",
        "contour_density",
    ]
    names += [f"hu_moment_{i}" for i in range(7)]
    names += ["total_contours_h", "external_contours", "internal_contours",
              "max_hierarchy_depth", "hierarchy_ratio"]
    return names


def extract_contour_feature_vector(
    image: np.ndarray, threshold_method: str = "otsu"
) -> np.ndarray:
    """ML 분류용 최종 윤곽선 특징 벡터 추출.

    Returns:
        고정 길이 1D numpy 배열 (~28차원).
    """
    feat = compute_image_contour_features(image, threshold_method)
    hier = contour_hierarchy_analysis(image, threshold_method)

    # Hu moments log 변환
    hu = feat["largest_contour_hu_moments"]
    hu_log = -np.sign(hu) * np.log10(np.abs(hu) + 1e-10)

    vec = [
        feat["contour_count"], feat["total_contour_area"], feat["contour_area_ratio"],
        feat["mean_area"], feat["std_area"], feat["max_area"],
        feat["mean_perimeter"], feat["std_perimeter"],
        feat["mean_circularity"], feat["std_circularity"],
        feat["mean_aspect_ratio"], feat["std_aspect_ratio"],
        feat["mean_solidity"], feat["std_solidity"], feat["mean_extent"],
        feat["contour_density"],
    ]
    vec.extend(hu_log.tolist())
    vec.extend([
        hier["total_contours"], hier["external_contours"], hier["internal_contours"],
        hier["max_hierarchy_depth"], hier["hierarchy_ratio"],
    ])

    return np.array(vec, dtype=np.float64)


if __name__ == "__main__":
    import os, sys
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    from utils.data_loader import NEUDataLoader

    loader = NEUDataLoader(os.path.join(project_root, "data", "NEU-DET"))
    samples = loader.get_sample_images(n_per_class=1)

    print("\n=== contour_features.py 테스트 ===")
    names = get_contour_feature_names()
    print(f"특징 이름 수: {len(names)}")

    for cn in loader.class_names:
        vec = extract_contour_feature_vector(samples[cn][0])
        feat = compute_image_contour_features(samples[cn][0])
        print(f"  {cn:20s}: vec_dim={vec.shape[0]:2d}  contours={feat['contour_count']:3d}  "
              f"circ={feat['mean_circularity']:.3f}  ar={feat['mean_aspect_ratio']:.3f}")

    print("✅ contour_features.py 테스트 완료")

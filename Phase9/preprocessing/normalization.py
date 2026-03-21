"""밝기/대비 정규화 모듈.

금속 표면 이미지의 밝기와 대비를 정규화하여 이미지 간 일관성을 확보한다.
히스토그램 균등화, CLAHE, 감마 보정 등 다양한 정규화 방법을 제공.
"""

import cv2
import numpy as np
import warnings
from typing import Optional


def _validate_image(image: np.ndarray) -> np.ndarray:
    """입력 이미지 유효성 검사 및 그레이스케일 변환.

    Returns:
        그레이스케일 이미지 복사본.
    """
    if image is None:
        raise ValueError("입력 이미지가 None입니다.")
    if image.ndim == 3:
        warnings.warn("컬러 이미지를 그레이스케일로 변환합니다.")
        return cv2.cvtColor(image.copy(), cv2.COLOR_BGR2GRAY)
    if image.ndim != 2:
        raise ValueError(f"이미지 차원이 올바르지 않습니다: ndim={image.ndim}")
    return image.copy()


def histogram_equalization(image: np.ndarray) -> np.ndarray:
    """글로벌 히스토그램 균등화.

    전체 이미지의 밝기 분포를 균등하게 펼친다.

    Args:
        image: 그레이스케일 입력 이미지.

    Returns:
        균등화된 이미지.
    """
    img = _validate_image(image)
    return cv2.equalizeHist(img)


def clahe_equalization(
    image: np.ndarray,
    clip_limit: float = 2.0,
    tile_grid_size: tuple = (8, 8),
) -> np.ndarray:
    """적응형 히스토그램 균등화 (CLAHE).

    글로벌 균등화보다 국소 대비 개선에 효과적이며,
    금속 표면 결함 강조에 가장 적합한 정규화 방법.

    Args:
        image: 그레이스케일 입력 이미지.
        clip_limit: 대비 증폭 제한 (기본 2.0).
        tile_grid_size: 타일 크기 (기본 8x8).

    Returns:
        CLAHE 적용된 이미지.
    """
    img = _validate_image(image)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    return clahe.apply(img)


def min_max_normalize(
    image: np.ndarray, target_min: int = 0, target_max: int = 255
) -> np.ndarray:
    """Min-Max 정규화.

    이미지의 최솟값→target_min, 최댓값→target_max로 선형 스케일링.

    Args:
        image: 그레이스케일 입력 이미지.
        target_min: 출력 최솟값.
        target_max: 출력 최댓값.

    Returns:
        정규화된 이미지.
    """
    img = _validate_image(image).astype(np.float64)
    mn, mx = img.min(), img.max()
    if mx - mn == 0:
        return np.full_like(image, target_min, dtype=np.uint8)
    normalized = (img - mn) / (mx - mn) * (target_max - target_min) + target_min
    return np.clip(normalized, 0, 255).astype(np.uint8)


def standardize(image: np.ndarray) -> np.ndarray:
    """Z-score 표준화 (평균 0, 표준편차 1).

    결과를 0~255 범위로 재매핑하여 uint8로 반환.

    Args:
        image: 그레이스케일 입력 이미지.

    Returns:
        표준화된 이미지 (uint8).
    """
    img = _validate_image(image).astype(np.float64)
    mean, std = img.mean(), img.std()
    if std == 0:
        warnings.warn("표준편차가 0입니다(단색 이미지). 128로 채운 이미지를 반환합니다.")
        return np.full_like(image, 128, dtype=np.uint8)
    z = (img - mean) / std
    # z-score를 0~255로 재매핑 (±3σ 범위를 0~255로)
    rescaled = (z + 3) / 6 * 255
    return np.clip(rescaled, 0, 255).astype(np.uint8)


def gamma_correction(image: np.ndarray, gamma: float = 1.0) -> np.ndarray:
    """감마 보정을 통한 밝기 조정.

    Args:
        image: 그레이스케일 입력 이미지.
        gamma: 감마 값. <1이면 밝게, >1이면 어둡게.

    Returns:
        감마 보정된 이미지.
    """
    img = _validate_image(image)
    inv_gamma = 1.0 / gamma if gamma != 0 else 1.0
    table = np.array(
        [((i / 255.0) ** inv_gamma) * 255 for i in range(256)], dtype=np.uint8
    )
    return cv2.LUT(img, table)


def auto_brightness_contrast(
    image: np.ndarray, clip_hist_percent: float = 1.0
) -> np.ndarray:
    """자동 밝기/대비 조정.

    히스토그램의 상/하위 clip_hist_percent%를 클리핑하여 최적 범위를 결정.

    Args:
        image: 그레이스케일 입력 이미지.
        clip_hist_percent: 클리핑 비율 (기본 1.0%).

    Returns:
        밝기/대비 조정된 이미지.
    """
    img = _validate_image(image)

    # 히스토그램 계산
    hist = cv2.calcHist([img], [0], None, [256], [0, 256]).flatten()
    total = img.size
    accumulator = np.cumsum(hist)

    # 하위 클리핑
    clip_amount = total * clip_hist_percent / 100.0
    min_val = 0
    while accumulator[min_val] < clip_amount:
        min_val += 1

    # 상위 클리핑
    max_val = 255
    while accumulator[max_val] >= (total - clip_amount):
        max_val -= 1
        if max_val <= min_val:
            break

    if max_val <= min_val:
        return img

    # alpha(대비), beta(밝기) 계산
    alpha = 255.0 / (max_val - min_val)
    beta = -min_val * alpha

    return cv2.convertScaleAbs(img, alpha=alpha, beta=beta)


def normalize_pipeline(
    image: np.ndarray, method: str = "clahe", **kwargs
) -> np.ndarray:
    """정규화 방법을 문자열로 선택하여 적용하는 통합 함수.

    Args:
        image: 그레이스케일 입력 이미지.
        method: 정규화 방법. "histogram", "clahe", "minmax",
                "standardize", "gamma", "auto" 중 택 1.
        **kwargs: 각 방법의 추가 파라미터.

    Returns:
        정규화된 이미지.

    Raises:
        ValueError: 지원하지 않는 method인 경우.
    """
    methods = {
        "histogram": histogram_equalization,
        "clahe": clahe_equalization,
        "minmax": min_max_normalize,
        "standardize": standardize,
        "gamma": gamma_correction,
        "auto": auto_brightness_contrast,
    }
    if method not in methods:
        raise ValueError(f"지원하지 않는 method: {method}. 가능: {list(methods.keys())}")

    return methods[method](image, **kwargs)


def compare_normalizations(image: np.ndarray) -> dict[str, np.ndarray]:
    """모든 정규화 방법의 결과를 한번에 비교.

    Args:
        image: 그레이스케일 입력 이미지.

    Returns:
        방법명→결과 이미지 딕셔너리.
    """
    img = _validate_image(image)
    return {
        "original": img,
        "histogram_eq": histogram_equalization(img),
        "clahe": clahe_equalization(img),
        "minmax": min_max_normalize(img),
        "standardize": standardize(img),
        "gamma_0.5": gamma_correction(img, 0.5),
        "gamma_1.5": gamma_correction(img, 1.5),
        "auto": auto_brightness_contrast(img),
    }


if __name__ == "__main__":
    import os, sys

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    from utils.data_loader import NEUDataLoader

    data_dir = os.path.join(project_root, "data", "NEU-DET")
    loader = NEUDataLoader(data_dir)

    print("\n=== normalization.py 테스트 ===")
    samples = loader.get_sample_images(n_per_class=1)

    for cn, imgs in samples.items():
        img = imgs[0]
        results = compare_normalizations(img)
        stats = {k: f"mean={v.mean():.1f}, std={v.std():.1f}" for k, v in results.items()}
        print(f"\n  [{cn}]")
        for method, s in stats.items():
            print(f"    {method:16s}: {s}")

    print("\n✅ normalization.py 테스트 완료")

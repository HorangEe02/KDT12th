"""블러 및 노이즈 제거 필터 모듈.

금속 표면 이미지의 노이즈를 제거하면서 결함의 핵심 특징(경계, 형태)을
최대한 보존하는 다양한 블러 방법을 제공한다.
"""

import cv2
import numpy as np
import warnings
from typing import Optional


def _validate_image(image: np.ndarray) -> np.ndarray:
    """입력 이미지 유효성 검사 및 그레이스케일 보장."""
    if image is None:
        raise ValueError("입력 이미지가 None입니다.")
    if image.ndim == 3:
        warnings.warn("컬러 이미지를 그레이스케일로 변환합니다.")
        return cv2.cvtColor(image.copy(), cv2.COLOR_BGR2GRAY)
    if image.ndim != 2:
        raise ValueError(f"이미지 차원이 올바르지 않습니다: ndim={image.ndim}")
    return image.copy()


def _ensure_odd(k: int) -> int:
    """커널 사이즈를 홀수로 보정."""
    if k % 2 == 0:
        warnings.warn(f"커널 사이즈 {k}을 {k+1}로 보정합니다 (홀수 필요).")
        return k + 1
    return k


def gaussian_blur(
    image: np.ndarray, kernel_size: int = 5, sigma: float = 0
) -> np.ndarray:
    """가우시안 블러.

    Args:
        image: 그레이스케일 입력 이미지.
        kernel_size: 커널 크기 (홀수).
        sigma: 가우시안 시그마. 0이면 커널 크기에서 자동 계산.

    Returns:
        블러 처리된 이미지.
    """
    img = _validate_image(image)
    k = _ensure_odd(kernel_size)
    return cv2.GaussianBlur(img, (k, k), sigma)


def median_blur(image: np.ndarray, kernel_size: int = 5) -> np.ndarray:
    """미디안 블러. 소금-후추 노이즈에 효과적이며 에지 보존력이 우수.

    Args:
        image: 그레이스케일 입력 이미지.
        kernel_size: 커널 크기 (홀수).

    Returns:
        블러 처리된 이미지.
    """
    img = _validate_image(image)
    k = _ensure_odd(kernel_size)
    return cv2.medianBlur(img, k)


def bilateral_filter(
    image: np.ndarray,
    d: int = 9,
    sigma_color: float = 75,
    sigma_space: float = 75,
) -> np.ndarray:
    """양방향 필터. 에지를 보존하면서 노이즈를 제거.

    금속 광택 반사 제거 + 결함 경계 보존에 가장 핵심적인 필터.

    Args:
        image: 그레이스케일 입력 이미지.
        d: 필터링에 사용할 이웃 픽셀 직경.
        sigma_color: 색상 공간 시그마.
        sigma_space: 좌표 공간 시그마.

    Returns:
        필터 처리된 이미지.
    """
    img = _validate_image(image)
    return cv2.bilateralFilter(img, d, sigma_color, sigma_space)


def average_blur(image: np.ndarray, kernel_size: int = 5) -> np.ndarray:
    """평균 블러 (단순 박스 필터). 비교 실험의 베이스라인용.

    Args:
        image: 그레이스케일 입력 이미지.
        kernel_size: 커널 크기 (홀수).

    Returns:
        블러 처리된 이미지.
    """
    img = _validate_image(image)
    k = _ensure_odd(kernel_size)
    return cv2.blur(img, (k, k))


def non_local_means_denoise(
    image: np.ndarray,
    h: float = 10,
    template_window_size: int = 7,
    search_window_size: int = 21,
) -> np.ndarray:
    """비국소 평균 노이즈 제거 (NLM). 가장 정교하나 연산 시간이 김.

    Args:
        image: 그레이스케일 입력 이미지.
        h: 필터 강도.
        template_window_size: 패치 크기 (홀수).
        search_window_size: 검색 영역 크기 (홀수).

    Returns:
        노이즈 제거된 이미지.
    """
    img = _validate_image(image)
    tw = _ensure_odd(template_window_size)
    sw = _ensure_odd(search_window_size)
    return cv2.fastNlMeansDenoising(img, None, h, tw, sw)


def apply_custom_kernel(image: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    """사용자 정의 커널을 적용하는 범용 함수.

    Args:
        image: 그레이스케일 입력 이미지.
        kernel: 2D numpy 배열 (예: 3x3, 5x5).

    Returns:
        필터 적용된 이미지.
    """
    img = _validate_image(image)
    return cv2.filter2D(img, -1, kernel)


def progressive_blur(
    image: np.ndarray,
    method: str = "gaussian",
    kernel_sizes: list[int] = None,
) -> dict[int, np.ndarray]:
    """점진적 블러 강도 비교용 함수.

    Args:
        image: 그레이스케일 입력 이미지.
        method: "gaussian", "median", "average" 중 택 1.
        kernel_sizes: 커널 사이즈 리스트. 기본 [3, 5, 7, 9, 11].

    Returns:
        {kernel_size: blurred_image} 딕셔너리.
    """
    if kernel_sizes is None:
        kernel_sizes = [3, 5, 7, 9, 11]

    methods = {
        "gaussian": gaussian_blur,
        "median": median_blur,
        "average": average_blur,
    }
    if method not in methods:
        raise ValueError(f"지원하지 않는 method: {method}. 가능: {list(methods.keys())}")

    results = {}
    for k in kernel_sizes:
        results[k] = methods[method](image, kernel_size=k)
    return results


def compare_blur_methods(
    image: np.ndarray, kernel_size: int = 5
) -> dict[str, np.ndarray]:
    """동일 커널 사이즈에서 모든 블러 방법 결과를 비교.

    Args:
        image: 그레이스케일 입력 이미지.
        kernel_size: 커널 크기.

    Returns:
        방법명→결과 이미지 딕셔너리.
    """
    img = _validate_image(image)
    return {
        "original": img,
        "gaussian": gaussian_blur(img, kernel_size),
        "median": median_blur(img, kernel_size),
        "bilateral": bilateral_filter(img),
        "average": average_blur(img, kernel_size),
        "nlm": non_local_means_denoise(img),
    }


if __name__ == "__main__":
    import os, sys

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    from utils.data_loader import NEUDataLoader

    data_dir = os.path.join(project_root, "data", "NEU-DET")
    loader = NEUDataLoader(data_dir)

    print("\n=== filters.py 테스트 ===")
    samples = loader.get_sample_images(n_per_class=1)
    img = samples["scratches"][0]

    results = compare_blur_methods(img)
    for name, r in results.items():
        edge = cv2.Canny(r, 50, 150)
        density = np.mean(edge > 0)
        print(f"  {name:12s}: mean={r.mean():.1f}, std={r.std():.1f}, edge_density={density:.4f}")

    prog = progressive_blur(img, "gaussian", [3, 5, 7, 9, 11])
    print(f"\nprogressive_blur 결과: {list(prog.keys())}")
    print("✅ filters.py 테스트 완료")

"""샤프닝 및 결함 강조 모듈.

금속 표면 결함의 경계와 디테일을 강조하는 다양한 샤프닝 기법을 제공한다.
블러(노이즈 제거) → 샤프닝(결함 강조) 순서의 파이프라인을 지원.
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


def unsharp_mask(
    image: np.ndarray,
    kernel_size: int = 5,
    sigma: float = 1.0,
    amount: float = 1.5,
    threshold: int = 0,
) -> np.ndarray:
    """언샤프 마스크. 가장 범용적인 샤프닝 기법.

    Args:
        image: 그레이스케일 입력 이미지.
        kernel_size: 가우시안 블러 커널 크기 (홀수).
        sigma: 가우시안 시그마.
        amount: 샤프닝 강도 (1.0=보통, 2.0=강함).
        threshold: 노이즈 보호 임계값 (0이면 모든 픽셀에 적용).

    Returns:
        샤프닝된 이미지.
    """
    img = _validate_image(image)
    k = kernel_size if kernel_size % 2 == 1 else kernel_size + 1
    blurred = cv2.GaussianBlur(img, (k, k), sigma)

    img_f = img.astype(np.float64)
    blur_f = blurred.astype(np.float64)
    sharpened = img_f + amount * (img_f - blur_f)

    if threshold > 0:
        diff = np.abs(img_f - blur_f)
        mask = (diff >= threshold).astype(np.float64)
        sharpened = mask * sharpened + (1 - mask) * img_f

    return np.clip(sharpened, 0, 255).astype(np.uint8)


def laplacian_sharpen(
    image: np.ndarray, kernel_size: int = 3, scale: float = 1.0
) -> np.ndarray:
    """라플라시안 기반 샤프닝. 모든 방향의 에지를 균등하게 강조.

    Args:
        image: 그레이스케일 입력 이미지.
        kernel_size: 라플라시안 커널 크기 (1, 3, 5, 7).
        scale: 라플라시안 가중치.

    Returns:
        샤프닝된 이미지.
    """
    img = _validate_image(image)
    laplacian = cv2.Laplacian(img, cv2.CV_64F, ksize=kernel_size)
    sharpened = img.astype(np.float64) - scale * laplacian
    return np.clip(sharpened, 0, 255).astype(np.uint8)


def highpass_sharpen(
    image: np.ndarray, kernel_size: int = 5, alpha: float = 1.5
) -> np.ndarray:
    """고주파 통과 필터 기반 샤프닝.

    Args:
        image: 그레이스케일 입력 이미지.
        kernel_size: 가우시안 블러 커널 크기.
        alpha: 고주파 성분 가중치.

    Returns:
        샤프닝된 이미지.
    """
    img = _validate_image(image)
    k = kernel_size if kernel_size % 2 == 1 else kernel_size + 1
    low_pass = cv2.GaussianBlur(img, (k, k), 0).astype(np.float64)
    high_pass = img.astype(np.float64) - low_pass
    sharpened = img.astype(np.float64) + alpha * high_pass
    return np.clip(sharpened, 0, 255).astype(np.uint8)


def custom_sharpen_kernel(
    image: np.ndarray, strength: str = "medium"
) -> np.ndarray:
    """사전 정의된 샤프닝 커널 적용.

    Args:
        image: 그레이스케일 입력 이미지.
        strength: "light", "medium", "strong" 중 택 1.

    Returns:
        샤프닝된 이미지.
    """
    kernels = {
        "light": np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], dtype=np.float64),
        "medium": np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]], dtype=np.float64),
        "strong": np.array([[-2, -2, -2], [-2, 17, -2], [-2, -2, -2]], dtype=np.float64) / 1.0,
    }
    if strength not in kernels:
        raise ValueError(f"지원하지 않는 strength: {strength}. 가능: {list(kernels.keys())}")

    img = _validate_image(image)
    result = cv2.filter2D(img, cv2.CV_64F, kernels[strength])
    return np.clip(result, 0, 255).astype(np.uint8)


def emboss_filter(
    image: np.ndarray, direction: str = "top_left"
) -> np.ndarray:
    """엠보싱 필터. 결함의 깊이감을 시각화.

    Args:
        image: 그레이스케일 입력 이미지.
        direction: "top_left", "top_right", "bottom" 중 택 1.

    Returns:
        엠보싱 처리된 이미지.
    """
    kernels = {
        "top_left": np.array([[-2, -1, 0], [-1, 1, 1], [0, 1, 2]], dtype=np.float64),
        "top_right": np.array([[0, -1, -2], [1, 1, -1], [2, 1, 0]], dtype=np.float64),
        "bottom": np.array([[0, 1, 2], [-1, 1, 1], [-2, -1, 0]], dtype=np.float64),
    }
    if direction not in kernels:
        raise ValueError(f"지원하지 않는 direction: {direction}. 가능: {list(kernels.keys())}")

    img = _validate_image(image)
    result = cv2.filter2D(img, cv2.CV_64F, kernels[direction]) + 128
    return np.clip(result, 0, 255).astype(np.uint8)


def detail_enhance(
    image: np.ndarray, sigma_s: float = 10, sigma_r: float = 0.15
) -> np.ndarray:
    """디테일 강조. 금속 표면의 미세 텍스처를 강조.

    Args:
        image: 그레이스케일 입력 이미지.
        sigma_s: 공간적 시그마.
        sigma_r: 범위 시그마.

    Returns:
        디테일 강조된 이미지.
    """
    img = _validate_image(image)
    # detailEnhance는 3채널 필요
    color = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    enhanced = cv2.detailEnhance(color, sigma_s=sigma_s, sigma_r=sigma_r)
    return cv2.cvtColor(enhanced, cv2.COLOR_BGR2GRAY)


def adaptive_sharpen(
    image: np.ndarray,
    blur_ksize: int = 5,
    sharp_amount: float = 1.5,
    noise_threshold: int = 10,
) -> np.ndarray:
    """적응형 샤프닝. 노이즈 영역은 보호하고 결함 영역만 강조.

    Args:
        image: 그레이스케일 입력 이미지.
        blur_ksize: 가우시안 블러 커널 크기.
        sharp_amount: 샤프닝 강도.
        noise_threshold: 결함/노이즈 구분 임계값.

    Returns:
        적응형 샤프닝된 이미지.
    """
    img = _validate_image(image)
    k = blur_ksize if blur_ksize % 2 == 1 else blur_ksize + 1
    noise_map = cv2.GaussianBlur(img, (k, k), 0)
    diff = np.abs(img.astype(np.float64) - noise_map.astype(np.float64))

    # 결함 가능 영역 마스크
    mask = (diff > noise_threshold).astype(np.float64)
    mask = cv2.GaussianBlur(mask, (k, k), 0)  # 부드러운 경계

    sharpened = unsharp_mask(img, k, 1.0, sharp_amount, 0)
    result = mask * sharpened.astype(np.float64) + (1 - mask) * img.astype(np.float64)
    return np.clip(result, 0, 255).astype(np.uint8)


def compare_sharpen_methods(image: np.ndarray) -> dict[str, np.ndarray]:
    """모든 샤프닝 방법의 결과를 한번에 비교.

    Args:
        image: 그레이스케일 입력 이미지.

    Returns:
        방법명→결과 이미지 딕셔너리.
    """
    img = _validate_image(image)
    return {
        "original": img,
        "unsharp_light": unsharp_mask(img, amount=1.0),
        "unsharp_strong": unsharp_mask(img, amount=2.5),
        "laplacian": laplacian_sharpen(img),
        "highpass": highpass_sharpen(img),
        "kernel_light": custom_sharpen_kernel(img, "light"),
        "kernel_medium": custom_sharpen_kernel(img, "medium"),
        "kernel_strong": custom_sharpen_kernel(img, "strong"),
        "emboss": emboss_filter(img),
        "adaptive": adaptive_sharpen(img),
    }


def blur_then_sharpen(
    image: np.ndarray,
    blur_method: str = "bilateral",
    blur_params: dict = None,
    sharpen_method: str = "unsharp",
    sharpen_params: dict = None,
) -> dict[str, np.ndarray]:
    """블러 → 샤프닝 순차 적용 파이프라인.

    Args:
        image: 그레이스케일 입력 이미지.
        blur_method: "gaussian", "median", "bilateral", "nlm" 중 택 1.
        blur_params: 블러 파라미터 딕셔너리.
        sharpen_method: "unsharp", "laplacian", "highpass", "adaptive" 중 택 1.
        sharpen_params: 샤프닝 파라미터 딕셔너리.

    Returns:
        {"original", "blurred", "sharpened"} 딕셔너리.
    """
    from preprocessing.filters import (
        gaussian_blur, median_blur, bilateral_filter, non_local_means_denoise
    )

    img = _validate_image(image)
    bp = blur_params or {}
    sp = sharpen_params or {}

    blur_fns = {
        "gaussian": lambda i: gaussian_blur(i, **bp),
        "median": lambda i: median_blur(i, **bp),
        "bilateral": lambda i: bilateral_filter(i, **bp),
        "nlm": lambda i: non_local_means_denoise(i, **bp),
    }
    sharpen_fns = {
        "unsharp": lambda i: unsharp_mask(i, **sp),
        "laplacian": lambda i: laplacian_sharpen(i, **sp),
        "highpass": lambda i: highpass_sharpen(i, **sp),
        "adaptive": lambda i: adaptive_sharpen(i, **sp),
    }

    blurred = blur_fns[blur_method](img)
    sharpened = sharpen_fns[sharpen_method](blurred)

    return {"original": img, "blurred": blurred, "sharpened": sharpened}


if __name__ == "__main__":
    import os, sys

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    from utils.data_loader import NEUDataLoader

    data_dir = os.path.join(project_root, "data", "NEU-DET")
    loader = NEUDataLoader(data_dir)

    print("\n=== sharpening.py 테스트 ===")
    samples = loader.get_sample_images(n_per_class=1)
    img = samples["scratches"][0]

    results = compare_sharpen_methods(img)
    for name, r in results.items():
        lap_var = cv2.Laplacian(r, cv2.CV_64F).var()
        print(f"  {name:16s}: mean={r.mean():.1f}, laplacian_var={lap_var:.1f}")

    pipe = blur_then_sharpen(img)
    print(f"\nblur_then_sharpen: {list(pipe.keys())}")
    print("✅ sharpening.py 테스트 완료")

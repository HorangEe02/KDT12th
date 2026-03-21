"""모폴로지(형태학적) 연산 모듈.

커널(구조 요소)의 모양과 크기에 따라 미세 결함을 확대하거나
작은 노이즈를 제거하는 비선형 필터링 기법을 제공한다.
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
    if k % 2 == 0:
        warnings.warn(f"커널 사이즈 {k}을 {k+1}로 보정합니다.")
        return k + 1
    return k


def get_kernel(shape: str = "rect", size: int = 3) -> np.ndarray:
    """모폴로지 연산용 구조 요소(커널) 생성.

    Args:
        shape: "rect", "ellipse", "cross" 중 택 1.
        size: 커널 크기 (홀수).

    Returns:
        (size, size) shape의 커널.
    """
    shape_map = {
        "rect": cv2.MORPH_RECT,
        "ellipse": cv2.MORPH_ELLIPSE,
        "cross": cv2.MORPH_CROSS,
    }
    if shape not in shape_map:
        raise ValueError(f"지원하지 않는 shape: {shape}. 가능: {list(shape_map.keys())}")
    s = _ensure_odd(size)
    return cv2.getStructuringElement(shape_map[shape], (s, s))


def erode(
    image: np.ndarray,
    kernel_shape: str = "rect",
    kernel_size: int = 3,
    iterations: int = 1,
) -> np.ndarray:
    """침식 연산. 밝은 영역 축소, 어두운 결함 강조.

    Args:
        image: 그레이스케일 입력 이미지.
        kernel_shape: 커널 모양.
        kernel_size: 커널 크기.
        iterations: 반복 횟수.

    Returns:
        침식 처리된 이미지.
    """
    img = _validate_image(image)
    kernel = get_kernel(kernel_shape, kernel_size)
    return cv2.erode(img, kernel, iterations=iterations)


def dilate(
    image: np.ndarray,
    kernel_shape: str = "rect",
    kernel_size: int = 3,
    iterations: int = 1,
) -> np.ndarray:
    """팽창 연산. 밝은 영역 확장, 밝은 결함 강조.

    Args:
        image: 그레이스케일 입력 이미지.
        kernel_shape: 커널 모양.
        kernel_size: 커널 크기.
        iterations: 반복 횟수.

    Returns:
        팽창 처리된 이미지.
    """
    img = _validate_image(image)
    kernel = get_kernel(kernel_shape, kernel_size)
    return cv2.dilate(img, kernel, iterations=iterations)


def opening(
    image: np.ndarray, kernel_shape: str = "rect", kernel_size: int = 3
) -> np.ndarray:
    """열기 연산 (침식→팽창). 작은 밝은 노이즈 점 제거.

    Args:
        image: 그레이스케일 입력 이미지.
        kernel_shape: 커널 모양.
        kernel_size: 커널 크기.

    Returns:
        Opening 처리된 이미지.
    """
    img = _validate_image(image)
    kernel = get_kernel(kernel_shape, kernel_size)
    return cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)


def closing(
    image: np.ndarray, kernel_shape: str = "rect", kernel_size: int = 3
) -> np.ndarray:
    """닫기 연산 (팽창→침식). 결함 내부의 작은 구멍 채우기, 끊어진 균열 연결.

    Args:
        image: 그레이스케일 입력 이미지.
        kernel_shape: 커널 모양.
        kernel_size: 커널 크기.

    Returns:
        Closing 처리된 이미지.
    """
    img = _validate_image(image)
    kernel = get_kernel(kernel_shape, kernel_size)
    return cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel)


def morphological_gradient(
    image: np.ndarray, kernel_shape: str = "rect", kernel_size: int = 3
) -> np.ndarray:
    """모폴로지 그래디언트 (팽창 - 침식 = 경계 추출).

    Args:
        image: 그레이스케일 입력 이미지.
        kernel_shape: 커널 모양.
        kernel_size: 커널 크기.

    Returns:
        그래디언트 이미지.
    """
    img = _validate_image(image)
    kernel = get_kernel(kernel_shape, kernel_size)
    return cv2.morphologyEx(img, cv2.MORPH_GRADIENT, kernel)


def tophat(
    image: np.ndarray, kernel_shape: str = "rect", kernel_size: int = 9
) -> np.ndarray:
    """탑햇 변환 (원본 - Opening). 배경보다 밝은 미세 결함 추출.

    Args:
        image: 그레이스케일 입력 이미지.
        kernel_shape: 커널 모양.
        kernel_size: 커널 크기 (결함보다 크게 설정).

    Returns:
        탑햇 변환 이미지.
    """
    img = _validate_image(image)
    kernel = get_kernel(kernel_shape, kernel_size)
    return cv2.morphologyEx(img, cv2.MORPH_TOPHAT, kernel)


def blackhat(
    image: np.ndarray, kernel_shape: str = "rect", kernel_size: int = 9
) -> np.ndarray:
    """블랙햇 변환 (Closing - 원본). 배경보다 어두운 미세 결함 추출.

    Args:
        image: 그레이스케일 입력 이미지.
        kernel_shape: 커널 모양.
        kernel_size: 커널 크기 (결함보다 크게 설정).

    Returns:
        블랙햇 변환 이미지.
    """
    img = _validate_image(image)
    kernel = get_kernel(kernel_shape, kernel_size)
    return cv2.morphologyEx(img, cv2.MORPH_BLACKHAT, kernel)


def morphology_pipeline(
    image: np.ndarray, operations: list[dict]
) -> dict[str, np.ndarray]:
    """모폴로지 연산을 순차적으로 적용하는 파이프라인.

    Args:
        image: 그레이스케일 입력 이미지.
        operations: [{"op": "opening", "kernel_shape": "rect", "kernel_size": 3}, ...].

    Returns:
        각 단계 중간 결과 딕셔너리.
    """
    op_map = {
        "erode": erode, "dilate": dilate, "opening": opening,
        "closing": closing, "gradient": morphological_gradient,
        "tophat": tophat, "blackhat": blackhat,
    }

    img = _validate_image(image)
    results = {"step_0_original": img}
    current = img

    for i, op_cfg in enumerate(operations, 1):
        op_name = op_cfg.get("op", "opening")
        if op_name not in op_map:
            raise ValueError(f"지원하지 않는 연산: {op_name}")
        params = {k: v for k, v in op_cfg.items() if k != "op"}
        current = op_map[op_name](current, **params)
        results[f"step_{i}_{op_name}"] = current

    return results


def defect_enhancement_morph(
    image: np.ndarray, defect_type: str = "general"
) -> np.ndarray:
    """결함 유형별 최적 모폴로지 전처리.

    Args:
        image: 그레이스케일 입력 이미지.
        defect_type: "crazing", "scratches", "pitted", "inclusion",
                     "patches", "rolled_in_scale", "general" 중 택 1.

    Returns:
        결함 강조된 이미지.
    """
    img = _validate_image(image)

    strategies = {
        "crazing": lambda i: tophat(closing(i, "ellipse", 3), "rect", 7),
        "scratches": lambda i: morphological_gradient(dilate(i, "rect", 3, 1), "rect", 3),
        "pitted": lambda i: blackhat(erode(i, "ellipse", 3, 1), "ellipse", 9),
        "inclusion": lambda i: tophat(i, "rect", 9),
        "patches": lambda i: opening(closing(i, "rect", 5), "rect", 3),
        "rolled_in_scale": lambda i: dilate(blackhat(i, "rect", 11), "rect", 3),
        "general": lambda i: closing(opening(i, "rect", 3), "rect", 3),
    }

    if defect_type not in strategies:
        raise ValueError(f"지원하지 않는 defect_type: {defect_type}. 가능: {list(strategies.keys())}")

    return strategies[defect_type](img)


def compare_morphology_methods(
    image: np.ndarray, kernel_size: int = 3
) -> dict[str, np.ndarray]:
    """모든 모폴로지 연산 결과를 한번에 비교.

    Args:
        image: 그레이스케일 입력 이미지.
        kernel_size: 커널 크기.

    Returns:
        연산명→결과 이미지 딕셔너리.
    """
    img = _validate_image(image)
    return {
        "original": img,
        "erode": erode(img, kernel_size=kernel_size),
        "dilate": dilate(img, kernel_size=kernel_size),
        "opening": opening(img, kernel_size=kernel_size),
        "closing": closing(img, kernel_size=kernel_size),
        "gradient": morphological_gradient(img, kernel_size=kernel_size),
        "tophat": tophat(img, kernel_size=9),
        "blackhat": blackhat(img, kernel_size=9),
    }


if __name__ == "__main__":
    import os, sys

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    from utils.data_loader import NEUDataLoader

    data_dir = os.path.join(project_root, "data", "NEU-DET")
    loader = NEUDataLoader(data_dir)

    print("\n=== morphology.py 테스트 ===")
    samples = loader.get_sample_images(n_per_class=1)

    for cn in ["scratches", "crazing", "pitted_surface"]:
        img = samples[cn][0]
        results = compare_morphology_methods(img)
        print(f"\n  [{cn}]")
        for name, r in results.items():
            print(f"    {name:10s}: mean={r.mean():.1f}, std={r.std():.1f}")

    # defect_enhancement_morph 테스트
    dtype_map = {"crazing": "crazing", "scratches": "scratches", "pitted_surface": "pitted"}
    for cn, dt in dtype_map.items():
        result = defect_enhancement_morph(samples[cn][0], dt)
        print(f"\n  defect_enhancement({dt}): shape={result.shape}, mean={result.mean():.1f}")

    print("\n✅ morphology.py 테스트 완료")

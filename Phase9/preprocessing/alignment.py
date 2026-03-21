"""이미지 기하학적 정렬 모듈.

NEU 금속 표면 결함 이미지의 기하학적 보정(회전, 어파인, 투시 변환)과
실환경 적용 시 필요한 정렬 기능을 제공한다.
"""

import cv2
import numpy as np
from typing import Union


def _validate_image(image: np.ndarray) -> None:
    """입력 이미지 유효성 검사."""
    if image is None:
        raise ValueError("입력 이미지가 None입니다.")
    if image.ndim not in (2, 3):
        raise ValueError(f"이미지 차원이 올바르지 않습니다: ndim={image.ndim}")


def rotate_image(
    image: np.ndarray, angle: float, scale: float = 1.0
) -> np.ndarray:
    """이미지 중심 기준으로 지정 각도만큼 회전.

    Args:
        image: 입력 이미지 (그레이스케일 또는 컬러).
        angle: 회전 각도 (도 단위, 반시계 방향 양수).
        scale: 회전 시 스케일 조정 (기본 1.0).

    Returns:
        회전된 이미지. 빈 영역은 가장자리 픽셀로 채움.
    """
    _validate_image(image)
    img = image.copy()
    h, w = img.shape[:2]
    center = (w / 2, h / 2)
    M = cv2.getRotationMatrix2D(center, angle, scale)
    rotated = cv2.warpAffine(
        img, M, (w, h), borderMode=cv2.BORDER_REPLICATE
    )
    return rotated


def auto_deskew(image: np.ndarray) -> tuple[np.ndarray, float]:
    """이미지의 기울어진 각도를 자동 감지하여 보정.

    이진화 → 윤곽선 검출 → 최소 외접 회전 사각형으로 기울기를 추정한 뒤
    보정된 이미지를 반환한다.

    Args:
        image: 그레이스케일 입력 이미지.

    Returns:
        (보정된 이미지, 감지된 기울기 각도) 튜플.
    """
    _validate_image(image)
    img = image.copy()
    if img.ndim == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img

    # 이진화
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # 윤곽선 검출
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return img, 0.0

    # 가장 큰 윤곽선
    largest = max(contours, key=cv2.contourArea)

    if len(largest) < 5:
        return img, 0.0

    rect = cv2.minAreaRect(largest)
    angle = rect[-1]

    # minAreaRect angle 보정: -90~0 범위를 -45~45로 변환
    if angle < -45:
        angle = 90 + angle
    elif angle > 45:
        angle = angle - 90

    corrected = rotate_image(img, -angle)
    return corrected, angle


def affine_transform(
    image: np.ndarray,
    src_points: np.ndarray,
    dst_points: np.ndarray,
) -> np.ndarray:
    """3점 기반 어파인 변환.

    Args:
        image: 입력 이미지.
        src_points: 원본 좌표 (3, 2) float32 배열.
        dst_points: 대상 좌표 (3, 2) float32 배열.

    Returns:
        어파인 변환된 이미지.
    """
    _validate_image(image)
    img = image.copy()
    h, w = img.shape[:2]
    M = cv2.getAffineTransform(
        src_points.astype(np.float32), dst_points.astype(np.float32)
    )
    return cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REPLICATE)


def perspective_transform(
    image: np.ndarray,
    src_points: np.ndarray,
    dst_points: np.ndarray,
) -> np.ndarray:
    """4점 기반 원근(투시) 변환.

    Args:
        image: 입력 이미지.
        src_points: 원본 좌표 (4, 2) float32 배열.
        dst_points: 대상 좌표 (4, 2) float32 배열.

    Returns:
        투시 변환된 이미지.
    """
    _validate_image(image)
    img = image.copy()
    h, w = img.shape[:2]
    M = cv2.getPerspectiveTransform(
        src_points.astype(np.float32), dst_points.astype(np.float32)
    )
    return cv2.warpPerspective(img, M, (w, h), borderMode=cv2.BORDER_REPLICATE)


def flip_image(image: np.ndarray, flip_code: int) -> np.ndarray:
    """이미지 대칭.

    Args:
        image: 입력 이미지.
        flip_code: 0(상하), 1(좌우), -1(양방향).

    Returns:
        대칭된 이미지.
    """
    _validate_image(image)
    return cv2.flip(image.copy(), flip_code)


def resize_with_aspect_ratio(
    image: np.ndarray,
    target_size: int = 200,
    interpolation: int = cv2.INTER_LINEAR,
) -> np.ndarray:
    """종횡비를 유지하면서 리사이즈.

    긴 변을 target_size에 맞추고, 결과를 정사각형 캔버스 중앙에 배치한다.

    Args:
        image: 입력 이미지.
        target_size: 출력 정사각형 크기 (기본 200).
        interpolation: 보간 방법.

    Returns:
        target_size × target_size 정사각형 이미지.
    """
    _validate_image(image)
    img = image.copy()
    h, w = img.shape[:2]

    # 스케일 계산
    scale = target_size / max(h, w)
    new_w, new_h = int(w * scale), int(h * scale)
    resized = cv2.resize(img, (new_w, new_h), interpolation=interpolation)

    # 정사각형 캔버스에 중앙 배치
    if img.ndim == 3:
        canvas = np.zeros((target_size, target_size, img.shape[2]), dtype=img.dtype)
    else:
        canvas = np.zeros((target_size, target_size), dtype=img.dtype)

    y_off = (target_size - new_h) // 2
    x_off = (target_size - new_w) // 2
    canvas[y_off : y_off + new_h, x_off : x_off + new_w] = resized
    return canvas


def demonstrate_alignment(
    image: np.ndarray,
    angles: list[float] = None,
) -> dict:
    """정렬 시연: 인위적 회전 후 auto_deskew로 복원.

    Args:
        image: 원본 이미지.
        angles: 테스트할 회전 각도 리스트. 기본 [-15, -10, -5, 5, 10, 15].

    Returns:
        각 각도별 (회전 이미지, 복원 이미지, 감지 각도, 복원 오차) 딕셔너리.
    """
    if angles is None:
        angles = [-15, -10, -5, 5, 10, 15]

    _validate_image(image)
    results = {}

    for ang in angles:
        rotated = rotate_image(image, ang)
        restored, detected = auto_deskew(rotated)
        error = abs(ang - (-detected))  # 복원 오차
        results[f"angle_{ang}"] = {
            "rotated": rotated,
            "restored": restored,
            "detected_angle": detected,
            "error": round(error, 2),
        }
    return results


if __name__ == "__main__":
    import os, sys

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)

    # 합성 테스트 이미지 (200x200에 직사각형)
    test_img = np.zeros((200, 200), dtype=np.uint8)
    cv2.rectangle(test_img, (50, 70), (150, 130), 255, -1)

    print("=== alignment.py 테스트 ===")

    # 회전
    rotated = rotate_image(test_img, 15)
    print(f"rotate_image: {rotated.shape}")

    # auto_deskew
    corrected, angle = auto_deskew(rotated)
    print(f"auto_deskew: 감지 각도={angle:.2f}°")

    # flip
    flipped = flip_image(test_img, 1)
    print(f"flip_image: {flipped.shape}")

    # resize
    resized = resize_with_aspect_ratio(test_img, 100)
    print(f"resize_with_aspect_ratio: {resized.shape}")

    # demonstrate
    demo = demonstrate_alignment(test_img, [-10, 10])
    for key, val in demo.items():
        print(f"  {key}: detected={val['detected_angle']:.2f}°, error={val['error']:.2f}°")

    print("✅ alignment.py 테스트 완료")

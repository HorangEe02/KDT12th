"""ROI(Region of Interest) 추출 모듈.

금속 표면 이미지에서 검사 대상 영역을 자동/수동으로 추출하는 기능을 제공한다.
윤곽선 기반, 에지 밀도 기반, 중앙 크롭, 멀티스케일 등 다양한 ROI 추출 방법을 포함.
"""

import cv2
import numpy as np
import warnings
from typing import Optional


def _validate_image(image: np.ndarray) -> None:
    """입력 이미지 유효성 검사."""
    if image is None:
        raise ValueError("입력 이미지가 None입니다.")
    if image.ndim not in (2, 3):
        raise ValueError(f"이미지 차원이 올바르지 않습니다: ndim={image.ndim}")


def extract_roi_manual(
    image: np.ndarray, x: int, y: int, w: int, h: int
) -> np.ndarray:
    """수동 좌표 지정으로 ROI 추출.

    Args:
        image: 입력 이미지.
        x, y: 좌상단 좌표.
        w, h: 너비, 높이.

    Returns:
        잘라낸 ROI 이미지.
    """
    _validate_image(image)
    img_h, img_w = image.shape[:2]
    x1 = max(0, min(x, img_w - 1))
    y1 = max(0, min(y, img_h - 1))
    x2 = max(0, min(x + w, img_w))
    y2 = max(0, min(y + h, img_h))
    return image[y1:y2, x1:x2].copy()


def extract_roi_center(
    image: np.ndarray, crop_ratio: float = 0.7
) -> np.ndarray:
    """이미지 중앙 기준으로 crop_ratio 비율만큼 잘라내기.

    추출 후 원본 크기(200x200)로 리사이즈한다.

    Args:
        image: 입력 이미지.
        crop_ratio: 크롭 비율 (0~1). 0.7이면 중앙 70% 영역.

    Returns:
        원본 크기로 리사이즈된 ROI 이미지.
    """
    _validate_image(image)
    img = image.copy()
    h, w = img.shape[:2]
    crop_h, crop_w = int(h * crop_ratio), int(w * crop_ratio)
    y1 = (h - crop_h) // 2
    x1 = (w - crop_w) // 2
    roi = img[y1 : y1 + crop_h, x1 : x1 + crop_w]
    return cv2.resize(roi, (w, h))


def extract_roi_by_contour(
    image: np.ndarray, threshold_value: int = 127
) -> tuple[np.ndarray, tuple]:
    """윤곽선 기반 자동 ROI 추출.

    Args:
        image: 그레이스케일 입력 이미지.
        threshold_value: 이진화 임계값. 127이면 Otsu 자동 적용.

    Returns:
        (ROI 이미지, (x, y, w, h) 바운딩 박스 좌표) 튜플.
    """
    _validate_image(image)
    img = image.copy()
    if img.ndim == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img

    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        warnings.warn("윤곽선이 검출되지 않았습니다. 원본 이미지를 반환합니다.")
        h, w = img.shape[:2]
        return img, (0, 0, w, h)

    largest = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(largest)

    # 10% 패딩
    img_h, img_w = img.shape[:2]
    pad_x, pad_y = int(w * 0.1), int(h * 0.1)
    x1 = max(0, x - pad_x)
    y1 = max(0, y - pad_y)
    x2 = min(img_w, x + w + pad_x)
    y2 = min(img_h, y + h + pad_y)

    roi = img[y1:y2, x1:x2]
    return roi, (x1, y1, x2 - x1, y2 - y1)


def extract_roi_by_edge_density(
    image: np.ndarray, grid_size: int = 4
) -> tuple[np.ndarray, tuple]:
    """에지 밀도 기반 관심 영역 자동 탐지.

    이미지를 grid로 분할하고 에지 밀도가 가장 높은 영역을 ROI로 선택한다.

    Args:
        image: 그레이스케일 입력 이미지.
        grid_size: 그리드 분할 수 (기본 4x4).

    Returns:
        (ROI 이미지, (x, y, w, h) 바운딩 박스 좌표) 튜플.
    """
    _validate_image(image)
    img = image.copy()
    if img.ndim == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img

    edges = cv2.Canny(gray, 50, 150)
    h, w = gray.shape
    cell_h, cell_w = h // grid_size, w // grid_size

    # 각 그리드 셀의 에지 밀도 계산
    density_map = np.zeros((grid_size, grid_size), dtype=np.float64)
    for r in range(grid_size):
        for c in range(grid_size):
            y1, y2 = r * cell_h, min((r + 1) * cell_h, h)
            x1, x2 = c * cell_w, min((c + 1) * cell_w, w)
            cell = edges[y1:y2, x1:x2]
            density_map[r, c] = np.mean(cell > 0)

    # 평균 이상인 셀들의 바운딩 박스
    threshold = density_map.mean()
    high_cells = np.argwhere(density_map > threshold)

    if len(high_cells) == 0:
        warnings.warn("고밀도 에지 영역이 없습니다. 원본을 반환합니다.")
        return img, (0, 0, w, h)

    r_min, c_min = high_cells.min(axis=0)
    r_max, c_max = high_cells.max(axis=0)

    y1 = r_min * cell_h
    y2 = min((r_max + 1) * cell_h, h)
    x1 = c_min * cell_w
    x2 = min((c_max + 1) * cell_w, w)

    roi = img[y1:y2, x1:x2]
    return roi, (x1, y1, x2 - x1, y2 - y1)


def visualize_roi(
    image: np.ndarray, roi_bbox: tuple, title: str = "ROI 추출 결과"
) -> np.ndarray:
    """원본 이미지 위에 ROI 영역을 초록색 사각형으로 표시.

    Args:
        image: 원본 이미지 (그레이스케일).
        roi_bbox: (x, y, w, h) 바운딩 박스 좌표.
        title: 표시 제목 (현재 미사용, 향후 확장용).

    Returns:
        ROI가 표시된 BGR 컬러 이미지.
    """
    _validate_image(image)
    if image.ndim == 2:
        vis = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    else:
        vis = image.copy()

    x, y, w, h = roi_bbox
    cv2.rectangle(vis, (x, y), (x + w, y + h), (0, 255, 0), 2)
    return vis


def multi_scale_roi(
    image: np.ndarray, scales: list[float] = None
) -> list[np.ndarray]:
    """여러 스케일로 중앙 ROI 추출.

    Args:
        image: 입력 이미지.
        scales: 크롭 비율 리스트. 기본 [0.5, 0.7, 0.9].

    Returns:
        각 스케일별 ROI 이미지 리스트.
    """
    if scales is None:
        scales = [0.5, 0.7, 0.9]
    _validate_image(image)
    return [extract_roi_center(image, s) for s in scales]


def create_roi_comparison(image: np.ndarray) -> dict:
    """모든 ROI 추출 방법의 결과를 비교.

    Args:
        image: 입력 이미지.

    Returns:
        방법명→결과 이미지 및 bbox 딕셔너리.
    """
    _validate_image(image)
    h, w = image.shape[:2]

    results = {"original": {"image": image.copy(), "bbox": (0, 0, w, h)}}

    # 수동 중앙 크롭
    center_img = extract_roi_center(image, 0.7)
    ch, cw = int(h * 0.7), int(w * 0.7)
    results["center_70"] = {
        "image": center_img,
        "bbox": ((w - cw) // 2, (h - ch) // 2, cw, ch),
    }

    # 윤곽선 기반
    contour_img, contour_bbox = extract_roi_by_contour(image)
    results["contour"] = {"image": contour_img, "bbox": contour_bbox}

    # 에지 밀도 기반
    edge_img, edge_bbox = extract_roi_by_edge_density(image)
    results["edge_density"] = {"image": edge_img, "bbox": edge_bbox}

    return results


if __name__ == "__main__":
    import os, sys

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    from utils.data_loader import NEUDataLoader

    data_dir = os.path.join(project_root, "data", "NEU-DET")
    loader = NEUDataLoader(data_dir)

    print("\n=== roi.py 테스트 ===")
    samples = loader.get_sample_images(n_per_class=1)

    for cn, imgs in samples.items():
        img = imgs[0]
        comparison = create_roi_comparison(img)
        bboxes = {k: v["bbox"] for k, v in comparison.items()}
        print(f"  {cn}: {bboxes}")

    print("✅ roi.py 테스트 완료")

"""필터 비교 및 평가 유틸리티.

필터링 전/후의 이미지 품질 변화를 측정하고,
결함 보존도를 정량화하는 평가 도구를 제공한다.
"""

import cv2
import numpy as np
import pandas as pd
from typing import Optional
from skimage.metrics import structural_similarity as ssim


def compute_edge_density(
    image: np.ndarray, low_threshold: int = 50, high_threshold: int = 150
) -> float:
    """Canny 에지 검출 후 에지 픽셀 비율 계산.

    Args:
        image: 그레이스케일 입력 이미지.
        low_threshold: Canny 하한 임계값.
        high_threshold: Canny 상한 임계값.

    Returns:
        0.0~1.0 범위의 에지 밀도 (에지 픽셀 수 / 전체 픽셀 수).
    """
    if image.ndim == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(image, low_threshold, high_threshold)
    return float(np.mean(edges > 0))


def compute_psnr(original: np.ndarray, processed: np.ndarray) -> float:
    """Peak Signal-to-Noise Ratio 계산. 높을수록 원본과 유사.

    Args:
        original: 원본 이미지.
        processed: 처리된 이미지.

    Returns:
        PSNR 값 (dB). 동일 이미지이면 float('inf').
    """
    mse = np.mean((original.astype(np.float64) - processed.astype(np.float64)) ** 2)
    if mse == 0:
        return float("inf")
    return float(20 * np.log10(255.0 / np.sqrt(mse)))


def compute_ssim(original: np.ndarray, processed: np.ndarray) -> float:
    """Structural Similarity Index 계산. 1.0에 가까울수록 구조적으로 유사.

    Args:
        original: 원본 이미지.
        processed: 처리된 이미지.

    Returns:
        SSIM 값 (-1.0~1.0).
    """
    return float(ssim(original, processed))


def compute_variance_of_laplacian(image: np.ndarray) -> float:
    """라플라시안 분산 (이미지 선명도 지표). 높을수록 선명.

    Args:
        image: 그레이스케일 입력 이미지.

    Returns:
        라플라시안 분산 값.
    """
    if image.ndim == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(image, cv2.CV_64F).var())


def compute_noise_level(image: np.ndarray) -> float:
    """이미지의 노이즈 수준 추정. 높을수록 노이즈가 많음.

    Args:
        image: 그레이스케일 입력 이미지.

    Returns:
        노이즈 수준 (가우시안 블러와의 차이 표준편차).
    """
    if image.ndim == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(image, (0, 0), 5)
    diff = image.astype(np.float64) - blurred.astype(np.float64)
    return float(np.std(diff))


def evaluate_filter(
    original: np.ndarray, filtered: np.ndarray
) -> dict[str, float]:
    """단일 필터의 종합 평가.

    Args:
        original: 원본 이미지.
        filtered: 필터 적용된 이미지.

    Returns:
        PSNR, SSIM, 에지 밀도 변화, 선명도 변화, 노이즈 감소 등을 포함하는 딕셔너리.
    """
    ed_orig = compute_edge_density(original)
    ed_filt = compute_edge_density(filtered)
    lv_orig = compute_variance_of_laplacian(original)
    lv_filt = compute_variance_of_laplacian(filtered)
    n_orig = compute_noise_level(original)
    n_filt = compute_noise_level(filtered)

    ed_change = ((ed_filt - ed_orig) / ed_orig * 100) if ed_orig > 0 else 0.0
    sharp_change = ((lv_filt - lv_orig) / lv_orig * 100) if lv_orig > 0 else 0.0
    noise_red = ((n_orig - n_filt) / n_orig * 100) if n_orig > 0 else 0.0

    return {
        "psnr": compute_psnr(original, filtered),
        "ssim": compute_ssim(original, filtered),
        "edge_density_original": ed_orig,
        "edge_density_filtered": ed_filt,
        "edge_density_change": ed_change,
        "laplacian_var_original": lv_orig,
        "laplacian_var_filtered": lv_filt,
        "sharpness_change": sharp_change,
        "noise_original": n_orig,
        "noise_filtered": n_filt,
        "noise_reduction": noise_red,
    }


def batch_evaluate_filters(
    image: np.ndarray, filtered_images: dict[str, np.ndarray]
) -> pd.DataFrame:
    """여러 필터를 한번에 비교 평가.

    Args:
        image: 원본 이미지.
        filtered_images: {"method_name": filtered_image, ...}.

    Returns:
        행=필터명, 열=평가 지표인 DataFrame (SSIM 내림차순).
    """
    rows = []
    for name, fimg in filtered_images.items():
        ev = evaluate_filter(image, fimg)
        ev["method"] = name
        rows.append(ev)

    df = pd.DataFrame(rows).set_index("method")
    return df.sort_values("ssim", ascending=False)


def find_optimal_filter(
    image: np.ndarray,
    filtered_images: dict[str, np.ndarray],
    priority: str = "edge_preservation",
) -> str:
    """최적 필터 자동 선택.

    Args:
        image: 원본 이미지.
        filtered_images: {"method_name": filtered_image, ...}.
        priority: "edge_preservation", "noise_reduction", "balanced" 중 택 1.

    Returns:
        최적 필터 이름 (문자열).
    """
    df = batch_evaluate_filters(image, filtered_images)

    if priority == "edge_preservation":
        # SSIM 높고 edge_density_change 절댓값 작은 것
        df["score"] = df["ssim"] - np.abs(df["edge_density_change"]) / 100
    elif priority == "noise_reduction":
        df["score"] = df["noise_reduction"]
    elif priority == "balanced":
        # SSIM, 에지 보존, 노이즈 감소 종합
        ssim_norm = (df["ssim"] - df["ssim"].min()) / (df["ssim"].max() - df["ssim"].min() + 1e-7)
        edge_norm = 1 - (np.abs(df["edge_density_change"]) - np.abs(df["edge_density_change"]).min()) / \
                    (np.abs(df["edge_density_change"]).max() - np.abs(df["edge_density_change"]).min() + 1e-7)
        noise_norm = (df["noise_reduction"] - df["noise_reduction"].min()) / \
                     (df["noise_reduction"].max() - df["noise_reduction"].min() + 1e-7)
        df["score"] = 0.4 * ssim_norm + 0.3 * edge_norm + 0.3 * noise_norm
    else:
        raise ValueError(f"지원하지 않는 priority: {priority}")

    return str(df["score"].idxmax())


if __name__ == "__main__":
    import os, sys

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    from utils.data_loader import NEUDataLoader
    from preprocessing.filters import compare_blur_methods

    data_dir = os.path.join(project_root, "data", "NEU-DET")
    loader = NEUDataLoader(data_dir)

    print("\n=== filter_utils.py 테스트 ===")
    samples = loader.get_sample_images(n_per_class=1)
    img = samples["scratches"][0]

    # 블러 방법 비교
    blur_results = compare_blur_methods(img)
    filtered = {k: v for k, v in blur_results.items() if k != "original"}

    df = batch_evaluate_filters(img, filtered)
    print("\n[Scratches 블러 평가]")
    print(df[["psnr", "ssim", "edge_density_change", "noise_reduction"]].to_string())

    best = find_optimal_filter(img, filtered, "balanced")
    print(f"\n최적 필터 (balanced): {best}")
    print("✅ filter_utils.py 테스트 완료")

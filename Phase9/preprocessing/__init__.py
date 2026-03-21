"""전처리 모듈 패키지.

OpenCV 기반 금속 표면 결함 이미지 전처리 파이프라인.

- 소주제 ① — 이미지 정렬, ROI 추출, 밝기/대비 정규화
- 소주제 ② — 필터링, 샤프닝, 모폴로지 연산
- 소주제 ③ — 임계값 처리, 에지 검출

사용 예시::

    # 소주제 ① 정렬/ROI/정규화
    from preprocessing import rotate_image, extract_roi_center, clahe_equalization

    # 소주제 ② 필터링/샤프닝
    from preprocessing.filters import gaussian_blur, bilateral_filter
    from preprocessing.sharpening import unsharp_mask, adaptive_sharpen
    from preprocessing.morphology import tophat, blackhat, opening

    # 통합 파이프라인
    img = clahe_equalization(raw_img)
    img = bilateral_filter(img, d=9, sigma_color=75, sigma_space=75)
    img = adaptive_sharpen(img, blur_ksize=5, sharp_amount=1.5, noise_threshold=10)
    img = opening(img, kernel_shape="rect", kernel_size=3)
"""

__version__ = "0.3.0"

# --- 소주제 ① ---
from preprocessing.alignment import (
    rotate_image, auto_deskew, affine_transform,
    perspective_transform, flip_image, resize_with_aspect_ratio,
    demonstrate_alignment,
)
from preprocessing.roi import (
    extract_roi_manual, extract_roi_center, extract_roi_by_contour,
    extract_roi_by_edge_density, visualize_roi, multi_scale_roi,
    create_roi_comparison,
)
from preprocessing.normalization import (
    histogram_equalization, clahe_equalization, min_max_normalize,
    standardize, gamma_correction, auto_brightness_contrast,
    normalize_pipeline, compare_normalizations,
)

# --- 소주제 ② ---
from preprocessing.filters import (
    gaussian_blur, median_blur, bilateral_filter, average_blur,
    non_local_means_denoise, apply_custom_kernel,
    progressive_blur, compare_blur_methods,
)
from preprocessing.sharpening import (
    unsharp_mask, laplacian_sharpen, highpass_sharpen,
    custom_sharpen_kernel, emboss_filter, detail_enhance,
    adaptive_sharpen, compare_sharpen_methods, blur_then_sharpen,
)
from preprocessing.morphology import (
    get_kernel, erode, dilate, opening, closing,
    morphological_gradient, tophat, blackhat,
    morphology_pipeline, defect_enhancement_morph,
    compare_morphology_methods,
)

# --- 소주제 ③ ---
from preprocessing.thresholding import (
    global_threshold, otsu_threshold, adaptive_threshold_mean,
    adaptive_threshold_gaussian, multi_threshold, triangle_threshold,
    compare_thresholds, find_optimal_threshold,
)
from preprocessing.edge_detection import (
    canny_edge, auto_canny, sobel_edge, laplacian_edge, scharr_edge,
    log_edge, multi_scale_edge, edge_direction_map,
    combine_edges, compare_edge_methods, evaluate_edge_quality,
)

__all__ = [
    # alignment
    "rotate_image", "auto_deskew", "affine_transform",
    "perspective_transform", "flip_image", "resize_with_aspect_ratio",
    "demonstrate_alignment",
    # roi
    "extract_roi_manual", "extract_roi_center", "extract_roi_by_contour",
    "extract_roi_by_edge_density", "visualize_roi", "multi_scale_roi",
    "create_roi_comparison",
    # normalization
    "histogram_equalization", "clahe_equalization", "min_max_normalize",
    "standardize", "gamma_correction", "auto_brightness_contrast",
    "normalize_pipeline", "compare_normalizations",
    # filters
    "gaussian_blur", "median_blur", "bilateral_filter", "average_blur",
    "non_local_means_denoise", "apply_custom_kernel",
    "progressive_blur", "compare_blur_methods",
    # sharpening
    "unsharp_mask", "laplacian_sharpen", "highpass_sharpen",
    "custom_sharpen_kernel", "emboss_filter", "detail_enhance",
    "adaptive_sharpen", "compare_sharpen_methods", "blur_then_sharpen",
    # morphology
    "get_kernel", "erode", "dilate", "opening", "closing",
    "morphological_gradient", "tophat", "blackhat",
    "morphology_pipeline", "defect_enhancement_morph",
    "compare_morphology_methods",
    # thresholding
    "global_threshold", "otsu_threshold", "adaptive_threshold_mean",
    "adaptive_threshold_gaussian", "multi_threshold", "triangle_threshold",
    "compare_thresholds", "find_optimal_threshold",
    # edge_detection
    "canny_edge", "auto_canny", "sobel_edge", "laplacian_edge", "scharr_edge",
    "log_edge", "multi_scale_edge", "edge_direction_map",
    "combine_edges", "compare_edge_methods", "evaluate_edge_quality",
]

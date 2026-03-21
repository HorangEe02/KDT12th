"""B-1: 전처리 분석 — 소주제 1~3의 전처리 파이프라인 시각화 및 효과 분석."""

import streamlit as st
import numpy as np
import os
import sys
import cv2
import matplotlib.pyplot as plt

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from preprocessing.normalization import clahe_equalization
from preprocessing.filters import bilateral_filter
from preprocessing.sharpening import adaptive_sharpen
from preprocessing.morphology import opening
from preprocessing.edge_detection import auto_canny
from features.hog_features import extract_hog
from features.lbp_features import extract_lbp_histogram, visualize_lbp_pattern
from utils.filter_utils import compute_edge_density, compute_variance_of_laplacian

plt.rcParams["font.family"] = "AppleGothic"
plt.rcParams["axes.unicode_minus"] = False


def _badge(letter, color_class="ib-blue"):
    return f'<span class="icon-badge {color_class}">{letter}</span>'


def render_tab_preprocessing(input_image, stages, preprocessed):
    """전처리 분석 탭."""
    B = _badge

    # ── 전처리 파이프라인 시각화 ──
    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("PP", "ib-green")} 전처리 파이프라인 시각화</div>', unsafe_allow_html=True)
    st.markdown("""<div class="info-box">
        <strong>전처리란?</strong> 카메라로 찍은 원본 이미지에는 조명 불균일, 노이즈(잡티) 등이 있어
        AI가 결함을 정확히 판단하기 어렵습니다. 아래 단계를 거치면 결함이 더 뚜렷하게 드러납니다.
    </div>""", unsafe_allow_html=True)

    img_cols = st.columns(len(stages))
    stage_descs = {
        "원본 이미지": "카메라에서 촬영된 그대로의 이미지",
        "CLAHE 정규화": "어둡고 밝은 부분의 대비를 자동 조절",
        "Bilateral 블러": "잡티는 제거하고 결함 경계는 보존",
        "Sharpen + Opening": "결함 부분을 선명하게 강조",
    }
    for i, (stage_name, stage_img) in enumerate(stages.items()):
        with img_cols[i]:
            st.image(stage_img, caption=stage_name, use_container_width=True, clamp=True)
            st.caption(stage_descs.get(stage_name, ""))

    flow_steps = [s for s in stages.keys() if s != "원본 이미지"]
    if flow_steps:
        st.markdown(f"**처리 흐름**: 원본 → {'  →  '.join(flow_steps)}")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── 전처리 효과 정량 평가 ──
    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("EF", "ib-blue")} 전처리 효과 정량 평가</div>', unsafe_allow_html=True)
    st.markdown("""<div class="info-box">
        <strong>에지 밀도</strong>: 결함 윤곽의 비율 (높을수록 결함이 잘 드러남)<br>
        <strong>선명도 (LV)</strong>: 이미지 디테일 수치 (높을수록 선명)
    </div>""", unsafe_allow_html=True)

    ed_orig = compute_edge_density(input_image)
    ed_proc = compute_edge_density(preprocessed)
    lv_orig = compute_variance_of_laplacian(input_image)
    lv_proc = compute_variance_of_laplacian(preprocessed)

    p1, p2, p3, p4 = st.columns(4)
    with p1:
        st.markdown(f'<div class="kpi-card"><p class="kpi-label">에지 밀도 (전)</p>'
                    f'<p class="kpi-value" style="color:#94a3b8;">{ed_orig:.4f}</p></div>',
                    unsafe_allow_html=True)
    with p2:
        st.markdown(f'<div class="kpi-card"><p class="kpi-label">에지 밀도 (후)</p>'
                    f'<p class="kpi-value">{ed_proc:.4f}</p></div>', unsafe_allow_html=True)
    with p3:
        st.markdown(f'<div class="kpi-card"><p class="kpi-label">선명도 LV (전)</p>'
                    f'<p class="kpi-value" style="color:#94a3b8;">{lv_orig:.0f}</p></div>',
                    unsafe_allow_html=True)
    with p4:
        st.markdown(f'<div class="kpi-card"><p class="kpi-label">선명도 LV (후)</p>'
                    f'<p class="kpi-value" style="color:#2563eb;">{lv_proc:.0f}</p></div>',
                    unsafe_allow_html=True)

    fig_perf, ax_perf = plt.subplots(1, 2, figsize=(10, 4))
    ax_perf[0].bar(["전처리 전", "전처리 후"], [ed_orig, ed_proc], color=["#94a3b8", "#059669"], width=0.4)
    ax_perf[0].set_title("에지 밀도 비교", fontsize=12, fontweight="bold")
    ax_perf[1].bar(["전처리 전", "전처리 후"], [lv_orig, lv_proc], color=["#94a3b8", "#2563eb"], width=0.4)
    ax_perf[1].set_title("선명도(LV) 비교", fontsize=12, fontweight="bold")
    fig_perf.patch.set_facecolor("#fff")
    plt.tight_layout()
    st.pyplot(fig_perf)
    plt.close(fig_perf)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── 특징 추출 시각화 ──
    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("FE", "ib-purple")} 특징 추출 시각화</div>', unsafe_allow_html=True)
    st.markdown("""<div class="info-box">
        AI는 이미지를 숫자로 변환해야 합니다.
        아래 3가지 방법으로 이미지의 패턴, 질감, 경계선 정보를 숫자 벡터로 변환합니다.
    </div>""", unsafe_allow_html=True)

    feat_cols = st.columns(3)
    with feat_cols[0]:
        hog_feat, hog_img = extract_hog(preprocessed, pixels_per_cell=(16, 16), visualize=True)
        hog_disp = hog_img.copy()
        if hog_disp.max() > 0:
            hog_disp = (hog_disp - hog_disp.min()) / (hog_disp.max() - hog_disp.min())
        hog_disp = np.clip(hog_disp * 3.0, 0, 1)
        hog_disp_u8 = (hog_disp * 255).astype(np.uint8)
        hog_color = cv2.applyColorMap(hog_disp_u8, cv2.COLORMAP_INFERNO)
        hog_color = cv2.cvtColor(hog_color, cv2.COLOR_BGR2RGB)
        st.image(hog_color, caption=f"HOG ({len(hog_feat)}차원)", use_container_width=True, clamp=True)
        st.caption("결함의 **형태와 방향** 패턴을 캡처")
    with feat_cols[1]:
        lbp_vis = visualize_lbp_pattern(preprocessed)
        lbp_hist = extract_lbp_histogram(preprocessed)
        lbp_disp = cv2.normalize(lbp_vis, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8) if lbp_vis.max() > 0 else lbp_vis
        lbp_color = cv2.applyColorMap(lbp_disp, cv2.COLORMAP_VIRIDIS)
        lbp_color = cv2.cvtColor(lbp_color, cv2.COLOR_BGR2RGB)
        st.image(lbp_color, caption=f"LBP ({len(lbp_hist)}차원)", use_container_width=True, clamp=True)
        st.caption("결함 표면의 **질감** 패턴을 캡처")
    with feat_cols[2]:
        edge, _, _ = auto_canny(preprocessed)
        ed = np.mean(edge > 0)
        edge_color = cv2.applyColorMap(edge, cv2.COLORMAP_HOT)
        edge_color = cv2.cvtColor(edge_color, cv2.COLOR_BGR2RGB)
        st.image(edge_color, caption=f"Canny Edge (밀도: {ed:.2%})", use_container_width=True, clamp=True)
        st.caption("결함의 **경계선** 추출")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── 노트북 실험 결과 갤러리 ──
    fig_dir = os.path.join(PROJECT_ROOT, "outputs", "figures", "severstal")
    if os.path.isdir(fig_dir):
        _render_nb_galleries(fig_dir)


def _render_nb_galleries(fig_dir):
    """NB01~03 실험 결과 갤러리."""
    galleries = {
        "NB01: 이미지 정렬 & ROI": {
            "01_class_samples.png": "5종 클래스 대표 샘플",
            "01_brightness_dist.png": "클래스별 밝기 분포",
            "01_pipeline_result.png": "전처리 파이프라인 결과",
            "01_normalization_comparison.png": "정규화 방법 비교 (6종)",
            "01_before_after_stats.png": "전처리 전후 통계",
        },
        "NB02: 필터링 & 샤프닝": {
            "02_blur_comparison.png": "블러 방법 비교",
            "02_bilateral_params.png": "Bilateral 파라미터 탐색",
            "02_sharpen_comparison.png": "샤프닝 방법 비교",
            "02_morphology.png": "형태학 연산 결과",
            "02_full_pipeline.png": "통합 파이프라인",
            "02_quantitative_eval.png": "정량 평가",
        },
        "NB03: 에지 & 윤곽선": {
            "03_thresholding.png": "이진화 방법 비교",
            "03_edge_detection.png": "에지 검출 비교",
            "03_contour_detection.png": "윤곽선 검출",
            "03_contour_features_boxplot.png": "클래스별 윤곽선 특징",
            "03_tsne_and_correlation.png": "t-SNE + 상관관계",
        },
    }

    for cat_name, files in galleries.items():
        available = sum(1 for f in files if os.path.exists(os.path.join(fig_dir, f)))
        with st.expander(f"{cat_name} ({available}/{len(files)}장)", expanded=False):
            for fname, caption in files.items():
                fpath = os.path.join(fig_dir, fname)
                if os.path.exists(fpath):
                    st.image(fpath, caption=caption, use_container_width=True)

"""A-2: 배치 검수 분석 — 다중 이미지 일괄 검수 및 통계."""

import streamlit as st
import numpy as np
import os
import sys
import cv2
import time
import matplotlib.pyplot as plt

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

plt.rcParams["font.family"] = "AppleGothic"
plt.rcParams["axes.unicode_minus"] = False


def _badge(letter, color_class="ib-blue"):
    return f'<span class="icon-badge {color_class}">{letter}</span>'


DEFECT_INFO = {
    1: {"name": "PS", "color": "#dc2626"},
    2: {"name": "LS", "color": "#2563eb"},
    3: {"name": "SS", "color": "#ca8a04"},
    4: {"name": "RD", "color": "#7c3aed"},
}


def render_tab_batch(input_image=None):
    """배치 검수 탭."""
    B = _badge

    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("BA", "ib-blue")} 배치 검수 분석</div>',
                unsafe_allow_html=True)
    st.markdown("""<div class="info-box">
        여러 이미지를 한 번에 업로드하여 일괄 검수하고, 결과를 통계적으로 분석합니다.<br>
        결함 분포, 유형별 통계, 검수 결과 요약을 확인할 수 있습니다.
    </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "검수할 이미지를 업로드하세요 (다중 선택 가능)",
        type=["jpg", "jpeg", "png", "bmp"],
        accept_multiple_files=True,
        key="batch_upload"
    )

    if not uploaded_files:
        # 테스트 배치 모드
        st.markdown(f'<div class="section-card"><div class="section-title">'
                    f'{B("TM", "ib-gray")} 테스트 모드</div>', unsafe_allow_html=True)

        patch_dir = os.path.join(PROJECT_ROOT, "data", "severstal_patches")
        if os.path.isdir(patch_dir):
            n_sample = st.slider("테스트 이미지 수", 10, 100, 30, 10, key="batch_n")
            if st.button("테스트 배치 실행", key="batch_test_run"):
                _run_test_batch(patch_dir, n_sample)
        else:
            st.info("`data/severstal_patches/` 폴더가 없습니다.")

        st.markdown('</div>', unsafe_allow_html=True)
        return

    # ── 업로드된 파일 일괄 처리 ──
    if st.button("배치 검수 실행", type="primary", use_container_width=True, key="batch_run"):
        _run_uploaded_batch(uploaded_files)


def _run_test_batch(patch_dir, n_sample):
    """테스트 배치 실행 (Severstal 패치 샘플)."""
    import glob
    import joblib
    import torch

    model_dir = os.path.join(PROJECT_ROOT, "outputs", "models_severstal", "binary_ml")
    scaler_path = os.path.join(model_dir, "binary_scaler.joblib")
    model_path = os.path.join(model_dir, "binary_LightGBM.joblib")

    if not os.path.exists(model_path) or not os.path.exists(scaler_path):
        st.error("Stage 1 ML 모델이 없습니다. 노트북 07을 실행하세요.")
        return

    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)

    from features.feature_pipeline import FeaturePipeline
    pipeline = FeaturePipeline()

    # 샘플 수집
    normal_dir = os.path.join(patch_dir, "normal")
    DEFECT_ABBR = {1: "PS", 2: "LS", 3: "SS", 4: "RD"}
    defect_dirs = [os.path.join(patch_dir, "defect", f"class_{i}_{DEFECT_ABBR[i]}") for i in range(1, 5)]

    images, labels = [], []
    if os.path.isdir(normal_dir):
        files = sorted([f for f in os.listdir(normal_dir) if not f.startswith(".")])[:n_sample // 2]
        for f in files:
            img = cv2.imread(os.path.join(normal_dir, f), cv2.IMREAD_GRAYSCALE)
            if img is not None:
                images.append(img)
                labels.append(0)

    remain = n_sample - len(images)
    per_class = max(1, remain // 4)
    for d in defect_dirs:
        if os.path.isdir(d):
            files = sorted([f for f in os.listdir(d) if not f.startswith(".")])[:per_class]
            for f in files:
                img = cv2.imread(os.path.join(d, f), cv2.IMREAD_GRAYSCALE)
                if img is not None:
                    images.append(img)
                    labels.append(1)

    if not images:
        st.error("이미지를 로드할 수 없습니다.")
        return

    # 추론
    progress = st.progress(0, text="배치 검수 중...")
    results = []
    for i, img in enumerate(images):
        resized = cv2.resize(img, (200, 200))
        feat = pipeline.extract_single(resized).reshape(1, -1)
        feat_scaled = scaler.transform(feat)
        pred = int(model.predict(feat_scaled)[0])
        results.append(pred)
        progress.progress((i + 1) / len(images), text=f"검수 중: {i+1}/{len(images)}")

    progress.empty()
    _display_batch_results(results, images, labels)


def _run_uploaded_batch(uploaded_files):
    """업로드된 파일 배치 처리."""
    import joblib

    model_dir = os.path.join(PROJECT_ROOT, "outputs", "models_severstal", "binary_ml")
    scaler_path = os.path.join(model_dir, "binary_scaler.joblib")
    model_path = os.path.join(model_dir, "binary_LightGBM.joblib")

    if not os.path.exists(model_path) or not os.path.exists(scaler_path):
        st.error("Stage 1 ML 모델이 없습니다.")
        return

    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)

    from features.feature_pipeline import FeaturePipeline
    pipeline = FeaturePipeline()

    images = []
    for f in uploaded_files:
        file_bytes = np.asarray(bytearray(f.read()), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_GRAYSCALE)
        if img is not None:
            images.append(cv2.resize(img, (256, 256)))

    if not images:
        st.error("유효한 이미지가 없습니다.")
        return

    progress = st.progress(0, text="배치 검수 중...")
    results = []
    for i, img in enumerate(images):
        resized = cv2.resize(img, (200, 200))
        feat = pipeline.extract_single(resized).reshape(1, -1)
        feat_scaled = scaler.transform(feat)
        pred = int(model.predict(feat_scaled)[0])
        results.append(pred)
        progress.progress((i + 1) / len(images), text=f"검수 중: {i+1}/{len(images)}")

    progress.empty()
    _display_batch_results(results, images)


def _display_batch_results(results, images, true_labels=None):
    """배치 결과 시각화."""
    B = _badge
    n_total = len(results)
    n_normal = sum(1 for r in results if r == 0)
    n_defect = n_total - n_normal

    # 요약 KPI
    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("SM", "ib-green")} 배치 검수 결과 요약</div>', unsafe_allow_html=True)

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f'<div class="kpi-card"><p class="kpi-label">총 검수</p>'
                    f'<p class="kpi-value">{n_total}장</p></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="kpi-card"><p class="kpi-label">정상</p>'
                    f'<p class="kpi-value" style="color:#059669;">{n_normal}장 ({n_normal/n_total:.0%})</p></div>',
                    unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="kpi-card"><p class="kpi-label">결함</p>'
                    f'<p class="kpi-value" style="color:#dc2626;">{n_defect}장 ({n_defect/n_total:.0%})</p></div>',
                    unsafe_allow_html=True)
    with k4:
        rate = n_defect / n_total * 100 if n_total > 0 else 0
        st.markdown(f'<div class="kpi-card"><p class="kpi-label">결함률</p>'
                    f'<p class="kpi-value" style="color:#ea580c;">{rate:.1f}%</p></div>',
                    unsafe_allow_html=True)

    # 파이차트
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].pie([n_normal, n_defect], labels=["정상", "결함"],
                colors=["#059669", "#dc2626"], autopct="%1.1f%%",
                startangle=90, textprops={"fontsize": 12})
    axes[0].set_title("정상/결함 비율", fontsize=13, fontweight="bold")

    if true_labels:
        from sklearn.metrics import accuracy_score
        acc = accuracy_score(true_labels, results)
        axes[1].bar(["Accuracy"], [acc], color="#2563eb", width=0.3)
        axes[1].set_ylim(0, 1)
        axes[1].set_title(f"검수 정확도: {acc:.1%}", fontsize=13, fontweight="bold")
        axes[1].text(0, acc + 0.03, f"{acc:.1%}", ha="center", fontsize=14, fontweight="bold")
    else:
        axes[1].text(0.5, 0.5, "실제 라벨 없음\n(업로드 모드)", ha="center", va="center",
                     fontsize=12, color="#94a3b8", transform=axes[1].transAxes)
        axes[1].set_title("정확도 (비교 불가)", fontsize=13, fontweight="bold")

    fig.patch.set_facecolor("#fff")
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    st.markdown('</div>', unsafe_allow_html=True)

    # 결함 이미지 갤러리
    if n_defect > 0:
        with st.expander(f"결함 이미지 갤러리 ({n_defect}장)", expanded=False):
            defect_indices = [i for i, r in enumerate(results) if r == 1]
            cols = st.columns(min(5, len(defect_indices)))
            for idx, di in enumerate(defect_indices[:20]):
                with cols[idx % len(cols)]:
                    st.image(images[di], caption=f"#{di+1} 결함",
                             use_container_width=True, clamp=True)

"""B-2: ML vs DL 분류 비교 — Stage 1/Stage 2 전체 모델 성능 비교."""

import streamlit as st
import numpy as np
import os
import sys
import matplotlib.pyplot as plt

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

plt.rcParams["font.family"] = "AppleGothic"
plt.rcParams["axes.unicode_minus"] = False


def _badge(letter, color_class="ib-blue"):
    return f'<span class="icon-badge {color_class}">{letter}</span>'


# ── Stage 1 이진 분류 결과 (NB07, NB08) ──
ML_BINARY_RESULTS = {
    "RandomForest":    {"acc": 0.7200, "f1": 0.7431, "auc": 0.7831, "recall": 0.8100},
    "LightGBM":        {"acc": 0.7200, "f1": 0.7358, "auc": 0.8040, "recall": 0.7800},
    "VotingEnsemble":  {"acc": 0.7150, "f1": 0.7349, "auc": 0.8085, "recall": 0.7900},
    "XGBoost":         {"acc": 0.6950, "f1": 0.7163, "auc": 0.8078, "recall": 0.7700},
    "SVM_RBF":         {"acc": 0.6500, "f1": 0.6667, "auc": 0.7337, "recall": 0.7000},
    "MLP":             {"acc": 0.6500, "f1": 0.5570, "auc": 0.7482, "recall": 0.4400},
    "KNN":             {"acc": 0.5550, "f1": 0.2124, "auc": 0.7064, "recall": 0.1200},
}
DL_BINARY_RESULTS = {
    "ResNet-18 Fine-tune":    {"acc": 0.9150},
    "ResNet-18 Feature Ext.": {"acc": 0.8988},
}

# ── Stage 2 결함 분류 결과 (NB10) ──
ML_DEFECT4_RESULTS = {
    "LightGBM":        {"acc": 0.7979, "f1": 0.7936},
    "XGBoost":         {"acc": 0.7772, "f1": 0.7751},
    "VotingEnsemble":  {"acc": 0.7565, "f1": 0.7560},
    "RandomForest":    {"acc": 0.7098, "f1": 0.7027},
    "SVM_RBF":         {"acc": 0.6891, "f1": 0.6908},
    "MLP":             {"acc": 0.6114, "f1": 0.6150},
    "KNN":             {"acc": 0.5337, "f1": 0.5112},
}
DL_DEFECT4_RESULTS = {
    "ResNet-18 Feature Ext.": {"acc": 0.8860},
    "ResNet-18 Fine-tune":    {"acc": 0.8705},
}


def render_tab_ml_dl_compare():
    """ML vs DL 분류 비교 탭."""
    B = _badge

    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("VS", "ib-red")} ML vs DL 분류 성능 비교</div>', unsafe_allow_html=True)
    st.markdown("""<div class="info-box">
        <strong>7종 ML 모델</strong>과 <strong>2종 DL 모델</strong>의 성능을
        Stage 1 (이진 분류)과 Stage 2 (4종 결함 분류) 양쪽에서 비교합니다.<br><br>
        ML: HOG + LBP + Pixel Stats 등 수작업 특징 → 분류기<br>
        DL: ResNet-18 CNN이 이미지에서 자동으로 특징 학습
    </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Stage 1: 이진 분류 ──
    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("S1", "ib-blue")} Stage 1: 정상 vs 비정상 이진 분류</div>', unsafe_allow_html=True)

    # ML 성능 차트
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    names = list(ML_BINARY_RESULTS.keys())
    accs = [ML_BINARY_RESULTS[n]["acc"] for n in names]
    aucs = [ML_BINARY_RESULTS[n]["auc"] for n in names]
    colors_acc = ["#059669" if a == max(accs) else "#94a3b8" for a in accs]

    axes[0].barh(names, accs, color=colors_acc, height=0.55)
    axes[0].set_xlim(0.45, 0.80)
    axes[0].set_xlabel("Accuracy", fontsize=11)
    axes[0].set_title("ML 7모델 정확도 (이진)", fontsize=13, fontweight="bold")
    axes[0].grid(True, alpha=0.3, axis="x")
    for i, v in enumerate(accs):
        axes[0].text(v + 0.005, i, f"{v:.2%}", va="center", fontsize=9, fontweight="bold")

    # ML vs DL 통합
    all_names = names + list(DL_BINARY_RESULTS.keys())
    all_accs = accs + [DL_BINARY_RESULTS[n]["acc"] for n in DL_BINARY_RESULTS]
    all_colors = ["#94a3b8"] * len(names) + ["#2563eb", "#059669"]

    axes[1].barh(all_names, all_accs, color=all_colors, height=0.55)
    axes[1].set_xlim(0.45, 1.0)
    axes[1].set_xlabel("Accuracy", fontsize=11)
    axes[1].set_title("Stage 1: ML vs DL 전체 비교", fontsize=13, fontweight="bold")
    axes[1].axvline(x=0.9, color="#dc2626", linestyle="--", alpha=0.4, label="90% 기준")
    axes[1].grid(True, alpha=0.3, axis="x")
    axes[1].legend(fontsize=9)
    for i, v in enumerate(all_accs):
        axes[1].text(v + 0.005, i, f"{v:.2%}", va="center", fontsize=8, fontweight="bold")

    fig.patch.set_facecolor("#fff")
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # Stage 1 KPI
    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown('<div class="kpi-card"><p class="kpi-label">ML 최고 (RF/LightGBM)</p>'
                    '<p class="kpi-value" style="color:#7c3aed;">72.00%</p></div>',
                    unsafe_allow_html=True)
    with k2:
        st.markdown('<div class="kpi-card"><p class="kpi-label">DL 최고 (ResNet-18 FT)</p>'
                    '<p class="kpi-value" style="color:#059669;">90.87%</p></div>',
                    unsafe_allow_html=True)
    with k3:
        st.markdown('<div class="kpi-card"><p class="kpi-label">DL vs ML 향상</p>'
                    '<p class="kpi-value" style="color:#dc2626;">+18.87%p</p></div>',
                    unsafe_allow_html=True)

    st.markdown("""<div class="info-box">
        <strong>핵심 발견</strong>: DL(ResNet-18)이 자동 특징 학습으로 ML 대비 <strong>+18.87%p</strong> 향상.<br>
        ML은 HOG/LBP 수작업 특징의 한계로 72% 수준에서 정체.
    </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Stage 2: 4종 결함 분류 ──
    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("S2", "ib-orange")} Stage 2: 4종 결함 세부 분류</div>', unsafe_allow_html=True)

    fig2, axes2 = plt.subplots(1, 2, figsize=(14, 5))

    d4_names = list(ML_DEFECT4_RESULTS.keys())
    d4_accs = [ML_DEFECT4_RESULTS[n]["acc"] for n in d4_names]
    d4_f1s = [ML_DEFECT4_RESULTS[n]["f1"] for n in d4_names]
    colors_d4 = ["#059669" if a == max(d4_accs) else "#94a3b8" for a in d4_accs]

    axes2[0].barh(d4_names, d4_accs, color=colors_d4, height=0.55)
    axes2[0].set_xlim(0.45, 0.85)
    axes2[0].set_xlabel("Accuracy", fontsize=11)
    axes2[0].set_title("ML 모델별 정확도 (4종)", fontsize=13, fontweight="bold")
    axes2[0].grid(True, alpha=0.3, axis="x")
    for i, v in enumerate(d4_accs):
        axes2[0].text(v + 0.003, i, f"{v:.4f}", va="center", fontsize=9, fontweight="bold")

    # ML vs DL 통합 (Stage 2)
    all_s2_names = d4_names + list(DL_DEFECT4_RESULTS.keys())
    all_s2_accs = d4_accs + [DL_DEFECT4_RESULTS[n]["acc"] for n in DL_DEFECT4_RESULTS]
    all_s2_colors = ["#94a3b8"] * len(d4_names) + ["#2563eb", "#059669"]

    axes2[1].barh(all_s2_names, all_s2_accs, color=all_s2_colors, height=0.55)
    axes2[1].set_xlim(0.45, 0.95)
    axes2[1].set_xlabel("Accuracy", fontsize=11)
    axes2[1].set_title("Stage 2: ML vs DL 전체 비교", fontsize=13, fontweight="bold")
    axes2[1].axvline(x=0.8, color="#dc2626", linestyle="--", alpha=0.4, label="80% 기준")
    axes2[1].grid(True, alpha=0.3, axis="x")
    axes2[1].legend(fontsize=9)
    for i, v in enumerate(all_s2_accs):
        axes2[1].text(v + 0.005, i, f"{v:.2%}", va="center", fontsize=8, fontweight="bold")

    fig2.patch.set_facecolor("#fff")
    plt.tight_layout()
    st.pyplot(fig2)
    plt.close(fig2)

    # Stage 2 KPI
    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown('<div class="kpi-card"><p class="kpi-label">ML 최고 (LightGBM)</p>'
                    '<p class="kpi-value" style="color:#7c3aed;">77.72%</p></div>',
                    unsafe_allow_html=True)
    with k2:
        st.markdown('<div class="kpi-card"><p class="kpi-label">DL 최고 (ResNet-18 FT)</p>'
                    '<p class="kpi-value" style="color:#059669;">86.01%</p></div>',
                    unsafe_allow_html=True)
    with k3:
        st.markdown('<div class="kpi-card"><p class="kpi-label">DL vs ML 향상</p>'
                    '<p class="kpi-value" style="color:#dc2626;">+8.29%p</p></div>',
                    unsafe_allow_html=True)

    st.markdown("""<div class="info-box">
        <strong>주목할 점</strong>: Stage 2에서는 Feature Extractor가 Fine-tune보다 <strong>+1.55%p</strong> 우수.<br>
        클래스당 241장이라는 소량 데이터에서 전체 미세 조정은 오히려 과적합 위험.
    </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── NB 실험 결과 갤러리 ──
    fig_dir = os.path.join(PROJECT_ROOT, "outputs", "figures", "severstal")
    if os.path.isdir(fig_dir):
        galleries = {
            "NB04~05: Stage 1 기초 실험": {
                "04_model_comparison.png": "ML 7모델 성능 비교",
                "04_best_confusion_matrix.png": "최고 모델 혼동 행렬",
                "05_dl_training_curves.png": "DL 학습 곡선",
                "05_ml_vs_dl_comparison.png": "ML vs DL 비교",
            },
            "NB07: Stage 1 이진 분류 (ML)": {
                "07_binary_samples.png": "정상/비정상 대표 샘플",
                "07_binary_ml_comparison.png": "ML 7모델 성능 비교",
                "07_best_cm_roc.png": "최고 모델 혼동 행렬 + ROC",
            },
            "NB08: Stage 1 이진 분류 (DL)": {
                "08_dl_learning_curves.png": "DL 학습 곡선",
                "08_dl_confusion_matrix.png": "DL 혼동 행렬",
            },
            "NB10: Stage 2 결함 분류": {
                "10_defect4_samples.png": "4종 결함 샘플",
                "10_defect4_ml_comparison.png": "ML 7모델 비교",
                "10_defect4_dl_curves.png": "DL 학습 곡선",
            },
        }

        for cat_name, files in galleries.items():
            available = sum(1 for f in files if os.path.exists(os.path.join(fig_dir, f)))
            if available > 0:
                with st.expander(f"{cat_name} ({available}/{len(files)}장)", expanded=False):
                    for fname, caption in files.items():
                        fpath = os.path.join(fig_dir, fname)
                        if os.path.exists(fpath):
                            st.image(fpath, caption=caption, use_container_width=True)

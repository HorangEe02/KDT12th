"""Severstal Stage 2: 4종 결함 세부 분류 — ML + DL 결과 탭."""

import streamlit as st
import numpy as np
import os
import sys
import cv2
import time
import torch
import torch.nn.functional as F
import matplotlib.pyplot as plt
import joblib

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.severstal_loader import CLASS_NAMES_KR, CLASS_ABBR

plt.rcParams["font.family"] = "AppleGothic"
plt.rcParams["axes.unicode_minus"] = False


def _badge(letter, color_class="ib-blue"):
    return f'<span class="icon-badge {color_class}">{letter}</span>'


# 4종 결함 정보
DEFECT_INFO = {
    1: {"name": "점상 결함 (PS)", "abbr": "PS", "desc": "표면에 점 형태로 나타나는 결함", "color": "#dc2626"},
    2: {"name": "선형 긁힘 (LS)", "abbr": "LS", "desc": "선형으로 긁힌 자국", "color": "#2563eb"},
    3: {"name": "표면 변색 (SS)", "abbr": "SS", "desc": "색상이 주변과 다른 변색 영역", "color": "#ca8a04"},
    4: {"name": "압연 압흔 (RD)", "abbr": "RD", "desc": "압연 과정에서 생긴 압흔", "color": "#7c3aed"},
}

# ML 실험 결과
ML_DEFECT4_RESULTS = {
    "LightGBM":        {"acc": 0.7772, "f1": 0.7936},
    "XGBoost":         {"acc": 0.7772, "f1": 0.7751},
    "VotingEnsemble":  {"acc": 0.7565, "f1": 0.7560},
    "RandomForest":    {"acc": 0.7098, "f1": 0.7027},
    "SVM_RBF":         {"acc": 0.6891, "f1": 0.6908},
    "MLP":             {"acc": 0.6114, "f1": 0.6150},
    "KNN":             {"acc": 0.5337, "f1": 0.5112},
}

# DL 실험 결과
DL_DEFECT4_RESULTS = {
    "ResNet-18 Fine-tune":    {"acc": 0.8601, "best_acc": 0.8601},
    "ResNet-18 Feature Ext.": {"acc": 0.8705, "best_acc": 0.8705},
}


@st.cache_resource
def _load_defect4_ml(model_path, scaler_path):
    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    return model, scaler


@st.cache_resource
def _load_defect4_dl(model_path, num_classes=4):
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    from deep_learning.models.resnet_transfer import get_resnet18_finetune
    model = get_resnet18_finetune(num_classes=num_classes)
    state = torch.load(model_path, map_location=device, weights_only=False)
    if isinstance(state, dict) and "model_state_dict" in state:
        model.load_state_dict(state["model_state_dict"])
    else:
        model.load_state_dict(state)
    model.to(device)
    model.eval()
    return model, device


def render_tab_severstal_defect(input_image=None):
    """Severstal Stage 2 결함 분류 탭 렌더링."""
    B = _badge

    # ── 개념 소개 ──
    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("S2", "ib-orange")} Stage 2: Severstal 4종 결함 세부 분류</div>',
                unsafe_allow_html=True)
    st.markdown("""<div class="info-box">
        <strong>Stage 2</strong>는 Stage 1에서 "비정상"으로 판별된 이미지를 대상으로
        <strong>4종 결함 유형</strong>을 세부 분류하는 단계입니다.<br><br>
        Severstal은 결함 유형을 ClassId 1~4로만 제공하였으며,
        본 프로젝트에서는 결함 영역의 <strong>형태적 특징(면적, 가로세로비, 밝기 차이)</strong>을
        통계적으로 분석하여 각 클래스에 직관적 명칭을 부여했습니다.
    </div>""", unsafe_allow_html=True)

    # 4종 결함 설명
    cols = st.columns(4)
    for i, (cid, info) in enumerate(DEFECT_INFO.items()):
        with cols[i]:
            st.markdown(f"""
            <div style="text-align:center; padding:12px; background:#f8fafc;
                 border-radius:8px; border-left:4px solid {info['color']};">
                <p style="color:{info['color']}; font-size:1.3rem; font-weight:700; margin:0;">
                    {info['abbr']}</p>
                <p style="color:#334155; font-size:0.9rem; margin:4px 0; font-weight:600;">
                    {info['name']}</p>
                <p style="color:#64748b; font-size:0.75rem; margin:0;">{info['desc']}</p>
            </div>""", unsafe_allow_html=True)

    st.markdown("""<div class="info-box">
        <strong>데이터 구성</strong>: PS(897장), LS(241장), SS(5,150장), RD(801장)<br>
        <strong>클래스 불균형 대응</strong>: 균형 샘플링 (클래스당 241장) 적용<br>
        <strong>특징 추출</strong>: 1,944D 벡터 (HOG + LBP + Pixel Stats + Contour + Edge, 64×64)
    </div>""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── ML 성능 비교 ──
    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("ML", "ib-purple")} ML 모델 4종 분류 성능</div>',
                unsafe_allow_html=True)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    names = list(ML_DEFECT4_RESULTS.keys())
    accs = [ML_DEFECT4_RESULTS[n]["acc"] for n in names]
    f1s = [ML_DEFECT4_RESULTS[n]["f1"] for n in names]

    colors_acc = ["#059669" if a == max(accs) else "#94a3b8" for a in accs]
    colors_f1 = ["#2563eb" if f == max(f1s) else "#94a3b8" for f in f1s]

    axes[0].barh(names, accs, color=colors_acc, height=0.55)
    axes[0].set_xlim(0.45, 0.85)
    axes[0].set_xlabel("Accuracy", fontsize=11)
    axes[0].set_title("ML 모델별 정확도 (4종)", fontsize=13, fontweight="bold")
    axes[0].grid(True, alpha=0.3, axis="x")
    for i, v in enumerate(accs):
        axes[0].text(v + 0.003, i, f"{v:.4f}", va="center", fontsize=9, fontweight="bold")

    axes[1].barh(names, f1s, color=colors_f1, height=0.55)
    axes[1].set_xlim(0.45, 0.85)
    axes[1].set_xlabel("F1 Score (macro)", fontsize=11)
    axes[1].set_title("ML 모델별 F1 Score (4종)", fontsize=13, fontweight="bold")
    axes[1].grid(True, alpha=0.3, axis="x")
    for i, v in enumerate(f1s):
        axes[1].text(v + 0.003, i, f"{v:.4f}", va="center", fontsize=9, fontweight="bold")

    fig.patch.set_facecolor("#fff")
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── DL 성능 비교 ──
    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("DL", "ib-green")} DL 모델 4종 분류 성능</div>',
                unsafe_allow_html=True)

    dl_col1, dl_col2 = st.columns(2)
    with dl_col1:
        st.markdown(f"""
        <div class="kpi-card">
            <p class="kpi-label">ResNet-18 Fine-tune</p>
            <p class="kpi-value">86.01%</p>
        </div>""", unsafe_allow_html=True)
    with dl_col2:
        st.markdown(f"""
        <div class="kpi-card">
            <p class="kpi-label">ResNet-18 Feature Ext.</p>
            <p class="kpi-value" style="color:#2563eb;">87.05%</p>
        </div>""", unsafe_allow_html=True)

    st.markdown("""<div class="info-box">
        <strong>주목할 점</strong>: 4종 분류에서는 Feature Extractor가 Fine-tune보다 <strong>+1.55%p</strong> 우수<br>
        → 클래스당 241장이라는 소량 데이터에서 전체 미세 조정은 오히려 과적합 위험<br>
        → Feature Extractor 방식이 소량 데이터에 더 안정적
    </div>""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── ML vs DL 통합 비교 ──
    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("VS", "ib-red")} Stage 2: ML vs DL 전체 비교</div>',
                unsafe_allow_html=True)

    fig2, ax2 = plt.subplots(figsize=(10, 5))
    all_names = list(ML_DEFECT4_RESULTS.keys()) + list(DL_DEFECT4_RESULTS.keys())
    all_accs = [ML_DEFECT4_RESULTS[n]["acc"] for n in ML_DEFECT4_RESULTS] + \
               [DL_DEFECT4_RESULTS[n]["acc"] for n in DL_DEFECT4_RESULTS]
    all_colors = ["#94a3b8"] * len(ML_DEFECT4_RESULTS) + ["#2563eb", "#059669"]

    bars = ax2.barh(all_names, all_accs, color=all_colors, height=0.55)
    ax2.set_xlim(0.45, 0.95)
    ax2.set_xlabel("Accuracy", fontsize=12)
    ax2.set_title("Stage 2 결함 분류: ML vs DL 전체 비교", fontsize=14, fontweight="bold")
    ax2.axvline(x=0.8, color="#dc2626", linestyle="--", alpha=0.5, label="80% 기준선")
    ax2.grid(True, alpha=0.3, axis="x")
    ax2.legend(fontsize=9)
    for i, v in enumerate(all_accs):
        ax2.text(v + 0.005, i, f"{v:.2%}", va="center", fontsize=9, fontweight="bold")

    fig2.patch.set_facecolor("#fff")
    plt.tight_layout()
    st.pyplot(fig2)
    plt.close(fig2)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── 실시간 추론 ──
    if input_image is not None:
        st.markdown(f'<div class="section-card"><div class="section-title">'
                    f'{B("RT", "ib-orange")} 실시간 4종 결함 분류</div>',
                    unsafe_allow_html=True)

        model_dir_ml = os.path.join(PROJECT_ROOT, "outputs", "models_severstal", "defect4_ml")
        model_dir_dl = os.path.join(PROJECT_ROOT, "outputs", "models_severstal", "defect4_dl")

        available = {}
        scaler_path = os.path.join(model_dir_ml, "defect4_scaler.joblib")
        if os.path.exists(scaler_path):
            for mname in ["LightGBM", "XGBoost", "SVM_RBF"]:
                mpath = os.path.join(model_dir_ml, f"defect4_{mname}.joblib")
                if os.path.exists(mpath):
                    available[f"ML: {mname}"] = ("ml", mpath, scaler_path)

        fe_path = os.path.join(model_dir_dl, "defect4_resnet18_feature_extractor.pt")
        if os.path.exists(fe_path):
            available["DL: ResNet-18 Feature Ext."] = ("dl", fe_path, None)
        ft_path = os.path.join(model_dir_dl, "defect4_resnet18_finetune.pt")
        if os.path.exists(ft_path):
            available["DL: ResNet-18 Fine-tune"] = ("dl", ft_path, None)

        if available:
            sel = st.selectbox("분류 모델 선택", list(available.keys()),
                               key="defect4_model_select")
            mtype, mpath, spath = available[sel]

            # 결함 분류 매핑 (0-indexed → ClassId)
            idx_to_cid = {0: 1, 1: 2, 2: 3, 3: 4}

            try:
                if mtype == "ml":
                    from features.feature_pipeline import FeaturePipeline
                    model, scaler = _load_defect4_ml(mpath, spath)

                    t0 = time.time()
                    img = cv2.resize(input_image, (64, 64))
                    if img.ndim == 3:
                        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    pipeline = FeaturePipeline()
                    feat = pipeline.extract_single(img).reshape(1, -1)
                    feat_scaled = scaler.transform(feat)
                    pred_idx = int(model.predict(feat_scaled)[0])
                    elapsed = (time.time() - t0) * 1000
                    cid = idx_to_cid[pred_idx]

                    prob = None
                    if hasattr(model, "predict_proba"):
                        prob = model.predict_proba(feat_scaled)[0]

                else:
                    model, device = _load_defect4_dl(mpath, num_classes=4)

                    t0 = time.time()
                    img = cv2.resize(input_image, (224, 224))
                    if img.ndim == 2:
                        img_3ch = np.stack([img] * 3, axis=0).astype(np.float32) / 255.0
                    else:
                        img_3ch = img.transpose(2, 0, 1).astype(np.float32) / 255.0
                    mean = np.array([0.485, 0.456, 0.406]).reshape(3, 1, 1)
                    std = np.array([0.229, 0.224, 0.225]).reshape(3, 1, 1)
                    img_norm = (img_3ch - mean) / std
                    tensor = torch.from_numpy(img_norm).float().unsqueeze(0).to(device)
                    with torch.no_grad():
                        logits = model(tensor)
                        probs_t = F.softmax(logits, dim=1).cpu().numpy()[0]
                    pred_idx = int(probs_t.argmax())
                    elapsed = (time.time() - t0) * 1000
                    cid = idx_to_cid[pred_idx]
                    prob = probs_t

                info = DEFECT_INFO[cid]
                r1, r2 = st.columns([1, 1])
                with r1:
                    st.image(input_image, caption="입력 이미지", use_container_width=True, clamp=True)
                with r2:
                    st.markdown(f"""
                    <div style="text-align:center; padding:20px; background:#f8fafc;
                         border-radius:12px; border:2px solid {info['color']};">
                        <p style="color:#64748b; margin:0;">결함 분류 결과</p>
                        <p style="color:{info['color']}; font-size:2rem; font-weight:700; margin:8px 0;">
                            {info['name']}</p>
                        <p style="color:#475569; font-size:0.9rem;">{info['desc']}</p>
                        <p style="color:#94a3b8; font-size:0.85rem; margin-top:8px;">
                            {sel} | {elapsed:.1f}ms</p>
                    </div>""", unsafe_allow_html=True)

                    if prob is not None:
                        st.markdown("**클래스별 확률:**")
                        for idx in range(4):
                            c = idx_to_cid[idx]
                            p = float(prob[idx])
                            st.markdown(f"- {DEFECT_INFO[c]['abbr']} ({DEFECT_INFO[c]['name']}): **{p:.1%}**")

            except Exception as e:
                st.error(f"추론 중 오류: {e}")
        else:
            st.info("학습된 모델이 없습니다. 노트북 10을 실행하세요.")

        st.markdown('</div>', unsafe_allow_html=True)

    # ── NB10 실험 결과 갤러리 ──
    fig_dir = os.path.join(PROJECT_ROOT, "outputs", "figures", "severstal")
    if os.path.isdir(fig_dir):
        with st.expander("📊 NB10 실험 결과 — 4종 결함 분류", expanded=False):
            nb_figs = {
                "10_defect4_samples.png": "4종 결함 대표 샘플 이미지",
                "10_defect4_ml_comparison.png": "ML 7모델 4종 분류 성능 비교",
                "10_defect4_dl_curves.png": "DL 학습 곡선 (ResNet-18 Fine-tune)",
            }
            for fname, caption in nb_figs.items():
                fpath = os.path.join(fig_dir, fname)
                if os.path.exists(fpath):
                    st.image(fpath, caption=caption, use_container_width=True)

    # ── KPI 요약 ──
    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("KP", "ib-teal")} Stage 2 핵심 성과</div>',
                unsafe_allow_html=True)

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown('<div class="kpi-card"><p class="kpi-label">ML 최고 (LightGBM)</p>'
                    '<p class="kpi-value" style="color:#7c3aed;">77.72%</p></div>',
                    unsafe_allow_html=True)
    with k2:
        st.markdown('<div class="kpi-card"><p class="kpi-label">DL 최고 (ResNet-18 FT)</p>'
                    '<p class="kpi-value">86.01%</p></div>',
                    unsafe_allow_html=True)
    with k3:
        st.markdown('<div class="kpi-card"><p class="kpi-label">DL vs ML 향상</p>'
                    '<p class="kpi-value" style="color:#dc2626;">+8.29%p</p></div>',
                    unsafe_allow_html=True)
    with k4:
        st.markdown('<div class="kpi-card"><p class="kpi-label">결함 유형 수</p>'
                    '<p class="kpi-value" style="color:#2563eb;">4종</p></div>',
                    unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

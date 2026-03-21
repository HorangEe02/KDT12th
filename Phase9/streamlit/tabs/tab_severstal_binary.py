"""Severstal Stage 1: 정상 vs 비정상 이진 분류 — ML + DL 결과 탭."""

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

from utils.severstal_loader import CLASS_NAMES_KR, CLASS_ABBR, BINARY_NAMES_KR as BINARY_NAMES

plt.rcParams["font.family"] = "AppleGothic"
plt.rcParams["axes.unicode_minus"] = False


def _badge(letter, color_class="ib-blue"):
    return f'<span class="icon-badge {color_class}">{letter}</span>'


# ── ML 실험 결과 (NB07 최신 실행 기준) ──
ML_BINARY_RESULTS = {
    "RandomForest":    {"acc": 0.7200, "f1": 0.7431, "auc": 0.7831, "recall": 0.8100},
    "LightGBM":        {"acc": 0.7200, "f1": 0.7358, "auc": 0.8040, "recall": 0.7800},
    "VotingEnsemble":  {"acc": 0.7300, "f1": 0.7349, "auc": 0.8085, "recall": 0.7900},
    "XGBoost":         {"acc": 0.6950, "f1": 0.7163, "auc": 0.8078, "recall": 0.7700},
    "SVM_RBF":         {"acc": 0.6500, "f1": 0.6667, "auc": 0.7337, "recall": 0.7000},
    "MLP":             {"acc": 0.6500, "f1": 0.5570, "auc": 0.7482, "recall": 0.4400},
    "KNN":             {"acc": 0.5550, "f1": 0.2124, "auc": 0.7064, "recall": 0.1200},
}

# ── DL 실험 결과 (NB08 최신 실행 기준) ──
DL_BINARY_RESULTS = {
    "ResNet-18 Fine-tune":       {"acc": 0.9087, "best_acc": 0.9087},
    "ResNet-18 Feature Ext.":    {"acc": 0.8988, "best_acc": 0.8988},
}


@st.cache_resource
def _load_binary_ml_model(model_path, scaler_path):
    """이진 분류 ML 모델 + 스케일러 로드."""
    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    return model, scaler


@st.cache_resource
def _load_binary_dl_model(model_path, num_classes=2):
    """이진 분류 DL 모델 로드."""
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


def _predict_binary_ml(model, scaler, image):
    """ML 이진 분류 추론."""
    from features.feature_pipeline import FeaturePipeline

    t0 = time.time()
    img = cv2.resize(image, (200, 200)) if image.shape[:2] != (200, 200) else image
    if img.ndim == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    pipeline = FeaturePipeline()
    feat = pipeline.extract_single(img).reshape(1, -1)
    feat_scaled = scaler.transform(feat)
    pred = model.predict(feat_scaled)[0]
    elapsed = (time.time() - t0) * 1000

    prob = None
    if hasattr(model, "predict_proba"):
        prob = model.predict_proba(feat_scaled)[0]

    return {
        "predicted_label": int(pred),
        "predicted_class": BINARY_NAMES[int(pred)],
        "confidence": float(prob.max()) if prob is not None else 0.0,
        "probabilities": {BINARY_NAMES[i]: float(prob[i]) for i in range(len(prob))} if prob is not None else {},
        "total_time_ms": elapsed,
    }


def _predict_binary_dl(model, device, image):
    """DL 이진 분류 추론."""
    t0 = time.time()
    img = cv2.resize(image, (224, 224))
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
        probs = F.softmax(logits, dim=1).cpu().numpy()[0]

    pred = int(probs.argmax())
    elapsed = (time.time() - t0) * 1000

    return {
        "predicted_label": pred,
        "predicted_class": BINARY_NAMES[pred],
        "confidence": float(probs.max()),
        "probabilities": {BINARY_NAMES[i]: float(probs[i]) for i in range(len(probs))},
        "total_time_ms": elapsed,
    }


def render_tab_severstal_binary(input_image=None):
    """Severstal Stage 1 이진 분류 탭 렌더링."""
    B = _badge

    # ── 개념 소개 ──
    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("S1", "ib-blue")} Stage 1: Severstal 정상 vs 비정상 이진 분류</div>',
                unsafe_allow_html=True)
    st.markdown("""<div class="info-box">
        <strong>Stage 1</strong>은 철강 표면 이미지를 <strong>정상(0)</strong>과 <strong>비정상(1)</strong>으로
        분류하는 첫 번째 단계입니다.<br><br>
        • <strong>데이터</strong>: Severstal 256×256 패치 (정상 120,583장 + 결함 30,233장)<br>
        • <strong>ML 모델</strong>: 7종 (SVM, RF, KNN, MLP, XGBoost, LightGBM, Voting Ensemble)<br>
        • <strong>DL 모델</strong>: ResNet-18 Fine-tune / Feature Extractor<br>
        • <strong>특징 추출</strong>: HOG + LBP + Pixel Stats + Contour + Edge → 20,916D 벡터 (200×200)
    </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── ML 성능 비교 ──
    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("ML", "ib-purple")} ML 모델 성능 비교 (7종)</div>',
                unsafe_allow_html=True)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Accuracy 비교
    names = list(ML_BINARY_RESULTS.keys())
    accs = [ML_BINARY_RESULTS[n]["acc"] for n in names]
    colors_acc = ["#059669" if a == max(accs) else "#94a3b8" for a in accs]

    bars1 = axes[0].barh(names, accs, color=colors_acc, height=0.55)
    axes[0].set_xlim(0.65, 0.85)
    axes[0].set_xlabel("Accuracy", fontsize=11)
    axes[0].set_title("ML 모델별 정확도", fontsize=13, fontweight="bold")
    axes[0].grid(True, alpha=0.3, axis="x")
    for i, v in enumerate(accs):
        axes[0].text(v + 0.003, i, f"{v:.4f}", va="center", fontsize=9, fontweight="bold")

    # AUC-ROC 비교
    aucs = [ML_BINARY_RESULTS[n]["auc"] for n in names]
    colors_auc = ["#2563eb" if a == max(aucs) else "#94a3b8" for a in aucs]

    bars2 = axes[1].barh(names, aucs, color=colors_auc, height=0.55)
    axes[1].set_xlim(0.75, 0.95)
    axes[1].set_xlabel("AUC-ROC", fontsize=11)
    axes[1].set_title("ML 모델별 AUC-ROC", fontsize=13, fontweight="bold")
    axes[1].grid(True, alpha=0.3, axis="x")
    for i, v in enumerate(aucs):
        axes[1].text(v + 0.003, i, f"{v:.4f}", va="center", fontsize=9, fontweight="bold")

    fig.patch.set_facecolor("#fff")
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # ML 성능 테이블
    st.markdown("#### ML 모델 상세 성능")
    table_md = "| 모델 | Accuracy | F1 Score | AUC-ROC | Recall |\n"
    table_md += "|------|----------|----------|---------|--------|\n"
    for name in names:
        r = ML_BINARY_RESULTS[name]
        best = " ⭐" if r["acc"] == max(accs) else ""
        table_md += f"| {name}{best} | {r['acc']:.4f} | {r['f1']:.4f} | {r['auc']:.4f} | {r['recall']:.4f} |\n"
    st.markdown(table_md)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── DL 성능 비교 ──
    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("DL", "ib-green")} DL 모델 성능 비교</div>',
                unsafe_allow_html=True)

    dl_col1, dl_col2 = st.columns(2)
    with dl_col1:
        st.markdown(f"""
        <div class="kpi-card">
            <p class="kpi-label">ResNet-18 Fine-tune</p>
            <p class="kpi-value">90.87%</p>
        </div>""", unsafe_allow_html=True)
    with dl_col2:
        st.markdown(f"""
        <div class="kpi-card">
            <p class="kpi-label">ResNet-18 Feature Extractor</p>
            <p class="kpi-value" style="color:#2563eb;">89.88%</p>
        </div>""", unsafe_allow_html=True)

    st.markdown("""<div class="info-box">
        <strong>딥러닝 분석</strong>:<br>
        • Fine-tune이 Feature Extractor보다 <strong>+1.62%p</strong> 우수<br>
        • 전체 레이어 미세 조정이 Severstal 도메인에 더 적합<br>
        • ML 최고(VotingEnsemble 73.00%) 대비 DL(ResNet-18 FT 90.87%) → <strong>+17.87%p 향상</strong>
    </div>""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── ML vs DL 통합 비교 ──
    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("VS", "ib-red")} Stage 1: ML vs DL 비교</div>',
                unsafe_allow_html=True)

    fig2, ax2 = plt.subplots(figsize=(10, 5))
    all_names = list(ML_BINARY_RESULTS.keys()) + list(DL_BINARY_RESULTS.keys())
    all_accs = [ML_BINARY_RESULTS[n]["acc"] for n in ML_BINARY_RESULTS] + \
               [DL_BINARY_RESULTS[n]["acc"] for n in DL_BINARY_RESULTS]
    all_colors = ["#94a3b8"] * len(ML_BINARY_RESULTS) + ["#059669", "#2563eb"]

    bars = ax2.barh(all_names, all_accs, color=all_colors, height=0.55)
    ax2.set_xlim(0.65, 1.0)
    ax2.set_xlabel("Accuracy", fontsize=12)
    ax2.set_title("Stage 1 이진 분류: ML vs DL 전체 비교", fontsize=14, fontweight="bold")
    ax2.axvline(x=0.9, color="#dc2626", linestyle="--", alpha=0.5, label="90% 기준선")
    ax2.grid(True, alpha=0.3, axis="x")
    ax2.legend(fontsize=9)
    for i, v in enumerate(all_accs):
        ax2.text(v + 0.005, i, f"{v:.2%}", va="center", fontsize=9, fontweight="bold")

    fig2.patch.set_facecolor("#fff")
    plt.tight_layout()
    st.pyplot(fig2)
    plt.close(fig2)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── 실시간 추론 (모델이 있는 경우) ──
    if input_image is not None:
        st.markdown(f'<div class="section-card"><div class="section-title">'
                    f'{B("RT", "ib-orange")} 실시간 이진 분류 추론</div>',
                    unsafe_allow_html=True)

        model_dir_ml = os.path.join(PROJECT_ROOT, "outputs", "models_severstal", "binary_ml")
        model_dir_dl = os.path.join(PROJECT_ROOT, "outputs", "models_severstal", "binary_dl")

        # 사용 가능한 모델 목록
        available_models = {}
        scaler_path = os.path.join(model_dir_ml, "binary_scaler.joblib")
        if os.path.exists(scaler_path):
            for mname in ["LightGBM", "XGBoost", "SVM_RBF", "RandomForest"]:
                mpath = os.path.join(model_dir_ml, f"binary_{mname}.joblib")
                if os.path.exists(mpath):
                    available_models[f"ML: {mname}"] = ("ml", mpath, scaler_path)

        ft_path = os.path.join(model_dir_dl, "binary_resnet18_finetune.pt")
        if os.path.exists(ft_path):
            available_models["DL: ResNet-18 Fine-tune"] = ("dl", ft_path, None)
        fe_path = os.path.join(model_dir_dl, "binary_resnet18_feature_extractor.pt")
        if os.path.exists(fe_path):
            available_models["DL: ResNet-18 Feature Ext."] = ("dl", fe_path, None)

        if available_models:
            sel = st.selectbox("추론 모델 선택", list(available_models.keys()),
                               key="binary_model_select")
            mtype, mpath, spath = available_models[sel]

            try:
                if mtype == "ml":
                    model, scaler = _load_binary_ml_model(mpath, spath)
                    result = _predict_binary_ml(model, scaler, input_image)
                else:
                    model, device = _load_binary_dl_model(mpath)
                    result = _predict_binary_dl(model, device, input_image)

                pred = result["predicted_class"]
                conf = result["confidence"]
                is_defect = result["predicted_label"] == 1
                color = "#dc2626" if is_defect else "#059669"
                bg = "#fef2f2" if is_defect else "#f0fdf4"
                icon = "⚠️" if is_defect else "✅"

                r1, r2 = st.columns([1, 1])
                with r1:
                    st.image(input_image, caption="입력 이미지", use_container_width=True, clamp=True)
                with r2:
                    st.markdown(f"""
                    <div style="text-align:center; padding:20px; background:{bg};
                         border-radius:12px; border:2px solid {color};">
                        <p style="font-size:2.5rem; margin:0;">{icon}</p>
                        <p style="color:{color}; font-size:2rem; font-weight:700; margin:8px 0;">{pred}</p>
                        <p style="color:#475569;">신뢰도: <strong>{conf:.1%}</strong></p>
                        <p style="color:#94a3b8; font-size:0.85rem;">{sel} | {result['total_time_ms']:.1f}ms</p>
                    </div>""", unsafe_allow_html=True)

                    if result["probabilities"]:
                        st.markdown("**확률 분포:**")
                        for cls_name, prob in sorted(result["probabilities"].items(), key=lambda x: -x[1]):
                            bar_width = int(prob * 100)
                            st.markdown(f"- {cls_name}: **{prob:.1%}**")

            except Exception as e:
                st.error(f"추론 중 오류: {e}")
        else:
            st.info("학습된 모델이 없습니다. 노트북 07, 08을 실행하세요.")

        st.markdown('</div>', unsafe_allow_html=True)

    # ── 노트북 학습 실험 결과 ──
    fig_dir = os.path.join(PROJECT_ROOT, "outputs", "figures", "severstal")
    if os.path.isdir(fig_dir):
        with st.expander("📊 노트북 학습 실험 결과 — ML & DL 학습 상세", expanded=False):
            st.markdown("""<div class="info-box">
                노트북 04~05에서 수행한 ML·DL 학습 실험의 상세 시각화입니다.
            </div>""", unsafe_allow_html=True)

            nb_figs = {
                "04_model_comparison.png": "ML 7모델 성능 비교 (Accuracy, F1, AUC-ROC)",
                "04_best_confusion_matrix.png": "ML 최고 모델 혼동 행렬",
                "05_dl_training_curves.png": "DL 학습 곡선 (Loss & Accuracy per Epoch)",
                "05_ml_vs_dl_comparison.png": "ML vs DL 정확도 종합 비교",
                "05_dl_confusion_matrix.png": "DL 최고 모델 혼동 행렬 & Classification Report",
                "07_binary_samples.png": "NB07: Severstal 이진 분류 샘플 갤러리",
                "07_binary_ml_comparison.png": "NB07: Severstal 이진 ML 7모델 성능 비교",
                "07_best_cm_roc.png": "NB07: 최고 모델 혼동 행렬 & ROC 곡선",
                "08_dl_learning_curves.png": "NB08: Severstal 이진 DL 학습 곡선",
                "08_dl_confusion_matrix.png": "NB08: Severstal 이진 DL 혼동 행렬",
            }

            for fname, caption in nb_figs.items():
                fpath = os.path.join(fig_dir, fname)
                if os.path.exists(fpath):
                    st.image(fpath, caption=caption, use_container_width=True)

    # ── KPI 요약 ──
    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("KP", "ib-teal")} Stage 1 핵심 성과</div>',
                unsafe_allow_html=True)

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown('<div class="kpi-card"><p class="kpi-label">ML 최고 (VotingEnsemble)</p>'
                    '<p class="kpi-value" style="color:#7c3aed;">73.00%</p></div>',
                    unsafe_allow_html=True)
    with k2:
        st.markdown('<div class="kpi-card"><p class="kpi-label">DL 최고 (ResNet-18 FT)</p>'
                    '<p class="kpi-value">90.87%</p></div>',
                    unsafe_allow_html=True)
    with k3:
        st.markdown('<div class="kpi-card"><p class="kpi-label">DL vs ML 향상</p>'
                    '<p class="kpi-value" style="color:#dc2626;">+17.87%p</p></div>',
                    unsafe_allow_html=True)
    with k4:
        st.markdown('<div class="kpi-card"><p class="kpi-label">ML AUC 최고</p>'
                    '<p class="kpi-value" style="color:#2563eb;">0.8085</p></div>',
                    unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

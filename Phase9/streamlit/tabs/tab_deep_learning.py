"""Phase 2 딥러닝 탭 — ResNet-18/Custom CNN 추론 + Grad-CAM + 실험 비교."""

import streamlit as st
import numpy as np
import os
import sys
import cv2
import torch
import torch.nn.functional as F
import matplotlib.pyplot as plt
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

plt.rcParams["font.family"] = "AppleGothic"
plt.rcParams["axes.unicode_minus"] = False


def _badge(letter, color_class="ib-blue"):
    return f'<span class="icon-badge {color_class}">{letter}</span>'


KR_MAP = {
    "crazing": "균열", "inclusion": "개재물", "patches": "패치",
    "pitted_surface": "구멍", "rolled-in_scale": "압연스케일", "scratches": "스크래치",
}
COLOR_MAP = {
    "균열": "#dc2626", "개재물": "#ea580c", "패치": "#ca8a04",
    "구멍": "#16a34a", "압연스케일": "#2563eb", "스크래치": "#9333ea",
}

DL_MODELS = {
    "ResNet-18 Fine-tune": ("resnet18_finetune.pt", "resnet18"),
    "ResNet-18 Feature Ext.": ("resnet18_feature_extractor.pt", "resnet18_fe"),
    "Custom CNN": ("custom_cnn.pt", "custom_cnn"),
}


@st.cache_resource
def _load_dl_model(model_path, model_type, class_names):
    """딥러닝 모델 로드 (캐시)."""
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    ckpt = torch.load(model_path, map_location=device, weights_only=False)

    if model_type == "custom_cnn":
        from deep_learning.models.custom_cnn import CustomCNN
        model = CustomCNN(num_classes=len(class_names))
    elif model_type == "resnet18_fe":
        from deep_learning.models.resnet_transfer import get_resnet18_feature_extractor
        model = get_resnet18_feature_extractor(num_classes=len(class_names))
    else:
        from deep_learning.models.resnet_transfer import get_resnet18_finetune
        model = get_resnet18_finetune(num_classes=len(class_names))

    model.load_state_dict(ckpt["model_state_dict"])
    model.to(device)
    model.eval()
    return model, device, ckpt


def _predict_dl(model, image, device, class_names, model_type):
    """딥러닝 추론."""
    from torchvision import transforms

    img = image.copy()
    if img.ndim == 2:
        img_pil = img
    else:
        img_pil = img

    t0 = time.time()

    if model_type == "custom_cnn":
        # 1채널, 200x200
        tensor = torch.from_numpy(img_pil).float().unsqueeze(0).unsqueeze(0) / 255.0
    else:
        # 3채널, 224x224 (ResNet)
        img_resized = cv2.resize(img_pil, (224, 224))
        img_3ch = np.stack([img_resized] * 3, axis=0).astype(np.float32) / 255.0
        # ImageNet 정규화
        mean = np.array([0.485, 0.456, 0.406]).reshape(3, 1, 1)
        std = np.array([0.229, 0.224, 0.225]).reshape(3, 1, 1)
        img_3ch = (img_3ch - mean) / std
        tensor = torch.from_numpy(img_3ch).float().unsqueeze(0)

    tensor = tensor.to(device)

    with torch.no_grad():
        logits = model(tensor)
        probs = F.softmax(logits, dim=1).cpu().numpy()[0]

    pred_label = int(probs.argmax())
    confidence = float(probs.max())
    elapsed = (time.time() - t0) * 1000

    pred_class = KR_MAP.get(class_names[pred_label], class_names[pred_label])
    prob_dict = {}
    for i, cn in enumerate(class_names):
        prob_dict[KR_MAP.get(cn, cn)] = float(probs[i])

    return {
        "predicted_class": pred_class,
        "predicted_label": pred_label,
        "confidence": confidence,
        "probabilities": prob_dict,
        "total_time_ms": elapsed,
        "input_tensor": tensor,
    }


def render_tab_deep_learning(input_image, selected_class=None, class_names=None):
    """Phase 2 딥러닝 탭 렌더링."""
    B = _badge

    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("DL","ib-purple")} 딥러닝 기반 결함 분류</div>',
                unsafe_allow_html=True)

    st.markdown("""<div class="info-box">
        <strong>딥러닝(Deep Learning)</strong>은 사람이 특징을 수동으로 설계하지 않아도
        AI가 스스로 이미지에서 중요한 패턴을 학습하는 기법입니다.<br><br>
        <strong>전통 ML</strong>: 사람이 HOG, LBP 등의 특징을 설계 → SVM/RF로 분류<br>
        <strong>딥러닝</strong>: CNN이 자동으로 특징 학습 → 더 높은 정확도 기대
    </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── 모델 선택 & 추론 ──
    model_dir = os.path.join(PROJECT_ROOT, "outputs", "models_dl")
    available = {}
    for name, (fname, mtype) in DL_MODELS.items():
        path = os.path.join(model_dir, fname)
        if os.path.exists(path):
            available[name] = (path, mtype)

    if not available:
        st.warning("학습된 딥러닝 모델이 없습니다. `notebooks/05_deep_learning.ipynb`을 실행하세요.")
        return

    col_sel, col_info = st.columns([1, 2])
    with col_sel:
        selected_model_name = st.selectbox("딥러닝 모델 선택", list(available.keys()))
    with col_info:
        with st.expander("모델 설명", expanded=False):
            st.markdown("""
            - **ResNet-18 Fine-tune**: 1,400만 장 사전학습 → 전체 미세조정. 최고 성능.
            - **ResNet-18 Feature Ext.**: 사전학습 가중치 고정, 분류기만 학습. 빠르지만 약간 낮은 성능.
            - **Custom CNN**: 4층 CNN을 처음부터 학습. 소규모 데이터에 과적합 위험.
            """)

    model_path, model_type = available[selected_model_name]
    model, device, ckpt = _load_dl_model(model_path, model_type, class_names)

    # 추론
    result = _predict_dl(model, input_image, device, class_names, model_type)
    pred_class = result["predicted_class"]
    confidence = result["confidence"]
    pred_color = COLOR_MAP.get(pred_class, "#2563eb")

    # ── 판정 결과 ──
    st.markdown(f'<div class="section-card"><div class="section-title">{B("AI","ib-blue")} DL 판정 결과</div>',
                unsafe_allow_html=True)

    r1, r2 = st.columns([1, 1])
    with r1:
        st.markdown(f"""
        <div style="text-align:center; padding:20px; background:#f8fafc;
             border-radius:12px; border:2px solid {pred_color};">
            <p style="color:#64748b; margin:0;">{selected_model_name} 예측</p>
            <p style="color:{pred_color}; font-size:2.2rem; font-weight:700; margin:8px 0;">{pred_class}</p>
            <p style="color:#059669; font-size:1.2rem;">
                신뢰도: <strong>{confidence:.1%}</strong></p>
            <p style="color:#94a3b8; font-size:0.85rem;">
                추론 시간: {result['total_time_ms']:.1f}ms |
                학습 정확도: {ckpt.get('best_accuracy', 0):.1%}</p>
        </div>""", unsafe_allow_html=True)

        if selected_class:
            actual_kr = KR_MAP.get(selected_class, selected_class)
            is_correct = actual_kr == pred_class
            label = "PASS 정분류" if is_correct else "FAIL 오분류"
            bg = "#f0fdf4" if is_correct else "#fef2f2"
            tc = "#166534" if is_correct else "#991b1b"
            st.markdown(f"""
            <div style="text-align:center; padding:10px; background:{bg};
                 border-radius:8px; margin-top:10px;">
                <p style="color:{tc}; font-weight:700; margin:0;">{label} — 실제: {actual_kr}</p>
            </div>""", unsafe_allow_html=True)

    with r2:
        if result["probabilities"]:
            sorted_probs = sorted(result["probabilities"].items(), key=lambda x: -x[1])
            fig, ax = plt.subplots(figsize=(6, 4))
            names = [p[0] for p in sorted_probs]
            vals = [p[1] for p in sorted_probs]
            colors = [pred_color if n == pred_class else "#cbd5e1" for n in names]
            ax.barh(names, vals, color=colors, height=0.55)
            ax.set_xlim(0, 1)
            ax.set_xlabel("확률")
            ax.set_facecolor("#fff")
            fig.patch.set_facecolor("#fff")
            for i, v in enumerate(vals):
                ax.text(v + 0.02, i, f"{v:.1%}", va="center", fontsize=9)
            for spine in ax.spines.values():
                spine.set_color("#e2e8f0")
            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Grad-CAM ──
    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("GC","ib-orange")} Grad-CAM — AI가 주목하는 영역</div>',
                unsafe_allow_html=True)
    st.markdown("""<div class="info-box">
        <strong>Grad-CAM</strong>은 딥러닝 모델이 이미지의 <strong>어디를 보고</strong> 결함을 판단했는지
        히트맵으로 보여줍니다. 빨간색 영역 = AI가 중요하게 본 부분.
    </div>""", unsafe_allow_html=True)

    try:
        from deep_learning.gradcam import GradCAM, overlay_gradcam
        target_layer = model.get_gradcam_target_layer()
        gc = GradCAM(model, target_layer)
        heatmap = gc(result["input_tensor"], target_class=result["predicted_label"])
        # heatmap을 원본 크기로 리사이즈
        heatmap_resized = cv2.resize(heatmap, (input_image.shape[1], input_image.shape[0]))
        overlay = overlay_gradcam(input_image, heatmap_resized, alpha=0.4)

        gc1, gc2, gc3 = st.columns(3)
        with gc1:
            st.image(input_image, caption="원본 이미지", use_container_width=True, clamp=True)
        with gc2:
            fig_hm, ax_hm = plt.subplots(figsize=(4, 4))
            ax_hm.imshow(heatmap_resized, cmap="jet")
            ax_hm.axis("off")
            ax_hm.set_title("Grad-CAM 히트맵", fontsize=11)
            fig_hm.patch.set_facecolor("#fff")
            plt.tight_layout()
            st.pyplot(fig_hm)
            plt.close(fig_hm)
        with gc3:
            st.image(overlay, caption="Grad-CAM 오버레이", use_container_width=True, clamp=True)
    except Exception as e:
        st.caption(f"Grad-CAM 생성 중 오류: {e}")

    st.markdown('</div>', unsafe_allow_html=True)

    # ── 저장된 실험 결과 이미지 ──
    fig_dir = os.path.join(PROJECT_ROOT, "outputs", "figures")

    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("EX","ib-green")} 딥러닝 실험 결과</div>',
                unsafe_allow_html=True)

    exp_col1, exp_col2 = st.columns(2)

    with exp_col1:
        tc_path = os.path.join(fig_dir, "05_dl_training_curves.png")
        if os.path.exists(tc_path):
            st.image(tc_path, caption="학습 곡선 비교 (Loss & Accuracy)", use_container_width=True)

    with exp_col2:
        exp_path = os.path.join(fig_dir, "05_dl_experiment_comparison.png")
        if os.path.exists(exp_path):
            st.image(exp_path, caption="전통 ML vs 딥러닝 성능 비교", use_container_width=True)

    cm_path = os.path.join(fig_dir, "05_dl_best_confusion_matrix.png")
    if os.path.exists(cm_path):
        st.image(cm_path, caption="최고 성능 모델 혼동행렬", use_container_width=True)

    gc_grid = os.path.join(fig_dir, "05_dl_gradcam_grid.png")
    if os.path.exists(gc_grid):
        st.image(gc_grid, caption="Grad-CAM: 6종 결함별 AI 주목 영역", use_container_width=True)

    # 성능 요약 KPI
    st.markdown(f'<div class="section-title">{B("KP","ib-teal")} 딥러닝 핵심 성과</div>',
                unsafe_allow_html=True)
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown('<div class="kpi-card"><p class="kpi-label">ResNet-18 Fine-tune</p>'
                    '<p class="kpi-value">100%</p></div>', unsafe_allow_html=True)
    with k2:
        st.markdown('<div class="kpi-card"><p class="kpi-label">ResNet-18 Feature Ext.</p>'
                    '<p class="kpi-value" style="color:#2563eb;">99.7%</p></div>', unsafe_allow_html=True)
    with k3:
        st.markdown('<div class="kpi-card"><p class="kpi-label">Custom CNN</p>'
                    '<p class="kpi-value" style="color:#7c3aed;">96.9%</p></div>', unsafe_allow_html=True)
    with k4:
        st.markdown('<div class="kpi-card"><p class="kpi-label">전통 ML 대비 향상</p>'
                    '<p class="kpi-value" style="color:#dc2626;">+6.9%</p></div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

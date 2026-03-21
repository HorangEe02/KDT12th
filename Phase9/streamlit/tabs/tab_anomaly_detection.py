"""Phase 3 이상 탐지 탭 — 진짜 정상 데이터 기반 + 2단계 파이프라인."""

import streamlit as st
import numpy as np
import os
import sys
import cv2
import torch
import matplotlib.pyplot as plt
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

plt.rcParams["font.family"] = "AppleGothic"
plt.rcParams["axes.unicode_minus"] = False


def _badge(letter, color_class="ib-blue"):
    return f'<span class="icon-badge {color_class}">{letter}</span>'


# 최신 실험 결과 (notebook 09 Severstal 50 epochs 기반)
AUROC_RESULTS = {
    "Autoencoder": 0.6806,
    "Isolation Forest": 0.420,
    "One-Class SVM": 0.423,
}

KR_MAP = {"crazing": "균열", "inclusion": "개재물", "patches": "패치",
          "pitted_surface": "구멍", "rolled-in_scale": "압연스케일", "scratches": "스크래치"}


@st.cache_resource
def _load_ae_model(model_path):
    import math
    from anomaly_detection.models.autoencoder import ConvAutoencoder
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    ckpt = torch.load(model_path, map_location=device, weights_only=False)

    # ── 체크포인트 형식 자동 감지 ──
    # Case 1: {"model_state_dict": ..., "in_channels": ..., ...} 래핑 형식
    # Case 2: 순수 state_dict (encoder.0.weight, ...)
    if "model_state_dict" in ckpt:
        state_dict = ckpt["model_state_dict"]
        in_channels = ckpt.get("in_channels", 1)
        image_size = ckpt.get("image_size", 128)
        latent_dim = ckpt.get("latent_dim", 128)
    else:
        # 순수 state_dict → 가중치 shape에서 파라미터 역추론
        state_dict = ckpt
        in_channels = ckpt["encoder.0.weight"].shape[1]           # (32, in_ch, 4, 4)
        latent_dim = ckpt["fc_encode.weight"].shape[0]            # (latent, flat)
        flat_dim = ckpt["fc_encode.weight"].shape[1]              # 256 * feat^2
        feat_size = int(math.sqrt(flat_dim // 256))
        image_size = feat_size * (2 ** 4)                         # 4번 다운샘플링

    model = ConvAutoencoder(
        in_channels=in_channels,
        image_size=image_size,
        latent_dim=latent_dim,
    )
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()
    return model, device


@st.cache_resource
def _load_traditional(model_path, model_type):
    if model_type == "isolation_forest":
        from anomaly_detection.models.traditional_ad import IsolationForestAD
        return IsolationForestAD.load(model_path)
    else:
        from anomaly_detection.models.traditional_ad import OneClassSVMAD
        return OneClassSVMAD.load(model_path)


def _predict_ae(model, device, image, threshold=0.002):
    from anomaly_detection.models.autoencoder import compute_anomaly_map, compute_anomaly_score
    t0 = time.time()
    # 모델의 학습 입력 크기에 맞춰 리사이즈
    ae_size = model.image_size   # 체크포인트에서 추론된 값 (예: 192)
    img = cv2.resize(image, (ae_size, ae_size)) if image.shape[:2] != (ae_size, ae_size) else image
    tensor = torch.from_numpy(img).float().unsqueeze(0).unsqueeze(0) / 255.0
    tensor = tensor.to(device)
    with torch.no_grad():
        recon = model(tensor)
    amap = compute_anomaly_map(tensor[0][0].cpu().numpy(), recon[0][0].cpu().numpy())
    score = compute_anomaly_score(amap)
    elapsed = (time.time() - t0) * 1000
    return {
        "anomaly_score": float(score), "anomaly_map": amap,
        "reconstruction": recon[0][0].cpu().numpy(),
        "total_time_ms": elapsed, "threshold": threshold,
        "is_anomaly": float(score) > threshold,
    }


def _predict_traditional(model, image):
    t0 = time.time()
    result = model.predict(image)
    result["total_time_ms"] = (time.time() - t0) * 1000
    return result


def render_tab_anomaly_detection(input_image, selected_class=None):
    B = _badge

    # ── 개념 소개 ──
    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("AD", "ib-orange")} 이상 탐지란?</div>', unsafe_allow_html=True)
    st.markdown("""<div class="info-box">
        <strong>기존 분류 방식</strong>: "이 결함은 6종 중 어떤 것인가?" (지도 학습, 라벨 필요)<br>
        <strong>이상 탐지 방식</strong>: <strong>"이것은 정상인가, 비정상인가?"</strong> (비지도 학습, 정상 데이터만 필요)<br><br>
        <strong>왜 중요한가?</strong><br>
        • 새로운 결함 유형이 나타나도 즉시 감지 → 학습하지 않은 7번째 결함도 잡아냄<br>
        • 라벨링 비용 절감 → 정상 이미지만 있으면 학습 가능<br>
        • 히트맵으로 결함 위치까지 시각화 가능
    </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── 정상 데이터 설명 ──
    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("ND", "ib-green")} 정상 데이터 구성</div>', unsafe_allow_html=True)
    st.markdown("""<div class="info-box">
        이번 프로젝트에서는 <strong>진짜 결함 없는 금속 표면</strong>을 정상 데이터로 사용합니다:<br><br>
        • <strong>NEU 크롭</strong>: 원본 결함 이미지에서 바운딩박스(결함 영역)를 제외한 깨끗한 영역을 크롭<br>
        • <strong>Severstal CSV</strong>: Kaggle 대회 데이터에서 결함 없는 강철 표면 이미지 활용<br>
        • <strong>합성 텍스처</strong>: 정상 패턴을 학습하여 생성한 보조 데이터<br><br>
        → 총 <strong>~1,800장</strong>의 정상 이미지로 학습, 6종 결함 1,800장은 테스트에만 사용
    </div>""", unsafe_allow_html=True)

    normal_fig = os.path.join(PROJECT_ROOT, "outputs", "figures", "06_real_normal_vs_defect.png")
    if os.path.exists(normal_fig):
        st.image(normal_fig, caption="정상 데이터 vs 결함 데이터 비교", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── 이상 탐지 추론 ──
    # 모델 검색 경로 (우선순위: models_severstal/anomaly → models_ad)
    model_dirs = [
        os.path.join(PROJECT_ROOT, "outputs", "models_severstal", "anomaly"),
        os.path.join(PROJECT_ROOT, "outputs", "models_ad"),
    ]

    AD_MODELS = {}

    # Autoencoder — 여러 파일명 패턴 탐색
    ae_candidates = [
        "autoencoder_severstal.pt",
        "autoencoder_real_normal.pt",
        "autoencoder.pt",
    ]
    for mdir in model_dirs:
        if AD_MODELS.get("Autoencoder (복원 기반)"):
            break
        for fname in ae_candidates:
            ae_path = os.path.join(mdir, fname)
            if os.path.exists(ae_path):
                AD_MODELS["Autoencoder (복원 기반)"] = (ae_path, "autoencoder")
                break

    # 전통 ML 이상 탐지 모델
    for name, fname, mtype in [
        ("Isolation Forest (트리 기반)", "isolation_forest.pkl", "isolation_forest"),
        ("One-Class SVM (경계 학습)", "one_class_svm.pkl", "one_class_svm"),
    ]:
        for mdir in model_dirs:
            path = os.path.join(mdir, fname)
            if os.path.exists(path):
                AD_MODELS[name] = (path, mtype)
                break

    if not AD_MODELS:
        st.warning("학습된 이상 탐지 모델이 없습니다. `notebooks/09_severstal_anomaly.ipynb`을 실행하세요.")
        return

    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("DT", "ib-blue")} 이상 탐지 추론</div>', unsafe_allow_html=True)

    col_m, col_i = st.columns([1, 2])
    with col_m:
        selected_ad = st.selectbox("이상 탐지 모델", list(AD_MODELS.keys()))
        with st.expander("모델 설명", expanded=False):
            st.markdown("""
            - **Autoencoder**: 정상 이미지 복원 패턴을 학습. 결함 이미지는 복원이 잘 안 됨 → 복원 오차가 높으면 이상.
            - **Isolation Forest**: 정상 데이터의 특징을 트리로 분리. 쉽게 고립되는 데이터 = 이상치.
            - **One-Class SVM**: 정상 데이터를 감싸는 경계면 학습. 경계 밖 = 이상.
            """)

    model_path, model_type = AD_MODELS[selected_ad]

    try:
        if model_type == "autoencoder":
            ae_model, device = _load_ae_model(model_path)
            result = _predict_ae(ae_model, device, input_image)
        else:
            trad_model = _load_traditional(model_path, model_type)
            result = _predict_traditional(trad_model, input_image)
    except Exception as e:
        st.error(f"추론 중 오류: {e}")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    score = result.get("anomaly_score", 0)
    threshold = result.get("threshold", 0.5)
    is_anomaly = result.get("is_anomaly", score > threshold)

    # ── 판정 결과 ──
    with col_i:
        status = "비정상 (결함 의심)" if is_anomaly else "정상 (결함 없음)"
        color = "#dc2626" if is_anomaly else "#059669"
        bg = "#fef2f2" if is_anomaly else "#f0fdf4"
        icon = "⚠️" if is_anomaly else "✅"

        st.markdown(f"""
        <div style="text-align:center; padding:20px; background:{bg};
             border-radius:12px; border:2px solid {color};">
            <p style="font-size:2.5rem; margin:0;">{icon}</p>
            <p style="color:{color}; font-size:1.8rem; font-weight:700; margin:8px 0;">{status}</p>
            <p style="color:#475569; margin:0;">
                이상 점수: <strong style="font-size:1.2rem;">{score:.6f}</strong>
                <span style="color:#94a3b8;"> (임계값: {threshold:.6f})</span>
            </p>
            <p style="color:#94a3b8; font-size:0.85rem; margin-top:8px;">
                {selected_ad} | {result['total_time_ms']:.1f}ms
            </p>
        </div>""", unsafe_allow_html=True)

    # ── 히트맵 시각화 ──
    amap = result.get("anomaly_map")
    if amap is not None:
        fig, axes = plt.subplots(1, 3, figsize=(12, 4))
        axes[0].imshow(input_image, cmap="gray")
        axes[0].set_title("원본", fontsize=11, fontweight="bold"); axes[0].axis("off")

        axes[1].imshow(amap, cmap="jet")
        axes[1].set_title("이상 히트맵", fontsize=11, fontweight="bold"); axes[1].axis("off")

        img_rgb = cv2.cvtColor(input_image, cv2.COLOR_GRAY2RGB) if input_image.ndim == 2 else input_image.copy()
        amap_r = cv2.resize(amap, (img_rgb.shape[1], img_rgb.shape[0]))
        amap_n = ((amap_r - amap_r.min()) / (amap_r.max() - amap_r.min() + 1e-8) * 255).astype(np.uint8)
        hm = cv2.applyColorMap(amap_n, cv2.COLORMAP_JET)
        overlay = cv2.addWeighted(img_rgb, 0.6, hm, 0.4, 0)
        axes[2].imshow(cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB))
        axes[2].set_title("오버레이 (빨간=이상)", fontsize=11, fontweight="bold"); axes[2].axis("off")

        fig.patch.set_facecolor("#fff")
        plt.tight_layout()
        st.pyplot(fig); plt.close(fig)
    else:
        st.info("이 모델은 히트맵을 생성하지 않습니다 (전체 이미지 점수만 계산).")

    # AE 복원
    recon = result.get("reconstruction")
    if recon is not None:
        with st.expander("Autoencoder 복원 비교", expanded=False):
            st.markdown("""<div class="info-box">
                왼쪽=원본, 오른쪽=AI 복원. 정상이면 잘 복원되지만, 결함 부분은 복원이 어려워 차이 발생.
            </div>""", unsafe_allow_html=True)
            rc1, rc2 = st.columns(2)
            with rc1:
                st.image(input_image, caption="원본", use_container_width=True, clamp=True)
            with rc2:
                recon_d = (recon * 255).astype(np.uint8) if recon.max() <= 1.0 else recon.astype(np.uint8)
                st.image(recon_d, caption="AE 복원", use_container_width=True, clamp=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── 2단계 파이프라인 설명 ──
    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("2S", "ib-teal")} 2단계 검수 파이프라인</div>', unsafe_allow_html=True)

    st.markdown("""<div class="info-box">
        실제 제조 현장에서는 이상 탐지와 결함 분류를 <strong>결합</strong>하여 사용합니다:<br><br>
        <strong>Stage 1 (이상 탐지)</strong>: "이 표면에 결함이 있는가?" → 정상이면 통과, 비정상이면 Stage 2로<br>
        <strong>Stage 2 (결함 분류)</strong>: "6종 중 어떤 결함인가?" → ResNet-18으로 결함 유형 특정<br><br>
        <strong>장점</strong>: 새로운 결함도 Stage 1에서 감지 + 기존 결함은 Stage 2에서 정확히 분류
    </div>""", unsafe_allow_html=True)

    # 2단계 파이프라인 데모 (AE가 선택된 경우)
    DEFECT_NAMES = {0: "점상 결함 (PS)", 1: "선형 긁힘 (LS)", 2: "표면 변색 (SS)", 3: "압연 압흔 (RD)"}

    if model_type == "autoencoder" and is_anomaly:
        st.markdown(f"#### 이 이미지에 대한 2단계 파이프라인 결과")
        st.markdown(f"**Stage 1**: 비정상 판정 (이상 점수 {score:.6f} > 임계값 {threshold:.6f})")

        # Stage 2: Severstal 4종 결함 분류 (DL 우선 → ML 폴백)
        import torch.nn.functional as _F
        s2_model_dir = os.path.join(PROJECT_ROOT, "outputs", "models_severstal")
        s2_dl_ft = os.path.join(s2_model_dir, "defect4_dl", "defect4_resnet18_finetune.pt")
        s2_dl_fe = os.path.join(s2_model_dir, "defect4_dl", "defect4_resnet18_feature_extractor.pt")
        s2_ml = os.path.join(s2_model_dir, "defect4_ml", "defect4_LightGBM.joblib")
        s2_scaler = os.path.join(s2_model_dir, "defect4_ml", "defect4_scaler.joblib")

        s2_done = False

        # DL 추론 시도
        for s2_path, s2_label in [(s2_dl_ft, "ResNet-18 Fine-tune"), (s2_dl_fe, "ResNet-18 Feature Ext.")]:
            if os.path.exists(s2_path):
                try:
                    from deep_learning.models.resnet_transfer import get_resnet18_finetune
                    s2_device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
                    s2_model = get_resnet18_finetune(num_classes=4)
                    s2_state = torch.load(s2_path, map_location=s2_device, weights_only=False)
                    if isinstance(s2_state, dict) and "model_state_dict" in s2_state:
                        s2_model.load_state_dict(s2_state["model_state_dict"])
                    else:
                        s2_model.load_state_dict(s2_state)
                    s2_model.to(s2_device).eval()

                    # 이미지 전처리 (224x224, ImageNet 정규화)
                    s2_img = cv2.resize(input_image, (224, 224))
                    if s2_img.ndim == 2:
                        s2_3ch = np.stack([s2_img]*3, axis=0).astype(np.float32) / 255.0
                    else:
                        s2_3ch = s2_img.transpose(2,0,1).astype(np.float32) / 255.0
                    s2_mean = np.array([0.485,0.456,0.406]).reshape(3,1,1)
                    s2_std = np.array([0.229,0.224,0.225]).reshape(3,1,1)
                    s2_tensor = torch.from_numpy((s2_3ch - s2_mean) / s2_std).float().unsqueeze(0).to(s2_device)

                    with torch.no_grad():
                        s2_logits = s2_model(s2_tensor)
                        s2_probs = _F.softmax(s2_logits, dim=1).cpu().numpy()[0]
                    s2_pred = int(s2_probs.argmax())
                    defect_type = DEFECT_NAMES.get(s2_pred, f"Class {s2_pred}")
                    confidence = float(s2_probs.max())

                    st.markdown(f"""
                    <div style="background:#eff6ff; border:1px solid #bfdbfe; border-radius:8px; padding:16px; margin:8px 0;">
                        <strong>Stage 2 결함 분류</strong>:
                        <span style="color:#dc2626; font-weight:700; font-size:1.2rem;">{defect_type}</span>
                        (신뢰도: {confidence:.1%})<br>
                        <span style="color:#64748b; font-size:0.85rem;">모델: {s2_label}</span>
                    </div>""", unsafe_allow_html=True)
                    s2_done = True
                    break
                except Exception as e:
                    st.warning(f"DL Stage 2 실패 ({s2_label}): {e}")

        # ML 폴백
        if not s2_done and os.path.exists(s2_ml) and os.path.exists(s2_scaler):
            try:
                import joblib as _jl
                from features.feature_pipeline import FeaturePipeline
                s2_clf = _jl.load(s2_ml)
                s2_sc = _jl.load(s2_scaler)
                s2_img = cv2.resize(input_image, (64, 64))
                if s2_img.ndim == 3:
                    s2_img = cv2.cvtColor(s2_img, cv2.COLOR_BGR2GRAY)
                feat = FeaturePipeline().extract_single(s2_img).reshape(1, -1)
                feat_scaled = s2_sc.transform(feat)
                s2_pred = int(s2_clf.predict(feat_scaled)[0])
                defect_type = DEFECT_NAMES.get(s2_pred, f"Class {s2_pred}")

                st.markdown(f"""
                <div style="background:#eff6ff; border:1px solid #bfdbfe; border-radius:8px; padding:16px; margin:8px 0;">
                    <strong>Stage 2 결함 분류 (ML)</strong>:
                    <span style="color:#dc2626; font-weight:700; font-size:1.2rem;">{defect_type}</span><br>
                    <span style="color:#64748b; font-size:0.85rem;">모델: LightGBM (77.72%)</span>
                </div>""", unsafe_allow_html=True)
                s2_done = True
            except Exception as e:
                st.warning(f"ML Stage 2 실패: {e}")

        if not s2_done:
            st.info("Stage 2 모델이 없습니다. 노트북 08(DL) 또는 10(ML)을 실행하세요.")

    elif model_type == "autoencoder" and not is_anomaly:
        st.success("Stage 1에서 **정상** 판정 → Stage 2 불필요 → 통과")

    st.markdown('</div>', unsafe_allow_html=True)

    # ── 실험 결과 이미지 ──
    fig_dir = os.path.join(PROJECT_ROOT, "outputs", "figures", "severstal")

    with st.expander("📊 Autoencoder 학습 실험 결과", expanded=False):
        st.markdown("""<div class="info-box">
            노트북 06에서 수행한 Autoencoder 이상 탐지 학습의 상세 결과입니다.
        </div>""", unsafe_allow_html=True)

        nb_figs = {
            "06_ae_loss_curve.png": "Autoencoder 학습 곡선 (Train Loss per Epoch)",
            "06_ae_reconstruction.png": "정상 vs 결함 복원 비교 (Original → Reconstructed → Difference)",
            "06_auroc_evaluation.png": "AUROC · ROC 커브 · 이상 점수 분포",
            "09_anomaly_results.png": "NB09: Severstal 이상탐지 결과 (50 epochs)",
            "09_reconstruction.png": "NB09: Severstal 정상/결함 복원 비교",
        }

        for fname, caption in nb_figs.items():
            fpath = os.path.join(fig_dir, fname)
            if os.path.exists(fpath):
                st.image(fpath, caption=caption, use_container_width=True)

    # AUROC KPI
    st.markdown(f'<div class="section-title">{B("KP", "ib-teal")} 핵심 성과 지표</div>',
                unsafe_allow_html=True)
    st.markdown("""<div class="info-box">
        <strong>AUROC</strong>: 정상과 비정상을 얼마나 잘 구분하는지의 지표 (1.0 = 완벽, 0.5 = 랜덤).<br>
        <strong>Recall</strong>: 실제 결함 중 몇 %를 잡아냈는가 (높을수록 불량 누출 적음).
    </div>""", unsafe_allow_html=True)

    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown('<div class="kpi-card"><p class="kpi-label">AE AUROC</p>'
                    '<p class="kpi-value" style="color:#dc2626;">0.6806</p></div>', unsafe_allow_html=True)
    with k2:
        st.markdown('<div class="kpi-card"><p class="kpi-label">AE Recall</p>'
                    '<p class="kpi-value" style="color:#059669;">93.2%</p></div>', unsafe_allow_html=True)
    with k3:
        st.markdown('<div class="kpi-card"><p class="kpi-label">AE F1</p>'
                    '<p class="kpi-value" style="color:#2563eb;">0.7339</p></div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

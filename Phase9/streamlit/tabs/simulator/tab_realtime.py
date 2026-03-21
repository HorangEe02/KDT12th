"""A-1: 실시간 통합 검수 — 2-Stage + 이상탐지 + Grad-CAM 통합 추론."""

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

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

plt.rcParams["font.family"] = "AppleGothic"
plt.rcParams["axes.unicode_minus"] = False


def _badge(letter, color_class="ib-blue"):
    return f'<span class="icon-badge {color_class}">{letter}</span>'


BINARY_NAMES = {0: "정상", 1: "비정상"}
DEFECT_INFO = {
    1: {"name": "점상 결함 (PS)", "abbr": "PS", "color": "#dc2626"},
    2: {"name": "선형 긁힘 (LS)", "abbr": "LS", "color": "#2563eb"},
    3: {"name": "표면 변색 (SS)", "abbr": "SS", "color": "#ca8a04"},
    4: {"name": "압연 압흔 (RD)", "abbr": "RD", "color": "#7c3aed"},
}


# ── 캐시 모델 로더 ──
@st.cache_resource
def _load_binary_ml(model_path, scaler_path):
    return joblib.load(model_path), joblib.load(scaler_path)


@st.cache_resource
def _load_binary_dl(model_path, num_classes=2):
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


@st.cache_resource
def _load_defect4_ml(model_path, scaler_path):
    return joblib.load(model_path), joblib.load(scaler_path)


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


@st.cache_resource
def _load_ae_model(model_path):
    import math
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    from anomaly_detection.models.autoencoder import ConvAutoencoder
    ckpt = torch.load(model_path, map_location=device, weights_only=False)

    # 체크포인트 형식 자동 감지
    if isinstance(ckpt, dict) and "model_state_dict" in ckpt:
        state_dict = ckpt["model_state_dict"]
        in_channels = ckpt.get("in_channels", 1)
        image_size = ckpt.get("image_size", 128)
        latent_dim = ckpt.get("latent_dim", 128)
    else:
        # 순수 state_dict → 가중치에서 파라미터 역추론
        state_dict = ckpt
        in_channels = ckpt["encoder.0.weight"].shape[1]
        latent_dim = ckpt["fc_encode.weight"].shape[0]
        flat_dim = ckpt["fc_encode.weight"].shape[1]
        feat_size = int(math.sqrt(flat_dim // 256))
        image_size = feat_size * (2 ** 4)

    model = ConvAutoencoder(in_channels=in_channels, image_size=image_size, latent_dim=latent_dim)
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()
    return model, device


def _dl_predict(model, device, image, size=224, num_classes=2):
    """DL 추론 공통 함수."""
    img = cv2.resize(image, (size, size))
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
    return int(probs.argmax()), probs


def _ae_predict(model, device, image):
    """Autoencoder 이상 점수 계산."""
    ae_size = model.image_size   # 체크포인트에서 추론된 입력 크기
    img = cv2.resize(image, (ae_size, ae_size))
    if img.ndim == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    tensor = torch.from_numpy(img.astype(np.float32) / 255.0).unsqueeze(0).unsqueeze(0).to(device)
    with torch.no_grad():
        recon = model(tensor)
    diff = (tensor - recon).abs()
    score = float(diff.mean().cpu())
    heatmap = diff.squeeze().cpu().numpy()
    return score, heatmap, recon.squeeze().cpu().numpy()


def run_full_inspection(image, config):
    """전체 2-Stage + 이상탐지 파이프라인 실행."""
    results = {"timings": {}}
    total_t0 = time.time()

    # ── Stage 1: 이진 분류 ──
    t0 = time.time()
    if config["stage1_type"] == "dl" and config.get("stage1_dl"):
        model, device = config["stage1_dl"]
        pred, probs = _dl_predict(model, device, image, size=224, num_classes=2)
        results["stage1"] = {"pred": pred, "label": BINARY_NAMES[pred], "probs": probs}
    elif config.get("stage1_ml"):
        from features.feature_pipeline import FeaturePipeline
        model, scaler = config["stage1_ml"]
        img = cv2.resize(image, (200, 200))
        if img.ndim == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        pipeline = FeaturePipeline()
        feat = pipeline.extract_single(img).reshape(1, -1)
        feat_scaled = scaler.transform(feat)
        pred = int(model.predict(feat_scaled)[0])
        prob = model.predict_proba(feat_scaled)[0] if hasattr(model, "predict_proba") else None
        results["stage1"] = {"pred": pred, "label": BINARY_NAMES[pred], "probs": prob}
    else:
        results["stage1"] = None
    results["timings"]["stage1"] = (time.time() - t0) * 1000

    # ── Stage 2: 결함 분류 (비정상일 때만) ──
    if results.get("stage1") and results["stage1"]["pred"] == 1:
        t0 = time.time()
        if config["stage2_type"] == "dl" and config.get("stage2_dl"):
            model, device = config["stage2_dl"]
            pred_idx, probs = _dl_predict(model, device, image, size=224, num_classes=4)
            cid = pred_idx + 1
            results["stage2"] = {"pred_idx": pred_idx, "class_id": cid, "probs": probs,
                                 "name": DEFECT_INFO[cid]["name"]}
        elif config.get("stage2_ml"):
            from features.feature_pipeline import FeaturePipeline
            model, scaler = config["stage2_ml"]
            img = cv2.resize(image, (64, 64))
            if img.ndim == 3:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            pipeline = FeaturePipeline()
            feat = pipeline.extract_single(img).reshape(1, -1)
            feat_scaled = scaler.transform(feat)
            pred_idx = int(model.predict(feat_scaled)[0])
            cid = pred_idx + 1
            prob = model.predict_proba(feat_scaled)[0] if hasattr(model, "predict_proba") else None
            results["stage2"] = {"pred_idx": pred_idx, "class_id": cid, "probs": prob,
                                 "name": DEFECT_INFO[cid]["name"]}
        else:
            results["stage2"] = None
        results["timings"]["stage2"] = (time.time() - t0) * 1000
    else:
        results["stage2"] = None

    # ── 이상탐지 ──
    if config.get("use_anomaly") and config.get("ae_model"):
        t0 = time.time()
        model, device = config["ae_model"]
        score, heatmap, recon = _ae_predict(model, device, image)
        results["anomaly"] = {"score": score, "heatmap": heatmap, "recon": recon}
        results["timings"]["anomaly"] = (time.time() - t0) * 1000
    else:
        results["anomaly"] = None

    results["timings"]["total"] = (time.time() - total_t0) * 1000
    return results


def _discover_models():
    """사용 가능한 모델 탐색 → (s1_options, s2_options, ae_path, has_ae)."""
    model_dir = os.path.join(PROJECT_ROOT, "outputs", "models_severstal")
    bin_ml_dir = os.path.join(model_dir, "binary_ml")
    bin_dl_dir = os.path.join(model_dir, "binary_dl")
    d4_ml_dir = os.path.join(model_dir, "defect4_ml")
    d4_dl_dir = os.path.join(model_dir, "defect4_dl")
    ad_dir = os.path.join(model_dir, "anomaly")

    # Stage 1
    s1_options = {}
    bin_scaler = os.path.join(bin_ml_dir, "binary_scaler.joblib")
    if os.path.exists(bin_scaler):
        for mname in ["LightGBM", "RandomForest", "XGBoost"]:
            mp = os.path.join(bin_ml_dir, f"binary_{mname}.joblib")
            if os.path.exists(mp):
                s1_options[f"ML: {mname}"] = ("ml", mp, bin_scaler)
    for fname, label in [("binary_resnet18_finetune.pt", "DL: ResNet-18 FT"),
                          ("binary_resnet18_feature_extractor.pt", "DL: ResNet-18 FE")]:
        fp = os.path.join(bin_dl_dir, fname)
        if os.path.exists(fp):
            s1_options[label] = ("dl", fp, None)

    # Stage 2
    s2_options = {}
    d4_scaler = os.path.join(d4_ml_dir, "defect4_scaler.joblib")
    if os.path.exists(d4_scaler):
        for mname in ["LightGBM", "XGBoost", "RandomForest"]:
            mp = os.path.join(d4_ml_dir, f"defect4_{mname}.joblib")
            if os.path.exists(mp):
                s2_options[f"ML: {mname}"] = ("ml", mp, d4_scaler)
    for fname, label in [("defect4_resnet18_feature_extractor.pt", "DL: ResNet-18 FE"),
                          ("defect4_resnet18_finetune.pt", "DL: ResNet-18 FT")]:
        fp = os.path.join(d4_dl_dir, fname)
        if os.path.exists(fp):
            s2_options[label] = ("dl", fp, None)

    # 이상탐지
    ae_path = None
    for _ae_fname in ["autoencoder_severstal.pt", "autoencoder_real_normal.pt", "autoencoder.pt"]:
        _ae_cand = os.path.join(ad_dir, _ae_fname)
        if os.path.exists(_ae_cand):
            ae_path = _ae_cand
            break

    return s1_options, s2_options, ae_path, ae_path is not None


def _match_setting_to_option(setting_name, options_dict):
    """파이프라인 설정의 모델명 → 실시간 검수의 옵션키로 매핑.

    예: "DL: ResNet-18 FT" → "DL: ResNet-18 FT" (직접 매칭)
        "ML: LightGBM" → "ML: LightGBM" (직접 매칭)
    """
    if setting_name in options_dict:
        return setting_name
    # 부분 매칭 시도 (FT→Fine-tune 등 이전 이름 호환)
    for key in options_dict:
        if setting_name.replace(" ", "") in key.replace(" ", ""):
            return key
    return None


def render_tab_realtime(input_image, preprocess_fn=None):
    """실시간 통합 검수 탭."""
    B = _badge

    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("RT", "ib-green")} 실시간 통합 검수</div>',
                unsafe_allow_html=True)
    st.markdown("""<div class="info-box">
        이미지 1장을 투입하면 <strong>2-Stage 파이프라인</strong>이 자동으로 실행됩니다.<br>
        Stage 1 (정상/비정상) -> 비정상 시 Stage 2 (4종 결함 분류) -> 이상탐지 히트맵<br>
        <strong>파이프라인 설정</strong> 페이지에서 모델 조합과 이상탐지를 미리 설정할 수 있습니다.
    </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if input_image is None:
        st.info("위의 이미지 입력에서 이미지를 선택하거나 업로드하세요.")
        return

    # ── 모델 발견 ──
    s1_options, s2_options, ae_path, has_ae = _discover_models()

    if not s1_options:
        st.warning("Stage 1 모델이 없습니다. 노트북 07~08을 실행하세요.")
        return

    # ── 설정 패널 (session_state에서 기본값 읽기) ──
    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("CF", "ib-gray")} 검수 설정</div>', unsafe_allow_html=True)

    # 파이프라인 설정에서 지정한 기본값 매핑
    cfg_s1 = st.session_state.get("cfg_stage1_model", "")
    cfg_s2 = st.session_state.get("cfg_stage2_model", "")
    cfg_ad = st.session_state.get("cfg_anomaly", has_ae)

    s1_keys = list(s1_options.keys())
    s1_default_idx = 0
    matched_s1 = _match_setting_to_option(cfg_s1, s1_options)
    if matched_s1 and matched_s1 in s1_keys:
        s1_default_idx = s1_keys.index(matched_s1)

    s2_keys = list(s2_options.keys()) if s2_options else []
    s2_default_idx = 0
    if s2_keys:
        matched_s2 = _match_setting_to_option(cfg_s2, s2_options)
        if matched_s2 and matched_s2 in s2_keys:
            s2_default_idx = s2_keys.index(matched_s2)

    c1, c2, c3 = st.columns(3)
    with c1:
        s1_sel = st.selectbox("Stage 1 모델", s1_keys, index=s1_default_idx, key="sim_s1")
    with c2:
        if s2_keys:
            s2_sel = st.selectbox("Stage 2 모델", s2_keys, index=s2_default_idx, key="sim_s2")
        else:
            st.info("Stage 2 모델 없음")
            s2_sel = None
    with c3:
        use_anomaly = st.checkbox("이상탐지 활성화", value=cfg_ad, key="sim_ad") if has_ae else False
        if has_ae:
            ad_threshold = st.session_state.get("cfg_anomaly_threshold", 0.02)
            st.caption(f"임계값: {ad_threshold:.3f}")

    st.markdown('</div>', unsafe_allow_html=True)

    # ── 추론 실행 ──
    if st.button("검수 실행", type="primary", use_container_width=True, key="sim_run"):
        config = {"stage1_type": None, "stage2_type": None, "use_anomaly": use_anomaly}

        # Stage 1 로드
        s1_type, s1_path, s1_scaler_path = s1_options[s1_sel]
        config["stage1_type"] = s1_type
        if s1_type == "ml":
            config["stage1_ml"] = _load_binary_ml(s1_path, s1_scaler_path)
        else:
            config["stage1_dl"] = _load_binary_dl(s1_path)

        # Stage 2 로드
        if s2_sel:
            s2_type, s2_path, s2_scaler_path = s2_options[s2_sel]
            config["stage2_type"] = s2_type
            if s2_type == "ml":
                config["stage2_ml"] = _load_defect4_ml(s2_path, s2_scaler_path)
            else:
                config["stage2_dl"] = _load_defect4_dl(s2_path)

        # 이상탐지 로드
        if use_anomaly and has_ae:
            config["ae_model"] = _load_ae_model(ae_path)

        with st.spinner("검수 중..."):
            results = run_full_inspection(input_image, config)

        st.session_state["sim_results"] = results
        st.session_state["sim_config_label"] = {"s1": s1_sel, "s2": s2_sel}

    # ── 결과 표시 ──
    if "sim_results" in st.session_state:
        results = st.session_state["sim_results"]
        cfg_label = st.session_state.get("sim_config_label", {})
        _render_results(results, input_image, cfg_label)


def _render_results(results, input_image, cfg_label):
    """검수 결과 렌더링."""
    B = _badge
    s1 = results.get("stage1")
    s2 = results.get("stage2")
    ad = results.get("anomaly")
    timings = results.get("timings", {})

    # ── 판정 카드 ──
    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("JD", "ib-green")} 검수 판정 결과</div>', unsafe_allow_html=True)

    if s1 is None:
        st.warning("Stage 1 결과가 없습니다.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    is_defect = s1["pred"] == 1

    # 큰 판정 카드
    if is_defect:
        verdict_color = "#dc2626"
        verdict_icon = "!"
        verdict_text = "결함 감지"
        verdict_detail = f"Stage 2: {s2['name']}" if s2 else "Stage 2 미실행"
    else:
        verdict_color = "#059669"
        verdict_icon = "O"
        verdict_text = "정상"
        verdict_detail = "결함이 감지되지 않았습니다"

    r1, r2 = st.columns([1, 2])
    with r1:
        st.image(input_image, caption="입력 이미지", use_container_width=True, clamp=True)
    with r2:
        st.markdown(f"""
        <div style="text-align:center; padding:24px; background:{'#fef2f2' if is_defect else '#f0fdf4'};
             border-radius:16px; border:3px solid {verdict_color}; margin-bottom:16px;">
            <p style="font-size:3rem; margin:0;">{verdict_icon}</p>
            <p style="color:{verdict_color}; font-size:2.2rem; font-weight:800; margin:4px 0;">
                {verdict_text}</p>
            <p style="color:#475569; font-size:1rem; margin:4px 0;">{verdict_detail}</p>
            <p style="color:#94a3b8; font-size:0.8rem; margin-top:8px;">
                총 추론시간: {timings.get('total', 0):.0f}ms</p>
        </div>""", unsafe_allow_html=True)

        # Stage별 요약 KPI
        kpi_cols = st.columns(3)
        with kpi_cols[0]:
            s1_conf = f"{float(s1['probs'].max()):.1%}" if s1.get("probs") is not None else "N/A"
            st.markdown(f'<div class="kpi-card"><p class="kpi-label">Stage 1: {s1["label"]}</p>'
                        f'<p class="kpi-value" style="color:{verdict_color};">{s1_conf}</p>'
                        f'<p style="color:#94a3b8;font-size:0.7rem;margin:0;">'
                        f'{cfg_label.get("s1","")} | {timings.get("stage1",0):.0f}ms</p></div>',
                        unsafe_allow_html=True)
        with kpi_cols[1]:
            if s2:
                info = DEFECT_INFO[s2["class_id"]]
                s2_conf = f"{float(s2['probs'].max()):.1%}" if s2.get("probs") is not None else "N/A"
                st.markdown(f'<div class="kpi-card"><p class="kpi-label">Stage 2: {info["abbr"]}</p>'
                            f'<p class="kpi-value" style="color:{info["color"]};">{s2_conf}</p>'
                            f'<p style="color:#94a3b8;font-size:0.7rem;margin:0;">'
                            f'{cfg_label.get("s2","")} | {timings.get("stage2",0):.0f}ms</p></div>',
                            unsafe_allow_html=True)
            else:
                st.markdown('<div class="kpi-card"><p class="kpi-label">Stage 2</p>'
                            '<p class="kpi-value" style="color:#94a3b8;">—</p></div>',
                            unsafe_allow_html=True)
        with kpi_cols[2]:
            if ad:
                ad_label = "이상" if ad["score"] > 0.02 else "정상 범위"
                ad_color = "#dc2626" if ad["score"] > 0.02 else "#059669"
                st.markdown(f'<div class="kpi-card"><p class="kpi-label">이상탐지: {ad_label}</p>'
                            f'<p class="kpi-value" style="color:{ad_color};">{ad["score"]:.4f}</p>'
                            f'<p style="color:#94a3b8;font-size:0.7rem;margin:0;">'
                            f'AE | {timings.get("anomaly",0):.0f}ms</p></div>',
                            unsafe_allow_html=True)
            else:
                st.markdown('<div class="kpi-card"><p class="kpi-label">이상탐지</p>'
                            '<p class="kpi-value" style="color:#94a3b8;">OFF</p></div>',
                            unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Stage 2 확률 분포 ──
    if s2 and s2.get("probs") is not None:
        st.markdown(f'<div class="section-card"><div class="section-title">'
                    f'{B("PR", "ib-purple")} 결함 유형별 확률 분포</div>', unsafe_allow_html=True)

        fig, ax = plt.subplots(figsize=(8, 3))
        labels = [DEFECT_INFO[i+1]["abbr"] for i in range(4)]
        colors = [DEFECT_INFO[i+1]["color"] for i in range(4)]
        probs = s2["probs"][:4] if len(s2["probs"]) >= 4 else s2["probs"]
        ax.barh(labels, probs, color=colors, height=0.5)
        ax.set_xlim(0, 1.0)
        ax.set_xlabel("확률", fontsize=11)
        for i, v in enumerate(probs):
            ax.text(v + 0.02, i, f"{v:.1%}", va="center", fontsize=10, fontweight="bold")
        ax.set_title("4종 결함 확률 분포", fontsize=13, fontweight="bold")
        fig.patch.set_facecolor("#fff")
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── 이상탐지 히트맵 ──
    if ad and ad.get("heatmap") is not None:
        st.markdown(f'<div class="section-card"><div class="section-title">'
                    f'{B("HM", "ib-orange")} 이상탐지 히트맵</div>', unsafe_allow_html=True)

        hm_cols = st.columns(3)
        with hm_cols[0]:
            _ae_sz = ad["heatmap"].shape[0]  # 모델 입력 크기
            disp_img = cv2.resize(input_image, (_ae_sz, _ae_sz))
            st.image(disp_img, caption=f"입력 ({_ae_sz}x{_ae_sz})", use_container_width=True, clamp=True)
        with hm_cols[1]:
            hm = ad["heatmap"]
            hm_norm = (hm - hm.min()) / (hm.max() - hm.min() + 1e-8)
            hm_color = cv2.applyColorMap((hm_norm * 255).astype(np.uint8), cv2.COLORMAP_JET)
            hm_color = cv2.cvtColor(hm_color, cv2.COLOR_BGR2RGB)
            st.image(hm_color, caption=f"이상 히트맵 (점수: {ad['score']:.4f})",
                     use_container_width=True, clamp=True)
        with hm_cols[2]:
            recon = ad["recon"]
            recon_disp = (recon * 255).clip(0, 255).astype(np.uint8)
            st.image(recon_disp, caption="AE 복원 이미지", use_container_width=True, clamp=True)

        st.markdown('</div>', unsafe_allow_html=True)

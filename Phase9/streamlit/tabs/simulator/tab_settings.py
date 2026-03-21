"""A-3: 파이프라인 설정 — 전처리 + 모델 조합 설정. session_state로 실시간/배치에 연동."""

import streamlit as st
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def _badge(letter, color_class="ib-blue"):
    return f'<span class="icon-badge {color_class}">{letter}</span>'


# 모델 성능 메타데이터
MODEL_META = {
    "stage1": {
        "ML: LightGBM":        {"acc": "72.00%", "speed": "~15ms", "size": "<5MB"},
        "ML: RandomForest":    {"acc": "72.00%", "speed": "~12ms", "size": "<5MB"},
        "ML: XGBoost":         {"acc": "69.50%", "speed": "~10ms", "size": "<5MB"},
        "DL: ResNet-18 FT":    {"acc": "90.87%", "speed": "~50ms", "size": "~43MB"},
        "DL: ResNet-18 FE":    {"acc": "89.88%", "speed": "~45ms", "size": "~43MB"},
    },
    "stage2": {
        "ML: LightGBM":        {"acc": "77.72%", "speed": "~10ms", "size": "<5MB"},
        "ML: XGBoost":         {"acc": "77.72%", "speed": "~8ms", "size": "<5MB"},
        "DL: ResNet-18 FT":    {"acc": "86.01%", "speed": "~50ms", "size": "~43MB"},
        "DL: ResNet-18 FE":    {"acc": "87.05%", "speed": "~50ms", "size": "~43MB"},
    },
}


def _get_pipeline_config():
    """현재 session_state에서 파이프라인 설정을 읽어 반환."""
    return {
        "preprocessing": {
            "clahe": st.session_state.get("cfg_clahe", True),
            "blur": st.session_state.get("cfg_blur", True),
            "sharpen": st.session_state.get("cfg_sharpen", True),
            "clahe_clip": st.session_state.get("cfg_clahe_clip", 2.0),
            "blur_d": st.session_state.get("cfg_blur_d", 9),
        },
        "stage1_model": st.session_state.get("cfg_stage1_model", "DL: ResNet-18 FT"),
        "stage2_model": st.session_state.get("cfg_stage2_model", "DL: ResNet-18 FT"),
        "anomaly_enabled": st.session_state.get("cfg_anomaly", False),
        "anomaly_threshold": st.session_state.get("cfg_anomaly_threshold", 0.02),
    }


def render_tab_settings():
    """파이프라인 설정 탭."""
    B = _badge

    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("CF", "ib-gray")} 검수 파이프라인 설정</div>',
                unsafe_allow_html=True)
    st.markdown("""<div class="info-box">
        검수에 사용할 <strong>전처리 파이프라인</strong>과 <strong>모델 조합</strong>을 설정합니다.<br>
        여기서 설정한 값은 <strong>실시간 검수</strong> 탭과 <strong>배치 분석</strong> 탭에 자동으로 적용됩니다.
    </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── 전처리 설정 ──
    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("PP", "ib-green")} 전처리 파이프라인</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.checkbox("CLAHE 정규화", True, key="cfg_clahe",
                     help="밝기 대비를 자동 조절하여 결함이 잘 보이게 합니다.")
        st.slider("CLAHE Clip Limit", 1.0, 5.0, 2.0, 0.5, key="cfg_clahe_clip")
    with c2:
        st.checkbox("Bilateral 블러", True, key="cfg_blur",
                     help="노이즈를 제거하면서 결함 경계는 보존합니다.")
        st.slider("Bilateral d", 3, 15, 9, 2, key="cfg_blur_d")
    with c3:
        st.checkbox("Adaptive Sharpen", True, key="cfg_sharpen",
                     help="결함 부분만 선택적으로 선명하게 만듭니다.")

    st.markdown('</div>', unsafe_allow_html=True)

    # ── 모델 선택 ──
    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("MD", "ib-purple")} 모델 조합 선택</div>', unsafe_allow_html=True)

    mc1, mc2 = st.columns(2)

    # Stage 1 — 사용 가능한 모델만 선택지로
    s1_available = [n for n in MODEL_META["stage1"] if _check_model_exists("stage1", n)]
    s2_available = [n for n in MODEL_META["stage2"] if _check_model_exists("stage2", n)]

    with mc1:
        st.markdown("**Stage 1: 이진 분류 (정상/비정상)**")
        if s1_available:
            # 기본값: DL FT > ML LightGBM > 첫 번째 가용 모델
            s1_default = "DL: ResNet-18 FT" if "DL: ResNet-18 FT" in s1_available else s1_available[0]
            s1_idx = s1_available.index(s1_default) if s1_default in s1_available else 0
            s1_selected = st.selectbox(
                "Stage 1 모델 선택",
                s1_available,
                index=s1_idx,
                format_func=lambda n: f"{n}  ({MODEL_META['stage1'][n]['acc']})",
                key="cfg_stage1_model",
            )
        else:
            st.warning("사용 가능한 Stage 1 모델이 없습니다.")

        # 전체 모델 목록 (참고용)
        with st.expander("전체 모델 성능 참고", expanded=False):
            for name, meta in MODEL_META["stage1"].items():
                avail = _check_model_exists("stage1", name)
                status = "OK" if avail else "없음"
                st.markdown(f"- **{name}** [{status}]: Acc {meta['acc']} / {meta['speed']} / {meta['size']}")

    with mc2:
        st.markdown("**Stage 2: 4종 결함 분류**")
        if s2_available:
            s2_default = "DL: ResNet-18 FT" if "DL: ResNet-18 FT" in s2_available else s2_available[0]
            s2_idx = s2_available.index(s2_default) if s2_default in s2_available else 0
            s2_selected = st.selectbox(
                "Stage 2 모델 선택",
                s2_available,
                index=s2_idx,
                format_func=lambda n: f"{n}  ({MODEL_META['stage2'][n]['acc']})",
                key="cfg_stage2_model",
            )
        else:
            st.warning("사용 가능한 Stage 2 모델이 없습니다.")

        with st.expander("전체 모델 성능 참고", expanded=False):
            for name, meta in MODEL_META["stage2"].items():
                avail = _check_model_exists("stage2", name)
                status = "OK" if avail else "없음"
                st.markdown(f"- **{name}** [{status}]: Acc {meta['acc']} / {meta['speed']} / {meta['size']}")

    st.markdown('</div>', unsafe_allow_html=True)

    # ── 이상탐지 설정 ──
    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("AD", "ib-orange")} 이상탐지 설정</div>', unsafe_allow_html=True)

    _anomaly_dir = os.path.join(PROJECT_ROOT, "outputs", "models_severstal", "anomaly")
    ae_path = None
    for _ae_fname in ["autoencoder_severstal.pt", "autoencoder_real_normal.pt", "autoencoder.pt"]:
        _ae_cand = os.path.join(_anomaly_dir, _ae_fname)
        if os.path.exists(_ae_cand):
            ae_path = _ae_cand
            break
    has_ae = ae_path is not None

    ad_c1, ad_c2 = st.columns(2)
    with ad_c1:
        st.checkbox("이상탐지 활성화", value=has_ae, key="cfg_anomaly",
                    disabled=not has_ae, help="Autoencoder 기반 이상 점수 계산을 활성화합니다.")
    with ad_c2:
        st.slider("이상 판정 임계값", 0.001, 0.1, 0.02, 0.001,
                  key="cfg_anomaly_threshold",
                  help="이 값보다 복원 오차가 높으면 이상으로 판정",
                  disabled=not has_ae)

    if has_ae:
        st.markdown(f"""
        - **모델**: Conv Autoencoder (192x192 입력, 1ch 그레이스케일)
        - **AUROC**: 0.6806
        - **방식**: 복원 오차 기반 이상 점수 계산
        """)
    else:
        st.warning("Autoencoder 모델이 없습니다. 노트북 09를 실행하세요.")

    st.markdown('</div>', unsafe_allow_html=True)

    # ── 현재 설정 요약 ──
    config = _get_pipeline_config()

    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("SM", "ib-teal")} 현재 설정 요약</div>', unsafe_allow_html=True)

    pp_steps = []
    if config["preprocessing"]["clahe"]:
        pp_steps.append(f"CLAHE (clip={config['preprocessing']['clahe_clip']})")
    if config["preprocessing"]["blur"]:
        pp_steps.append(f"Bilateral (d={config['preprocessing']['blur_d']})")
    if config["preprocessing"]["sharpen"]:
        pp_steps.append("Sharpen")

    pp_text = " -> ".join(pp_steps) if pp_steps else "없음"

    sm1, sm2, sm3, sm4 = st.columns(4)
    with sm1:
        st.markdown(f'<div class="kpi-card"><p class="kpi-label">전처리</p>'
                    f'<p style="color:#059669; font-size:0.85rem; font-weight:600; margin:4px 0 0 0;">'
                    f'{len(pp_steps)}단계</p></div>', unsafe_allow_html=True)
    with sm2:
        s1_label = config.get("stage1_model", "미설정")
        st.markdown(f'<div class="kpi-card"><p class="kpi-label">Stage 1</p>'
                    f'<p style="color:#2563eb; font-size:0.85rem; font-weight:600; margin:4px 0 0 0;">'
                    f'{s1_label}</p></div>', unsafe_allow_html=True)
    with sm3:
        s2_label = config.get("stage2_model", "미설정")
        st.markdown(f'<div class="kpi-card"><p class="kpi-label">Stage 2</p>'
                    f'<p style="color:#7c3aed; font-size:0.85rem; font-weight:600; margin:4px 0 0 0;">'
                    f'{s2_label}</p></div>', unsafe_allow_html=True)
    with sm4:
        ad_status = "ON" if config["anomaly_enabled"] else "OFF"
        ad_color = "#ea580c" if config["anomaly_enabled"] else "#94a3b8"
        st.markdown(f'<div class="kpi-card"><p class="kpi-label">이상탐지</p>'
                    f'<p style="color:{ad_color}; font-size:0.85rem; font-weight:600; margin:4px 0 0 0;">'
                    f'{ad_status}</p></div>', unsafe_allow_html=True)

    st.markdown(f"**전처리 흐름**: {pp_text}")
    st.markdown("**추천 조합**: Stage1 DL(ResNet-18 FT, 90.87%) + Stage2 DL(ResNet-18 FT, 86.01%)")

    st.markdown('</div>', unsafe_allow_html=True)


def _check_model_exists(stage, name):
    """모델 파일 존재 여부 확인."""
    model_dir = os.path.join(PROJECT_ROOT, "outputs", "models_severstal")
    if stage == "stage1":
        if "ML:" in name:
            mname = name.replace("ML: ", "")
            return os.path.exists(os.path.join(model_dir, "binary_ml", f"binary_{mname}.joblib"))
        else:
            if "FT" in name:
                return os.path.exists(os.path.join(model_dir, "binary_dl", "binary_resnet18_finetune.pt"))
            else:
                return os.path.exists(os.path.join(model_dir, "binary_dl", "binary_resnet18_feature_extractor.pt"))
    else:
        if "ML:" in name:
            mname = name.replace("ML: ", "")
            return os.path.exists(os.path.join(model_dir, "defect4_ml", f"defect4_{mname}.joblib"))
        else:
            if "FT" in name:
                return os.path.exists(os.path.join(model_dir, "defect4_dl", "defect4_resnet18_finetune.pt"))
            else:
                return os.path.exists(os.path.join(model_dir, "defect4_dl", "defect4_resnet18_feature_extractor.pt"))

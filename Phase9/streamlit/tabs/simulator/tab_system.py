"""A-4: 시스템 정보 — 데이터셋/모델/환경 상태."""

import streamlit as st
import os
import sys
import platform
import glob

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def _badge(letter, color_class="ib-blue"):
    return f'<span class="icon-badge {color_class}">{letter}</span>'


def render_tab_system():
    """시스템 정보 탭."""
    B = _badge

    # ── 데이터셋 정보 ──
    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("DS", "ib-blue")} 데이터셋 정보</div>', unsafe_allow_html=True)

    patch_dir = os.path.join(PROJECT_ROOT, "data", "severstal_patches")
    neu_dir = os.path.join(PROJECT_ROOT, "data", "NEU-DET")

    DEFECT_ABBR = {1: "PS", 2: "LS", 3: "SS", 4: "RD"}

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Severstal Steel Defect Detection**")
        if os.path.isdir(patch_dir):
            normal_count = len(glob.glob(os.path.join(patch_dir, "normal", "*.jpg")))
            defect_counts = {}
            for cid in [1, 2, 3, 4]:
                abbr = DEFECT_ABBR[cid]
                d = os.path.join(patch_dir, "defect", f"class_{cid}_{abbr}")
                defect_counts[cid] = len(glob.glob(os.path.join(d, "*.jpg"))) if os.path.isdir(d) else 0
            total_defect = sum(defect_counts.values())
            st.markdown(f"""
            - 정상: **{normal_count:,}** 패치
            - 결함: **{total_defect:,}** 패치
              - PS (Class1): {defect_counts[1]:,}
              - LS (Class2): {defect_counts[2]:,}
              - SS (Class3): {defect_counts[3]:,}
              - RD (Class4): {defect_counts[4]:,}
            - 총합: **{normal_count + total_defect:,}** 패치 (256x256)
            """)
        else:
            st.warning("`data/severstal_patches/` 없음")

    with c2:
        st.markdown("**NEU-DET (교차 검증용)**")
        if os.path.isdir(neu_dir):
            classes = sorted([d for d in os.listdir(neu_dir)
                            if os.path.isdir(os.path.join(neu_dir, d)) and not d.startswith(".")])
            total = 0
            for cls in classes:
                cnt = len(glob.glob(os.path.join(neu_dir, cls, "*")))
                st.markdown(f"- {cls}: {cnt}장")
                total += cnt
            st.markdown(f"- **총합: {total}장** (200x200)")
        else:
            st.info("`data/NEU-DET/` 없음")

    st.markdown('</div>', unsafe_allow_html=True)

    # ── 모델 상태 ──
    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("MD", "ib-purple")} 학습 모델 상태</div>', unsafe_allow_html=True)

    model_base = os.path.join(PROJECT_ROOT, "outputs", "models_severstal")
    checks = [
        ("Stage 1 ML", "binary_ml", ["binary_LightGBM.joblib", "binary_RandomForest.joblib",
                                       "binary_XGBoost.joblib", "binary_scaler.joblib"]),
        ("Stage 1 DL", "binary_dl", ["binary_resnet18_finetune.pt",
                                       "binary_resnet18_feature_extractor.pt"]),
        ("Stage 2 ML", "defect4_ml", ["defect4_LightGBM.joblib", "defect4_XGBoost.joblib",
                                        "defect4_scaler.joblib"]),
        ("Stage 2 DL", "defect4_dl", ["defect4_resnet18_finetune.pt",
                                        "defect4_resnet18_feature_extractor.pt"]),
        ("이상탐지", "anomaly", ["autoencoder_severstal.pt"]),
    ]

    for label, subdir, files in checks:
        found = sum(1 for f in files
                    if os.path.exists(os.path.join(model_base, subdir, f)))
        total = len(files)
        icon = "OK" if found == total else ("!" if found > 0 else "X")
        color = "#059669" if found == total else ("#ea580c" if found > 0 else "#dc2626")
        st.markdown(f"**{icon}** <span style='color:{color}'>{label}</span>: "
                    f"{found}/{total} 파일", unsafe_allow_html=True)
        if found < total:
            missing = [f for f in files
                      if not os.path.exists(os.path.join(model_base, subdir, f))]
            st.caption(f"  누락: {', '.join(missing)}")

    st.markdown('</div>', unsafe_allow_html=True)

    # ── 시스템 환경 ──
    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("SY", "ib-gray")} 시스템 환경</div>', unsafe_allow_html=True)

    import torch
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        **Python**: {platform.python_version()}<br>
        **OS**: {platform.system()} {platform.machine()}
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        **PyTorch**: {torch.__version__}<br>
        **MPS**: {'사용 가능' if torch.backends.mps.is_available() else '사용 불가'}
        """, unsafe_allow_html=True)
    with c3:
        try:
            import streamlit
            st_ver = streamlit.__version__
        except Exception:
            st_ver = "?"
        st.markdown(f"""
        **Streamlit**: {st_ver}<br>
        **프로젝트**: Phase9_v2
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

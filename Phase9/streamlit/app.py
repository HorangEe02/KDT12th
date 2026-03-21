"""
OpenCV & ML 하이브리드 부품 결함 자동 검수 시스템 대시보드
Severstal Steel Defect Detection 기반 — 2-모드 체제
  Mode A: 부품 결함 자동 검수 시뮬레이터 (4페이지)
  Mode B: 알고리즘 인사이트 (5페이지)

Q1: 사이드바에서 페이지 선택, 이미지 입력은 필요한 페이지 내부로 이동
Q4: 파이프라인 설정 → session_state로 실시간/배치 탭에 연동
"""

import streamlit as st
import cv2
import numpy as np
import os
import sys
import datetime
import matplotlib.pyplot as plt

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from preprocessing.normalization import clahe_equalization
from preprocessing.filters import bilateral_filter
from preprocessing.sharpening import adaptive_sharpen
from preprocessing.morphology import opening

st.set_page_config(
    page_title="OpenCV & ML 하이브리드 부품 결함 자동 검수 시스템",
    page_icon="HF",
    layout="wide",
    initial_sidebar_state="expanded",
)

plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams["font.family"] = "AppleGothic"
plt.rcParams["axes.unicode_minus"] = False

# ─── 테마 시스템 ───
def _get_auto_theme():
    h = datetime.datetime.now().hour
    return "light" if 6 <= h < 18 else "dark"

THEMES = {
    "light": {
        "app_bg": "#f8fafc",
        "header_grad_sim": "linear-gradient(135deg, #065f46 0%, #059669 100%)",
        "header_grad_ins": "linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%)",
        "header_title": "#fff", "header_sub": "#bfdbfe",
        "card_bg": "#fff", "card_border": "#e2e8f0",
        "section_title": "#1e40af", "section_border": "#dbeafe",
        "info_bg": "#eff6ff", "info_border": "#bfdbfe", "info_text": "#1e40af",
        "kpi_bg": "#f1f5f9", "kpi_border": "#e2e8f0",
        "kpi_value": "#059669", "kpi_label": "#64748b",
        "bar_bg": "#1e3a5f", "bar_text": "#e2e8f0", "bar_accent": "#93c5fd",
        "sidebar_bg": "#f1f5f9",
        "text_primary": "#334155", "text_secondary": "#64748b",
        "shadow": "rgba(0,0,0,0.06)",
        "plt_style": "seaborn-v0_8-whitegrid",
        "plt_face": "#ffffff", "plt_text": "#334155",
    },
    "dark": {
        "app_bg": "#0f172a",
        "header_grad_sim": "linear-gradient(135deg, #064e3b 0%, #047857 100%)",
        "header_grad_ins": "linear-gradient(135deg, #1e293b 0%, #1d4ed8 100%)",
        "header_title": "#f1f5f9", "header_sub": "#93c5fd",
        "card_bg": "#1e293b", "card_border": "#334155",
        "section_title": "#93c5fd", "section_border": "#1e3a5f",
        "info_bg": "#1e293b", "info_border": "#1e3a5f", "info_text": "#93c5fd",
        "kpi_bg": "#1e293b", "kpi_border": "#334155",
        "kpi_value": "#34d399", "kpi_label": "#94a3b8",
        "bar_bg": "#0f172a", "bar_text": "#cbd5e1", "bar_accent": "#60a5fa",
        "sidebar_bg": "#1e293b",
        "text_primary": "#e2e8f0", "text_secondary": "#94a3b8",
        "shadow": "rgba(0,0,0,0.3)",
        "plt_style": "dark_background",
        "plt_face": "#1e293b", "plt_text": "#e2e8f0",
    },
}

if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "auto"

if st.session_state.theme_mode == "auto":
    _active_theme = _get_auto_theme()
else:
    _active_theme = st.session_state.theme_mode

T = THEMES[_active_theme]

plt.style.use(T["plt_style"])
plt.rcParams["figure.facecolor"] = T["plt_face"]
plt.rcParams["axes.facecolor"] = T["plt_face"]
plt.rcParams["text.color"] = T["plt_text"]
plt.rcParams["axes.labelcolor"] = T["plt_text"]
plt.rcParams["xtick.color"] = T["plt_text"]
plt.rcParams["ytick.color"] = T["plt_text"]


def _badge(letter, color_class="ib-blue"):
    return f'<span class="icon-badge {color_class}">{letter}</span>'


# ─── CSS 주입 (모드 공통) ───
st.markdown(f"""
<style>
    .stApp {{ background-color: {T["app_bg"]}; }}
    .main-header {{
        border-radius: 12px; padding: 18px 28px; margin-bottom: 18px;
    }}
    .main-header h1 {{ color: {T["header_title"]}; margin: 0; font-size: 1.5rem; font-weight: 700; }}
    .main-header .subtitle {{ color: {T["header_sub"]}; font-size: 0.85rem; margin: 4px 0 0 0; }}
    .section-card {{
        background: {T["card_bg"]}; border: 1px solid {T["card_border"]}; border-radius: 10px;
        padding: 20px; margin-bottom: 14px; box-shadow: 0 1px 3px {T["shadow"]};
    }}
    .section-title {{
        color: {T["section_title"]}; font-size: 1.1rem; font-weight: 600;
        margin-bottom: 12px; border-bottom: 2px solid {T["section_border"]}; padding-bottom: 8px;
    }}
    .info-box {{
        background: {T["info_bg"]}; border: 1px solid {T["info_border"]}; border-radius: 8px;
        padding: 12px 16px; margin: 10px 0; font-size: 0.85rem; color: {T["info_text"]};
        line-height: 1.6;
    }}
    .kpi-card {{
        background: {T["kpi_bg"]}; border: 1px solid {T["kpi_border"]}; border-radius: 8px;
        padding: 14px 18px; text-align: center;
    }}
    .kpi-value {{ color: {T["kpi_value"]}; font-size: 2rem; font-weight: 700; margin: 0; }}
    .kpi-label {{ color: {T["kpi_label"]}; font-size: 0.8rem; margin: 0; }}
    .bottom-bar {{
        background: {T["bar_bg"]}; border-radius: 8px; padding: 10px 20px;
        text-align: center; color: {T["bar_text"]}; font-size: 0.8rem; margin-top: 12px;
    }}
    .bottom-bar strong {{ color: {T["bar_accent"]}; }}
    [data-testid="stSidebar"] {{ background-color: {T["sidebar_bg"]}; }}
    .stMarkdown p, .stMarkdown li {{ color: {T["text_primary"]}; }}
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stMarkdown li,
    [data-testid="stSidebar"] label {{ color: {T["text_primary"]}; }}
    [data-testid="stExpander"] details {{
        background: {T["card_bg"]}; border-color: {T["card_border"]};
    }}
    [data-testid="stExpander"] summary span {{ color: {T["text_primary"]}; }}
    .stSelectbox label, .stRadio label, .stSlider label,
    .stCheckbox label, .stMultiSelect label {{ color: {T["text_primary"]} !important; }}
    .stSelectbox [data-baseweb="select"] {{ background: {T["card_bg"]}; }}
    .stTabs [data-baseweb="tab-list"] {{ background: {T["card_bg"]}; }}
    .stTabs [data-baseweb="tab"] {{ color: {T["text_secondary"]}; }}
    .stTabs [aria-selected="true"] {{ color: {T["section_title"]}; }}
    .icon-badge {{
        display: inline-flex; align-items: center; justify-content: center;
        width: 22px; height: 22px; border-radius: 6px;
        font-size: 0.65rem; font-weight: 700; color: #fff;
        margin-right: 6px; vertical-align: middle;
    }}
    .ib-blue   {{ background: #2563eb; }}
    .ib-green  {{ background: #059669; }}
    .ib-orange {{ background: #ea580c; }}
    .ib-purple {{ background: #7c3aed; }}
    .ib-gray   {{ background: #64748b; }}
    .ib-red    {{ background: #dc2626; }}
    .ib-teal   {{ background: #0d9488; }}
    .sidebar-page-item {{
        padding: 4px 0; font-size: 0.9rem;
    }}
</style>
""", unsafe_allow_html=True)


# ─── 공통 유틸 ───
DEFECT_ABBR = {1: "PS", 2: "LS", 3: "SS", 4: "RD"}
MAX_DROPDOWN_FILES = 100


@st.cache_resource
def load_severstal_file_index():
    """파일명 목록만 캐시 (이미지 데이터 X -> 메모리 절약)."""
    patch_dir = os.path.join(PROJECT_ROOT, "data", "severstal_patches")
    index = {"normal": {"dir": "", "files": [], "total": 0},
             "defect": {cid: {"dir": "", "files": [], "total": 0} for cid in range(1, 5)}}

    normal_dir = os.path.join(patch_dir, "normal")
    if os.path.isdir(normal_dir):
        all_files = sorted([f for f in os.listdir(normal_dir)
                            if not f.startswith(".") and f.lower().endswith((".jpg", ".jpeg", ".png", ".bmp"))])
        index["normal"]["dir"] = normal_dir
        index["normal"]["total"] = len(all_files)
        if len(all_files) > MAX_DROPDOWN_FILES:
            step = len(all_files) / MAX_DROPDOWN_FILES
            index["normal"]["files"] = [all_files[int(i * step)] for i in range(MAX_DROPDOWN_FILES)]
        else:
            index["normal"]["files"] = all_files

    for cid in [1, 2, 3, 4]:
        abbr = DEFECT_ABBR[cid]
        defect_dir = os.path.join(patch_dir, "defect", f"class_{cid}_{abbr}")
        if os.path.isdir(defect_dir):
            all_files = sorted([f for f in os.listdir(defect_dir)
                                if not f.startswith(".") and f.lower().endswith((".jpg", ".jpeg", ".png", ".bmp"))])
            index["defect"][cid]["dir"] = defect_dir
            index["defect"][cid]["total"] = len(all_files)
            if len(all_files) > MAX_DROPDOWN_FILES:
                step = len(all_files) / MAX_DROPDOWN_FILES
                index["defect"][cid]["files"] = [all_files[int(i * step)] for i in range(MAX_DROPDOWN_FILES)]
            else:
                index["defect"][cid]["files"] = all_files

    return index


def load_single_image(directory, filename):
    """단일 이미지를 그레이스케일로 로드."""
    if not directory or not filename:
        return None
    path = os.path.join(directory, filename)
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is not None and img.shape[:2] != (256, 256):
        img = cv2.resize(img, (256, 256))
    return img


@st.cache_resource
def load_neu_data():
    try:
        from utils.data_loader import NEUDataLoader
        loader = NEUDataLoader(os.path.join(PROJECT_ROOT, "data", "NEU-DET"))
        images, labels, class_names = loader.load_all_images()
        return loader, images, labels, class_names
    except Exception:
        return None, None, None, None


def preprocess_pipeline(image, use_clahe=True, use_blur=True, use_sharpen=True,
                        clahe_clip=2.0, blur_d=9, blur_sc=75, blur_ss=75,
                        sharp_amount=1.5, sharp_thresh=10):
    stages = {"원본 이미지": image.copy()}
    current = image.copy()
    if use_clahe:
        current = clahe_equalization(current, clip_limit=clahe_clip)
        stages["CLAHE 정규화"] = current.copy()
    if use_blur:
        current = bilateral_filter(current, d=blur_d, sigma_color=blur_sc, sigma_space=blur_ss)
        stages["Bilateral 블러"] = current.copy()
    if use_sharpen:
        current = adaptive_sharpen(current, blur_ksize=5, sharp_amount=sharp_amount, noise_threshold=sharp_thresh)
        current = opening(current, kernel_shape="rect", kernel_size=3)
        stages["Sharpen + Opening"] = current.copy()
    return stages, current


def render_image_input_ui(file_index, key_prefix="page"):
    """이미지 입력 UI를 페이지 본문에 렌더링.

    Returns
    -------
    numpy.ndarray  입력 이미지 (256x256 그레이스케일)
    """
    B = _badge

    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("IN", "ib-blue")} 이미지 입력</div>', unsafe_allow_html=True)

    col_mode, col_content = st.columns([1, 3])

    with col_mode:
        input_mode = st.radio(
            "입력 방식",
            ["Severstal 샘플", "파일 업로드"],
            key=f"{key_prefix}_input_mode",
            label_visibility="collapsed",
        )

    with col_content:
        if input_mode == "Severstal 샘플":
            c1, c2 = st.columns(2)
            with c1:
                type_options = []
                n_normal = file_index["normal"]["total"]
                type_options.append(f"정상 ({n_normal:,}장)")
                for cid in [1, 2, 3, 4]:
                    n = file_index["defect"][cid]["total"]
                    abbr = DEFECT_ABBR[cid]
                    type_options.append(f"결함 Class{cid} ({abbr}) - {n:,}장")

                sample_type = st.selectbox("이미지 유형", type_options,
                                           key=f"{key_prefix}_img_type")

            if sample_type.startswith("정상"):
                file_list = file_index["normal"]["files"]
                img_dir = file_index["normal"]["dir"]
                total_count = file_index["normal"]["total"]
            else:
                cid = int(sample_type.split("Class")[1][0])
                file_list = file_index["defect"][cid]["files"]
                img_dir = file_index["defect"][cid]["dir"]
                total_count = file_index["defect"][cid]["total"]

            with c2:
                if file_list:
                    if total_count > MAX_DROPDOWN_FILES:
                        st.caption(f"전체 {total_count:,}장 중 {len(file_list)}개 균등 샘플")
                    selected_file = st.selectbox(
                        "파일 선택", file_list,
                        key=f"{key_prefix}_img_file",
                    )
                    input_image = load_single_image(img_dir, selected_file)
                    if input_image is None:
                        st.warning(f"이미지 로드 실패: {selected_file}")
                        input_image = np.zeros((256, 256), dtype=np.uint8)
                else:
                    st.warning("해당 유형의 샘플이 없습니다.")
                    input_image = np.zeros((256, 256), dtype=np.uint8)
        else:
            uploaded = st.file_uploader("검수할 이미지를 업로드하세요",
                                         type=["jpg", "jpeg", "png", "bmp"],
                                         key=f"{key_prefix}_upload")
            if uploaded is not None:
                file_bytes = np.asarray(bytearray(uploaded.read()), dtype=np.uint8)
                input_image = cv2.imdecode(file_bytes, cv2.IMREAD_GRAYSCALE)
                if input_image is not None and input_image.shape[:2] != (256, 256):
                    input_image = cv2.resize(input_image, (256, 256))
                if input_image is None:
                    input_image = np.zeros((256, 256), dtype=np.uint8)
            else:
                default_files = file_index["normal"]["files"]
                default_dir = file_index["normal"]["dir"]
                input_image = None
                if default_files and default_dir:
                    input_image = load_single_image(default_dir, default_files[0])
                if input_image is None:
                    input_image = np.zeros((256, 256), dtype=np.uint8)

    st.markdown('</div>', unsafe_allow_html=True)
    return input_image


def _import_tab(name, subdir=None):
    """탭 모듈 동적 임포트."""
    import importlib.util as _ilu
    _tabs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tabs")
    if subdir:
        _tabs_dir = os.path.join(_tabs_dir, subdir)
    spec = _ilu.spec_from_file_location(name, os.path.join(_tabs_dir, f"{name}.py"))
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ─── 페이지 정의 ───
SIMULATOR_PAGES = {
    "실시간 검수":      {"icon": "RT", "color": "ib-green",  "needs_image": True},
    "배치 분석":       {"icon": "BA", "color": "ib-blue",   "needs_image": False},
    "파이프라인 설정":  {"icon": "CF", "color": "ib-gray",   "needs_image": False},
    "시스템 정보":      {"icon": "SY", "color": "ib-teal",   "needs_image": False},
}

INSIGHT_PAGES = {
    "전처리 분석":      {"icon": "PP", "color": "ib-green",  "needs_image": True},
    "ML vs DL 비교":   {"icon": "ML", "color": "ib-purple", "needs_image": False},
    "이상탐지 분석":    {"icon": "AD", "color": "ib-orange", "needs_image": True},
    "도메인 일반화 분석": {"icon": "DG", "color": "ib-red",   "needs_image": False},
    "통합 비교":       {"icon": "CP", "color": "ib-blue",   "needs_image": False},
}


# ═══════════════════════════════════════════════════
# 메인
# ═══════════════════════════════════════════════════
def main():
    B = _badge
    file_index = load_severstal_file_index()

    # ═══ 사이드바 ═══
    with st.sidebar:
        st.markdown(f"## {B('CP','ib-gray')} Control Panel", unsafe_allow_html=True)

        # ─── 모드 선택 ───
        mode = st.radio(
            "모드 선택",
            ["부품 결함 자동 검수 시뮬레이터", "알고리즘 인사이트"],
            index=0,
            key="app_mode",
        )
        is_simulator = mode.startswith("부품")

        st.markdown("---")

        # ─── 페이지 선택 ───
        if is_simulator:
            page_names = list(SIMULATOR_PAGES.keys())
            page_meta = SIMULATOR_PAGES
        else:
            page_names = list(INSIGHT_PAGES.keys())
            page_meta = INSIGHT_PAGES

        # 페이지 목록을 아이콘 뱃지와 함께 표시
        page_display = [f"{p}" for p in page_names]
        selected_page = st.selectbox(
            "페이지 선택",
            page_display,
            key="selected_page",
        )
        current_page_info = page_meta[selected_page]

        st.markdown("---")

        # ─── 테마 토글 ───
        _now = datetime.datetime.now()
        _auto_label = "주간" if 6 <= _now.hour < 18 else "야간"
        theme_options = [f"자동 ({_auto_label})", "주간 모드", "야간 모드"]
        _current_idx = {"auto": 0, "light": 1, "dark": 2}.get(st.session_state.theme_mode, 0)
        theme_choice = st.radio(
            "테마", theme_options, index=_current_idx,
            horizontal=True, label_visibility="collapsed",
        )
        _new_mode = {0: "auto", 1: "light", 2: "dark"}[theme_options.index(theme_choice)]
        if _new_mode != st.session_state.theme_mode:
            st.session_state.theme_mode = _new_mode
            st.rerun()

        # ─── 데이터셋 통계 ───
        st.markdown("---")
        _total_patches = file_index["normal"]["total"] + sum(
            file_index["defect"][c]["total"] for c in range(1, 5))
        st.markdown(f"""
        **Severstal**: {_total_patches:,} 패치 (256x256)<br>
        &nbsp; 정상 {file_index["normal"]["total"]:,} / 결함 {_total_patches - file_index["normal"]["total"]:,}<br>
        **NEU-DET**: 1,440장 (도메인 검증)
        """, unsafe_allow_html=True)

    # ═══ 헤더 ═══
    if is_simulator:
        st.markdown(f"""
        <div class="main-header" style="background:{T['header_grad_sim']};">
            <h1>{B("SM","ib-green")} 부품 결함 자동 검수 시뮬레이터</h1>
            <p class="subtitle">
                {B(current_page_info["icon"], current_page_info["color"])}
                {selected_page}
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="main-header" style="background:{T['header_grad_ins']};">
            <h1>{B("AI","ib-blue")} 알고리즘 인사이트</h1>
            <p class="subtitle">
                {B(current_page_info["icon"], current_page_info["color"])}
                {selected_page}
            </p>
        </div>
        """, unsafe_allow_html=True)

    # ═══ 페이지별 렌더링 ═══
    if is_simulator:
        _render_simulator_page(selected_page, file_index)
    else:
        _render_insight_page(selected_page, file_index)

    # ── 하단 바 ──
    mode_label = "시뮬레이터" if is_simulator else "인사이트"
    st.markdown(f"""
    <div class="bottom-bar">
        <strong>Severstal 2-Stage 하이브리드</strong>: Stage 1 (정상/비정상) -> Stage 2 (4종 결함)
        &nbsp;|&nbsp; {mode_label} > {selected_page}
        &nbsp;|&nbsp; {"주간" if _active_theme == "light" else "야간"}
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════
# Mode A: 부품 결함 자동 검수 시뮬레이터
# ═══════════════════════════════════════════════════
def _render_simulator_page(page_name, file_index):
    if page_name == "실시간 검수":
        input_image = render_image_input_ui(file_index, key_prefix="sim_rt")
        mod = _import_tab("tab_realtime", "simulator")
        mod.render_tab_realtime(input_image)

    elif page_name == "배치 분석":
        mod = _import_tab("tab_batch", "simulator")
        mod.render_tab_batch()

    elif page_name == "파이프라인 설정":
        mod = _import_tab("tab_settings", "simulator")
        mod.render_tab_settings()

    elif page_name == "시스템 정보":
        mod = _import_tab("tab_system", "simulator")
        mod.render_tab_system()


# ═══════════════════════════════════════════════════
# Mode B: 알고리즘 인사이트
# ═══════════════════════════════════════════════════
def _render_insight_page(page_name, file_index):
    if page_name == "전처리 분석":
        input_image = render_image_input_ui(file_index, key_prefix="ins_pp")
        # 전처리 설정 UI (전처리 분석 페이지 전용)
        B = _badge
        st.markdown(f'<div class="section-card"><div class="section-title">'
                    f'{B("PP","ib-green")} 전처리 설정</div>', unsafe_allow_html=True)
        pp_c1, pp_c2, pp_c3 = st.columns(3)
        with pp_c1:
            use_clahe = st.checkbox("CLAHE 정규화", True, key="ins_pp_clahe")
            clahe_clip = st.slider("CLAHE Clip Limit", 1.0, 5.0, 2.0, 0.5, key="ins_pp_clip")
        with pp_c2:
            use_blur = st.checkbox("Bilateral 블러", True, key="ins_pp_blur")
            blur_d = st.slider("Bilateral d", 3, 15, 9, 2, key="ins_pp_blur_d")
        with pp_c3:
            use_sharpen = st.checkbox("Adaptive Sharpen", True, key="ins_pp_sharpen")
        st.markdown('</div>', unsafe_allow_html=True)

        stages, preprocessed = preprocess_pipeline(
            input_image, use_clahe=use_clahe, use_blur=use_blur,
            use_sharpen=use_sharpen, clahe_clip=clahe_clip, blur_d=blur_d)

        mod = _import_tab("tab_preprocessing", "insight")
        mod.render_tab_preprocessing(input_image, stages, preprocessed)

    elif page_name == "ML vs DL 비교":
        mod = _import_tab("tab_ml_dl_compare", "insight")
        mod.render_tab_ml_dl_compare()

    elif page_name == "이상탐지 분석":
        input_image = render_image_input_ui(file_index, key_prefix="ins_ad")
        mod = _import_tab("tab_anomaly_detection")
        mod.render_tab_anomaly_detection(input_image, None)

    elif page_name == "도메인 일반화 분석":
        mod = _import_tab("tab_cross_validation")
        mod.render_tab_cross_validation()

    elif page_name == "통합 비교":
        mod = _import_tab("tab_comparison")
        mod.render_tab_comparison()


if __name__ == "__main__":
    main()

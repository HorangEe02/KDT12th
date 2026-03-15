"""발주 전략 — v3.5 확장: Sub-clustering · DBSCAN/GMM · Safety Stock · 민감도 · t-SNE/UMAP"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.stats import norm
import sys, os, json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_loader import load_raw_data, load_model, load_feature_info, MODELS_DIR
from utils.preprocessor import prepare_doi_features, prepare_cluster_features
from utils.styles import (
    GLOBAL_CSS, kpi_card, section_header, COLORS,
    render_common_sidebar, footer_html,
    section_anchor, render_mini_toc, render_custom_tabs,
)
from utils.descriptions import render_algorithm_info, render_feature_importance, render_shap_analysis, render_glossary, COLUMN_DESC

st.set_page_config(page_title="발주 전략 | WMS v3.5", layout="wide")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# ── 사이드바 (공통) ───────────────────────────────────────
render_common_sidebar(st, current_page="/Reorder_Strategy")

st.markdown('<div class="page-title">발주 전략</div>', unsafe_allow_html=True)

# ── 모드 토글 (2버튼) ──────────────────────────────────────────
if "reorder_mode" not in st.session_state:
    st.session_state.reorder_mode = "알고리즘 인사이트"
# 이전 가이드 모드 사용자 호환: WMS 시뮬레이터로 전환
if st.session_state.reorder_mode == "가이드 모드":
    st.session_state.reorder_mode = "WMS 시뮬레이터"

col_mode_l, col_mode_r, _ = st.columns([1.5, 1.5, 5])
_cur = st.session_state.reorder_mode
with col_mode_l:
    if st.button("WMS 시뮬레이터", key="reorder_basic_btn", use_container_width=True,
                 type="primary" if _cur == "WMS 시뮬레이터" else "secondary"):
        st.session_state.reorder_mode = "WMS 시뮬레이터"
        st.rerun()
with col_mode_r:
    if st.button("알고리즘 인사이트", key="reorder_adv_btn", use_container_width=True,
                 type="primary" if _cur == "알고리즘 인사이트" else "secondary"):
        st.session_state.reorder_mode = "알고리즘 인사이트"
        st.rerun()

is_advanced = st.session_state.reorder_mode == "알고리즘 인사이트"
mode_labels = {
    "WMS 시뮬레이터": "WMS 시뮬레이터 — 긴급 발주 현황 | 제품별 시뮬레이션 | 발주 해석 가이드",
    "알고리즘 인사이트": "알고리즘 인사이트 — 제품 그룹 분석 | Sub-clustering | 알고리즘 비교 | Safety Stock EOQ | 민감도 분석 | 비선형 시각화",
}
st.markdown(f'<div class="page-subtitle">{mode_labels[st.session_state.reorder_mode]}</div>', unsafe_allow_html=True)

# ── 미니 TOC ───────────────────────────────────────────────
if not is_advanced:
    st.markdown(render_mini_toc([
        ("sec-kpi",           "KPI 요약",           "◈"),
        ("sec-wms-simulator", "발주 시뮬레이터",     "▸"),
        ("sec-top5",          "긴급 발주 TOP 5",     "△"),
        ("sec-guide",         "해석 가이드",         "◎"),
        ("sec-quick-sim",     "빠른 시뮬레이터",     "▪"),
        ("sec-urgency-tab",   "발주 긴급도",         "◔"),
    ]), unsafe_allow_html=True)
else:
    pass  # advanced mini_toc rendered after render_custom_tabs below

df = load_raw_data()

# ── 모델 로딩 ──────────────────────────────────────────────
feat_info_v5 = load_feature_info("feature_info_v5.json")
ORDERING_COST = 50
HOLDING_RATE = 0.20

try:
    kmeans = load_model("phase_b_kmeans_baseline_v5.pkl")
    kmeans_scaler = load_model("phase_b_scaler_baseline_v5.pkl")
    cluster_features = feat_info_v5["baseline_cluster_features"]
except FileNotFoundError:
    kmeans = None

# ── Sub-clustering 모델 ────────────────────────────────────
try:
    km_sub = load_model("imp1_kmeans_sub_c1.pkl")
    scaler_sub = load_model("imp1_scaler_sub_c1.pkl")
    with open(os.path.join(MODELS_DIR, "imp1_sub_clustering_info.json")) as f:
        sub_info = json.load(f)
except (FileNotFoundError, Exception):
    km_sub = None
    sub_info = None

# ── DBSCAN / GMM 모델 ──────────────────────────────────────
try:
    dbscan_model = load_model("imp2_dbscan_best.pkl")
except FileNotFoundError:
    dbscan_model = None

try:
    gmm_model = load_model("imp2_gmm_best.pkl")
except FileNotFoundError:
    gmm_model = None

# ── 파생변수 추가 (04d 동일) ────────────────────────────────
df["Dynamic_ROP"] = df["Avg_Daily_Sales"] * df["Lead_Time_Days"] + df["Safety_Stock"]
ads_safe = df["Avg_Daily_Sales"].replace(0, np.nan)
df["Stock_Coverage_Days"] = (
    (df["Quantity_On_Hand"] - df["Safety_Stock"]) / ads_safe
).fillna(0).clip(-100, 365)
df["Annual_Demand"] = df["Avg_Daily_Sales"] * 365
df["Holding_Cost"] = df["Unit_Cost_USD"] * HOLDING_RATE
df["Order_Efficiency"] = (
    df["Quantity_On_Hand"] / df["EOQ"].replace(0, np.nan)
).fillna(1).clip(0, 10)
df["Available_Stock_v2"] = df["Quantity_On_Hand"] - df["Reorder_Point"]

# ── Phase B 클러스터링 ──────────────────────────────────────
if kmeans is not None:
    X_cluster = prepare_cluster_features(df, cluster_features)
    X_cluster_scaled = pd.DataFrame(
        kmeans_scaler.transform(X_cluster), columns=X_cluster.columns, index=X_cluster.index,
    )
    df["Cluster"] = kmeans.predict(X_cluster_scaled)

    cluster_names = {}
    for c in sorted(df["Cluster"].unique()):
        seg = df[df["Cluster"] == c]
        avg_qty = seg["Quantity_On_Hand"].mean()
        if avg_qty > df["Quantity_On_Hand"].median():
            cluster_names[c] = f"Cluster {c}: 고재고"
        else:
            cluster_names[c] = f"Cluster {c}: 저재고"
    df["Cluster_Label"] = df["Cluster"].map(cluster_names)

    # Sub-clustering (Cluster 1)
    if km_sub is not None and sub_info is not None:
        sub_features = sub_info["features"]
        mask_c1 = df["Cluster"] == 1
        if mask_c1.sum() > 0:
            X_c1 = df.loc[mask_c1, sub_features].values
            X_c1_scaled = scaler_sub.transform(X_c1)
            df.loc[mask_c1, "SubCluster"] = km_sub.predict(X_c1_scaled)
            df["SubCluster"] = df["SubCluster"].fillna(-1).astype(int)

            # 3-Tier 분류
            df["Tier"] = "Tier1: 일반 관리"
            df.loc[(df["Cluster"] == 1) & (df["SubCluster"] == 0), "Tier"] = "Tier2: 준긴급"
            df.loc[(df["Cluster"] == 1) & (df["SubCluster"] == 1), "Tier"] = "Tier3: 긴급"

    # DBSCAN / GMM 적용 (enhanced features 기반)
    enhanced_features = feat_info_v5.get("enhanced_cluster_features", cluster_features)
    try:
        enhanced_scaler = load_model("phase_b_scaler_enhanced_v5.pkl")
        X_enh = df[enhanced_features].copy()
        X_enh_scaled = pd.DataFrame(
            enhanced_scaler.transform(X_enh), columns=X_enh.columns, index=X_enh.index,
        )
    except (FileNotFoundError, KeyError):
        X_enh_scaled = X_cluster_scaled  # fallback

    if dbscan_model is not None:
        df["Cluster_DBSCAN"] = dbscan_model.fit_predict(X_enh_scaled)
    if gmm_model is not None:
        df["Cluster_GMM"] = gmm_model.predict(X_enh_scaled)
        df["GMM_Prob"] = gmm_model.predict_proba(X_enh_scaled).max(axis=1)

# fallback: X_enh_scaled가 미정의된 경우
if "X_enh_scaled" not in dir():
    X_enh_scaled = None

# ── KPI ────────────────────────────────────────────────────
st.markdown(section_anchor("sec-kpi"), unsafe_allow_html=True)
avg_doi = df["Days_of_Inventory"].mean()
avg_urgency = df["Reorder_Urgency"].mean()
urgent_count = (df["Reorder_Urgency"] < 0).sum()
n_tiers = df["Tier"].nunique() if "Tier" in df.columns else 0

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(kpi_card("평균 재고 소진일", f"{avg_doi:.1f}일", "avg_doi", COLORS["accent_blue"],
                         tooltip="현재 재고로 평균 며칠간 판매 가능"), unsafe_allow_html=True)
with k2:
    st.markdown(kpi_card("평균 발주 여유도", f"{avg_urgency:.2f}", "urgency", COLORS["accent_orange"],
                         tooltip="음수=재고 부족, 양수=여유"), unsafe_allow_html=True)
with k3:
    st.markdown(kpi_card("긴급 발주 제품", f"{urgent_count}", "urgent_sku", COLORS["accent_red"],
                         tooltip="발주 기준선 이하 제품 수"), unsafe_allow_html=True)
with k4:
    st.markdown(kpi_card("관리 등급 수", f"{n_tiers}", "n_clusters", COLORS["accent_purple"],
                         tooltip="3-Tier 분류 체계 (일반/준긴급/긴급)"), unsafe_allow_html=True)

# ── KPI 상세 정보 패널 ──────────────────────────────────────
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

detail_cols = st.columns(4)
with detail_cols[0]:
    with st.popover("재고 소진일 상세"):
        st.markdown("**카테고리별 평균 재고 소진일**")
        doi_by_cat = df.groupby("Category")["Days_of_Inventory"].mean().sort_values()
        for cat, val in doi_by_cat.items():
            bar_color = "#1565C0" if val >= 30 else "#FF9800" if val >= 14 else "#F44336"
            st.markdown(f"**{cat}**: `{val:.1f}일`")
            st.progress(min(val / 60, 1.0))
        st.divider()
        st.markdown("**ABC 등급별 평균 소진일**")
        for abc in ["A", "B", "C"]:
            abc_doi = df[df["ABC_Class"] == abc]["Days_of_Inventory"].mean()
            st.markdown(f"- **{abc}**: {abc_doi:.1f}일")

with detail_cols[1]:
    with st.popover("발주 여유도 상세"):
        st.markdown("**여유도 구간 분포**")
        bins = [float("-inf"), -1, 0, 1, float("inf")]
        labels = ["매우 긴급 (<-1)", "긴급 (-1~0)", "적정 (0~1)", "여유 (>1)"]
        urg_dist = pd.cut(df["Reorder_Urgency"], bins=bins, labels=labels).value_counts().reindex(labels)
        for lbl, cnt in urg_dist.items():
            pct = cnt / len(df) * 100
            st.markdown(f"- **{lbl}**: {cnt}건 ({pct:.1f}%)")
        st.divider()
        st.markdown("**Tier별 평균 여유도**")
        if "Tier" in df.columns:
            for tier in sorted(df["Tier"].unique()):
                t_urg = df[df["Tier"] == tier]["Reorder_Urgency"].mean()
                st.markdown(f"- **{tier}**: {t_urg:.3f}")

with detail_cols[2]:
    with st.popover("긴급 발주 제품 보기"):
        urgent_items = df[df["Reorder_Urgency"] < 0].sort_values("Reorder_Urgency")
        if len(urgent_items) == 0:
            st.success("긴급 발주 필요 제품 없음")
        else:
            st.markdown(f"**총 {len(urgent_items)}건 긴급 발주 필요**")
            for _, row in urgent_items.head(15).iterrows():
                st.markdown(
                    f"- **{row['SKU_ID']}** ({row['SKU_Name']}): "
                    f"여유도 `{row['Reorder_Urgency']:.3f}` | "
                    f"보유 {row['Quantity_On_Hand']} / RP {row['Reorder_Point']:.0f}"
                )
            if len(urgent_items) > 15:
                st.caption(f"... 외 {len(urgent_items) - 15}건 (발주 긴급도 탭에서 전체 확인)")

with detail_cols[3]:
    with st.popover("관리 등급 상세"):
        if "Tier" in df.columns:
            st.markdown("**3-Tier 분류 체계**")
            tier_desc = {
                "Tier1: 일반 관리": "재고 여유 — 정기 모니터링",
                "Tier2: 준긴급": "재고 주의 — 발주 검토 필요",
                "Tier3: 긴급": "재고 위험 — 즉시 발주 필요",
            }
            for tier in sorted(df["Tier"].unique()):
                t_count = (df["Tier"] == tier).sum()
                t_pct = t_count / len(df) * 100
                st.markdown(f"**{tier}** — {t_count}건 ({t_pct:.1f}%)")
                if tier in tier_desc:
                    st.caption(tier_desc[tier])
            st.divider()
            st.markdown("**Tier별 ABC 분포**")
            for tier in sorted(df["Tier"].unique()):
                abc_counts = df[df["Tier"] == tier]["ABC_Class"].value_counts().sort_index()
                abc_str = ", ".join([f"{k}={v}" for k, v in abc_counts.items()])
                st.markdown(f"- {tier}: {abc_str}")
        else:
            st.info("3-Tier 분류 미적용")

# ═══════════════════════════════════════════════════════════
# WMS 시뮬레이터 전용: 긴급 발주 현황 + 제품별 시뮬레이션 + 해석 가이드
# ═══════════════════════════════════════════════════════════
if not is_advanced:
    st.markdown("---")
    st.markdown(section_anchor("sec-wms-simulator"), unsafe_allow_html=True)
    st.markdown(section_header("WMS 발주 시뮬레이터", "제품별 재고 현황 분석 및 발주 시뮬레이션"), unsafe_allow_html=True)

    # ── 제품 선택 ──
    wms_sku = st.selectbox(
        "제품 선택 (SKU)", df["SKU_ID"].tolist(), key="wms_sku_select",
        format_func=lambda x: f"{x} — {df[df['SKU_ID']==x]['SKU_Name'].values[0]}",
    )
    wms_row = df[df["SKU_ID"] == wms_sku].iloc[0]

    # ── 1) 제품 개요 카드 ──
    ov_cols = st.columns(5)
    with ov_cols[0]:
        st.markdown(kpi_card("카테고리", wms_row["Category"], "wms_cat", COLORS["accent_blue"]), unsafe_allow_html=True)
    with ov_cols[1]:
        st.markdown(kpi_card("ABC 등급", wms_row["ABC_Class"], "wms_abc", COLORS["accent_orange"]), unsafe_allow_html=True)
    with ov_cols[2]:
        st.markdown(kpi_card("현재 재고", f"{wms_row['Quantity_On_Hand']:.0f}", "wms_qoh", COLORS["accent_green"]), unsafe_allow_html=True)
    with ov_cols[3]:
        st.markdown(kpi_card("일 평균 판매", f"{wms_row['Avg_Daily_Sales']:.1f}", "wms_ads", COLORS["accent_purple"]), unsafe_allow_html=True)
    with ov_cols[4]:
        st.markdown(kpi_card("리드타임", f"{wms_row['Lead_Time_Days']:.0f}일", "wms_lt", COLORS["accent_red"]), unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ── 2) 현재 발주 상태 평가 ──
    wms_urgency = wms_row["Reorder_Urgency"]
    if wms_urgency < -1:
        wms_status, wms_status_color = "즉시 발주 필요", "#F44336"
        wms_status_desc = f"보유량({wms_row['Quantity_On_Hand']:.0f})이 안전재고({wms_row['Safety_Stock']:.0f}) 이하입니다. 재고 소진 임박으로 즉시 발주가 필요합니다."
    elif wms_urgency < 0:
        wms_status, wms_status_color = "발주 검토 필요", "#FF9800"
        wms_status_desc = f"보유량({wms_row['Quantity_On_Hand']:.0f})이 발주점({wms_row['Dynamic_ROP']:.0f}) 이하입니다. 리드타임 내 재고 소진 가능성이 있어 발주를 준비하세요."
    elif wms_urgency < 1:
        wms_status, wms_status_color = "정기 모니터링", "#4CAF50"
        wms_status_desc = f"현재 재고 수준은 적정합니다. 다음 정기 발주 시 포함을 검토하세요."
    else:
        wms_status, wms_status_color = "재고 충분", "#2196F3"
        wms_status_desc = f"충분한 재고를 보유 중입니다(소진 예상 {max(wms_row['Stock_Coverage_Days'], 0):.0f}일). 과잉 발주에 주의하세요."

    wms_col1, wms_col2 = st.columns(2)
    with wms_col1:
        st.markdown(f"""
        <div style="background:white;border-radius:12px;padding:18px;box-shadow:0 2px 8px rgba(0,0,0,0.07);
                    border-left:5px solid {wms_status_color};">
            <div style="font-size:15px;font-weight:700;color:{wms_status_color};margin-bottom:8px;">
                현재 상태: {wms_status}
            </div>
            <div style="font-size:13px;color:#333;line-height:1.8;">{wms_status_desc}</div>
        </div>
        """, unsafe_allow_html=True)

    # ── 3) 권장 발주 조치 ──
    wms_eoq_val = max(0, wms_row["EOQ"])
    wms_shortage = max(0, wms_row["Dynamic_ROP"] - wms_row["Quantity_On_Hand"])
    wms_coverage = max(wms_row["Stock_Coverage_Days"], 0)

    with wms_col2:
        if wms_urgency < 0:
            rec_action = f"EOQ 기준 {wms_eoq_val:.0f}개를 즉시 주문하세요. 현재 부족량은 {wms_shortage:.0f}개이며, 리드타임 {wms_row['Lead_Time_Days']:.0f}일을 고려하면 빠른 발주가 필요합니다."
        elif wms_urgency < 1:
            rec_action = f"다음 정기 발주 시 EOQ 기준 {wms_eoq_val:.0f}개를 포함하세요. 현재 재고로 약 {wms_coverage:.0f}일간 운영 가능합니다."
        else:
            rec_action = f"현재 발주가 불필요합니다. 재고 소진까지 약 {wms_coverage:.0f}일이 남아 있습니다. 과잉 재고 보관 비용에 주의하세요."

        st.markdown(f"""
        <div style="background:white;border-radius:12px;padding:18px;box-shadow:0 2px 8px rgba(0,0,0,0.07);
                    border-left:5px solid #1565C0;">
            <div style="font-size:15px;font-weight:700;color:#1565C0;margin-bottom:8px;">
                권장 발주 조치
            </div>
            <div style="font-size:13px;color:#333;line-height:1.8;">{rec_action}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ── 4) 핵심 지표 ──
    met_cols = st.columns(4)
    with met_cols[0]:
        st.markdown(kpi_card("EOQ (최적 주문량)", f"{wms_eoq_val:.0f}개", "wms_eoq", COLORS["accent_blue"],
                             tooltip="경제적 주문량 — 총비용 최소화"), unsafe_allow_html=True)
    with met_cols[1]:
        st.markdown(kpi_card("발주점 (ROP)", f"{wms_row['Dynamic_ROP']:.0f}", "wms_rop", COLORS["accent_orange"],
                             tooltip="이 수량 이하이면 발주 시점"), unsafe_allow_html=True)
    with met_cols[2]:
        st.markdown(kpi_card("안전재고", f"{wms_row['Safety_Stock']:.0f}", "wms_ss", COLORS["accent_red"],
                             tooltip="수요 변동 대비 최소 보유량"), unsafe_allow_html=True)
    with met_cols[3]:
        st.markdown(kpi_card("재고 잔여일", f"{wms_coverage:.1f}일", "wms_cov", COLORS["accent_green"],
                             tooltip="현재 재고로 판매 가능한 일수"), unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── 5) 발주 시뮬레이터 ──
    st.markdown(section_header("발주 시뮬레이터", "파라미터를 조정하여 발주 시나리오를 시뮬레이션"), unsafe_allow_html=True)

    def _adj(key, delta, lo, hi):
        st.session_state[key] = max(lo, min(hi, st.session_state[key] + delta))

    sim_p1, sim_p2, sim_p3 = st.columns(3)

    with sim_p1:
        sim_qoh = st.slider(
            "보유 수량 (Quantity_On_Hand)", 0, int(wms_row["Quantity_On_Hand"] * 3) + 100,
            int(wms_row["Quantity_On_Hand"]), key="sim_qoh",
            help="현재 보유 재고 수량을 시뮬레이션",
        )
        _sq1, _sq2 = st.columns(2)
        with _sq1:
            st.button("−10", key="sim_qoh_m", use_container_width=True,
                      on_click=_adj, args=("sim_qoh", -10, 0, int(wms_row["Quantity_On_Hand"] * 3) + 100))
        with _sq2:
            st.button("+10", key="sim_qoh_p", use_container_width=True,
                      on_click=_adj, args=("sim_qoh", 10, 0, int(wms_row["Quantity_On_Hand"] * 3) + 100))

    with sim_p2:
        sim_lt = st.slider(
            "리드타임 (Lead_Time_Days)", 1, 30,
            int(wms_row["Lead_Time_Days"]), key="sim_lt",
            help="배송 소요 일수를 시뮬레이션",
        )
        _sl1, _sl2 = st.columns(2)
        with _sl1:
            st.button("−1", key="sim_lt_m", use_container_width=True,
                      on_click=_adj, args=("sim_lt", -1, 1, 30))
        with _sl2:
            st.button("+1", key="sim_lt_p", use_container_width=True,
                      on_click=_adj, args=("sim_lt", 1, 1, 30))

    with sim_p3:
        sim_rop = st.slider(
            "발주점 (Reorder_Point)", 0, int(wms_row["Dynamic_ROP"] * 3) + 50,
            int(wms_row["Dynamic_ROP"]), key="sim_rop",
            help="발주 기준 수량을 시뮬레이션",
        )
        _sr1, _sr2 = st.columns(2)
        with _sr1:
            st.button("−5", key="sim_rop_m", use_container_width=True,
                      on_click=_adj, args=("sim_rop", -5, 0, int(wms_row["Dynamic_ROP"] * 3) + 50))
        with _sr2:
            st.button("+5", key="sim_rop_p", use_container_width=True,
                      on_click=_adj, args=("sim_rop", 5, 0, int(wms_row["Dynamic_ROP"] * 3) + 50))

    # ── 시뮬레이션 결과 계산 ──
    sim_ads = wms_row["Avg_Daily_Sales"]
    sim_coverage_days = (sim_qoh - wms_row["Safety_Stock"]) / sim_ads if sim_ads > 0 else 999
    sim_coverage_days = max(sim_coverage_days, 0)
    sim_need_order = sim_qoh <= sim_rop
    sim_eoq_cost = wms_eoq_val * wms_row["Unit_Cost_USD"] if wms_eoq_val > 0 else 0
    sim_days_to_stockout = sim_qoh / sim_ads if sim_ads > 0 else 999

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ── 시뮬레이션 결과 표시 ──
    res_cols = st.columns(4)
    with res_cols[0]:
        cov_color = COLORS["accent_red"] if sim_coverage_days < sim_lt else COLORS["accent_green"]
        st.markdown(kpi_card("시뮬 재고 잔여일", f"{sim_coverage_days:.1f}일", "sim_cov", cov_color,
                             tooltip="시뮬레이션 조건에서의 재고 잔여일"), unsafe_allow_html=True)
    with res_cols[1]:
        ord_color = COLORS["accent_red"] if sim_need_order else COLORS["accent_green"]
        ord_text = "필요" if sim_need_order else "불필요"
        st.markdown(kpi_card("발주 필요 여부", ord_text, "sim_ord", ord_color,
                             tooltip="시뮬레이션 조건에서 발주 필요 여부"), unsafe_allow_html=True)
    with res_cols[2]:
        st.markdown(kpi_card("예상 EOQ 비용", f"${sim_eoq_cost:,.0f}", "sim_cost", COLORS["accent_blue"],
                             tooltip="EOQ 수량 × 단가"), unsafe_allow_html=True)
    with res_cols[3]:
        so_color = COLORS["accent_red"] if sim_days_to_stockout < sim_lt else COLORS["accent_orange"] if sim_days_to_stockout < sim_lt * 1.5 else COLORS["accent_green"]
        st.markdown(kpi_card("재고 소진까지", f"{sim_days_to_stockout:.1f}일", "sim_so", so_color,
                             tooltip="보유량 기준 총 소진 일수"), unsafe_allow_html=True)

    # ── 타임라인 시각화 ──
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    st.markdown(section_header("타임라인 비교", "재고 소진일 vs 리드타임"), unsafe_allow_html=True)

    timeline_df = pd.DataFrame({
        "항목": ["재고 소진까지", "리드타임 (배송)"],
        "일수": [min(sim_days_to_stockout, 60), sim_lt],
        "구분": ["재고 소진", "리드타임"],
    })
    fig_timeline = px.bar(
        timeline_df, x="일수", y="항목", orientation="h",
        color="구분",
        color_discrete_map={"재고 소진": "#1565C0" if sim_days_to_stockout >= sim_lt else "#F44336", "리드타임": "#FF9800"},
        text="일수",
    )
    fig_timeline.update_layout(height=200, margin=dict(t=10, b=10, l=10, r=10), showlegend=True,
                                yaxis_title="", xaxis_title="일수")
    fig_timeline.update_traces(texttemplate="%{text:.1f}일", textposition="outside")
    st.plotly_chart(fig_timeline, use_container_width=True)

    if sim_days_to_stockout < sim_lt:
        st.warning(f"재고 소진({sim_days_to_stockout:.1f}일)이 리드타임({sim_lt}일)보다 빨라 품절 위험이 있습니다. 즉시 발주를 권장합니다.")
    elif sim_days_to_stockout < sim_lt * 1.5:
        st.info(f"재고 소진({sim_days_to_stockout:.1f}일)과 리드타임({sim_lt}일)이 근접합니다. 발주 준비를 권장합니다.")
    else:
        st.success(f"재고 소진({sim_days_to_stockout:.1f}일)까지 리드타임({sim_lt}일) 대비 충분한 여유가 있습니다.")

    # ═══════════════════════════════════════════════════════════
    # 긴급 발주 TOP 5 + 발주 전략 해석 가이드 (통합)
    # ═══════════════════════════════════════════════════════════
    st.markdown("---")

    # ── 1) 긴급 발주 TOP 5 ──────────────────────────────────
    st.markdown(section_anchor("sec-top5"), unsafe_allow_html=True)
    st.markdown(section_header("긴급 발주 TOP 5", "즉시 발주가 필요한 최우선 제품"), unsafe_allow_html=True)

    top5 = df.nsmallest(5, "Reorder_Urgency")
    top5_cols = st.columns(5)
    for idx, (_, row) in enumerate(top5.iterrows()):
        urg = row["Reorder_Urgency"]
        if urg < -1:
            badge_color, badge_text = "#F44336", "매우 긴급"
        elif urg < 0:
            badge_color, badge_text = "#FF9800", "긴급"
        else:
            badge_color, badge_text = "#4CAF50", "적정"

        coverage = row["Stock_Coverage_Days"]
        rop = row["Dynamic_ROP"]
        shortage = max(0, rop - row["Quantity_On_Hand"])

        with top5_cols[idx]:
            st.markdown(f"""
            <div style="background:white;border-radius:12px;padding:16px;box-shadow:0 2px 8px rgba(0,0,0,0.07);
                        border-left:4px solid {badge_color};min-height:220px;">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                    <span style="font-weight:700;font-size:14px;color:#1a1a2e;">#{idx+1}</span>
                    <span style="background:{badge_color};color:white;padding:2px 8px;border-radius:10px;
                                 font-size:11px;font-weight:600;">{badge_text}</span>
                </div>
                <div style="font-weight:600;font-size:13px;color:#1a1a2e;margin-bottom:4px;">{row['SKU_ID']}</div>
                <div style="font-size:11px;color:#6c757d;margin-bottom:10px;">{row['SKU_Name']}</div>
                <div style="font-size:12px;line-height:1.8;">
                    <div>여유도: <b style="color:{badge_color};">{urg:.3f}</b></div>
                    <div>보유: <b>{row['Quantity_On_Hand']:.0f}</b> / RP: <b>{rop:.0f}</b></div>
                    <div>부족량: <b style="color:#F44336;">{shortage:.0f}</b></div>
                    <div>잔여일: <b>{max(coverage, 0):.1f}일</b></div>
                    <div>카테고리: {row['Category']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── 2) 발주 전략 해석 가이드 ─────────────────────────────
    st.markdown(section_anchor("sec-guide"), unsafe_allow_html=True)
    st.markdown(section_header("발주 전략 해석 가이드", "상황별 발주 의사결정 기준"), unsafe_allow_html=True)

    guide_col1, guide_col2 = st.columns(2)
    with guide_col1:
        st.markdown("""
        <div style="background:white;border-radius:12px;padding:20px;box-shadow:0 2px 8px rgba(0,0,0,0.07);">
            <div style="font-size:15px;font-weight:700;color:#1a1a2e;margin-bottom:12px;">발주 시점 판단 기준</div>
            <table style="width:100%;font-size:12px;border-collapse:collapse;">
                <tr style="border-bottom:1px solid #f0f0f0;">
                    <td style="padding:10px 4px;">
                        <span style="background:#F44336;color:white;padding:2px 8px;border-radius:8px;font-size:11px;font-weight:600;">즉시 발주</span>
                    </td>
                    <td style="padding:10px 8px;color:#333;">
                        여유도 < -1 이거나 보유량 < 안전재고<br>
                        <span style="color:#6c757d;">→ 재고 소진 임박, 긴급 발주 필요</span>
                    </td>
                </tr>
                <tr style="border-bottom:1px solid #f0f0f0;">
                    <td style="padding:10px 4px;">
                        <span style="background:#FF9800;color:white;padding:2px 8px;border-radius:8px;font-size:11px;font-weight:600;">발주 검토</span>
                    </td>
                    <td style="padding:10px 8px;color:#333;">
                        여유도 -1 ~ 0 이거나 보유량 ≤ 발주점(ROP)<br>
                        <span style="color:#6c757d;">→ 리드타임 내 재고 소진 가능, 발주 준비</span>
                    </td>
                </tr>
                <tr style="border-bottom:1px solid #f0f0f0;">
                    <td style="padding:10px 4px;">
                        <span style="background:#4CAF50;color:white;padding:2px 8px;border-radius:8px;font-size:11px;font-weight:600;">정기 모니터링</span>
                    </td>
                    <td style="padding:10px 8px;color:#333;">
                        여유도 0 ~ 1 이면서 재고 소진일 > 리드타임<br>
                        <span style="color:#6c757d;">→ 다음 정기 발주 시 포함</span>
                    </td>
                </tr>
                <tr>
                    <td style="padding:10px 4px;">
                        <span style="background:#2196F3;color:white;padding:2px 8px;border-radius:8px;font-size:11px;font-weight:600;">발주 불필요</span>
                    </td>
                    <td style="padding:10px 8px;color:#333;">
                        여유도 > 1 이면서 재고 소진일 > 30일<br>
                        <span style="color:#6c757d;">→ 충분한 재고 확보, 과잉 발주 주의</span>
                    </td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

    with guide_col2:
        st.markdown("""
        <div style="background:white;border-radius:12px;padding:20px;box-shadow:0 2px 8px rgba(0,0,0,0.07);">
            <div style="font-size:15px;font-weight:700;color:#1a1a2e;margin-bottom:12px;">핵심 지표 해석법</div>
            <table style="width:100%;font-size:12px;border-collapse:collapse;">
                <tr style="border-bottom:1px solid #f0f0f0;">
                    <td style="padding:10px 4px;font-weight:600;width:120px;color:#1565C0;">발주 여유도</td>
                    <td style="padding:10px 8px;color:#333;">
                        (보유량 - 발주점) ÷ 안전재고<br>
                        <span style="color:#6c757d;">음수 = 발주점 이하, 양수 = 여유 있음</span>
                    </td>
                </tr>
                <tr style="border-bottom:1px solid #f0f0f0;">
                    <td style="padding:10px 4px;font-weight:600;color:#1565C0;">발주점 (ROP)</td>
                    <td style="padding:10px 8px;color:#333;">
                        평균 일 판매량 × 리드타임 + 안전재고<br>
                        <span style="color:#6c757d;">보유량이 ROP 이하이면 발주 시점</span>
                    </td>
                </tr>
                <tr style="border-bottom:1px solid #f0f0f0;">
                    <td style="padding:10px 4px;font-weight:600;color:#1565C0;">EOQ (경제적 주문량)</td>
                    <td style="padding:10px 8px;color:#333;">
                        √(2 × 연간수요 × 주문비용 ÷ 보관비용)<br>
                        <span style="color:#6c757d;">총비용을 최소화하는 1회 최적 주문량</span>
                    </td>
                </tr>
                <tr>
                    <td style="padding:10px 4px;font-weight:600;color:#1565C0;">재고 소진일 (DOI)</td>
                    <td style="padding:10px 8px;color:#333;">
                        보유량 ÷ 평균 일 판매량<br>
                        <span style="color:#6c757d;">현재 재고로 버틸 수 있는 일수</span>
                    </td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── 3) 빠른 발주 시뮬레이터 ──────────────────────────────
    st.markdown(section_anchor("sec-quick-sim"), unsafe_allow_html=True)
    st.markdown(section_header("빠른 발주 시뮬레이터", "제품을 선택하여 최적 발주량과 발주 시점을 확인"), unsafe_allow_html=True)

    guide_sku = st.selectbox("제품 선택", df["SKU_ID"].tolist(), key="sim_sku_select",
                             format_func=lambda x: f"{x} — {df[df['SKU_ID']==x]['SKU_Name'].values[0]}")
    guide_row = df[df["SKU_ID"] == guide_sku].iloc[0]

    sim_c1, sim_c2, sim_c3, sim_c4 = st.columns(4)

    # 발주 필요 여부 판단
    need_order = guide_row["Quantity_On_Hand"] <= guide_row["Dynamic_ROP"]
    days_left = max(guide_row["Stock_Coverage_Days"], 0)
    order_qty = max(0, guide_row["EOQ"])
    shortage_qty = max(0, guide_row["Dynamic_ROP"] - guide_row["Quantity_On_Hand"])

    with sim_c1:
        order_status = "즉시 발주" if guide_row["Reorder_Urgency"] < -1 else "발주 검토" if guide_row["Reorder_Urgency"] < 0 else "정기 모니터링" if guide_row["Reorder_Urgency"] < 1 else "발주 불필요"
        status_color = "#F44336" if guide_row["Reorder_Urgency"] < -1 else "#FF9800" if guide_row["Reorder_Urgency"] < 0 else "#4CAF50" if guide_row["Reorder_Urgency"] < 1 else "#2196F3"
        st.metric("발주 상태", order_status)
    with sim_c2:
        st.metric("권장 주문량 (EOQ)", f"{order_qty:.0f}개")
    with sim_c3:
        st.metric("현재 부족량", f"{shortage_qty:.0f}개", delta=f"-{shortage_qty:.0f}" if shortage_qty > 0 else "0", delta_color="inverse")
    with sim_c4:
        st.metric("재고 소진 예상", f"{days_left:.1f}일", delta=f"리드타임 {guide_row['Lead_Time_Days']:.0f}일")

    # 시뮬레이션 상세 정보
    sim_d1, sim_d2 = st.columns(2)
    with sim_d1:
        st.markdown(f"""
        <div style="background:white;border-radius:12px;padding:16px;box-shadow:0 2px 8px rgba(0,0,0,0.07);">
            <div style="font-size:14px;font-weight:700;color:#1a1a2e;margin-bottom:10px;">현재 재고 현황</div>
            <div style="font-size:12px;line-height:2;">
                <div>보유 수량: <b>{guide_row['Quantity_On_Hand']:.0f}</b>개</div>
                <div>안전 재고: <b>{guide_row['Safety_Stock']:.0f}</b>개</div>
                <div>발주점 (ROP): <b>{guide_row['Dynamic_ROP']:.0f}</b>개</div>
                <div>평균 일 판매량: <b>{guide_row['Avg_Daily_Sales']:.1f}</b>개</div>
                <div>리드타임: <b>{guide_row['Lead_Time_Days']:.0f}</b>일</div>
                <div>ABC 등급: <b>{guide_row['ABC_Class']}</b>
                    {'(상위 80% 매출)' if guide_row['ABC_Class']=='A' else '(중간 15% 매출)' if guide_row['ABC_Class']=='B' else '(하위 5% 매출)'}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with sim_d2:
        # 발주 의사결정 가이드 (제품 맞춤)
        if guide_row["Reorder_Urgency"] < -1:
            action = "즉시 발주를 실행하세요."
            reason = f"보유량({guide_row['Quantity_On_Hand']:.0f})이 안전재고({guide_row['Safety_Stock']:.0f}) 이하입니다. 재고 소진까지 약 {days_left:.0f}일 남았으며, 리드타임({guide_row['Lead_Time_Days']:.0f}일)을 고려하면 품절 위험이 매우 높습니다."
            action_color = "#F44336"
        elif guide_row["Reorder_Urgency"] < 0:
            action = "발주를 준비하세요."
            reason = f"보유량({guide_row['Quantity_On_Hand']:.0f})이 발주점({guide_row['Dynamic_ROP']:.0f}) 이하입니다. 리드타임({guide_row['Lead_Time_Days']:.0f}일) 내에 재고가 소진될 수 있으므로 빠른 발주를 권장합니다."
            action_color = "#FF9800"
        elif guide_row["Reorder_Urgency"] < 1:
            action = "다음 정기 발주에 포함하세요."
            reason = f"현재 재고는 적정 수준이지만 여유가 크지 않습니다. 재고 소진 예상 {days_left:.0f}일이므로 정기 발주 시 함께 주문하는 것을 권장합니다."
            action_color = "#4CAF50"
        else:
            action = "현재 발주가 불필요합니다."
            reason = f"충분한 재고를 보유하고 있습니다(소진 예상 {days_left:.0f}일). 과잉 발주로 인한 보관 비용 증가에 주의하세요."
            action_color = "#2196F3"

        st.markdown(f"""
        <div style="background:white;border-radius:12px;padding:16px;box-shadow:0 2px 8px rgba(0,0,0,0.07);
                    border-left:4px solid {action_color};">
            <div style="font-size:14px;font-weight:700;color:{action_color};margin-bottom:10px;">
                권장 조치: {action}
            </div>
            <div style="font-size:12px;color:#333;line-height:1.8;">
                {reason}
            </div>
            <div style="margin-top:12px;padding-top:10px;border-top:1px solid #f0f0f0;font-size:12px;color:#6c757d;">
                권장 주문량: <b>{order_qty:.0f}개</b> (EOQ 기준) | 예상 비용: <b>${order_qty * guide_row['Unit_Cost_USD']:,.0f}</b>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ── 탭 구성 ───────────────────────────────────────────────
st.markdown("---")
st.markdown(section_anchor("sec-urgency-tab"), unsafe_allow_html=True)

if is_advanced:
    adv_tab_names = ["발주 긴급도", "제품 그룹 · 3-Tier", "Safety Stock EOQ",
        "알고리즘 비교", "S×H 민감도", "t-SNE · UMAP", "Phase A 회귀 개선",
        "AI 모델 분석", "용어 사전"]
    active_tab = render_custom_tabs(st, adv_tab_names, "reorder_adv_tab")

    # ── 탭별 동적 미니 TOC ──────────────────────────────────────
    _adv_toc_map = {
        0: [("sec-kpi", "KPI 요약", "◈"), ("sec-urgency-tab", "발주 긴급도", "△")],
        1: [("sec-kpi", "KPI 요약", "◈"), ("sec-tier", "3-Tier 분류", "◔")],
        2: [("sec-kpi", "KPI 요약", "◈"), ("sec-ss-eoq", "Safety Stock EOQ", "▦")],
        3: [("sec-kpi", "KPI 요약", "◈"), ("sec-algo-compare", "알고리즘 비교", "◉")],
        4: [("sec-kpi", "KPI 요약", "◈"), ("sec-sensitivity", "S×H 민감도", "◇")],
        5: [("sec-kpi", "KPI 요약", "◈"), ("sec-tsne", "t-SNE · UMAP", "◎")],
        6: [("sec-kpi", "KPI 요약", "◈"), ("sec-regression", "회귀 개선", "▪")],
        7: [("sec-kpi", "KPI 요약", "◈"), ("sec-ai-model", "AI 모델 분석", "▸")],
        8: [("sec-kpi", "KPI 요약", "◈"), ("sec-glossary", "용어 사전", "▤")],
    }
    st.markdown(render_mini_toc(_adv_toc_map.get(active_tab, [])), unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# Tab 1: 제품 그룹 + Sub-clustering (고급 모드)
# ═══════════════════════════════════════════════════════════
if is_advanced and active_tab == 1:
    st.markdown(section_anchor("sec-tier"), unsafe_allow_html=True)
    if "Tier" in df.columns:
        st.markdown(section_header("3-Tier 분류 체계", "Cluster 1 내부 재클러스터링 결과"), unsafe_allow_html=True)

        # Tier 분포
        col_t1, col_t2 = st.columns([1, 2])
        with col_t1:
            tier_counts = df["Tier"].value_counts().reset_index()
            tier_counts.columns = ["Tier", "Count"]
            tier_counts["비율"] = (tier_counts["Count"] / len(df) * 100).round(1)

            tier_colors = {"Tier1: 일반 관리": "#1565C0", "Tier2: 준긴급": "#FF9800", "Tier3: 긴급": "#F44336"}
            fig_tier = px.pie(tier_counts, values="Count", names="Tier",
                              color="Tier", color_discrete_map=tier_colors, hole=0.4)
            fig_tier.update_layout(height=350, margin=dict(t=20, b=20))
            st.plotly_chart(fig_tier, use_container_width=True)

        with col_t2:
            fig_scatter = px.scatter(
                df, x="Quantity_On_Hand", y="Days_of_Inventory",
                color="Tier", hover_data=["SKU_ID", "Category", "ABC_Class"],
                opacity=0.6, color_discrete_map=tier_colors,
            )
            fig_scatter.update_layout(height=350, margin=dict(t=20, b=20))
            st.plotly_chart(fig_scatter, use_container_width=True)

        # Tier별 통계
        st.markdown(section_header("Tier별 주요 통계"), unsafe_allow_html=True)
        tier_stats = df.groupby("Tier").agg(
            SKU=("SKU_ID", "count"),
            Avg_QOH=("Quantity_On_Hand", "mean"),
            Avg_DOI=("Days_of_Inventory", "mean"),
            Avg_EOQ=("EOQ", "mean"),
            Avg_SS=("Safety_Stock", "mean"),
            Avg_Lead=("Lead_Time_Days", "mean"),
            Urgency_Pct=("Reorder_Urgency", lambda x: (x < 0).mean() * 100),
        ).round(1).reset_index()
        st.dataframe(tier_stats, use_container_width=True, hide_index=True)

        # Sub-cluster 정보
        if sub_info is not None:
            st.markdown(section_header("Sub-clustering 메타데이터"), unsafe_allow_html=True)
            col_m1, col_m2, col_m3 = st.columns(3)
            hopkins_val = sub_info.get('hopkins_c1', 0)
            sub_k_val = sub_info.get('optimal_k_sub', 0)
            sil_sub_val = sub_info.get('silhouette_sub', 0)
            col_m1.metric("Hopkins Statistic", f"{hopkins_val:.4f}",
                          help="0.7 이상 = 강한 군집 경향")
            col_m2.metric("Sub-cluster K", f"{sub_k_val}")
            col_m3.metric("Silhouette Score", f"{sil_sub_val:.4f}")

            # 해석 도우미 패널
            hop_grade = "강한 군집 경향" if hopkins_val >= 0.7 else "보통 군집 경향" if hopkins_val >= 0.5 else "군집 경향 약함"
            hop_color = "#4CAF50" if hopkins_val >= 0.7 else "#FF9800" if hopkins_val >= 0.5 else "#F44336"
            sil_grade = "매우 우수" if sil_sub_val >= 0.7 else "양호" if sil_sub_val >= 0.5 else "보통" if sil_sub_val >= 0.25 else "재검토 필요"
            sil_color = "#4CAF50" if sil_sub_val >= 0.5 else "#FF9800" if sil_sub_val >= 0.25 else "#F44336"

            st.markdown(f"""
            <div style="background:#f8f9fa;border-radius:10px;padding:16px;margin-top:8px;border:1px solid #e9ecef;">
                <div style="font-size:13px;font-weight:700;color:#1a1a2e;margin-bottom:10px;">지표 해석 가이드</div>
                <table style="width:100%;font-size:12px;border-collapse:collapse;">
                    <tr style="border-bottom:1px solid #dee2e6;">
                        <td style="padding:8px 4px;font-weight:600;width:140px;">Hopkins Statistic</td>
                        <td style="padding:8px;">
                            데이터에 자연스러운 그룹(군집)이 존재하는지 측정합니다.<br>
                            <span style="color:{hop_color};font-weight:600;">현재 {hopkins_val:.4f} → {hop_grade}</span><br>
                            <span style="color:#6c757d;">0.5 미만=랜덤, 0.5~0.7=보통, 0.7 이상=뚜렷한 그룹 존재</span>
                        </td>
                    </tr>
                    <tr style="border-bottom:1px solid #dee2e6;">
                        <td style="padding:8px 4px;font-weight:600;">Sub-cluster K</td>
                        <td style="padding:8px;">
                            고재고 그룹 내부를 더 세분화할 때 최적의 하위 그룹 수입니다.<br>
                            <span style="color:#1565C0;font-weight:600;">현재 K={sub_k_val} → 고재고 제품을 {sub_k_val}개 세부 그룹으로 구분</span><br>
                            <span style="color:#6c757d;">각 하위 그룹은 서로 다른 발주 전략이 필요합니다</span>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding:8px 4px;font-weight:600;">Silhouette Score</td>
                        <td style="padding:8px;">
                            그룹 분류가 얼마나 잘 되었는지 품질을 나타냅니다.<br>
                            <span style="color:{sil_color};font-weight:600;">현재 {sil_sub_val:.4f} → {sil_grade}</span><br>
                            <span style="color:#6c757d;">-1~1 범위, 1에 가까울수록 그룹 간 구분이 뚜렷함</span>
                        </td>
                    </tr>
                </table>
            </div>
            """, unsafe_allow_html=True)

        # ABC · 카테고리 분포
        st.markdown(section_header("Tier별 ABC/카테고리 분포"), unsafe_allow_html=True)
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            abc_tier = df.groupby(["Tier", "ABC_Class"]).size().reset_index(name="Count")
            fig_abc = px.bar(abc_tier, x="Tier", y="Count", color="ABC_Class", barmode="group",
                             color_discrete_map={"A": "#F44336", "B": "#FF9800", "C": "#2196F3"})
            fig_abc.update_layout(height=300, margin=dict(t=20, b=20))
            st.plotly_chart(fig_abc, use_container_width=True)
        with col_a2:
            cat_tier = df.groupby(["Tier", "Category"]).size().reset_index(name="Count")
            fig_cat = px.bar(cat_tier, x="Tier", y="Count", color="Category", barmode="stack")
            fig_cat.update_layout(height=300, margin=dict(t=20, b=20))
            st.plotly_chart(fig_cat, use_container_width=True)

    elif "Cluster" in df.columns:
        # fallback: 기존 K=2 표시
        st.markdown(section_header("제품 그룹 분석"), unsafe_allow_html=True)
        fig_cl = px.scatter(df, x="Quantity_On_Hand", y="Days_of_Inventory",
                            color="Cluster_Label", opacity=0.6)
        fig_cl.update_layout(height=400, margin=dict(t=20, b=20))
        st.plotly_chart(fig_cl, use_container_width=True)

# ═══════════════════════════════════════════════════════════
# Tab 2: 알고리즘 비교 (고급 모드)
# ═══════════════════════════════════════════════════════════
if is_advanced and active_tab == 3:
    st.markdown(section_anchor("sec-algo-compare"), unsafe_allow_html=True)
    st.markdown(section_header("클러스터링 알고리즘 비교", "K-Means vs DBSCAN vs GMM"), unsafe_allow_html=True)

    if "Cluster" in df.columns:
        from sklearn.decomposition import PCA
        from sklearn.metrics import silhouette_score

        pca = PCA(n_components=2)
        X_pca = pca.fit_transform(X_cluster_scaled)
        df["PC1"] = X_pca[:, 0]
        df["PC2"] = X_pca[:, 1]

        # enhanced PCA (DBSCAN/GMM 시각화용)
        if X_enh_scaled is not None:
            pca_enh = PCA(n_components=2)
            X_pca_enh = pca_enh.fit_transform(X_enh_scaled)
            df["PC1_enh"] = X_pca_enh[:, 0]
            df["PC2_enh"] = X_pca_enh[:, 1]

        # 알고리즘 비교 테이블
        algo_data = []

        # K-Means
        sil_km = silhouette_score(X_cluster_scaled, df["Cluster"])
        algo_data.append({"알고리즘": "K-Means (K=2)", "Silhouette": f"{sil_km:.4f}",
                          "클러스터 수": 2, "Noise %": "0.0%", "소프트 할당": "No"})

        # DBSCAN
        if "Cluster_DBSCAN" in df.columns:
            mask_valid = df["Cluster_DBSCAN"] != -1
            n_noise = (~mask_valid).sum()
            n_db_clusters = df.loc[mask_valid, "Cluster_DBSCAN"].nunique()
            if n_db_clusters >= 2:
                sil_db = silhouette_score(X_enh_scaled[mask_valid], df.loc[mask_valid, "Cluster_DBSCAN"])
            else:
                sil_db = -1
            algo_data.append({"알고리즘": "DBSCAN", "Silhouette": f"{sil_db:.4f}",
                              "클러스터 수": n_db_clusters, "Noise %": f"{n_noise/len(df)*100:.1f}%",
                              "소프트 할당": "No"})

        # GMM
        if "Cluster_GMM" in df.columns:
            sil_gmm = silhouette_score(X_enh_scaled, df["Cluster_GMM"])
            n_gmm = df["Cluster_GMM"].nunique()
            algo_data.append({"알고리즘": f"GMM (K={n_gmm})", "Silhouette": f"{sil_gmm:.4f}",
                              "클러스터 수": n_gmm, "Noise %": "0.0%", "소프트 할당": "Yes"})

        st.dataframe(pd.DataFrame(algo_data), use_container_width=True, hide_index=True)

        # 알고리즘 비교 해석 도우미
        with st.expander("알고리즘 비교 지표 해석 가이드", expanded=False):
            st.markdown("""
**Silhouette Score (실루엣 점수)**
- 각 제품이 자신의 그룹에 얼마나 잘 속해 있는지 측정 (-1 ~ 1)
- **0.7 이상**: 매우 우수한 분류 | **0.5~0.7**: 양호 | **0.25~0.5**: 보통 | **0.25 미만**: 재검토 필요
- 높을수록 그룹 간 차이가 뚜렷하고, 같은 그룹 내 제품끼리 유사

**클러스터 수**
- 제품을 몇 개의 관리 그룹으로 나누었는지 표시
- 너무 적으면 세밀한 관리 불가, 너무 많으면 관리 복잡도 증가

**Noise % (이상치 비율)**
- DBSCAN만 해당: 어떤 그룹에도 속하지 않는 특이 제품 비율
- 높으면 데이터에 일반적이지 않은 제품이 많다는 의미

**소프트 할당**
- No: 각 제품이 하나의 그룹에만 확정 배정 (K-Means, DBSCAN)
- Yes: 각 제품이 여러 그룹에 속할 확률을 가짐 (GMM) — 경계에 있는 제품 파악 가능
            """)

        # PCA 시각화 비교
        n_plots = 1 + ("Cluster_DBSCAN" in df.columns) + ("Cluster_GMM" in df.columns)
        cols = st.columns(n_plots)

        with cols[0]:
            fig_km = px.scatter(df, x="PC1", y="PC2", color=df["Cluster"].astype(str),
                                opacity=0.5, title=f"K-Means (Sil={sil_km:.4f})")
            fig_km.update_layout(height=350, margin=dict(t=40, b=20), showlegend=False)
            fig_km.update_traces(marker_size=4)
            st.plotly_chart(fig_km, use_container_width=True)

        idx = 1
        pc_x = "PC1_enh" if "PC1_enh" in df.columns else "PC1"
        pc_y = "PC2_enh" if "PC2_enh" in df.columns else "PC2"

        if "Cluster_DBSCAN" in df.columns:
            with cols[idx]:
                fig_db = px.scatter(df, x=pc_x, y=pc_y,
                                    color=df["Cluster_DBSCAN"].astype(str),
                                    opacity=0.5, title=f"DBSCAN (Sil={sil_db:.4f})")
                fig_db.update_layout(height=350, margin=dict(t=40, b=20), showlegend=False)
                fig_db.update_traces(marker_size=4)
                st.plotly_chart(fig_db, use_container_width=True)
            idx += 1

        if "Cluster_GMM" in df.columns:
            with cols[idx]:
                fig_gm = px.scatter(df, x=pc_x, y=pc_y,
                                    color=df["Cluster_GMM"].astype(str),
                                    opacity=0.5, title=f"GMM (Sil={sil_gmm:.4f})")
                fig_gm.update_layout(height=350, margin=dict(t=40, b=20), showlegend=False)
                fig_gm.update_traces(marker_size=4)
                st.plotly_chart(fig_gm, use_container_width=True)

        # GMM 경계 샘플
        if "GMM_Prob" in df.columns:
            st.markdown(section_header("GMM 경계 샘플", "소속 확률 < 0.7인 모호한 제품"), unsafe_allow_html=True)
            boundary = df[df["GMM_Prob"] < 0.7][
                ["SKU_ID", "SKU_Name", "Category", "ABC_Class", "GMM_Prob", "Cluster_GMM"]
            ].sort_values("GMM_Prob")
            st.caption(f"경계 샘플 수: {len(boundary)}개 ({len(boundary)/len(df)*100:.1f}%)")
            if len(boundary) > 0:
                st.dataframe(boundary, use_container_width=True, hide_index=True, height=250)
            st.info("**경계 샘플이란?** 어떤 그룹에 속하는지 확실하지 않은 제품입니다. "
                    "GMM_Prob(소속 확률)이 낮을수록 두 그룹의 경계에 위치하며, "
                    "이런 제품은 발주 전략을 결정할 때 추가 검토가 필요합니다.")

# ═══════════════════════════════════════════════════════════
# Tab 3: 발주 긴급도 (양쪽 모드)
# ═══════════════════════════════════════════════════════════
if not is_advanced or active_tab == 0:
    st.markdown(section_anchor("sec-urgency-tab"), unsafe_allow_html=True)
    st.markdown(section_header("발주 긴급도 대시보드"), unsafe_allow_html=True)
    st.caption("발주 여유도 = (보유 수량 - 발주 기준선) / 안전 재고  |  음수 = 긴급 발주 필요")

    urgency_bins = [float("-inf"), -1, 0, 1, float("inf")]
    urgency_labels = ["매우 긴급 (<-1)", "긴급 (-1~0)", "적정 (0~1)", "여유 (>1)"]
    df["Urgency_Level"] = pd.cut(df["Reorder_Urgency"], bins=urgency_bins, labels=urgency_labels)

    col_u1, col_u2 = st.columns(2)
    with col_u1:
        urgency_counts = df["Urgency_Level"].value_counts().reindex(urgency_labels)
        fig4 = px.pie(values=urgency_counts.values, names=urgency_counts.index,
                      color_discrete_sequence=["#F44336", "#FF9800", "#4CAF50", "#2196F3"],
                      hole=0.4)
        fig4.update_layout(height=350, margin=dict(t=20, b=20))
        st.plotly_chart(fig4, use_container_width=True)
    with col_u2:
        fig5 = px.histogram(df, x="Reorder_Urgency", nbins=40,
                            color_discrete_sequence=[COLORS["accent_orange"]])
        fig5.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="RP 기준선")
        fig5.update_layout(height=350, margin=dict(t=20, b=20))
        st.plotly_chart(fig5, use_container_width=True)

    st.markdown(section_header("긴급 발주 필요 제품"), unsafe_allow_html=True)
    urgent_df = df[df["Reorder_Urgency"] < 0].sort_values("Reorder_Urgency")
    st.dataframe(
        urgent_df[["SKU_ID", "SKU_Name", "Category", "ABC_Class",
                   "Quantity_On_Hand", "Reorder_Point", "Safety_Stock",
                   "Reorder_Urgency", "Lead_Time_Days"]
        ].style.format({"Reorder_Urgency": "{:.3f}"}).background_gradient(
            subset=["Reorder_Urgency"], cmap="RdBu"
        ),
        use_container_width=True, height=400, hide_index=True,
    )

# ═══════════════════════════════════════════════════════════
# Tab 4: Safety Stock 통합 EOQ (고급 모드)
# ═══════════════════════════════════════════════════════════
if is_advanced and active_tab == 2:
    st.markdown(section_anchor("sec-ss-eoq"), unsafe_allow_html=True)
    st.markdown(section_header("Safety Stock 통합 EOQ", "서비스 수준별 안전재고 시뮬레이션"), unsafe_allow_html=True)
    st.caption("SS = Z × σ_d × √(LT)  |  TC = (D/Q)×S + (Q/2 + SS)×H")

    with st.expander("수식 및 용어 해석 가이드", expanded=False):
        st.markdown("""
**Safety Stock (안전 재고, SS)**
- 예상치 못한 수요 변동이나 납품 지연에 대비해 추가로 보유하는 재고
- SS = Z × σ_d × √(LT) : Z=서비스 수준 계수, σ_d=판매량 변동폭, LT=리드타임

**서비스 수준 (Service Level)**
- 고객 주문 시 품절 없이 즉시 납품할 확률
- 90% → 10번 중 9번 즉시 납품 | 95% → 20번 중 19번 | 99% → 100번 중 99번
- 높을수록 안전재고가 증가하여 보관 비용 상승

**TC (Total Cost, 연간 총비용)**
- 주문 비용 + 보관 비용의 합계
- 주문 비용: 1회 주문 비용(S) × 연간 주문 횟수
- 보관 비용: (평균 재고량 + 안전 재고) × 단위당 보관 비용(H)

**슬라이더 조작 가이드**
- **주문 비용(S)**: 한 번 발주 시 드는 고정 비용 (물류비, 행정비 등)
- **보관 비용률(H)**: 제품 원가 대비 연간 보관에 드는 비용 비율 (창고비, 손실 등)
        """)

    # 파라미터
    def _adj(key, delta, lo, hi):
        st.session_state[key] = max(lo, min(hi, st.session_state[key] + delta))

    col_p1, col_p2 = st.columns(2)
    with col_p1:
        ordering_cost = st.slider("1회 주문 비용 (S, $)", 10, 200, 50, key="ss_S",
                                  help="한 번 주문 시 고정 비용")
        _m1, _p1 = st.columns(2)
        with _m1:
            st.button("−1", key="ss_S_m", use_container_width=True,
                      on_click=_adj, args=("ss_S", -1, 10, 200))
        with _p1:
            st.button("+1", key="ss_S_p", use_container_width=True,
                      on_click=_adj, args=("ss_S", 1, 10, 200))
    with col_p2:
        holding_rate_ss = st.slider("연간 보관 비용률 (H, %)", 5, 50, 20, key="ss_H") / 100
        _m2, _p2 = st.columns(2)
        with _m2:
            st.button("−1", key="ss_H_m", use_container_width=True,
                      on_click=_adj, args=("ss_H", -1, 5, 50))
        with _p2:
            st.button("+1", key="ss_H_p", use_container_width=True,
                      on_click=_adj, args=("ss_H", 1, 5, 50))

    # 서비스 수준별 계산
    service_levels = [0.90, 0.95, 0.99]
    cat_std = df.groupby("Category")["Avg_Daily_Sales"].transform("std")

    ss_results = []
    for sl in service_levels:
        z = norm.ppf(sl)
        sl_pct = int(sl * 100)
        ss = z * cat_std * np.sqrt(df["Lead_Time_Days"])
        hc = df["Unit_Cost_USD"] * holding_rate_ss
        eoq = np.sqrt(2 * df["Annual_Demand"] * ordering_cost / hc.replace(0, np.nan)).fillna(0)
        tc = (df["Annual_Demand"] / eoq.replace(0, np.nan)) * ordering_cost + (eoq / 2 + ss) * hc

        for tier in df["Tier"].unique() if "Tier" in df.columns else ["전체"]:
            mask = df["Tier"] == tier if "Tier" in df.columns else pd.Series(True, index=df.index)
            ss_results.append({
                "서비스 수준": f"{sl_pct}%",
                "Tier": tier,
                "Z값": f"{z:.3f}",
                "평균 SS": f"{ss[mask].mean():.1f}",
                "평균 EOQ": f"{eoq[mask].mean():.0f}",
                "평균 TC": f"${tc[mask].mean():,.0f}",
            })

    st.dataframe(pd.DataFrame(ss_results), use_container_width=True, hide_index=True)

    # 시각화: Tier별 SS & TC
    col_ss1, col_ss2 = st.columns(2)

    with col_ss1:
        chart_data = []
        for sl in service_levels:
            z = norm.ppf(sl)
            ss = z * cat_std * np.sqrt(df["Lead_Time_Days"])
            if "Tier" in df.columns:
                for tier in sorted(df["Tier"].unique()):
                    mask = df["Tier"] == tier
                    chart_data.append({"SL": f"{int(sl*100)}%", "Tier": tier, "Safety Stock": ss[mask].mean()})
            else:
                chart_data.append({"SL": f"{int(sl*100)}%", "Tier": "전체", "Safety Stock": ss.mean()})

        fig_ss = px.bar(pd.DataFrame(chart_data), x="Tier", y="Safety Stock", color="SL",
                        barmode="group", title="서비스 수준별 Safety Stock")
        fig_ss.update_layout(height=350, margin=dict(t=40, b=20))
        st.plotly_chart(fig_ss, use_container_width=True)

    with col_ss2:
        tc_data = []
        for sl in service_levels:
            z = norm.ppf(sl)
            ss = z * cat_std * np.sqrt(df["Lead_Time_Days"])
            hc = df["Unit_Cost_USD"] * holding_rate_ss
            eoq = np.sqrt(2 * df["Annual_Demand"] * ordering_cost / hc.replace(0, np.nan)).fillna(0)
            tc = (df["Annual_Demand"] / eoq.replace(0, np.nan)) * ordering_cost + (eoq / 2 + ss) * hc
            if "Tier" in df.columns:
                for tier in sorted(df["Tier"].unique()):
                    mask = df["Tier"] == tier
                    tc_data.append({"SL": f"{int(sl*100)}%", "Tier": tier, "TC ($)": tc[mask].mean()})
            else:
                tc_data.append({"SL": f"{int(sl*100)}%", "Tier": "전체", "TC ($)": tc.mean()})

        fig_tc = px.bar(pd.DataFrame(tc_data), x="Tier", y="TC ($)", color="SL",
                        barmode="group", title="서비스 수준별 연간 총비용 (TC)")
        fig_tc.update_layout(height=350, margin=dict(t=40, b=20))
        st.plotly_chart(fig_tc, use_container_width=True)

    # 개별 EOQ 상세
    st.divider()
    st.markdown(section_header("개별 제품 EOQ 상세"), unsafe_allow_html=True)
    selected_sku = st.selectbox("제품 선택", df["SKU_ID"].tolist(), key="eoq_sku_v35")
    sku_row = df[df["SKU_ID"] == selected_sku].iloc[0]

    col_d1, col_d2, col_d3, col_d4 = st.columns(4)
    sku_eoq = np.sqrt(2 * sku_row["Annual_Demand"] * ordering_cost /
                      max(sku_row["Unit_Cost_USD"] * holding_rate_ss, 0.01))
    sku_orders = sku_row["Annual_Demand"] / max(sku_eoq, 1)
    sku_tc = sku_orders * ordering_cost + (sku_eoq / 2) * sku_row["Unit_Cost_USD"] * holding_rate_ss

    col_d1.metric("최적 주문량", f"{sku_eoq:.0f}")
    col_d2.metric("연간 주문횟수", f"{sku_orders:.1f}회")
    col_d3.metric("연간 총비용", f"${sku_tc:,.0f}")
    col_d4.metric("현재 보유량", f"{sku_row['Quantity_On_Hand']:.0f}")

    if sku_row["Avg_Daily_Sales"] > 0 and sku_row["Unit_Cost_USD"] > 0:
        D = sku_row["Annual_Demand"]
        H = sku_row["Unit_Cost_USD"] * holding_rate_ss
        q_range = np.linspace(max(1, sku_eoq * 0.2), sku_eoq * 3, 200)
        order_cost_curve = (D / q_range) * ordering_cost
        hold_cost_curve = (q_range / 2) * H
        total_cost_curve = order_cost_curve + hold_cost_curve

        fig8 = go.Figure()
        fig8.add_trace(go.Scatter(x=q_range, y=order_cost_curve, name="주문비용",
                                  line=dict(color=COLORS["accent_blue"])))
        fig8.add_trace(go.Scatter(x=q_range, y=hold_cost_curve, name="보관비용",
                                  line=dict(color=COLORS["accent_red"])))
        fig8.add_trace(go.Scatter(x=q_range, y=total_cost_curve, name="총비용",
                                  line=dict(color="#2c3e50", width=3)))
        fig8.add_vline(x=sku_eoq, line_dash="dash", line_color="green", annotation_text="최적점(EOQ)")
        fig8.update_layout(xaxis_title="주문 수량", yaxis_title="연간 비용 ($)",
                           height=380, margin=dict(t=20, b=20))
        st.plotly_chart(fig8, use_container_width=True)

# ═══════════════════════════════════════════════════════════
# Tab 5: S×H 2차원 민감도 (고급 모드)
# ═══════════════════════════════════════════════════════════
if is_advanced and active_tab == 4:
    st.markdown(section_anchor("sec-sensitivity"), unsafe_allow_html=True)
    st.markdown(section_header("S × H 2차원 민감도 분석", "주문비용과 보관비용률 조합별 총비용"), unsafe_allow_html=True)

    with st.expander("히트맵 읽는 법", expanded=False):
        st.markdown("""
**히트맵이란?** 두 가지 비용 조건(주문비용 S, 보관비용률 H)의 조합에 따라 연간 총비용이 어떻게 변하는지 색상으로 보여줍니다.

**읽는 법**:
- **가로축(S)**: 1회 주문 비용 ($25~$150)
- **세로축(H)**: 연간 보관 비용률 (10%~30%)
- **색상**: 진한 빨강 = 비용 높음, 연한 노랑 = 비용 낮음
- **숫자**: 해당 조합에서의 연간 총비용($)

**활용**: 현재 우리 창고의 실제 주문비용과 보관비용률에 해당하는 셀을 찾으면, 해당 조건에서의 최적 비용을 확인할 수 있습니다.
        """)

    S_vals = [25, 50, 75, 100, 150]
    H_vals = [0.10, 0.15, 0.20, 0.25, 0.30]

    # Tier 또는 Cluster별
    group_col = "Tier" if "Tier" in df.columns else ("Cluster_Label" if "Cluster_Label" in df.columns else None)

    if group_col:
        groups = sorted(df[group_col].unique())
        cols_hm = st.columns(min(len(groups), 3))

        for idx, grp in enumerate(groups):
            mask = df[group_col] == grp
            D_avg = df[mask]["Annual_Demand"].mean()
            UC_avg = df[mask]["Unit_Cost_USD"].mean()

            grid = np.zeros((len(H_vals), len(S_vals)))
            for i, h in enumerate(H_vals):
                for j, s in enumerate(S_vals):
                    hc = UC_avg * h
                    eoq = np.sqrt(2 * D_avg * s / max(hc, 0.01))
                    grid[i, j] = (D_avg / eoq) * s + (eoq / 2) * hc

            fig_hm = go.Figure(data=go.Heatmap(
                z=grid, x=[f"S=${s}" for s in S_vals], y=[f"H={h:.0%}" for h in H_vals],
                colorscale="YlOrRd", texttemplate="%{z:.0f}", textfont={"size": 10},
            ))
            fig_hm.update_layout(title=grp, height=350, margin=dict(t=40, b=20))

            with cols_hm[idx % len(cols_hm)]:
                st.plotly_chart(fig_hm, use_container_width=True)

        # TC 절감 효과
        st.markdown(section_header("TC 절감 효과", "기준: S=$50, H=20%"), unsafe_allow_html=True)
        saving_data = []
        for grp in groups:
            mask = df[group_col] == grp
            D_avg = df[mask]["Annual_Demand"].mean()
            UC_avg = df[mask]["Unit_Cost_USD"].mean()

            # 기준 TC
            hc_base = UC_avg * 0.20
            eoq_base = np.sqrt(2 * D_avg * 50 / max(hc_base, 0.01))
            tc_base = (D_avg / eoq_base) * 50 + (eoq_base / 2) * hc_base

            # 최저 TC
            min_tc = float("inf")
            best_s, best_h = 50, 0.20
            for h in H_vals:
                for s in S_vals:
                    hc = UC_avg * h
                    eoq = np.sqrt(2 * D_avg * s / max(hc, 0.01))
                    tc = (D_avg / eoq) * s + (eoq / 2) * hc
                    if tc < min_tc:
                        min_tc = tc
                        best_s, best_h = s, h

            saving_data.append({
                "그룹": grp, "기준 TC": f"${tc_base:,.0f}",
                "최저 TC": f"${min_tc:,.0f}",
                "최적 S": f"${best_s}", "최적 H": f"{best_h:.0%}",
                "절감": f"${tc_base - min_tc:,.0f} ({(tc_base - min_tc)/tc_base*100:.1f}%)",
            })
        st.dataframe(pd.DataFrame(saving_data), use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════
# Tab 6: t-SNE / UMAP 시각화 (고급 모드)
# ═══════════════════════════════════════════════════════════
if is_advanced and active_tab == 5:
    st.markdown(section_anchor("sec-tsne"), unsafe_allow_html=True)
    st.markdown(section_header("비선형 차원축소 시각화", "t-SNE · UMAP으로 숨겨진 구조 탐색"), unsafe_allow_html=True)

    with st.expander("차원축소 시각화란?", expanded=False):
        st.markdown("""
**왜 필요한가?** 제품 데이터는 재고량, 판매량, 리드타임 등 여러 변수(차원)로 구성됩니다. 사람이 한눈에 볼 수 있도록 2차원 평면에 압축해서 보여주는 기법입니다.

**t-SNE**: 가까운 제품끼리 뭉치도록 배치합니다. 비슷한 특성의 제품끼리 모여 있으면 그룹이 잘 형성된 것입니다.
- **Perplexity** 슬라이더: 작은 값은 좁은 범위의 유사 제품끼리 뭉침, 큰 값은 넓은 범위에서 전체 패턴을 봅니다.

**UMAP**: t-SNE와 유사하지만 전체적인 구조(그룹 간 거리)도 보존합니다.

**읽는 법**: 같은 색 점들이 모여 있으면 → 해당 그룹 분류가 잘 됨. 색이 섞여 있으면 → 그룹 간 구분이 모호한 영역.
        """)

    if "Cluster" in df.columns:
        from sklearn.manifold import TSNE

        color_by = st.radio("색상 기준", ["3-Tier 분류", "K-Means (K=2)", "ABC 등급"],
                            horizontal=True, key="tsne_color")

        if color_by == "3-Tier 분류" and "Tier" in df.columns:
            color_col = "Tier"
        elif color_by == "K-Means (K=2)":
            color_col = "Cluster_Label"
        else:
            color_col = "ABC_Class"

        def _adj_tsne(key, delta, lo, hi):
            st.session_state[key] = max(lo, min(hi, st.session_state[key] + delta))

        perplexity = st.slider("t-SNE Perplexity", 5, 50, 30, key="tsne_perp",
                               help="작을수록 지역 구조, 클수록 전역 구조 강조")
        _tm, _tp = st.columns(2)
        with _tm:
            st.button("−1", key="tsne_perp_m", use_container_width=True,
                      on_click=_adj_tsne, args=("tsne_perp", -1, 5, 50))
        with _tp:
            st.button("+1", key="tsne_perp_p", use_container_width=True,
                      on_click=_adj_tsne, args=("tsne_perp", 1, 5, 50))

        X_vis = X_enh_scaled if X_enh_scaled is not None else X_cluster_scaled
        with st.spinner("t-SNE 계산 중..."):
            tsne = TSNE(n_components=2, perplexity=perplexity, random_state=42, max_iter=1000)
            X_tsne = tsne.fit_transform(X_vis)

        df["tSNE1"] = X_tsne[:, 0]
        df["tSNE2"] = X_tsne[:, 1]

        col_v1, col_v2 = st.columns(2)
        with col_v1:
            fig_tsne = px.scatter(df, x="tSNE1", y="tSNE2", color=color_col,
                                  hover_data=["SKU_ID", "Category"],
                                  opacity=0.6, title="t-SNE 시각화")
            fig_tsne.update_layout(height=450, margin=dict(t=40, b=20))
            fig_tsne.update_traces(marker_size=5)
            st.plotly_chart(fig_tsne, use_container_width=True)

        with col_v2:
            # UMAP 시도
            try:
                import umap
                with st.spinner("UMAP 계산 중..."):
                    reducer = umap.UMAP(n_neighbors=15, min_dist=0.1, random_state=42)
                    X_umap = reducer.fit_transform(X_vis)

                df["UMAP1"] = X_umap[:, 0]
                df["UMAP2"] = X_umap[:, 1]

                fig_umap = px.scatter(df, x="UMAP1", y="UMAP2", color=color_col,
                                      hover_data=["SKU_ID", "Category"],
                                      opacity=0.6, title="UMAP 시각화")
                fig_umap.update_layout(height=450, margin=dict(t=40, b=20))
                fig_umap.update_traces(marker_size=5)
                st.plotly_chart(fig_umap, use_container_width=True)

            except ImportError:
                st.info("UMAP 시각화를 위해 `pip install umap-learn`이 필요합니다.")
                # PCA fallback
                fig_pca = px.scatter(df, x="PC1", y="PC2", color=color_col,
                                     hover_data=["SKU_ID", "Category"],
                                     opacity=0.6, title="PCA 시각화 (UMAP 대체)")
                fig_pca.update_layout(height=450, margin=dict(t=40, b=20))
                fig_pca.update_traces(marker_size=5)
                st.plotly_chart(fig_pca, use_container_width=True)

        st.caption("t-SNE/UMAP은 비선형 차원축소로 PCA보다 복잡한 군집 구조를 시각화합니다. "
                   "Perplexity를 조절하여 지역/전역 구조 강조 정도를 변경할 수 있습니다.")

# ═══════════════════════════════════════════════════════════
# Tab 7: Phase A 회귀 성능 심층 개선 (고급 모드)
# ═══════════════════════════════════════════════════════════
if is_advanced and active_tab == 6:
    st.markdown(section_anchor("sec-regression"), unsafe_allow_html=True)
    st.markdown(section_header("Phase A 회귀 성능 심층 개선", "Optuna TPE 베이지안 하이퍼파라미터 최적화"), unsafe_allow_html=True)

    with st.expander("이 탭의 내용 해석 가이드", expanded=False):
        st.markdown("""
**이 탭은 무엇인가?** 재고 소진일(DOI) 예측 모델의 정확도를 자동으로 개선한 결과를 보여줍니다.

**핵심 지표 해석**:
- **CV R² (교차검증 결정계수)**: 예측이 실제값을 얼마나 잘 설명하는지 (0~1, 1에 가까울수록 정확)
- **CV 표준편차**: 예측의 안정성 (낮을수록 일관된 예측)
- **Test R²**: 학습에 사용하지 않은 새 데이터에서의 예측 정확도

**Baseline vs Optuna**: 기본 설정(Baseline)과 자동 최적화 후(Optuna) 성능을 비교합니다.
개선율이 높을수록 최적화 효과가 큽니다.

**하이퍼파라미터**: ML 모델의 세부 설정값입니다. 사람이 수동으로 조정하는 대신 Optuna가 자동으로 최적 조합을 찾아줍니다.
        """)

    # Optuna 결과 로드
    optuna_path = os.path.join(MODELS_DIR, "phase_a_optuna_results.json")
    try:
        with open(optuna_path) as f:
            optuna_res = json.load(f)

        # KPI 요약
        cv_base = optuna_res["cv_baseline"]
        cv_opt = optuna_res["cv_optuna"]
        cv_improve = (cv_opt["mean"] - cv_base["mean"]) / cv_base["mean"] * 100
        std_improve = (cv_opt["std"] - cv_base["std"]) / cv_base["std"] * 100

        ok1, ok2, ok3, ok4 = st.columns(4)
        with ok1:
            st.markdown(kpi_card("CV R² (Baseline)", f"{cv_base['mean']:.4f}", "cv_base", COLORS["accent_blue"],
                                 tooltip="Optuna 이전 Cross-Validation R² 평균"), unsafe_allow_html=True)
        with ok2:
            st.markdown(kpi_card("CV R² (Optuna)", f"{cv_opt['mean']:.4f}", "cv_opt", COLORS["accent_green"],
                                 tooltip="Optuna 최적화 후 Cross-Validation R² 평균"), unsafe_allow_html=True)
        with ok3:
            st.markdown(kpi_card("CV R² 개선", f"+{cv_improve:.1f}%", "cv_imp", COLORS["accent_orange"],
                                 tooltip="CV R² 상대적 개선율"), unsafe_allow_html=True)
        with ok4:
            st.markdown(kpi_card("안정성 개선", f"{std_improve:.0f}%", "std_imp", COLORS["accent_purple"],
                                 tooltip="CV 표준편차 변화 (음수=더 안정)"), unsafe_allow_html=True)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        # 상세 비교 테이블
        col_o1, col_o2 = st.columns(2)
        with col_o1:
            st.markdown(section_header("Baseline vs Optuna 비교"), unsafe_allow_html=True)
            compare_data = pd.DataFrame([
                {"지표": "CV R² 평균", "Baseline": f"{cv_base['mean']:.4f}", "Optuna": f"{cv_opt['mean']:.4f}", "변화": f"+{cv_opt['mean'] - cv_base['mean']:.4f}"},
                {"지표": "CV R² 표준편차", "Baseline": f"{cv_base['std']:.4f}", "Optuna": f"{cv_opt['std']:.4f}", "변화": f"{cv_opt['std'] - cv_base['std']:.4f}"},
                {"지표": "Test R²", "Baseline": f"{optuna_res['test_r2_baseline']:.4f}", "Optuna": f"{optuna_res['test_r2_optuna']:.4f}", "변화": f"{optuna_res['test_r2_optuna'] - optuna_res['test_r2_baseline']:.4f}"},
                {"지표": "Test RMSE", "Baseline": "—", "Optuna": f"{optuna_res['test_rmse_optuna']:.4f}", "변화": "—"},
                {"지표": "탐색 횟수", "Baseline": "—", "Optuna": f"{optuna_res['n_trials']}회", "변화": "—"},
                {"지표": "샘플러", "Baseline": "Grid/Manual", "Optuna": optuna_res["sampler"], "변화": "—"},
            ])
            st.dataframe(compare_data, use_container_width=True, hide_index=True)

        with col_o2:
            st.markdown(section_header("Optuna 최적 하이퍼파라미터"), unsafe_allow_html=True)
            bp = optuna_res["best_params"]
            param_data = pd.DataFrame([
                {"파라미터": k, "최적값": f"{v:.6f}" if isinstance(v, float) else str(v)}
                for k, v in bp.items()
            ])
            st.dataframe(param_data, use_container_width=True, hide_index=True)

        # 시각화: CV 비교 차트
        st.markdown(section_header("CV 성능 비교 시각화"), unsafe_allow_html=True)

        col_c1, col_c2 = st.columns(2)
        with col_c1:
            fig_cv = go.Figure()
            fig_cv.add_trace(go.Bar(
                x=["Baseline", "Optuna"], y=[cv_base["mean"], cv_opt["mean"]],
                error_y=dict(type="data", array=[cv_base["std"], cv_opt["std"]]),
                marker_color=[COLORS["accent_blue"], COLORS["accent_green"]],
                text=[f"{cv_base['mean']:.4f}", f"{cv_opt['mean']:.4f}"],
                textposition="outside",
            ))
            fig_cv.update_layout(
                title="CV R² 비교 (±1σ)",
                yaxis_title="R²", height=350, margin=dict(t=40, b=20),
                yaxis_range=[min(cv_base["mean"] - cv_base["std"] * 2, 0.8), 1.0],
            )
            st.plotly_chart(fig_cv, use_container_width=True)

        with col_c2:
            fig_std = go.Figure()
            fig_std.add_trace(go.Bar(
                x=["Baseline", "Optuna"], y=[cv_base["std"], cv_opt["std"]],
                marker_color=[COLORS["accent_orange"], COLORS["accent_green"]],
                text=[f"{cv_base['std']:.4f}", f"{cv_opt['std']:.4f}"],
                textposition="outside",
            ))
            fig_std.update_layout(
                title="CV 표준편차 비교 (낮을수록 안정)",
                yaxis_title="Std", height=350, margin=dict(t=40, b=20),
            )
            st.plotly_chart(fig_std, use_container_width=True)

        # 개선 탐색 결과 요약
        st.markdown(section_header("Phase A 개선 탐색 결과 요약"), unsafe_allow_html=True)
        findings = optuna_res.get("findings", {})
        finding_desc = {
            "target_transform": ("타겟 변환 (Log/Box-Cox)", "NOT_NEEDED", "분포가 이미 정규에 가까워 변환 불필요"),
            "hurdle_model": ("허들 모델 (영판매 분리)", "NOT_NEEDED", "영판매 비율이 낮아 별도 모델링 불필요"),
            "interaction_features": ("교호작용 피처", "NO_IMPROVEMENT", "기존 피처로 충분한 성능 확보"),
            "optuna_tpe": ("Optuna TPE 최적화", "CV_STABILITY_IMPROVED", "CV 안정성 36% 개선 (std 0.048→0.031)"),
        }
        for key, (name, expected, desc) in finding_desc.items():
            result = findings.get(key, expected)
            if result in ("NOT_NEEDED", "NO_IMPROVEMENT"):
                icon = "gray"
                status = "불필요/미개선"
            else:
                icon = "green"
                status = "개선 확인"
            st.markdown(
                f"**{name}** — "
                f"<span style='color:{icon};font-weight:700;'>{status}</span>: {desc}",
                unsafe_allow_html=True,
            )

    except FileNotFoundError:
        st.warning("Phase A Optuna 결과 파일을 찾을 수 없습니다 (phase_a_optuna_results.json)")

# ═══════════════════════════════════════════════════════════
# Tab 8: AI 모델 분석 (알고리즘 인사이트)
# ═══════════════════════════════════════════════════════════
if is_advanced and active_tab == 7:
    st.markdown(section_anchor("sec-ai-model"), unsafe_allow_html=True)
    st.markdown(section_header("AI 모델 분석", "클러스터링 알고리즘 소개 및 심층 분석"), unsafe_allow_html=True)

    # ── 알고리즘 소개 ──
    st.markdown("### 클러스터링 알고리즘 소개")
    algo_col1, algo_col2, algo_col3 = st.columns(3)
    with algo_col1:
        render_algorithm_info(st, "kmeans")
    with algo_col2:
        render_algorithm_info(st, "dbscan")
    with algo_col3:
        render_algorithm_info(st, "gmm")

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── 클러스터 중심 분석 ──
    if "Cluster" in df.columns and kmeans is not None:
        st.markdown("### 클러스터 중심(Centroid) 분석")
        st.caption("K-Means 클러스터의 중심점이 각 피처에서 어떤 값을 가지는지 보여줍니다.")

        centroids = pd.DataFrame(
            kmeans_scaler.inverse_transform(kmeans.cluster_centers_),
            columns=cluster_features,
        )
        centroids.index = [f"Cluster {i}" for i in range(len(centroids))]
        centroids_display = centroids.T.copy()
        centroids_display.index.name = "피처"
        st.dataframe(centroids_display.style.format("{:.2f}").background_gradient(axis=1, cmap="RdBu_r"),
                      use_container_width=True)

        # 중심점 레이더 차트
        from sklearn.preprocessing import MinMaxScaler
        centroid_norm = pd.DataFrame(
            MinMaxScaler().fit_transform(centroids),
            columns=cluster_features, index=centroids.index,
        )

        fig_radar = go.Figure()
        for idx_c, row_c in centroid_norm.iterrows():
            fig_radar.add_trace(go.Scatterpolar(
                r=row_c.values.tolist() + [row_c.values[0]],
                theta=cluster_features + [cluster_features[0]],
                fill="toself", name=idx_c, opacity=0.5,
            ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
            height=400, margin=dict(t=30, b=30),
            title="클러스터 중심 레이더 차트 (정규화)",
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── 알고리즘 비교 요약 ──
    st.markdown("### 알고리즘 비교 요약")
    algo_compare = pd.DataFrame([
        {"알고리즘": "K-Means", "유형": "분할 기반", "장점": "빠른 수행, 해석 용이", "단점": "K 사전 지정, 구형 클러스터만", "적합 상황": "명확한 그룹 수를 알 때"},
        {"알고리즘": "DBSCAN", "유형": "밀도 기반", "장점": "K 불필요, 이상치 탐지", "단점": "밀도 차이 민감, 고차원 어려움", "적합 상황": "노이즈가 많거나 비정형 클러스터"},
        {"알고리즘": "GMM", "유형": "확률 기반", "장점": "소프트 할당, 타원형 클러스터", "단점": "수렴 불안정, K 필요", "적합 상황": "겹치는 클러스터, 확률 기반 의사결정"},
    ])
    st.dataframe(algo_compare, use_container_width=True, hide_index=True)

    # ── 클러스터별 주요 통계 비교 ──
    if "Cluster" in df.columns:
        st.markdown("### 알고리즘별 클러스터 주요 통계")
        stat_tabs = st.tabs(["K-Means", "DBSCAN", "GMM"])

        with stat_tabs[0]:
            km_stats = df.groupby("Cluster_Label").agg(
                제품수=("SKU_ID", "count"),
                평균재고=("Quantity_On_Hand", "mean"),
                평균DOI=("Days_of_Inventory", "mean"),
                평균판매=("Avg_Daily_Sales", "mean"),
            ).round(1)
            st.dataframe(km_stats, use_container_width=True)

        with stat_tabs[1]:
            if "Cluster_DBSCAN" in df.columns:
                db_stats = df.groupby("Cluster_DBSCAN").agg(
                    제품수=("SKU_ID", "count"),
                    평균재고=("Quantity_On_Hand", "mean"),
                    평균DOI=("Days_of_Inventory", "mean"),
                    평균판매=("Avg_Daily_Sales", "mean"),
                ).round(1)
                db_stats.index = [f"Cluster {i}" if i != -1 else "Noise" for i in db_stats.index]
                st.dataframe(db_stats, use_container_width=True)
            else:
                st.info("DBSCAN 모델이 로드되지 않았습니다.")

        with stat_tabs[2]:
            if "Cluster_GMM" in df.columns:
                gmm_stats = df.groupby("Cluster_GMM").agg(
                    제품수=("SKU_ID", "count"),
                    평균재고=("Quantity_On_Hand", "mean"),
                    평균DOI=("Days_of_Inventory", "mean"),
                    평균판매=("Avg_Daily_Sales", "mean"),
                    평균소속확률=("GMM_Prob", "mean"),
                ).round(3)
                gmm_stats.index = [f"Cluster {i}" for i in gmm_stats.index]
                st.dataframe(gmm_stats, use_container_width=True)
            else:
                st.info("GMM 모델이 로드되지 않았습니다.")

# ═══════════════════════════════════════════════════════════
# Tab 9: 용어 사전 (알고리즘 인사이트)
# ═══════════════════════════════════════════════════════════
if is_advanced and active_tab == 8:
    st.markdown(section_anchor("sec-glossary"), unsafe_allow_html=True)
    st.markdown(section_header("용어 사전", "발주 전략 페이지에서 사용되는 주요 용어 설명"), unsafe_allow_html=True)
    render_glossary(st)

# ── 푸터 ──────────────────────────────────────────────────
st.markdown(footer_html(), unsafe_allow_html=True)

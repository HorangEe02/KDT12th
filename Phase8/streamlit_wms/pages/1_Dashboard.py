"""Dashboard — v3.5 Enhanced Mode KPI + Cluster + Simulator + Risk Table"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_loader import load_raw_data, load_model, load_feature_info, PERISHABLE_CATEGORIES
from utils.preprocessor import prepare_cluster_features, prepare_regression_features, prepare_risk_features
from utils.styles import (
    GLOBAL_CSS, kpi_card, section_header, COLORS,
    render_common_sidebar, footer_html, section_anchor, render_mini_toc,
)

st.set_page_config(page_title="Dashboard | WMS", layout="wide")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# ── 사이드바 (공통) ───────────────────────────────────────
render_common_sidebar(st, current_page="/Dashboard")

# ── 타이틀 ────────────────────────────────────────────────
st.markdown('<div class="page-title">재고 최적화 대시보드</div>', unsafe_allow_html=True)

# ── 모드 토글 (실제 동작) ─────────────────────────────────
if "dash_mode" not in st.session_state:
    st.session_state.dash_mode = "알고리즘 인사이트"

col_mode_l, col_mode_r, _ = st.columns([1.5, 1.5, 5])
with col_mode_l:
    if st.button(
        "WMS 시뮬레이터", key="dash_basic_btn",
        use_container_width=True,
        type="secondary" if st.session_state.dash_mode == "알고리즘 인사이트" else "primary",
    ):
        st.session_state.dash_mode = "WMS 시뮬레이터"
        st.rerun()
with col_mode_r:
    if st.button(
        "알고리즘 인사이트", key="dash_adv_btn",
        use_container_width=True,
        type="primary" if st.session_state.dash_mode == "알고리즘 인사이트" else "secondary",
    ):
        st.session_state.dash_mode = "알고리즘 인사이트"
        st.rerun()

is_advanced = st.session_state.dash_mode == "알고리즘 인사이트"
mode_label = "알고리즘 인사이트 — ML 기반 KPI 요약 및 재고 현황 분석" if is_advanced else "WMS 시뮬레이터 — 핵심 지표 요약"
st.markdown(f'<div class="page-subtitle">{mode_label}</div>', unsafe_allow_html=True)

# ── 미니 목차 ────────────────────────────────────────────
if is_advanced:
    st.markdown(render_mini_toc([
        ("sec-kpi", "KPI 요약", "◈"),
        ("sec-cluster", "제품 그룹 분석", "◉"),
        ("sec-simulator", "예측 시뮬레이터", "▸"),
        ("sec-risk-table", "위험 제품 목록", "△"),
        ("sec-charts", "분포 차트", "▪"),
    ]), unsafe_allow_html=True)
else:
    st.markdown(render_mini_toc([
        ("sec-kpi", "KPI 요약", "◈"),
        ("sec-status", "재고 상태 분포", "◔"),
        ("sec-category", "카테고리별 재고", "▦"),
    ]), unsafe_allow_html=True)

df = load_raw_data()

# ── 모델 로딩 (클러스터 + 리스크) ──────────────────────────
feat_info_v5 = load_feature_info("feature_info_v5.json")

try:
    kmeans = load_model("phase_b_kmeans_baseline_v5.pkl")
    kmeans_scaler = load_model("phase_b_scaler_baseline_v5.pkl")
    cluster_features = feat_info_v5["baseline_cluster_features"]
    X_cluster = prepare_cluster_features(df, cluster_features)
    X_cluster_scaled = pd.DataFrame(
        kmeans_scaler.transform(X_cluster), columns=X_cluster.columns, index=X_cluster.index
    )
    df["Cluster"] = kmeans.predict(X_cluster_scaled)
    cluster_names = {0: "빠른 회전 제품", 1: "느린 회전 제품"}
    if len(df["Cluster"].unique()) > 2:
        cluster_names[2] = "계절성 제품"
    df["Cluster_Name"] = df["Cluster"].map(lambda c: cluster_names.get(c, f"Cluster {c}"))
except Exception:
    df["Cluster"] = 0
    df["Cluster_Name"] = "N/A"

try:
    risk_model = load_model("best_risk_model.pkl")
    risk_scaler = load_model("scaler_risk.pkl")
    risk_feat = load_feature_info("feature_info_risk.json")
    X_risk = prepare_risk_features(df, risk_feat)
    X_risk_scaled = pd.DataFrame(risk_scaler.transform(X_risk), columns=X_risk.columns, index=X_risk.index)
    df["Risk_Pred"] = risk_model.predict(X_risk_scaled)
    if hasattr(risk_model, "predict_proba"):
        df["Risk_Prob"] = risk_model.predict_proba(X_risk_scaled)[:, 1]
    else:
        df["Risk_Prob"] = df["Risk_Pred"].astype(float)
except Exception:
    df["Risk_Pred"] = df["Waste_Risk"]
    df["Risk_Prob"] = df["Waste_Risk"].astype(float)

st.markdown(section_anchor("sec-kpi"), unsafe_allow_html=True)
# ── KPI 카드 (4열) ────────────────────────────────────────
total_sku = len(df)
out_of_stock_risk = (df["Inventory_Status"] == "Out of Stock").sum() + (df["Inventory_Status"] == "Low Stock").sum()
high_waste_risk = int(df["Risk_Pred"].sum())
eoq_cost = (df["EOQ"] * df["Unit_Cost_USD"]).sum()

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(kpi_card("전체 제품 수", f"{total_sku:,}", "total_sku", COLORS["accent_green"],
                         tooltip="관리 중인 전체 제품(SKU) 수"), unsafe_allow_html=True)
with k2:
    st.markdown(kpi_card("재고 부족 위험", f"{out_of_stock_risk}", "out_of_stock", COLORS["accent_red"],
                         tooltip="품절이거나 재고가 부족한 제품 수"), unsafe_allow_html=True)
with k3:
    st.markdown(kpi_card("폐기 위험 높음", f"{high_waste_risk}", "waste_risk", COLORS["accent_orange"],
                         tooltip="유통기한 초과로 폐기될 가능성이 높은 제품 수"), unsafe_allow_html=True)
with k4:
    st.markdown(kpi_card("최적 주문 총액", f"${eoq_cost:,.0f}", "eoq_value", COLORS["accent_green"],
                         tooltip="전체 제품의 최적 주문량(EOQ)을 금액으로 환산한 총합 (EOQ × 단가)"), unsafe_allow_html=True)

# ── KPI 상세 정보 패널 ──────────────────────────────────────
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

detail_cols = st.columns(4)
with detail_cols[0]:
    with st.popover("제품 수 상세 보기"):
        st.markdown("**카테고리별 제품 수**")
        cat_counts = df["Category"].value_counts()
        for cat, cnt in cat_counts.items():
            st.markdown(f"- **{cat}**: {cnt}건 ({cnt/len(df)*100:.1f}%)")
        st.divider()
        st.markdown("**ABC 등급별 분포**")
        for abc in ["A", "B", "C"]:
            abc_n = (df["ABC_Class"] == abc).sum()
            st.markdown(f"- **{abc}등급**: {abc_n}건 ({abc_n/len(df)*100:.1f}%)")

with detail_cols[1]:
    with st.popover("재고 부족 상세 보기"):
        st.markdown("**재고 부족 제품 현황**")
        oos = df[df["Inventory_Status"] == "Out of Stock"]
        low = df[df["Inventory_Status"] == "Low Stock"]
        st.markdown(f"- **품절**: {len(oos)}건")
        st.markdown(f"- **부족**: {len(low)}건")
        st.divider()
        st.markdown("**카테고리별 부족 현황**")
        shortage = df[df["Inventory_Status"].isin(["Out of Stock", "Low Stock"])]
        if len(shortage) > 0:
            for cat, cnt in shortage["Category"].value_counts().items():
                st.markdown(f"- **{cat}**: {cnt}건")

with detail_cols[2]:
    with st.popover("폐기 위험 상세 보기"):
        st.markdown("**폐기 위험 제품 현황**")
        risk_cnt = int(df["Risk_Pred"].sum())
        st.markdown(f"- 위험 제품: **{risk_cnt}건** ({risk_cnt/len(df)*100:.1f}%)")
        st.divider()
        st.markdown("**카테고리별 위험 현황**")
        risk_items = df[df["Risk_Pred"] == 1]
        if len(risk_items) > 0:
            for cat, cnt in risk_items["Category"].value_counts().items():
                st.markdown(f"- **{cat}**: {cnt}건")

with detail_cols[3]:
    with st.popover("최적 주문 상세 보기"):
        st.markdown("**ABC 등급별 EOQ 금액**")
        for abc in ["A", "B", "C"]:
            abc_mask = df["ABC_Class"] == abc
            abc_eoq_cost = (df.loc[abc_mask, "EOQ"] * df.loc[abc_mask, "Unit_Cost_USD"]).sum()
            st.markdown(f"- **{abc}등급**: ${abc_eoq_cost:,.0f}")
        st.divider()
        avg_eoq_cost = (df["EOQ"] * df["Unit_Cost_USD"]).mean()
        st.markdown(f"**제품당 평균 EOQ 금액**: ${avg_eoq_cost:,.0f}")

st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

# ── 알고리즘 인사이트: 클러스터 분석 + 판매 예측 시뮬레이터 ────────
if is_advanced:
    st.markdown(section_anchor("sec-cluster"), unsafe_allow_html=True)
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown(section_header("고급 발주 전략", "제품 그룹 분석"), unsafe_allow_html=True)

        fig_cluster = px.scatter_3d(
            df,
            x="Quantity_On_Hand",
            y="Avg_Daily_Sales",
            z="Days_of_Inventory",
            color="Cluster_Name",
            hover_data=["SKU_ID", "Category", "ABC_Class"],
            opacity=0.7,
            color_discrete_map={
                "빠른 회전 제품": "#4CAF50",
                "느린 회전 제품": "#F44336",
                "계절성 제품": "#FF9800",
                "N/A": "#9E9E9E",
            },
        )
        fig_cluster.update_layout(
            height=450,
            margin=dict(t=10, b=10, l=0, r=0),
            scene=dict(
                xaxis_title="보유 수량",
                yaxis_title="일평균 판매량",
                zaxis_title="재고 소진 예상일",
            ),
            legend=dict(orientation="h", y=-0.05),
        )
        st.plotly_chart(fig_cluster, use_container_width=True)

    with col_right:
        st.markdown(section_anchor("sec-simulator"), unsafe_allow_html=True)
        st.markdown(section_header("판매량 예측 시뮬레이터", "ML 예측"), unsafe_allow_html=True)

        with st.container(border=True):
            sim_sku = st.selectbox("제품 선택", df["SKU_ID"].tolist(), key="dash_sim_sku",
                                   help="예측할 제품(SKU)을 선택하세요.")
            sim_row = df[df["SKU_ID"] == sim_sku].iloc[0]

            # 제품 변경 시 슬라이더 초기화
            if "dash_prev_sku" not in st.session_state or st.session_state.dash_prev_sku != sim_sku:
                st.session_state.dash_qty = int(sim_row["Quantity_On_Hand"])
                st.session_state.dash_lead = int(sim_row["Lead_Time_Days"])
                st.session_state.dash_rp = int(sim_row["Reorder_Point"])
                st.session_state.dash_prev_sku = sim_sku

            def _adj(key, delta, lo, hi):
                st.session_state[key] = max(lo, min(hi, st.session_state[key] + delta))

            sim_qty = st.slider("현재 보유 수량", 10, 1000, key="dash_qty",
                                help="지금 창고에 남아 있는 제품 수량입니다.")
            _dq1, _dq2 = st.columns(2)
            with _dq1:
                st.button("−1", key="dash_qty_m", use_container_width=True,
                          on_click=_adj, args=("dash_qty", -1, 10, 1000))
            with _dq2:
                st.button("+1", key="dash_qty_p", use_container_width=True,
                          on_click=_adj, args=("dash_qty", 1, 10, 1000))

            sim_lead = st.slider("배송 소요일", 1, 14, key="dash_lead",
                                 help="발주 후 물건이 창고에 도착하기까지 걸리는 날수입니다.")
            _dl1, _dl2 = st.columns(2)
            with _dl1:
                st.button("−1", key="dash_lead_m", use_container_width=True,
                          on_click=_adj, args=("dash_lead", -1, 1, 14))
            with _dl2:
                st.button("+1", key="dash_lead_p", use_container_width=True,
                          on_click=_adj, args=("dash_lead", 1, 1, 14))

            sim_rp = st.slider("자동 발주 기준선", 10, 800, key="dash_rp",
                               help="재고가 이 수량 아래로 떨어지면 자동으로 새 주문을 넣는 기준입니다.")
            _dr1, _dr2 = st.columns(2)
            with _dr1:
                st.button("−1", key="dash_rp_m", use_container_width=True,
                          on_click=_adj, args=("dash_rp", -1, 10, 800))
            with _dr2:
                st.button("+1", key="dash_rp_p", use_container_width=True,
                          on_click=_adj, args=("dash_rp", 1, 10, 800))

            # 예측 버튼
            predict_clicked = st.button("예측 실행", key="dash_predict_btn", type="primary", use_container_width=True)

            if predict_clicked or "dash_pred_result" in st.session_state:
                try:
                    reg_model = load_model("best_regressor.pkl")
                    reg_scaler = load_model("scaler_regression.pkl")
                    reg_feat = load_feature_info("feature_info_regression.json")

                    sim_data = df[df["SKU_ID"] == sim_sku].copy()
                    sim_data["Quantity_On_Hand"] = sim_qty
                    sim_data["Lead_Time_Days"] = sim_lead
                    sim_data["Reorder_Point"] = sim_rp

                    X_sim = prepare_regression_features(sim_data, reg_feat)
                    X_sim_scaled = pd.DataFrame(reg_scaler.transform(X_sim), columns=X_sim.columns)
                    pred_sales = reg_model.predict(X_sim_scaled)[0]
                    st.session_state.dash_pred_result = pred_sales

                    st.markdown(
                        f"""
                        <div style="text-align:center;margin-top:12px;padding:16px;background:#f5f7fa;border-radius:8px;">
                            <div style="font-size:12px;color:#6c757d;text-transform:uppercase;letter-spacing:1px;">예측 일평균 판매량</div>
                            <div style="font-size:36px;font-weight:800;color:#4CAF50;">{pred_sales:.1f}</div>
                            <div style="font-size:13px;color:#6c757d;">단위 / 일</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                except Exception:
                    st.warning("판매 예측 모델을 로드할 수 없습니다.")

# ── WMS 시뮬레이터: 간단한 요약 차트 ──────────────────────────
else:
    col_left, col_right = st.columns(2)
    STATUS_KR = {"In Stock": "In Stock (충분)", "Low Stock": "Low Stock (부족)",
                 "Out of Stock": "Out of Stock (품절)", "Expiring Soon": "Expiring Soon (임박)"}

    with col_left:
        st.markdown(section_anchor("sec-status"), unsafe_allow_html=True)
        st.markdown(section_header("재고 상태 분포"), unsafe_allow_html=True)
        status_counts = df["Inventory_Status"].value_counts()
        fig_pie = px.pie(
            values=status_counts.values,
            names=[STATUS_KR.get(s, s) for s in status_counts.index],
            color_discrete_sequence=["#4CAF50", "#FF9800", "#F44336", "#2196F3", "#9C27B0"],
            hole=0.45,
        )
        fig_pie.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=320)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_right:
        st.markdown(section_anchor("sec-category"), unsafe_allow_html=True)
        st.markdown(section_header("카테고리별 재고량"), unsafe_allow_html=True)
        cat_qty = df.groupby("Category")["Quantity_On_Hand"].sum().sort_values(ascending=False).reset_index()
        fig_cat = px.bar(cat_qty, x="Category", y="Quantity_On_Hand", color="Category")
        fig_cat.update_layout(margin=dict(t=10, b=10), height=320, showlegend=False)
        st.plotly_chart(fig_cat, use_container_width=True)

st.markdown(section_anchor("sec-risk-table"), unsafe_allow_html=True)
# ── 하단: 폐기 위험 + 재고 부족 테이블 (알고리즘 인사이트만) ──────
if is_advanced:
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    st.markdown(section_header("폐기 위험 및 재고 부족 목록", "위험 제품 현황"), unsafe_allow_html=True)

    risk_table = df[df["Risk_Pred"] == 1].sort_values("Risk_Prob", ascending=False).head(30)
    display_cols = [
        "SKU_ID", "SKU_Name", "Category", "ABC_Class",
        "Days_To_Expiry", "Risk_Prob",
        "Quantity_On_Hand", "Avg_Daily_Sales",
        "Inventory_Status", "Waste_Risk",
    ]

    if len(risk_table) > 0:
        st.dataframe(
            risk_table[display_cols].style.format({
                "Risk_Prob": "{:.3f}",
                "Avg_Daily_Sales": "{:.2f}",
                "Days_To_Expiry": "{:.0f}",
            }).background_gradient(subset=["Risk_Prob"], cmap="Reds"),
            use_container_width=True,
            height=350,
            hide_index=True,
        )
    else:
        st.success("위험 SKU 없음")

st.markdown(section_anchor("sec-charts"), unsafe_allow_html=True)
# ── 하단 차트: 재고 상태 + ABC 등급 분포 ─────────────────
if is_advanced:
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    col_b1, col_b2 = st.columns(2)

    STATUS_KR_ADV = {"In Stock": "In Stock (충분)", "Low Stock": "Low Stock (부족)",
                     "Out of Stock": "Out of Stock (품절)", "Expiring Soon": "Expiring Soon (임박)"}
    ABC_KR = {"A": "A (상위 80%)", "B": "B (중간 15%)", "C": "C (하위 5%)"}

    with col_b1:
        st.markdown(section_header("재고 상태 분포"), unsafe_allow_html=True)
        status_counts = df["Inventory_Status"].value_counts()
        fig_pie = px.pie(
            values=status_counts.values,
            names=[STATUS_KR_ADV.get(s, s) for s in status_counts.index],
            color_discrete_sequence=["#4CAF50", "#FF9800", "#F44336", "#2196F3", "#9C27B0"],
            hole=0.45,
        )
        fig_pie.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=320)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_b2:
        st.markdown(section_header("중요도 등급별 재고 가치"), unsafe_allow_html=True)
        abc_val = df.groupby("ABC_Class")["Total_Inventory_Value_USD"].sum().reset_index()
        abc_val.columns = ["ABC_Class", "Total_Value"]
        abc_val["ABC_Label"] = abc_val["ABC_Class"].map(ABC_KR)
        fig_abc = px.bar(
            abc_val, x="ABC_Label", y="Total_Value",
            color="ABC_Class",
            color_discrete_map={"A": "#F44336", "B": "#FF9800", "C": "#2196F3"},
            text_auto="$.2s",
        )
        fig_abc.update_layout(margin=dict(t=10, b=10), height=320, showlegend=False,
                              xaxis_title="ABC_Class")
        st.plotly_chart(fig_abc, use_container_width=True)

# ── 푸터 ──────────────────────────────────────────────────
st.markdown(footer_html(), unsafe_allow_html=True)

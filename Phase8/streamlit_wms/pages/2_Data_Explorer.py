"""데이터 탐색 — WMS 시뮬레이터 / 알고리즘 인사이트"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_loader import load_raw_data, CATEGORIES, ABC_CLASSES
from utils.styles import (
    GLOBAL_CSS, kpi_card, section_header, COLORS,
    render_common_sidebar, footer_html, section_anchor, render_mini_toc,
    render_custom_tabs,
)
from utils.descriptions import (
    COLUMN_DESC, NUMERIC_ANALYSIS_COLS, CATEGORICAL_COLS,
    render_algorithm_info, render_feature_importance, render_shap_analysis,
    render_glossary, ALGORITHM_INFO, GLOSSARY,
)

st.set_page_config(page_title="데이터 탐색 | WMS", layout="wide")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# ── 사이드바 (공통 목차 + 필터) ──────────────────────────────
render_common_sidebar(st, current_page="/Data_Explorer")

st.markdown('<div class="page-title">데이터 탐색기</div>', unsafe_allow_html=True)

# ── 모드 토글 ─────────────────────────────────────────────────
if "explorer_mode" not in st.session_state:
    st.session_state.explorer_mode = "알고리즘 인사이트"

col_mode_l, col_mode_r, _ = st.columns([1.5, 1.5, 5])
with col_mode_l:
    if st.button("WMS 시뮬레이터", key="explorer_basic_btn", use_container_width=True,
                 type="secondary" if st.session_state.explorer_mode == "알고리즘 인사이트" else "primary"):
        st.session_state.explorer_mode = "WMS 시뮬레이터"
        st.rerun()
with col_mode_r:
    if st.button("알고리즘 인사이트", key="explorer_adv_btn", use_container_width=True,
                 type="primary" if st.session_state.explorer_mode == "알고리즘 인사이트" else "secondary"):
        st.session_state.explorer_mode = "알고리즘 인사이트"
        st.rerun()

is_advanced = st.session_state.explorer_mode == "알고리즘 인사이트"
mode_label = (
    "알고리즘 인사이트 — 데이터 통계 / 분포 / AI 알고리즘 소개 / 용어 사전"
    if is_advanced
    else "WMS 시뮬레이터 — 인터랙티브 데이터 탐색 / 컬럼 분석 / 비교"
)
st.markdown(f'<div class="page-subtitle">{mode_label}</div>', unsafe_allow_html=True)

# ── 미니 목차 ─────────────────────────────────────────────────
if not is_advanced:
    st.markdown(
        render_mini_toc([
            ("sec-data-table",   "데이터 테이블",       "▤"),
            ("sec-summary",      "한눈에 보는 요약",     "◈"),
            ("sec-col-analysis", "컬럼별 심층 분석",     "◎"),
            ("sec-scatter",      "컬럼 간 비교",         "▪"),
        ]),
        unsafe_allow_html=True,
    )
else:
    pass  # advanced mini_toc rendered after render_custom_tabs below

if not is_advanced:
    st.info(
        "이 페이지에서는 전체 제품 데이터를 **컬럼별로 심층 분석**할 수 있습니다. "
        "원하는 컬럼을 선택하면 통계, 분포, 카테고리별 비교를 자동으로 보여줍니다."
    )

df = load_raw_data()

# ── 필터 (사이드바 하단) ──────────────────────────────────────
st.sidebar.markdown(
    """<div style="font-size:11px;color:#8e9aaf;text-transform:uppercase;letter-spacing:1px;margin:12px 0 8px;font-weight:600;">필터</div>""",
    unsafe_allow_html=True,
)
sel_categories = st.sidebar.multiselect("카테고리", CATEGORIES, default=CATEGORIES,
                                       help="식품 분류별로 필터링합니다")
sel_abc = st.sidebar.multiselect("중요도 등급 (ABC)", ABC_CLASSES, default=ABC_CLASSES,
                                 help="A=매출 상위 80%, B=중간 15%, C=하위 5%")
sel_status = st.sidebar.multiselect(
    "재고 상태",
    df["Inventory_Status"].unique().tolist(),
    default=df["Inventory_Status"].unique().tolist(),
    help="재고 보유 상황별로 필터링합니다 (충분/부족/품절 등)",
)
sel_risk = st.sidebar.radio("폐기 위험", ["전체", "Risk", "Safe"],
                            help="유통기한 초과로 폐기될 위험이 있는 제품만 보기")
sku_search = st.sidebar.text_input("제품 검색 (ID 또는 이름)",
                                   help="제품 코드(SKU ID)나 제품명으로 검색합니다")

# ── 필터 적용 ──────────────────────────────────────────────────
mask = (
    df["Category"].isin(sel_categories)
    & df["ABC_Class"].isin(sel_abc)
    & df["Inventory_Status"].isin(sel_status)
)
if sel_risk == "Risk":
    mask &= df["Waste_Risk"] == 1
elif sel_risk == "Safe":
    mask &= df["Waste_Risk"] == 0

if sku_search:
    mask &= (
        df["SKU_ID"].str.contains(sku_search, case=False, na=False)
        | df["SKU_Name"].str.contains(sku_search, case=False, na=False)
    )

filtered = df[mask]

# ── KPI ────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(kpi_card("필터 결과", f"{len(filtered):,}", "filter_count", COLORS["accent_blue"],
                         tooltip="현재 필터 조건에 맞는 제품 수"), unsafe_allow_html=True)
with k2:
    st.markdown(kpi_card("전체 제품 수", f"{len(df):,}", "all_sku", COLORS["accent_green"],
                         tooltip="관리 중인 전체 제품(SKU) 수"), unsafe_allow_html=True)
with k3:
    avg_sales = filtered["Avg_Daily_Sales"].mean() if len(filtered) > 0 else 0
    st.markdown(kpi_card("평균 일일 판매량", f"{avg_sales:.1f}", "sales_avg", COLORS["accent_orange"],
                         tooltip="필터된 제품들의 하루 평균 판매 수량"), unsafe_allow_html=True)
with k4:
    total_val = filtered["Total_Inventory_Value_USD"].sum() if len(filtered) > 0 else 0
    st.markdown(kpi_card("재고 총 가치", f"${total_val:,.0f}", "inv_value", COLORS["accent_purple"],
                         tooltip="필터된 제품들의 총 재고 금액"), unsafe_allow_html=True)

# ── KPI 상세 정보 패널 ──────────────────────────────────────────
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

detail_cols = st.columns(4)
with detail_cols[0]:
    with st.popover("필터 결과 상세"):
        st.markdown("**필터 적용 현황**")
        st.markdown(f"- 선택 카테고리: {len(sel_categories)}개")
        st.markdown(f"- 선택 ABC 등급: {len(sel_abc)}개")
        st.markdown(f"- 필터 결과: **{len(filtered)}건** / 전체 {len(df)}건")
        st.divider()
        if len(filtered) > 0:
            st.markdown("**필터 결과 카테고리 분포**")
            for cat, cnt in filtered["Category"].value_counts().items():
                st.markdown(f"- **{cat}**: {cnt}건")

with detail_cols[1]:
    with st.popover("전체 제품 분포"):
        st.markdown("**ABC 등급별 분포**")
        for abc in ["A", "B", "C"]:
            abc_n = (df["ABC_Class"] == abc).sum()
            st.markdown(f"- **{abc}등급**: {abc_n}건 ({abc_n/len(df)*100:.1f}%)")
        st.divider()
        st.markdown("**재고 상태별 분포**")
        for status, cnt in df["Inventory_Status"].value_counts().items():
            st.markdown(f"- **{status}**: {cnt}건")

with detail_cols[2]:
    with st.popover("판매량 상세 보기"):
        if len(filtered) > 0:
            st.markdown("**카테고리별 평균 일일 판매량**")
            cat_sales = filtered.groupby("Category")["Avg_Daily_Sales"].mean().sort_values(ascending=False)
            for cat, val in cat_sales.items():
                st.markdown(f"- **{cat}**: {val:.1f}개/일")
            st.divider()
            st.markdown("**ABC 등급별 평균 판매량**")
            for abc in ["A", "B", "C"]:
                abc_sales = filtered[filtered["ABC_Class"] == abc]["Avg_Daily_Sales"].mean()
                if not pd.isna(abc_sales):
                    st.markdown(f"- **{abc}등급**: {abc_sales:.1f}개/일")
        else:
            st.info("필터 결과가 없습니다")

with detail_cols[3]:
    with st.popover("재고 가치 상세"):
        if len(filtered) > 0:
            st.markdown("**카테고리별 재고 가치**")
            cat_val = filtered.groupby("Category")["Total_Inventory_Value_USD"].sum().sort_values(ascending=False)
            for cat, val in cat_val.items():
                st.markdown(f"- **{cat}**: ${val:,.0f}")
            st.divider()
            avg_val = filtered["Total_Inventory_Value_USD"].mean()
            st.markdown(f"**제품당 평균 재고 가치**: ${avg_val:,.0f}")
        else:
            st.info("필터 결과가 없습니다")

# ── 변수 설명 테이블 ──────────────────────────────────────────
COLUMN_DESCRIPTIONS = {
    "SKU_ID": "제품 고유 코드",
    "SKU_Name": "제품명",
    "Category": "식품 카테고리 (Dairy, Bakery 등)",
    "ABC_Class": "중요도 등급 (A=상위80%, B=중간15%, C=하위5%)",
    "Inventory_Status": "재고 상태 (Sufficient / Low Stock / Out of Stock)",
    "Quantity_On_Hand": "현재 보유 수량 (단위)",
    "Avg_Daily_Sales": "일평균 판매량 (단위/일)",
    "Days_of_Inventory": "재고 소진 예상일 (일)",
    "Unit_Cost_USD": "단위 원가 ($)",
    "Total_Inventory_Value_USD": "총 재고 가치 ($)",
    "Waste_Risk": "폐기 위험 여부 (1=위험, 0=안전)",
    "Warehouse_Location": "창고 위치",
    "Lead_Time_Days": "배송 소요일 (발주→입고)",
    "Reorder_Point": "자동 발주 기준선 (이 수량 이하 시 발주)",
    "Safety_Stock": "안전 재고 수량 (최소 보유 권장량)",
}

st.markdown(section_anchor("sec-data-table"), unsafe_allow_html=True)
st.markdown(section_header("데이터 테이블"), unsafe_allow_html=True)

with st.expander("컬럼 설명 보기", expanded=False):
    desc_rows = ""
    for col, desc in COLUMN_DESCRIPTIONS.items():
        desc_rows += f"""<tr style="border-bottom:1px solid #f0f0f0;">
            <td style="padding:6px 10px;font-weight:600;color:#1a1a2e;font-size:13px;white-space:nowrap;">{col}</td>
            <td style="padding:6px 10px;color:#6c757d;font-size:13px;">{desc}</td>
        </tr>"""
    st.markdown(
        f"""<div style="background:white;border-radius:10px;padding:12px;box-shadow:0 1px 6px rgba(0,0,0,0.05);">
        <table style="width:100%;border-collapse:collapse;">{desc_rows}</table>
        </div>""",
        unsafe_allow_html=True,
    )

# ── 데이터 표시 ────────────────────────────────────────────────
display_cols = [
    "SKU_ID", "SKU_Name", "Category", "ABC_Class", "Inventory_Status",
    "Quantity_On_Hand", "Avg_Daily_Sales", "Days_of_Inventory",
    "Unit_Cost_USD", "Total_Inventory_Value_USD", "Waste_Risk",
    "Warehouse_Location", "Lead_Time_Days", "Reorder_Point", "Safety_Stock",
]

st.dataframe(
    filtered[display_cols].sort_values("SKU_ID"),
    use_container_width=True,
    height=450,
    hide_index=True,
)

# ══════════════════════════════════════════════════════════════
# WMS 시뮬레이터 모드 (인터랙티브 데이터 탐색)
# ══════════════════════════════════════════════════════════════
if not is_advanced and len(filtered) > 0:

    # -- 한눈에 보는 요약 (기존 유지) --
    st.markdown(section_anchor("sec-summary"), unsafe_allow_html=True)
    st.markdown(section_header("한눈에 보는 요약"), unsafe_allow_html=True)
    sum_col1, sum_col2 = st.columns(2)
    with sum_col1:
        st.caption("카테고리별 제품 수")
        fig_cat = px.pie(filtered, names="Category", hole=0.4,
                         color_discrete_sequence=px.colors.qualitative.Set2)
        fig_cat.update_layout(height=300, margin=dict(t=20, b=20))
        st.plotly_chart(fig_cat, use_container_width=True)
    with sum_col2:
        st.caption("재고 상태별 제품 수")
        fig_status = px.pie(filtered, names="Inventory_Status", hole=0.4,
                            color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_status.update_layout(height=300, margin=dict(t=20, b=20))
        st.plotly_chart(fig_status, use_container_width=True)

    # 간단 통계 요약 (기존 유지)
    with st.expander("주요 통계 요약", expanded=True):
        sc1, sc2, sc3, sc4 = st.columns(4)
        sc1.metric("평균 보유 수량", f"{filtered['Quantity_On_Hand'].mean():.0f}개",
                   help="필터된 제품들의 평균 재고 수량")
        sc2.metric("평균 판매량", f"{filtered['Avg_Daily_Sales'].mean():.1f}개/일",
                   help="필터된 제품들의 하루 평균 판매량")
        sc3.metric("평균 재고일", f"{filtered['Days_of_Inventory'].mean():.0f}일",
                   help="평균적으로 재고가 소진되기까지 걸리는 일수")
        sc4.metric("위험 제품 비율", f"{filtered['Waste_Risk'].mean()*100:.1f}%",
                   help="필터된 제품 중 폐기 위험이 있는 제품 비율")

    # ── 컬럼별 심층 분석 ──────────────────────────────────────
    st.markdown(section_anchor("sec-col-analysis"), unsafe_allow_html=True)
    st.markdown(section_header("컬럼별 심층 분석"), unsafe_allow_html=True)
    st.caption("분석하고 싶은 컬럼을 선택하면 통계, 분포, 해석을 자동으로 보여줍니다.")

    # 컬럼 그룹핑
    COLUMN_GROUPS = {
        "수량 관련": [c for c in ["Quantity_On_Hand", "Quantity_Reserved", "Quantity_Committed",
                              "Damaged_Qty", "Returns_Qty", "Safety_Stock", "Reorder_Point",
                              "Available_Stock", "Stock_Gap", "EOQ"] if c in filtered.columns],
        "판매/수요 관련": [c for c in ["Avg_Daily_Sales", "Forecast_Next_30d", "Annual_Demand",
                                "Order_Frequency_per_month"] if c in filtered.columns],
        "기간 관련": [c for c in ["Days_of_Inventory", "Lead_Time_Days", "Days_To_Expiry",
                             "Stock_Age_Days", "Days_Since_Last_Order", "Days_To_Deplete",
                             "Remaining_Shelf_Days"] if c in filtered.columns],
        "금액 관련": [c for c in ["Unit_Cost_USD", "Last_Purchase_Price_USD",
                             "Total_Inventory_Value_USD", "Holding_Cost"] if c in filtered.columns],
        "비율/지표": [c for c in ["SKU_Churn_Rate", "Supplier_OnTime_Pct",
                             "Demand_Forecast_Accuracy_Pct", "Audit_Variance_Pct",
                             "Count_Variance", "Demand_Variability", "Supply_Risk",
                             "Reorder_Urgency", "RP_SS_Ratio"] if c in filtered.columns],
        "범주형": [c for c in CATEGORICAL_COLS if c in filtered.columns],
    }

    # 드롭다운용 옵션 만들기 (그룹명 — 컬럼명)
    col_options = []
    col_group_map = {}
    for group_name, cols in COLUMN_GROUPS.items():
        for c in cols:
            col_info = COLUMN_DESC.get(c, {})
            label = f"[{group_name}] {col_info.get('name', c)} ({c})"
            col_options.append(label)
            col_group_map[label] = c

    if col_options:
        selected_label = st.selectbox(
            "분석할 컬럼 선택",
            col_options,
            index=0,
            help="카테고리별로 그룹화된 컬럼 중 하나를 선택하세요.",
        )
        selected_col = col_group_map[selected_label]
        col_info = COLUMN_DESC.get(selected_col, {})

        # 컬럼 설명
        st.markdown(
            f"""<div style="background:linear-gradient(135deg,#f8f9fa,#e9ecef);border-radius:10px;
            padding:16px 20px;margin:10px 0;border-left:4px solid {COLORS['accent_blue']};">
            <div style="font-size:18px;font-weight:700;color:#1a1a2e;margin-bottom:4px;">
            {col_info.get('name', selected_col)}</div>
            <div style="font-size:14px;color:#6c757d;">{col_info.get('desc', '')}</div>
            <div style="font-size:12px;color:#adb5bd;margin-top:4px;">
            타입: {col_info.get('type', 'N/A')} | 단위: {col_info.get('unit', 'N/A') or '없음'}</div>
            </div>""",
            unsafe_allow_html=True,
        )

        # 범주형 vs 수치형 분석 분기
        is_categorical = selected_col in CATEGORICAL_COLS

        if is_categorical:
            # ── 범주형 컬럼 분석 ──
            vc = filtered[selected_col].value_counts()

            vc_col1, vc_col2 = st.columns(2)
            with vc_col1:
                st.caption(f"{col_info.get('name', selected_col)} — 빈도 막대 차트")
                fig_bar = px.bar(
                    x=vc.index.tolist(), y=vc.values.tolist(),
                    labels={"x": selected_col, "y": "건수"},
                    color=vc.index.tolist(),
                    color_discrete_sequence=px.colors.qualitative.Set2,
                )
                fig_bar.update_layout(height=350, margin=dict(t=20, b=20), showlegend=False)
                st.plotly_chart(fig_bar, use_container_width=True)

            with vc_col2:
                st.caption(f"{col_info.get('name', selected_col)} — 구성 비율")
                fig_pie = px.pie(
                    names=vc.index.tolist(), values=vc.values.tolist(),
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Pastel,
                )
                fig_pie.update_layout(height=350, margin=dict(t=20, b=20))
                st.plotly_chart(fig_pie, use_container_width=True)

            # 해석
            top_cat = vc.index[0] if len(vc) > 0 else "N/A"
            top_pct = (vc.values[0] / vc.values.sum() * 100) if len(vc) > 0 else 0
            st.markdown(
                f"""**해석**: `{selected_col}` 컬럼에는 **{len(vc)}개의 고유 값**이 있습니다.
                가장 많은 것은 **{top_cat}** ({top_pct:.1f}%)이며,
                가장 적은 것은 **{vc.index[-1]}** ({vc.values[-1]}건)입니다."""
            )

        else:
            # ── 수치형 컬럼 분석 ──
            col_data = filtered[selected_col].dropna()

            if len(col_data) == 0:
                st.warning("선택한 컬럼에 유효한 데이터가 없습니다.")
            else:
                # 통계 메트릭
                stats_c1, stats_c2, stats_c3, stats_c4 = st.columns(4)
                stats_c5, stats_c6, stats_c7, _ = st.columns(4)

                unit = col_info.get("unit", "")
                stats_c1.metric("평균 (Mean)", f"{col_data.mean():,.2f} {unit}")
                stats_c2.metric("중앙값 (Median)", f"{col_data.median():,.2f} {unit}")
                stats_c3.metric("표준편차 (Std)", f"{col_data.std():,.2f} {unit}")
                stats_c4.metric("최솟값 (Min)", f"{col_data.min():,.2f} {unit}")
                stats_c5.metric("최댓값 (Max)", f"{col_data.max():,.2f} {unit}")
                stats_c6.metric("Q1 (25%)", f"{col_data.quantile(0.25):,.2f} {unit}")
                stats_c7.metric("Q3 (75%)", f"{col_data.quantile(0.75):,.2f} {unit}")

                # 히스토그램 + 박스플롯
                viz_c1, viz_c2 = st.columns(2)
                with viz_c1:
                    st.caption(f"{col_info.get('name', selected_col)} — 분포 히스토그램")
                    fig_hist = px.histogram(
                        filtered, x=selected_col, nbins=30,
                        color="ABC_Class",
                        barmode="overlay",
                        color_discrete_map={"A": "#F44336", "B": "#FF9800", "C": "#2196F3"},
                    )
                    fig_hist.update_layout(height=350, margin=dict(t=20, b=20))
                    st.plotly_chart(fig_hist, use_container_width=True)

                with viz_c2:
                    st.caption(f"{col_info.get('name', selected_col)} — 박스 플롯")
                    fig_box = px.box(
                        filtered, x="Category", y=selected_col, color="Category",
                    )
                    fig_box.update_layout(height=350, margin=dict(t=20, b=20), showlegend=False)
                    st.plotly_chart(fig_box, use_container_width=True)

                # 카테고리별 분석
                st.caption("카테고리별 평균 / 합계")
                cat_agg = filtered.groupby("Category")[selected_col].agg(["mean", "sum", "count"])
                cat_agg.columns = ["평균", "합계", "건수"]
                cat_agg = cat_agg.sort_values("평균", ascending=False)
                st.dataframe(
                    cat_agg.style.format({"평균": "{:,.2f}", "합계": "{:,.2f}", "건수": "{:,.0f}"}),
                    use_container_width=True,
                )

                # 해석 텍스트
                iqr = col_data.quantile(0.75) - col_data.quantile(0.25)
                cv = col_data.std() / col_data.mean() * 100 if col_data.mean() != 0 else 0
                skew = col_data.skew()

                skew_text = "좌우 대칭에 가깝습니다" if abs(skew) < 0.5 else (
                    "오른쪽으로 긴 꼬리를 가진 분포 (높은 값 쪽에 이상치 가능성)" if skew > 0
                    else "왼쪽으로 긴 꼬리를 가진 분포 (낮은 값 쪽에 이상치 가능성)"
                )

                st.markdown(
                    f"""**해석**: `{col_info.get('name', selected_col)}` 의 평균은 **{col_data.mean():,.2f}**이고 """
                    f"""중앙값은 **{col_data.median():,.2f}**입니다. """
                    f"""변동계수(CV)는 **{cv:.1f}%**로 {'편차가 큰 편' if cv > 50 else '비교적 안정적인 편'}입니다. """
                    f"""IQR(사분위범위)은 **{iqr:,.2f}**이며, 분포 형태는 {skew_text} (왜도: {skew:.2f})."""
                )

    # ── 두 컬럼 비교 (산점도) ──────────────────────────────────
    st.markdown(section_anchor("sec-scatter"), unsafe_allow_html=True)
    st.markdown(section_header("컬럼 간 비교 (산점도)"), unsafe_allow_html=True)
    st.caption("두 수치형 컬럼을 선택하여 상관 관계를 산점도로 확인합니다.")

    # 필터된 데이터에서 사용 가능한 수치형 컬럼
    available_numeric = [c for c in NUMERIC_ANALYSIS_COLS if c in filtered.columns]

    if len(available_numeric) >= 2:
        cmp_c1, cmp_c2 = st.columns(2)
        with cmp_c1:
            x_col = st.selectbox(
                "X축 컬럼",
                available_numeric,
                index=available_numeric.index("Quantity_On_Hand") if "Quantity_On_Hand" in available_numeric else 0,
                key="scatter_x",
            )
        with cmp_c2:
            default_y_idx = available_numeric.index("Avg_Daily_Sales") if "Avg_Daily_Sales" in available_numeric else min(1, len(available_numeric) - 1)
            y_col = st.selectbox(
                "Y축 컬럼",
                available_numeric,
                index=default_y_idx,
                key="scatter_y",
            )

        x_info = COLUMN_DESC.get(x_col, {})
        y_info = COLUMN_DESC.get(y_col, {})

        fig_scatter = px.scatter(
            filtered, x=x_col, y=y_col,
            color="Category",
            hover_data=["SKU_ID", "SKU_Name"],
            labels={
                x_col: x_info.get("name", x_col),
                y_col: y_info.get("name", y_col),
            },
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig_scatter.update_layout(height=450, margin=dict(t=30, b=20))
        # 추세선
        if len(filtered) > 2:
            corr_val = filtered[[x_col, y_col]].dropna().corr().iloc[0, 1]
            fig_scatter.update_layout(
                title=f"상관계수: {corr_val:.3f} ({'강한 양의' if corr_val > 0.7 else '강한 음의' if corr_val < -0.7 else '약한'} 상관관계)"
            )
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.info("비교에 필요한 수치형 컬럼이 2개 이상 있어야 합니다.")


# ══════════════════════════════════════════════════════════════
# 알고리즘 인사이트 모드 (ML 알고리즘 소개 + 통계 + 분포)
# ══════════════════════════════════════════════════════════════
if is_advanced:
    st.markdown(
        """<div style="background:linear-gradient(135deg,#667eea,#764ba2);border-radius:12px;
        padding:20px 24px;margin:16px 0;color:white;">
        <div style="font-size:16px;font-weight:700;margin-bottom:6px;">
        이 모드에서는 WMS 시스템 뒤에서 작동하는 AI 알고리즘과 데이터 통계를 자세히 살펴볼 수 있습니다.</div>
        <div style="font-size:13px;opacity:0.9;">
        각 탭을 클릭하여 데이터의 기술 통계, 분포/상관관계, 사용된 AI 알고리즘, 용어 사전을 확인하세요.</div>
        </div>""",
        unsafe_allow_html=True,
    )

    tab_names_adv = ["데이터 통계 분석", "분포 & 상관관계", "AI 알고리즘 소개", "용어 사전"]
    active_tab = render_custom_tabs(st, tab_names_adv, "explorer_adv_tab")

    # ── 탭별 동적 미니 TOC ──────────────────────────────────────
    _adv_toc_map = {
        0: [("sec-data-table", "데이터 테이블", "▤"), ("sec-tab-stats", "데이터 통계 분석", "◇")],
        1: [("sec-data-table", "데이터 테이블", "▤"), ("sec-tab-dist", "분포 & 상관관계", "◈")],
        2: [("sec-data-table", "데이터 테이블", "▤"), ("sec-tab-algo", "AI 알고리즘 소개", "◉")],
        3: [("sec-data-table", "데이터 테이블", "▤"), ("sec-tab-glossary", "용어 사전", "▸")],
    }
    st.markdown(render_mini_toc(_adv_toc_map.get(active_tab, [])), unsafe_allow_html=True)

    # ── Tab 1: 데이터 통계 분석 ──────────────────────────────────
    if active_tab == 0:
        st.markdown(section_anchor("sec-tab-stats"), unsafe_allow_html=True)
        st.markdown(section_header("기술 통계"), unsafe_allow_html=True)
        with st.expander("기술 통계 지표 해석 가이드", expanded=True):
            st.markdown("""
| 지표 | 의미 | 활용 팁 |
|------|------|---------|
| **count** | 데이터 건수 | 결측치가 있으면 전체 건수보다 작습니다 |
| **mean** | 평균값 | 전체적인 수준을 파악할 때 사용합니다 |
| **std** | 표준편차 | 값이 크면 데이터가 넓게 퍼져 있습니다 |
| **min / max** | 최솟값 / 최댓값 | 이상치를 발견하는 데 유용합니다 |
| **25% (Q1)** | 하위 25% 지점 | 이 아래는 하위 그룹입니다 |
| **50% (중앙값)** | 정확히 중간값 | 평균보다 이상치에 강합니다 |
| **75% (Q3)** | 상위 25% 지점 | 이 위는 상위 그룹입니다 |
""")

        num_cols = [
            "Quantity_On_Hand", "Avg_Daily_Sales", "Days_of_Inventory",
            "Unit_Cost_USD", "Total_Inventory_Value_USD", "Lead_Time_Days",
            "Safety_Stock", "Reorder_Point", "Stock_Age_Days",
        ]
        available_num = [c for c in num_cols if c in filtered.columns]
        desc_df = filtered[available_num].describe().T
        # 한글 컬럼명 추가
        desc_df.insert(0, "한글명", [COLUMN_DESC.get(c, {}).get("name", c) for c in desc_df.index])
        st.dataframe(
            desc_df.style.format({c: "{:.2f}" for c in desc_df.columns if c != "한글명"}),
            use_container_width=True,
        )

        # 간단 해석
        if len(filtered) > 0:
            st.markdown("**자동 해석:**")
            for col_name in available_num[:5]:
                col_data = filtered[col_name].dropna()
                if len(col_data) == 0:
                    continue
                kr_name = COLUMN_DESC.get(col_name, {}).get("name", col_name)
                cv = col_data.std() / col_data.mean() * 100 if col_data.mean() != 0 else 0
                stability = "안정적" if cv < 30 else "보통" if cv < 60 else "편차가 큼"
                st.markdown(
                    f"- **{kr_name}**: 평균 {col_data.mean():,.1f}, 중앙값 {col_data.median():,.1f} "
                    f"(CV {cv:.0f}% — {stability})"
                )

    # ── Tab 2: 분포 & 상관관계 ───────────────────────────────────
    if active_tab == 1:
        st.markdown(section_anchor("sec-tab-dist"), unsafe_allow_html=True)
        st.markdown(section_header("분포 시각화"), unsafe_allow_html=True)

        vis_col = st.selectbox("분석 항목 선택", available_num, index=1,
                               help="분포를 확인할 데이터 항목을 선택하세요", key="adv_vis_col")
        col1, col2 = st.columns(2)

        with col1:
            fig1 = px.histogram(filtered, x=vis_col, color="ABC_Class", nbins=30, barmode="overlay",
                                color_discrete_map={"A": "#F44336", "B": "#FF9800", "C": "#2196F3"})
            fig1.update_layout(margin=dict(t=30, b=20), height=350)
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            fig2 = px.box(filtered, x="Category", y=vis_col, color="Category")
            fig2.update_layout(margin=dict(t=30, b=20), height=350, showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown(section_header("상관관계 히트맵"), unsafe_allow_html=True)
        with st.expander("상관관계 히트맵 읽는 법"):
            st.markdown("""
- **+1 (빨간색)**: 두 항목이 **함께 증가**하는 강한 양의 상관관계
- **-1 (파란색)**: 한 항목이 증가하면 다른 항목이 **감소**하는 강한 음의 상관관계
- **0 (흰색)**: 두 항목 간에 관련이 없음
- 예: `Quantity_On_Hand`와 `Days_of_Inventory`가 빨간색이면 재고가 많을수록 소진 예상일도 길다는 뜻
""")

        corr_cols = st.multiselect(
            "분석 항목 선택 (2개 이상)",
            available_num,
            default=[c for c in ["Quantity_On_Hand", "Avg_Daily_Sales", "Days_of_Inventory", "Unit_Cost_USD"]
                     if c in available_num],
            help="서로 관련성을 분석할 항목들을 2개 이상 선택하세요.",
            key="adv_corr_cols",
        )
        if len(corr_cols) >= 2:
            corr = filtered[corr_cols].corr()
            # 한글 라벨
            kr_labels = [COLUMN_DESC.get(c, {}).get("name", c) for c in corr_cols]
            fig3 = px.imshow(
                corr, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
                x=kr_labels, y=kr_labels,
            )
            fig3.update_layout(margin=dict(t=20, b=20), height=400)
            st.plotly_chart(fig3, use_container_width=True)

    # ── Tab 3: AI 알고리즘 소개 ──────────────────────────────────
    if active_tab == 2:
        st.markdown(section_anchor("sec-tab-algo"), unsafe_allow_html=True)
        st.markdown(section_header("WMS에 사용된 AI 알고리즘"), unsafe_allow_html=True)
        st.markdown(
            "아래는 이 WMS 시스템의 각 기능에 사용된 머신러닝 알고리즘입니다. "
            "각 카드를 펼쳐 알고리즘의 작동 원리와 성능 지표 해석법을 확인하세요."
        )

        # 알고리즘 카드들
        algo_sections = [
            {
                "key": "LightGBM_Classification",
                "role": "재고 상태 예측 (Inventory Status Prediction)",
                "color": "#4CAF50",
            },
            {
                "key": "XGBoost_Regression",
                "role": "판매량 예측 (Sales Prediction)",
                "color": "#2196F3",
            },
            {
                "key": "Risk_Classification",
                "role": "폐기 위험 탐지 (Waste Risk Detection)",
                "color": "#FF5722",
            },
            {
                "key": "KMeans_Clustering",
                "role": "발주 전략 군집화 (Reorder Strategy - K-Means)",
                "color": "#9C27B0",
            },
            {
                "key": "DBSCAN",
                "role": "이상치 탐지 (Anomaly Detection - DBSCAN)",
                "color": "#FF9800",
            },
            {
                "key": "GMM",
                "role": "확률적 제품 분류 (Probabilistic Clustering - GMM)",
                "color": "#00BCD4",
            },
        ]

        for section in algo_sections:
            info = ALGORITHM_INFO.get(section["key"], {})
            st.markdown(
                f"""<div style="background:white;border-radius:12px;padding:16px 20px;margin:12px 0;
                border-left:5px solid {section['color']};box-shadow:0 2px 8px rgba(0,0,0,0.06);">
                <div style="font-size:11px;color:{section['color']};text-transform:uppercase;
                letter-spacing:1px;font-weight:600;">{section['role']}</div>
                </div>""",
                unsafe_allow_html=True,
            )
            render_algorithm_info(st, section["key"])
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Tab 4: 용어 사전 ─────────────────────────────────────────
    if active_tab == 3:
        st.markdown(section_anchor("sec-tab-glossary"), unsafe_allow_html=True)
        st.markdown(section_header("AI/ML 용어 사전"), unsafe_allow_html=True)
        st.markdown(
            "머신러닝과 데이터 분석에서 자주 사용되는 용어들을 비전공자도 이해할 수 있도록 설명합니다."
        )

        # 검색 기능
        term_search = st.text_input("용어 검색", placeholder="찾고 싶은 용어를 입력하세요...", key="glossary_search")

        filtered_glossary = {
            k: v for k, v in GLOSSARY.items()
            if not term_search or term_search.lower() in k.lower() or term_search.lower() in v.lower()
        }

        if not filtered_glossary:
            st.info(f"'{term_search}'에 해당하는 용어를 찾을 수 없습니다.")
        else:
            for term, definition in filtered_glossary.items():
                st.markdown(
                    f"""<div style="background:white;border-radius:10px;padding:14px 18px;margin:8px 0;
                    box-shadow:0 1px 4px rgba(0,0,0,0.05);border-left:3px solid {COLORS['accent_blue']};">
                    <div style="font-size:15px;font-weight:700;color:#1a1a2e;margin-bottom:4px;">{term}</div>
                    <div style="font-size:13px;color:#6c757d;line-height:1.6;">{definition}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )

# ── 푸터 ──────────────────────────────────────────────────────
st.markdown(footer_html(), unsafe_allow_html=True)

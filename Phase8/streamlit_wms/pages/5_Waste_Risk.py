"""폐기 위험 관리 — v4.0 WMS 시뮬레이터 + 알고리즘 인사이트"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_loader import load_raw_data, load_model, load_feature_info, PERISHABLE_CATEGORIES
from utils.preprocessor import prepare_risk_features
from utils.styles import (
    GLOBAL_CSS, kpi_card, section_header, COLORS,
    render_common_sidebar, footer_html,
    section_anchor, render_mini_toc, render_custom_tabs,
)
from utils.descriptions import render_algorithm_info, render_feature_importance, render_shap_analysis, render_glossary, COLUMN_DESC

st.set_page_config(page_title="폐기 위험 관리 | WMS", layout="wide")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# ── 사이드바 (공통) ───────────────────────────────────────
render_common_sidebar(st, current_page="/Waste_Risk")

st.markdown('<div class="page-title">폐기 위험 탐지</div>', unsafe_allow_html=True)

# ── 모드 토글 ─────────────────────────────────────────────────
if "waste_mode" not in st.session_state:
    st.session_state.waste_mode = "알고리즘 인사이트"

col_mode_l, col_mode_r, _ = st.columns([1.5, 1.5, 5])
with col_mode_l:
    if st.button("WMS 시뮬레이터", key="waste_basic_btn", use_container_width=True,
                 type="secondary" if st.session_state.waste_mode == "알고리즘 인사이트" else "primary"):
        st.session_state.waste_mode = "WMS 시뮬레이터"
        st.rerun()
with col_mode_r:
    if st.button("알고리즘 인사이트", key="waste_adv_btn", use_container_width=True,
                 type="primary" if st.session_state.waste_mode == "알고리즘 인사이트" else "secondary"):
        st.session_state.waste_mode = "알고리즘 인사이트"
        st.rerun()

is_advanced = st.session_state.waste_mode == "알고리즘 인사이트"
mode_label = "알고리즘 인사이트 — ML 폐기 위험 탐지 | 정확도 98.8%" if is_advanced else "WMS 시뮬레이터 — 폐기 위험 제품 현황"
st.markdown(f'<div class="page-subtitle">{mode_label}</div>', unsafe_allow_html=True)

if is_advanced:
    pass  # advanced mini_toc rendered after render_custom_tabs below
else:
    st.markdown(render_mini_toc([
        ("sec-kpi",             "KPI 요약",            "◈"),
        ("sec-cat-analysis",    "카테고리별 위험 분석",  "◎"),
        ("sec-cat-summary",     "위험 요약 테이블",     "▤"),
        ("sec-risk-list",       "위험 제품 목록",       "△"),
        ("sec-whatif",          "What-if 시뮬레이터",   "▸"),
    ]), unsafe_allow_html=True)

if not is_advanced:
    st.info("이 페이지는 **유통기한이 임박**하거나 **판매 속도가 느려** 폐기될 위험이 있는 제품을 AI가 탐지합니다. "
            "카테고리별 필터링과 개별 제품 What-if 시뮬레이션을 지원합니다.")

df = load_raw_data()

# ── 모델 로딩 ──────────────────────────────────────────────
model = load_model("best_risk_model.pkl")
scaler = load_model("scaler_risk.pkl")
feat_info = load_feature_info("feature_info_risk.json")

# ── 전체 예측 수행 ─────────────────────────────────────────
X = prepare_risk_features(df, feat_info)
X_scaled = pd.DataFrame(scaler.transform(X), columns=X.columns, index=X.index)

df["Risk_Pred"] = model.predict(X_scaled)
if hasattr(model, "predict_proba"):
    df["Risk_Prob"] = model.predict_proba(X_scaled)[:, 1]
elif hasattr(model, "decision_function"):
    from scipy.special import expit
    df["Risk_Prob"] = expit(model.decision_function(X_scaled))
else:
    df["Risk_Prob"] = df["Risk_Pred"].astype(float)

# ── KPI ────────────────────────────────────────────────────
st.markdown(section_anchor("sec-kpi"), unsafe_allow_html=True)
risk_df = df[df["Risk_Pred"] == 1]
safe_df = df[df["Risk_Pred"] == 0]

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(kpi_card("위험 제품 수", f"{len(risk_df)}", "risk_sku", COLORS["accent_red"],
                         tooltip="유통기한 초과로 폐기 위험이 있는 제품 수"), unsafe_allow_html=True)
with k2:
    st.markdown(kpi_card("안전 제품 수", f"{len(safe_df)}", "safe_sku", COLORS["accent_green"],
                         tooltip="폐기 위험이 낮은 제품 수"), unsafe_allow_html=True)
with k3:
    st.markdown(kpi_card("위험 비율", f"{len(risk_df)/len(df)*100:.1f}%", "risk_rate", COLORS["accent_orange"],
                         tooltip="전체 제품 중 폐기 위험 제품이 차지하는 비율"), unsafe_allow_html=True)
with k4:
    st.markdown(kpi_card("위험 재고 금액", f"${risk_df['Total_Inventory_Value_USD'].sum():,.0f}", "risk_value", COLORS["accent_purple"],
                         tooltip="폐기 위험 제품들의 총 재고 금액 — 폐기 시 예상 손실액"), unsafe_allow_html=True)

# ── KPI 상세 정보 패널 ──────────────────────────────────────
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

detail_cols = st.columns(4)
with detail_cols[0]:
    with st.popover("위험 제품 상세 보기"):
        st.markdown("**카테고리별 위험 제품 수**")
        for cat, cnt in risk_df["Category"].value_counts().items():
            st.markdown(f"- **{cat}**: {cnt}건")
        st.divider()
        st.markdown("**ABC 등급별 위험 제품**")
        for abc in ["A", "B", "C"]:
            abc_risk = (risk_df["ABC_Class"] == abc).sum()
            st.markdown(f"- **{abc}등급**: {abc_risk}건")

with detail_cols[1]:
    with st.popover("안전 제품 상세 보기"):
        st.markdown("**카테고리별 안전 제품 수**")
        for cat, cnt in safe_df["Category"].value_counts().items():
            st.markdown(f"- **{cat}**: {cnt}건")
        st.divider()
        avg_expiry = safe_df["Days_To_Expiry"].mean() if len(safe_df) > 0 else 0
        st.markdown(f"**평균 잔여 유통기한**: {avg_expiry:.0f}일")

with detail_cols[2]:
    with st.popover("위험 비율 상세 보기"):
        st.markdown("**카테고리별 위험 비율**")
        cat_total = df.groupby("Category").size()
        cat_risk = risk_df.groupby("Category").size()
        for cat in cat_total.index:
            r = cat_risk.get(cat, 0)
            t = cat_total[cat]
            pct = r / t * 100 if t > 0 else 0
            st.markdown(f"- **{cat}**: {pct:.1f}% ({r}/{t})")

with detail_cols[3]:
    with st.popover("위험 재고 금액 상세"):
        st.markdown("**카테고리별 위험 재고 금액**")
        risk_val = risk_df.groupby("Category")["Total_Inventory_Value_USD"].sum().sort_values(ascending=False)
        for cat, val in risk_val.items():
            st.markdown(f"- **{cat}**: ${val:,.0f}")
        st.divider()
        avg_risk_val = risk_df["Total_Inventory_Value_USD"].mean() if len(risk_df) > 0 else 0
        st.markdown(f"**제품당 평균 위험 금액**: ${avg_risk_val:,.0f}")

# ══════════════════════════════════════════════════════════════
# WMS 시뮬레이터 모드
# ══════════════════════════════════════════════════════════════
if not is_advanced:
    NON_PERISHABLE = [c for c in df["Category"].unique() if c not in PERISHABLE_CATEGORIES]

    # ── 카테고리 그룹 선택 ─────────────────────────────────────
    st.markdown(section_anchor("sec-cat-analysis"), unsafe_allow_html=True)
    st.markdown(section_header("카테고리별 폐기 위험 분석"), unsafe_allow_html=True)

    col_group, col_cats = st.columns([1, 3])
    with col_group:
        cat_group = st.radio(
            "카테고리 그룹",
            ["신선식품", "비신선식품"],
            key="waste_cat_group",
            help="신선식품은 부패 위험이 높은 카테고리, 비신선식품은 나머지입니다.",
        )
    group_cats = PERISHABLE_CATEGORIES if cat_group == "신선식품" else NON_PERISHABLE
    with col_cats:
        selected_cats = st.multiselect(
            "세부 카테고리 선택",
            group_cats,
            default=group_cats,
            key="waste_selected_cats",
            help="분석할 카테고리를 선택하세요.",
        )

    if not selected_cats:
        st.warning("카테고리를 하나 이상 선택하세요.")
        st.stop()

    filtered_df = df[df["Category"].isin(selected_cats)]
    filtered_risk = filtered_df[filtered_df["Risk_Pred"] == 1]

    # ── 1) 카테고리별 요약 ─────────────────────────────────────
    st.markdown(section_anchor("sec-cat-summary"), unsafe_allow_html=True)
    st.markdown(section_header("카테고리별 위험 요약"), unsafe_allow_html=True)

    cat_summary = filtered_df.groupby("Category").agg(
        총_제품수=("SKU_ID", "count"),
        위험_제품수=("Risk_Pred", "sum"),
    ).reset_index()
    cat_summary["위험_비율"] = (cat_summary["위험_제품수"] / cat_summary["총_제품수"] * 100).round(1)

    st.dataframe(
        cat_summary.style.format({"위험_비율": "{:.1f}%"}).background_gradient(
            subset=["위험_비율"], cmap="Reds"
        ),
        use_container_width=True, hide_index=True,
    )

    # ── 2) 위험 제품 테이블 (색상 코딩) ────────────────────────
    st.markdown(section_anchor("sec-risk-list"), unsafe_allow_html=True)
    st.markdown(section_header("위험 제품 목록"), unsafe_allow_html=True)
    st.markdown("""
> **표 읽는 법**:
> - **Risk_Prob** (위험도): 1에 가까울수록 폐기 위험이 높습니다. 0.7 이상이면 즉시 조치가 필요합니다.
> - **Days_To_Expiry** (유통기한 잔여일): 30일 미만이면 주의, 7일 미만이면 긴급입니다.
> - 빨간색이 진할수록 위험도가 높은 제품입니다.
""")

    show_cols = [
        "SKU_ID", "SKU_Name", "Category", "ABC_Class",
        "Risk_Prob", "Days_To_Expiry", "Avg_Daily_Sales",
        "Quantity_On_Hand", "FIFO_FEFO", "Total_Inventory_Value_USD",
    ]
    risk_sorted = filtered_risk.sort_values("Risk_Prob", ascending=False)
    if len(risk_sorted) > 0:
        st.dataframe(
            risk_sorted[show_cols].style.format({
                "Risk_Prob": "{:.3f}",
                "Total_Inventory_Value_USD": "${:,.2f}",
                "Avg_Daily_Sales": "{:.2f}",
            }).background_gradient(subset=["Risk_Prob"], cmap="Reds"),
            use_container_width=True, height=400, hide_index=True,
        )
    else:
        st.success("선택한 카테고리에 위험 제품이 없습니다.")

    # ── 3) 긴급 알림 ──────────────────────────────────────────
    if len(filtered_risk) > 0:
        urgent = filtered_risk[filtered_risk["Days_To_Expiry"] < 7]
        warning = filtered_risk[(filtered_risk["Days_To_Expiry"] >= 7) & (filtered_risk["Days_To_Expiry"] < 30)]
        if len(urgent) > 0:
            st.error(f"유통기한 7일 미만 제품 **{len(urgent)}건** — 즉시 할인 판매 또는 폐기 검토 필요!")
        if len(warning) > 0:
            st.warning(f"유통기한 30일 미만 제품 **{len(warning)}건** — 소진 계획을 세우세요.")
        if len(urgent) == 0 and len(warning) == 0:
            st.success("유통기한 30일 미만의 긴급 제품은 없습니다.")

    # ── 개별 제품 시뮬레이터 ───────────────────────────────────
    st.markdown(section_anchor("sec-whatif"), unsafe_allow_html=True)
    st.markdown(section_header("개별 제품 What-if 시뮬레이터"), unsafe_allow_html=True)
    st.caption("특정 제품을 선택하고, 유통기한이나 판매 속도가 달라지면 위험도가 어떻게 변하는지 시뮬레이션합니다.")

    sim_products = filtered_df["SKU_ID"].tolist()
    if not sim_products:
        st.warning("시뮬레이션할 제품이 없습니다.")
    else:
        selected_sim_sku = st.selectbox(
            "제품 선택",
            sim_products,
            format_func=lambda x: f"{x} — {filtered_df[filtered_df['SKU_ID'] == x].iloc[0]['SKU_Name']}",
            key="waste_sim_sku",
        )
        row = filtered_df[filtered_df["SKU_ID"] == selected_sim_sku].iloc[0]

        # 현재 제품 정보
        col_i1, col_i2, col_i3 = st.columns(3)
        col_i1.metric("제품명", row["SKU_Name"])
        col_i2.metric("카테고리", f"{row['Category']} ({row['ABC_Class']})",
                      help="A=매출 상위 80%, B=중간 15%, C=하위 5%")
        col_i3.metric("출하 방식", row["FIFO_FEFO"],
                      help="FIFO=먼저 들어온 것 먼저 출고, FEFO=유통기한 빠른 것 먼저 출고")

        col_i4, col_i5, col_i6, col_i7 = st.columns(4)
        col_i4.metric("현재 보유 수량", f"{row['Quantity_On_Hand']}",
                      help="창고에 남아 있는 제품 수량")
        col_i5.metric("하루 평균 판매량", f"{row['Avg_Daily_Sales']:.1f}",
                      help="하루에 평균적으로 판매되는 수량")
        col_i6.metric("유통기한 잔여일", f"{row['Days_To_Expiry']:.0f}일",
                      help="유통기한까지 남은 날수")
        col_i7.metric("재고 금액", f"${row['Total_Inventory_Value_USD']:,.2f}",
                      help="이 제품 재고의 총 금액")

        st.divider()

        # 현재 위험 분석 (게이지 차트)
        risk_label = "위험" if row["Risk_Pred"] == 1 else "안전"
        risk_color = "#F44336" if row["Risk_Pred"] == 1 else "#1565C0"

        col_gauge, col_factors = st.columns([1, 2])
        with col_gauge:
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=row["Risk_Prob"] * 100,
                title={"text": f"현재 폐기 위험도: {risk_label}"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": risk_color},
                    "steps": [
                        {"range": [0, 30], "color": "#BBDEFB"},
                        {"range": [30, 70], "color": "#fdebd0"},
                        {"range": [70, 100], "color": "#fadbd8"},
                    ],
                },
            ))
            fig_gauge.update_layout(height=250, margin=dict(t=40, b=20))
            st.plotly_chart(fig_gauge, use_container_width=True)

        with col_factors:
            st.markdown("**주요 위험 요인:**")
            if row["Risk_Pred"] == 1:
                st.caption("아래 요인들이 폐기 위험을 높이고 있습니다.")
            else:
                st.caption("현재 특별한 위험 요인이 없습니다.")
            factors = []
            if row["Days_To_Expiry"] < 30:
                factors.append(f"- 유통기한 잔여일 짧음: {row['Days_To_Expiry']:.0f}일")
            if row["Category"] in PERISHABLE_CATEGORIES:
                factors.append(f"- 부패성 카테고리: {row['Category']}")
            if row["FIFO_FEFO"] == "FIFO":
                factors.append("- FIFO 정책 (FEFO 권장 검토)")
            if row["Damaged_Qty"] > 0:
                factors.append(f"- 손상 수량: {row['Damaged_Qty']}개")
            if row["Avg_Daily_Sales"] < 5:
                factors.append(f"- 낮은 판매 속도: {row['Avg_Daily_Sales']:.1f}개/일")
            if not factors:
                factors.append("- 특이 위험 요인 없음")
            st.markdown("\n".join(factors))

        # What-if 시뮬레이션
        st.markdown("---")
        st.markdown("#### What-if 시뮬레이션")
        st.caption("유통기한 잔여일이나 판매 속도가 달라지면 폐기 위험이 어떻게 변하는지 확인하세요.")

        col_sl1, col_sl2 = st.columns(2)
        with col_sl1:
            max_expiry = max(int(row["Days_To_Expiry"]) * 3, 365)
            sim_expiry = st.slider(
                "유통기한 잔여일 시뮬레이션",
                min_value=0, max_value=max_expiry,
                value=int(row["Days_To_Expiry"]),
                key="waste_sim_expiry",
                help="유통기한이 달라지면 위험도가 어떻게 변하는지 확인",
            )
        with col_sl2:
            max_sales = max(row["Avg_Daily_Sales"] * 5, 50.0)
            sim_sales = st.slider(
                "일평균 판매량 시뮬레이션",
                min_value=0.1, max_value=float(max_sales),
                value=float(row["Avg_Daily_Sales"]),
                step=0.5,
                key="waste_sim_sales",
                help="판매 속도가 변하면 재고 소진 기간이 변합니다",
            )

        # 재계산
        sim_days_to_deplete = row["Quantity_On_Hand"] / sim_sales if sim_sales > 0 else float("inf")
        sim_risk = sim_days_to_deplete > sim_expiry

        orig_days_to_deplete = row["Quantity_On_Hand"] / row["Avg_Daily_Sales"] if row["Avg_Daily_Sales"] > 0 else float("inf")

        col_sim1, col_sim2, col_sim3 = st.columns(3)
        with col_sim1:
            st.metric(
                "재고 소진 예상일",
                f"{sim_days_to_deplete:.1f}일" if sim_days_to_deplete != float("inf") else "무한",
                delta=f"{sim_days_to_deplete - orig_days_to_deplete:+.1f}일" if orig_days_to_deplete != float("inf") and sim_days_to_deplete != float("inf") else None,
                delta_color="inverse",
            )
        with col_sim2:
            st.metric(
                "유통기한 잔여일",
                f"{sim_expiry}일",
                delta=f"{sim_expiry - int(row['Days_To_Expiry']):+d}일" if sim_expiry != int(row["Days_To_Expiry"]) else None,
            )
        with col_sim3:
            sim_risk_label = "위험" if sim_risk else "안전"
            sim_risk_color_val = "#F44336" if sim_risk else "#4CAF50"
            st.markdown(
                f"<div style='text-align:center; padding:16px; border-radius:8px; "
                f"background:{sim_risk_color_val}22; border:2px solid {sim_risk_color_val};'>"
                f"<div style='font-size:14px; color:#666;'>시뮬레이션 결과</div>"
                f"<div style='font-size:28px; font-weight:bold; color:{sim_risk_color_val};'>{sim_risk_label}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

        # 시뮬레이션 게이지
        sim_risk_pct = min(100, max(0, (sim_days_to_deplete / sim_expiry * 100) if sim_expiry > 0 else 100))
        sim_gauge_color = "#F44336" if sim_risk else "#1565C0"

        fig_sim_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=sim_risk_pct,
            title={"text": "소진일/유통기한 비율 (%)"},
            number={"suffix": "%"},
            gauge={
                "axis": {"range": [0, 200]},
                "bar": {"color": sim_gauge_color},
                "steps": [
                    {"range": [0, 70], "color": "#BBDEFB"},
                    {"range": [70, 100], "color": "#fdebd0"},
                    {"range": [100, 200], "color": "#fadbd8"},
                ],
                "threshold": {
                    "line": {"color": "#F44336", "width": 3},
                    "thickness": 0.75,
                    "value": 100,
                },
            },
        ))
        fig_sim_gauge.update_layout(height=250, margin=dict(t=40, b=20))
        st.plotly_chart(fig_sim_gauge, use_container_width=True)

        # 해석 및 권장 조치
        st.markdown("**해석 및 권장 조치:**")
        if sim_risk:
            if sim_days_to_deplete != float("inf"):
                shortage_days = sim_days_to_deplete - sim_expiry
                st.error(
                    f"현재 판매 속도(일 {sim_sales:.1f}개)로는 재고 소진에 **{sim_days_to_deplete:.0f}일**이 걸리지만, "
                    f"유통기한은 **{sim_expiry}일** 남았습니다. "
                    f"유통기한보다 **{shortage_days:.0f}일 더** 걸려 폐기 위험이 있습니다."
                )
            else:
                st.error("판매가 거의 없어 재고 소진이 불가능합니다. 즉시 조치가 필요합니다.")

            st.markdown("""
**권장 조치:**
1. 할인 판매를 통해 판매 속도를 높이세요.
2. 묶음 판매나 프로모션을 검토하세요.
3. 유통기한이 매우 짧다면 폐기 검토가 필요합니다.
4. FEFO(유통기한순 출고) 정책 적용을 권장합니다.
""")
        else:
            st.success(
                f"현재 조건에서 재고 소진에 **{sim_days_to_deplete:.0f}일**, "
                f"유통기한은 **{sim_expiry}일** 남아 있어 안전합니다. "
                f"유통기한 전에 충분히 소진할 수 있습니다."
            )

# ══════════════════════════════════════════════════════════════
# 알고리즘 인사이트 모드
# ══════════════════════════════════════════════════════════════
if is_advanced:
    tab_names_adv = ["위험 제품 분석", "신선식품 분석", "AI 모델 분석", "SHAP 분석", "개별 제품 예측", "용어 사전"]
    active_tab = render_custom_tabs(st, tab_names_adv, "waste_adv_tab")

    # ── 탭별 동적 미니 TOC ──────────────────────────────────────
    _adv_toc_map = {
        0: [("sec-kpi", "KPI 요약", "◈"), ("sec-risk-sku", "위험 제품 목록", "△")],
        1: [("sec-kpi", "KPI 요약", "◈"), ("sec-perishable", "신선식품 분석", "◔")],
        2: [("sec-kpi", "KPI 요약", "◈"), ("sec-ai-model", "AI 모델 분석", "◉")],
        3: [("sec-kpi", "KPI 요약", "◈"), ("sec-shap", "SHAP 분석", "◎")],
        4: [("sec-kpi", "KPI 요약", "◈"), ("sec-individual", "개별 제품 예측", "◇")],
        5: [("sec-kpi", "KPI 요약", "◈"), ("sec-glossary", "용어 사전", "▸")],
    }
    st.markdown(render_mini_toc(_adv_toc_map.get(active_tab, [])), unsafe_allow_html=True)

    # ── Tab 0: 위험 제품 분석 ──────────────────────────────────
    if active_tab == 0:
        st.markdown(section_anchor("sec-risk-sku"), unsafe_allow_html=True)
        st.markdown(section_header("폐기 위험 SKU 목록"), unsafe_allow_html=True)

        col_filter1, col_filter2 = st.columns(2)
        with col_filter1:
            risk_cat = st.multiselect(
                "카테고리 필터", df["Category"].unique().tolist(),
                default=PERISHABLE_CATEGORIES, key="risk_cat",
                help="분석할 식품 카테고리를 선택하세요",
            )
        with col_filter2:
            risk_sort = st.selectbox("정렬 기준",
                                     ["Risk_Prob", "Days_To_Expiry", "Total_Inventory_Value_USD"],
                                     format_func=lambda x: {"Risk_Prob": "폐기 위험도", "Days_To_Expiry": "유통기한 잔여일", "Total_Inventory_Value_USD": "재고 금액"}[x],
                                     help="목록을 어떤 기준으로 정렬할지 선택하세요")

        risk_filtered = risk_df[risk_df["Category"].isin(risk_cat)].sort_values(
            risk_sort, ascending=(risk_sort == "Days_To_Expiry")
        )

        show_cols = [
            "SKU_ID", "SKU_Name", "Category", "ABC_Class",
            "Risk_Prob", "Days_To_Expiry", "Avg_Daily_Sales",
            "Quantity_On_Hand", "FIFO_FEFO", "Total_Inventory_Value_USD",
        ]
        st.dataframe(
            risk_filtered[show_cols].style.format({
                "Risk_Prob": "{:.3f}",
                "Total_Inventory_Value_USD": "${:,.2f}",
                "Avg_Daily_Sales": "{:.2f}",
            }).background_gradient(subset=["Risk_Prob"], cmap="Reds"),
            use_container_width=True, height=400, hide_index=True,
        )

        col_v1, col_v2 = st.columns(2)
        with col_v1:
            cat_risk_counts = risk_filtered.groupby("Category").size().reset_index(name="Count")
            fig1 = px.bar(cat_risk_counts, x="Category", y="Count", color="Category",
                          color_discrete_sequence=px.colors.qualitative.Set2)
            fig1.update_layout(showlegend=False, margin=dict(t=20, b=20), height=350)
            st.plotly_chart(fig1, use_container_width=True)

        with col_v2:
            fig2 = px.scatter(
                risk_filtered, x="Days_To_Expiry", y="Risk_Prob",
                color="Category", size="Total_Inventory_Value_USD",
                hover_data=["SKU_ID", "SKU_Name"],
            )
            fig2.update_layout(margin=dict(t=20, b=20), height=350)
            st.plotly_chart(fig2, use_container_width=True)

    # ── Tab 1: 신선식품 분석 ──────────────────────────────────
    if active_tab == 1:
        st.markdown(section_anchor("sec-perishable"), unsafe_allow_html=True)
        st.markdown(section_header("신선식품 카테고리 상세 분석"), unsafe_allow_html=True)

        perishable = df[df["Category"].isin(PERISHABLE_CATEGORIES)]
        perish_agg = perishable.groupby("Category").agg(
            Total=("SKU_ID", "count"), Risk=("Risk_Pred", "sum"),
        ).reset_index()
        perish_agg["Safe"] = perish_agg["Total"] - perish_agg["Risk"]
        perish_agg["Risk_Rate"] = (perish_agg["Risk"] / perish_agg["Total"] * 100).round(1)

        col_p1, col_p2 = st.columns([1, 1])
        with col_p1:
            st.dataframe(
                perish_agg.style.format({"Risk_Rate": "{:.1f}%"}).background_gradient(
                    subset=["Risk_Rate"], cmap="Reds"
                ), use_container_width=True, hide_index=True,
            )

        with col_p2:
            fig3 = px.bar(
                perish_agg, x="Category", y=["Risk", "Safe"], barmode="stack",
                color_discrete_map={"Risk": "#F44336", "Safe": "#1565C0"},
            )
            fig3.update_layout(margin=dict(t=20, b=20), height=350)
            st.plotly_chart(fig3, use_container_width=True)

        st.markdown(section_header("출하 방식별 위험 분석", "FIFO=선입선출, FEFO=유통기한순 출고"), unsafe_allow_html=True)
        with st.expander("출하 방식 용어 해설"):
            st.markdown("""
- **FIFO (First In, First Out)**: 먼저 입고된 제품을 먼저 출고. 범용적이지만 유통기한 관리에는 불리할 수 있음.
- **FEFO (First Expiry, First Out)**: 유통기한이 가장 빠른 제품을 먼저 출고. 신선식품에 권장.
- 위험률(Risk_Rate)이 높은 출하 방식은 전환을 검토해 보세요.
""")
        fifo_risk = perishable.groupby("FIFO_FEFO").agg(
            Total=("SKU_ID", "count"), Risk=("Risk_Pred", "sum"),
        ).reset_index()
        fifo_risk["Risk_Rate"] = (fifo_risk["Risk"] / fifo_risk["Total"] * 100).round(1)
        st.dataframe(fifo_risk, use_container_width=True, hide_index=True)

    # ── Tab 2: AI 모델 분석 ───────────────────────────────────
    if active_tab == 2:
        st.markdown(section_anchor("sec-ai-model"), unsafe_allow_html=True)
        st.markdown(section_header("AI 모델 분석"), unsafe_allow_html=True)

        # 알고리즘 소개
        render_algorithm_info(st, "Risk_Classification")

        st.divider()

        # 모델 정확도 메트릭
        st.markdown("#### 모델 성능 지표")
        if hasattr(model, "predict_proba") or hasattr(model, "predict"):
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
            y_true = df["Waste_Risk"]
            y_pred = df["Risk_Pred"]

            acc = accuracy_score(y_true, y_pred)
            prec = precision_score(y_true, y_pred, zero_division=0)
            rec = recall_score(y_true, y_pred, zero_division=0)
            f1 = f1_score(y_true, y_pred, zero_division=0)

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("정확도 (Accuracy)", f"{acc:.1%}")
            m2.metric("정밀도 (Precision)", f"{prec:.1%}")
            m3.metric("재현율 (Recall)", f"{rec:.1%}")
            m4.metric("F1 점수", f"{f1:.1%}")

            if "Risk_Prob" in df.columns:
                try:
                    auc = roc_auc_score(y_true, df["Risk_Prob"])
                    st.metric("AUC-ROC", f"{auc:.4f}")
                except Exception:
                    pass

        st.divider()

        # 피처 중요도
        st.markdown("#### 피처 중요도 분석")
        render_feature_importance(st, model, X.columns.tolist(), title="폐기 위험 모델 — 피처 중요도")

        # 상위 피처가 폐기 위험에 미치는 영향 해석
        st.markdown("#### 상위 피처가 폐기 위험에 미치는 영향")
        if hasattr(model, "feature_importances_"):
            fi_series = pd.Series(model.feature_importances_, index=X.columns)
            top_feats = fi_series.sort_values(ascending=False).head(5)
            for feat_name, imp_val in top_feats.items():
                col_info = COLUMN_DESC.get(feat_name, {})
                kr_name = col_info.get("name", feat_name)
                desc = col_info.get("desc", "")
                st.markdown(f"- **{kr_name}** (중요도: {imp_val:.4f})")
                if desc:
                    st.caption(f"  {desc}")
                # 추가 해석
                if feat_name in ("Days_To_Expiry", "Remaining_Shelf_Days"):
                    st.caption("  → 유통기한이 짧을수록 폐기 위험이 높아집니다.")
                elif feat_name in ("Avg_Daily_Sales",):
                    st.caption("  → 판매 속도가 느릴수록 재고 소진이 어려워 폐기 위험이 높아집니다.")
                elif feat_name in ("Days_To_Deplete",):
                    st.caption("  → 재고 소진 예상일이 유통기한보다 길면 폐기 위험이 있습니다.")
                elif feat_name in ("Quantity_On_Hand",):
                    st.caption("  → 보유 수량이 많을수록 유통기한 내 소진이 어려울 수 있습니다.")
                elif feat_name == "FIFO_FEFO_encoded":
                    st.caption("  → FEFO 정책을 사용하면 유통기한 관리에 유리합니다.")

    # ── Tab 3: SHAP 분석 ─────────────────────────────────────
    if active_tab == 3:
        st.markdown(section_anchor("sec-shap"), unsafe_allow_html=True)
        st.markdown(section_header("SHAP 분석"), unsafe_allow_html=True)
        st.caption("SHAP(SHapley Additive exPlanations)은 각 피처가 개별 예측에 얼마나 기여했는지를 수학적으로 설명합니다.")
        render_shap_analysis(st, model, X_scaled, X.columns.tolist())

    # ── Tab 4: 개별 제품 예측 ────────────────────────────────
    if active_tab == 4:
        st.markdown(section_anchor("sec-individual"), unsafe_allow_html=True)
        st.markdown(section_header("개별 제품 폐기 위험 예측"), unsafe_allow_html=True)

        selected_sku = st.selectbox("제품 선택", df["SKU_ID"].tolist(),
                                    help="폐기 위험을 분석할 제품을 선택하세요",
                                    key="waste_adv_sku")
        row = df[df["SKU_ID"] == selected_sku].iloc[0]

        col_i1, col_i2, col_i3 = st.columns(3)
        col_i1.metric("제품명", row["SKU_Name"])
        col_i2.metric("카테고리", f"{row['Category']} ({row['ABC_Class']})",
                      help="A=매출 상위 80%, B=중간 15%, C=하위 5%")
        col_i3.metric("출하 방식", row["FIFO_FEFO"],
                      help="FIFO=먼저 들어온 것 먼저 출고, FEFO=유통기한 빠른 것 먼저 출고")

        col_i4, col_i5, col_i6, col_i7 = st.columns(4)
        col_i4.metric("현재 보유 수량", f"{row['Quantity_On_Hand']}",
                      help="창고에 남아 있는 제품 수량")
        col_i5.metric("하루 평균 판매량", f"{row['Avg_Daily_Sales']:.1f}",
                      help="하루에 평균적으로 판매되는 수량")
        col_i6.metric("유통기한 잔여일", f"{row['Days_To_Expiry']:.0f}일",
                      help="유통기한까지 남은 날수")
        col_i7.metric("재고 금액", f"${row['Total_Inventory_Value_USD']:,.2f}",
                      help="이 제품 재고의 총 금액")

        st.divider()

        risk_label = "위험" if row["Risk_Pred"] == 1 else "안전"
        risk_color = "#F44336" if row["Risk_Pred"] == 1 else "#1565C0"

        col_r1, col_r2 = st.columns([1, 2])
        with col_r1:
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=row["Risk_Prob"] * 100,
                title={"text": f"폐기 위험도: {risk_label}"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": risk_color},
                    "steps": [
                        {"range": [0, 30], "color": "#BBDEFB"},
                        {"range": [30, 70], "color": "#fdebd0"},
                        {"range": [70, 100], "color": "#fadbd8"},
                    ],
                },
            ))
            fig_gauge.update_layout(height=250, margin=dict(t=40, b=20))
            st.plotly_chart(fig_gauge, use_container_width=True)

        with col_r2:
            st.markdown("**주요 위험 요인:**")
            if row["Risk_Pred"] == 1:
                st.caption("아래 요인들이 폐기 위험을 높이고 있습니다. 해당 요인을 개선하면 위험을 줄일 수 있습니다.")
            else:
                st.caption("현재 특별한 위험 요인이 없습니다.")
            factors = []
            if row["Days_To_Expiry"] < 30:
                factors.append(f"- 유통기한 잔여일 짧음: {row['Days_To_Expiry']:.0f}일")
            if row["Category"] in PERISHABLE_CATEGORIES:
                factors.append(f"- 부패성 카테고리: {row['Category']}")
            if row["FIFO_FEFO"] == "FIFO":
                factors.append("- FIFO 정책 (FEFO 권장 검토)")
            if row["Damaged_Qty"] > 0:
                factors.append(f"- 손상 수량: {row['Damaged_Qty']}개")
            if row["Avg_Daily_Sales"] < 5:
                factors.append(f"- 낮은 판매 속도: {row['Avg_Daily_Sales']:.1f}개/일")
            if not factors:
                factors.append("- 특이 위험 요인 없음")
            st.markdown("\n".join(factors))

    # ── Tab 5: 용어 사전 ─────────────────────────────────────
    if active_tab == 5:
        st.markdown(section_anchor("sec-glossary"), unsafe_allow_html=True)
        st.markdown(section_header("용어 사전"), unsafe_allow_html=True)
        render_glossary(st)

# ── 푸터 ──────────────────────────────────────────────────
st.markdown(footer_html(), unsafe_allow_html=True)

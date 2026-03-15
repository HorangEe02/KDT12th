"""판매량 예측 — v4.0 WMS 시뮬레이터 + 알고리즘 인사이트 (XGBoost Regression)"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_loader import load_raw_data, load_model, load_feature_info
from utils.preprocessor import prepare_regression_features
from utils.styles import (
    GLOBAL_CSS, kpi_card, section_header, COLORS,
    render_common_sidebar, footer_html,
    section_anchor, render_mini_toc, render_custom_tabs,
)
from utils.descriptions import (
    render_algorithm_info, render_feature_importance,
    render_shap_analysis, render_glossary, COLUMN_DESC,
)

st.set_page_config(page_title="판매량 예측 | WMS", layout="wide")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# ── 사이드바 (공통) ───────────────────────────────────────
render_common_sidebar(st, current_page="/Sales_Prediction")

st.markdown('<div class="page-title">판매량 예측 시뮬레이터</div>', unsafe_allow_html=True)

# ── 모드 토글 ─────────────────────────────────────────────────
if "sales_mode" not in st.session_state:
    st.session_state.sales_mode = "알고리즘 인사이트"

col_mode_l, col_mode_r, _ = st.columns([1.5, 1.5, 5])
with col_mode_l:
    if st.button("WMS 시뮬레이터", key="sales_basic_btn", use_container_width=True,
                 type="secondary" if st.session_state.sales_mode == "알고리즘 인사이트" else "primary"):
        st.session_state.sales_mode = "WMS 시뮬레이터"
        st.rerun()
with col_mode_r:
    if st.button("알고리즘 인사이트", key="sales_adv_btn", use_container_width=True,
                 type="primary" if st.session_state.sales_mode == "알고리즘 인사이트" else "secondary"):
        st.session_state.sales_mode = "알고리즘 인사이트"
        st.rerun()

is_advanced = st.session_state.sales_mode == "알고리즘 인사이트"
mode_label = (
    "알고리즘 인사이트 — ML 판매량 예측 모델 | XGBoost (정확도 94.8%, 평균 오차 4.79)"
    if is_advanced
    else "WMS 시뮬레이터 — 개별 제품 판매량 예측"
)
st.markdown(f'<div class="page-subtitle">{mode_label}</div>', unsafe_allow_html=True)

# ── 미니 목차 ──────────────────────────────────────────────
if not is_advanced:
    st.markdown(render_mini_toc([
        ("sec-product",    "개별 제품 예측",         "◎"),
        ("sec-compare",    "실제 vs AI 예측 비교",   "◇"),
        ("sec-simulation", "조건 변경 시뮬레이션",   "▸"),
        ("sec-sim-chart",  "시뮬레이션 비교 차트",   "▪"),
    ]), unsafe_allow_html=True)

if not is_advanced:
    st.info("이 페이지에서는 AI가 예측한 **하루 평균 판매량**을 확인할 수 있습니다. "
            "재고 수량이나 배송일을 바꿔가며 판매량이 어떻게 변하는지 시뮬레이션해 보세요.")

df = load_raw_data()

# ── 모델 로딩 ──────────────────────────────────────────────
model = load_model("best_regressor.pkl")
scaler = load_model("scaler_regression.pkl")
feat_info = load_feature_info("feature_info_regression.json")

# ── 전체 예측 ──────────────────────────────────────────────
X = prepare_regression_features(df, feat_info)
X_scaled = pd.DataFrame(scaler.transform(X), columns=X.columns, index=X.index)
df["Sales_Pred"] = model.predict(X_scaled)
df["Error"] = df["Avg_Daily_Sales"] - df["Sales_Pred"]
df["Abs_Error"] = df["Error"].abs()

# ── KPI ────────────────────────────────────────────────────
rmse = np.sqrt((df["Error"] ** 2).mean())
mae = df["Abs_Error"].mean()
r2 = 1 - (df["Error"] ** 2).sum() / ((df["Avg_Daily_Sales"] - df["Avg_Daily_Sales"].mean()) ** 2).sum()

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(kpi_card("예측 정확도", f"{r2:.4f}", "r2", COLORS["accent_green"],
                         tooltip="R² — 모델이 실제 판매량을 얼마나 잘 설명하는지 (1에 가까울수록 좋음)"), unsafe_allow_html=True)
with k2:
    st.markdown(kpi_card("평균 예측 오차", f"{rmse:.2f}", "rmse", COLORS["accent_blue"],
                         tooltip="RMSE — 예측값과 실제값의 평균적인 차이 (낮을수록 정확)"), unsafe_allow_html=True)
with k3:
    st.markdown(kpi_card("평균 오차 크기", f"{mae:.2f}", "mae", COLORS["accent_orange"],
                         tooltip="MAE — 예측이 평균적으로 몇 개 단위 벗어나는지 (낮을수록 좋음)"), unsafe_allow_html=True)
with k4:
    st.markdown(kpi_card("평균 일일 판매량", f"{df['Avg_Daily_Sales'].mean():.2f}", "avg_sales", COLORS["accent_purple"],
                         tooltip="전체 제품의 하루 평균 판매 수량"), unsafe_allow_html=True)

# ── KPI 상세 정보 패널 ──────────────────────────────────────
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

detail_cols = st.columns(4)
with detail_cols[0]:
    with st.popover("R² 상세 보기"):
        st.markdown("**ABC 등급별 R²**")
        for abc in sorted(df["ABC_Class"].unique()):
            seg = df[df["ABC_Class"] == abc]
            ss_res = (seg["Error"] ** 2).sum()
            ss_tot = ((seg["Avg_Daily_Sales"] - seg["Avg_Daily_Sales"].mean()) ** 2).sum()
            seg_r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0
            st.markdown(f"**등급 {abc}** ({len(seg)}건): R² = `{seg_r2:.4f}`")
            st.progress(min(max(seg_r2, 0), 1.0))
        st.divider()
        st.markdown("**카테고리별 R² (상위 5)**")
        cat_r2s = []
        for cat in df["Category"].unique():
            seg = df[df["Category"] == cat]
            ss_res = (seg["Error"] ** 2).sum()
            ss_tot = ((seg["Avg_Daily_Sales"] - seg["Avg_Daily_Sales"].mean()) ** 2).sum()
            cat_r2s.append({"Category": cat, "R2": 1 - ss_res / ss_tot if ss_tot > 0 else 0, "N": len(seg)})
        cat_r2_df = pd.DataFrame(cat_r2s).sort_values("R2", ascending=False)
        for _, r in cat_r2_df.head(5).iterrows():
            st.markdown(f"- **{r['Category']}** ({r['N']}건): `{r['R2']:.4f}`")

with detail_cols[1]:
    with st.popover("RMSE 상세 보기"):
        st.markdown("**판매량 구간별 RMSE**")
        bins = [0, 20, 40, 70, float("inf")]
        labels = ["저판매 (0~20)", "중판매 (20~40)", "고판매 (40~70)", "초고판매 (70+)"]
        df["_Bin"] = pd.cut(df["Avg_Daily_Sales"], bins=bins, labels=labels, right=False)
        for lbl in labels:
            seg = df[df["_Bin"] == lbl]
            if len(seg) > 0:
                seg_rmse = np.sqrt((seg["Error"] ** 2).mean())
                st.markdown(f"**{lbl}** ({len(seg)}건)")
                st.markdown(f"  RMSE = `{seg_rmse:.2f}`, MAE = `{seg['Abs_Error'].mean():.2f}`")
        df.drop(columns=["_Bin"], inplace=True)

with detail_cols[2]:
    with st.popover("MAE 상세 보기"):
        st.markdown("**오차 크기 분포**")
        thresholds = [1, 2, 5, 10]
        for t in thresholds:
            cnt = (df["Abs_Error"] <= t).sum()
            st.markdown(f"- |오차| ≤ {t}: **{cnt}건** ({cnt/len(df)*100:.1f}%)")
        st.divider()
        st.markdown("**오차가 큰 제품 (Top 5)**")
        top_err = df.nlargest(5, "Abs_Error")[["SKU_ID", "SKU_Name", "Avg_Daily_Sales", "Sales_Pred", "Abs_Error"]]
        for _, r in top_err.iterrows():
            st.markdown(f"- **{r['SKU_ID']}**: 실제 {r['Avg_Daily_Sales']:.1f} → 예측 {r['Sales_Pred']:.1f} (오차 {r['Abs_Error']:.1f})")

with detail_cols[3]:
    with st.popover("판매량 분포 보기"):
        st.markdown("**전체 판매량 통계**")
        st.markdown(f"- 평균: `{df['Avg_Daily_Sales'].mean():.2f}`")
        st.markdown(f"- 중앙값: `{df['Avg_Daily_Sales'].median():.2f}`")
        st.markdown(f"- 표준편차: `{df['Avg_Daily_Sales'].std():.2f}`")
        st.markdown(f"- 최소: `{df['Avg_Daily_Sales'].min():.2f}`")
        st.markdown(f"- 최대: `{df['Avg_Daily_Sales'].max():.2f}`")
        st.divider()
        st.markdown("**ABC 등급별 평균 판매량**")
        for abc in sorted(df["ABC_Class"].unique()):
            seg = df[df["ABC_Class"] == abc]
            st.markdown(f"- **등급 {abc}**: 평균 `{seg['Avg_Daily_Sales'].mean():.2f}` ({len(seg)}건)")

# ══════════════════════════════════════════════════════════════
# WMS 시뮬레이터 모드 (formerly 기본 모드)
# ══════════════════════════════════════════════════════════════
if not is_advanced:
    st.markdown(section_anchor("sec-product"), unsafe_allow_html=True)
    st.markdown(section_header("개별 제품 판매량 예측"), unsafe_allow_html=True)

    selected_sku = st.selectbox(
        "제품 선택", df["SKU_ID"].tolist(), key="sales_sku",
        format_func=lambda x: f"{x} — {df[df['SKU_ID'] == x].iloc[0]['SKU_Name']}",
        help="분석할 개별 제품(SKU)을 선택하세요",
    )
    row = df[df["SKU_ID"] == selected_sku].iloc[0]

    # ── 제품 정보 메트릭 ──────────────────────────────────────
    col_i1, col_i2, col_i3 = st.columns(3)
    col_i1.metric("제품명", row["SKU_Name"])
    col_i2.metric("카테고리", f"{row['Category']} ({row['ABC_Class']})")
    col_i3.metric("창고", row["Warehouse_Location"].split(" - ")[0])

    col_i4, col_i5, col_i6, col_i7 = st.columns(4)
    col_i4.metric("현재 보유 수량", f"{int(row['Quantity_On_Hand']):,}",
                  help="지금 창고에 남아 있는 제품 수량")
    col_i5.metric("재주문점 (ROP)", f"{int(row['Reorder_Point']):,}",
                  help="재고가 이 수준 아래로 떨어지면 자동 발주")
    col_i6.metric("배송 소요일", f"{int(row['Lead_Time_Days'])}일",
                  help="발주 후 물건이 도착하기까지 걸리는 날수")
    col_i7.metric("재고 소진 예상일", f"{row['Days_of_Inventory']:.1f}일",
                  help="현재 속도로 팔리면 재고가 며칠 후 바닥나는지")

    # ── 실제 vs ML 예측 비교 ──────────────────────────────────
    st.divider()
    st.markdown(section_anchor("sec-compare"), unsafe_allow_html=True)
    st.markdown(section_header("실제 vs AI 예측 비교"), unsafe_allow_html=True)

    col_av1, col_av2, col_av3 = st.columns(3)
    col_av1.metric("실제 일일 판매량", f"{row['Avg_Daily_Sales']:.2f}",
                   help="실제 하루 평균 판매 수량")
    col_av2.metric("AI 예측 판매량", f"{row['Sales_Pred']:.2f}",
                   help="모델이 예측한 하루 평균 판매 수량")
    col_av3.metric("예측 오차", f"{row['Error']:.2f}",
                   help="실제값 - 예측값 (양수면 과소예측, 음수면 과대예측)")

    # 정확도 평가
    err = row['Error']
    if abs(err) < 2:
        st.success(f"AI 예측이 매우 정확합니다 (오차 {abs(err):.1f}개). 이 제품의 판매 패턴이 안정적입니다.")
    elif err > 0:
        st.warning(f"AI가 실제보다 **{abs(err):.1f}개 적게** 예측했습니다. 예상보다 잘 팔리는 제품이니 재고를 넉넉히 확보하세요.")
    else:
        st.info(f"AI가 실제보다 **{abs(err):.1f}개 많게** 예측했습니다. 실제 판매가 예상보다 적으니 과잉 재고에 주의하세요.")

    # ── 시뮬레이션 섹션 ──────────────────────────────────────
    st.divider()
    st.markdown(section_anchor("sec-simulation"), unsafe_allow_html=True)
    st.markdown(section_header("조건 변경 시뮬레이션", "값을 바꿔서 예측 결과가 어떻게 달라지는지 확인하세요"), unsafe_allow_html=True)

    sim_row = df[df["SKU_ID"] == selected_sku].iloc[0]

    # 제품 변경 시 슬라이더 초기화
    if "sp_prev_sku" not in st.session_state or st.session_state.sp_prev_sku != selected_sku:
        st.session_state.sp_sim_qty = int(sim_row["Quantity_On_Hand"])
        st.session_state.sp_sim_rp = int(sim_row["Reorder_Point"])
        st.session_state.sp_sim_lead = int(sim_row["Lead_Time_Days"])
        st.session_state.sp_prev_sku = selected_sku

    def _adj(key, delta, lo, hi):
        st.session_state[key] = max(lo, min(hi, st.session_state[key] + delta))

    sim_col1, sim_col2, sim_col3 = st.columns(3)
    with sim_col1:
        sim_qty = st.slider("현재 보유 수량", 10, 1000, key="sp_sim_qty",
                            help="지금 창고에 남아 있는 제품 수량")
        _m1, _p1 = st.columns(2)
        with _m1:
            st.button("−1", key="sp_qty_m", use_container_width=True,
                      on_click=_adj, args=("sp_sim_qty", -1, 10, 1000))
        with _p1:
            st.button("+1", key="sp_qty_p", use_container_width=True,
                      on_click=_adj, args=("sp_sim_qty", 1, 10, 1000))
    with sim_col2:
        sim_rp = st.slider("자동 발주 기준선", 10, 800, key="sp_sim_rp",
                           help="재고가 이 수량 아래로 떨어지면 자동으로 새 주문을 넣는 기준")
        _m2, _p2 = st.columns(2)
        with _m2:
            st.button("−1", key="sp_rp_m", use_container_width=True,
                      on_click=_adj, args=("sp_sim_rp", -1, 10, 800))
        with _p2:
            st.button("+1", key="sp_rp_p", use_container_width=True,
                      on_click=_adj, args=("sp_sim_rp", 1, 10, 800))
    with sim_col3:
        sim_lead = st.slider("배송 소요일", 1, 14, key="sp_sim_lead",
                             help="발주 후 물건이 창고에 도착하기까지 걸리는 날수")
        _m3, _p3 = st.columns(2)
        with _m3:
            st.button("−1", key="sp_lead_m", use_container_width=True,
                      on_click=_adj, args=("sp_sim_lead", -1, 1, 14))
        with _p3:
            st.button("+1", key="sp_lead_p", use_container_width=True,
                      on_click=_adj, args=("sp_sim_lead", 1, 1, 14))

    # 시뮬레이션 실행 버튼
    if st.button("시뮬레이션 실행", key="sp_run_sim", type="primary", use_container_width=True):
        st.session_state.sp_sim_executed = True

    # 시뮬레이션 결과 (항상 계산하되 표시는 조건부)
    sim_data = df[df["SKU_ID"] == selected_sku].copy()
    sim_data["Quantity_On_Hand"] = sim_qty
    sim_data["Reorder_Point"] = sim_rp
    sim_data["Lead_Time_Days"] = sim_lead

    X_sim = prepare_regression_features(sim_data, feat_info)
    X_sim_scaled = pd.DataFrame(scaler.transform(X_sim), columns=X_sim.columns)
    sim_pred = model.predict(X_sim_scaled)[0]

    col_sim1, col_sim2 = st.columns(2)
    col_sim1.metric("시뮬레이션 예측 판매량", f"{sim_pred:.2f}",
                    help="조건을 변경했을 때의 예측 일일 판매량")
    col_sim2.metric("기존 대비 변화", f"{sim_pred - row['Sales_Pred']:+.2f}",
                    help="원래 예측값 대비 얼마나 변화했는지")

    # 시뮬레이션 해석
    diff = sim_pred - row['Sales_Pred']
    if abs(diff) < 0.5:
        st.success("조건 변경에도 예측 판매량이 거의 동일합니다. 현재 설정이 안정적입니다.")
    elif diff > 0:
        st.warning(f"예측 판매량이 **{diff:+.2f}개** 증가했습니다. 재고를 더 확보해 두는 것이 좋습니다.")
    else:
        st.info(f"예측 판매량이 **{diff:+.2f}개** 감소했습니다. 과잉 재고에 주의하세요.")

    # ── 비교 바 차트 ──────────────────────────────────────────
    st.divider()
    st.markdown(section_anchor("sec-sim-chart"), unsafe_allow_html=True)
    st.markdown(section_header("원본 vs 시뮬레이션 예측 비교"), unsafe_allow_html=True)

    bar_data = pd.DataFrame({
        "구분": ["실제 판매량", "원본 예측", "시뮬레이션 예측"],
        "판매량": [row["Avg_Daily_Sales"], row["Sales_Pred"], sim_pred],
    })
    fig_bar = px.bar(
        bar_data, x="구분", y="판매량", color="구분",
        color_discrete_map={
            "실제 판매량": COLORS["accent_green"],
            "원본 예측": COLORS["accent_blue"],
            "시뮬레이션 예측": COLORS["accent_orange"],
        },
        text_auto=".2f",
    )
    fig_bar.update_layout(height=350, margin=dict(t=20, b=20), showlegend=False)
    st.plotly_chart(fig_bar, use_container_width=True)


# ══════════════════════════════════════════════════════════════
# 알고리즘 인사이트 모드 (formerly 고급 모드)
# ══════════════════════════════════════════════════════════════
if is_advanced:
    tab_names_adv = ["예측 정확도", "XGBoost 알고리즘", "SHAP 분석", "성능 상세 분석", "용어 사전"]
    active_tab = render_custom_tabs(st, tab_names_adv, "sales_adv_tab")

    # Advanced mode: tab-aware TOC
    _adv_toc_map = {
        0: [("sec-accuracy", "예측 정확도", "◈")],
        1: [("sec-algorithm", "XGBoost 알고리즘", "◉")],
        2: [("sec-shap", "SHAP 분석", "◎")],
        3: [("sec-perf", "성능 상세 분석", "▪")],
        4: [("sec-glossary", "용어 사전", "▸")],
    }
    st.markdown(render_mini_toc(_adv_toc_map.get(active_tab, [])), unsafe_allow_html=True)

    # ── Tab 1: 예측 정확도 ────────────────────────────────────
    if active_tab == 0:
        st.markdown(section_anchor("sec-accuracy"), unsafe_allow_html=True)
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(section_header("실제 vs 예측 산점도"), unsafe_allow_html=True)
            fig1 = px.scatter(
                df, x="Avg_Daily_Sales", y="Sales_Pred", color="ABC_Class",
                color_discrete_map={"A": "#F44336", "B": "#FF9800", "C": "#2196F3"},
                hover_data=["SKU_ID", "Category"], opacity=0.6,
            )
            max_val = max(df["Avg_Daily_Sales"].max(), df["Sales_Pred"].max())
            fig1.add_trace(go.Scatter(
                x=[0, max_val], y=[0, max_val], mode="lines",
                line=dict(dash="dash", color="gray"), name="이상적 예측선",
            ))
            fig1.update_layout(height=400, margin=dict(t=20, b=20))
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            st.markdown(section_header("예측 오차 분포"), unsafe_allow_html=True)
            fig2 = px.histogram(df, x="Error", nbins=40, color_discrete_sequence=[COLORS["accent_purple"]])
            fig2.add_vline(x=0, line_dash="dash", line_color="red")
            fig2.update_layout(height=400, margin=dict(t=20, b=20))
            st.plotly_chart(fig2, use_container_width=True)

        # ── 오차 비대칭 심층 분석 ────────────────────────────────
        st.markdown(section_header("예측 오차 비대칭 분석", "과대/과소 예측 패턴 상세"), unsafe_allow_html=True)
        with st.expander("오차 분석 용어 해석"):
            st.markdown("""
- **과대 예측**: AI가 실제보다 **높게** 예측 → 재고를 너무 많이 준비할 위험
- **과소 예측**: AI가 실제보다 **낮게** 예측 → 품절 위험
- **Bias(편향)**: 양수면 과소예측 경향, 음수면 과대예측 경향
- **±2σ 선**: 이 범위를 벗어나면 이상치(예측이 크게 빗나간 제품)
""")

        over = df[df["Error"] < 0]
        under = df[df["Error"] > 0]
        accurate = df[df["Abs_Error"] < 2]

        col_e1, col_e2, col_e3 = st.columns(3)
        col_e1.metric("과대 예측", f"{len(over)}건 ({len(over)/len(df)*100:.1f}%)",
                      help="모델이 실제보다 높게 예측한 제품 수")
        col_e2.metric("과소 예측", f"{len(under)}건 ({len(under)/len(df)*100:.1f}%)",
                      help="모델이 실제보다 낮게 예측한 제품 수")
        col_e3.metric("정확 (|오차|<2)", f"{len(accurate)}건 ({len(accurate)/len(df)*100:.1f}%)",
                      help="오차가 2 이내인 정확한 예측 제품 수")

        # 잔차 vs 예측값 산점도
        st.markdown("**잔차 vs 예측값 (이상치 탐지)**")
        fig_resid = px.scatter(df, x="Sales_Pred", y="Error", color="ABC_Class",
                                color_discrete_map={"A": "#F44336", "B": "#FF9800", "C": "#2196F3"},
                                opacity=0.5, hover_data=["SKU_ID", "Category"])
        fig_resid.add_hline(y=0, line_dash="dash", line_color="gray")
        fig_resid.add_hline(y=2*df["Error"].std(), line_dash="dot", line_color="red",
                             annotation_text="+2σ")
        fig_resid.add_hline(y=-2*df["Error"].std(), line_dash="dot", line_color="red",
                             annotation_text="-2σ")
        fig_resid.update_layout(height=400, margin=dict(t=20, b=20),
                                 xaxis_title="예측 판매량", yaxis_title="잔차 (실제-예측)")
        st.plotly_chart(fig_resid, use_container_width=True)

    # ── Tab 2: XGBoost 알고리즘 ──────────────────────────────
    if active_tab == 1:
        st.markdown(section_anchor("sec-algorithm"), unsafe_allow_html=True)
        render_algorithm_info(st, "XGBoost_Regression")

        st.divider()
        st.markdown(section_header("모델 성능 지표"), unsafe_allow_html=True)
        mk1, mk2, mk3 = st.columns(3)
        mk1.metric("R² (결정계수)", f"{r2:.4f}", help="1에 가까울수록 모델이 데이터를 잘 설명합니다")
        mk2.metric("RMSE", f"{rmse:.2f}", help="예측 오차의 크기 (낮을수록 정확)")
        mk3.metric("MAE", f"{mae:.2f}", help="예측이 평균적으로 몇 개 빗나갔는지")

        st.divider()
        st.markdown(section_header("피처 중요도 분석"), unsafe_allow_html=True)
        render_feature_importance(st, model, X.columns.tolist(),
                                  title="XGBoost 판매량 예측 — 피처 중요도")

        st.divider()
        st.markdown("#### 핵심 피처가 판매량 예측에 미치는 영향")
        st.markdown("""
판매량 예측 모델이 가장 중요하게 참고하는 피처들의 의미:

- **판매량 관련 피처** (Avg_Daily_Sales, Forecast_Next_30d 등): 과거 판매 패턴이 미래 판매를 가장 잘 예측합니다.
- **재고 관련 피처** (Quantity_On_Hand, Safety_Stock 등): 재고 수준이 판매 기회와 직결됩니다. 재고가 부족하면 판매 기회를 놓칩니다.
- **수요 변동성**: 수요가 불안정한 제품은 예측이 어렵고, 안전재고를 더 확보해야 합니다.
- **배송/공급 피처** (Lead_Time_Days, Supplier_OnTime_Pct 등): 공급망의 안정성이 재고 가용성에 영향을 줍니다.
""")

    # ── Tab 3: SHAP 분석 ─────────────────────────────────────
    if active_tab == 2:
        st.markdown(section_anchor("sec-shap"), unsafe_allow_html=True)
        st.markdown(section_header("SHAP 분석", "각 피처가 예측에 기여하는 정도를 시각화"), unsafe_allow_html=True)
        render_shap_analysis(st, model, X_scaled, X.columns.tolist())

    # ── Tab 4: 성능 상세 분석 ────────────────────────────────
    if active_tab == 3:
        st.markdown(section_anchor("sec-perf"), unsafe_allow_html=True)
        st.markdown(section_header("판매량 구간별 예측 성능"), unsafe_allow_html=True)
        with st.expander("지표 해석 가이드"):
            st.markdown("""
- **RMSE**: 예측 오차의 크기 (낮을수록 정확). 큰 오차에 더 민감합니다.
- **MAE**: 예측이 평균적으로 몇 개나 빗나갔는지 (낮을수록 좋음)
- **Bias**: 양수=과소예측 경향, 음수=과대예측 경향. 0에 가까울수록 편향 없음.
- 일반적으로 고판매 제품은 오차 절댓값이 크지만 **비율** 기준으로는 정확할 수 있습니다.
""")

        bins = [0, 20, 40, 70, float("inf")]
        labels = ["저판매 (0~20)", "중판매 (20~40)", "고판매 (40~70)", "초고판매 (70+)"]
        df["Sales_Bin"] = pd.cut(df["Avg_Daily_Sales"], bins=bins, labels=labels, right=False)

        segment_stats = []
        for label in labels:
            seg = df[df["Sales_Bin"] == label]
            if len(seg) > 0:
                segment_stats.append({
                    "구간": label, "N": len(seg),
                    "RMSE": round(np.sqrt((seg["Error"] ** 2).mean()), 2),
                    "MAE": round(seg["Abs_Error"].mean(), 2),
                    "Bias": round(seg["Error"].mean(), 2),
                })

        seg_df = pd.DataFrame(segment_stats)
        st.dataframe(
            seg_df.style.background_gradient(subset=["RMSE"], cmap="Reds"),
            use_container_width=True, hide_index=True,
        )

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            fig3 = px.bar(seg_df, x="구간", y="RMSE", color="구간")
            fig3.update_layout(showlegend=False, height=350, margin=dict(t=20, b=20))
            st.plotly_chart(fig3, use_container_width=True)

        with col_s2:
            fig4 = px.bar(seg_df, x="구간", y="Bias", color="Bias", color_continuous_scale="RdBu_r")
            fig4.update_layout(height=350, margin=dict(t=20, b=20))
            st.plotly_chart(fig4, use_container_width=True)

        st.markdown(section_header("카테고리별 예측 성능"), unsafe_allow_html=True)
        cat_perf = []
        for cat in sorted(df["Category"].unique()):
            seg = df[df["Category"] == cat]
            cat_perf.append({
                "Category": cat, "N": len(seg),
                "Mean Sales": round(seg["Avg_Daily_Sales"].mean(), 2),
                "RMSE": round(np.sqrt((seg["Error"] ** 2).mean()), 2),
                "MAE": round(seg["Abs_Error"].mean(), 2),
            })
        st.dataframe(pd.DataFrame(cat_perf), use_container_width=True, hide_index=True)

    # ── Tab 5: 용어 사전 ─────────────────────────────────────
    if active_tab == 4:
        st.markdown(section_anchor("sec-glossary"), unsafe_allow_html=True)
        st.markdown(section_header("ML 용어 사전", "비전공자를 위한 개념 설명"), unsafe_allow_html=True)
        render_glossary(st)

# ── 푸터 ──────────────────────────────────────────────────
st.markdown(footer_html(), unsafe_allow_html=True)

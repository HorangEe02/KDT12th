"""재고 상태 분류 — v4.0 WMS 시뮬레이터 + 알고리즘 인사이트 (LightGBM) + KPI 상세"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.metrics import confusion_matrix, classification_report
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_loader import load_raw_data, load_model, load_feature_info
from utils.preprocessor import prepare_classification_features
from utils.styles import (
    GLOBAL_CSS, kpi_card, section_header, COLORS,
    render_common_sidebar, footer_html,
    section_anchor, render_mini_toc, render_custom_tabs,
)
from utils.descriptions import (
    render_algorithm_info, render_feature_importance,
    render_shap_analysis, render_glossary, COLUMN_DESC,
)

st.set_page_config(page_title="재고 상태 분류 | WMS", layout="wide")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# ── 사이드바 (공통) ───────────────────────────────────────
render_common_sidebar(st, current_page="/Inventory_Status")

st.markdown('<div class="page-title">재고 상태 분류</div>', unsafe_allow_html=True)

# ── 모드 토글 ─────────────────────────────────────────────────
if "inventory_mode" not in st.session_state:
    st.session_state.inventory_mode = "알고리즘 인사이트"

col_mode_l, col_mode_r, _ = st.columns([1.5, 1.5, 5])
with col_mode_l:
    if st.button("WMS 시뮬레이터", key="inv_basic_btn", use_container_width=True,
                 type="secondary" if st.session_state.inventory_mode == "알고리즘 인사이트" else "primary"):
        st.session_state.inventory_mode = "WMS 시뮬레이터"
        st.rerun()
with col_mode_r:
    if st.button("알고리즘 인사이트", key="inv_adv_btn", use_container_width=True,
                 type="primary" if st.session_state.inventory_mode == "알고리즘 인사이트" else "secondary"):
        st.session_state.inventory_mode = "알고리즘 인사이트"
        st.rerun()

is_advanced = st.session_state.inventory_mode == "알고리즘 인사이트"
mode_label = (
    "알고리즘 인사이트 — ML 재고 상태 예측 | 정확도 98.8%"
    if is_advanced
    else "WMS 시뮬레이터 — 재고 상태 분류 시뮬레이션"
)
st.markdown(f'<div class="page-subtitle">{mode_label}</div>', unsafe_allow_html=True)

# ── 미니 목차 ──────────────────────────────────────────────
if not is_advanced:
    st.markdown(render_mini_toc([
        ("sec-product-selector",     "제품 선택",         "◎"),
        ("sec-classification-result","AI 분류 결과",      "◉"),
        ("sec-whatif-simulation",    "What-If 시뮬레이션", "▸"),
    ]), unsafe_allow_html=True)

if not is_advanced:
    st.info("이 페이지는 각 제품의 **재고 상태**(충분 / 부족 / 품절 등)를 AI가 자동으로 분류한 결과를 보여줍니다. "
            "제품을 선택하고 파라미터를 조정하여 **What-If 시뮬레이션**을 수행할 수 있습니다.")

df = load_raw_data()

# ── 모델 로딩 ──────────────────────────────────────────────
model = load_model("best_classification_model.pkl")
scaler = load_model("scaler_classification.pkl")
label_enc = load_model("label_encoder.pkl")
feat_info = load_feature_info("feature_info_classification.json")

# ── 전체 예측 ──────────────────────────────────────────────
X = prepare_classification_features(df, feat_info)
X_scaled = pd.DataFrame(scaler.transform(X), columns=X.columns, index=X.index)

pred_encoded = model.predict(X_scaled)
df["Status_Pred"] = label_enc.inverse_transform(pred_encoded)

if hasattr(model, "predict_proba"):
    proba = model.predict_proba(X_scaled)
    class_names = label_enc.inverse_transform(range(len(label_enc.classes_)))
    for i, cls in enumerate(class_names):
        df[f"Prob_{cls}"] = proba[:, i]

# ── KPI ────────────────────────────────────────────────────
accuracy = (df["Inventory_Status"] == df["Status_Pred"]).mean()
misclass_count = (df["Inventory_Status"] != df["Status_Pred"]).sum()
n_classes = len(label_enc.classes_)

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(kpi_card("전체 정확도", f"{accuracy:.1%}", "accuracy", COLORS["accent_green"],
                         tooltip="모델이 재고 상태를 올바르게 예측한 비율"), unsafe_allow_html=True)
with k2:
    st.markdown(kpi_card("전체 제품 수", f"{len(df):,}", "all_sku", COLORS["accent_blue"],
                         tooltip="분석 대상인 전체 제품(SKU) 수"), unsafe_allow_html=True)
with k3:
    st.markdown(kpi_card("상태 유형 수", f"{n_classes}", "class_count", COLORS["accent_purple"],
                         tooltip="구분되는 재고 상태 종류 수 (충분/부족/품절 등)"), unsafe_allow_html=True)
with k4:
    st.markdown(kpi_card("잘못 분류된 제품", f"{misclass_count}", "misclass", COLORS["accent_red"],
                         tooltip="모델이 실제와 다르게 예측한 제품 수"), unsafe_allow_html=True)

# ── KPI 상세 정보 패널 ──────────────────────────────────────
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

detail_cols = st.columns(4)
with detail_cols[0]:
    with st.popover("정확도 상세 보기"):
        st.markdown("**클래스별 정확도**")
        for cls in sorted(df["Inventory_Status"].unique()):
            cls_mask = df["Inventory_Status"] == cls
            cls_acc = (df.loc[cls_mask, "Inventory_Status"] == df.loc[cls_mask, "Status_Pred"]).mean()
            cls_n = cls_mask.sum()
            st.markdown(f"**{cls}** ({cls_n}건): `{cls_acc:.1%}`")
            st.progress(cls_acc)

with detail_cols[1]:
    with st.popover("제품 분포 보기"):
        st.markdown("**카테고리별 제품 수**")
        cat_counts = df["Category"].value_counts()
        for cat, cnt in cat_counts.items():
            st.markdown(f"- **{cat}**: {cnt}건 ({cnt/len(df)*100:.1f}%)")

with detail_cols[2]:
    with st.popover("상태 범주 보기"):
        st.markdown("**재고 상태 유형 목록**")
        for cls in sorted(label_enc.classes_):
            cls_count = (df["Inventory_Status"] == cls).sum()
            pred_count = (df["Status_Pred"] == cls).sum()
            st.markdown(f"**{cls}**")
            st.markdown(f"  - 실제: {cls_count}건 / 예측: {pred_count}건")
        st.divider()
        st.markdown("**유형 설명**")
        status_desc = {
            "In Stock": "재고 충분 — 정상 수준",
            "Low Stock": "재고 부족 — 발주 검토 필요",
            "Out of Stock": "품절 — 긴급 발주 필요",
            "Expiring Soon": "유통기한 임박 — 할인/폐기 검토",
        }
        for s, d in status_desc.items():
            if s in label_enc.classes_:
                st.markdown(f"- **{s}**: {d}")

with detail_cols[3]:
    with st.popover("오분류 제품 보기"):
        misclassified = df[df["Inventory_Status"] != df["Status_Pred"]]
        if len(misclassified) == 0:
            st.success("오분류 제품 없음")
        else:
            st.markdown(f"**총 {len(misclassified)}건 오분류**")
            for _, row in misclassified.iterrows():
                st.markdown(
                    f"- **{row['SKU_ID']}** ({row['SKU_Name']}): "
                    f"실제 `{row['Inventory_Status']}` → 예측 `{row['Status_Pred']}`"
                )

# ══════════════════════════════════════════════════════════════
# WMS 시뮬레이터 모드
# ══════════════════════════════════════════════════════════════
if not is_advanced:
    st.markdown(section_header("제품별 재고 상태 시뮬레이터"), unsafe_allow_html=True)
    st.caption("제품을 선택하고 파라미터를 조정하여 AI가 재고 상태를 어떻게 분류하는지 확인하세요.")

    # ── 제품 선택 ──────────────────────────────────────────
    st.markdown(section_anchor("sec-product-selector"), unsafe_allow_html=True)
    selected_sku = st.selectbox(
        "제품 선택 (SKU)",
        df["SKU_ID"].tolist(),
        key="inv_sim_sku",
        format_func=lambda x: f"{x} — {df[df['SKU_ID'] == x].iloc[0]['SKU_Name']}",
        help="재고 상태를 시뮬레이션할 제품을 선택하세요",
    )
    row = df[df["SKU_ID"] == selected_sku].iloc[0]

    # ── 1. 제품 정보 카드 ──────────────────────────────────
    st.markdown(section_header("제품 기본 정보"), unsafe_allow_html=True)
    info_c1, info_c2, info_c3, info_c4 = st.columns(4)
    info_c1.metric("제품명", row["SKU_Name"])
    info_c2.metric("카테고리", row["Category"])
    info_c3.metric("ABC 등급", row["ABC_Class"],
                   help="A=매출 상위 80%, B=중간 15%, C=하위 5%")
    info_c4.metric("창고", row["Warehouse_Location"].split(" - ")[0])

    # ── 2. 현재 실제 데이터 메트릭 ──────────────────────────
    st.markdown(section_header("현재 실제 데이터"), unsafe_allow_html=True)
    d_c1, d_c2, d_c3, d_c4 = st.columns(4)
    d_c1.metric("현재 보유 수량", f"{row['Quantity_On_Hand']:,}",
                help="창고에 남아 있는 제품 수량")
    d_c2.metric("일평균 판매량", f"{row['Avg_Daily_Sales']:.1f}",
                help="하루에 평균적으로 판매되는 수량")
    d_c3.metric("유통기한 잔여일", f"{row['Days_To_Expiry']:.0f}일" if pd.notna(row.get("Days_To_Expiry")) else "N/A",
                help="유통기한까지 남은 일수")
    d_c4.metric("재고 소진 예상일", f"{row['Days_of_Inventory']:.1f}일",
                help="현재 판매 속도로 재고가 며칠 후 바닥나는지")

    d2_c1, d2_c2, d2_c3, d2_c4 = st.columns(4)
    d2_c1.metric("자동 발주 기준선", f"{row['Reorder_Point']:.0f}",
                 help="재고가 이 수량 아래로 떨어지면 새 주문을 넣는 기준")
    d2_c2.metric("안전 재고", f"{row['Safety_Stock']:.0f}",
                 help="예상치 못한 수요 변동에 대비한 최소 재고량")
    d2_c3.metric("배송 소요일", f"{row['Lead_Time_Days']}일",
                 help="주문 후 물건이 도착하기까지 걸리는 날수")
    d2_c4.metric("재고 보관일", f"{row['Stock_Age_Days']}일",
                 help="현재 재고가 창고에 보관된 기간")

    # ── 3. ML 분류 결과 ────────────────────────────────────
    st.markdown(section_anchor("sec-classification-result"), unsafe_allow_html=True)
    st.markdown(section_header("AI 재고 상태 분류 결과"), unsafe_allow_html=True)
    status = row["Status_Pred"]
    status_config = {
        "In Stock": ("충분", "#4CAF50",
                     "현재 재고가 충분합니다. 급하게 발주하지 않아도 됩니다.",
                     "현재 판매 속도 대비 보유 수량이 충분하고, 재주문점 이상을 유지하고 있습니다."),
        "Low Stock": ("부족", "#FF9800",
                      "재고가 줄어들고 있습니다. 곧 발주를 진행하세요.",
                      "보유 수량이 재주문점에 근접하거나 일평균 판매량 대비 재고 소진 예상일이 짧습니다."),
        "Out of Stock": ("품절", "#F44336",
                         "재고가 바닥났습니다! 즉시 긴급 발주가 필요합니다.",
                         "보유 수량이 0이거나 극도로 낮아 판매가 불가능한 상태입니다."),
        "Expiring Soon": ("유통기한 임박", "#F44336",
                          "곧 유통기한이 만료됩니다. 할인 판매나 폐기를 검토하세요.",
                          "유통기한 잔여일이 짧아 현재 판매 속도로는 기한 내 소진이 어렵습니다."),
    }
    label, color, advice, reason = status_config.get(status, ("알 수 없음", "#999", "", ""))

    st.markdown(f"""
<div style="background:linear-gradient(135deg, {color}15, {color}05); border-left:4px solid {color};
            padding:16px 20px; border-radius:8px; margin:12px 0;">
    <span style="font-size:18px; font-weight:700; color:{color};">AI 판정: {label} ({status})</span><br>
    <span style="color:#555; font-size:14px;">{advice}</span>
</div>""", unsafe_allow_html=True)

    # ── 4. 확률 분포 차트 ──────────────────────────────────
    if hasattr(model, "predict_proba"):
        prob_cols = [c for c in df.columns if c.startswith("Prob_")]
        if prob_cols:
            st.markdown(section_header("분류 확률 분포"), unsafe_allow_html=True)
            st.caption("막대가 높을수록 해당 상태일 가능성이 높습니다. 가장 높은 막대가 AI의 최종 판정입니다.")
            probs = {c.replace("Prob_", ""): row[c] for c in prob_cols}
            prob_colors = {
                "In Stock": "#4CAF50", "Low Stock": "#FF9800",
                "Out of Stock": "#F44336", "Expiring Soon": "#E91E63",
            }
            bar_colors = [prob_colors.get(k, COLORS["accent_blue"]) for k in probs.keys()]
            fig_prob = go.Figure(go.Bar(
                x=list(probs.keys()), y=list(probs.values()),
                marker_color=bar_colors,
                text=[f"{v:.1%}" for v in probs.values()],
                textposition="outside",
            ))
            fig_prob.update_layout(
                height=320, margin=dict(t=20, b=20),
                yaxis_title="확률", xaxis_title="재고 상태",
                yaxis_range=[0, 1.1],
            )
            st.plotly_chart(fig_prob, use_container_width=True)

    # ── 5. 해석 및 액션 ───────────────────────────────────
    st.markdown(f"""
<div style="background:#f8f9fa; border-radius:8px; padding:16px 20px; margin:8px 0;">
    <span style="font-size:15px; font-weight:600; color:#333;">해석</span><br>
    <span style="color:#555; font-size:14px;">
        AI가 이 제품의 재고 상태를 <strong style="color:{color};">{label}</strong>로 분류했습니다.
        이유: {reason}
    </span>
</div>""", unsafe_allow_html=True)

    # 액션 추천
    action_map = {
        "In Stock": ("정상 운영", "현재 발주 주기를 유지하세요. 특별한 조치가 필요하지 않습니다.", "#4CAF50"),
        "Low Stock": ("발주 검토", "재주문점 아래로 떨어지기 전에 발주를 진행하세요. "
                      f"현재 배송 소요일({row['Lead_Time_Days']}일)을 고려하여 미리 주문하는 것이 좋습니다.", "#FF9800"),
        "Out of Stock": ("긴급 발주", "즉시 긴급 발주를 진행하세요. 공급업체에 긴급 배송을 요청하고, "
                         "대체 상품을 통한 임시 대응도 검토하세요.", "#F44336"),
        "Expiring Soon": ("할인/폐기 검토", "할인 판매로 빠르게 소진하거나, 폐기 절차를 준비하세요. "
                          "FEFO(유통기한 순) 출하 방식 적용을 권장합니다.", "#F44336"),
    }
    act_title, act_desc, act_color = action_map.get(status, ("확인 필요", "", "#999"))
    st.markdown(f"""
<div style="background:linear-gradient(135deg, {act_color}10, {act_color}05);
            border:1px solid {act_color}30; border-radius:8px; padding:14px 18px; margin:8px 0;">
    <span style="font-size:14px; font-weight:700; color:{act_color};">권장 조치: {act_title}</span><br>
    <span style="color:#555; font-size:13px;">{act_desc}</span>
</div>""", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════
    # 시뮬레이션 섹션
    # ══════════════════════════════════════════════════════
    st.markdown(section_anchor("sec-whatif-simulation"), unsafe_allow_html=True)
    st.divider()
    st.markdown(section_header("What-If 시뮬레이션", "파라미터를 조정하여 재고 상태 변화를 확인하세요"), unsafe_allow_html=True)

    # 초기값 설정
    if "inv_prev_sku" not in st.session_state or st.session_state.inv_prev_sku != selected_sku:
        st.session_state.inv_sim_qty = int(row["Quantity_On_Hand"])
        st.session_state.inv_sim_lead = int(row["Lead_Time_Days"])
        st.session_state.inv_sim_rp = int(row["Reorder_Point"])
        st.session_state.inv_prev_sku = selected_sku

    def _adj(key, delta, lo, hi):
        st.session_state[key] = max(lo, min(hi, st.session_state[key] + delta))

    sim_col1, sim_col2, sim_col3 = st.columns(3)
    with sim_col1:
        sim_qty = st.slider("현재 보유 수량", 0, 2000, key="inv_sim_qty",
                            help="창고에 남아 있는 제품 수량을 조정합니다")
        _m1, _p1 = st.columns(2)
        with _m1:
            st.button("−10", key="inv_qty_m", use_container_width=True,
                      on_click=_adj, args=("inv_sim_qty", -10, 0, 2000))
        with _p1:
            st.button("+10", key="inv_qty_p", use_container_width=True,
                      on_click=_adj, args=("inv_sim_qty", 10, 0, 2000))

    with sim_col2:
        sim_lead = st.slider("배송 소요일", 1, 30, key="inv_sim_lead",
                             help="발주 후 물건이 도착하기까지 걸리는 날수")
        _m2, _p2 = st.columns(2)
        with _m2:
            st.button("−1", key="inv_lead_m", use_container_width=True,
                      on_click=_adj, args=("inv_sim_lead", -1, 1, 30))
        with _p2:
            st.button("+1", key="inv_lead_p", use_container_width=True,
                      on_click=_adj, args=("inv_sim_lead", 1, 1, 30))

    with sim_col3:
        sim_rp = st.slider("자동 발주 기준선", 0, 1000, key="inv_sim_rp",
                           help="재고가 이 수량 아래로 떨어지면 자동으로 새 주문을 넣는 기준")
        _m3, _p3 = st.columns(2)
        with _m3:
            st.button("−10", key="inv_rp_m", use_container_width=True,
                      on_click=_adj, args=("inv_sim_rp", -10, 0, 1000))
        with _p3:
            st.button("+10", key="inv_rp_p", use_container_width=True,
                      on_click=_adj, args=("inv_sim_rp", 10, 0, 1000))

    # 시뮬레이션 실행
    sim_row = df[df["SKU_ID"] == selected_sku].copy()
    sim_row["Quantity_On_Hand"] = sim_qty
    sim_row["Lead_Time_Days"] = sim_lead
    sim_row["Reorder_Point"] = sim_rp
    # 파생 변수 재계산
    ads_val = sim_row["Avg_Daily_Sales"].values[0]
    if ads_val > 0:
        sim_row["Days_of_Inventory"] = sim_qty / ads_val
    sim_row["Stock_Gap"] = sim_rp - sim_qty
    sim_row["Available_Stock"] = sim_qty - sim_row["Quantity_Reserved"].values[0] - sim_row["Quantity_Committed"].values[0]

    sim_X = prepare_classification_features(sim_row, feat_info)
    sim_X_scaled = pd.DataFrame(scaler.transform(sim_X), columns=sim_X.columns, index=sim_X.index)
    sim_pred_encoded = model.predict(sim_X_scaled)
    sim_status = label_enc.inverse_transform(sim_pred_encoded)[0]

    sim_label, sim_color, sim_advice, _ = status_config.get(sim_status, ("알 수 없음", "#999", "", ""))

    # 변경 사항 표시
    changed = (sim_qty != int(row["Quantity_On_Hand"]) or
               sim_lead != int(row["Lead_Time_Days"]) or
               sim_rp != int(row["Reorder_Point"]))

    sim_r1, sim_r2 = st.columns([1, 2])
    with sim_r1:
        st.markdown(f"""
<div style="background:linear-gradient(135deg, {sim_color}15, {sim_color}05); border-left:4px solid {sim_color};
            padding:16px 20px; border-radius:8px; margin:8px 0;">
    <span style="font-size:16px; font-weight:700; color:{sim_color};">
        시뮬레이션 결과: {sim_label} ({sim_status})
    </span><br>
    <span style="color:#555; font-size:13px;">{sim_advice}</span>
</div>""", unsafe_allow_html=True)
        if changed and sim_status != status:
            st.warning(f"원래 상태 **{status}** → 시뮬레이션 상태 **{sim_status}**로 변경됨")
        elif changed:
            st.success("파라미터가 변경되었지만 분류 결과는 동일합니다.")

    with sim_r2:
        if hasattr(model, "predict_proba"):
            sim_proba = model.predict_proba(sim_X_scaled)[0]
            sim_class_names = label_enc.inverse_transform(range(len(label_enc.classes_)))
            sim_probs = dict(zip(sim_class_names, sim_proba))
            sim_bar_colors = [prob_colors.get(k, COLORS["accent_blue"]) for k in sim_probs.keys()]
            fig_sim = go.Figure(go.Bar(
                x=list(sim_probs.keys()), y=list(sim_probs.values()),
                marker_color=sim_bar_colors,
                text=[f"{v:.1%}" for v in sim_probs.values()],
                textposition="outside",
            ))
            fig_sim.update_layout(
                height=280, margin=dict(t=20, b=20),
                yaxis_title="확률", xaxis_title="재고 상태",
                yaxis_range=[0, 1.1],
                title_text="시뮬레이션 확률 분포",
            )
            st.plotly_chart(fig_sim, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# 알고리즘 인사이트 모드
# ══════════════════════════════════════════════════════════════
if is_advanced:
    st.markdown(section_anchor("sec-algo-tabs"), unsafe_allow_html=True)
    tab_names_adv = ["분류 결과 분석", "LightGBM 알고리즘", "SHAP 분석", "개별 제품 예측", "용어 사전"]
    active_tab = render_custom_tabs(st, tab_names_adv, "inv_adv_tab")
    _adv_toc_map = {
        0: [("sec-algo-tabs", "분류 결과 분석", "◈")],
        1: [("sec-algo-tabs", "LightGBM 알고리즘", "◉")],
        2: [("sec-algo-tabs", "SHAP 분석", "◎")],
        3: [("sec-algo-tabs", "개별 제품 예측", "◇")],
        4: [("sec-algo-tabs", "용어 사전", "▸")],
    }
    st.markdown(render_mini_toc(_adv_toc_map.get(active_tab, [])), unsafe_allow_html=True)

    # ── Tab 0: 분류 결과 분석 ──────────────────────────────
    if active_tab == 0:
        st.markdown(section_header("예측 정확도 표 (혼동 행렬)", "대각선 숫자가 클수록 정확"), unsafe_allow_html=True)
        with st.expander("혼동 행렬 읽는 법"):
            st.markdown("""
- **대각선 (좌상→우하)** 숫자가 크면 정확한 예측입니다.
- **대각선 바깥** 숫자는 오분류 — 예: 행 `Low Stock`, 열 `In Stock`이면 실제로는 부족인데 충분으로 잘못 예측한 경우입니다.
- 색이 진할수록 해당 건수가 많습니다.
""")
        classes = sorted(df["Inventory_Status"].unique())
        cm = confusion_matrix(df["Inventory_Status"], df["Status_Pred"], labels=classes)

        fig_cm = px.imshow(
            cm, x=classes, y=classes, text_auto=True, color_continuous_scale="Blues",
            labels={"x": "예측", "y": "실제", "color": "Count"},
        )
        fig_cm.update_layout(height=450, margin=dict(t=20, b=20))
        st.plotly_chart(fig_cm, use_container_width=True)

        # 실제 vs 예측 분포
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(section_header("실제 vs 예측 분포"), unsafe_allow_html=True)
            status_actual = df["Inventory_Status"].value_counts()
            status_pred = df["Status_Pred"].value_counts()
            compare = pd.DataFrame({"실제": status_actual, "예측": status_pred}).fillna(0).astype(int)
            st.dataframe(compare, use_container_width=True)

            fig1 = go.Figure()
            for col_name, clr in [("실제", COLORS["accent_blue"]), ("예측", COLORS["accent_red"])]:
                fig1.add_trace(go.Bar(x=compare.index, y=compare[col_name], name=col_name, marker_color=clr))
            fig1.update_layout(barmode="group", height=350, margin=dict(t=20, b=20))
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            st.markdown(section_header("카테고리별 재고 상태"), unsafe_allow_html=True)
            cat_status = df.groupby(["Category", "Status_Pred"]).size().reset_index(name="Count")
            fig2 = px.bar(cat_status, x="Category", y="Count", color="Status_Pred", barmode="stack",
                          color_discrete_sequence=px.colors.qualitative.Set2)
            fig2.update_layout(height=350, margin=dict(t=20, b=20))
            st.plotly_chart(fig2, use_container_width=True)

            abc_status = df.groupby(["ABC_Class", "Status_Pred"]).size().reset_index(name="Count")
            fig3 = px.bar(abc_status, x="ABC_Class", y="Count", color="Status_Pred", barmode="stack",
                          color_discrete_sequence=px.colors.qualitative.Set2)
            fig3.update_layout(height=300, margin=dict(t=20, b=20))
            st.plotly_chart(fig3, use_container_width=True)

        # 오분류 목록
        misclassified = df[df["Inventory_Status"] != df["Status_Pred"]]
        st.markdown(section_header(f"오분류 SKU ({len(misclassified)}건)"), unsafe_allow_html=True)
        if len(misclassified) > 0:
            st.dataframe(
                misclassified[[
                    "SKU_ID", "SKU_Name", "Category", "ABC_Class",
                    "Inventory_Status", "Status_Pred",
                    "Quantity_On_Hand", "Reorder_Point", "Days_of_Inventory",
                ]].sort_values("SKU_ID"),
                use_container_width=True, hide_index=True,
            )
        else:
            st.success("오분류 없음")

    # ── Tab 1: LightGBM 알고리즘 ──────────────────────────
    if active_tab == 1:
        render_algorithm_info(st, "LightGBM_Classification")

        st.divider()

        # 모델 성능 메트릭
        st.markdown(section_header("모델 성능 메트릭"), unsafe_allow_html=True)
        perf_c1, perf_c2 = st.columns(2)
        with perf_c1:
            st.markdown(f"**전체 정확도 (Accuracy):** `{accuracy:.4f}` ({accuracy:.1%})")
            st.caption("전체 예측 중 맞춘 비율입니다. 높을수록 모델이 정확합니다.")

        with perf_c2:
            st.markdown(f"**클래스 수:** {n_classes}개")
            st.caption("모델이 구분하는 재고 상태의 종류 수입니다.")

        # 클래스별 정밀도/재현율
        st.markdown("**클래스별 성능 (Precision / Recall / F1-Score)**")
        report = classification_report(
            df["Inventory_Status"], df["Status_Pred"],
            output_dict=True, zero_division=0,
        )
        report_rows = []
        for cls in sorted(label_enc.classes_):
            if cls in report:
                r = report[cls]
                report_rows.append({
                    "상태": cls,
                    "정밀도 (Precision)": f"{r['precision']:.4f}",
                    "재현율 (Recall)": f"{r['recall']:.4f}",
                    "F1-Score": f"{r['f1-score']:.4f}",
                    "샘플 수": int(r['support']),
                })
        if report_rows:
            st.dataframe(pd.DataFrame(report_rows), use_container_width=True, hide_index=True)

        st.divider()

        # 피처 중요도
        st.markdown(section_header("피처 중요도 분석"), unsafe_allow_html=True)
        st.caption("모델이 재고 상태를 분류할 때 가장 많이 참고한 데이터 항목 순위입니다. "
                   "상위 피처일수록 분류 결과에 더 큰 영향을 미칩니다.")
        render_feature_importance(st, model, X.columns.tolist(),
                                 title="LightGBM 재고 상태 분류 — 피처 중요도")

        # 주요 피처 해석
        with st.expander("주요 피처가 중요한 이유", expanded=False):
            st.markdown("""
- **Quantity_On_Hand (현재 보유 수량)**: 재고 상태를 직접적으로 결정하는 가장 핵심 지표입니다.
  수량이 0에 가까우면 품절, 재주문점 이하이면 부족으로 분류됩니다.
- **Days_of_Inventory (재고 소진 예상일)**: 현재 판매 속도로 재고가 며칠간 유지되는지를 나타내며,
  낮을수록 긴급한 상태입니다.
- **Reorder_Point (재주문점)**: 발주 기준선으로, 보유 수량과의 비교를 통해 부족 여부를 판단합니다.
- **Avg_Daily_Sales (일평균 판매량)**: 판매 속도가 빠른 제품은 재고 소진이 빠르므로
  더 자주 부족 상태에 놓일 수 있습니다.
- **Lead_Time_Days (배송 소요일)**: 배송이 오래 걸릴수록 미리 발주해야 하므로
  재고 부족 위험이 높아집니다.
""")

    # ── Tab 2: SHAP 분석 ──────────────────────────────────
    if active_tab == 2:
        st.markdown(section_header("SHAP 분석 (모델 예측 설명)"), unsafe_allow_html=True)
        st.caption("SHAP(SHapley Additive exPlanations)은 각 피처가 개별 예측에 얼마나 기여했는지를 "
                   "수학적으로 계산하는 설명 기법입니다.")
        render_shap_analysis(st, model, X_scaled, X.columns.tolist())

    # ── Tab 3: 개별 제품 예측 ─────────────────────────────
    if active_tab == 3:
        st.markdown(section_header("개별 제품 재고 상태 예측"), unsafe_allow_html=True)

        selected_sku_adv = st.selectbox(
            "제품 선택", df["SKU_ID"].tolist(), key="cls_sku",
            format_func=lambda x: f"{x} — {df[df['SKU_ID'] == x].iloc[0]['SKU_Name']}",
            help="재고 상태를 확인할 제품을 선택하세요",
        )
        row_adv = df[df["SKU_ID"] == selected_sku_adv].iloc[0]

        col_i1, col_i2, col_i3 = st.columns(3)
        col_i1.metric("제품명", row_adv["SKU_Name"])
        col_i2.metric("카테고리", f"{row_adv['Category']} ({row_adv['ABC_Class']})",
                      help="A=매출 상위 80%, B=중간 15%, C=하위 5%")
        col_i3.metric("창고", row_adv["Warehouse_Location"].split(" - ")[0])

        col_i4, col_i5, col_i6 = st.columns(3)
        col_i4.metric("현재 보유 수량", f"{row_adv['Quantity_On_Hand']}",
                      help="창고에 남아 있는 제품 수량")
        col_i5.metric("자동 발주 기준선", f"{row_adv['Reorder_Point']:.0f}",
                      help="재고가 이 수량 아래로 떨어지면 새 주문을 넣는 기준")
        col_i6.metric("재고 소진 예상일", f"{row_adv['Days_of_Inventory']:.1f}",
                      help="현재 판매 속도로 재고가 며칠 후 바닥나는지")

        st.divider()

        col_r1, col_r2 = st.columns([1, 2])
        with col_r1:
            actual = row_adv["Inventory_Status"]
            pred = row_adv["Status_Pred"]
            match = "일치" if actual == pred else "불일치"
            match_color = "#1565C0" if actual == pred else "#F44336"
            st.markdown(f"**실제 상태:** {actual}")
            st.markdown(f"**예측 상태:** {pred}")
            st.markdown(f'**판정:** <span style="color:{match_color};font-weight:700;">{match}</span>',
                        unsafe_allow_html=True)

        with col_r2:
            if hasattr(model, "predict_proba"):
                prob_cols = [c for c in df.columns if c.startswith("Prob_")]
                if prob_cols:
                    probs_adv = {c.replace("Prob_", ""): row_adv[c] for c in prob_cols}
                    fig_bar = px.bar(
                        x=list(probs_adv.keys()), y=list(probs_adv.values()),
                        labels={"x": "클래스", "y": "확률"},
                        color=list(probs_adv.keys()),
                        color_discrete_sequence=["#1565C0", "#42A5F5", "#FF9800", "#F44336", COLORS["accent_purple"]],
                    )
                    fig_bar.update_layout(height=300, margin=dict(t=20, b=20), showlegend=False)
                    st.plotly_chart(fig_bar, use_container_width=True)

    # ── Tab 4: 용어 사전 ──────────────────────────────────
    if active_tab == 4:
        st.markdown(section_header("용어 사전"), unsafe_allow_html=True)
        st.caption("재고 관리와 머신러닝에서 사용되는 주요 용어를 설명합니다.")
        render_glossary(st)

# ── 푸터 ──────────────────────────────────────────────────
st.markdown(footer_html(), unsafe_allow_html=True)

"""
E-Grocery WMS — Home (통합 소개 페이지)
"""
import streamlit as st
import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils.styles import (
    GLOBAL_CSS, COLORS, render_common_sidebar, get_icon_svg, footer_html,
)

st.set_page_config(
    page_title="E-Grocery WMS",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 글로벌 CSS 적용 ───────────────────────────────────────
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# ── 사이드바 (공통) ───────────────────────────────────────
render_common_sidebar(st, current_page="/")

# ── 메인 영역 ─────────────────────────────────────────────
st.markdown(
    '<div class="page-title">재고 최적화 대시보드</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="page-subtitle">ML 기반 식료품 유통 재고 관리 최적화 시스템</div>',
    unsafe_allow_html=True,
)

# ── 아이콘 준비 ────────────────────────────────────────────
ic_dash = get_icon_svg("nav_dashboard", size=20)
ic_expl = get_icon_svg("nav_explorer", size=20)
ic_waste = get_icon_svg("nav_waste", size=20)
ic_inv = get_icon_svg("nav_status", size=20)
ic_sales = get_icon_svg("nav_sales", size=20)
ic_reord = get_icon_svg("nav_reorder", size=20)
ic_target = get_icon_svg("accuracy", size=18)

st.markdown("---")

# ── 분석 모듈 + ML 모델 정확도 (2열) ──────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown(
        f"""
        <div style="background:white;border-radius:14px;padding:24px;box-shadow:0 2px 10px rgba(0,0,0,0.07);margin-bottom:16px;">
            <div style="font-size:16px;font-weight:700;color:#1a1a2e;margin-bottom:14px;">{ic_dash} 분석 모듈</div>
            <table style="width:100%;font-size:13px;border-collapse:collapse;">
                <tr style="border-bottom:1px solid #f0f0f0;">
                    <td style="padding:10px 4px;vertical-align:middle;">{ic_dash}</td>
                    <td style="padding:10px 4px;font-weight:600;color:#4CAF50;">대시보드</td>
                    <td style="padding:10px 4px;color:#6c757d;">핵심 지표 요약 및 전체 현황</td>
                </tr>
                <tr style="border-bottom:1px solid #f0f0f0;">
                    <td style="padding:10px 4px;vertical-align:middle;">{ic_expl}</td>
                    <td style="padding:10px 4px;font-weight:600;color:#2196F3;">데이터 탐색</td>
                    <td style="padding:10px 4px;color:#6c757d;">원본 데이터 검색 / 필터링</td>
                </tr>
                <tr style="border-bottom:1px solid #f0f0f0;">
                    <td style="padding:10px 4px;vertical-align:middle;">{ic_inv}</td>
                    <td style="padding:10px 4px;font-weight:600;color:#9C27B0;">재고 상태</td>
                    <td style="padding:10px 4px;color:#6c757d;">충분/부족/품절 자동 분류</td>
                </tr>
                <tr style="border-bottom:1px solid #f0f0f0;">
                    <td style="padding:10px 4px;vertical-align:middle;">{ic_sales}</td>
                    <td style="padding:10px 4px;font-weight:600;color:#FF9800;">판매량 예측</td>
                    <td style="padding:10px 4px;color:#6c757d;">하루 평균 판매량 예측</td>
                </tr>
                <tr style="border-bottom:1px solid #f0f0f0;">
                    <td style="padding:10px 4px;vertical-align:middle;">{ic_waste}</td>
                    <td style="padding:10px 4px;font-weight:600;color:#F44336;">폐기 위험</td>
                    <td style="padding:10px 4px;color:#6c757d;">유통기한 초과 위험 제품 탐지</td>
                </tr>
                <tr>
                    <td style="padding:10px 4px;vertical-align:middle;">{ic_reord}</td>
                    <td style="padding:10px 4px;font-weight:600;color:#00BCD4;">발주 전략</td>
                    <td style="padding:10px 4px;color:#6c757d;">제품 그룹 분류 + 최적 주문량</td>
                </tr>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        f"""
        <div style="background:white;border-radius:14px;padding:24px;box-shadow:0 2px 10px rgba(0,0,0,0.07);margin-bottom:16px;">
            <div style="font-size:16px;font-weight:700;color:#1a1a2e;margin-bottom:14px;">{ic_target} ML 모델 정확도</div>
            <table style="width:100%;font-size:13px;border-collapse:collapse;">
                <tr style="border-bottom:1px solid #f0f0f0;">
                    <td style="padding:10px 4px;font-weight:600;">재고 상태 분류</td>
                    <td style="padding:10px 4px;color:#6c757d;">LightGBM</td>
                    <td style="padding:10px 4px;text-align:right;"><span style="background:#4CAF50;color:white;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600;">정확도 98.8%</span></td>
                </tr>
                <tr style="border-bottom:1px solid #f0f0f0;">
                    <td style="padding:10px 4px;font-weight:600;">판매량 예측</td>
                    <td style="padding:10px 4px;color:#6c757d;">XGBoost</td>
                    <td style="padding:10px 4px;text-align:right;"><span style="background:#2196F3;color:white;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600;">정확도 94.8%</span></td>
                </tr>
                <tr style="border-bottom:1px solid #f0f0f0;">
                    <td style="padding:10px 4px;font-weight:600;">폐기 위험 탐지</td>
                    <td style="padding:10px 4px;color:#6c757d;">로지스틱 회귀</td>
                    <td style="padding:10px 4px;text-align:right;"><span style="background:#FF9800;color:white;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600;">정확도 98.8%</span></td>
                </tr>
                <tr style="border-bottom:1px solid #f0f0f0;">
                    <td style="padding:10px 4px;font-weight:600;">발주 전략</td>
                    <td style="padding:10px 4px;color:#6c757d;">XGBoost + K-Means + Sub-clustering</td>
                    <td style="padding:10px 4px;text-align:right;"><span style="background:#9C27B0;color:white;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600;">3-Tier 분류</span></td>
                </tr>
                <tr>
                    <td style="padding:10px 4px;font-weight:600;">DOI 예측 (Optuna)</td>
                    <td style="padding:10px 4px;color:#6c757d;">XGBoost + TPE 최적화</td>
                    <td style="padding:10px 4px;text-align:right;"><span style="background:#00BCD4;color:white;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600;">CV R² 0.885</span></td>
                </tr>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ── 페이지별 상세 소개 ──────────────────────────────────────
st.markdown("---")
st.markdown(
    '<div style="font-size:20px;font-weight:700;color:#1a1a2e;margin-bottom:16px;">📋 페이지별 기능 소개</div>',
    unsafe_allow_html=True,
)

pages_info = [
    {
        "icon": ic_dash, "title": "대시보드", "color": "#4CAF50",
        "desc": "전체 재고 현황을 한눈에 파악하는 핵심 요약 페이지",
        "sim": ["전체 제품 수, 재고 부족 위험, 폐기 위험 KPI 카드", "재고 상태 분포 파이 차트 / 카테고리별 재고량 바 차트",
                "ABC 등급별 재고 가치 분석"],
        "algo": ["K-Means 기반 제품 그룹 3D 시각화", "XGBoost 판매량 예측 시뮬레이터 (파라미터 조정)",
                 "폐기 위험 제품 목록 (확률 순 정렬)"],
    },
    {
        "icon": ic_expl, "title": "데이터 탐색", "color": "#2196F3",
        "desc": "원본 데이터를 자유롭게 필터링하고 통계적으로 분석하는 페이지",
        "sim": ["카테고리별 컬럼 선택 (수량/판매/기간/금액/비율/범주형)", "통계 분석 7개 지표 (평균, 중앙값, 표준편차 등)",
                "히스토그램 / 박스플롯 시각화", "카테고리별 비교 분석 / 산점도"],
        "algo": ["전체 기술 통계 분석 (describe)", "분포 & 상관관계 히트맵",
                 "6개 ML 알고리즘 소개 (LightGBM, XGBoost, K-Means 등)", "용어 사전 (23개 핵심 용어 검색)"],
    },
    {
        "icon": ic_inv, "title": "재고 상태 분류", "color": "#9C27B0",
        "desc": "ML 모델이 각 제품의 재고 상태를 자동 분류하는 페이지",
        "sim": ["제품 선택 → 실시간 ML 분류 결과 확인", "확률 분포 바 차트 (충분/부족/품절 확률)",
                "What-If 시뮬레이션 (수량, 리드타임, ROP 조정)"],
        "algo": ["혼동 행렬 + 분류 정확도 분석", "LightGBM 알고리즘 원리 해설 + 피처 중요도",
                 "SHAP 분석 (개별 예측 설명)", "용어 사전"],
    },
    {
        "icon": ic_sales, "title": "판매량 예측", "color": "#FF9800",
        "desc": "XGBoost 회귀 모델로 제품별 일평균 판매량을 예측하는 페이지",
        "sim": ["제품 선택 → 실제 vs 예측 판매량 비교", "파라미터 조정 시뮬레이션 (수량, ROP, 리드타임)",
                "실제/원래예측/시뮬레이션 3종 비교 바 차트"],
        "algo": ["모델 성능 지표 (R², RMSE, MAE)", "XGBoost 알고리즘 원리 + 피처 중요도 Top 15",
                 "SHAP 분석", "판매량 구간별 예측 성능 분석", "용어 사전"],
    },
    {
        "icon": ic_waste, "title": "폐기 위험 탐지", "color": "#F44336",
        "desc": "유통기한 초과로 폐기될 위험이 있는 제품을 사전 탐지하는 페이지",
        "sim": ["신선식품 / 비신선식품 카테고리 필터", "위험 제품 테이블 (색상 그라디언트)",
                "7일/30일 이내 긴급 알림", "개별 제품 What-If 시뮬레이터 (게이지 차트)"],
        "algo": ["모델 성능 (정확도, 정밀도, 재현율, F1, AUC-ROC)", "위험 요인 분석 + 피처 중요도",
                 "SHAP 분석", "신선식품 카테고리별 위험 비교", "용어 사전"],
    },
    {
        "icon": ic_reord, "title": "발주 전략", "color": "#00BCD4",
        "desc": "최적 발주 시점과 주문량을 결정하는 전략 수립 페이지",
        "sim": ["제품별 재고 현황 분석 + 발주 긴급도 평가", "파라미터 시뮬레이션 (수량, 리드타임, ROP)",
                "재고 소진 타임라인 시각화"],
        "algo": ["발주 긴급도 분류", "K-Means / DBSCAN / GMM 클러스터링 비교",
                 "Safety Stock & EOQ 분석", "t-SNE / UMAP 차원축소 시각화",
                 "AI 모델 분석 + 용어 사전"],
    },
]

for i in range(0, len(pages_info), 2):
    cols = st.columns(2)
    for j, col in enumerate(cols):
        if i + j < len(pages_info):
            p = pages_info[i + j]
            sim_items = "".join(f'<li style="margin-bottom:4px;">{s}</li>' for s in p["sim"])
            algo_items = "".join(f'<li style="margin-bottom:4px;">{s}</li>' for s in p["algo"])
            with col:
                st.markdown(
                    f"""
                    <div style="background:white;border-radius:14px;padding:20px;box-shadow:0 2px 10px rgba(0,0,0,0.07);margin-bottom:16px;min-height:320px;">
                        <div style="font-size:15px;font-weight:700;color:{p['color']};margin-bottom:8px;">
                            {p['icon']} {p['title']}
                        </div>
                        <div style="font-size:13px;color:#6c757d;margin-bottom:12px;">{p['desc']}</div>
                        <div style="display:flex;gap:12px;">
                            <div style="flex:1;">
                                <div style="font-size:11px;font-weight:700;color:#4CAF50;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;">
                                    🖥 WMS 시뮬레이터
                                </div>
                                <ul style="font-size:11.5px;color:#555;padding-left:16px;margin:0;line-height:1.7;">
                                    {sim_items}
                                </ul>
                            </div>
                            <div style="flex:1;">
                                <div style="font-size:11px;font-weight:700;color:#2196F3;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;">
                                    🔬 알고리즘 인사이트
                                </div>
                                <ul style="font-size:11.5px;color:#555;padding-left:16px;margin:0;line-height:1.7;">
                                    {algo_items}
                                </ul>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

# ── 모드 안내 ──────────────────────────────────────────────
st.markdown(
    """
    <div style="background:linear-gradient(135deg,#e8f5e9,#e3f2fd);border-radius:14px;padding:20px;margin-top:8px;margin-bottom:16px;">
        <div style="font-size:14px;font-weight:700;color:#1a1a2e;margin-bottom:8px;">💡 모드 전환 안내</div>
        <div style="font-size:13px;color:#555;line-height:1.8;">
            각 분석 페이지에서 상단의 <b style="color:#4CAF50;">WMS 시뮬레이터</b> / <b style="color:#2196F3;">알고리즘 인사이트</b> 버튼으로 모드를 전환할 수 있습니다.<br>
            · <b style="color:#4CAF50;">WMS 시뮬레이터</b> — 제품을 선택하고 파라미터를 조정하며 실시간으로 결과를 확인하는 실무 중심 모드<br>
            · <b style="color:#2196F3;">알고리즘 인사이트</b> — ML 모델의 원리, 성능 지표, SHAP 분석, 용어 해설을 제공하는 학습 중심 모드
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── 푸터 ──────────────────────────────────────────────────
st.markdown(footer_html(), unsafe_allow_html=True)

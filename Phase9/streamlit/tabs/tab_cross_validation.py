"""도메인 일반화 분석 탭 — Severstal → NEU-DET 도메인 전이 + 합성 변형 강건성 검증."""

import streamlit as st
import numpy as np
import os
import sys
import json
import matplotlib.pyplot as plt

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

plt.rcParams["font.family"] = "AppleGothic"
plt.rcParams["axes.unicode_minus"] = False


def _badge(letter, color_class="ib-blue"):
    return f'<span class="icon-badge {color_class}">{letter}</span>'


# 도메인 일반화 검증 결과 데이터
CROSS_VALIDATION_RESULTS = {
    "NEU → ML (LightGBM)": {
        "recall": 0.527,
        "desc": "Severstal ML 모델에 NEU 투입",
        "detail": "1,800장 중 949장만 비정상으로 탐지",
    },
    "NEU → DL (ResNet-18 FT)": {
        "recall": 0.113,
        "desc": "Severstal DL 모델에 NEU 투입",
        "detail": "1,800장 중 203장만 비정상으로 탐지",
    },
    "NEU 독립 학습 (ResNet-18)": {
        "recall": 1.000,
        "desc": "NEU 자체 6종 분류 학습",
        "detail": "동일 아키텍처로 NEU에서 학습 시 100% 달성",
    },
}

# NEU 6종 클래스별 도메인 전이 탐지율 (ML)
NEU_CLASS_RECALLS_ML = {
    "Crazing (균열)": 0.807,
    "Inclusion (개재물)": 0.033,
    "Patches (패치)": 0.920,
    "Pitted Surface (구멍)": 0.157,
    "Rolled-in Scale (압연)": 0.453,
    "Scratches (스크래치)": 0.793,
}

# NEU 6종 클래스별 도메인 전이 탐지율 (DL)
NEU_CLASS_RECALLS_DL = {
    "Crazing (균열)": 0.000,
    "Inclusion (개재물)": 0.043,
    "Patches (패치)": 0.000,
    "Pitted Surface (구멍)": 0.007,
    "Rolled-in Scale (압연)": 0.000,
    "Scratches (스크래치)": 0.630,
}


def render_tab_cross_validation():
    """도메인 일반화 분석 탭 렌더링."""
    B = _badge

    # ── 개념 소개 ──
    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("DG", "ib-red")} 도메인 일반화 분석: Severstal → NEU-DET</div>',
                unsafe_allow_html=True)
    st.markdown("""<div class="info-box">
        <strong>왜 이 분석이 중요한가?</strong><br>
        AI 모델이 학습한 데이터에서만 잘 작동하면 실제 현장에서는 무용지물입니다.
        이 분석은 Severstal로 학습한 모델이 <strong>전혀 다른 환경(NEU-DET)</strong>의 결함도
        탐지할 수 있는지 — 즉 <strong>일반화 능력(Generalization)</strong>을 검증합니다.<br><br>
        <strong>핵심 질문</strong>:<br>
        • 학습 데이터에 없던 결함 유형도 탐지할 수 있는가?<br>
        • ML과 DL 중 어떤 접근이 새로운 환경에 더 강건한가?<br>
        • 실제 공장 배포 시 재학습 없이 사용 가능한가?<br><br>
        <strong>NEU-DET</strong>: 1,440장 (6종 결함 x 240장, train set), 100% 결함 이미지<br>
        → 모두 "비정상"으로 탐지되어야 Recall = 100%
    </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── 도메인 일반화 핵심 결과 ──
    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("RS", "ib-blue")} 도메인 일반화 핵심 결과</div>',
                unsafe_allow_html=True)

    # KPI 카드
    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown(f"""
        <div class="kpi-card">
            <p class="kpi-label">NEU → ML Recall</p>
            <p class="kpi-value" style="color:#ea580c;">52.7%</p>
            <p style="color:#94a3b8; font-size:0.75rem; margin:0;">LightGBM (Severstal 학습)</p>
        </div>""", unsafe_allow_html=True)
    with k2:
        st.markdown(f"""
        <div class="kpi-card">
            <p class="kpi-label">NEU → DL Recall</p>
            <p class="kpi-value" style="color:#dc2626;">14.4%</p>
            <p style="color:#94a3b8; font-size:0.75rem; margin:0;">ResNet-18 FT (Severstal 학습)</p>
        </div>""", unsafe_allow_html=True)
    with k3:
        st.markdown(f"""
        <div class="kpi-card">
            <p class="kpi-label">NEU 독립 학습</p>
            <p class="kpi-value" style="color:#059669;">100%</p>
            <p style="color:#94a3b8; font-size:0.75rem; margin:0;">동일 ResNet-18 (NEU 학습)</p>
        </div>""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Recall 비교 차트 ──
    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("CH", "ib-purple")} 도메인 전이 Recall 비교</div>',
                unsafe_allow_html=True)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # 전체 Recall 비교
    scenarios = list(CROSS_VALIDATION_RESULTS.keys())
    recalls = [CROSS_VALIDATION_RESULTS[s]["recall"] for s in scenarios]
    colors = ["#ea580c", "#dc2626", "#059669"]

    bars = axes[0].bar(range(len(scenarios)), recalls, color=colors, width=0.5)
    axes[0].set_xticks(range(len(scenarios)))
    axes[0].set_xticklabels([s.split("(")[0].strip() for s in scenarios],
                            fontsize=9, rotation=15, ha="right")
    axes[0].set_ylabel("Recall", fontsize=11)
    axes[0].set_title("도메인 전이 Recall", fontsize=13, fontweight="bold")
    axes[0].set_ylim(0, 1.15)
    axes[0].axhline(y=1.0, color="gray", linestyle="--", alpha=0.3)
    axes[0].axhline(y=0.5, color="red", linestyle="--", alpha=0.2, label="50% 기준")
    axes[0].grid(True, alpha=0.3, axis="y")
    axes[0].legend(fontsize=8)
    for bar, val in zip(bars, recalls):
        axes[0].text(bar.get_x() + bar.get_width() / 2., bar.get_height() + 0.02,
                     f"{val:.1%}", ha="center", va="bottom", fontsize=11, fontweight="bold")

    # 성능 변화 화살표 (Severstal 내부 vs 교차)
    internal_accs = [0.7200, 0.9150, 1.000]
    cross_recalls = [0.527, 0.113, 1.000]
    labels_short = ["ML\n(LightGBM)", "DL\n(ResNet-18)", "NEU 독립"]
    x_pos = np.arange(len(labels_short))

    axes[1].bar(x_pos - 0.15, internal_accs, 0.3, label="Severstal 내부 Acc", color="#2563eb", alpha=0.8)
    axes[1].bar(x_pos + 0.15, cross_recalls, 0.3, label="NEU 교차 Recall", color="#dc2626", alpha=0.8)
    axes[1].set_xticks(x_pos)
    axes[1].set_xticklabels(labels_short, fontsize=10)
    axes[1].set_ylabel("성능", fontsize=11)
    axes[1].set_title("Severstal 내부 성능 vs NEU 교차 성능", fontsize=13, fontweight="bold")
    axes[1].set_ylim(0, 1.15)
    axes[1].legend(fontsize=9)
    axes[1].grid(True, alpha=0.3, axis="y")

    # 드롭율 표시
    for i, (ia, cr) in enumerate(zip(internal_accs, cross_recalls)):
        if ia > cr:
            drop = ia - cr
            axes[1].annotate(
                f"▼{drop:.0%}", xy=(i + 0.15, cr + 0.02),
                fontsize=9, color="#dc2626", fontweight="bold", ha="center",
            )

    fig.patch.set_facecolor("#fff")
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── 클래스별 탐지율 ──
    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("CL", "ib-orange")} NEU 클래스별 비정상 탐지율</div>',
                unsafe_allow_html=True)

    st.markdown("""<div class="info-box">
        NEU 6종 결함 각각에 대해 Severstal 학습 모델이 "비정상"으로 탐지한 비율입니다.<br>
        ML은 특징 기반이라 일부 감지 가능하지만, DL은 Severstal 도메인에 과적합되어 거의 탐지 불가.
    </div>""", unsafe_allow_html=True)

    fig2, axes2 = plt.subplots(1, 2, figsize=(14, 5))

    class_names = list(NEU_CLASS_RECALLS_ML.keys())
    ml_recalls = list(NEU_CLASS_RECALLS_ML.values())
    dl_recalls = list(NEU_CLASS_RECALLS_DL.values())

    # ML 클래스별
    colors_ml = ["#059669" if r >= 0.5 else "#ea580c" if r >= 0.3 else "#dc2626" for r in ml_recalls]
    axes2[0].barh(class_names, ml_recalls, color=colors_ml, height=0.55)
    axes2[0].set_xlim(0, 1.0)
    axes2[0].set_xlabel("Recall", fontsize=11)
    axes2[0].set_title("ML (LightGBM) — 클래스별 탐지율", fontsize=12, fontweight="bold")
    axes2[0].axvline(x=0.5, color="red", linestyle="--", alpha=0.3)
    axes2[0].grid(True, alpha=0.3, axis="x")
    for i, v in enumerate(ml_recalls):
        axes2[0].text(v + 0.02, i, f"{v:.0%}", va="center", fontsize=9)

    # DL 클래스별
    colors_dl = ["#dc2626"] * len(dl_recalls)  # 모두 매우 낮음
    axes2[1].barh(class_names, dl_recalls, color=colors_dl, height=0.55)
    axes2[1].set_xlim(0, 1.0)
    axes2[1].set_xlabel("Recall", fontsize=11)
    axes2[1].set_title("DL (ResNet-18 FT) — 클래스별 탐지율", fontsize=12, fontweight="bold")
    axes2[1].axvline(x=0.5, color="red", linestyle="--", alpha=0.3)
    axes2[1].grid(True, alpha=0.3, axis="x")
    for i, v in enumerate(dl_recalls):
        axes2[1].text(v + 0.02, i, f"{v:.0%}", va="center", fontsize=9)

    fig2.patch.set_facecolor("#fff")
    plt.tight_layout()
    st.pyplot(fig2)
    plt.close(fig2)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Domain Gap 분석 ──
    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("DG", "ib-red")} Domain Gap 분석</div>',
                unsafe_allow_html=True)

    st.markdown("""
| 차원 | Severstal | NEU-DET | Gap |
|------|-----------|---------|-----|
| **이미지 크기** | 256×1600 (패치 256×256) | 200×200 | 크기·비율 상이 |
| **촬영 환경** | 연속 주조 라인 카메라 | 실험실 통제 환경 | 조명·해상도 상이 |
| **결함 유형** | 4종 (PS/LS/SS/RD) | 6종 (Cr/In/Pa/PS/RS/Sc) | 유형 불일치 |
| **결함 표현** | 미세·연속적 패턴 | 뚜렷·국소적 패턴 | 시각적 특성 상이 |
| **배경 텍스처** | 강철 연속 주조 표면 | 열연 강판 표면 | 텍스처 상이 |
    """)

    st.markdown("""<div class="info-box">
        <strong>핵심 발견</strong>:<br><br>
        1. <strong>DL이 ML보다 도메인 전이에서 더 취약</strong> (14.4% vs 52.7%)<br>
           → DL은 Severstal 고유 텍스처에 과적합, ML은 범용 특징(HOG/LBP)으로 일부 일반화<br><br>
        2. <strong>동일 아키텍처(ResNet-18)도 데이터에 따라 성능 극변</strong><br>
           → Severstal 90.87%, NEU 교차 14.4%, NEU 독립 100%<br><br>
        3. <strong>Domain Adaptation 필수</strong><br>
           → 실제 제조 현장에서는 각 공정·장비에 맞춘 재학습이 반드시 필요
    </div>""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── 시사점 정리 ──
    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("IN", "ib-teal")} 도메인 일반화 시사점</div>',
                unsafe_allow_html=True)

    st.markdown("""
    #### 학술적 시사점

    1. **전이 학습의 한계**: ImageNet → Severstal 전이는 성공(90.87%)했지만,
       Severstal → NEU 전이는 실패(14.4%). **도메인 간 전이와 태스크 간 전이는 다름**.

    2. **특징 공학의 가치**: 전통 ML의 HOG/LBP 특징이 도메인 변화에 더 강건함(52.7%).
       범용 특징은 특정 도메인에 과적합되지 않는 장점.

    3. **데이터 중심 AI**: 모델 아키텍처보다 **학습 데이터의 품질과 대표성**이 더 중요.
       같은 ResNet-18도 데이터에 따라 14.4%~100%의 성능 차이.

    #### 실무적 시사점

    1. **신규 공정 도입 시**: 기존 모델 재사용 불가 → **현장 데이터로 Fine-tune 필수**
    2. **품질 관리 시스템**: 도메인 일반화 검증을 **모델 배포 전 필수 단계**로 포함
    3. **하이브리드 전략**: 1차 필터는 범용 ML → 2차 정밀 분류는 도메인 특화 DL
    """)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── 합성 변형 강건성 테스트 (NB11b) ──
    fig_dir = os.path.join(PROJECT_ROOT, "outputs", "figures", "severstal")
    _render_robustness_section(B, fig_dir)

    # ── NB11 실험 결과 갤러리 ──
    if os.path.isdir(fig_dir):
        with st.expander("NB11 실험 결과 - 도메인 일반화 분석", expanded=False):
            nb_figs = {
                "11_cross_ml_recall.png": "ML (LightGBM) 도메인 전이 클래스별 Recall",
                "11_cross_dl_recall.png": "DL (ResNet-18) 도메인 전이 클래스별 Recall",
                "11_neu_6class_cm.png": "NEU 독립 학습 6종 분류 혼동 행렬",
            }
            for fname, caption in nb_figs.items():
                fpath = os.path.join(fig_dir, fname)
                if os.path.exists(fpath):
                    st.image(fpath, caption=caption, use_container_width=True)

        with st.expander("NB11b 실험 결과 - 합성 변형 강건성 테스트", expanded=False):
            nb11b_figs = {
                "11b_transform_samples.png": "7가지 합성 변형 예시",
                "11b_robustness_comparison.png": "ML vs DL 강건성 비교 (변형별 Recall)",
                "11b_robustness_heatmap.png": "강건성 히트맵",
            }
            for fname, caption in nb11b_figs.items():
                fpath = os.path.join(fig_dir, fname)
                if os.path.exists(fpath):
                    st.image(fpath, caption=caption, use_container_width=True)

    # ── KPI 요약 ──
    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("KP", "ib-blue")} 도메인 일반화 핵심 수치</div>',
                unsafe_allow_html=True)

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown('<div class="kpi-card"><p class="kpi-label">Severstal→NEU 성능 하락</p>'
                    '<p class="kpi-value" style="color:#dc2626;">-76.47%p</p></div>',
                    unsafe_allow_html=True)
    with k2:
        st.markdown('<div class="kpi-card"><p class="kpi-label">ML 교차 Recall</p>'
                    '<p class="kpi-value" style="color:#ea580c;">52.7%</p></div>',
                    unsafe_allow_html=True)
    with k3:
        st.markdown('<div class="kpi-card"><p class="kpi-label">DL 교차 Recall</p>'
                    '<p class="kpi-value" style="color:#dc2626;">14.4%</p></div>',
                    unsafe_allow_html=True)
    with k4:
        st.markdown('<div class="kpi-card"><p class="kpi-label">NEU 독립 Acc</p>'
                    '<p class="kpi-value" style="color:#059669;">100%</p></div>',
                    unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


def _render_robustness_section(B, fig_dir):
    """NB11b 합성 변형 강건성 테스트 결과 렌더링."""

    # 결과 JSON 로드
    results_path = os.path.join(PROJECT_ROOT, "outputs", "11b_robustness_results.json")
    if not os.path.exists(results_path):
        st.info("강건성 테스트 결과가 없습니다. notebooks/11b_robustness_test.ipynb를 실행하세요.")
        return

    with open(results_path, 'r') as f:
        results = json.load(f)

    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("RB", "ib-purple")} 합성 변형 강건성 테스트 (NB11b)</div>',
                unsafe_allow_html=True)

    st.markdown("""<div class="info-box">
        <strong>도메인 전이(NB11)와 다른 관점의 검증</strong><br>
        NB11은 "다른 도메인(NEU-DET)의 결함도 감지하는가?"를 테스트했다면,<br>
        NB11b는 <strong>"같은 결함을 다른 촬영 조건에서도 탐지하는가?"</strong>를 테스트합니다.<br><br>
        • 밝기 변화 (±30%) — 조명이 밝거나 어두운 환경<br>
        • 노이즈 (σ=15) — 센서 노이즈<br>
        • 블러 (5×5) — 카메라 초점 이탈<br>
        • 대비 변화 (×1.5, ×0.6) — 고/저대비 촬영<br>
        • 해상도 열화 (2× 축소→재확대) — 저해상도 카메라
    </div>""", unsafe_allow_html=True)

    # KPI 카드
    k1, k2, k3, k4 = st.columns(4)
    ml_score = results['ml_robustness_score']
    dl_score = results['dl_robustness_score']
    ml_worst = results['ml_worst']
    dl_worst = results['dl_worst']

    with k1:
        color = "#059669" if ml_score >= 0.9 else "#ea580c" if ml_score >= 0.8 else "#dc2626"
        st.markdown(f'<div class="kpi-card"><p class="kpi-label">ML 강건성 점수</p>'
                    f'<p class="kpi-value" style="color:{color};">{ml_score:.1%}</p>'
                    f'<p style="color:#94a3b8;font-size:0.75rem;margin:0;">변형 평균 / 기준선</p></div>',
                    unsafe_allow_html=True)
    with k2:
        color = "#059669" if dl_score >= 0.9 else "#ea580c" if dl_score >= 0.8 else "#dc2626"
        st.markdown(f'<div class="kpi-card"><p class="kpi-label">DL 강건성 점수</p>'
                    f'<p class="kpi-value" style="color:{color};">{dl_score:.1%}</p>'
                    f'<p style="color:#94a3b8;font-size:0.75rem;margin:0;">변형 평균 / 기준선</p></div>',
                    unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="kpi-card"><p class="kpi-label">ML 최저 Recall</p>'
                    f'<p class="kpi-value" style="color:#dc2626;">{ml_worst:.1%}</p>'
                    f'<p style="color:#94a3b8;font-size:0.75rem;margin:0;">가장 취약한 변형</p></div>',
                    unsafe_allow_html=True)
    with k4:
        st.markdown(f'<div class="kpi-card"><p class="kpi-label">DL 최저 Recall</p>'
                    f'<p class="kpi-value" style="color:#dc2626;">{dl_worst:.1%}</p>'
                    f'<p style="color:#94a3b8;font-size:0.75rem;margin:0;">가장 취약한 변형</p></div>',
                    unsafe_allow_html=True)

    # 변형별 비교 테이블
    st.markdown("#### 변형별 Recall 비교")
    ml_res = results['ml_results']
    dl_res = results['dl_results']
    ml_base = results['ml_baseline']
    dl_base = results['dl_baseline']

    table_md = "| 변형 조건 | ML Recall | ML Δ | DL Recall | DL Δ |\n"
    table_md += "|----------|----------|------|----------|------|\n"
    for name in ml_res.keys():
        ml_r = ml_res[name]
        dl_r = dl_res[name]
        if name == '원본 (기준)':
            ml_d, dl_d = '-', '-'
        else:
            ml_d = f'{ml_r - ml_base:+.1%}p'
            dl_d = f'{dl_r - dl_base:+.1%}p'
        table_md += f"| {name} | {ml_r:.1%} | {ml_d} | {dl_r:.1%} | {dl_d} |\n"
    st.markdown(table_md)

    # 비교 차트 이미지
    comparison_path = os.path.join(fig_dir, "11b_robustness_comparison.png")
    if os.path.exists(comparison_path):
        st.image(comparison_path, caption="ML vs DL 변형별 강건성 비교", use_container_width=True)

    # 핵심 인사이트
    st.markdown(f"""<div class="info-box">
        <strong>강건성 테스트 핵심 발견</strong>:<br><br>
        1. <strong>DL이 원본에서는 압도적</strong> (기준: DL {dl_base:.1%} vs ML {ml_base:.1%})<br>
           → 그러나 노이즈/블러/해상도 열화에서 DL도 급격히 하락 (최저 {dl_worst:.1%})<br><br>
        2. <strong>ML이 상대적으로 안정적</strong> (강건성: ML {ml_score:.1%} vs DL {dl_score:.1%})<br>
           → 수작업 특징(HOG/LBP)은 픽셀 수준 변형에 덜 민감<br><br>
        3. <strong>NB11과 일관된 패턴</strong>: ML이 환경 변화에 더 안정적<br>
           → 도메인 전이(NB11)에서도 ML 51.6% vs DL 14.4%<br><br>
        4. <strong>가장 취약한 변형: 블러 + 해상도 열화</strong><br>
           → 고주파 텍스처 정보 소실 시 두 모델 모두 큰 성능 하락
    </div>""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

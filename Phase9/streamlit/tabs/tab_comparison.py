"""Phase 1~3 통합 비교 탭 — Severstal 2-Stage + 도메인 일반화 종합 분석."""

import streamlit as st
import numpy as np
import os
import sys
import matplotlib.pyplot as plt

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

plt.rcParams["font.family"] = "AppleGothic"
plt.rcParams["axes.unicode_minus"] = False


def _badge(letter, color_class="ib-blue"):
    return f'<span class="icon-badge {color_class}">{letter}</span>'


def render_tab_comparison():
    """Phase 1~3 통합 비교 + 도메인 일반화 종합 탭."""
    B = _badge

    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("VS","ib-red")} Severstal 2-Stage 파이프라인 종합 비교</div>',
                unsafe_allow_html=True)

    st.markdown("""<div class="info-box">
        <strong>Stage 1</strong> (정상/비정상 이진 분류) + <strong>Stage 2</strong> (4종 결함 세부 분류)
        파이프라인의 전 단계를 ML · DL · 이상 탐지 관점에서 종합 비교합니다.<br><br>
        추가로 <strong>도메인 일반화 검증</strong>(Severstal → NEU-DET) 결과를 포함하여
        모델의 일반화 능력까지 평가합니다.
    </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Stage 1 성능 비교 ──
    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("S1","ib-blue")} Stage 1: 이진 분류 성능 비교</div>',
                unsafe_allow_html=True)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # ML vs DL 정확도
    s1_models = ["KNN", "MLP", "SVM_RBF", "XGBoost", "RF", "LightGBM", "VotingEnsemble",
                 "ResNet-18 FE", "ResNet-18 FT"]
    s1_accs = [0.5550, 0.6500, 0.6500, 0.6950, 0.7200, 0.7200, 0.7300,
               0.8988, 0.9087]
    s1_colors = (["#94a3b8"] * 7) + ["#2563eb", "#059669"]

    axes[0].barh(s1_models, s1_accs, color=s1_colors, height=0.55)
    axes[0].set_xlim(0.45, 1.0)
    axes[0].set_xlabel("Accuracy", fontsize=11)
    axes[0].set_title("Stage 1 이진 분류 — 전 모델 비교", fontsize=13, fontweight="bold")
    axes[0].axvline(x=0.9, color="#dc2626", linestyle="--", alpha=0.4)
    axes[0].grid(True, alpha=0.3, axis="x")
    for i, v in enumerate(s1_accs):
        axes[0].text(v + 0.005, i, f"{v:.2%}", va="center", fontsize=8, fontweight="bold")

    # Stage 2 ML vs DL
    s2_models = ["KNN", "MLP", "SVM_RBF", "RF", "Voting", "XGBoost", "LightGBM",
                 "ResNet-18 FE", "ResNet-18 FT"]
    s2_accs = [0.5337, 0.6114, 0.6891, 0.7098, 0.7565, 0.7772, 0.7772,
               0.8705, 0.8601]
    s2_colors = (["#94a3b8"] * 7) + ["#2563eb", "#059669"]

    axes[1].barh(s2_models, s2_accs, color=s2_colors, height=0.55)
    axes[1].set_xlim(0.45, 0.95)
    axes[1].set_xlabel("Accuracy", fontsize=11)
    axes[1].set_title("Stage 2 결함 분류 — 전 모델 비교", fontsize=13, fontweight="bold")
    axes[1].axvline(x=0.8, color="#dc2626", linestyle="--", alpha=0.4)
    axes[1].grid(True, alpha=0.3, axis="x")
    for i, v in enumerate(s2_accs):
        axes[1].text(v + 0.005, i, f"{v:.2%}", va="center", fontsize=8, fontweight="bold")

    fig.patch.set_facecolor("#fff")
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── 접근법별 상세 비교표 ──
    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("TB","ib-purple")} 접근법 상세 비교</div>',
                unsafe_allow_html=True)

    st.markdown("""
| 항목 | 전통 ML | 딥러닝 (DL) | 이상 탐지 |
|------|---------|------------|----------|
| **학습 방식** | Supervised (HOG+LBP→ML) | Supervised (CNN 자동 특징) | **Unsupervised** (정상만) |
| **Stage 1 최고** | VotingEnsemble 73.00% | **ResNet-18 FT 90.87%** | AE (Recall 기반) |
| **Stage 2 최고** | LightGBM 77.72% | **ResNet-18 FT 86.01%** | — |
| **도메인 전이** | Recall 52.7% | Recall 14.4% | — |
| **추론 시간** | ~15ms | ~50ms | ~100ms |
| **모델 크기** | <5MB | ~43MB | ~1.6MB |
| **새 결함 대응** | 불가능 | 불가능 | **가능** |
| **해석 가능성** | 높음 (HOG/LBP) | 중간 (Grad-CAM) | 높음 (히트맵) |
| **데이터 효율성** | 중간 | 낮음 (대량 필요) | **높음** (정상만) |
    """)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── 레이더 차트 ──
    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("RD","ib-green")} 다차원 비교 레이더 차트</div>',
                unsafe_allow_html=True)
    st.markdown("""<div class="info-box">
        6가지 핵심 차원에서 각 접근법의 상대적 강점을 비교합니다 (5점 만점).
    </div>""", unsafe_allow_html=True)

    categories = ["정확도", "추론 속도", "해석 가능성", "데이터 효율성", "범용성", "도메인 일반화"]
    ml_scores = [3.5, 5.0, 4.5, 3.0, 3.5, 3.0]
    dl_scores = [5.0, 3.5, 3.0, 2.0, 2.0, 1.0]
    ad_scores = [3.0, 2.5, 4.0, 5.0, 4.5, 3.5]

    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    angles += angles[:1]

    for scores, label, color, alpha in [
        (ml_scores, "전통 ML", "#2563eb", 0.15),
        (dl_scores, "딥러닝", "#7c3aed", 0.15),
        (ad_scores, "이상 탐지", "#ea580c", 0.15),
    ]:
        values = scores + scores[:1]
        ax.plot(angles, values, "o-", linewidth=2, color=color, label=label)
        ax.fill(angles, values, alpha=alpha, color=color)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=11)
    ax.set_ylim(0, 5.5)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_yticklabels(["1", "2", "3", "4", "5"], fontsize=9, color="#94a3b8")
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), fontsize=11)
    ax.set_facecolor("#f8fafc")
    fig.patch.set_facecolor("#fff")
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── 도메인 일반화 검증 요약 ──
    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("DG","ib-red")} 도메인 일반화 핵심 결과</div>',
                unsafe_allow_html=True)

    fig2, ax2 = plt.subplots(figsize=(10, 5))

    x = np.arange(3)
    internal = [0.7300, 0.9087, 1.000]
    cross = [0.527, 0.144, 1.000]
    labels = ["ML (LightGBM)", "DL (ResNet-18 FT)", "NEU 독립 학습"]

    bars1 = ax2.bar(x - 0.17, internal, 0.3, label="Severstal 내부 성능", color="#2563eb", alpha=0.85)
    bars2 = ax2.bar(x + 0.17, cross, 0.3, label="NEU 교차 Recall", color="#dc2626", alpha=0.85)
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, fontsize=11)
    ax2.set_ylabel("성능", fontsize=12)
    ax2.set_title("Severstal 내부 성능 vs NEU 도메인 전이 성능", fontsize=14, fontweight="bold")
    ax2.set_ylim(0, 1.15)
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3, axis="y")

    for bar, val in zip(bars1, internal):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                 f"{val:.1%}", ha="center", fontsize=9, fontweight="bold", color="#2563eb")
    for bar, val in zip(bars2, cross):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                 f"{val:.1%}", ha="center", fontsize=9, fontweight="bold", color="#dc2626")

    fig2.patch.set_facecolor("#fff")
    plt.tight_layout()
    st.pyplot(fig2)
    plt.close(fig2)

    st.markdown("""<div class="info-box">
        <strong>핵심 발견</strong>: DL은 도메인 내 성능(90.87%)은 우수하지만,
        다른 도메인(NEU)에서 14.4%로 급락. ML은 52.7%로 상대적으로 강건.<br>
        → <strong>도메인 적응(Domain Adaptation)</strong> 없이는 범용 모델 불가능.
    </div>""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── 2단계 하이브리드 파이프라인 ──
    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("2S","ib-teal")} 제안: 2단계 하이브리드 검수 시스템</div>',
                unsafe_allow_html=True)

    st.markdown("""<div class="info-box">
        Severstal 실험 결과를 바탕으로 한 <strong>실무 적용 가능 아키텍처</strong>입니다.
    </div>""", unsafe_allow_html=True)

    st.markdown("""
    ```
    입력 이미지 (라인 카메라, 256×1600)
        │
        ▼
    ┌─────────────────────────────────────────┐
    │  Sliding Window → 256×256 패치 크롭      │
    └─────────────┬───────────────────────────┘
                  │
                  ▼
    ┌─────────────────────────────────────────┐
    │  Stage 1: 이진 분류 (Gate)               │
    │  "이 패치에 결함이 있는가?"                │
    │  ML: VotingEnsemble (73.00% / 빠름)        │
    │  DL: ResNet-18 FT (90.87% / 정확)        │
    └─────────────┬───────────────────────────┘
                  │
          ┌───────┴───────┐
          │               │
       [정상]           [비정상]
          │               │
       통과              ▼
                  ┌─────────────────────────────────────────┐
                  │  Stage 2: 4종 결함 분류 (Type)           │
                  │  "PS / LS / SS / RD 중 어떤 결함인가?"    │
                  │  ML: LightGBM (77.72%)                   │
                  │  DL: ResNet-18 FT (86.01%)               │
                  └─────────────────────────────────────────┘
                            │
                       ┌────┴────┐
                       │         │
                  결함 리포트   경보 발생
                  (유형+위치)   (실시간 모니터링)
    ```
    """)

    st.markdown("""
    **이 구성의 장점:**

    | 장점 | 설명 |
    |------|------|
    | **2단계 분리** | Stage 1에서 대부분 정상 패치를 빠르게 통과시켜 처리 효율 향상 |
    | **도메인 특화** | 각 공정에 맞춰 재학습하면 최고 성능 달성 (도메인 일반화 분석 결론) |
    | **ML+DL 하이브리드** | 빠른 1차 필터(ML) + 정밀 2차 분류(DL) 조합 가능 |
    | **확장성** | 새 결함 유형 추가 시 Stage 2만 재학습 |
    """)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── 핵심 인사이트 ──
    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("IN","ib-red")} 프로젝트 핵심 인사이트</div>',
                unsafe_allow_html=True)

    st.markdown("""
    #### 기 (Introduction)
    Severstal 철강 결함 데이터(12,568장, 4종 결함)를 활용하여
    **OpenCV 전처리 + 전통 ML + 딥러닝 + 이상 탐지**의 하이브리드 결함 검수 시스템을 구축했습니다.

    #### 승 (Development)
    - **Stage 1 이진 분류**: ML 최고 73.00% (VotingEnsemble) → DL 90.87% (ResNet-18) = **+17.87%p 향상**
    - **Stage 2 결함 분류**: ML 77.72% → DL 86.01% = **+8.29%p 향상**
    - 딥러닝이 특징 추출을 자동화하면서 전통 ML의 한계를 극복

    #### 전 (Turning Point)
    - **도메인 전이 검증**: Severstal 90.87% → NEU 14.4% (**-76.47%p 성능 하락**)
    - 같은 ResNet-18도 데이터에 따라 14.4%~100%의 극단적 성능 차이
    - **데이터 중심 AI**: 모델 아키텍처보다 학습 데이터의 대표성이 핵심

    #### 결 (Conclusion)
    1. **전이 학습의 양면성**: ImageNet→Severstal 전이는 성공, Severstal→NEU 전이는 실패
    2. **전통 ML의 가치**: HOG/LBP 기반 ML이 도메인 전이에서 더 강건 (52.7% vs 14.4%)
    3. **실무 적용**: 각 공정에 맞춘 **도메인 특화 재학습** + **2-Stage 하이브리드** 구조 필수
    4. **품질 관리**: 도메인 일반화 검증을 모델 배포 전 필수 단계로 포함해야 함
    """)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── 노트북 근거 자료 ──
    fig_dir = os.path.join(PROJECT_ROOT, "outputs", "figures", "severstal")
    if os.path.isdir(fig_dir):
        with st.expander("📊 실험 근거 자료 — 핵심 시각화", expanded=False):
            st.markdown("""<div class="info-box">
                위 분석의 근거가 되는 노트북 실험 결과입니다.
            </div>""", unsafe_allow_html=True)

            evidence_figs = {
                "03_tsne_and_correlation.png": "특징 공간 t-SNE 시각화 + 특징 상관관계 (정상/결함 분리도 확인)",
                "05_ml_vs_dl_comparison.png": "ML vs DL 정확도 종합 비교 (Stage 1 이진 분류)",
                "04_model_comparison.png": "ML 7모델 성능 비교 차트",
                "05_dl_training_curves.png": "DL 학습 곡선 (ResNet-18 Fine-tune & Feature Extractor)",
                "12_stage1_comparison.png": "Stage 1 이진 분류 전체 비교",
                "12_stage2_comparison.png": "Stage 2 결함 분류 전체 비교",
                "12_cross_domain.png": "도메인 일반화 종합 결과",
            }

            for fname, caption in evidence_figs.items():
                fpath = os.path.join(fig_dir, fname)
                if os.path.exists(fpath):
                    st.image(fpath, caption=caption, use_container_width=True)

    # ── 종합 KPI ──
    st.markdown(f'<div class="section-card"><div class="section-title">'
                f'{B("KP","ib-teal")} 종합 핵심 수치</div>',
                unsafe_allow_html=True)

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.markdown('<div class="kpi-card"><p class="kpi-label">Stage 1 DL</p>'
                    '<p class="kpi-value">90.87%</p></div>', unsafe_allow_html=True)
    with k2:
        st.markdown('<div class="kpi-card"><p class="kpi-label">Stage 2 DL</p>'
                    '<p class="kpi-value" style="color:#2563eb;">86.01%</p></div>', unsafe_allow_html=True)
    with k3:
        st.markdown('<div class="kpi-card"><p class="kpi-label">DL vs ML 향상</p>'
                    '<p class="kpi-value" style="color:#7c3aed;">+17.87%p</p></div>', unsafe_allow_html=True)
    with k4:
        st.markdown('<div class="kpi-card"><p class="kpi-label">Domain Gap</p>'
                    '<p class="kpi-value" style="color:#dc2626;">-76.47%p</p></div>', unsafe_allow_html=True)
    with k5:
        st.markdown('<div class="kpi-card"><p class="kpi-label">NEU 독립</p>'
                    '<p class="kpi-value" style="color:#059669;">100%</p></div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

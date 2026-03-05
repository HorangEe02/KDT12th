"""
=============================================================
종합 대시보드 생성 모듈
=============================================================
matplotlib 3x3 그리드 대시보드 + Plotly 인터랙티브 대시보드
모든 차트를 실제 수집/분석 데이터 기반으로 생성
개별 서브차트 PNG 저장 기능 포함
=============================================================
"""

import os
import re
import glob

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib import rcParams
import seaborn as sns

from config.settings import (
    DATA_PROCESSED_DIR, DATA_RAW_DIR, OUTPUTS_CHARTS_DIR,
    KOREAN_FONT_CANDIDATES,
)

KOREAN_FONT_PATH = None


def setup_korean_font():
    global KOREAN_FONT_PATH
    candidates = list(KOREAN_FONT_CANDIDATES)
    for f in fm.fontManager.ttflist:
        if any(k in f.name for k in ["Apple SD Gothic Neo", "AppleGothic", "Malgun", "NanumGothic", "Noto Sans CJK"]):
            candidates.insert(0, f.fname)
    for fp in candidates:
        if os.path.exists(fp):
            KOREAN_FONT_PATH = fp
            break
    if KOREAN_FONT_PATH:
        font_prop = fm.FontProperties(fname=KOREAN_FONT_PATH)
        fm.fontManager.addfont(KOREAN_FONT_PATH)
        rcParams["font.family"] = font_prop.get_name()
        rcParams["axes.unicode_minus"] = False


sns.set_style("whitegrid")
setup_korean_font()


class AnalysisDashboard:
    """분석 결과 종합 대시보드 (실제 데이터 기반)"""

    def __init__(self, processed_data_path: str = None):
        self.data_path = processed_data_path or DATA_PROCESSED_DIR
        self.data = {}
        self._load_all_data()

    def _load_all_data(self):
        """전처리 완료된 데이터 로드"""
        csv_files = glob.glob(os.path.join(self.data_path, "*.csv"))
        for f in csv_files:
            name = os.path.basename(f).replace("_processed.csv", "").replace(".csv", "")
            try:
                self.data[name] = pd.read_csv(f, encoding="utf-8-sig")
                print(f"  📂 {name}: {len(self.data[name])}건")
            except Exception as e:
                print(f"  ⚠️ {name} 로드 실패: {e}")

    def _find_df(self, *keywords):
        """키워드를 포함하는 데이터프레임 반환"""
        for name, df in self.data.items():
            if any(kw in name for kw in keywords):
                return df
        return None

    def _get_tech_stack(self):
        """기술스택 빈도 데이터"""
        df = self._find_df("tech_stack")
        if df is not None and not df.empty:
            return df
        return None

    def _get_review_df(self):
        """잡플래닛 리뷰 데이터"""
        return self._find_df("리뷰", "review")

    def _get_interview_df(self):
        """잡플래닛 면접후기 데이터"""
        return self._find_df("면접", "interview")

    def _get_company_df(self):
        """잡플래닛 기업정보 데이터"""
        return self._find_df("기업정보", "company")

    def _get_blog_df(self):
        """네이버 블로그 데이터"""
        return self._find_df("blog", "블로그")

    def _get_news_df(self):
        """네이버 뉴스 데이터"""
        return self._find_df("news", "뉴스")

    def _get_domain_freq(self):
        """자율주행 도메인 빈도"""
        return self._find_df("domain")

    def _get_cert_freq(self):
        """자격증 빈도"""
        return self._find_df("certificate")

    def _compute_monthly_trend(self):
        """블로그+뉴스 게시일자 기반 월별 콘텐츠 수 (최근 12개월)"""
        all_dates = []

        blog_df = self._get_blog_df()
        if blog_df is not None and "게시일자" in blog_df.columns:
            dates = pd.to_datetime(blog_df["게시일자"], errors="coerce")
            all_dates.append(dates.dropna())

        news_df = self._get_news_df()
        if news_df is not None and "게시일자" in news_df.columns:
            dates = pd.to_datetime(news_df["게시일자"], errors="coerce")
            all_dates.append(dates.dropna())

        # 리뷰 등록일 ("2025. 11" 형식)
        review_df = self._get_review_df()
        if review_df is not None and "등록일" in review_df.columns:
            def parse_review_date(s):
                m = re.match(r"(\d{4})\.\s*(\d{1,2})", str(s))
                if m:
                    return pd.Timestamp(year=int(m.group(1)), month=int(m.group(2)), day=1)
                return pd.NaT
            dates = review_df["등록일"].apply(parse_review_date)
            all_dates.append(dates.dropna())

        if not all_dates:
            return None, None

        combined = pd.concat(all_dates, ignore_index=True)

        # 최근 12개월 범위 계산
        end_month = pd.Timestamp.now().to_period("M")
        start_month = end_month - 11
        all_months = pd.period_range(start_month, end_month, freq="M")

        combined_period = combined.dt.to_period("M")
        counts = combined_period.value_counts().sort_index()

        # 12개월 모두 포함 (없는 달은 0)
        month_labels = []
        month_values = []
        for m in all_months:
            month_labels.append(f"{m.month}월")
            month_values.append(int(counts.get(m, 0)))

        return month_labels, month_values

    def generate_summary_stats(self) -> dict:
        """실제 데이터 기반 핵심 통계"""
        stats = {
            "총 분석 데이터": f"{sum(len(df) for df in self.data.values())}건",
            "데이터 소스": f"{len(self.data)}개",
        }

        # 블로그/뉴스 건수
        blog_df = self._get_blog_df()
        news_df = self._get_news_df()
        if blog_df is not None:
            stats["블로그 수집"] = f"{len(blog_df)}건"
        if news_df is not None:
            stats["뉴스 수집"] = f"{len(news_df)}건"

        # 리뷰 기반 통계
        review_df = self._get_review_df()
        if review_df is not None and "별점" in review_df.columns:
            ratings = pd.to_numeric(review_df["별점"], errors="coerce").dropna()
            if len(ratings) > 0:
                stats["평균 별점"] = f"{ratings.mean():.2f} / 5.0"
                # 최고 평점 기업
                company_avg = review_df.groupby("기업명")["별점"].apply(
                    lambda x: pd.to_numeric(x, errors="coerce").mean()
                ).sort_values(ascending=False)
                if len(company_avg) > 0:
                    top_name = company_avg.index[0]
                    top_score = company_avg.iloc[0]
                    stats["최고평점 기업"] = f"{top_name} ({top_score:.1f})"
            stats["리뷰 수집"] = f"{len(review_df)}건"

        # 면접 통계
        interview_df = self._get_interview_df()
        if interview_df is not None and "면접난이도" in interview_df.columns:
            top_diff = interview_df["면접난이도"].value_counts()
            if len(top_diff) > 0:
                stats["면접난이도 최다"] = f"{top_diff.index[0]} ({top_diff.iloc[0]}건)"
            stats["면접후기 수집"] = f"{len(interview_df)}건"

        # 대상 기업 수
        company_df = self._get_company_df()
        if company_df is not None:
            stats["분석 기업"] = f"{len(company_df)}개"

        # 기술스택 TOP 3
        tech_df = self._get_tech_stack()
        if tech_df is not None and len(tech_df) >= 3:
            top3 = tech_df.iloc[:3, 0].tolist()
            stats["기술스택 TOP3"] = ", ".join(str(t) for t in top3)

        # 원티드 포지션 통계
        wanted_df = self._find_df("원티드", "wanted")
        if wanted_df is not None:
            stats["원티드 포지션"] = f"{len(wanted_df)}건"
            if "회사명" in wanted_df.columns:
                stats["원티드 기업"] = f"{wanted_df['회사명'].nunique()}개"

        return stats

    # ─────────────────────────────────────────────
    # 개별 서브차트 _draw_* 메서드
    # ─────────────────────────────────────────────

    def _draw_tech_stack(self, ax):
        """[1] 기술스택 TOP 10"""
        tech_df = self._get_tech_stack()
        if tech_df is not None and not tech_df.empty:
            top10 = tech_df.head(10).iloc[::-1]
            name_col, freq_col = top10.columns[0], top10.columns[1]
            colors = plt.cm.Blues(np.linspace(0.3, 0.9, len(top10)))
            ax.barh(top10[name_col].astype(str), top10[freq_col], color=colors)
            for i, (_, row) in enumerate(top10.iterrows()):
                ax.text(row[freq_col] + 0.3, i, str(int(row[freq_col])),
                        va="center", fontsize=9, fontweight="bold")
        ax.set_title("기술스택 TOP 10", fontsize=14, fontweight="bold")

    def _draw_review_status(self, ax):
        """[2] 재직상태 분포"""
        review_df = self._get_review_df()
        if review_df is not None and "재직상태" in review_df.columns:
            status_counts = review_df["재직상태"].value_counts()
            valid = status_counts[status_counts.index.isin(["현직원", "전직원"])]
            if not valid.empty:
                ax.pie(
                    valid.values, labels=valid.index, autopct="%1.0f%%",
                    colors=["#4ECDC4", "#FF6B6B"], startangle=90,
                    wedgeprops=dict(width=0.4))
                ax.text(0, 0, f"총 {valid.sum()}건", ha="center", va="center",
                        fontsize=11, fontweight="bold")
        ax.set_title("리뷰 재직상태 분포", fontsize=14, fontweight="bold")

    def _draw_interview_difficulty(self, ax):
        """[3] 면접난이도 분포"""
        interview_df = self._get_interview_df()
        if interview_df is not None and "면접난이도" in interview_df.columns:
            diff_counts = interview_df["면접난이도"].value_counts()
            order = ["매우 쉬움", "쉬움", "보통", "어려움", "매우 어려움"]
            ordered = diff_counts.reindex([o for o in order if o in diff_counts.index])
            colors_diff = ["#85C1E9", "#5DADE2", "#F4D03F", "#E67E22", "#E74C3C"]
            bars = ax.bar(ordered.index, ordered.values,
                          color=colors_diff[:len(ordered)], edgecolor="white")
            for bar, val in zip(bars, ordered.values):
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                        str(val), ha="center", fontsize=10, fontweight="bold")
            ax.set_ylabel("건수")
        ax.set_title("면접 난이도 분포", fontsize=14, fontweight="bold")

    def _draw_company_ratings(self, ax):
        """[4] 기업 평균 별점 비교"""
        review_df = self._get_review_df()
        if review_df is not None and "별점" in review_df.columns:
            company_avg = review_df.groupby("기업명")["별점"].apply(
                lambda x: pd.to_numeric(x, errors="coerce").mean()
            ).sort_values(ascending=True)

            cmap = plt.cm.RdYlGn
            norm_vals = (company_avg - company_avg.min()) / (company_avg.max() - company_avg.min() + 1e-9)
            colors_bar = [cmap(v) for v in norm_vals]

            ax.barh(company_avg.index, company_avg.values, color=colors_bar)
            ax.axvline(x=3.0, color="red", linestyle="--", alpha=0.5, label="3.0 기준")
            ax.set_xlim(0, 5.5)
            for i, (name, val) in enumerate(company_avg.items()):
                ax.text(val + 0.05, i, f"{val:.1f}", va="center", fontsize=9, fontweight="bold")
            ax.legend(fontsize=9)
        ax.set_title("기업 평균 별점 비교", fontsize=14, fontweight="bold")

    def _draw_monthly_trend(self, ax):
        """[5] 월별 콘텐츠 동향"""
        month_labels, month_values = self._compute_monthly_trend()
        if month_labels and month_values:
            ax.plot(month_labels, month_values, marker="o", color="#0891B2",
                    linewidth=2, markersize=6)
            ax.fill_between(range(len(month_labels)), month_values,
                            alpha=0.1, color="#0891B2")
            for i, val in enumerate(month_values):
                if val > 0:
                    ax.text(i, val + max(month_values) * 0.03, str(val),
                            ha="center", fontsize=8, fontweight="bold")
            ax.set_ylabel("콘텐츠 수")
            plt.sca(ax)
            plt.xticks(rotation=45, ha="right", fontsize=9)
        ax.set_title("월별 자율주행/모빌리티 콘텐츠 동향 (최근 12개월)", fontsize=14, fontweight="bold")

    def _draw_company_size(self, ax):
        """[6] 기업 규모 분포"""
        company_df = self._get_company_df()
        if company_df is not None and "분야" in company_df.columns:
            sizes = company_df["분야"].str.split("_").str[0]
            size_counts = sizes.value_counts()
            colors_pie = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4"]
            ax.pie(size_counts.values, labels=size_counts.index, autopct="%1.0f%%",
                   colors=colors_pie[:len(size_counts)], startangle=90,
                   explode=[0.03] * len(size_counts))
        ax.set_title("기업 규모 분포", fontsize=14, fontweight="bold")

    def _draw_domain_distribution(self, ax):
        """[7] 자율주행 도메인 분포"""
        domain_df = self._get_domain_freq()
        if domain_df is not None and not domain_df.empty:
            if "카테고리" in domain_df.columns and "빈도" in domain_df.columns:
                cat_sum = domain_df.groupby("카테고리")["빈도"].sum().sort_values(ascending=False)
            else:
                cat_sum = domain_df.iloc[:, :2].set_index(domain_df.columns[0]).iloc[:, 0]
            ax.pie(cat_sum.values, labels=cat_sum.index, autopct="%1.0f%%",
                   colors=sns.color_palette("Set3", len(cat_sum)), startangle=90)
        ax.set_title("자율주행 도메인 분포", fontsize=14, fontweight="bold")

    def _draw_certificate_freq(self, ax):
        """[8] 자격증 빈도"""
        cert_df = self._get_cert_freq()
        if cert_df is not None and not cert_df.empty:
            name_col, freq_col = cert_df.columns[0], cert_df.columns[1]
            colors_cert = sns.color_palette("YlOrRd_r", len(cert_df))
            bars = ax.bar(cert_df[name_col], cert_df[freq_col],
                          color=colors_cert, edgecolor="white")
            for bar, val in zip(bars, cert_df[freq_col]):
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.2,
                        str(int(val)), ha="center", fontsize=10, fontweight="bold")
            ax.set_ylabel("빈도")
            plt.sca(ax)
            plt.xticks(rotation=30, ha="right", fontsize=9)
        ax.set_title("자격증/우대사항 빈도", fontsize=14, fontweight="bold")

    def _draw_key_stats(self, ax):
        """[9] 핵심 통계"""
        stats = self.generate_summary_stats()
        ax.axis("off")

        stat_lines = []
        for key, val in stats.items():
            stat_lines.append(f"  {key}: {val}")

        stat_text = "핵심 통계 요약\n\n" + "\n".join(stat_lines)

        font_kw = {"fname": KOREAN_FONT_PATH} if KOREAN_FONT_PATH else {}
        ax.text(0.05, 0.95, stat_text, transform=ax.transAxes, fontsize=12,
                verticalalignment="top", linespacing=1.6,
                fontproperties=fm.FontProperties(**font_kw) if font_kw else None,
                bbox=dict(boxstyle="round,pad=0.8", facecolor="#F0F8FF", alpha=0.9,
                          edgecolor="#4ECDC4", linewidth=2))
        ax.set_title("핵심 통계", fontsize=14, fontweight="bold")

    # ─────────────────────────────────────────────
    # 개별 PNG 저장 헬퍼
    # ─────────────────────────────────────────────

    def _save_individual_chart(self, draw_func, filename, figsize=(8, 6)):
        """개별 서브차트를 별도 PNG로 저장"""
        fig, ax = plt.subplots(figsize=figsize)
        draw_func(ax)
        fig.tight_layout()
        save_path = os.path.join(OUTPUTS_CHARTS_DIR, filename)
        fig.savefig(save_path, dpi=300, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        print(f"    -> {filename}")

    def save_individual_charts(self):
        """9개 서브차트를 개별 PNG로 저장"""
        print("\n  📂 개별 서브차트 PNG 저장 중...")

        chart_specs = [
            (self._draw_tech_stack,          "dashboard_01_tech_stack.png",          (8, 6)),
            (self._draw_review_status,       "dashboard_02_review_status.png",       (7, 7)),
            (self._draw_interview_difficulty, "dashboard_03_interview_difficulty.png", (8, 6)),
            (self._draw_company_ratings,     "dashboard_04_company_ratings.png",     (8, 6)),
            (self._draw_monthly_trend,       "dashboard_05_monthly_trend.png",       (10, 5)),
            (self._draw_company_size,        "dashboard_06_company_size.png",        (7, 7)),
            (self._draw_domain_distribution, "dashboard_07_domain_distribution.png", (7, 7)),
            (self._draw_certificate_freq,    "dashboard_08_certificate_freq.png",    (8, 6)),
            (self._draw_key_stats,           "dashboard_09_key_stats.png",           (8, 6)),
        ]

        for draw_func, filename, figsize in chart_specs:
            try:
                self._save_individual_chart(draw_func, filename, figsize)
            except Exception as e:
                print(f"    ⚠️ {filename} 저장 실패: {e}")

        print(f"  ✅ 개별 서브차트 {len(chart_specs)}개 저장 완료")

    # ─────────────────────────────────────────────
    # 종합 대시보드
    # ─────────────────────────────────────────────

    def create_summary_dashboard(self):
        """matplotlib subplot 기반 종합 대시보드 (3x3, 실제 데이터)"""
        print("\n📊 종합 대시보드 생성 중...")

        fig = plt.figure(figsize=(24, 20))
        fig.suptitle("자율주행/모빌리티 분야 취업 동향 종합 분석",
                     fontsize=24, fontweight="bold", y=0.98)

        # 9개 서브차트를 _draw_* 메서드로 그리기
        draw_methods = [
            self._draw_tech_stack,
            self._draw_review_status,
            self._draw_interview_difficulty,
            self._draw_company_ratings,
            self._draw_monthly_trend,
            self._draw_company_size,
            self._draw_domain_distribution,
            self._draw_certificate_freq,
            self._draw_key_stats,
        ]

        for idx, draw_func in enumerate(draw_methods, 1):
            ax = fig.add_subplot(3, 3, idx)
            draw_func(ax)

        plt.tight_layout(rect=[0, 0, 1, 0.96])
        save_path = os.path.join(OUTPUTS_CHARTS_DIR, "dashboard_summary.png")
        fig.savefig(save_path, dpi=300, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        print(f"  📊 대시보드 저장: {save_path}")

        # 개별 서브차트 PNG 자동 저장
        self.save_individual_charts()

    def create_plotly_dashboard(self):
        """Plotly subplots 기반 인터랙티브 대시보드 (실제 데이터)"""
        print("\n📊 인터랙티브 대시보드 생성 중...")

        try:
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots
        except ImportError:
            print("  ⚠️ plotly 패키지 필요: pip install plotly")
            return

        fig = make_subplots(
            rows=3, cols=3,
            subplot_titles=[
                "기술스택 TOP 10", "리뷰 재직상태 분포", "면접 난이도 분포",
                "기업 평균 별점", "월별 콘텐츠 동향 (12개월)", "기업 규모 분포",
                "자율주행 도메인 분포", "자격증/우대사항 빈도", "핵심 통계",
            ],
            specs=[
                [{"type": "bar"}, {"type": "pie"}, {"type": "bar"}],
                [{"type": "bar"}, {"type": "scatter"}, {"type": "pie"}],
                [{"type": "pie"}, {"type": "bar"}, {"type": "table"}],
            ],
        )

        # [1] 기술스택 TOP 10
        tech_df = self._get_tech_stack()
        if tech_df is not None and not tech_df.empty:
            top10 = tech_df.head(10)
            fig.add_trace(go.Bar(
                x=top10.iloc[:, 1], y=top10.iloc[:, 0].astype(str),
                orientation="h", marker_color="#4ECDC4"
            ), row=1, col=1)

        # [2] 재직상태 분포
        review_df = self._get_review_df()
        if review_df is not None and "재직상태" in review_df.columns:
            status = review_df["재직상태"].value_counts()
            valid = status[status.index.isin(["현직원", "전직원"])]
            if not valid.empty:
                fig.add_trace(go.Pie(
                    labels=valid.index.tolist(), values=valid.values.tolist(), hole=0.4
                ), row=1, col=2)

        # [3] 면접난이도 분포
        interview_df = self._get_interview_df()
        if interview_df is not None and "면접난이도" in interview_df.columns:
            order = ["매우 쉬움", "쉬움", "보통", "어려움", "매우 어려움"]
            diff = interview_df["면접난이도"].value_counts()
            ordered = diff.reindex([o for o in order if o in diff.index])
            fig.add_trace(go.Bar(
                x=ordered.index.tolist(), y=ordered.values.tolist(),
                marker_color=["#85C1E9", "#5DADE2", "#F4D03F", "#E67E22", "#E74C3C"][:len(ordered)]
            ), row=1, col=3)

        # [4] 기업 평균 별점
        if review_df is not None and "별점" in review_df.columns:
            company_avg = review_df.groupby("기업명")["별점"].apply(
                lambda x: pd.to_numeric(x, errors="coerce").mean()
            ).sort_values(ascending=True)
            fig.add_trace(go.Bar(
                x=company_avg.values, y=company_avg.index.tolist(),
                orientation="h", marker_color="#FF6B6B"
            ), row=2, col=1)

        # [5] 월별 동향 (12개월)
        month_labels, month_values = self._compute_monthly_trend()
        if month_labels and month_values:
            fig.add_trace(go.Scatter(
                x=month_labels, y=month_values, mode="lines+markers",
                line=dict(color="#0891B2", width=2), fill="tozeroy",
                fillcolor="rgba(8, 145, 178, 0.1)"
            ), row=2, col=2)

        # [6] 기업 규모 분포
        company_df = self._get_company_df()
        if company_df is not None and "분야" in company_df.columns:
            sizes = company_df["분야"].str.split("_").str[0].value_counts()
            fig.add_trace(go.Pie(
                labels=sizes.index.tolist(), values=sizes.values.tolist()
            ), row=2, col=3)

        # [7] 자율주행 도메인 분포
        domain_df = self._get_domain_freq()
        if domain_df is not None and "카테고리" in domain_df.columns:
            cat_sum = domain_df.groupby("카테고리")["빈도"].sum().sort_values(ascending=False)
            fig.add_trace(go.Pie(
                labels=cat_sum.index.tolist(), values=cat_sum.values.tolist()
            ), row=3, col=1)

        # [8] 자격증 빈도
        cert_df = self._get_cert_freq()
        if cert_df is not None and not cert_df.empty:
            fig.add_trace(go.Bar(
                x=cert_df.iloc[:, 0].astype(str).tolist(),
                y=cert_df.iloc[:, 1].tolist(),
                marker_color="#FF9F1C"
            ), row=3, col=2)

        # [9] 핵심 통계 테이블
        stats = self.generate_summary_stats()
        fig.add_trace(go.Table(
            header=dict(values=["항목", "값"], fill_color="#4ECDC4",
                       font=dict(color="white", size=12)),
            cells=dict(
                values=[list(stats.keys()), list(str(v) for v in stats.values())],
                fill_color="#F0F8FF", font=dict(size=11),
                align="left",
            ),
        ), row=3, col=3)

        fig.update_layout(
            title="자율주행/모빌리티 분야 취업 동향 종합 대시보드",
            template="plotly_white",
            height=1200,
            showlegend=False,
        )

        html_path = os.path.join(OUTPUTS_CHARTS_DIR, "dashboard_interactive.html")
        fig.write_html(html_path)
        print(f"  📊 인터랙티브 대시보드 저장: {html_path}")


if __name__ == "__main__":
    dashboard = AnalysisDashboard()
    dashboard.create_summary_dashboard()
    dashboard.create_plotly_dashboard()

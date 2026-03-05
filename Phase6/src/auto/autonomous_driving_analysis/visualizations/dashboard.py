"""
종합 대시보드 모듈
matplotlib 기반 정적 대시보드 + Plotly 기반 인터랙티브 대시보드
"""

import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from config.settings import FONT_PATH, OUTPUT_CHARTS_DIR, DATA_PROCESSED_DIR

logger = logging.getLogger(__name__)

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


class AnalysisDashboard:
    """분석 결과 종합 대시보드"""

    def __init__(self, processed_data_path: str = None):
        self.data_path = Path(processed_data_path) if processed_data_path else DATA_PROCESSED_DIR
        self.output_dir = OUTPUT_CHARTS_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.data = {}
        self._setup_font()
        self._load_data()

    def _setup_font(self):
        sns.set_style("whitegrid")
        if FONT_PATH:
            fm.fontManager.addfont(FONT_PATH)
            font_name = fm.FontProperties(fname=FONT_PATH).get_name()
            plt.rcParams["font.family"] = font_name
            plt.rcParams["font.sans-serif"] = [font_name] + plt.rcParams.get("font.sans-serif", [])
        else:
            plt.rcParams["font.family"] = "AppleGothic"
            plt.rcParams["font.sans-serif"] = ["AppleGothic"] + plt.rcParams.get("font.sans-serif", [])
        plt.rcParams["axes.unicode_minus"] = False

    def _load_data(self):
        """전처리 완료된 데이터 로드"""
        if not self.data_path.exists():
            logger.warning(f"데이터 경로가 존재하지 않습니다: {self.data_path}")
            return

        for csv_file in self.data_path.glob("*.csv"):
            key = csv_file.stem
            try:
                self.data[key] = pd.read_csv(csv_file, encoding="utf-8-sig")
                logger.info(f"데이터 로드: {key} ({len(self.data[key])}건)")
            except Exception as e:
                logger.warning(f"로드 실패: {csv_file.name} - {e}")

    def create_summary_dashboard(self):
        """matplotlib 기반 종합 대시보드 (2×3 그리드)"""
        fig = plt.figure(figsize=(24, 16))  # A3 비율
        fig.suptitle("자율주행 AI 분야 취업 동향 종합 분석",
                     fontsize=22, fontweight="bold", y=0.98)

        # ── [1] 기술스택 TOP 10 막대그래프 ──
        ax1 = fig.add_subplot(2, 3, 1)
        tech_data = self._get_tech_data()
        if tech_data is not None:
            df = tech_data.head(10).sort_values("빈도", ascending=True)
            colors = sns.color_palette("Blues_d", len(df))
            ax1.barh(df["기술스택"], df["빈도"], color=colors)
            ax1.set_title("기술스택 TOP 10", fontsize=14, fontweight="bold")
            ax1.set_xlabel("빈도")
        else:
            ax1.text(0.5, 0.5, "데이터 없음", ha="center", va="center", fontsize=14)
            ax1.set_title("기술스택 TOP 10", fontsize=14)

        # ── [2] 경력/신입 비율 도넛차트 ──
        ax2 = fig.add_subplot(2, 3, 2)
        career_data = self._get_career_data()
        if career_data is not None:
            colors = sns.color_palette("Set2", len(career_data))
            wedges, _, autotexts = ax2.pie(
                career_data["건수"], labels=career_data["경력구분"],
                autopct="%1.1f%%", colors=colors,
                pctdistance=0.85, wedgeprops=dict(width=0.4)
            )
            total = career_data["건수"].sum()
            ax2.text(0, 0, f"{total}건", ha="center", va="center", fontsize=14, fontweight="bold")
        ax2.set_title("경력/신입 비율", fontsize=14, fontweight="bold")

        # ── [3] 기업별 연봉 박스플롯 ──
        ax3 = fig.add_subplot(2, 3, 3)
        salary_data = self._get_salary_data()
        if salary_data is not None:
            company_col = "기업명" if "기업명" in salary_data.columns else "회사명"
            if company_col in salary_data.columns and "연봉_만원" in salary_data.columns:
                salary_data.boxplot(column="연봉_만원", by=company_col, ax=ax3)
                ax3.set_title("기업별 연봉 분포", fontsize=14, fontweight="bold")
                plt.sca(ax3)
                plt.xticks(rotation=45, ha="right", fontsize=8)
                ax3.set_xlabel("")
                fig.suptitle("자율주행 AI 분야 취업 동향 종합 분석",
                             fontsize=22, fontweight="bold", y=0.98)
            else:
                ax3.text(0.5, 0.5, "데이터 없음", ha="center", va="center")
                ax3.set_title("기업별 연봉 분포", fontsize=14)
        else:
            ax3.text(0.5, 0.5, "데이터 없음", ha="center", va="center")
            ax3.set_title("기업별 연봉 분포", fontsize=14)

        # ── [4] 기업 평점 레이더차트 ──
        ax4 = fig.add_subplot(2, 3, 4, polar=True)
        ratings = self._get_ratings_data()
        if ratings:
            categories = list(list(ratings.values())[0].keys())
            angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
            angles += angles[:1]
            colors_list = ["#2196F3", "#F44336", "#4CAF50"]

            for idx, (company, vals) in enumerate(list(ratings.items())[:3]):
                values = list(vals.values()) + [list(vals.values())[0]]
                ax4.plot(angles, values, "o-", label=company, color=colors_list[idx % 3])
                ax4.fill(angles, values, alpha=0.1, color=colors_list[idx % 3])

            ax4.set_xticks(angles[:-1])
            ax4.set_xticklabels(categories, fontsize=8)
            ax4.legend(loc="upper right", fontsize=8)
        ax4.set_title("기업 평점 비교", fontsize=14, fontweight="bold", y=1.1)

        # ── [5] 채용 트렌드 라인차트 ──
        ax5 = fig.add_subplot(2, 3, 5)
        trend_data = self._get_trend_data()
        if trend_data is not None:
            ax5.plot(trend_data.index, trend_data.values, "o-", color="#2196F3", linewidth=2)
            ax5.fill_between(trend_data.index, trend_data.values, alpha=0.1, color="#2196F3")
            plt.sca(ax5)
            plt.xticks(rotation=45, ha="right", fontsize=8)
        ax5.set_title("월별 채용 트렌드", fontsize=14, fontweight="bold")
        ax5.set_ylabel("공고 수")

        # ── [6] 기업 규모별 분포 파이차트 ──
        ax6 = fig.add_subplot(2, 3, 6)
        size_data = self._get_size_data()
        if size_data is not None:
            colors = ["#2196F3", "#4CAF50", "#FF9800", "#F44336"]
            ax6.pie(size_data["건수"], labels=size_data["기업규모"],
                    autopct="%1.1f%%", colors=colors[:len(size_data)])
        ax6.set_title("기업 규모별 분포", fontsize=14, fontweight="bold")

        fig.tight_layout(rect=[0, 0, 1, 0.95])
        filepath = self.output_dir / "dashboard_summary.png"
        fig.savefig(filepath, dpi=300, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        logger.info(f"종합 대시보드 저장: {filepath}")

    def create_plotly_dashboard(self):
        """Plotly 기반 인터랙티브 대시보드"""
        if not PLOTLY_AVAILABLE:
            logger.warning("Plotly가 설치되지 않아 인터랙티브 대시보드를 생성할 수 없습니다.")
            return

        fig = make_subplots(
            rows=2, cols=3,
            subplot_titles=["기술스택 TOP 10", "경력 분포", "기업별 연봉",
                           "기업 평점", "채용 트렌드", "기업 규모"],
            specs=[[{"type": "bar"}, {"type": "pie"}, {"type": "box"}],
                   [{"type": "scatterpolar"}, {"type": "scatter"}, {"type": "pie"}]]
        )

        # [1] 기술스택 TOP 10
        tech_data = self._get_tech_data()
        if tech_data is not None:
            df = tech_data.head(10)
            fig.add_trace(go.Bar(x=df["기술스택"], y=df["빈도"], name="기술스택",
                                marker_color="#2196F3"), row=1, col=1)

        # [2] 경력 분포
        career_data = self._get_career_data()
        if career_data is not None:
            fig.add_trace(go.Pie(labels=career_data["경력구분"], values=career_data["건수"],
                                name="경력", hole=0.4), row=1, col=2)

        # [3] 기업별 연봉
        salary_data = self._get_salary_data()
        if salary_data is not None:
            company_col = "기업명" if "기업명" in salary_data.columns else "회사명"
            if company_col in salary_data.columns and "연봉_만원" in salary_data.columns:
                for company in salary_data[company_col].unique()[:5]:
                    subset = salary_data[salary_data[company_col] == company]
                    fig.add_trace(go.Box(y=subset["연봉_만원"], name=company), row=1, col=3)

        # [5] 채용 트렌드
        trend_data = self._get_trend_data()
        if trend_data is not None:
            fig.add_trace(go.Scatter(x=list(trend_data.index), y=list(trend_data.values),
                                    mode="lines+markers", name="트렌드",
                                    line=dict(color="#2196F3")), row=2, col=2)

        # [6] 기업 규모
        size_data = self._get_size_data()
        if size_data is not None:
            fig.add_trace(go.Pie(labels=size_data["기업규모"], values=size_data["건수"],
                                name="규모"), row=2, col=3)

        fig.update_layout(
            title_text="자율주행 AI 분야 취업 동향 종합 분석 (인터랙티브)",
            template="plotly_white",
            showlegend=False,
            height=900, width=1400,
        )

        filepath = self.output_dir / "dashboard_interactive.html"
        fig.write_html(str(filepath))
        logger.info(f"인터랙티브 대시보드 저장: {filepath}")

    def generate_summary_stats(self) -> dict:
        """핵심 통계 요약"""
        stats = {
            "분석일시": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
            "총_분석_공고수": 0,
            "기술스택_TOP5": [],
            "평균연봉_만원": 0,
            "연봉범위_만원": "",
            "신입채용_비율": 0,
            "최고평점_기업": "",
        }

        # 총 공고수
        for key, df in self.data.items():
            if "saramin" in key or "wanted" in key:
                stats["총_분석_공고수"] += len(df)

        # 기술스택 TOP5
        tech_data = self._get_tech_data()
        if tech_data is not None:
            stats["기술스택_TOP5"] = tech_data.head(5)["기술스택"].tolist()

        # 연봉 정보
        salary_data = self._get_salary_data()
        if salary_data is not None and "연봉_만원" in salary_data.columns:
            salary = salary_data["연봉_만원"].dropna()
            if not salary.empty:
                stats["평균연봉_만원"] = round(salary.mean())
                stats["연봉범위_만원"] = f"{round(salary.min())} ~ {round(salary.max())}"

        # 출력
        print("\n" + "=" * 50)
        print("📊 분석 결과 핵심 요약")
        print("=" * 50)
        for key, val in stats.items():
            print(f"  {key}: {val}")
        print("=" * 50)

        return stats

    # ── 데이터 추출 헬퍼 메서드 ──

    def _get_tech_data(self):
        for key in ["tech_stack_freq", "processed_saramin", "processed_wanted"]:
            if key in self.data and "기술스택" in self.data[key].columns:
                return self.data[key]
        return None

    def _get_career_data(self):
        for key, df in self.data.items():
            if "경력구분" in df.columns:
                counts = df["경력구분"].value_counts().reset_index()
                counts.columns = ["경력구분", "건수"]
                return counts
        return None

    def _get_salary_data(self):
        for key, df in self.data.items():
            if "연봉_만원" in df.columns:
                return df
        return None

    def _get_ratings_data(self):
        for key, df in self.data.items():
            if "총점" in df.columns and ("기업명" in df.columns or "회사명" in df.columns):
                company_col = "기업명" if "기업명" in df.columns else "회사명"
                rating_cols = ["총점", "승진기회", "워라밸", "급여", "사내문화", "경영진"]
                available = [c for c in rating_cols if c in df.columns]
                if available:
                    grouped = df.groupby(company_col)[available].mean()
                    return {company: row.to_dict() for company, row in grouped.head(5).iterrows()}
        return None

    def _get_trend_data(self):
        for key, df in self.data.items():
            date_col = None
            for c in ["작성일", "발행일", "마감일"]:
                if c in df.columns:
                    date_col = c
                    break
            if date_col:
                temp = df.copy()
                temp[date_col] = pd.to_datetime(temp[date_col], errors="coerce")
                temp = temp.dropna(subset=[date_col])
                if not temp.empty:
                    monthly = temp.set_index(date_col).resample("ME").size()
                    if len(monthly) > 1:
                        return monthly
        return None

    def _get_size_data(self):
        for key, df in self.data.items():
            if "기업규모" in df.columns:
                counts = df["기업규모"].value_counts().reset_index()
                counts.columns = ["기업규모", "건수"]
                return counts
        return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    dashboard = AnalysisDashboard()
    dashboard.create_summary_dashboard()
    dashboard.create_plotly_dashboard()
    dashboard.generate_summary_stats()

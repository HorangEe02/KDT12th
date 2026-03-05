"""
기본 차트 시각화 모듈 (matplotlib + seaborn)
8종 정적 차트 생성: 막대, 도넛, 박스플롯, 그룹막대, 라인, 파이 등
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
from config.settings import FONT_PATH, OUTPUT_CHARTS_DIR

logger = logging.getLogger(__name__)


class ChartVisualizer:
    """기본 정적 차트 시각화 (8종)"""

    def __init__(self):
        self.output_dir = OUTPUT_CHARTS_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.dpi = 300
        self.figsize = (12, 8)
        sns.set_style("whitegrid")
        self._setup_korean_font()

    def _setup_korean_font(self):
        """한글 폰트 설정 (sns.set_style 이후에 호출해야 함)"""
        if FONT_PATH:
            fm.fontManager.addfont(FONT_PATH)
            font_name = fm.FontProperties(fname=FONT_PATH).get_name()
            plt.rcParams["font.family"] = font_name
            plt.rcParams["font.sans-serif"] = [font_name] + plt.rcParams.get("font.sans-serif", [])
        else:
            plt.rcParams["font.family"] = "AppleGothic"
            plt.rcParams["font.sans-serif"] = ["AppleGothic"] + plt.rcParams.get("font.sans-serif", [])

        plt.rcParams["axes.unicode_minus"] = False
        logger.info("한글 폰트 설정 완료")

    def _save_chart(self, fig, filename: str):
        """차트 저장"""
        filepath = self.output_dir / filename
        fig.savefig(filepath, dpi=self.dpi, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        logger.info(f"차트 저장: {filepath}")

    # ── 1. 기술스택 TOP 15 수평 막대그래프 ──
    def plot_tech_stack_top15(self, tech_freq_df: pd.DataFrame):
        """기술스택 TOP 15 수평 막대그래프"""
        df = tech_freq_df.head(15).sort_values("빈도", ascending=True)

        fig, ax = plt.subplots(figsize=self.figsize)
        colors = sns.color_palette("Blues_d", len(df))
        bars = ax.barh(df["기술스택"], df["빈도"], color=colors)

        # 수치 레이블
        for bar, val in zip(bars, df["빈도"]):
            ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                    f" {int(val)}", va="center", fontsize=10)

        ax.set_xlabel("빈도수", fontsize=12)
        ax.set_ylabel("기술스택", fontsize=12)
        ax.set_title("자율주행 분야 기술스택 TOP 15", fontsize=16, fontweight="bold")
        fig.tight_layout()
        self._save_chart(fig, "chart_tech_stack_top15.png")

    # ── 2. 경력/신입 비율 도넛차트 ──
    def plot_career_ratio_donut(self, career_data: pd.DataFrame):
        """경력 구분별 비율 도넛차트"""
        fig, ax = plt.subplots(figsize=(10, 10))
        colors = sns.color_palette("Set2", len(career_data))

        wedges, texts, autotexts = ax.pie(
            career_data["건수"], labels=career_data["경력구분"],
            autopct="%1.1f%%", startangle=90, colors=colors,
            pctdistance=0.85, wedgeprops=dict(width=0.4)
        )

        for text in autotexts:
            text.set_fontsize(11)
            text.set_fontweight("bold")

        # 중앙에 전체 수 표시
        total = career_data["건수"].sum()
        ax.text(0, 0, f"전체\n{total}건", ha="center", va="center",
                fontsize=18, fontweight="bold")

        ax.set_title("경력/신입 채용 비율", fontsize=16, fontweight="bold")
        self._save_chart(fig, "chart_career_ratio.png")

    # ── 3. 기업별 연봉 박스플롯 ──
    def plot_salary_boxplot(self, salary_data: pd.DataFrame):
        """기업별 연봉 박스플롯"""
        fig, ax = plt.subplots(figsize=(14, 8))

        # 기업규모별 색상 팔레트
        if "기업규모" in salary_data.columns:
            palette = {"대기업": "#2196F3", "대기업_부품": "#2196F3", "대기업_IT": "#1976D2",
                       "IT_대기업": "#1976D2", "중견기업": "#4CAF50", "중소기업": "#FF9800",
                       "스타트업": "#F44336"}
            sns.boxplot(data=salary_data, x="기업명", y="연봉_만원", hue="기업규모",
                        palette=palette, ax=ax, dodge=False)
        else:
            sns.boxplot(data=salary_data, x="기업명", y="연봉_만원", ax=ax,
                        palette="Set2")

        ax.set_xlabel("기업명", fontsize=12)
        ax.set_ylabel("연봉 (만원)", fontsize=12)
        ax.set_title("기업별 연봉 분포", fontsize=16, fontweight="bold")
        plt.xticks(rotation=45, ha="right")
        fig.tight_layout()
        self._save_chart(fig, "chart_salary_boxplot.png")

    # ── 4. 기업 평점 항목별 그룹 막대그래프 ──
    def plot_company_ratings(self, ratings_data: pd.DataFrame):
        """기업별 평점 비교 그룹 막대그래프"""
        rating_cols = ["총점", "승진기회", "워라밸", "급여", "사내문화", "경영진"]
        available_cols = [c for c in rating_cols if c in ratings_data.columns]

        if not available_cols:
            logger.warning("평점 데이터 컬럼이 없습니다.")
            return

        company_col = "기업명" if "기업명" in ratings_data.columns else "회사명"
        melted = ratings_data.melt(id_vars=[company_col], value_vars=available_cols,
                                    var_name="평가항목", value_name="점수")
        melted["점수"] = pd.to_numeric(melted["점수"], errors="coerce")

        fig, ax = plt.subplots(figsize=(14, 8))
        sns.barplot(data=melted, x="평가항목", y="점수", hue=company_col, ax=ax, palette="Set2")

        ax.axhline(y=5, color="red", linestyle="--", alpha=0.5, label="5점 만점")
        ax.set_xlabel("평가 항목", fontsize=12)
        ax.set_ylabel("점수", fontsize=12)
        ax.set_title("기업별 평점 항목 비교", fontsize=16, fontweight="bold")
        ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
        fig.tight_layout()
        self._save_chart(fig, "chart_company_ratings.png")

    # ── 5. 자격증/우대사항 빈도 수평 막대그래프 ──
    def plot_certificate_frequency(self, cert_data: pd.DataFrame):
        """자격증 빈도 TOP 10"""
        df = cert_data.head(10).sort_values("빈도", ascending=True)

        fig, ax = plt.subplots(figsize=self.figsize)
        colors = sns.color_palette("Oranges_d", len(df))
        bars = ax.barh(df["자격증"], df["빈도"], color=colors)

        for bar, val in zip(bars, df["빈도"]):
            ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                    f" {int(val)}", va="center", fontsize=10)

        ax.set_xlabel("빈도수", fontsize=12)
        ax.set_title("요구/우대 자격증 TOP 10", fontsize=16, fontweight="bold")
        fig.tight_layout()
        self._save_chart(fig, "chart_certificates.png")

    # ── 6. 월별 채용공고 수 추이 라인차트 ──
    def plot_monthly_trend(self, trend_data: pd.DataFrame):
        """월별 채용공고 수 추이"""
        fig, ax = plt.subplots(figsize=self.figsize)

        if isinstance(trend_data, pd.DataFrame) and "월" in trend_data.columns:
            ax.plot(trend_data["월"], trend_data["건수"], marker="o", linewidth=2,
                    color="#2196F3", markersize=8)
            ax.fill_between(trend_data["월"], trend_data["건수"], alpha=0.1, color="#2196F3")
        else:
            # Series 또는 인덱스 기반
            ax.plot(trend_data.index, trend_data.values, marker="o", linewidth=2,
                    color="#2196F3", markersize=8)

        ax.set_xlabel("월", fontsize=12)
        ax.set_ylabel("채용공고 수", fontsize=12)
        ax.set_title("월별 채용공고 수 추이", fontsize=16, fontweight="bold")
        plt.xticks(rotation=45, ha="right")
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        self._save_chart(fig, "chart_monthly_trend.png")

    # ── 7. 기업 규모별 채용 비율 파이차트 ──
    def plot_company_size_ratio(self, size_data: pd.DataFrame):
        """기업 규모별 채용 비율"""
        fig, ax = plt.subplots(figsize=(10, 10))
        colors = ["#2196F3", "#4CAF50", "#FF9800", "#F44336"]

        wedges, texts, autotexts = ax.pie(
            size_data["건수"], labels=size_data["기업규모"],
            autopct="%1.1f%%", startangle=90, colors=colors[:len(size_data)],
            explode=[0.02] * len(size_data)
        )

        for text in autotexts:
            text.set_fontsize(12)
            text.set_fontweight("bold")

        ax.set_title("기업 규모별 채용 비율", fontsize=16, fontweight="bold")
        self._save_chart(fig, "chart_company_size.png")

    # ── 8. 근무 지역별 분포 수평 막대그래프 ──
    def plot_location_distribution(self, location_data: pd.DataFrame):
        """근무 지역별 공고 수"""
        df = location_data.sort_values("건수", ascending=True)

        fig, ax = plt.subplots(figsize=self.figsize)
        colors = sns.color_palette("Greens_d", len(df))
        bars = ax.barh(df["지역"], df["건수"], color=colors)

        for bar, val in zip(bars, df["건수"]):
            ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                    f" {int(val)}", va="center", fontsize=10)

        ax.set_xlabel("공고 수", fontsize=12)
        ax.set_title("근무 지역별 채용공고 분포", fontsize=16, fontweight="bold")
        fig.tight_layout()
        self._save_chart(fig, "chart_location.png")

    def create_all(self, data: dict):
        """전체 기본 차트 생성 (8종)"""
        logger.info("=" * 40)
        logger.info("기본 차트 생성 시작 (총 8개)")
        logger.info("=" * 40)

        chart_map = {
            "tech_freq_df": self.plot_tech_stack_top15,
            "career_data": self.plot_career_ratio_donut,
            "salary_data": self.plot_salary_boxplot,
            "ratings_data": self.plot_company_ratings,
            "cert_data": self.plot_certificate_frequency,
            "trend_data": self.plot_monthly_trend,
            "size_data": self.plot_company_size_ratio,
            "location_data": self.plot_location_distribution,
        }

        for key, func in chart_map.items():
            if data.get(key) is not None:
                try:
                    func(data[key])
                except Exception as e:
                    logger.error(f"차트 생성 실패 ({key}): {e}")
            else:
                logger.warning(f"데이터 없음: {key}")

        logger.info("기본 차트 생성 완료")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    # 테스트
    test_tech = pd.DataFrame({
        "기술스택": ["Python", "C++", "ROS", "PyTorch", "OpenCV", "SLAM",
                   "LiDAR", "딥러닝", "Linux", "Docker", "TensorFlow",
                   "센서퓨전", "MATLAB", "Git", "CUDA"],
        "빈도": [85, 72, 65, 58, 52, 45, 40, 38, 35, 30, 28, 25, 22, 20, 18],
        "비율(%)": [85, 72, 65, 58, 52, 45, 40, 38, 35, 30, 28, 25, 22, 20, 18],
    })

    viz = ChartVisualizer()
    viz.plot_tech_stack_top15(test_tech)

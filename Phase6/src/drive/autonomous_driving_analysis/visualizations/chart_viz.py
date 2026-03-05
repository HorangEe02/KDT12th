"""
=============================================================
기본 차트 시각화 모듈 (matplotlib + seaborn)
=============================================================
10종 기본 정적 차트 생성
=============================================================
"""

import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib import rcParams
from matplotlib.patches import Patch
import seaborn as sns

from config.settings import OUTPUTS_CHARTS_DIR, KOREAN_FONT_CANDIDATES, KEYWORD_COLOR_MAP

# 한글 폰트 설정
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
sns.set_palette("husl")
setup_korean_font()


class ChartVisualizer:
    """기본 정적 차트 시각화 (10종)"""

    def __init__(self, save_dir: str = None):
        self.save_dir = save_dir or OUTPUTS_CHARTS_DIR
        os.makedirs(self.save_dir, exist_ok=True)

    def _save(self, fig, filename):
        path = os.path.join(self.save_dir, filename)
        fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        print(f"  📊 저장: {path}")

    def plot_tech_stack_bar(self, tech_freq_df: pd.DataFrame):
        """1. 기술스택 TOP 15 수평 막대그래프"""
        if tech_freq_df is None or tech_freq_df.empty:
            print("  ⚠️ 기술스택 데이터 없음")
            return

        df = tech_freq_df.head(15).iloc[::-1]
        name_col = df.columns[0]
        freq_col = df.columns[1]

        fig, ax = plt.subplots(figsize=(12, 8))
        colors = plt.cm.Blues(np.linspace(0.3, 0.9, len(df)))
        bars = ax.barh(df[name_col], df[freq_col], color=colors)

        for bar, val in zip(bars, df[freq_col]):
            ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                    str(int(val)), va="center", fontsize=10, fontweight="bold")

        ax.set_xlabel("빈도수", fontsize=12)
        ax.set_title("자율주행/모빌리티 채용 기술스택 TOP 15", fontsize=16, fontweight="bold", pad=15)
        self._save(fig, "chart_tech_stack_top15.png")

    def plot_career_donut(self, career_data: pd.DataFrame):
        """2. 경력/신입 비율 도넛차트"""
        if career_data is None or career_data.empty:
            print("  ⚠️ 경력 데이터 없음")
            return

        name_col = career_data.columns[0]
        count_col = career_data.columns[1]

        fig, ax = plt.subplots(figsize=(10, 8))
        colors = sns.color_palette("Set2", len(career_data))
        wedges, texts, autotexts = ax.pie(
            career_data[count_col], labels=career_data[name_col],
            autopct="%1.1f%%", colors=colors, startangle=90,
            wedgeprops=dict(width=0.4, edgecolor="white"),
            pctdistance=0.8,
        )
        total = career_data[count_col].sum()
        ax.text(0, 0, f"총 {int(total)}건", ha="center", va="center",
                fontsize=16, fontweight="bold")
        ax.set_title("경력/신입 채용 비율", fontsize=16, fontweight="bold", pad=15)
        self._save(fig, "chart_career_donut.png")

    def plot_salary_boxplot(self, salary_data: pd.DataFrame):
        """3. 기업별 연봉 박스플롯"""
        if salary_data is None or salary_data.empty:
            print("  ⚠️ 연봉 데이터 없음")
            return

        company_col = [c for c in salary_data.columns if "기업" in c or "회사" in c]
        salary_col = [c for c in salary_data.columns if "연봉" in c]
        if not company_col or not salary_col:
            return

        fig, ax = plt.subplots(figsize=(14, 8))
        sns.boxplot(data=salary_data, x=company_col[0], y=salary_col[0], ax=ax, palette="Set3")
        ax.set_xlabel("기업명", fontsize=12)
        ax.set_ylabel("연봉 (만원)", fontsize=12)
        ax.set_title("자율주행/모빌리티 기업별 연봉 분포", fontsize=16, fontweight="bold", pad=15)
        plt.xticks(rotation=45, ha="right")
        self._save(fig, "chart_salary_boxplot.png")

    def plot_company_ratings_grouped_bar(self, ratings_data: pd.DataFrame):
        """4. 기업 평점 항목별 그룹 막대그래프"""
        if ratings_data is None or ratings_data.empty:
            print("  ⚠️ 평점 데이터 없음")
            return

        fig, ax = plt.subplots(figsize=(14, 8))
        rating_cols = [c for c in ratings_data.columns if "평점" in c and c != "전체평점"]
        if not rating_cols:
            rating_cols = ["총점", "승진기회", "워라밸", "급여", "사내문화", "경영진"]
            rating_cols = [c for c in rating_cols if c in ratings_data.columns]

        company_col = [c for c in ratings_data.columns if "기업" in c]
        if not company_col or not rating_cols:
            return

        ratings_data[rating_cols] = ratings_data[rating_cols].apply(pd.to_numeric, errors="coerce")
        ratings_data.set_index(company_col[0])[rating_cols].plot(kind="bar", ax=ax, width=0.8)
        ax.axhline(y=3.0, color="red", linestyle="--", alpha=0.5, label="3.0 기준선")
        ax.set_ylabel("평점 (5.0 만점)", fontsize=12)
        ax.set_title("자율주행/모빌리티 기업 평점 항목별 비교", fontsize=16, fontweight="bold", pad=15)
        ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
        plt.xticks(rotation=45, ha="right")
        self._save(fig, "chart_company_ratings.png")

    def plot_certificate_bar(self, cert_freq_df: pd.DataFrame):
        """5. 자격증/우대사항 빈도 수평 막대그래프"""
        if cert_freq_df is None or cert_freq_df.empty:
            print("  ⚠️ 자격증 데이터 없음")
            return

        df = cert_freq_df.head(10).iloc[::-1]
        name_col = df.columns[0]
        freq_col = df.columns[1]

        fig, ax = plt.subplots(figsize=(10, 6))
        colors = sns.color_palette("YlOrRd_r", len(df))
        bars = ax.barh(df[name_col], df[freq_col], color=colors)

        for bar, val in zip(bars, df[freq_col]):
            ax.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height() / 2,
                    str(int(val)), va="center", fontsize=10, fontweight="bold")

        ax.set_xlabel("빈도수", fontsize=12)
        ax.set_title("자격증/우대사항 빈도 TOP 10", fontsize=16, fontweight="bold", pad=15)
        self._save(fig, "chart_certificate_freq.png")

    def plot_monthly_trend_line(self, monthly_data: pd.DataFrame):
        """6. 월별 채용공고 수 추이 라인차트"""
        if monthly_data is None or monthly_data.empty:
            print("  ⚠️ 월별 데이터 없음")
            return

        fig, ax = plt.subplots(figsize=(12, 6))
        if isinstance(monthly_data, pd.Series):
            monthly_data.plot(kind="line", ax=ax, color="#0891B2", linewidth=2, marker="o")
        else:
            x_col, y_col = monthly_data.columns[0], monthly_data.columns[1]
            ax.plot(monthly_data[x_col], monthly_data[y_col], color="#0891B2",
                    linewidth=2, marker="o", markersize=6)

        ax.set_xlabel("월", fontsize=12)
        ax.set_ylabel("채용 공고 수", fontsize=12)
        ax.set_title("월별 자율주행/모빌리티 채용공고 수 추이", fontsize=16, fontweight="bold", pad=15)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        self._save(fig, "chart_monthly_trend.png")

    def plot_company_size_pie(self, size_data: pd.DataFrame):
        """7. 기업 규모별 채용 비율 파이차트"""
        if size_data is None or size_data.empty:
            print("  ⚠️ 기업규모 데이터 없음")
            return

        name_col = size_data.columns[0]
        count_col = size_data.columns[1]

        fig, ax = plt.subplots(figsize=(8, 8))
        colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4"]
        ax.pie(size_data[count_col], labels=size_data[name_col], autopct="%1.1f%%",
               colors=colors[:len(size_data)], startangle=90, explode=[0.03] * len(size_data))
        ax.set_title("기업 규모별 채용 비율", fontsize=16, fontweight="bold", pad=15)
        self._save(fig, "chart_company_size_pie.png")

    def plot_location_bar(self, location_data: pd.DataFrame):
        """8. 근무 지역별 분포 수평 막대그래프"""
        if location_data is None or location_data.empty:
            print("  ⚠️ 지역 데이터 없음")
            return

        df = location_data.head(10).iloc[::-1]
        name_col = df.columns[0]
        count_col = df.columns[1]

        fig, ax = plt.subplots(figsize=(10, 6))
        colors = plt.cm.Greens(np.linspace(0.3, 0.9, len(df)))
        ax.barh(df[name_col], df[count_col], color=colors)
        ax.set_xlabel("채용 공고 수", fontsize=12)
        ax.set_title("근무 지역별 자율주행/모빌리티 채용 분포", fontsize=16, fontweight="bold", pad=15)
        self._save(fig, "chart_location.png")

    def plot_education_bar(self, education_data: pd.DataFrame):
        """9. 학력 조건 분포 막대그래프 (자율주행/모빌리티 특화)"""
        if education_data is None or education_data.empty:
            print("  ⚠️ 학력 데이터 없음")
            return

        name_col = education_data.columns[0]
        count_col = education_data.columns[1]

        fig, ax = plt.subplots(figsize=(8, 6))
        colors = ["#FF9F1C", "#2EC4B6", "#E71D36", "#011627"]
        bars = ax.bar(education_data[name_col], education_data[count_col],
                      color=colors[:len(education_data)], width=0.6, edgecolor="white")

        for bar, val in zip(bars, education_data[count_col]):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                    str(int(val)), ha="center", fontsize=12, fontweight="bold")

        ax.set_ylabel("채용 공고 수", fontsize=12)
        ax.set_title("학력 조건 분포 (자율주행/모빌리티 특화)", fontsize=16, fontweight="bold", pad=15)
        self._save(fig, "chart_education.png")

    def plot_domain_pie(self, domain_data: pd.DataFrame):
        """10. 자율주행 도메인별 채용 분포 파이차트 (자율주행/모빌리티 특화)"""
        if domain_data is None or domain_data.empty:
            print("  ⚠️ 자율주행 도메인 데이터 없음")
            return

        name_col = domain_data.columns[0]
        count_col = domain_data.columns[1]

        fig, ax = plt.subplots(figsize=(9, 8))
        colors = sns.color_palette("Set2", len(domain_data))
        wedges, texts, autotexts = ax.pie(
            domain_data[count_col], labels=domain_data[name_col],
            autopct="%1.1f%%", colors=colors, startangle=90,
        )
        ax.set_title("자율주행/모빌리티 도메인별 채용 분포", fontsize=16, fontweight="bold", pad=15)
        self._save(fig, "chart_domain_pie.png")

    def plot_keyword_distribution(self, blog_df: pd.DataFrame = None,
                                   news_df: pd.DataFrame = None):
        """11. 검색 키워드별 수집 현황 (블로그 + 뉴스, 키워드별 색상 통일)"""
        fig, axes = plt.subplots(1, 2, figsize=(20, 10))

        for ax, df, title, data_type in [
            (axes[0], blog_df, "블로그 키워드별 수집 현황", "blog"),
            (axes[1], news_df, "뉴스 키워드별 수집 현황", "news"),
        ]:
            if df is None or df.empty or "검색키워드" not in df.columns:
                ax.text(0.5, 0.5, f"{title}\n(데이터 없음)", ha="center", va="center",
                        fontsize=14, transform=ax.transAxes)
                ax.set_title(title, fontsize=14, fontweight="bold")
                continue

            counts = df["검색키워드"].value_counts()
            keywords = counts.index.tolist()
            values = counts.values.tolist()

            # KEYWORD_COLOR_MAP에서 색상 가져오기 (없으면 기본 색상)
            colors = [KEYWORD_COLOR_MAP.get(kw, "#888888") for kw in keywords]

            bars = ax.barh(range(len(keywords)), values, color=colors)
            ax.set_yticks(range(len(keywords)))
            ax.set_yticklabels(keywords, fontsize=9)
            ax.invert_yaxis()
            ax.set_xlabel("수집 건수", fontsize=11)
            ax.set_title(title, fontsize=14, fontweight="bold")

            for bar, val in zip(bars, values):
                ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                        str(val), va="center", fontsize=9, fontweight="bold")

        fig.suptitle("Naver 검색 키워드별 수집 현황", fontsize=18, fontweight="bold", y=1.02)
        plt.tight_layout()
        self._save(fig, "chart_keyword_distribution.png")

    def generate_all(self, data_dict: dict):
        """전체 기본 차트 생성"""
        print("=" * 60)
        print("🎨 기본 차트 시각화 생성")
        print("=" * 60)

        if data_dict.get("tech_freq") is not None:
            self.plot_tech_stack_bar(data_dict["tech_freq"])
        if data_dict.get("career") is not None:
            self.plot_career_donut(data_dict["career"])
        if data_dict.get("salary") is not None:
            self.plot_salary_boxplot(data_dict["salary"])
        if data_dict.get("ratings") is not None:
            self.plot_company_ratings_grouped_bar(data_dict["ratings"])
        if data_dict.get("cert_freq") is not None:
            self.plot_certificate_bar(data_dict["cert_freq"])
        if data_dict.get("monthly") is not None:
            self.plot_monthly_trend_line(data_dict["monthly"])
        if data_dict.get("company_size") is not None:
            self.plot_company_size_pie(data_dict["company_size"])
        if data_dict.get("location") is not None:
            self.plot_location_bar(data_dict["location"])
        if data_dict.get("education") is not None:
            self.plot_education_bar(data_dict["education"])
        if data_dict.get("domain") is not None:
            self.plot_domain_pie(data_dict["domain"])
        # 키워드 분포 차트 (키워드별 색상 통일)
        if data_dict.get("blog_df") is not None or data_dict.get("news_df") is not None:
            self.plot_keyword_distribution(data_dict.get("blog_df"), data_dict.get("news_df"))

        print("\n✅ 기본 차트 생성 완료!")

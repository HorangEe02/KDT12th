"""
=============================================================
크로스 분석 시각화 모듈
=============================================================
여러 데이터 소스를 결합한 통합 인사이트 차트 4종 생성
- 기술스택 카테고리 도넛
- 기업 분야별 평균 별점
- 재직상태별 별점 박스플롯
- 면접 지원직무 분포
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
    DATA_PROCESSED_DIR, OUTPUTS_CHARTS_DIR,
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

# 기술스택 카테고리 매핑
TECH_CATEGORIES = {
    "프로그래밍 언어": ["Python", "R", "Java", "C++", "JavaScript"],
    "AI/ML 프레임워크": ["PyTorch", "TensorFlow", "Keras", "scikit-learn",
                        "딥러닝", "머신러닝"],
    "데이터/통계": ["pandas", "NumPy", "SciPy", "SQL", "MongoDB", "PostgreSQL",
                    "SPSS", "SAS", "통계분석", "생존분석"],
    "자율주행 특화": ["LiDAR", "RADAR", "SLAM", "센서퓨전", "AUTOSAR",
                      "V2X", "CAN", "포인트클라우드", "HD맵", "CARLA", "시뮬레이션"],
    "인프라/DevOps": ["Docker", "Kubernetes", "AWS", "GCP", "Azure",
                       "Git", "Linux", "MLOps", "Kubeflow", "MLflow"],
    "웹/기타": ["React", "FastAPI", "Django", "컴퓨터비전", "자연어처리", "NLP",
                "논문", "SCI", "특허"],
}


class CrossAnalysisVisualizer:
    """크로스 분석 시각화"""

    def __init__(self, processed_data_path: str = None):
        self.data_path = processed_data_path or DATA_PROCESSED_DIR
        self.data = {}
        self._load_data()

    def _load_data(self):
        csv_files = glob.glob(os.path.join(self.data_path, "*.csv"))
        for f in csv_files:
            name = os.path.basename(f).replace("_processed.csv", "").replace(".csv", "")
            try:
                self.data[name] = pd.read_csv(f, encoding="utf-8-sig")
            except Exception:
                pass

    def _find_df(self, *keywords):
        for name, df in self.data.items():
            if any(kw in name for kw in keywords):
                return df
        return None

    def _save(self, fig, filename):
        path = os.path.join(OUTPUTS_CHARTS_DIR, filename)
        fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        print(f"    -> {filename}")

    # ─────────────────────────────────────────
    # 1. 기술스택 카테고리 도넛
    # ─────────────────────────────────────────
    def plot_tech_category_donut(self):
        tech_df = self._find_df("tech_stack")
        if tech_df is None or tech_df.empty:
            print("    ⚠️ 기술스택 데이터 없음")
            return

        name_col, freq_col = tech_df.columns[0], tech_df.columns[1]
        tech_dict = dict(zip(tech_df[name_col].astype(str), tech_df[freq_col]))

        cat_sums = {}
        for cat, techs in TECH_CATEGORIES.items():
            total = sum(tech_dict.get(t, 0) for t in techs)
            if total > 0:
                cat_sums[cat] = total

        if not cat_sums:
            return

        labels = list(cat_sums.keys())
        values = list(cat_sums.values())

        fig, ax = plt.subplots(figsize=(9, 9))
        colors = sns.color_palette("Set2", len(labels))
        wedges, texts, autotexts = ax.pie(
            values, labels=labels, autopct="%1.1f%%",
            colors=colors, startangle=90, pctdistance=0.78,
            wedgeprops=dict(width=0.45, edgecolor="white", linewidth=2))
        for t in autotexts:
            t.set_fontsize(10)
            t.set_fontweight("bold")
        ax.text(0, 0, "기술스택\n카테고리", ha="center", va="center",
                fontsize=13, fontweight="bold", color="#333")
        ax.set_title("기술스택 카테고리 분포", fontsize=15, fontweight="bold")
        fig.tight_layout()
        self._save(fig, "cross_01_tech_category_donut.png")

    # ─────────────────────────────────────────
    # 2. 기업 분야별 평균 별점 (그룹 막대)
    # ─────────────────────────────────────────
    def plot_field_avg_rating(self):
        review_df = self._find_df("리뷰", "review")
        if review_df is None or "분야" not in review_df.columns or "별점" not in review_df.columns:
            print("    ⚠️ 리뷰 분야/별점 데이터 없음")
            return

        df = review_df.copy()
        df["별점"] = pd.to_numeric(df["별점"], errors="coerce")
        df = df.dropna(subset=["별점", "분야"])

        # 분야에서 카테고리 추출 (스타트업_의료영상 → 의료영상)
        df["세부분야"] = df["분야"].str.split("_").str[-1]
        grouped = df.groupby("세부분야")["별점"].agg(["mean", "count"]).sort_values("mean", ascending=True)
        grouped = grouped[grouped["count"] >= 2]  # 최소 2건

        if grouped.empty:
            return

        fig, ax = plt.subplots(figsize=(9, max(5, len(grouped) * 0.8)))
        colors = plt.cm.RdYlGn(np.linspace(0.2, 0.8, len(grouped)))
        bars = ax.barh(grouped.index, grouped["mean"], color=colors, edgecolor="white")
        ax.axvline(x=3.0, color="red", linestyle="--", alpha=0.4, label="3.0 기준")
        ax.set_xlim(0, 5.5)
        for i, (idx, row) in enumerate(grouped.iterrows()):
            ax.text(row["mean"] + 0.05, i,
                    f'{row["mean"]:.1f} ({int(row["count"])}건)',
                    va="center", fontsize=10, fontweight="bold")
        ax.set_xlabel("평균 별점")
        ax.set_title("기업 분야별 평균 별점", fontsize=15, fontweight="bold")
        ax.legend(fontsize=9)
        fig.tight_layout()
        self._save(fig, "cross_02_field_avg_rating.png")

    # ─────────────────────────────────────────
    # 3. 재직상태별 별점 분포 (박스플롯)
    # ─────────────────────────────────────────
    def plot_status_rating_boxplot(self):
        review_df = self._find_df("리뷰", "review")
        if review_df is None or "재직상태" not in review_df.columns or "별점" not in review_df.columns:
            print("    ⚠️ 리뷰 재직상태/별점 데이터 없음")
            return

        df = review_df.copy()
        df["별점"] = pd.to_numeric(df["별점"], errors="coerce")
        df = df.dropna(subset=["별점"])
        valid = df[df["재직상태"].isin(["현직원", "전직원"])]
        if valid.empty:
            return

        fig, ax = plt.subplots(figsize=(8, 6))
        palette = {"현직원": "#4ECDC4", "전직원": "#FF6B6B"}
        sns.boxplot(data=valid, x="재직상태", y="별점", palette=palette, ax=ax,
                    width=0.5, linewidth=1.5)
        sns.stripplot(data=valid, x="재직상태", y="별점", color="black", alpha=0.3,
                      size=5, jitter=True, ax=ax)

        # 평균값 표시
        for i, status in enumerate(["현직원", "전직원"]):
            subset = valid[valid["재직상태"] == status]["별점"]
            if len(subset) > 0:
                mean_val = subset.mean()
                ax.text(i, mean_val + 0.15, f"평균: {mean_val:.2f}",
                        ha="center", fontsize=10, fontweight="bold", color="#333")

        ax.set_ylim(0, 5.5)
        ax.set_ylabel("별점 (5점 만점)")
        ax.set_xlabel("")
        ax.set_title("재직상태별 별점 분포", fontsize=15, fontweight="bold")
        fig.tight_layout()
        self._save(fig, "cross_03_status_rating_boxplot.png")

    # ─────────────────────────────────────────
    # 4. 면접 지원직무 분포 (수평 막대)
    # ─────────────────────────────────────────
    def plot_interview_position(self):
        interview_df = self._find_df("면접", "interview")
        if interview_df is None or "지원직무" not in interview_df.columns:
            print("    ⚠️ 면접 지원직무 데이터 없음")
            return

        # 지원직무 파싱: "금융/재무\n         / \n        주임/계장" → "금융/재무"
        def parse_position(s):
            s = str(s).strip()
            # 첫 줄(직무 카테고리)만 추출
            first_line = s.split("\n")[0].strip()
            return first_line if first_line and first_line != "nan" else None

        positions = interview_df["지원직무"].apply(parse_position).dropna()
        counts = positions.value_counts().head(15)
        if counts.empty:
            return

        fig, ax = plt.subplots(figsize=(9, max(5, len(counts) * 0.5)))
        colors = plt.cm.Purples(np.linspace(0.3, 0.9, len(counts)))[::-1]
        ax.barh(counts.index[::-1], counts.values[::-1], color=colors)
        for i, val in enumerate(counts.values[::-1]):
            ax.text(val + 0.2, i, str(val), va="center", fontsize=10, fontweight="bold")
        ax.set_xlabel("면접후기 수")
        ax.set_title("면접 지원직무 분포", fontsize=15, fontweight="bold")
        fig.tight_layout()
        self._save(fig, "cross_04_interview_position.png")

    # ─────────────────────────────────────────
    # 전체 생성
    # ─────────────────────────────────────────
    def generate_all(self):
        print("\n  📊 크로스 분석 차트 생성 중...")
        self.plot_tech_category_donut()
        self.plot_field_avg_rating()
        self.plot_status_rating_boxplot()
        self.plot_interview_position()
        print("  ✅ 크로스 분석 4종 완료")


if __name__ == "__main__":
    viz = CrossAnalysisVisualizer()
    viz.generate_all()

"""
=============================================================
잡플래닛 심층 분석 시각화 모듈
=============================================================
리뷰/면접후기의 미시각화 컬럼(직종, 위치, 면접경로, 지원직무)을
활용한 심층 분석 차트 6종 생성
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


class JobPlanetDeepVisualizer:
    """잡플래닛 리뷰/면접 심층 분석 시각화"""

    def __init__(self, processed_data_path: str = None):
        self.data_path = processed_data_path or DATA_PROCESSED_DIR
        self.review_df = None
        self.interview_df = None
        self._load_data()

    def _load_data(self):
        csv_files = glob.glob(os.path.join(self.data_path, "*.csv"))
        for f in csv_files:
            name = os.path.basename(f).lower()
            try:
                df = pd.read_csv(f, encoding="utf-8-sig")
                if "리뷰" in name or "review" in name:
                    self.review_df = df
                elif "면접" in name or "interview" in name:
                    self.interview_df = df
            except Exception:
                pass

    def _save(self, fig, filename):
        path = os.path.join(OUTPUTS_CHARTS_DIR, filename)
        fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        print(f"    -> {filename}")

    # ─────────────────────────────────────────
    # 1. 직종별 리뷰 분포 (수평 막대)
    # ─────────────────────────────────────────
    def plot_job_type_distribution(self):
        if self.review_df is None or "직종" not in self.review_df.columns:
            print("    ⚠️ 리뷰 직종 데이터 없음")
            return
        counts = self.review_df["직종"].value_counts()
        fig, ax = plt.subplots(figsize=(9, 6))
        colors = plt.cm.Paired(np.linspace(0.1, 0.9, len(counts)))
        ax.barh(counts.index[::-1], counts.values[::-1], color=colors[:len(counts)])
        for i, val in enumerate(counts.values[::-1]):
            ax.text(val + 0.3, i, str(val), va="center", fontsize=14, fontweight="bold")
        ax.set_xlabel("리뷰 수", fontsize=16)
        ax.set_title("직종별 리뷰 분포", fontsize=20, fontweight="bold")
        ax.tick_params(axis='both', labelsize=14)
        fig.tight_layout()
        self._save(fig, "jobplanet_01_job_type_dist.png")

    # ─────────────────────────────────────────
    # 2. 지역별 리뷰 분포 (수평 막대)
    # ─────────────────────────────────────────
    def plot_location_distribution(self):
        if self.review_df is None or "위치" not in self.review_df.columns:
            print("    ⚠️ 리뷰 위치 데이터 없음")
            return
        counts = self.review_df["위치"].value_counts()
        fig, ax = plt.subplots(figsize=(9, 6))
        colors = plt.cm.Set2(np.linspace(0.1, 0.9, len(counts)))
        ax.barh(counts.index[::-1], counts.values[::-1], color=colors[:len(counts)])
        for i, val in enumerate(counts.values[::-1]):
            ax.text(val + 0.3, i, str(val), va="center", fontsize=14, fontweight="bold")
        ax.set_xlabel("리뷰 수", fontsize=16)
        ax.set_title("지역별 리뷰 분포", fontsize=20, fontweight="bold")
        ax.tick_params(axis='both', labelsize=14)
        fig.tight_layout()
        self._save(fig, "jobplanet_02_location_dist.png")

    # ─────────────────────────────────────────
    # 3. 면접경로 분포 (파이 차트)
    # ─────────────────────────────────────────
    def plot_interview_route(self):
        if self.interview_df is None or "면접경로" not in self.interview_df.columns:
            print("    ⚠️ 면접경로 데이터 없음")
            return
        counts = self.interview_df["면접경로"].dropna().value_counts()
        if counts.empty:
            return
        fig, ax = plt.subplots(figsize=(10, 8))
        colors = sns.color_palette("Set3", len(counts))
        wedges, texts, autotexts = ax.pie(
            counts.values, labels=None, autopct="%1.1f%%",
            colors=colors, startangle=90, pctdistance=0.80,
            textprops={"fontsize": 14, "fontweight": "bold"})

        ax.legend(
            wedges, counts.index,
            loc="center left", bbox_to_anchor=(1.0, 0.5),
            fontsize=14, frameon=False,
        )

        ax.set_title("면접경로 분포", fontsize=18, fontweight="bold")
        fig.tight_layout()
        self._save(fig, "jobplanet_03_interview_route.png")

    # ─────────────────────────────────────────
    # 4. 기업별 면접난이도 히트맵
    # ─────────────────────────────────────────
    def plot_difficulty_heatmap(self):
        if self.interview_df is None:
            print("    ⚠️ 면접후기 데이터 없음")
            return
        if "기업명" not in self.interview_df.columns or "면접난이도" not in self.interview_df.columns:
            return
        ct = pd.crosstab(self.interview_df["기업명"], self.interview_df["면접난이도"])
        order = ["매우 쉬움", "쉬움", "보통", "어려움", "매우 어려움"]
        ct = ct.reindex(columns=[c for c in order if c in ct.columns], fill_value=0)
        if ct.empty:
            return
        fig, ax = plt.subplots(figsize=(10, max(6, len(ct) * 0.6)))
        sns.heatmap(ct, annot=True, fmt="d", cmap="YlOrRd", linewidths=0.5, ax=ax,
                    annot_kws={"fontsize": 13, "fontweight": "bold"})
        ax.set_title("기업별 면접난이도 분포", fontsize=20, fontweight="bold")
        ax.set_ylabel("")
        ax.tick_params(axis='both', labelsize=14)
        fig.tight_layout()
        self._save(fig, "jobplanet_04_difficulty_heatmap.png")

    # ─────────────────────────────────────────
    # 5. 기업별 직종 분포 (누적 수평 막대)
    # ─────────────────────────────────────────
    def plot_company_job_type_stacked(self):
        if self.review_df is None:
            print("    ⚠️ 리뷰 데이터 없음")
            return
        if "기업명" not in self.review_df.columns or "직종" not in self.review_df.columns:
            return
        ct = pd.crosstab(self.review_df["기업명"], self.review_df["직종"])
        if ct.empty:
            return
        fig, ax = plt.subplots(figsize=(10, max(6, len(ct) * 0.6)))
        ct.plot(kind="barh", stacked=True, ax=ax,
                colormap="Set3", edgecolor="white", linewidth=0.5)
        ax.set_xlabel("리뷰 수", fontsize=16)
        ax.set_title("기업별 직종 분포", fontsize=20, fontweight="bold")
        ax.legend(title="직종", bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=13)
        ax.tick_params(axis='both', labelsize=14)
        fig.tight_layout()
        self._save(fig, "jobplanet_05_company_jobtype_stacked.png")

    # ─────────────────────────────────────────
    # 6. 별점 vs 면접난이도 산점도
    # ─────────────────────────────────────────
    def plot_rating_vs_difficulty(self):
        if self.review_df is None or self.interview_df is None:
            print("    ⚠️ 리뷰 또는 면접후기 데이터 없음")
            return

        # 기업별 평균 별점
        if "별점" not in self.review_df.columns or "기업명" not in self.review_df.columns:
            return
        avg_rating = self.review_df.groupby("기업명")["별점"].apply(
            lambda x: pd.to_numeric(x, errors="coerce").mean()
        ).dropna()

        # 면접난이도 수치 변환
        diff_map = {"매우 쉬움": 1, "쉬움": 2, "보통": 3, "어려움": 4, "매우 어려움": 5}
        if "면접난이도" not in self.interview_df.columns or "기업명" not in self.interview_df.columns:
            return
        iv = self.interview_df.copy()
        iv["난이도_수치"] = iv["면접난이도"].map(diff_map)
        avg_diff = iv.groupby("기업명")["난이도_수치"].mean().dropna()

        # 공통 기업
        common = avg_rating.index.intersection(avg_diff.index)
        if len(common) < 2:
            print("    ⚠️ 공통 기업이 부족합니다")
            return

        fig, ax = plt.subplots(figsize=(9, 7))
        x = avg_diff.loc[common]
        y = avg_rating.loc[common]
        ax.scatter(x, y, s=120, c="#E74C3C", edgecolors="white", linewidth=1.5, zorder=3)
        for company in common:
            ax.annotate(company, (x[company], y[company]),
                        textcoords="offset points", xytext=(8, 4), fontsize=13)
        ax.set_xlabel("평균 면접난이도 (1=매우 쉬움 ~ 5=매우 어려움)", fontsize=15)
        ax.set_ylabel("평균 별점 (5점 만점)", fontsize=15)
        ax.set_title("기업별 별점 vs 면접난이도", fontsize=20, fontweight="bold")
        ax.tick_params(axis='both', labelsize=14)
        ax.set_xlim(0.5, 5.5)
        ax.set_ylim(0.5, 5.5)
        ax.axhline(y=3.0, color="gray", linestyle="--", alpha=0.4)
        ax.axvline(x=3.0, color="gray", linestyle="--", alpha=0.4)
        fig.tight_layout()
        self._save(fig, "jobplanet_06_rating_vs_difficulty.png")

    # ─────────────────────────────────────────
    # 전체 생성
    # ─────────────────────────────────────────
    def generate_all(self):
        print("\n  📊 잡플래닛 심층 분석 차트 생성 중...")
        self.plot_job_type_distribution()
        self.plot_location_distribution()
        self.plot_interview_route()
        self.plot_difficulty_heatmap()
        self.plot_company_job_type_stacked()
        self.plot_rating_vs_difficulty()
        print("  ✅ 잡플래닛 심층 분석 6종 완료")


if __name__ == "__main__":
    viz = JobPlanetDeepVisualizer()
    viz.generate_all()

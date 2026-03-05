"""
=============================================================
콘텐츠 트렌드 분석 시각화 모듈
=============================================================
블로그/뉴스의 미시각화 컬럼(블로거명, 원본링크 도메인, 게시일자)을
활용한 트렌드 분석 차트 5종 생성
=============================================================
"""

import os
import re
import glob
from urllib.parse import urlparse

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


class ContentTrendVisualizer:
    """블로그/뉴스 콘텐츠 트렌드 분석 시각화"""

    def __init__(self, processed_data_path: str = None):
        self.data_path = processed_data_path or DATA_PROCESSED_DIR
        self.blog_df = None
        self.news_df = None
        self._load_data()

    def _load_data(self):
        csv_files = glob.glob(os.path.join(self.data_path, "*.csv"))
        for f in csv_files:
            name = os.path.basename(f).lower()
            try:
                df = pd.read_csv(f, encoding="utf-8-sig")
                if ("blog" in name or "블로그" in name) and "검색키워드" in df.columns:
                    self.blog_df = df
                elif ("news" in name or "뉴스" in name) and "검색키워드" in df.columns:
                    self.news_df = df
            except Exception:
                pass

    def _save(self, fig, filename):
        path = os.path.join(OUTPUTS_CHARTS_DIR, filename)
        fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        print(f"    -> {filename}")

    def _parse_dates(self, df):
        """게시일자 파싱하여 datetime 반환"""
        if df is None or "게시일자" not in df.columns:
            return None
        return pd.to_datetime(df["게시일자"], errors="coerce")

    # ─────────────────────────────────────────
    # 1. 블로그 vs 뉴스 월별 비교 (이중 라인)
    # ─────────────────────────────────────────
    def plot_blog_vs_news_monthly(self):
        blog_dates = self._parse_dates(self.blog_df)
        news_dates = self._parse_dates(self.news_df)
        if blog_dates is None and news_dates is None:
            print("    ⚠️ 게시일자 데이터 없음")
            return

        fig, ax = plt.subplots(figsize=(12, 5))

        # 최근 12개월 범위
        end_month = pd.Timestamp.now().to_period("M")
        start_month = end_month - 11
        all_months = pd.period_range(start_month, end_month, freq="M")
        labels = [f"{m.year}-{m.month:02d}" for m in all_months]

        for dates, label, color, marker in [
            (blog_dates, "블로그", "#3498DB", "o"),
            (news_dates, "뉴스", "#E74C3C", "s"),
        ]:
            if dates is None:
                continue
            periods = dates.dropna().dt.to_period("M")
            counts = periods.value_counts().sort_index()
            vals = [int(counts.get(m, 0)) for m in all_months]
            ax.plot(labels, vals, marker=marker, label=label, color=color,
                    linewidth=2, markersize=6)

        ax.set_xlabel("월", fontsize=16)
        ax.set_ylabel("게시 건수", fontsize=16)
        ax.set_title("블로그 vs 뉴스 월별 콘텐츠 추이 (최근 12개월)", fontsize=20, fontweight="bold")
        ax.legend(fontsize=14)
        ax.tick_params(axis='y', labelsize=14)
        plt.xticks(rotation=45, ha="right", fontsize=13)
        fig.tight_layout()
        self._save(fig, "content_01_blog_vs_news_monthly.png")

    # ─────────────────────────────────────────
    # 2. 뉴스 매체 분포 TOP 15 (수평 막대)
    # ─────────────────────────────────────────
    def plot_news_source_top15(self):
        if self.news_df is None or "원본링크" not in self.news_df.columns:
            print("    ⚠️ 뉴스 원본링크 데이터 없음")
            return

        def extract_domain(url):
            try:
                parsed = urlparse(str(url))
                domain = parsed.netloc
                if domain.startswith("www."):
                    domain = domain[4:]
                return domain
            except Exception:
                return None

        domains = self.news_df["원본링크"].apply(extract_domain).dropna()
        counts = domains.value_counts().head(15)
        if counts.empty:
            return

        fig, ax = plt.subplots(figsize=(10, 7))
        colors = plt.cm.Oranges(np.linspace(0.3, 0.9, len(counts)))[::-1]
        ax.barh(counts.index[::-1], counts.values[::-1], color=colors)
        for i, val in enumerate(counts.values[::-1]):
            ax.text(val + 0.3, i, str(val), va="center", fontsize=14, fontweight="bold")
        ax.set_xlabel("기사 수", fontsize=16)
        ax.set_title("뉴스 매체 분포 TOP 15", fontsize=20, fontweight="bold")
        ax.tick_params(axis='both', labelsize=14)
        fig.tight_layout()
        self._save(fig, "content_02_news_source_top15.png")

    # ─────────────────────────────────────────
    # 3. 활발 블로거 TOP 15 (수평 막대)
    # ─────────────────────────────────────────
    def plot_active_bloggers_top15(self):
        if self.blog_df is None or "블로거명" not in self.blog_df.columns:
            print("    ⚠️ 블로거명 데이터 없음")
            return

        counts = self.blog_df["블로거명"].value_counts().head(15)
        if counts.empty:
            return

        fig, ax = plt.subplots(figsize=(10, 7))
        colors = plt.cm.Blues(np.linspace(0.3, 0.9, len(counts)))[::-1]
        ax.barh(counts.index[::-1], counts.values[::-1], color=colors)
        for i, val in enumerate(counts.values[::-1]):
            ax.text(val + 0.1, i, str(val), va="center", fontsize=14, fontweight="bold")
        ax.set_xlabel("게시글 수", fontsize=16)
        ax.set_title("활발 블로거 TOP 15", fontsize=20, fontweight="bold")
        ax.tick_params(axis='both', labelsize=14)
        fig.tight_layout()
        self._save(fig, "content_03_active_bloggers_top15.png")

    # ─────────────────────────────────────────
    # 4. 키워드별 월별 히트맵
    # ─────────────────────────────────────────
    def plot_keyword_monthly_heatmap(self):
        if self.blog_df is None or "검색키워드" not in self.blog_df.columns:
            print("    ⚠️ 블로그 검색키워드 데이터 없음")
            return
        dates = self._parse_dates(self.blog_df)
        if dates is None:
            return

        df = self.blog_df.copy()
        df["월"] = dates.dt.to_period("M")
        df = df.dropna(subset=["월"])

        # 상위 키워드만 (TOP 10)
        top_kw = df["검색키워드"].value_counts().head(10).index.tolist()
        df_top = df[df["검색키워드"].isin(top_kw)]

        ct = pd.crosstab(df_top["검색키워드"], df_top["월"])
        # 최근 12개월만
        end_month = pd.Timestamp.now().to_period("M")
        start_month = end_month - 11
        all_months = pd.period_range(start_month, end_month, freq="M")
        ct = ct.reindex(columns=[m for m in all_months if m in ct.columns], fill_value=0)
        ct.columns = [f"{m.month}월" for m in ct.columns]

        if ct.empty:
            return

        fig, ax = plt.subplots(figsize=(14, max(6, len(ct) * 0.6)))
        sns.heatmap(ct, annot=True, fmt="d", cmap="YlGnBu", linewidths=0.5, ax=ax,
                    annot_kws={"fontsize": 13, "fontweight": "bold"})
        ax.set_title("검색키워드별 월별 블로그 게시 현황", fontsize=20, fontweight="bold")
        ax.set_ylabel("")
        ax.tick_params(axis='both', labelsize=14)
        fig.tight_layout()
        self._save(fig, "content_04_keyword_monthly_heatmap.png")

    # ─────────────────────────────────────────
    # 5. 요일별 게시 패턴 (그룹 막대)
    # ─────────────────────────────────────────
    def plot_weekday_pattern(self):
        blog_dates = self._parse_dates(self.blog_df)
        news_dates = self._parse_dates(self.news_df)
        if blog_dates is None and news_dates is None:
            print("    ⚠️ 게시일자 데이터 없음")
            return

        weekday_kr = ["월", "화", "수", "목", "금", "토", "일"]
        data = {}

        if blog_dates is not None:
            blog_wd = blog_dates.dropna().dt.dayofweek.value_counts().sort_index()
            data["블로그"] = [int(blog_wd.get(i, 0)) for i in range(7)]
        if news_dates is not None:
            news_wd = news_dates.dropna().dt.dayofweek.value_counts().sort_index()
            data["뉴스"] = [int(news_wd.get(i, 0)) for i in range(7)]

        if not data:
            return

        fig, ax = plt.subplots(figsize=(10, 6))
        x = np.arange(7)
        width = 0.35
        colors = {"블로그": "#3498DB", "뉴스": "#E74C3C"}
        offset = -width / 2 if len(data) > 1 else 0

        for i, (label, vals) in enumerate(data.items()):
            bars = ax.bar(x + offset + i * width, vals, width,
                          label=label, color=colors.get(label, "#999"),
                          edgecolor="white")
            for bar, val in zip(bars, vals):
                if val > 0:
                    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                            str(val), ha="center", fontsize=13, fontweight="bold")

        ax.set_xticks(x)
        ax.set_xticklabels(weekday_kr, fontsize=14)
        ax.set_ylabel("게시 건수", fontsize=16)
        ax.set_title("요일별 콘텐츠 게시 패턴", fontsize=20, fontweight="bold")
        ax.legend(fontsize=14)
        ax.tick_params(axis='y', labelsize=14)
        fig.tight_layout()
        self._save(fig, "content_05_weekday_pattern.png")

    # ─────────────────────────────────────────
    # 전체 생성
    # ─────────────────────────────────────────
    def generate_all(self):
        print("\n  📊 콘텐츠 트렌드 분석 차트 생성 중...")
        self.plot_blog_vs_news_monthly()
        self.plot_news_source_top15()
        self.plot_active_bloggers_top15()
        self.plot_keyword_monthly_heatmap()
        self.plot_weekday_pattern()
        print("  ✅ 콘텐츠 트렌드 분석 5종 완료")


if __name__ == "__main__":
    viz = ContentTrendVisualizer()
    viz.generate_all()

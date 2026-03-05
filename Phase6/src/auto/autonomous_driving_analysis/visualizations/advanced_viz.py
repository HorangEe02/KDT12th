"""
고급 시각화 모듈
히트맵, 레이더차트, 트리맵, 네트워크 그래프, 산점도+회귀선, 바이올린 플롯 등 8종
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
from config.settings import FONT_PATH, OUTPUT_CHARTS_DIR, TECH_CATEGORIES

logger = logging.getLogger(__name__)

try:
    import squarify
    SQUARIFY_AVAILABLE = True
except ImportError:
    SQUARIFY_AVAILABLE = False

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False

try:
    from scipy import stats as scipy_stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False


class AdvancedVisualizer:
    """고급 시각화 (8종)"""

    def __init__(self):
        self.output_dir = OUTPUT_CHARTS_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.dpi = 300
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

    def _save_chart(self, fig, filename: str):
        filepath = self.output_dir / filename
        fig.savefig(filepath, dpi=self.dpi, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        logger.info(f"고급 차트 저장: {filepath}")

    # ── 1. 기업×기술스택 히트맵 ──
    def plot_company_tech_heatmap(self, data: pd.DataFrame):
        """기업×기술스택 히트맵"""
        fig, ax = plt.subplots(figsize=(16, 10))
        sns.heatmap(data, annot=True, fmt=".0f", cmap="YlOrRd",
                    linewidths=0.5, ax=ax, cbar_kws={"label": "언급 빈도"})

        ax.set_xlabel("기술스택", fontsize=12)
        ax.set_ylabel("기업명", fontsize=12)
        ax.set_title("기업×기술스택 요구 현황 히트맵", fontsize=16, fontweight="bold")
        plt.xticks(rotation=45, ha="right")
        plt.yticks(rotation=0)
        fig.tight_layout()
        self._save_chart(fig, "adv_tech_heatmap.png")

    # ── 2. 기업별 종합 평가 레이더차트 ──
    def plot_company_radar(self, ratings_dict: dict):
        """기업별 레이더차트 (3~5개 기업 비교)"""
        categories = ["연봉", "워라밸", "성장성", "사내문화", "복지", "기술력"]
        num_cats = len(categories)
        angles = np.linspace(0, 2 * np.pi, num_cats, endpoint=False).tolist()
        angles += angles[:1]

        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))
        colors = ["#2196F3", "#F44336", "#4CAF50", "#FF9800", "#9C27B0"]

        for idx, (company, values) in enumerate(ratings_dict.items()):
            vals = list(values.values())[:num_cats]
            while len(vals) < num_cats:
                vals.append(0)
            vals += vals[:1]

            color = colors[idx % len(colors)]
            ax.plot(angles, vals, "o-", linewidth=2, label=company, color=color)
            ax.fill(angles, vals, alpha=0.15, color=color)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=11)
        ax.set_ylim(0, 5)
        ax.set_title("기업별 종합 평가 비교", fontsize=16, fontweight="bold", y=1.08)
        ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))
        fig.tight_layout()
        self._save_chart(fig, "adv_company_radar.png")

    # ── 3. 직무 분류 트리맵 ──
    def plot_job_treemap(self, job_categories: pd.DataFrame):
        """직무 분류 트리맵"""
        if not SQUARIFY_AVAILABLE:
            logger.warning("squarify 패키지가 필요합니다. pip install squarify")
            return

        fig, ax = plt.subplots(figsize=(14, 10))
        colors = sns.color_palette("Set2", len(job_categories))

        squarify.plot(
            sizes=job_categories["건수"],
            label=[f"{row['직무']}\n({row['건수']}건)" for _, row in job_categories.iterrows()],
            color=colors, alpha=0.8, ax=ax,
            text_kwargs={"fontsize": 10, "fontweight": "bold"}
        )

        ax.set_title("자율주행 분야 직무 분류 트리맵", fontsize=16, fontweight="bold")
        ax.axis("off")
        fig.tight_layout()
        self._save_chart(fig, "adv_job_treemap.png")

    # ── 4. 기술스택 네트워크 그래프 ──
    def plot_tech_network(self, co_occurrence: pd.DataFrame):
        """기술스택 동시 출현 네트워크 그래프"""
        if not NETWORKX_AVAILABLE:
            logger.warning("networkx 패키지가 필요합니다. pip install networkx")
            return

        G = nx.Graph()

        # 엣지 추가 (동시 출현 빈도 기반)
        for _, row in co_occurrence.iterrows():
            if row.get("빈도", 0) > 0:
                G.add_edge(row["기술1"], row["기술2"], weight=row["빈도"])

        if not G.nodes():
            logger.warning("네트워크 그래프 데이터가 비어있습니다.")
            return

        fig, ax = plt.subplots(figsize=(14, 14))
        pos = nx.spring_layout(G, k=2, iterations=50, seed=42)

        # 노드 크기: degree centrality 비례
        degrees = dict(G.degree(weight="weight"))
        node_sizes = [max(degrees.get(n, 1) * 50, 200) for n in G.nodes()]

        # 엣지 두께
        edge_weights = [G[u][v]["weight"] * 0.5 for u, v in G.edges()]

        nx.draw_networkx_edges(G, pos, width=edge_weights, alpha=0.3, edge_color="gray", ax=ax)
        nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color="#2196F3",
                               alpha=0.7, ax=ax)
        nx.draw_networkx_labels(G, pos, font_size=9, font_weight="bold", ax=ax)

        ax.set_title("자율주행 기술스택 생태계 네트워크", fontsize=16, fontweight="bold")
        ax.axis("off")
        fig.tight_layout()
        self._save_chart(fig, "adv_tech_network.png")

    # ── 5. 경력-연봉 산점도 + 회귀선 ──
    def plot_career_salary_scatter(self, data: pd.DataFrame):
        """경력-연봉 산점도 + 회귀선"""
        fig, ax = plt.subplots(figsize=(12, 8))

        # 경력 연수 컬럼 필요
        if "경력_년" not in data.columns:
            # 경력구분에서 숫자 추출 시도
            import re
            data = data.copy()
            def extract_years(text):
                nums = re.findall(r"(\d+)", str(text))
                return int(nums[0]) if nums else 0
            career_col = "경력구분" if "경력구분" in data.columns else "경력조건"
            if career_col in data.columns:
                data["경력_년"] = data[career_col].apply(extract_years)

        if "경력_년" not in data.columns or "연봉_만원" not in data.columns:
            logger.warning("경력_년 또는 연봉_만원 컬럼이 없습니다.")
            return

        # 기업규모별 색상
        size_col = "기업규모" if "기업규모" in data.columns else None
        if size_col:
            palette = {"대기업": "#2196F3", "중견기업": "#4CAF50",
                       "중소기업": "#FF9800", "스타트업": "#F44336"}
            for size_name, color in palette.items():
                subset = data[data[size_col] == size_name]
                if not subset.empty:
                    ax.scatter(subset["경력_년"], subset["연봉_만원"],
                              c=color, label=size_name, alpha=0.6, s=60)
        else:
            ax.scatter(data["경력_년"], data["연봉_만원"], c="#2196F3", alpha=0.6, s=60)

        # 회귀선
        if SCIPY_AVAILABLE and len(data) >= 3:
            x = data["경력_년"].values
            y = data["연봉_만원"].values
            mask = ~np.isnan(x) & ~np.isnan(y)
            if mask.sum() >= 3:
                slope, intercept, r_value, _, _ = scipy_stats.linregress(x[mask], y[mask])
                x_line = np.linspace(x[mask].min(), x[mask].max(), 100)
                ax.plot(x_line, slope * x_line + intercept, "r--", linewidth=2,
                        label=f"회귀선 (R²={r_value**2:.3f})")

        ax.set_xlabel("요구 경력 (년)", fontsize=12)
        ax.set_ylabel("연봉 (만원)", fontsize=12)
        ax.set_title("경력-연봉 산점도", fontsize=16, fontweight="bold")
        ax.legend()
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        self._save_chart(fig, "adv_career_salary_scatter.png")

    # ── 6. 기술스택 카테고리별 스택 막대그래프 ──
    def plot_tech_category_stacked_bar(self, data: pd.DataFrame):
        """기술스택 카테고리별 스택 막대그래프"""
        fig, ax = plt.subplots(figsize=(14, 8))

        categories = list(data.columns)
        x = np.arange(len(data.index))
        width = 0.6
        bottom = np.zeros(len(data.index))
        colors = sns.color_palette("Set2", len(categories))

        for idx, cat in enumerate(categories):
            vals = data[cat].values
            ax.bar(x, vals, width, label=cat, bottom=bottom, color=colors[idx])
            bottom += vals

        ax.set_xticks(x)
        ax.set_xticklabels(data.index, rotation=45, ha="right")
        ax.set_ylabel("빈도", fontsize=12)
        ax.set_title("기술스택 카테고리별 분포", fontsize=16, fontweight="bold")
        ax.legend(title="카테고리")
        fig.tight_layout()
        self._save_chart(fig, "adv_tech_category_stacked.png")

    # ── 7. 기업 리뷰 감성 분포 바이올린 플롯 ──
    def plot_review_violin(self, review_data: pd.DataFrame):
        """기업 리뷰 평점 바이올린 플롯"""
        fig, ax = plt.subplots(figsize=(14, 8))

        company_col = "기업명" if "기업명" in review_data.columns else "회사명"
        score_col = "총점" if "총점" in review_data.columns else review_data.select_dtypes(include=[np.number]).columns[0]

        review_data[score_col] = pd.to_numeric(review_data[score_col], errors="coerce")

        if "카테고리" in review_data.columns:
            sns.violinplot(data=review_data, x=company_col, y=score_col,
                          hue="카테고리", split=True, ax=ax, palette="Set2")
        else:
            sns.violinplot(data=review_data, x=company_col, y=score_col,
                          ax=ax, palette="Set2")

        ax.set_xlabel("기업명", fontsize=12)
        ax.set_ylabel("평점", fontsize=12)
        ax.set_title("기업 리뷰 감성 분포", fontsize=16, fontweight="bold")
        plt.xticks(rotation=45, ha="right")
        fig.tight_layout()
        self._save_chart(fig, "adv_review_violin.png")

    # ── 8. 채용 키워드 시계열 버블차트 ──
    def plot_keyword_bubble(self, trend_data: pd.DataFrame):
        """채용 키워드 시계열 버블차트"""
        fig, ax = plt.subplots(figsize=(16, 10))

        if trend_data.empty:
            logger.warning("트렌드 데이터가 비어있습니다.")
            return

        # trend_data: index=월, columns=키워드, values=빈도
        months = list(trend_data.index)
        keywords = list(trend_data.columns)
        colors = sns.color_palette("tab10", len(keywords))

        for idx, keyword in enumerate(keywords):
            for m_idx, month in enumerate(months):
                size = trend_data.loc[month, keyword]
                if size > 0:
                    ax.scatter(m_idx, idx, s=size * 30, c=[colors[idx]], alpha=0.6,
                              edgecolors="gray", linewidth=0.5)

        ax.set_xticks(range(len(months)))
        ax.set_xticklabels(months, rotation=45, ha="right")
        ax.set_yticks(range(len(keywords)))
        ax.set_yticklabels(keywords)
        ax.set_xlabel("시기", fontsize=12)
        ax.set_ylabel("키워드", fontsize=12)
        ax.set_title("채용 키워드 시계열 버블차트", fontsize=16, fontweight="bold")
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        self._save_chart(fig, "adv_keyword_bubble.png")

    def create_all(self, data: dict):
        """전체 고급 차트 생성 (8종)"""
        logger.info("=" * 40)
        logger.info("고급 차트 생성 시작 (총 8개)")
        logger.info("=" * 40)

        chart_map = {
            "heatmap_data": self.plot_company_tech_heatmap,
            "radar_data": self.plot_company_radar,
            "treemap_data": self.plot_job_treemap,
            "network_data": self.plot_tech_network,
            "scatter_data": self.plot_career_salary_scatter,
            "stacked_data": self.plot_tech_category_stacked_bar,
            "violin_data": self.plot_review_violin,
            "bubble_data": self.plot_keyword_bubble,
        }

        for key, func in chart_map.items():
            if data.get(key) is not None:
                try:
                    func(data[key])
                except Exception as e:
                    logger.error(f"고급 차트 생성 실패 ({key}): {e}")
            else:
                logger.warning(f"데이터 없음: {key}")

        logger.info("고급 차트 생성 완료")

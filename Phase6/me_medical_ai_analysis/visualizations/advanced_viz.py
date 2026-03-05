"""
=============================================================
고급 시각화 모듈
=============================================================
히트맵, 레이더차트, 트리맵, 네트워크 그래프,
스택 막대, 바이올린 플롯, 버블차트 등
보유 데이터 기반 자체 로딩 + 가공 → 10종 생성
=============================================================
"""

import os
import re
import math
import glob
from itertools import combinations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib import rcParams
import seaborn as sns

from config.settings import (
    DATA_PROCESSED_DIR, OUTPUTS_CHARTS_DIR,
    KOREAN_FONT_CANDIDATES, TECH_STACK_KEYWORDS,
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

# 기술스택 카테고리 분류
TECH_CATEGORIES = {
    "프로그래밍 언어": ["Python", "R", "Java", "C++", "JavaScript"],
    "AI/ML 프레임워크": ["PyTorch", "TensorFlow", "Keras", "scikit-learn",
                        "딥러닝", "머신러닝"],
    "데이터/통계": ["pandas", "NumPy", "SciPy", "SQL", "MongoDB", "PostgreSQL",
                    "SPSS", "SAS", "통계분석", "생존분석"],
    "의료 특화": ["의료영상", "DICOM", "PACS", "HL7", "FHIR",
                   "CT", "MRI", "X-ray", "병리", "내시경",
                   "임상시험", "FDA", "MFDS"],
    "인프라/DevOps": ["Docker", "Kubernetes", "AWS", "GCP", "Azure",
                       "Git", "Linux", "MLOps", "Kubeflow", "MLflow"],
    "웹/기타": ["React", "FastAPI", "Django", "컴퓨터비전", "자연어처리", "NLP",
                "논문", "SCI", "특허"],
}


class AdvancedVisualizer:
    """고급 시각화 (보유 데이터 기반 자체 로딩, 10종)"""

    def __init__(self, save_dir: str = None, data_path: str = None):
        self.save_dir = save_dir or OUTPUTS_CHARTS_DIR
        self.data_path = data_path or DATA_PROCESSED_DIR
        os.makedirs(self.save_dir, exist_ok=True)
        self.data = {}
        self._load_all_data()

    def _load_all_data(self):
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
        path = os.path.join(self.save_dir, filename)
        fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        print(f"    -> {filename}")

    # ─────────────────────────────────────────
    # 1. 검색키워드별 기술스택 언급 히트맵
    # ─────────────────────────────────────────
    def plot_keyword_tech_heatmap(self):
        """블로그+뉴스 제목/내용에서 검색키워드별 기술스택 언급 빈도 히트맵"""
        blog_df = self._find_df("blog", "블로그")
        news_df = self._find_df("news", "뉴스")
        frames = [df for df in [blog_df, news_df] if df is not None]
        if not frames:
            print("    ⚠️ 블로그/뉴스 데이터 없음 → 키워드-기술 히트맵 스킵")
            return

        combined = pd.concat(frames, ignore_index=True)
        if "검색키워드" not in combined.columns:
            return

        # 제목+내용 합치기
        combined["텍스트"] = (
            combined.get("제목", pd.Series(dtype=str)).fillna("")
            + " "
            + combined.get("내용요약", pd.Series(dtype=str)).fillna("")
        )

        # 기술 키워드 탐지 (대소문자 구분 주의)
        tech_list = TECH_STACK_KEYWORDS[:20]  # 상위 20개만
        records = []
        for kw, group in combined.groupby("검색키워드"):
            row = {"검색키워드": kw}
            for tech in tech_list:
                pattern = re.escape(tech)
                count = group["텍스트"].str.contains(pattern, case=False, na=False).sum()
                row[tech] = count
            records.append(row)

        matrix = pd.DataFrame(records).set_index("검색키워드")
        # 행/열 모두 합계 0 제거
        matrix = matrix.loc[:, matrix.sum() > 0]
        matrix = matrix.loc[matrix.sum(axis=1) > 0]
        if matrix.empty or matrix.shape[0] < 2 or matrix.shape[1] < 2:
            print("    ⚠️ 키워드-기술 조합 데이터 부족 → 스킵")
            return

        # 상위 10 키워드 x 상위 10 기술로 축소
        top_kw = matrix.sum(axis=1).nlargest(10).index
        top_tech = matrix.sum(axis=0).nlargest(10).index
        matrix = matrix.loc[top_kw, top_tech]

        fig, ax = plt.subplots(figsize=(14, 9))
        sns.heatmap(matrix, annot=True, fmt=".0f", cmap="Greens",
                    linewidths=0.5, ax=ax, cbar_kws={"label": "언급 빈도"},
                    annot_kws={"fontsize": 13, "fontweight": "bold"})
        ax.set_title("검색키워드별 기술스택 언급 히트맵", fontsize=20, fontweight="bold", pad=15)
        ax.set_ylabel("")
        plt.xticks(rotation=45, ha="right", fontsize=14)
        plt.yticks(rotation=0, fontsize=14)
        self._save(fig, "adv_keyword_tech_heatmap.png")

    # ─────────────────────────────────────────
    # 2. 기업 종합 프로필 레이더차트
    # ─────────────────────────────────────────
    def plot_company_radar(self):
        """기업별 다차원 지표(평균별점, 리뷰수, 면접수, 면접난이도, 직종다양성) 레이더"""
        review_df = self._find_df("리뷰", "review")
        interview_df = self._find_df("면접", "interview")
        if review_df is None:
            print("    ⚠️ 리뷰 데이터 없음 → 기업 레이더 스킵")
            return

        # 기업별 지표 계산
        companies = review_df["기업명"].unique()
        rows = []
        for comp in companies:
            rv = review_df[review_df["기업명"] == comp]
            rating = pd.to_numeric(rv["별점"], errors="coerce").mean()
            review_cnt = len(rv)
            job_diversity = rv["직종"].nunique() if "직종" in rv.columns else 0

            iv_cnt = 0
            avg_diff = 0
            if interview_df is not None:
                iv = interview_df[interview_df["기업명"] == comp]
                iv_cnt = len(iv)
                diff_map = {"매우 쉬움": 1, "쉬움": 2, "보통": 3, "어려움": 4, "매우 어려움": 5}
                if "면접난이도" in iv.columns and len(iv) > 0:
                    avg_diff = iv["면접난이도"].map(diff_map).mean()
                    if pd.isna(avg_diff):
                        avg_diff = 0

            rows.append({
                "기업명": comp,
                "평균별점": rating if not pd.isna(rating) else 0,
                "리뷰수": review_cnt,
                "면접후기수": iv_cnt,
                "면접난이도": avg_diff,
                "직종다양성": job_diversity,
            })

        profile = pd.DataFrame(rows)
        if len(profile) < 2:
            return

        # 정규화 (0~5 스케일)
        metrics = ["평균별점", "리뷰수", "면접후기수", "면접난이도", "직종다양성"]
        for col in metrics:
            col_min, col_max = profile[col].min(), profile[col].max()
            if col_max > col_min:
                profile[col + "_norm"] = (profile[col] - col_min) / (col_max - col_min) * 5
            else:
                profile[col + "_norm"] = 2.5

        norm_cols = [m + "_norm" for m in metrics]
        categories = metrics
        N = len(categories)
        angles = [n / float(N) * 2 * math.pi for n in range(N)]
        angles += angles[:1]

        # 상위 6개 기업만
        profile = profile.sort_values("리뷰수", ascending=False).head(6)

        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))
        colors = sns.color_palette("Set2", len(profile))

        for idx, (_, row) in enumerate(profile.iterrows()):
            values = [float(row[nc]) for nc in norm_cols]
            values += values[:1]
            ax.plot(angles, values, linewidth=2, linestyle="solid",
                    label=row["기업명"], color=colors[idx])
            ax.fill(angles, values, alpha=0.08, color=colors[idx])

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=14)
        ax.set_ylim(0, 5.5)
        ax.tick_params(axis='y', labelsize=12)
        ax.set_title("기업 종합 프로필 레이더차트", fontsize=20, fontweight="bold", pad=25)
        ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.1), fontsize=14)
        self._save(fig, "adv_company_radar.png")

    # ─────────────────────────────────────────
    # 3. 직종 분류 트리맵 (3개 소스별 개별)
    # ─────────────────────────────────────────
    def _plot_single_treemap(self, jobs_series, title, filename, top_n=20, colormap="Set3"):
        """단일 데이터 소스에 대한 트리맵 생성 헬퍼"""
        try:
            import squarify
        except ImportError:
            print("    ⚠️ squarify 미설치 → 트리맵 스킵")
            return

        if jobs_series.empty:
            return

        counts = jobs_series.value_counts().head(top_n)
        if counts.empty:
            return

        fig, ax = plt.subplots(figsize=(14, 9))
        colors = sns.color_palette(colormap, len(counts))
        labels = [f"{name}\n({cnt}건)" for name, cnt in counts.items()]

        fontsize = 14 if len(counts) <= 15 else 12
        squarify.plot(sizes=counts.values, label=labels,
                      color=colors, alpha=0.85, ax=ax,
                      text_kwargs={"fontsize": fontsize, "fontweight": "bold"})
        ax.set_title(title, fontsize=20, fontweight="bold", pad=15)
        ax.axis("off")
        self._save(fig, filename)

    def plot_job_treemap(self):
        """잡플래닛 / 원티드 / 사람인 각각의 직종·직무 트리맵 (3개)"""
        try:
            import squarify  # noqa: F401
        except ImportError:
            print("    ⚠️ squarify 미설치 → 트리맵 스킵")
            return

        generated = 0

        # (1) 잡플래닛 리뷰 직종
        review_df = self._find_df("리뷰", "review")
        if review_df is not None and "직종" in review_df.columns:
            jobs = review_df["직종"].dropna()
            if not jobs.empty:
                self._plot_single_treemap(
                    jobs,
                    "잡플래닛 리뷰 직종 분류 트리맵",
                    "adv_job_treemap_jobplanet.png",
                    top_n=20, colormap="Pastel1",
                )
                generated += 1

        # (2) 원티드 직무카테고리
        wanted_df = self._find_df("원티드", "wanted")
        if wanted_df is not None and "직무카테고리" in wanted_df.columns:
            items = []
            for val in wanted_df["직무카테고리"].dropna():
                for cat in str(val).split(","):
                    cat = cat.strip()
                    if cat:
                        items.append(cat)
            if items:
                self._plot_single_treemap(
                    pd.Series(items),
                    "원티드 직무 카테고리 트리맵",
                    "adv_job_treemap_wanted.png",
                    top_n=20, colormap="Pastel2",
                )
                generated += 1

        # (3) 사람인 직무분야
        saramin_df = self._find_df("사람인", "saramin")
        if saramin_df is not None and "직무분야" in saramin_df.columns:
            items = []
            for val in saramin_df["직무분야"].dropna():
                for cat in str(val).split(","):
                    cat = cat.strip()
                    if cat:
                        items.append(cat)
            if items:
                self._plot_single_treemap(
                    pd.Series(items),
                    "사람인 직무분야 트리맵",
                    "adv_job_treemap_saramin.png",
                    top_n=20, colormap="Set3",
                )
                generated += 1

        if generated == 0:
            print("    ⚠️ 직종/직무 데이터 없음 → 트리맵 스킵")

    # ─────────────────────────────────────────
    # 4. 기술스택 네트워크 그래프
    # ─────────────────────────────────────────
    def plot_tech_network(self):
        """블로그+뉴스+원티드+사람인 텍스트에서 기술 키워드 동시출현 네트워크"""
        try:
            import networkx as nx
        except ImportError:
            print("    ⚠️ networkx 미설치 → 네트워크 스킵")
            return

        blog_df = self._find_df("blog", "블로그")
        news_df = self._find_df("news", "뉴스")
        frames = [df for df in [blog_df, news_df] if df is not None]
        if not frames:
            print("    ⚠️ 블로그/뉴스 데이터 없음 → 네트워크 스킵")
            return

        combined = pd.concat(frames, ignore_index=True)
        texts = (
            combined.get("제목", pd.Series(dtype=str)).fillna("")
            + " "
            + combined.get("내용요약", pd.Series(dtype=str)).fillna("")
        )

        # 원티드 자격요건/우대사항/주요업무/기술스택태그 텍스트 추가
        wanted_df = self._find_df("원티드", "wanted")
        if wanted_df is not None:
            wanted_texts = pd.Series(dtype=str)
            for col in ["자격요건", "우대사항", "주요업무", "기술스택태그"]:
                if col in wanted_df.columns:
                    wanted_texts = pd.concat([wanted_texts, wanted_df[col].fillna("")], ignore_index=True)
            if not wanted_texts.empty:
                texts = pd.concat([texts, wanted_texts], ignore_index=True)

        # 사람인 자격요건/우대사항/주요업무/기술스택 텍스트 추가
        saramin_df = self._find_df("사람인", "saramin")
        if saramin_df is not None:
            saramin_texts = pd.Series(dtype=str)
            for col in ["자격요건", "우대사항", "주요업무", "기술스택", "공고제목"]:
                if col in saramin_df.columns:
                    saramin_texts = pd.concat([saramin_texts, saramin_df[col].fillna("")], ignore_index=True)
            if not saramin_texts.empty:
                texts = pd.concat([texts, saramin_texts], ignore_index=True)

        # 각 문서에서 등장하는 기술 키워드 추출
        tech_list = TECH_STACK_KEYWORDS[:25]
        cooccur = {}
        for text in texts:
            found = [t for t in tech_list if t.lower() in str(text).lower()]
            for a, b in combinations(sorted(set(found)), 2):
                pair = (a, b)
                cooccur[pair] = cooccur.get(pair, 0) + 1

        if len(cooccur) < 3:
            print("    ⚠️ 동시출현 데이터 부족 → 네트워크 스킵")
            return

        # 상위 동시출현만 사용
        top_pairs = sorted(cooccur.items(), key=lambda x: x[1], reverse=True)[:40]

        G = nx.Graph()
        for (a, b), w in top_pairs:
            G.add_edge(a, b, weight=w)

        fig, ax = plt.subplots(figsize=(14, 14))
        pos = nx.spring_layout(G, k=2.5, seed=42)
        degrees = dict(G.degree())
        node_sizes = [degrees[n] * 250 + 400 for n in G.nodes()]
        node_colors = [degrees[n] for n in G.nodes()]

        # 엣지 두께 = weight
        edge_weights = [G[u][v]["weight"] for u, v in G.edges()]
        max_w = max(edge_weights) if edge_weights else 1
        edge_widths = [w / max_w * 4 + 0.5 for w in edge_weights]

        nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color=node_colors,
                               cmap=plt.cm.Blues, alpha=0.85, ax=ax)
        nx.draw_networkx_edges(G, pos, alpha=0.4, width=edge_widths, ax=ax)

        font_kw = {"fname": KOREAN_FONT_PATH} if KOREAN_FONT_PATH else {}
        for node, (x, y) in pos.items():
            ax.text(x, y, node, fontsize=14, ha="center", va="center",
                    fontweight="bold",
                    fontproperties=fm.FontProperties(**font_kw) if font_kw else None)

        ax.set_title("기술스택 동시출현 네트워크", fontsize=20, fontweight="bold", pad=15)
        ax.axis("off")
        self._save(fig, "adv_tech_network.png")

    # ─────────────────────────────────────────
    # 5. 기술스택 카테고리 스택 막대그래프
    # ─────────────────────────────────────────
    def plot_tech_category_stacked_bar(self):
        """tech_stack_frequency를 카테고리별로 분류한 스택 막대"""
        tech_df = self._find_df("tech_stack")
        if tech_df is None or tech_df.empty:
            print("    ⚠️ 기술스택 빈도 데이터 없음 → 카테고리 스택 스킵")
            return

        name_col, freq_col = tech_df.columns[0], tech_df.columns[1]
        tech_dict = dict(zip(tech_df[name_col].astype(str), tech_df[freq_col]))

        # 카테고리별 집계
        cat_data = {}
        for cat, techs in TECH_CATEGORIES.items():
            for t in techs:
                if t in tech_dict and tech_dict[t] > 0:
                    cat_data.setdefault(cat, {})[t] = tech_dict[t]

        if not cat_data:
            return

        # 카테고리별 상위 기술만 표시
        fig, ax = plt.subplots(figsize=(12, 7))
        categories = list(cat_data.keys())
        bottoms = np.zeros(len(categories))
        colors = sns.color_palette("Set3", 15)
        color_idx = 0
        legend_handles = []

        all_techs = set()
        for cat in categories:
            all_techs.update(cat_data[cat].keys())

        for tech in sorted(all_techs):
            vals = []
            for cat in categories:
                vals.append(cat_data.get(cat, {}).get(tech, 0))
            if sum(vals) > 0:
                bars = ax.bar(categories, vals, bottom=bottoms,
                              label=tech, color=colors[color_idx % len(colors)],
                              edgecolor="white", linewidth=0.5)
                legend_handles.append(bars)
                bottoms += np.array(vals)
                color_idx += 1

        ax.set_ylabel("빈도수", fontsize=16)
        ax.set_title("기술스택 카테고리별 상세 분포", fontsize=20, fontweight="bold", pad=15)
        ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=12, ncol=1)
        ax.tick_params(axis='y', labelsize=14)
        plt.xticks(rotation=25, ha="right", fontsize=14)
        self._save(fig, "adv_tech_category_stacked.png")

    # ─────────────────────────────────────────
    # 6. 기업 리뷰 별점 바이올린 플롯
    # ─────────────────────────────────────────
    def plot_review_violin(self):
        """기업별 별점 분포 바이올린 플롯"""
        review_df = self._find_df("리뷰", "review")
        if review_df is None or "기업명" not in review_df.columns or "별점" not in review_df.columns:
            print("    ⚠️ 리뷰 별점 데이터 없음 → 바이올린 스킵")
            return

        df = review_df.copy()
        df["별점"] = pd.to_numeric(df["별점"], errors="coerce")
        df = df.dropna(subset=["별점"])

        # 리뷰 3건 이상인 기업만
        valid_companies = df["기업명"].value_counts()
        valid_companies = valid_companies[valid_companies >= 3].index.tolist()
        df = df[df["기업명"].isin(valid_companies)]
        if df.empty:
            return

        fig, ax = plt.subplots(figsize=(max(10, len(valid_companies) * 1.2), 8))
        sns.violinplot(data=df, x="기업명", y="별점", ax=ax, palette="Set2",
                       inner="box", cut=0)
        ax.set_xlabel("")
        ax.set_ylabel("별점 (5점 만점)", fontsize=16)
        ax.set_ylim(0, 5.5)
        ax.set_title("기업별 리뷰 별점 분포 (바이올린 플롯)", fontsize=20, fontweight="bold", pad=15)
        ax.tick_params(axis='y', labelsize=14)
        plt.xticks(rotation=35, ha="right", fontsize=14)
        self._save(fig, "adv_review_violin.png")

    # ─────────────────────────────────────────
    # 7. 검색키워드 월별 버블차트
    # ─────────────────────────────────────────
    def plot_keyword_bubble(self):
        """블로그 검색키워드별 월별 게시 건수 버블차트"""
        blog_df = self._find_df("blog", "블로그")
        if blog_df is None or "검색키워드" not in blog_df.columns or "게시일자" not in blog_df.columns:
            print("    ⚠️ 블로그 키워드/일자 데이터 없음 → 버블 스킵")
            return

        df = blog_df.copy()
        df["date"] = pd.to_datetime(df["게시일자"], errors="coerce")
        df = df.dropna(subset=["date"])
        df["월"] = df["date"].dt.to_period("M")

        # 상위 8개 키워드
        top_kw = df["검색키워드"].value_counts().head(8).index.tolist()
        df = df[df["검색키워드"].isin(top_kw)]

        grouped = df.groupby(["월", "검색키워드"]).size().reset_index(name="건수")
        if grouped.empty:
            return

        # 월 → 숫자 인덱스
        all_months = sorted(grouped["월"].unique())
        month_map = {m: i for i, m in enumerate(all_months)}
        grouped["x"] = grouped["월"].map(month_map)

        # 키워드 → y 인덱스
        kw_map = {kw: i for i, kw in enumerate(top_kw)}
        grouped["y"] = grouped["검색키워드"].map(kw_map)

        fig, ax = plt.subplots(figsize=(14, 8))
        scatter = ax.scatter(
            grouped["x"], grouped["y"],
            s=grouped["건수"] * 80, alpha=0.6,
            c=grouped["y"], cmap="Set2", edgecolors="white", linewidth=0.8)

        # 버블 위에 건수 표기
        for _, row in grouped.iterrows():
            if row["건수"] >= 2:
                ax.text(row["x"], row["y"], str(int(row["건수"])),
                        ha="center", va="center", fontsize=12, fontweight="bold")

        ax.set_xticks(range(len(all_months)))
        ax.set_xticklabels([f"{m.month}월" for m in all_months], rotation=45, ha="right", fontsize=13)
        ax.set_yticks(range(len(top_kw)))
        ax.set_yticklabels(top_kw, fontsize=13)
        ax.set_xlabel("월", fontsize=16)
        ax.set_ylabel("검색키워드", fontsize=16)
        ax.set_title("검색키워드별 월별 블로그 게시 버블차트", fontsize=20, fontweight="bold", pad=15)
        self._save(fig, "adv_keyword_bubble.png")

    # ─────────────────────────────────────────
    # 8. 의료 도메인-키워드 히트맵
    # ─────────────────────────────────────────
    def plot_domain_keyword_heatmap(self):
        """medical_domain_frequency 카테고리×키워드 빈도 히트맵"""
        domain_df = self._find_df("medical_domain")
        if domain_df is None or domain_df.empty:
            print("    ⚠️ 의료 도메인 데이터 없음 → 도메인 히트맵 스킵")
            return

        if "카테고리" not in domain_df.columns or "키워드" not in domain_df.columns or "빈도" not in domain_df.columns:
            return

        pivot = domain_df.pivot_table(index="카테고리", columns="키워드", values="빈도",
                                       fill_value=0, aggfunc="sum")
        if pivot.empty:
            return

        fig, ax = plt.subplots(figsize=(14, 7))
        sns.heatmap(pivot, annot=True, fmt=".0f", cmap="YlOrRd",
                    linewidths=0.5, ax=ax, cbar_kws={"label": "빈도"},
                    annot_kws={"fontsize": 13, "fontweight": "bold"})
        ax.set_title("의료 도메인별 키워드 빈도 히트맵", fontsize=20, fontweight="bold", pad=15)
        ax.set_ylabel("")
        plt.xticks(rotation=45, ha="right", fontsize=14)
        plt.yticks(fontsize=14)
        self._save(fig, "adv_domain_keyword_heatmap.png")

    # ─────────────────────────────────────────
    # 9. 기업별 면접경험 종합 비교
    # ─────────────────────────────────────────
    def plot_company_interview_comparison(self):
        """기업별 면접 건수·난이도 수평 이중 막대"""
        interview_df = self._find_df("면접", "interview")
        if interview_df is None or "기업명" not in interview_df.columns:
            print("    ⚠️ 면접 데이터 없음 → 면접 비교 스킵")
            return

        diff_map = {"매우 쉬움": 1, "쉬움": 2, "보통": 3, "어려움": 4, "매우 어려움": 5}
        df = interview_df.copy()
        df["난이도_수치"] = df["면접난이도"].map(diff_map)

        grouped = df.groupby("기업명").agg(
            면접건수=("기업명", "size"),
            평균난이도=("난이도_수치", "mean"),
        ).dropna().sort_values("면접건수", ascending=True)

        if grouped.empty:
            return

        fig, ax1 = plt.subplots(figsize=(10, max(6, len(grouped) * 0.6)))
        y = np.arange(len(grouped))

        bars = ax1.barh(y, grouped["면접건수"], color="#5DADE2", edgecolor="white", label="면접 건수")
        ax1.set_xlabel("면접 건수", fontsize=15, color="#5DADE2")
        ax1.set_yticks(y)
        ax1.set_yticklabels(grouped.index, fontsize=14)
        for bar, val in zip(bars, grouped["면접건수"]):
            ax1.text(val + 0.2, bar.get_y() + bar.get_height() / 2,
                     str(int(val)), va="center", fontsize=13, fontweight="bold", color="#5DADE2")

        ax2 = ax1.twiny()
        ax2.plot(grouped["평균난이도"], y, "D-", color="#E74C3C", markersize=8, linewidth=2, label="평균 난이도")
        ax2.set_xlabel("평균 면접난이도 (1~5)", fontsize=15, color="#E74C3C")
        ax2.set_xlim(0, 5.5)

        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc="lower right", fontsize=14)

        ax1.set_title("기업별 면접 건수 & 난이도 비교", fontsize=20, fontweight="bold", pad=40)
        fig.tight_layout()
        self._save(fig, "adv_company_interview_comparison.png")

    # ─────────────────────────────────────────
    # 10. 단어 빈도 상위 버블 클라우드
    # ─────────────────────────────────────────
    def plot_word_freq_bubble(self):
        """word_frequency 상위 단어 버블 시각화"""
        word_df = self._find_df("word_frequency")
        if word_df is None or word_df.empty:
            print("    ⚠️ 단어 빈도 데이터 없음 → 버블 클라우드 스킵")
            return

        name_col, freq_col = word_df.columns[0], word_df.columns[1]
        top = word_df.head(30).copy()
        top[freq_col] = pd.to_numeric(top[freq_col], errors="coerce")
        top = top.dropna(subset=[freq_col])
        if top.empty:
            return

        fig, ax = plt.subplots(figsize=(14, 10))
        np.random.seed(42)
        x = np.random.uniform(0, 10, len(top))
        y = np.random.uniform(0, 10, len(top))
        sizes = top[freq_col].values
        max_size = sizes.max()
        bubble_sizes = (sizes / max_size) * 3000 + 200

        colors = plt.cm.viridis(np.linspace(0.2, 0.9, len(top)))
        ax.scatter(x, y, s=bubble_sizes, c=colors, alpha=0.6, edgecolors="white", linewidth=1.5)

        font_kw = {"fname": KOREAN_FONT_PATH} if KOREAN_FONT_PATH else {}
        fp = fm.FontProperties(**font_kw) if font_kw else None
        for i, (_, row) in enumerate(top.iterrows()):
            fs = max(12, int(sizes[i] / max_size * 20))
            ax.text(x[i], y[i], f"{row[name_col]}\n({int(row[freq_col])})",
                    ha="center", va="center", fontsize=fs, fontweight="bold",
                    fontproperties=fp)

        ax.set_xlim(-1, 11)
        ax.set_ylim(-1, 11)
        ax.axis("off")
        ax.set_title("핵심 키워드 버블 시각화 (TOP 30)", fontsize=20, fontweight="bold", pad=15)
        self._save(fig, "adv_word_freq_bubble.png")

    # ─────────────────────────────────────────
    # 전체 생성
    # ─────────────────────────────────────────
    def generate_all(self, data_dict: dict = None):
        """고급 차트 전체 생성 (보유 데이터 자체 로딩)"""
        print("=" * 60)
        print("🎨 고급 시각화 생성 (12종)")
        print("=" * 60)

        self.plot_keyword_tech_heatmap()       # 1
        self.plot_company_radar()              # 2
        self.plot_job_treemap()                # 3
        self.plot_tech_network()               # 4
        self.plot_tech_category_stacked_bar()  # 5
        self.plot_review_violin()              # 6
        self.plot_keyword_bubble()             # 7
        self.plot_domain_keyword_heatmap()     # 8
        self.plot_company_interview_comparison()  # 9
        self.plot_word_freq_bubble()           # 10

        print("\n✅ 고급 차트 생성 완료!")

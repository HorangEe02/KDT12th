"""
=============================================================
원티드 채용 포지션 시각화 모듈
=============================================================
원티드 의료/제약/바이오 포지션 데이터를 활용한 시각화 7종 생성
- 자격요건/우대사항 워드클라우드
- 직무카테고리별 분포
- 업종별 분포
- 근무지(지역)별 분포
- 기술스택 분포
- 경력범위 분포
- 회사별 포지션 수 TOP 15
=============================================================
"""

import os
import re
import glob
from collections import Counter

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib import rcParams
import seaborn as sns
from PIL import Image

from config.settings import (
    DATA_PROCESSED_DIR, OUTPUTS_CHARTS_DIR,
    KOREAN_FONT_CANDIDATES, TECH_STACK_KEYWORDS,
    WORDCLOUD_MASK_PATH,
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


class WantedVisualizer:
    """원티드 채용 포지션 시각화"""

    def __init__(self, processed_data_path: str = None):
        self.data_path = processed_data_path or DATA_PROCESSED_DIR
        self.df = None
        self._load_data()

    def _load_data(self):
        csv_files = glob.glob(os.path.join(self.data_path, "*.csv"))
        for f in csv_files:
            basename = os.path.basename(f).lower()
            if "원티드" in basename or "wanted" in basename:
                try:
                    self.df = pd.read_csv(f, encoding="utf-8-sig")
                except UnicodeDecodeError:
                    self.df = pd.read_csv(f, encoding="utf-8")
                break

        if self.df is not None:
            print(f"  원티드 데이터 로드: {len(self.df)}건")
        else:
            print("  원티드 데이터 없음")

    def _save_chart(self, fig, filename):
        path = os.path.join(OUTPUTS_CHARTS_DIR, filename)
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        print(f"    -> {filename}")

    # ─────────────────────────────────────────
    # 1. 자격요건/우대사항 워드클라우드
    # ─────────────────────────────────────────
    def plot_requirements_wordcloud(self):
        """자격요건+우대사항+주요업무 텍스트 워드클라우드"""
        if self.df is None:
            return

        try:
            from wordcloud import WordCloud
        except ImportError:
            print("    wordcloud 패키지 미설치, 스킵")
            return

        texts = []
        for col in ["자격요건", "우대사항", "주요업무"]:
            if col in self.df.columns:
                texts.extend(self.df[col].dropna().tolist())

        if not texts:
            return

        combined = " ".join(str(t) for t in texts)

        # 불용어
        stopwords = {
            "경험", "이상", "관련", "분야", "우대", "있는", "보유", "가능",
            "대한", "업무", "등", "및", "또는", "있으신", "능력", "수행",
            "참여", "통해", "위한", "이해", "활용", "기반", "개발", "진행",
            "해당", "담당", "필요", "사항", "다양", "전공", "지원", "경력",
            "근무", "함께", "대해", "하는", "있다", "합니다", "입니다",
            "것이", "하고", "에서", "으로", "하며", "되는", "위해", "그리고",
        }

        font_path = KOREAN_FONT_PATH or ""

        # cross.png 마스크 로드 (적절한 크기로 리사이즈)
        mask_array = None
        if os.path.exists(WORDCLOUD_MASK_PATH):
            mask_image = Image.open(WORDCLOUD_MASK_PATH).convert("L")
            # 마스크가 너무 크면 단어가 상대적으로 작아지므로 리사이즈
            mask_image = mask_image.resize((800, 600), Image.LANCZOS)
            mask_arr = np.array(mask_image)
            # 이진화: 검정(건물)=0 → 단어 배치, 흰색(배경)=255 → 빈 영역
            mask_array = np.where(mask_arr < 128, 0, 255).astype(np.uint8)

        wc_params = {
            "font_path": font_path,
            "background_color": "white",
            "max_words": 200,
            "colormap": "viridis",
            "stopwords": stopwords,
            "min_font_size": 4,
            "prefer_horizontal": 0.7,
        }

        if mask_array is not None:
            wc_params["mask"] = mask_array
            wc_params["max_font_size"] = 150
            wc_params["contour_width"] = 2
            wc_params["contour_color"] = "#cccccc"
        else:
            wc_params["width"] = 1200
            wc_params["height"] = 600
            wc_params["max_font_size"] = 80

        wc = WordCloud(**wc_params)
        wc.generate(combined)

        fig, ax = plt.subplots(figsize=(10, 8) if mask_array is not None else (14, 7))
        ax.imshow(wc, interpolation="bilinear")
        ax.set_title("원티드 의료/제약/바이오 채용 자격요건 워드클라우드",
                      fontsize=20, fontweight="bold", pad=15)
        ax.axis("off")
        self._save_chart(fig, "wanted_01_requirements_wordcloud.png")

    # ─────────────────────────────────────────
    # 2. 직무카테고리별 포지션 분포
    # ─────────────────────────────────────────
    def plot_job_category_dist(self):
        """직무카테고리별 포지션 수"""
        if self.df is None or "직무카테고리" not in self.df.columns:
            return

        # 멀티 카테고리 분리 (쉼표 구분)
        categories = []
        for val in self.df["직무카테고리"].dropna():
            for cat in str(val).split(","):
                cat = cat.strip()
                if cat:
                    categories.append(cat)

        if not categories:
            return

        counter = Counter(categories)
        top = counter.most_common(15)
        labels = [x[0] for x in top]
        values = [x[1] for x in top]

        fig, ax = plt.subplots(figsize=(12, 7))
        colors = sns.color_palette("Blues_d", len(labels))[::-1]
        bars = ax.barh(range(len(labels)), values, color=colors)
        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels(labels, fontsize=14)
        ax.invert_yaxis()
        ax.set_xlabel("포지션 수", fontsize=16)
        ax.set_title("원티드 직무카테고리별 포지션 분포", fontsize=20, fontweight="bold", pad=15)

        for bar, val in zip(bars, values):
            ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                    str(val), va="center", fontsize=14, fontweight="bold")

        plt.tight_layout()
        self._save_chart(fig, "wanted_02_job_category_dist.png")

    # ─────────────────────────────────────────
    # 3. 업종별 분포
    # ─────────────────────────────────────────
    def plot_industry_dist(self):
        """업종별 포지션 분포 (파이차트)"""
        if self.df is None or "업종" not in self.df.columns:
            return

        industry_counts = self.df["업종"].value_counts()
        if industry_counts.empty:
            return

        # 5% 미만 항목은 '기타'로 묶기 (라벨 겹침 방지)
        total = industry_counts.sum()
        threshold = total * 0.05
        major = industry_counts[industry_counts >= threshold]
        minor_sum = industry_counts[industry_counts < threshold].sum()
        if minor_sum > 0:
            major["기타"] = major.get("기타", 0) + minor_sum
        industry_counts = major

        fig, ax = plt.subplots(figsize=(10, 8))
        colors = sns.color_palette("Set2", len(industry_counts))
        wedges, texts, autotexts = ax.pie(
            industry_counts.values,
            labels=None,
            autopct=lambda pct: f"{pct:.1f}%\n({int(round(pct / 100 * total))}건)",
            colors=colors,
            startangle=90,
            pctdistance=0.75,
            textprops={"fontsize": 14, "fontweight": "bold"},
        )

        ax.legend(
            wedges, industry_counts.index,
            loc="center left", bbox_to_anchor=(1.0, 0.5),
            fontsize=14, frameon=False,
        )

        ax.set_title("원티드 의료/제약/바이오 업종별 포지션 분포",
                      fontsize=18, fontweight="bold", pad=20)

        plt.tight_layout()
        self._save_chart(fig, "wanted_03_industry_dist.png")

    # ─────────────────────────────────────────
    # 4. 근무지(지역)별 분포
    # ─────────────────────────────────────────
    def plot_location_dist(self):
        """근무지를 시/도 단위로 정규화하여 분포 시각화"""
        if self.df is None or "근무지" not in self.df.columns:
            return

        def normalize_location(loc):
            if not isinstance(loc, str):
                return "기타"
            loc = loc.strip()
            # 서울 variants
            if any(k in loc for k in ["서울", "강남", "서초", "송파", "마포", "영등포",
                                       "금천", "구로", "관악", "용산", "종로", "성동",
                                       "동대문", "중구", "강서", "양천", "성북"]):
                return "서울"
            if any(k in loc for k in ["경기", "성남", "수원", "용인", "안양", "화성",
                                       "고양", "평택", "파주", "하남", "시흥", "안산",
                                       "김포", "의왕", "광명", "부천", "이천"]):
                return "경기"
            if "인천" in loc:
                return "인천"
            if any(k in loc for k in ["대전", "세종"]):
                return "대전/세종"
            if "대구" in loc:
                return "대구"
            if "부산" in loc:
                return "부산"
            if "광주" in loc:
                return "광주"
            if any(k in loc for k in ["충남", "충북", "충청"]):
                return "충청"
            if any(k in loc for k in ["전남", "전북", "전라"]):
                return "전라"
            if any(k in loc for k in ["경남", "경북", "경상"]):
                return "경상"
            if "강원" in loc:
                return "강원"
            if "제주" in loc:
                return "제주"
            return "기타"

        locations = self.df["근무지"].apply(normalize_location)
        loc_counts = locations.value_counts()

        if loc_counts.empty:
            return

        fig, ax = plt.subplots(figsize=(10, 6))
        colors = sns.color_palette("YlOrRd_r", len(loc_counts))
        bars = ax.barh(range(len(loc_counts)), loc_counts.values, color=colors)
        ax.set_yticks(range(len(loc_counts)))
        ax.set_yticklabels(loc_counts.index, fontsize=14)
        ax.invert_yaxis()
        ax.set_xlabel("포지션 수", fontsize=16)
        ax.set_title("원티드 근무지(지역)별 포지션 분포", fontsize=20, fontweight="bold", pad=15)

        for bar, val in zip(bars, loc_counts.values):
            ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                    f"{val}건 ({val / len(self.df) * 100:.0f}%)",
                    va="center", fontsize=14, fontweight="bold")

        plt.tight_layout()
        self._save_chart(fig, "wanted_04_location_dist.png")

    # ─────────────────────────────────────────
    # 5. 기술스택 분포
    # ─────────────────────────────────────────
    def plot_tech_stack_dist(self):
        """기술스택태그 + 텍스트 스캔 기반 기술스택 분포"""
        if self.df is None:
            return

        counter = Counter()

        # 방법1: 기술스택태그 컬럼 (쉼표 구분) 파싱
        if "기술스택태그" in self.df.columns:
            for val in self.df["기술스택태그"].dropna():
                for tag in str(val).split(","):
                    tag = tag.strip()
                    if tag:
                        counter[tag] += 1

        # 방법2: 자격요건/우대사항/주요업무 텍스트 스캔
        texts = []
        for col in ["자격요건", "우대사항", "주요업무"]:
            if col in self.df.columns:
                texts.extend(self.df[col].dropna().tolist())

        if texts:
            combined = " ".join(str(t) for t in texts)
            for tech in TECH_STACK_KEYWORDS:
                escaped = re.escape(tech)
                pattern = re.compile(
                    rf"\b{escaped}\b" if tech.isascii() else escaped,
                    re.IGNORECASE,
                )
                count = len(pattern.findall(combined))
                if count > 0:
                    counter[tech] += count

        if not counter:
            return

        top = counter.most_common(20)
        labels = [x[0] for x in top]
        values = [x[1] for x in top]

        fig, ax = plt.subplots(figsize=(12, 8))
        colors = sns.color_palette("coolwarm_r", len(labels))
        bars = ax.barh(range(len(labels)), values, color=colors)
        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels(labels, fontsize=14)
        ax.invert_yaxis()
        ax.set_xlabel("언급 횟수", fontsize=16)
        ax.set_title("원티드 의료/제약/바이오 기술스택 TOP 20",
                      fontsize=20, fontweight="bold", pad=15)

        for bar, val in zip(bars, values):
            ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                    str(val), va="center", fontsize=14, fontweight="bold")

        plt.tight_layout()
        self._save_chart(fig, "wanted_05_tech_stack_dist.png")

    # ─────────────────────────────────────────
    # 6. 경력범위 분포
    # ─────────────────────────────────────────
    def plot_career_range_dist(self):
        """연봉범위(실제 경력범위) 분포 시각화"""
        if self.df is None or "연봉범위" not in self.df.columns:
            return

        career_data = self.df["연봉범위"].dropna()
        if career_data.empty:
            return

        def categorize_career(text):
            text = str(text)
            nums = re.findall(r"(\d+)", text)
            if not nums:
                return "미표기"
            min_yr = int(nums[0])
            if min_yr == 0 or "신입" in text:
                return "신입 가능"
            elif min_yr <= 2:
                return "1~2년차"
            elif min_yr <= 5:
                return "3~5년차"
            elif min_yr <= 10:
                return "6~10년차"
            else:
                return "10년차 이상"

        career_cat = career_data.apply(categorize_career)
        order = ["신입 가능", "1~2년차", "3~5년차", "6~10년차", "10년차 이상", "미표기"]
        cat_counts = career_cat.value_counts().reindex(
            [o for o in order if o in career_cat.values], fill_value=0
        )

        if cat_counts.empty:
            return

        fig, ax = plt.subplots(figsize=(10, 6))
        colors = ["#2ecc71", "#3498db", "#9b59b6", "#e74c3c", "#e67e22", "#95a5a6"]
        bars = ax.bar(range(len(cat_counts)), cat_counts.values,
                      color=colors[:len(cat_counts)])
        ax.set_xticks(range(len(cat_counts)))
        ax.set_xticklabels(cat_counts.index, fontsize=14)
        ax.set_ylabel("포지션 수", fontsize=16)
        ax.set_title("원티드 의료/제약/바이오 요구 경력 분포",
                      fontsize=20, fontweight="bold", pad=15)

        for bar, val in zip(bars, cat_counts.values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                    f"{val}건", ha="center", fontsize=14, fontweight="bold")

        plt.tight_layout()
        self._save_chart(fig, "wanted_06_career_range_dist.png")

    # ─────────────────────────────────────────
    # 7. 회사별 포지션 수 TOP 15
    # ─────────────────────────────────────────
    def plot_company_positions(self):
        """회사별 채용 포지션 수 TOP 15"""
        if self.df is None or "회사명" not in self.df.columns:
            return

        company_counts = self.df["회사명"].value_counts().head(15)
        if company_counts.empty:
            return

        fig, ax = plt.subplots(figsize=(12, 7))
        colors = sns.color_palette("Greens_d", len(company_counts))[::-1]
        bars = ax.barh(range(len(company_counts)), company_counts.values, color=colors)
        ax.set_yticks(range(len(company_counts)))
        ax.set_yticklabels(company_counts.index, fontsize=14)
        ax.invert_yaxis()
        ax.set_xlabel("포지션 수", fontsize=16)
        ax.set_title("원티드 의료/제약/바이오 회사별 채용 포지션 수 TOP 15",
                      fontsize=20, fontweight="bold", pad=15)

        for bar, val in zip(bars, company_counts.values):
            ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height() / 2,
                    f"{val}건", va="center", fontsize=14, fontweight="bold")

        plt.tight_layout()
        self._save_chart(fig, "wanted_07_company_positions.png")

    # ─────────────────────────────────────────
    # 전체 생성
    # ─────────────────────────────────────────
    def generate_all(self):
        """원티드 시각화 7종 생성"""
        if self.df is None or self.df.empty:
            print("  원티드 데이터 없음, 스킵")
            return

        print(f"\n  원티드 포지션 시각화 생성 중... ({len(self.df)}건)")
        self.plot_requirements_wordcloud()
        self.plot_job_category_dist()
        self.plot_industry_dist()
        self.plot_location_dist()
        self.plot_tech_stack_dist()
        self.plot_career_range_dist()
        self.plot_company_positions()
        print("  원티드 시각화 7종 완료")


if __name__ == "__main__":
    viz = WantedVisualizer()
    viz.generate_all()

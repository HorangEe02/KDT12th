"""
=============================================================
사람인 채용공고 시각화 모듈
=============================================================
사람인 자동차 설계 채용공고 데이터를 활용한 시각화 7종 생성
- 직무분야 분포 (Top 15)
- 경력조건 분포 (도넛)
- 학력조건 분포
- 근무지역 분포 (Top 15)
- 고용형태 분포 (도넛)
- 기술스택 분포 (Top 15)
- 회사별 채용 수 Top 15
=============================================================
"""

import os
import re
import glob
from collections import Counter

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


class SaraminVisualizer:
    """사람인 채용공고 시각화"""

    def __init__(self, processed_data_path: str = None):
        self.data_path = processed_data_path or DATA_PROCESSED_DIR
        self.df = None
        self._load_data()

    def _load_data(self):
        csv_files = glob.glob(os.path.join(self.data_path, "*.csv"))
        for f in csv_files:
            basename = os.path.basename(f).lower()
            if "사람인" in basename or "saramin" in basename:
                try:
                    self.df = pd.read_csv(f, encoding="utf-8-sig")
                except UnicodeDecodeError:
                    self.df = pd.read_csv(f, encoding="utf-8")
                break

        if self.df is not None:
            print(f"  사람인 데이터 로드: {len(self.df)}건")
        else:
            print("  사람인 데이터 없음")

    def _save_chart(self, fig, filename):
        path = os.path.join(OUTPUTS_CHARTS_DIR, filename)
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        print(f"    -> {filename}")

    # ─────────────────────────────────────────
    # 1. 직무분야 분포 Top 15
    # ─────────────────────────────────────────
    def plot_job_sector_dist(self):
        """직무분야별 공고 수 Top 15"""
        if self.df is None or "직무분야" not in self.df.columns:
            return

        sectors = []
        for val in self.df["직무분야"].dropna():
            for sector in str(val).split(","):
                sector = sector.strip()
                if sector:
                    sectors.append(sector)

        if not sectors:
            return

        counter = Counter(sectors)
        top = counter.most_common(15)
        labels = [x[0] for x in top]
        values = [x[1] for x in top]

        fig, ax = plt.subplots(figsize=(12, 7))
        colors = sns.color_palette("Blues_d", len(labels))[::-1]
        bars = ax.barh(range(len(labels)), values, color=colors)
        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels(labels, fontsize=14)
        ax.invert_yaxis()
        ax.set_xlabel("공고 수", fontsize=16)
        ax.set_title("사람인 자동차 설계 채용공고 직무분야 Top 15",
                      fontsize=20, fontweight="bold", pad=15)

        for bar, val in zip(bars, values):
            ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                    str(val), va="center", fontsize=14, fontweight="bold")

        plt.tight_layout()
        self._save_chart(fig, "saramin_01_job_sector_dist.png")

    # ─────────────────────────────────────────
    # 2. 경력조건 분포 (도넛)
    # ─────────────────────────────────────────
    def plot_career_dist(self):
        """경력조건 분포 도넛 차트"""
        if self.df is None or "경력조건" not in self.df.columns:
            return

        career_counts = self.df["경력조건"].dropna().value_counts()
        if career_counts.empty:
            return

        # 상위 8개까지, 나머지는 '기타'로 묶기
        if len(career_counts) > 8:
            top = career_counts.head(7)
            others = career_counts.iloc[7:].sum()
            top["기타"] = others
            career_counts = top

        fig, ax = plt.subplots(figsize=(10, 8))
        colors = sns.color_palette("Set2", len(career_counts))
        wedges, texts, autotexts = ax.pie(
            career_counts.values,
            labels=career_counts.index,
            autopct=lambda pct: f"{pct:.1f}%\n({int(round(pct / 100 * sum(career_counts.values)))}건)",
            colors=colors,
            startangle=90,
            pctdistance=0.75,
            textprops={"fontsize": 14},
            wedgeprops={"width": 0.5},
        )
        for at in autotexts:
            at.set_fontsize(13)
            at.set_fontweight("bold")
        ax.set_title(f"사람인 자동차 설계 채용공고 경력조건 분포 (총 {len(self.df)}건)",
                      fontsize=18, fontweight="bold", pad=20)

        plt.tight_layout()
        self._save_chart(fig, "saramin_02_career_dist.png")

    # ─────────────────────────────────────────
    # 3. 학력조건 분포
    # ─────────────────────────────────────────
    def plot_education_dist(self):
        """학력조건 분포 막대 차트"""
        if self.df is None or "학력조건" not in self.df.columns:
            return

        edu_counts = self.df["학력조건"].dropna().value_counts()
        if edu_counts.empty:
            return

        fig, ax = plt.subplots(figsize=(10, 6))
        colors = ["#3498db", "#2ecc71", "#e74c3c", "#f39c12", "#9b59b6",
                  "#1abc9c", "#e67e22", "#95a5a6"][:len(edu_counts)]
        bars = ax.bar(range(len(edu_counts)), edu_counts.values, color=colors)
        ax.set_xticks(range(len(edu_counts)))
        ax.set_xticklabels(edu_counts.index, fontsize=14, rotation=20, ha="right")
        ax.set_ylabel("공고 수", fontsize=16)
        ax.set_title("사람인 자동차 설계 채용공고 학력조건 분포",
                      fontsize=20, fontweight="bold", pad=15)

        for bar, val in zip(bars, edu_counts.values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                    f"{val}건", ha="center", fontsize=14, fontweight="bold")

        plt.tight_layout()
        self._save_chart(fig, "saramin_03_education_dist.png")

    # ─────────────────────────────────────────
    # 4. 근무지역 분포 Top 15
    # ─────────────────────────────────────────
    def plot_location_dist(self):
        """근무지역 분포 Top 15"""
        if self.df is None or "근무지역" not in self.df.columns:
            return

        # 시/도 단위로 정규화
        def normalize_location(loc):
            if not isinstance(loc, str):
                return "기타"
            loc = loc.strip()
            if any(k in loc for k in ["서울", "강남", "서초", "송파", "마포", "영등포",
                                       "금천", "구로", "관악", "용산", "종로", "성동",
                                       "동대문", "중구", "강서", "양천", "성북"]):
                return "서울"
            if any(k in loc for k in ["경기", "성남", "수원", "용인", "안양", "화성",
                                       "고양", "평택", "파주", "하남", "시흥", "안산",
                                       "김포", "의왕", "광명", "부천", "이천", "판교"]):
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
            return loc[:10] if len(loc) > 10 else loc

        locations = self.df["근무지역"].dropna().apply(normalize_location)
        loc_counts = locations.value_counts().head(15)

        if loc_counts.empty:
            return

        fig, ax = plt.subplots(figsize=(12, 7))
        colors = sns.color_palette("YlOrRd_r", len(loc_counts))
        bars = ax.barh(range(len(loc_counts)), loc_counts.values, color=colors)
        ax.set_yticks(range(len(loc_counts)))
        ax.set_yticklabels(loc_counts.index, fontsize=14)
        ax.invert_yaxis()
        ax.set_xlabel("공고 수", fontsize=16)
        ax.set_title("사람인 자동차 설계 채용공고 근무지역 Top 15",
                      fontsize=20, fontweight="bold", pad=15)

        total = len(self.df)
        for bar, val in zip(bars, loc_counts.values):
            ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                    f"{val}건 ({val / total * 100:.1f}%)",
                    va="center", fontsize=14, fontweight="bold")

        plt.tight_layout()
        self._save_chart(fig, "saramin_04_location_dist.png")

    # ─────────────────────────────────────────
    # 5. 고용형태 분포 (도넛)
    # ─────────────────────────────────────────
    def plot_employment_type(self):
        """고용형태 분포 도넛 차트"""
        if self.df is None or "고용형태" not in self.df.columns:
            return

        type_counts = self.df["고용형태"].dropna().value_counts()
        if type_counts.empty:
            return

        # 2% 미만 항목은 '기타'로 묶기 (소수 항목 라벨 겹침 방지)
        total = type_counts.sum()
        threshold = total * 0.02
        major = type_counts[type_counts >= threshold]
        minor_sum = type_counts[type_counts < threshold].sum()
        if minor_sum > 0:
            major["기타"] = minor_sum
        type_counts = major

        fig, ax = plt.subplots(figsize=(10, 8))
        colors = sns.color_palette("Pastel1", len(type_counts))

        wedges, texts, autotexts = ax.pie(
            type_counts.values,
            labels=None,
            autopct=lambda pct: f"{pct:.1f}%\n({int(round(pct / 100 * total))}건)",
            colors=colors,
            startangle=90,
            pctdistance=0.75,
            textprops={"fontsize": 14, "fontweight": "bold"},
            wedgeprops={"width": 0.5},
        )

        # 범례로 라벨 표시 (도넛 바깥 겹침 방지)
        ax.legend(
            wedges, type_counts.index,
            loc="center left", bbox_to_anchor=(1.0, 0.5),
            fontsize=14, frameon=False,
        )

        ax.set_title("사람인 자동차 설계 채용공고 고용형태 분포",
                      fontsize=18, fontweight="bold", pad=20)

        plt.tight_layout()
        self._save_chart(fig, "saramin_05_employment_type.png")

    # ─────────────────────────────────────────
    # 6. 기술스택 분포 Top 15
    # ─────────────────────────────────────────
    def plot_tech_stack_dist(self):
        """기술스택 분포 Top 15 (공고제목 + 직무분야 + 기술스택 컬럼)"""
        if self.df is None:
            return

        counter = Counter()

        # 기술스택 컬럼 파싱 (쉼표 구분)
        if "기술스택" in self.df.columns:
            for val in self.df["기술스택"].dropna():
                for tag in str(val).split(","):
                    tag = tag.strip()
                    if tag:
                        counter[tag] += 1

        # 공고제목 + 직무분야에서도 텍스트 스캔
        texts = []
        for col in ["공고제목", "직무분야"]:
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

        top = counter.most_common(15)
        labels = [x[0] for x in top]
        values = [x[1] for x in top]

        fig, ax = plt.subplots(figsize=(12, 7))
        colors = sns.color_palette("coolwarm_r", len(labels))
        bars = ax.barh(range(len(labels)), values, color=colors)
        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels(labels, fontsize=14)
        ax.invert_yaxis()
        ax.set_xlabel("언급 횟수", fontsize=16)
        ax.set_title("사람인 자동차 설계 채용공고 기술스택 Top 15",
                      fontsize=20, fontweight="bold", pad=15)

        for bar, val in zip(bars, values):
            ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                    str(val), va="center", fontsize=14, fontweight="bold")

        plt.tight_layout()
        self._save_chart(fig, "saramin_06_tech_stack_dist.png")

    # ─────────────────────────────────────────
    # 7. 회사별 채용 수 Top 15
    # ─────────────────────────────────────────
    def plot_company_positions(self):
        """회사별 채용공고 수 Top 15"""
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
        ax.set_xlabel("공고 수", fontsize=16)
        ax.set_title("사람인 자동차 설계 채용 회사별 공고 수 Top 15",
                      fontsize=20, fontweight="bold", pad=15)

        for bar, val in zip(bars, company_counts.values):
            ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height() / 2,
                    f"{val}건", va="center", fontsize=14, fontweight="bold")

        plt.tight_layout()
        self._save_chart(fig, "saramin_07_company_positions.png")

    # ─────────────────────────────────────────
    # 전체 생성
    # ─────────────────────────────────────────
    def generate_all(self):
        """사람인 시각화 7종 생성"""
        if self.df is None or self.df.empty:
            print("  사람인 데이터 없음, 스킵")
            return

        print(f"\n  사람인 채용공고 시각화 생성 중... ({len(self.df)}건)")
        self.plot_job_sector_dist()
        self.plot_career_dist()
        self.plot_education_dist()
        self.plot_location_dist()
        self.plot_employment_type()
        self.plot_tech_stack_dist()
        self.plot_company_positions()
        print("  사람인 시각화 7종 완료")


if __name__ == "__main__":
    viz = SaraminVisualizer()
    viz.generate_all()

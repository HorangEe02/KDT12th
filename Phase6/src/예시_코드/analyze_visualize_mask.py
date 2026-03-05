"""
=============================================================
📌 데이터 분석 및 시각화 - 자율주행·의료 AI 취업 동향
    (maga.png 마스크 워드클라우드 버전)
=============================================================
- Naver OpenAPI + 잡플래닛 크롤링 데이터를 종합 분석
- maga.png 이미지 모양으로 워드클라우드 생성
- 시각화 차트 생성 및 저장
=============================================================
⚠️ 실행 전: crawl_naver_api.py, crawl_jobplanet.py를 먼저 실행하여
   data_naver/, data_jobplanet/ 폴더에 데이터가 있어야 합니다.
⚠️ 필요 패키지: pip install wordcloud Pillow numpy
=============================================================
"""

import os
import re
from collections import Counter

import numpy as np
from PIL import Image
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib import rcParams
import seaborn as sns


# ============================================================
# 0. 한글 폰트 설정 (파일 경로 직접 지정 방식)
# ============================================================
KOREAN_FONT_PATH = None  # 전역 폰트 경로 (워드클라우드에서도 사용)


def setup_korean_font():
    """시스템에서 한글 폰트 파일을 찾아 matplotlib에 직접 등록"""
    global KOREAN_FONT_PATH

    # macOS / Linux / Windows 한글 폰트 파일 경로 후보
    font_candidates = [
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/Library/Fonts/AppleSDGothicNeo.ttc",
        "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
        "C:/Windows/Fonts/malgun.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]

    # matplotlib에 등록된 한글 폰트 파일도 후보에 추가
    for f in fm.fontManager.ttflist:
        if any(
            k in f.name
            for k in [
                "Apple SD Gothic Neo",
                "AppleGothic",
                "Malgun",
                "NanumGothic",
                "Noto Sans CJK",
            ]
        ):
            font_candidates.insert(0, f.fname)

    # 실제 존재하는 첫 번째 폰트 사용
    for fp in font_candidates:
        if os.path.exists(fp):
            KOREAN_FONT_PATH = fp
            break

    if KOREAN_FONT_PATH:
        font_prop = fm.FontProperties(fname=KOREAN_FONT_PATH)
        font_name = font_prop.get_name()

        # matplotlib에 폰트 등록 및 캐시 갱신
        fm.fontManager.addfont(KOREAN_FONT_PATH)
        rcParams["font.family"] = font_name
        rcParams["axes.unicode_minus"] = False
        print(f"✅ 한글 폰트 설정: {font_name}")
        print(f"   경로: {KOREAN_FONT_PATH}")
    else:
        print("⚠️ 한글 폰트를 찾을 수 없습니다. 기본 폰트를 사용합니다.")
        rcParams["axes.unicode_minus"] = False


# Seaborn 스타일을 먼저 설정한 후 한글 폰트를 적용해야
# seaborn이 폰트 설정을 덮어쓰지 않음
sns.set_style("whitegrid")
sns.set_palette("husl")
setup_korean_font()

# 현재 스크립트 경로 기준으로 maga.png 경로 설정
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MASK_IMAGE_PATH = os.path.join(SCRIPT_DIR, "car.png")

SAVE_DIR = "data_analysis"
os.makedirs(SAVE_DIR, exist_ok=True)


# ============================================================
# 1. 데이터 로드
# ============================================================
def load_naver_data():
    """Naver 크롤링 데이터 로드"""
    blog_path = "data_naver/naver_blog_자율주행_의료AI.csv"
    news_path = "data_naver/naver_news_자율주행_의료AI.csv"

    df_blog, df_news = None, None

    if os.path.exists(blog_path):
        df_blog = pd.read_csv(blog_path)
        print(f"📝 블로그 데이터 로드: {len(df_blog)}건")
    else:
        print(f"⚠️ 블로그 데이터 없음: {blog_path}")

    if os.path.exists(news_path):
        df_news = pd.read_csv(news_path)
        print(f"📰 뉴스 데이터 로드: {len(df_news)}건")
    else:
        print(f"⚠️ 뉴스 데이터 없음: {news_path}")

    return df_blog, df_news


def load_jobplanet_data():
    """잡플래닛 크롤링 데이터 로드"""
    company_path = "data_jobplanet/잡플래닛_기업정보_자율주행_의료AI.csv"
    review_path = "data_jobplanet/잡플래닛_리뷰_자율주행_의료AI.csv"
    interview_path = "data_jobplanet/잡플래닛_면접후기_자율주행_의료AI.csv"

    df_company, df_review, df_interview = None, None, None

    if os.path.exists(company_path):
        df_company = pd.read_csv(company_path)
        print(f"🏢 기업 정보 로드: {len(df_company)}건")
    else:
        print(f"⚠️ 기업 정보 없음: {company_path}")

    if os.path.exists(review_path):
        df_review = pd.read_csv(review_path)
        print(f"💬 리뷰 데이터 로드: {len(df_review)}건")
    else:
        print(f"⚠️ 리뷰 데이터 없음: {review_path}")

    if os.path.exists(interview_path):
        df_interview = pd.read_csv(interview_path)
        print(f"🎤 면접 데이터 로드: {len(df_interview)}건")
    else:
        print(f"⚠️ 면접 데이터 없음: {interview_path}")

    return df_company, df_review, df_interview


# ============================================================
# 2. 기술스택 키워드 추출
# ============================================================
TECH_KEYWORDS = {
    "Python": r"\bPython\b|\b파이썬\b",
    "C++": r"\bC\+\+\b|\bCPP\b",
    "C": r"\b[Cc]언어\b|\bC language\b",
    "Java": r"\bJava\b|\b자바\b",
    "MATLAB": r"\bMATLAB\b|\b매트랩\b",
    "R": r"\bR\b(?!OS|NN)",
    "SQL": r"\bSQL\b",
    "PyTorch": r"\bPyTorch\b|\b파이토치\b",
    "TensorFlow": r"\bTensorFlow\b|\b텐서플로\b",
    "Keras": r"\bKeras\b|\b케라스\b",
    "scikit-learn": r"\bscikit-learn\b|\bsklearn\b",
    "OpenCV": r"\bOpenCV\b",
    "ROS": r"\bROS\b|\bROS2\b",
    "SLAM": r"\bSLAM\b",
    "LiDAR": r"\bLiDAR\b|\b라이다\b",
    "센서퓨전": r"\b센서\s*퓨전\b|\bSensor\s*Fusion\b",
    "ADAS": r"\bADAS\b",
    "CARLA": r"\bCARLA\b|\b카를라\b",
    "V2X": r"\bV2X\b",
    "CAN": r"\bCAN\b|\bCAN\s*통신\b",
    "AUTOSAR": r"\bAUTOSAR\b",
    "DICOM": r"\bDICOM\b",
    "HL7/FHIR": r"\bHL7\b|\bFHIR\b",
    "의료영상": r"\b의료\s*영상\b|\bMedical\s*Image\b",
    "CT/MRI": r"\bCT\b|\bMRI\b|\bX-ray\b|\bX선\b",
    "자연어처리(NLP)": r"\bNLP\b|\b자연어\s*처리\b",
    "Docker": r"\bDocker\b|\b도커\b",
    "Kubernetes": r"\bKubernetes\b|\bk8s\b",
    "AWS": r"\bAWS\b",
    "GCP": r"\bGCP\b|\bGoogle\s*Cloud\b",
    "Git": r"\bGit\b|\bGitHub\b",
    "Linux": r"\bLinux\b|\b리눅스\b",
    "Pandas": r"\bPandas\b|\b판다스\b",
    "NumPy": r"\bNumPy\b|\b넘파이\b",
    "Spark": r"\bSpark\b|\bPySpark\b",
}

CERT_KEYWORDS = {
    "정보처리기사": r"정보처리기사",
    "빅데이터분석기사": r"빅데이터\s*분석\s*기사",
    "ADsP": r"\bADsP\b",
    "ADP": r"\bADP\b",
    "SQLD": r"\bSQLD\b|\bSQL\s*개발자\b",
    "SQLP": r"\bSQLP\b",
    "데이터분석준전문가": r"데이터\s*분석\s*준전문가",
    "AWS 자격증": r"\bAWS\b.*자격|AWS\s*(SAA|SAP|CLF)",
    "TOEIC": r"\bTOEIC\b|\b토익\b",
    "OPIc": r"\bOPIc\b|\b오픽\b",
    "컴퓨터활용능력": r"컴퓨터\s*활용\s*능력|컴활",
    "리눅스마스터": r"리눅스\s*마스터",
    "네트워크관리사": r"네트워크\s*관리사",
    "OPIC": r"\bOPIC\b",
}


def extract_keywords(texts, keyword_dict):
    """텍스트 목록에서 키워드 빈도 추출"""
    counter = Counter()
    for text in texts:
        if not isinstance(text, str):
            continue
        for keyword, pattern in keyword_dict.items():
            if re.search(pattern, text, re.IGNORECASE):
                counter[keyword] += 1
    return counter


# ============================================================
# 3. 시각화 함수들
# ============================================================


def plot_keyword_frequency(df, title="키워드별 수집 건수", filename="keyword_freq.png"):
    """검색 키워드별 수집 건수 막대그래프"""
    if df is None or "검색키워드" not in df.columns:
        return

    fig, ax = plt.subplots(figsize=(12, 6))
    counts = df["검색키워드"].value_counts()

    colors = sns.color_palette("viridis", len(counts))
    bars = ax.barh(range(len(counts)), counts.values, color=colors)
    ax.set_yticks(range(len(counts)))
    ax.set_yticklabels(counts.index, fontsize=10)
    ax.set_xlabel("수집 건수", fontsize=12)
    ax.set_title(title, fontsize=16, fontweight="bold", pad=15)

    for bar, val in zip(bars, counts.values):
        ax.text(
            bar.get_width() + 0.5,
            bar.get_y() + bar.get_height() / 2,
            str(val),
            va="center",
            fontsize=9,
        )

    plt.tight_layout()
    save_path = os.path.join(SAVE_DIR, filename)
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  📊 저장: {save_path}")


def plot_tech_stack(texts, title="요구 기술스택 빈도 분석", filename="tech_stack.png"):
    """기술스택 빈도 분석 막대그래프"""
    tech_counts = extract_keywords(texts, TECH_KEYWORDS)

    if not tech_counts:
        print("  ⚠️ 기술스택 키워드를 찾을 수 없습니다.")
        return tech_counts

    top_techs = tech_counts.most_common(20)
    names = [t[0] for t in top_techs]
    values = [t[1] for t in top_techs]

    fig, ax = plt.subplots(figsize=(12, 7))
    colors = sns.color_palette("coolwarm_r", len(names))
    bars = ax.barh(range(len(names)), values, color=colors)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=11)
    ax.set_xlabel("언급 빈도", fontsize=12)
    ax.set_title(title, fontsize=16, fontweight="bold", pad=15)
    ax.invert_yaxis()

    for bar, val in zip(bars, values):
        ax.text(
            bar.get_width() + 0.3,
            bar.get_y() + bar.get_height() / 2,
            str(val),
            va="center",
            fontsize=10,
            fontweight="bold",
        )

    plt.tight_layout()
    save_path = os.path.join(SAVE_DIR, filename)
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  📊 저장: {save_path}")

    return tech_counts


def plot_cert_frequency(texts, title="자격증 언급 빈도", filename="cert_freq.png"):
    """자격증 빈도 분석"""
    cert_counts = extract_keywords(texts, CERT_KEYWORDS)

    if not cert_counts:
        print("  ⚠️ 자격증 키워드를 찾을 수 없습니다.")
        return cert_counts

    top_certs = cert_counts.most_common(15)
    names = [t[0] for t in top_certs]
    values = [t[1] for t in top_certs]

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = sns.color_palette("YlOrRd_r", len(names))
    bars = ax.bar(range(len(names)), values, color=colors)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=45, ha="right", fontsize=10)
    ax.set_ylabel("언급 빈도", fontsize=12)
    ax.set_title(title, fontsize=16, fontweight="bold", pad=15)

    for bar, val in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.2,
            str(val),
            ha="center",
            fontsize=10,
            fontweight="bold",
        )

    plt.tight_layout()
    save_path = os.path.join(SAVE_DIR, filename)
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  📊 저장: {save_path}")

    return cert_counts


def plot_field_comparison(
    df_blog, title="자율주행 vs 의료AI 블로그 언급량", filename="field_comparison.png"
):
    """자율주행 vs 의료 AI 분야 비교"""
    if df_blog is None:
        return

    auto_keywords = ["자율주행", "ADAS", "ROS"]
    medical_keywords = ["의료", "헬스케어", "의료AI"]

    auto_count = 0
    medical_count = 0

    for _, row in df_blog.iterrows():
        kw = str(row.get("검색키워드", ""))
        if any(k in kw for k in auto_keywords):
            auto_count += 1
        if any(k in kw for k in medical_keywords):
            medical_count += 1

    fig, ax = plt.subplots(figsize=(8, 5))
    categories = ["자율주행 분야", "의료 AI 분야"]
    values = [auto_count, medical_count]
    colors = ["#0891B2", "#F59E0B"]

    bars = ax.bar(
        categories, values, color=colors, width=0.5, edgecolor="white", linewidth=2
    )

    for bar, val in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1,
            f"{val}건",
            ha="center",
            fontsize=14,
            fontweight="bold",
        )

    ax.set_ylabel("수집 건수", fontsize=12)
    ax.set_title(title, fontsize=16, fontweight="bold", pad=15)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    save_path = os.path.join(SAVE_DIR, filename)
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  📊 저장: {save_path}")


def plot_wordcloud_with_mask(
    texts,
    title="자율주행·의료AI 취업 키워드 워드클라우드",
    filename="wordcloud_mask.png",
):
    """maga.png 마스크를 적용한 워드클라우드 생성"""
    try:
        from wordcloud import WordCloud, ImageColorGenerator
    except ImportError:
        print("  ⚠️ wordcloud 패키지가 필요합니다: pip install wordcloud")
        return

    # --- 마스크 이미지 로드 ---
    if not os.path.exists(MASK_IMAGE_PATH):
        print(f"  ⚠️ 마스크 이미지를 찾을 수 없습니다: {MASK_IMAGE_PATH}")
        print("  → maga.png 파일이 스크립트와 같은 폴더에 있어야 합니다.")
        return

    mask_image = Image.open(MASK_IMAGE_PATH).convert("RGBA")

    # RGBA -> RGB 변환 (투명 배경을 흰색으로 처리)
    # WordCloud는 흰색(255)인 영역을 비워두므로 배경을 흰색으로 채움
    rgb_image = Image.new("RGB", mask_image.size, (255, 255, 255))
    rgb_image.paste(mask_image, mask=mask_image.split()[3])  # 알파 채널을 마스크로 사용

    mask_array = np.array(rgb_image)

    print(f"  🖼️ 마스크 이미지 로드 완료: {mask_image.size[0]}x{mask_image.size[1]}px")

    # --- 텍스트 합치기 ---
    combined = " ".join([str(t) for t in texts if isinstance(t, str)])

    # --- 불용어 ---
    stopwords = {
        "있는",
        "하는",
        "있다",
        "합니다",
        "입니다",
        "등",
        "및",
        "또한",
        "위해",
        "통해",
        "대한",
        "관련",
        "이상",
        "이하",
        "필요",
        "해당",
        "것이",
        "하고",
        "에서",
        "으로",
        "그리고",
        "하며",
        "되는",
        "위한",
    }

    # --- WordCloud 생성 (마스크 적용) ---
    wc_params = {
        "mask": mask_array,
        "background_color": "white",
        "max_words": 200,
        "max_font_size": 150,
        "min_font_size": 8,
        "stopwords": stopwords,
        "colormap": "viridis",
        "contour_width": 2,
        "contour_color": "#333333",
    }

    if KOREAN_FONT_PATH:
        wc_params["font_path"] = KOREAN_FONT_PATH

    wc = WordCloud(**wc_params)
    wc.generate(combined)

    # --- 이미지 색상을 워드클라우드에 입히기 (선택) ---
    # 마스크 이미지의 원본 색상을 글자에 적용
    image_colors = ImageColorGenerator(mask_array)
    wc.recolor(color_func=image_colors)

    # --- 시각화 ---
    fig, axes = plt.subplots(1, 2, figsize=(20, 10))

    # 왼쪽: 마스크 모양 워드클라우드
    axes[0].imshow(wc, interpolation="bilinear")
    axes[0].axis("off")
    axes[0].set_title(title, fontsize=18, fontweight="bold", pad=15)

    # 오른쪽: 원본 마스크 이미지 (비교용)
    axes[1].imshow(mask_array, interpolation="bilinear")
    axes[1].axis("off")
    axes[1].set_title("원본 마스크 이미지 (maga.png)", fontsize=14, pad=15)

    plt.tight_layout()
    save_path = os.path.join(SAVE_DIR, filename)
    plt.savefig(save_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"  📊 저장: {save_path}")

    # --- 워드클라우드만 단독 저장 ---
    fig2, ax2 = plt.subplots(figsize=(12, 12))
    ax2.imshow(wc, interpolation="bilinear")
    ax2.axis("off")
    ax2.set_title(title, fontsize=18, fontweight="bold", pad=15)

    solo_path = os.path.join(SAVE_DIR, "wordcloud_mask_only.png")
    plt.savefig(solo_path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"  📊 저장: {solo_path}")


def plot_company_ratings(df_company, filename="company_ratings.png"):
    """기업별 평점 비교 (잡플래닛 데이터)"""
    if df_company is None or "전체평점" not in df_company.columns:
        print("  ⚠️ 기업 평점 데이터가 없습니다.")
        return

    df = df_company.copy()
    df["평점_숫자"] = df["전체평점"].apply(
        lambda x: (
            float(re.search(r"[\d.]+", str(x)).group())
            if pd.notna(x) and re.search(r"[\d.]+", str(x))
            else None
        )
    )
    df = df.dropna(subset=["평점_숫자"])

    if df.empty:
        return

    fig, ax = plt.subplots(figsize=(14, 7))

    colors = (
        df["분야"].map({"자율주행": "#0891B2", "의료AI": "#F59E0B"}).fillna("#94A3B8")
    )

    bars = ax.barh(range(len(df)), df["평점_숫자"].values, color=colors)
    ax.set_yticks(range(len(df)))
    ax.set_yticklabels(df["기업명"].values, fontsize=10)
    ax.set_xlabel("평점 (5.0 만점)", fontsize=12)
    ax.set_title(
        "자율주행·의료AI 기업 잡플래닛 평점 비교",
        fontsize=16,
        fontweight="bold",
        pad=15,
    )
    ax.set_xlim(0, 5.5)

    for bar, val in zip(bars, df["평점_숫자"].values):
        ax.text(
            bar.get_width() + 0.05,
            bar.get_y() + bar.get_height() / 2,
            f"{val:.1f}",
            va="center",
            fontsize=10,
            fontweight="bold",
        )

    from matplotlib.patches import Patch

    legend_elements = [
        Patch(facecolor="#0891B2", label="자율주행"),
        Patch(facecolor="#F59E0B", label="의료AI"),
    ]
    ax.legend(handles=legend_elements, loc="lower right", fontsize=11)

    plt.tight_layout()
    save_path = os.path.join(SAVE_DIR, filename)
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  📊 저장: {save_path}")


def plot_news_trend(df_news, filename="news_trend.png"):
    """뉴스 게시 날짜 트렌드 분석"""
    if df_news is None or "게시일자" not in df_news.columns:
        return

    df = df_news.copy()
    df["게시일자_dt"] = pd.to_datetime(df["게시일자"], errors="coerce")
    df = df.dropna(subset=["게시일자_dt"])

    if df.empty:
        return

    df["월"] = df["게시일자_dt"].dt.to_period("M")
    monthly = df.groupby("월").size()

    fig, ax = plt.subplots(figsize=(12, 5))
    monthly.plot(
        kind="line", ax=ax, color="#0891B2", linewidth=2, marker="o", markersize=5
    )
    ax.fill_between(range(len(monthly)), monthly.values, alpha=0.15, color="#0891B2")
    ax.set_xlabel("월", fontsize=12)
    ax.set_ylabel("뉴스 건수", fontsize=12)
    ax.set_title(
        "자율주행·의료AI 채용 관련 뉴스 추이", fontsize=16, fontweight="bold", pad=15
    )
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    save_path = os.path.join(SAVE_DIR, filename)
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  📊 저장: {save_path}")


# ============================================================
# 4. 메인 실행
# ============================================================
def main():
    print("=" * 60)
    print("📊 자율주행·의료AI 취업 동향 분석 및 시각화")
    print("   (maga.png 마스크 워드클라우드 버전)")
    print("=" * 60)
    print()

    # 데이터 로드
    print("📂 데이터 로드 중...")
    df_blog, df_news = load_naver_data()
    df_company, df_review, df_interview = load_jobplanet_data()
    print()

    # ---- 분석 1: 키워드별 수집 건수 ----
    print("📈 분석 1: 키워드별 수집 건수")
    if df_blog is not None:
        plot_keyword_frequency(
            df_blog, "블로그 검색 키워드별 수집 건수", "blog_keyword_freq.png"
        )
    if df_news is not None:
        plot_keyword_frequency(
            df_news, "뉴스 검색 키워드별 수집 건수", "news_keyword_freq.png"
        )

    # ---- 분석 2: 기술스택 빈도 ----
    print("\n📈 분석 2: 기술스택 빈도 분석")
    all_texts = []
    if df_blog is not None:
        all_texts.extend(df_blog["제목"].tolist() + df_blog["내용요약"].tolist())
    if df_news is not None:
        all_texts.extend(df_news["제목"].tolist() + df_news["내용요약"].tolist())
    if df_review is not None and "장점" in df_review.columns:
        all_texts.extend(df_review["장점"].tolist() + df_review["단점"].tolist())

    if all_texts:
        tech_counts = plot_tech_stack(all_texts)
        if tech_counts:
            print("\n  🔧 기술스택 TOP 10:")
            for tech, count in tech_counts.most_common(10):
                print(f"     {tech}: {count}회")

    # ---- 분석 3: 자격증 빈도 ----
    print("\n📈 분석 3: 자격증 언급 빈도")
    if all_texts:
        cert_counts = plot_cert_frequency(all_texts)
        if cert_counts:
            print("\n  📜 자격증 TOP 5:")
            for cert, count in cert_counts.most_common(5):
                print(f"     {cert}: {count}회")

    # ---- 분석 4: 분야 비교 ----
    print("\n📈 분석 4: 자율주행 vs 의료AI 비교")
    plot_field_comparison(df_blog)

    # ---- 분석 5: 마스크 워드클라우드 ----
    print("\n📈 분석 5: 마스크 워드클라우드 (maga.png)")
    if all_texts:
        plot_wordcloud_with_mask(all_texts)

    # ---- 분석 6: 기업 평점 비교 ----
    print("\n📈 분석 6: 기업 평점 비교")
    plot_company_ratings(df_company)

    # ---- 분석 7: 뉴스 트렌드 ----
    print("\n📈 분석 7: 뉴스 트렌드 분석")
    plot_news_trend(df_news)

    # ---- 결과 요약 ----
    print()
    print("=" * 60)
    print("✅ 분석 완료! 생성된 차트 목록:")
    print("=" * 60)
    for f in sorted(os.listdir(SAVE_DIR)):
        if f.endswith(".png"):
            print(f"  📊 {os.path.join(SAVE_DIR, f)}")

    print(f"\n📁 분석 결과 저장 경로: {os.path.abspath(SAVE_DIR)}")
    print("🎉 시각화 완료!")


if __name__ == "__main__":
    main()

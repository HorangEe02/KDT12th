"""
=============================================================
📌 데이터 분석 및 시각화 - 자율주행·의료 AI 취업 동향
=============================================================
- Naver OpenAPI + 잡플래닛 크롤링 데이터를 종합 분석
- 시각화 차트 생성 및 저장
=============================================================
⚠️ 실행 전: crawl_naver_api.py, crawl_jobplanet.py를 먼저 실행하여
   data_naver/, data_jobplanet/ 폴더에 데이터가 있어야 합니다.
=============================================================
"""

import os
import re
from collections import Counter

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib import rcParams
import seaborn as sns


# ============================================================
# 0. 한글 폰트 설정
# ============================================================
def setup_korean_font():
    """시스템에서 한글 폰트를 찾아서 설정"""
    # 사용 가능한 한글 폰트 목록
    korean_fonts = [
        "Malgun Gothic",  # Windows
        "AppleGothic",  # macOS
        "Apple SD Gothic Neo",  # macOS
        "NanumGothic",  # 나눔고딕
        "NanumBarunGothic",
        "Noto Sans KR",
        "Noto Sans CJK KR",
        "DejaVu Sans",
    ]

    available_fonts = [f.name for f in fm.fontManager.ttflist]

    for font_name in korean_fonts:
        if font_name in available_fonts:
            rcParams["font.family"] = font_name
            rcParams["axes.unicode_minus"] = False
            print(f"✅ 한글 폰트 설정: {font_name}")
            return

    # 폰트를 찾지 못한 경우
    print("⚠️ 한글 폰트를 찾을 수 없습니다. 기본 폰트를 사용합니다.")
    print("   → pip install matplotlib 후 나눔고딕 설치를 권장합니다.")
    rcParams["axes.unicode_minus"] = False


setup_korean_font()

# Seaborn 스타일 설정
sns.set_style("whitegrid")
sns.set_palette("husl")

# 저장 경로
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
# 자율주행·의료AI 분야 기술스택 사전
TECH_KEYWORDS = {
    # 프로그래밍 언어
    "Python": r"\bPython\b|\b파이썬\b",
    "C++": r"\bC\+\+\b|\bCPP\b",
    "C": r"\b[Cc]언어\b|\bC language\b",
    "Java": r"\bJava\b|\b자바\b",
    "MATLAB": r"\bMATLAB\b|\b매트랩\b",
    "R": r"\bR\b(?!OS|NN)",
    "SQL": r"\bSQL\b",
    # 딥러닝/ML 프레임워크
    "PyTorch": r"\bPyTorch\b|\b파이토치\b",
    "TensorFlow": r"\bTensorFlow\b|\b텐서플로\b",
    "Keras": r"\bKeras\b|\b케라스\b",
    "scikit-learn": r"\bscikit-learn\b|\bsklearn\b",
    "OpenCV": r"\bOpenCV\b",
    # 자율주행 특화
    "ROS": r"\bROS\b|\bROS2\b",
    "SLAM": r"\bSLAM\b",
    "LiDAR": r"\bLiDAR\b|\b라이다\b",
    "센서퓨전": r"\b센서\s*퓨전\b|\bSensor\s*Fusion\b",
    "ADAS": r"\bADAS\b",
    "CARLA": r"\bCARLA\b|\b카를라\b",
    "V2X": r"\bV2X\b",
    "CAN": r"\bCAN\b|\bCAN\s*통신\b",
    "AUTOSAR": r"\bAUTOSAR\b",
    # 의료 AI 특화
    "DICOM": r"\bDICOM\b",
    "HL7/FHIR": r"\bHL7\b|\bFHIR\b",
    "의료영상": r"\b의료\s*영상\b|\bMedical\s*Image\b",
    "CT/MRI": r"\bCT\b|\bMRI\b|\bX-ray\b|\bX선\b",
    "자연어처리(NLP)": r"\bNLP\b|\b자연어\s*처리\b",
    # 인프라/도구
    "Docker": r"\bDocker\b|\b도커\b",
    "Kubernetes": r"\bKubernetes\b|\bk8s\b",
    "AWS": r"\bAWS\b",
    "GCP": r"\bGCP\b|\bGoogle\s*Cloud\b",
    "Git": r"\bGit\b|\bGitHub\b",
    "Linux": r"\bLinux\b|\b리눅스\b",
    # 데이터/분석
    "Pandas": r"\bPandas\b|\b판다스\b",
    "NumPy": r"\bNumPy\b|\b넘파이\b",
    "Spark": r"\bSpark\b|\bPySpark\b",
}

# 자격증 사전
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
    """
    텍스트 목록에서 키워드 빈도 추출

    Parameters:
        texts (list): 텍스트 목록
        keyword_dict (dict): {키워드명: 정규식 패턴}

    Returns:
        Counter: 키워드별 빈도
    """
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

    # 값 표시
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

    # 상위 20개
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


def plot_wordcloud(
    texts, title="자율주행·의료AI 취업 키워드 워드클라우드", filename="wordcloud.png"
):
    """워드클라우드 생성"""
    try:
        from wordcloud import WordCloud
    except ImportError:
        print("  ⚠️ wordcloud 패키지가 필요합니다: pip install wordcloud")
        return

    # 한글 폰트 경로 탐색
    font_paths = [
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf",
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "C:/Windows/Fonts/malgun.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]

    font_path = None
    for fp in font_paths:
        if os.path.exists(fp):
            font_path = fp
            break

    # 텍스트 합치기
    combined = " ".join([str(t) for t in texts if isinstance(t, str)])

    # 불용어
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

    wc_params = {
        "width": 1200,
        "height": 600,
        "background_color": "white",
        "max_words": 100,
        "max_font_size": 100,
        "stopwords": stopwords,
        "colormap": "viridis",
    }

    if font_path:
        wc_params["font_path"] = font_path

    wc = WordCloud(**wc_params)
    wc.generate(combined)

    fig, ax = plt.subplots(figsize=(14, 7))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    ax.set_title(title, fontsize=18, fontweight="bold", pad=15)

    save_path = os.path.join(SAVE_DIR, filename)
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  📊 저장: {save_path}")


def plot_company_ratings(df_company, filename="company_ratings.png"):
    """기업별 평점 비교 (잡플래닛 데이터)"""
    if df_company is None or "전체평점" not in df_company.columns:
        print("  ⚠️ 기업 평점 데이터가 없습니다.")
        return

    # 평점 숫자 추출
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

    # 분야별 색상
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

    # 값 표시
    for bar, val in zip(bars, df["평점_숫자"].values):
        ax.text(
            bar.get_width() + 0.05,
            bar.get_y() + bar.get_height() / 2,
            f"{val:.1f}",
            va="center",
            fontsize=10,
            fontweight="bold",
        )

    # 범례
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

    # ---- 분석 5: 워드클라우드 ----
    print("\n📈 분석 5: 워드클라우드")
    if all_texts:
        plot_wordcloud(all_texts)

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

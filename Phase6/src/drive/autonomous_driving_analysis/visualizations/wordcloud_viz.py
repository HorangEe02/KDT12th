"""
=============================================================
워드클라우드 시각화 모듈
=============================================================
car.png 마스크를 활용한 자율주행/모빌리티 특화 워드클라우드 6종 생성
=============================================================
"""

import os

import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib import rcParams

from config.settings import OUTPUTS_CHARTS_DIR, WORDCLOUD_MASK_PATH, KOREAN_FONT_CANDIDATES

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


setup_korean_font()


class WordCloudVisualizer:
    """워드클라우드 시각화 (car.png 마스크 지원)"""

    # 공통 불용어
    STOPWORDS = {
        "있는", "하는", "있다", "합니다", "입니다", "등", "및", "또한",
        "위해", "통해", "대한", "관련", "이상", "이하", "필요", "해당",
        "것이", "하고", "에서", "으로", "그리고", "하며", "되는", "위한",
        "수행", "가능", "경험", "우대", "기반", "활용", "개발", "진행",
        "이해", "능력", "업무", "분야", "것으로", "같은", "때문",
    }

    def __init__(self, save_dir: str = None):
        self.save_dir = save_dir or OUTPUTS_CHARTS_DIR
        os.makedirs(self.save_dir, exist_ok=True)
        self._mask = self._load_mask()  # 마스크 1회 로드 후 캐싱

    def _get_font_path(self) -> str:
        return KOREAN_FONT_PATH

    def _load_mask(self) -> np.ndarray:
        """car.png 마스크 이미지 로드 (이진화 처리)"""
        if not os.path.exists(WORDCLOUD_MASK_PATH):
            print(f"  ⚠️ 마스크 이미지를 찾을 수 없습니다: {WORDCLOUD_MASK_PATH}")
            return None

        mask_image = Image.open(WORDCLOUD_MASK_PATH).convert("L")  # 그레이스케일
        mask_array = np.array(mask_image)

        # 이진화: 128 기준, 검정(자동차)=0, 흰색(배경)=255
        mask_array = np.where(mask_array < 128, 0, 255).astype(np.uint8)

        # WordCloud는 (H, W, 3) RGB 배열 필요
        mask_rgb = np.stack([mask_array] * 3, axis=-1)

        print(f"  🖼️ 마스크 이미지 로드: {mask_image.size[0]}x{mask_image.size[1]}px")
        return mask_rgb

    def _create_wordcloud(self, text_data, title: str, filename: str,
                          colormap: str = "viridis"):
        """
        워드클라우드 핵심 생성 메서드 (마스크 항상 적용)

        Parameters:
            text_data: 텍스트 리스트 또는 단어-빈도 딕셔너리
            title: 차트 제목
            filename: 저장 파일명
            colormap: 색상맵
        """
        try:
            from wordcloud import WordCloud
        except ImportError:
            print("  ⚠️ wordcloud 패키지 필요: pip install wordcloud")
            return

        # 데이터 유형 판별
        is_freq_dict = isinstance(text_data, dict)

        if not is_freq_dict:
            if isinstance(text_data, list):
                combined = " ".join(str(t) for t in text_data if isinstance(t, str))
            else:
                combined = str(text_data)
            if not combined.strip():
                print(f"  ⚠️ '{title}' - 텍스트 데이터가 없습니다.")
                return
        else:
            if not text_data:
                print(f"  ⚠️ '{title}' - 텍스트 데이터가 없습니다.")
                return

        wc_params = {
            "width": 1200,
            "height": 800,
            "background_color": "white",
            "max_words": 300,
            "max_font_size": 200,
            "min_font_size": 6,
            "prefer_horizontal": 0.7,
            "relative_scaling": 0.5,
            "stopwords": self.STOPWORDS,
            "colormap": colormap,
        }

        font_path = self._get_font_path()
        if font_path:
            wc_params["font_path"] = font_path

        if self._mask is not None:
            wc_params["mask"] = self._mask
            wc_params["contour_width"] = 3
            wc_params["contour_color"] = "#333333"
            wc_params.pop("width", None)
            wc_params.pop("height", None)

        wc = WordCloud(**wc_params)

        # dict → generate_from_frequencies, list/str → generate
        if is_freq_dict:
            # 불용어 필터링 적용
            filtered = {k: v for k, v in text_data.items()
                        if k not in self.STOPWORDS and len(k) > 1}
            wc.generate_from_frequencies(filtered)
        else:
            wc.generate(combined)

        fig, ax = plt.subplots(figsize=(12, 14) if self._mask is not None else (14, 7))
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")
        ax.set_title(title, fontsize=18, fontweight="bold", pad=15)

        plt.tight_layout()
        save_path = os.path.join(self.save_dir, filename)
        plt.savefig(save_path, dpi=300, bbox_inches="tight", facecolor="white")
        plt.close()
        print(f"  📊 저장: {save_path}")

    def generate_tech_stack_wordcloud(self, tech_data):
        """채용공고 기술스택 워드클라우드 (car.png 마스크 적용)"""
        print("\n  [1/6] 채용공고 기술스택 워드클라우드")
        self._create_wordcloud(
            tech_data,
            "자율주행/모빌리티 채용공고 기술스택 워드클라우드",
            "wc_tech_stack.png",
            colormap="cool",
        )

    def generate_blog_keyword_wordcloud(self, blog_texts):
        """블로그 취준 키워드 워드클라우드"""
        print("\n  [2/6] 블로그 취준 키워드 워드클라우드")
        self._create_wordcloud(
            blog_texts,
            "자율주행/모빌리티 취준 블로그 키워드 워드클라우드",
            "wc_blog_keywords.png",
            colormap="viridis",
        )

    def generate_interview_keyword_wordcloud(self, interview_texts):
        """면접후기 키워드 워드클라우드"""
        print("\n  [3/6] 면접후기 키워드 워드클라우드")
        self._create_wordcloud(
            interview_texts,
            "자율주행/모빌리티 면접후기 키워드 워드클라우드",
            "wc_interview.png",
            colormap="plasma",
        )

    def generate_review_pros_wordcloud(self, pros_texts):
        """기업리뷰 장점 워드클라우드"""
        print("\n  [4/6] 기업리뷰 장점 워드클라우드")
        self._create_wordcloud(
            pros_texts,
            "자율주행/모빌리티 기업 리뷰 - 장점 워드클라우드",
            "wc_review_pros.png",
            colormap="Greens",
        )

    def generate_review_cons_wordcloud(self, cons_texts):
        """기업리뷰 단점 워드클라우드"""
        print("\n  [5/6] 기업리뷰 단점 워드클라우드")
        self._create_wordcloud(
            cons_texts,
            "자율주행/모빌리티 기업 리뷰 - 단점 워드클라우드",
            "wc_review_cons.png",
            colormap="Reds",
        )

    def generate_job_requirements_wordcloud(self, req_texts):
        """채용 자격요건/우대사항 워드클라우드 (원티드 등 채용 데이터)"""
        print("\n  [7] 채용 자격요건/우대사항 워드클라우드")
        self._create_wordcloud(
            req_texts,
            "자율주행/모빌리티 채용 자격요건·우대사항 워드클라우드",
            "wc_job_requirements.png",
            colormap="coolwarm",
        )

    def generate_domain_wordcloud(self, domain_texts):
        """자율주행 도메인 키워드 워드클라우드 (car.png 마스크 적용)"""
        print("\n  [6/6] 자율주행 도메인 키워드 워드클라우드")
        self._create_wordcloud(
            domain_texts,
            "자율주행/모빌리티 도메인 키워드 워드클라우드",
            "wc_domain.png",
            colormap="YlGn",
        )

    def generate_all(self, data_dict: dict):
        """
        전체 워드클라우드 생성

        Parameters:
            data_dict: {
                "tech_stack": 기술스택 텍스트/딕셔너리,
                "blog": 블로그 텍스트 리스트,
                "interview": 면접후기 텍스트 리스트,
                "review_pros": 장점 텍스트 리스트,
                "review_cons": 단점 텍스트 리스트,
                "domain": 도메인 텍스트/딕셔너리,
            }
        """
        print("=" * 60)
        print("🎨 워드클라우드 시각화 생성 (6종)")
        print("=" * 60)

        if data_dict.get("tech_stack"):
            self.generate_tech_stack_wordcloud(data_dict["tech_stack"])
        if data_dict.get("blog"):
            self.generate_blog_keyword_wordcloud(data_dict["blog"])
        if data_dict.get("interview"):
            self.generate_interview_keyword_wordcloud(data_dict["interview"])
        if data_dict.get("review_pros"):
            self.generate_review_pros_wordcloud(data_dict["review_pros"])
        if data_dict.get("review_cons"):
            self.generate_review_cons_wordcloud(data_dict["review_cons"])
        if data_dict.get("domain"):
            self.generate_domain_wordcloud(data_dict["domain"])
        if data_dict.get("job_requirements"):
            self.generate_job_requirements_wordcloud(data_dict["job_requirements"])

        print("\n✅ 워드클라우드 생성 완료!")

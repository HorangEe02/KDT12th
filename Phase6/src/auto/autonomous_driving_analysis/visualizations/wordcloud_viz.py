"""
워드클라우드 시각화 모듈
마스크 이미지(m1.png, m2.png, car.png)를 활용한 5종 워드클라우드 생성
"""

import logging
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
from wordcloud import WordCloud

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from config.settings import FONT_PATH, OUTPUT_CHARTS_DIR, WORDCLOUD_MASK_PATHS

logger = logging.getLogger(__name__)


class WordCloudVisualizer:
    """워드클라우드 시각화 생성기"""

    def __init__(self):
        self.font_path = FONT_PATH
        self.output_dir = OUTPUT_CHARTS_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.width = 1200
        self.height = 800
        self.dpi = 300
        self.background_color = "white"

        if not self.font_path:
            logger.warning("한글 폰트를 찾을 수 없습니다. 워드클라우드에 한글이 깨질 수 있습니다.")

    def _load_mask(self, mask_name: str) -> np.ndarray:
        """마스크 이미지 로드"""
        mask_path = WORDCLOUD_MASK_PATHS.get(mask_name)
        if not mask_path or not Path(mask_path).exists():
            logger.warning(f"마스크 이미지를 찾을 수 없습니다: {mask_name} ({mask_path})")
            return None

        try:
            mask_image = Image.open(mask_path).convert("RGBA")

            # 흰색 배경 이미지 생성
            background = Image.new("RGBA", mask_image.size, (255, 255, 255, 255))

            # 마스크 이미지 합성 (알파 채널 고려)
            if mask_image.mode == "RGBA":
                background.paste(mask_image, mask=mask_image.split()[3])
            else:
                background.paste(mask_image)

            # RGB로 변환 후 numpy 배열로
            mask_array = np.array(background.convert("RGB"))
            logger.info(f"마스크 로드 완료: {mask_name} ({mask_array.shape})")
            return mask_array
        except Exception as e:
            logger.error(f"마스크 로드 실패: {e}")
            return None

    def _create_wordcloud(self, word_freq: dict, mask_name: str = None, colormap: str = "Blues") -> WordCloud:
        """WordCloud 객체 생성"""
        kwargs = {
            "width": self.width,
            "height": self.height,
            "background_color": self.background_color,
            "colormap": colormap,
            "max_words": 200,
            "max_font_size": 150,
            "min_font_size": 10,
            "prefer_horizontal": 0.7,
            "random_state": 42,
        }

        if self.font_path:
            kwargs["font_path"] = self.font_path

        if mask_name:
            mask = self._load_mask(mask_name)
            if mask is not None:
                kwargs["mask"] = mask
                kwargs["contour_width"] = 2
                kwargs["contour_color"] = "steelblue"

        wc = WordCloud(**kwargs)
        wc.generate_from_frequencies(word_freq)
        return wc

    def _save_wordcloud(self, wc: WordCloud, title: str, filename: str):
        """워드클라우드 저장"""
        fig, ax = plt.subplots(1, 1, figsize=(self.width / 100, self.height / 100))
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")
        ax.set_title(title, fontsize=20, fontweight="bold", pad=20,
                     fontproperties=None)

        # 한글 폰트 설정
        if self.font_path:
            from matplotlib import font_manager
            font_prop = font_manager.FontProperties(fname=self.font_path)
            ax.set_title(title, fontsize=20, fontweight="bold", pad=20, fontproperties=font_prop)

        filepath = self.output_dir / filename
        fig.savefig(filepath, dpi=self.dpi, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        logger.info(f"워드클라우드 저장: {filepath}")

    def create_tech_stack_wordcloud(self, tech_freq: dict):
        """채용공고 기술스택 워드클라우드 (car 마스크)"""
        if not tech_freq:
            logger.warning("기술스택 빈도 데이터가 비어있습니다.")
            return

        wc = self._create_wordcloud(tech_freq, mask_name="car", colormap="Blues")
        self._save_wordcloud(wc, "채용공고 기술스택 워드클라우드", "wc_tech_stack.png")

    def create_blog_keyword_wordcloud(self, word_freq: dict):
        """블로그 취준 키워드 워드클라우드 (m1 마스크)"""
        if not word_freq:
            logger.warning("블로그 키워드 빈도 데이터가 비어있습니다.")
            return

        wc = self._create_wordcloud(word_freq, mask_name="m1", colormap="Greens")
        self._save_wordcloud(wc, "블로그 취준 키워드 워드클라우드", "wc_blog_keywords.png")

    def create_interview_keyword_wordcloud(self, word_freq: dict):
        """면접후기 키워드 워드클라우드 (m2 마스크)"""
        if not word_freq:
            logger.warning("면접후기 키워드 빈도 데이터가 비어있습니다.")
            return

        wc = self._create_wordcloud(word_freq, mask_name="m2", colormap="Oranges")
        self._save_wordcloud(wc, "면접후기 키워드 워드클라우드", "wc_interview_keywords.png")

    def create_review_pros_wordcloud(self, word_freq: dict):
        """기업리뷰 장점 워드클라우드 (m1 마스크)"""
        if not word_freq:
            logger.warning("장점 키워드 빈도 데이터가 비어있습니다.")
            return

        wc = self._create_wordcloud(word_freq, mask_name="m1", colormap="YlGn")
        self._save_wordcloud(wc, "기업리뷰 장점 워드클라우드", "wc_review_pros.png")

    def create_review_cons_wordcloud(self, word_freq: dict):
        """기업리뷰 단점 워드클라우드 (m2 마스크)"""
        if not word_freq:
            logger.warning("단점 키워드 빈도 데이터가 비어있습니다.")
            return

        wc = self._create_wordcloud(word_freq, mask_name="m2", colormap="OrRd")
        self._save_wordcloud(wc, "기업리뷰 단점 워드클라우드", "wc_review_cons.png")

    def create_all(self, data: dict):
        """전체 워드클라우드 생성"""
        logger.info("=" * 40)
        logger.info("워드클라우드 생성 시작 (총 5개)")
        logger.info("=" * 40)

        if data.get("tech_freq"):
            self.create_tech_stack_wordcloud(data["tech_freq"])
        if data.get("blog_freq"):
            self.create_blog_keyword_wordcloud(data["blog_freq"])
        if data.get("interview_freq"):
            self.create_interview_keyword_wordcloud(data["interview_freq"])
        if data.get("pros_freq"):
            self.create_review_pros_wordcloud(data["pros_freq"])
        if data.get("cons_freq"):
            self.create_review_cons_wordcloud(data["cons_freq"])

        logger.info("워드클라우드 생성 완료")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    # 테스트
    test_freq = {
        "Python": 85, "C++": 72, "ROS": 65, "PyTorch": 58, "OpenCV": 52,
        "SLAM": 45, "LiDAR": 40, "딥러닝": 38, "Linux": 35, "Docker": 30,
        "TensorFlow": 28, "센서퓨전": 25, "MATLAB": 22, "Git": 20, "CUDA": 18,
    }

    viz = WordCloudVisualizer()
    viz.create_tech_stack_wordcloud(test_freq)

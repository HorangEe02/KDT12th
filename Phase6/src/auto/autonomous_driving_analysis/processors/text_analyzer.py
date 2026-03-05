"""
텍스트 분석 모듈
키워드 추출, 빈도 분석, 기술스택/자격증 매칭
"""

import re
import logging
from collections import Counter
import pandas as pd

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from config.settings import TECH_STACK_KEYWORDS, CERTIFICATE_KEYWORDS, STOPWORDS

logger = logging.getLogger(__name__)

# KoNLPy 임포트 시도
try:
    from konlpy.tag import Okt
    KONLPY_AVAILABLE = True
except ImportError:
    KONLPY_AVAILABLE = False
    logger.warning("KoNLPy가 설치되지 않았습니다. 정규식 기반 명사 추출을 사용합니다.")


class TextAnalyzer:
    """텍스트 데이터 분석 - 키워드 추출 및 빈도 분석"""

    def __init__(self):
        self.okt = None
        if KONLPY_AVAILABLE:
            try:
                self.okt = Okt()
                logger.info("KoNLPy Okt 형태소 분석기 초기화 완료")
            except Exception as e:
                logger.warning(f"Okt 초기화 실패: {e}")

        self.stopwords = set(STOPWORDS)

    def extract_nouns(self, text: str, min_length: int = 2) -> list:
        """텍스트에서 명사 추출"""
        if not text or not isinstance(text, str):
            return []

        if self.okt:
            # KoNLPy Okt 사용
            try:
                nouns = self.okt.nouns(text)
            except Exception:
                nouns = self._regex_extract_nouns(text)
        else:
            # 정규식 기반 폴백
            nouns = self._regex_extract_nouns(text)

        # 불용어 제거 및 최소 길이 필터
        nouns = [n for n in nouns if n not in self.stopwords and len(n) >= min_length]
        return nouns

    @staticmethod
    def _regex_extract_nouns(text: str) -> list:
        """정규식 기반 명사 추출 (KoNLPy 미사용 시 폴백)"""
        # 한글 단어 추출
        korean_words = re.findall(r"[가-힣]{2,}", text)
        # 영문 단어 추출
        english_words = re.findall(r"[A-Za-z][A-Za-z0-9+#]+", text)
        return korean_words + english_words

    def get_word_frequency(self, texts: list, top_n: int = 50) -> pd.DataFrame:
        """텍스트 리스트에서 전체 단어 빈도 계산"""
        all_nouns = []
        for text in texts:
            if isinstance(text, str):
                all_nouns.extend(self.extract_nouns(text))

        if not all_nouns:
            return pd.DataFrame(columns=["단어", "빈도", "비율(%)"])

        counter = Counter(all_nouns)
        total = sum(counter.values())

        top_words = counter.most_common(top_n)
        df = pd.DataFrame(top_words, columns=["단어", "빈도"])
        df["비율(%)"] = round(df["빈도"] / total * 100, 2)

        logger.info(f"단어 빈도 분석 완료: 총 {len(counter)}개 단어, 상위 {top_n}개 추출")
        return df

    def get_tech_stack_frequency(self, job_data: pd.DataFrame) -> pd.DataFrame:
        """채용 공고 데이터에서 기술스택 빈도 분석"""
        # 텍스트 컬럼 결합
        text_cols = ["자격요건", "우대사항", "주요업무", "기술스택", "기술스택태그"]
        combined_text = ""
        for col in text_cols:
            if col in job_data.columns:
                combined_text += " ".join(job_data[col].dropna().astype(str)) + " "

        if not combined_text.strip():
            return pd.DataFrame(columns=["기술스택", "빈도", "비율(%)"])

        # 각 기술스택 키워드 매칭
        tech_counts = {}
        total_postings = len(job_data)

        for tech in TECH_STACK_KEYWORDS:
            # 대소문자 무관 매칭
            pattern = re.compile(re.escape(tech), re.IGNORECASE)
            count = 0
            for _, row in job_data.iterrows():
                row_text = " ".join(str(row.get(col, "")) for col in text_cols if col in job_data.columns)
                if pattern.search(row_text):
                    count += 1
            if count > 0:
                tech_counts[tech] = count

        df = pd.DataFrame([
            {"기술스택": tech, "빈도": count, "비율(%)": round(count / total_postings * 100, 1)}
            for tech, count in sorted(tech_counts.items(), key=lambda x: x[1], reverse=True)
        ])

        logger.info(f"기술스택 빈도 분석 완료: {len(df)}개 기술 발견")
        return df

    def get_certificate_frequency(self, job_data: pd.DataFrame) -> pd.DataFrame:
        """채용 공고 데이터에서 자격증 빈도 분석"""
        text_cols = ["자격요건", "우대사항", "자격증"]

        cert_counts = {}
        total_postings = len(job_data)

        for cert in CERTIFICATE_KEYWORDS:
            count = 0
            for _, row in job_data.iterrows():
                row_text = " ".join(str(row.get(col, "")) for col in text_cols if col in job_data.columns)
                if cert in row_text:
                    count += 1
            if count > 0:
                cert_counts[cert] = count

        df = pd.DataFrame([
            {"자격증": cert, "빈도": count, "비율(%)": round(count / total_postings * 100, 1)}
            for cert, count in sorted(cert_counts.items(), key=lambda x: x[1], reverse=True)
        ])

        logger.info(f"자격증 빈도 분석 완료: {len(df)}개 자격증 발견")
        return df

    def get_keyword_trend(self, blog_data: pd.DataFrame) -> pd.DataFrame:
        """블로그/뉴스 데이터에서 시기별 키워드 트렌드 분석"""
        date_col = None
        for col in ["작성일", "발행일", "날짜"]:
            if col in blog_data.columns:
                date_col = col
                break

        if not date_col:
            logger.warning("날짜 컬럼을 찾을 수 없습니다.")
            return pd.DataFrame()

        # 월별 집계
        df = blog_data.copy()
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.dropna(subset=[date_col])
        df["월"] = df[date_col].dt.to_period("M").astype(str)

        # 검색키워드별 월별 빈도
        if "검색키워드" in df.columns:
            trend = df.groupby(["월", "검색키워드"]).size().unstack(fill_value=0)
        else:
            trend = df.groupby("월").size().to_frame("건수")

        logger.info(f"키워드 트렌드 분석 완료: {len(trend)}개 시점")
        return trend

    def extract_job_requirements(self, text: str) -> dict:
        """채용 공고 텍스트에서 구조화된 정보 추출"""
        result = {"학력": "", "경력": "", "기술": [], "자격증": []}

        if not text or not isinstance(text, str):
            return result

        # 학력
        edu_patterns = ["박사", "석사", "학사", "대졸", "대학교", "전문대", "고졸"]
        for edu in edu_patterns:
            if edu in text:
                result["학력"] = edu
                break

        # 경력
        career_match = re.search(r"경력\s*(\d+)", text)
        if career_match:
            result["경력"] = f"경력 {career_match.group(1)}년"
        elif "신입" in text:
            result["경력"] = "신입"

        # 기술스택
        for tech in TECH_STACK_KEYWORDS:
            if re.search(re.escape(tech), text, re.IGNORECASE):
                result["기술"].append(tech)

        # 자격증
        for cert in CERTIFICATE_KEYWORDS:
            if cert in text:
                result["자격증"].append(cert)

        return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    analyzer = TextAnalyzer()

    # 테스트
    test_text = "Python, C++, ROS2를 활용한 자율주행 인지 시스템 개발 경험이 있는 분을 찾습니다."
    nouns = analyzer.extract_nouns(test_text)
    print(f"추출된 명사: {nouns}")

    reqs = analyzer.extract_job_requirements(test_text)
    print(f"구조화된 요건: {reqs}")

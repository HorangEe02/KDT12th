"""
=============================================================
텍스트 분석 모듈
=============================================================
텍스트 데이터에서 키워드 추출, 빈도 분석, 기술스택/자격증 추출,
자동차 설계 도메인 분석, 트렌드 분석 수행
=============================================================
"""

import re
from collections import Counter

import pandas as pd

from config.settings import (
    TECH_STACK_KEYWORDS,
    CERTIFICATE_KEYWORDS,
    CAR_DESIGN_DOMAIN_KEYWORDS,
)


class TextAnalyzer:
    """텍스트 분석 (키워드 추출, 빈도 분석)"""

    def __init__(self):
        # KoNLPy 형태소 분석기 초기화 (실패 시 정규식 기반 대체)
        self.okt = None
        try:
            from konlpy.tag import Okt
            self.okt = Okt()
            print("  ✅ KoNLPy Okt 형태소 분석기 초기화 완료")
        except (ImportError, Exception) as e:
            print(f"  ⚠️ KoNLPy 사용 불가 ({e}), 정규식 기반 추출 사용")

        # 불용어 리스트
        self.stopwords = {
            "있는", "하는", "있다", "합니다", "입니다", "등", "및", "또한",
            "위해", "통해", "대한", "관련", "이상", "이하", "필요", "해당",
            "것이", "하고", "에서", "으로", "그리고", "하며", "되는", "위한",
            "수행", "가능", "경험", "우대", "기반", "활용", "개발", "진행",
            "이해", "능력", "업무", "분야", "대해", "함께", "사항", "다양",
            "보유", "참여", "자체", "주요", "프로", "이용", "제공",
            "것으로", "같은", "때문", "이런", "정도", "않는",
        }

        # 자동차 설계 도메인 사용자 사전
        self.medical_terms = [
            "차체설계", "CAE해석", "구조해석", "유동해석", "충돌해석",
            "NVH", "경량화", "플랫폼", "전기차", "배터리", "자율주행",
        ]

        # 기술스택 정규식 패턴
        self.tech_patterns = {}
        for tech in TECH_STACK_KEYWORDS:
            escaped = re.escape(tech)
            self.tech_patterns[tech] = re.compile(
                rf"\b{escaped}\b" if tech.isascii() else escaped,
                re.IGNORECASE,
            )

        # 자격증 정규식 패턴
        self.cert_patterns = {}
        for cert in CERTIFICATE_KEYWORDS:
            escaped = re.escape(cert)
            self.cert_patterns[cert] = re.compile(escaped, re.IGNORECASE)

    def extract_nouns(self, text: str) -> list:
        """
        텍스트에서 명사 추출
        - KoNLPy 사용 가능하면 Okt 형태소 분석
        - 불가능하면 정규식 기반 추출
        """
        if not isinstance(text, str) or not text.strip():
            return []

        if self.okt:
            try:
                nouns = self.okt.nouns(text)
            except Exception:
                nouns = self._regex_extract_nouns(text)
        else:
            nouns = self._regex_extract_nouns(text)

        # 불용어 제거 + 1글자 제거
        filtered = [
            n for n in nouns
            if len(n) > 1 and n not in self.stopwords
        ]
        return filtered

    def _regex_extract_nouns(self, text: str) -> list:
        """정규식 기반 간이 명사 추출 (KoNLPy 대체)"""
        # 한글 2글자 이상 단어 추출
        korean = re.findall(r"[가-힣]{2,}", text)
        # 영문 단어 추출
        english = re.findall(r"[A-Za-z][A-Za-z+#.]{1,}", text)
        return korean + english

    def get_word_frequency(self, texts: list, top_n: int = 50) -> pd.DataFrame:
        """
        텍스트 리스트에서 전체 단어 빈도 계산

        Returns:
            DataFrame[단어, 빈도, 비율(%)]
        """
        all_nouns = []
        for text in texts:
            all_nouns.extend(self.extract_nouns(str(text)))

        if not all_nouns:
            return pd.DataFrame(columns=["단어", "빈도", "비율(%)"])

        counter = Counter(all_nouns)
        total = sum(counter.values())

        top_words = counter.most_common(top_n)
        df = pd.DataFrame(top_words, columns=["단어", "빈도"])
        df["비율(%)"] = (df["빈도"] / total * 100).round(2)

        return df

    def get_tech_stack_frequency(self, job_data: pd.DataFrame) -> pd.DataFrame:
        """
        채용 공고 데이터에서 기술스택 빈도 분석

        Returns:
            DataFrame[기술스택, 빈도, 비율(%)]
        """
        if job_data is None or job_data.empty:
            return pd.DataFrame(columns=["기술스택", "빈도", "비율(%)"])

        # 분석 대상 텍스트 컬럼
        text_cols = ["자격요건", "우대사항", "주요업무", "제목", "내용요약",
                     "장점", "단점", "한줄평", "기술스택태그", "기술스택",
                     "공고제목", "직무분야"]
        texts = []
        for col in text_cols:
            if col in job_data.columns:
                texts.extend(job_data[col].dropna().tolist())

        if not texts:
            return pd.DataFrame(columns=["기술스택", "빈도", "비율(%)"])

        combined = " ".join(str(t) for t in texts)
        counter = Counter()

        for tech, pattern in self.tech_patterns.items():
            count = len(pattern.findall(combined))
            if count > 0:
                counter[tech] = count

        if not counter:
            return pd.DataFrame(columns=["기술스택", "빈도", "비율(%)"])

        total = sum(counter.values())
        data = [(tech, freq, round(freq / total * 100, 2))
                for tech, freq in counter.most_common()]

        return pd.DataFrame(data, columns=["기술스택", "빈도", "비율(%)"])

    def get_certificate_frequency(self, job_data: pd.DataFrame) -> pd.DataFrame:
        """
        채용 공고 데이터에서 자격증 빈도 분석

        Returns:
            DataFrame[자격증, 빈도, 비율(%)]
        """
        if job_data is None or job_data.empty:
            return pd.DataFrame(columns=["자격증", "빈도", "비율(%)"])

        text_cols = ["자격요건", "우대사항", "제목", "내용요약", "기술스택태그",
                     "기술스택", "자격증", "공고제목", "직무분야"]
        texts = []
        for col in text_cols:
            if col in job_data.columns:
                texts.extend(job_data[col].dropna().tolist())

        if not texts:
            return pd.DataFrame(columns=["자격증", "빈도", "비율(%)"])

        combined = " ".join(str(t) for t in texts)
        counter = Counter()

        for cert, pattern in self.cert_patterns.items():
            count = len(pattern.findall(combined))
            if count > 0:
                counter[cert] = count

        if not counter:
            return pd.DataFrame(columns=["자격증", "빈도", "비율(%)"])

        total = sum(counter.values())
        data = [(cert, freq, round(freq / total * 100, 2))
                for cert, freq in counter.most_common()]

        return pd.DataFrame(data, columns=["자격증", "빈도", "비율(%)"])

    def get_domain_frequency(self, job_data: pd.DataFrame) -> pd.DataFrame:
        """
        자동차 설계 도메인 키워드 빈도 분석 (자동차 설계 특화)

        카테고리: 영상의학 / 병리 / 임상 / 인허가 / 유전체

        Returns:
            DataFrame[카테고리, 키워드, 빈도]
        """
        if job_data is None or job_data.empty:
            return pd.DataFrame(columns=["카테고리", "키워드", "빈도"])

        text_cols = ["자격요건", "우대사항", "주요업무", "제목", "내용요약",
                     "장점", "단점", "기술스택태그", "기술스택",
                     "공고제목", "직무분야"]
        texts = []
        for col in text_cols:
            if col in job_data.columns:
                texts.extend(job_data[col].dropna().tolist())

        if not texts:
            return pd.DataFrame(columns=["카테고리", "키워드", "빈도"])

        combined = " ".join(str(t) for t in texts)
        results = []

        for category, keywords in CAR_DESIGN_DOMAIN_KEYWORDS.items():
            for keyword in keywords:
                pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                count = len(pattern.findall(combined))
                if count > 0:
                    results.append({
                        "카테고리": category,
                        "키워드": keyword,
                        "빈도": count,
                    })

        df = pd.DataFrame(results)
        if not df.empty:
            df = df.sort_values("빈도", ascending=False).reset_index(drop=True)

        return df

    def get_keyword_trend(self, blog_data: pd.DataFrame) -> pd.DataFrame:
        """
        블로그/뉴스 데이터에서 시기별 키워드 트렌드 분석

        Returns:
            DataFrame (월별 × 키워드 빈도 피벗 테이블)
        """
        if blog_data is None or blog_data.empty:
            return pd.DataFrame()

        date_col = None
        for col in ["게시일자", "작성일", "발행일", "등록일"]:
            if col in blog_data.columns:
                date_col = col
                break

        if date_col is None:
            return pd.DataFrame()

        df = blog_data.copy()
        df["날짜"] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.dropna(subset=["날짜"])

        if df.empty:
            return pd.DataFrame()

        df["월"] = df["날짜"].dt.to_period("M").astype(str)

        # 키워드 컬럼이 있으면 활용
        if "검색키워드" in df.columns:
            pivot = df.groupby(["월", "검색키워드"]).size().unstack(fill_value=0)
            return pivot

        return df.groupby("월").size().reset_index(name="건수")

    def extract_job_requirements(self, text: str) -> dict:
        """
        채용 공고 텍스트에서 구조화된 정보 추출

        Returns:
            {"학력": ..., "경력": ..., "기술": [...], "자격증": [...], "도메인": [...]}
        """
        result = {
            "학력": "무관",
            "경력": "무관",
            "기술": [],
            "자격증": [],
            "도메인": [],
        }

        if not isinstance(text, str) or not text.strip():
            return result

        # 학력 추출
        if re.search(r"박사", text):
            result["학력"] = "박사"
        elif re.search(r"석사", text):
            result["학력"] = "석사"
        elif re.search(r"학사|대졸|대학교", text):
            result["학력"] = "학사"

        # 경력 추출
        career_match = re.search(r"(\d+)\s*[~\-]\s*(\d+)\s*년", text)
        if career_match:
            min_y, max_y = career_match.groups()
            result["경력"] = f"경력 {min_y}~{max_y}년"
        elif re.search(r"신입", text):
            result["경력"] = "신입"

        # 기술스택 추출
        for tech, pattern in self.tech_patterns.items():
            if pattern.search(text):
                result["기술"].append(tech)

        # 자격증 추출
        for cert, pattern in self.cert_patterns.items():
            if pattern.search(text):
                result["자격증"].append(cert)

        # 자동차 설계 도메인 추출
        for category, keywords in CAR_DESIGN_DOMAIN_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in text.lower():
                    result["도메인"].append(f"{category}:{keyword}")
                    break

        return result


if __name__ == "__main__":
    analyzer = TextAnalyzer()

    # 테스트
    test_text = "CATIA, NX, ANSYS 활용한 자동차 차체설계 CAE해석 경력 3~5년"
    print("명사 추출:", analyzer.extract_nouns(test_text))
    print("요구사항 추출:", analyzer.extract_job_requirements(test_text))

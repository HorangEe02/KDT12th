"""
데이터 전처리 및 정제 모듈
수집된 원본 데이터의 HTML 태그 제거, 연봉 정규화, 날짜 통일 등
"""

import re
import html
import logging
import pandas as pd
from datetime import datetime
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent))
from config.settings import DATA_RAW_DIR, DATA_PROCESSED_DIR

logger = logging.getLogger(__name__)


class DataCleaner:
    """데이터 전처리 및 정제"""

    def __init__(self):
        logger.info("DataCleaner 초기화")

    def clean_html_tags(self, text: str) -> str:
        """HTML 태그 및 특수문자 제거"""
        if not text or not isinstance(text, str):
            return ""
        # HTML 엔티티 디코딩
        text = html.unescape(text)
        # HTML 태그 제거
        text = re.sub(r"<[^>]+>", "", text)
        # 연속 공백 정리
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def normalize_salary(self, salary_text: str) -> int:
        """연봉 텍스트를 정수(만원 단위)로 변환"""
        if not salary_text or not isinstance(salary_text, str):
            return None

        # "회사 내규에 따름", "면접 후 결정" 등
        skip_patterns = ["내규", "면접", "협의", "추후", "미정"]
        if any(p in salary_text for p in skip_patterns):
            return None

        # 숫자 추출 (쉼표 포함)
        numbers = re.findall(r"[\d,]+", salary_text)
        if not numbers:
            return None

        cleaned = [int(n.replace(",", "")) for n in numbers if n.replace(",", "").isdigit()]

        if not cleaned:
            return None

        # "억" 단위 처리
        if "억" in salary_text:
            cleaned = [n * 10000 if n < 100 else n for n in cleaned]

        # 범위 형식 ("3,500 ~ 4,500만원") → 평균값
        if len(cleaned) >= 2:
            return int(sum(cleaned[:2]) / 2)

        return cleaned[0]

    def normalize_career(self, career_text: str) -> str:
        """경력 조건 통일"""
        if not career_text or not isinstance(career_text, str):
            return "무관"

        text = career_text.strip()

        if "무관" in text:
            return "무관"
        if "신입" in text and "경력" not in text:
            return "신입"

        # 숫자 추출
        years = re.findall(r"(\d+)", text)
        if years:
            min_year = int(years[0])
            if min_year == 0:
                return "신입"
            elif min_year <= 3:
                return "경력 1~3년"
            elif min_year <= 5:
                return "경력 3~5년"
            else:
                return "경력 5년 이상"

        if "신입" in text:
            return "신입"
        if "경력" in text:
            return "경력 1~3년"

        return "무관"

    def normalize_company_size(self, info: dict) -> str:
        """사원수 기반 기업 규모 분류"""
        employee_text = info.get("사원수", "") or info.get("employee_count", "")
        if not employee_text:
            return "미분류"

        # 숫자 추출
        numbers = re.findall(r"(\d+)", str(employee_text).replace(",", ""))
        if not numbers:
            return "미분류"

        count = int(numbers[0])

        if count < 50:
            return "스타트업"
        elif count < 300:
            return "중소기업"
        elif count < 1000:
            return "중견기업"
        else:
            return "대기업"

    def normalize_date(self, date_str: str) -> str:
        """다양한 날짜 포맷을 YYYY-MM-DD로 통일"""
        if not date_str or not isinstance(date_str, str):
            return ""

        date_str = date_str.strip()

        # 이미 YYYY-MM-DD 형식
        if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
            return date_str

        # YYYYMMDD
        if re.match(r"^\d{8}$", date_str):
            return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"

        # YYYY.MM.DD
        m = re.match(r"^(\d{4})\.(\d{1,2})\.(\d{1,2})", date_str)
        if m:
            return f"{m.group(1)}-{m.group(2).zfill(2)}-{m.group(3).zfill(2)}"

        # RFC 2822 (Mon, 15 Jan 2024 00:00:00 +0900)
        try:
            dt = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass

        # YYYY/MM/DD
        m = re.match(r"^(\d{4})/(\d{1,2})/(\d{1,2})", date_str)
        if m:
            return f"{m.group(1)}-{m.group(2).zfill(2)}-{m.group(3).zfill(2)}"

        return date_str

    def deduplicate(self, df: pd.DataFrame, subset: list) -> pd.DataFrame:
        """중복 데이터 제거"""
        before = len(df)
        # subset 컬럼 중 실제 존재하는 것만 사용
        valid_cols = [c for c in subset if c in df.columns]
        if not valid_cols:
            return df

        df = df.drop_duplicates(subset=valid_cols).reset_index(drop=True)
        removed = before - len(df)
        if removed > 0:
            logger.info(f"중복 제거: {before} → {len(df)}건 ({removed}건 제거)")
        return df

    def process_all_raw_data(self):
        """data/raw/ 폴더의 모든 CSV를 읽어 전처리 후 data/processed/에 저장"""
        logger.info("=" * 50)
        logger.info("데이터 전처리 시작")
        logger.info("=" * 50)

        raw_files = list(DATA_RAW_DIR.glob("*.csv"))
        if not raw_files:
            logger.warning(f"원본 데이터 파일이 없습니다: {DATA_RAW_DIR}")
            return

        for raw_file in raw_files:
            logger.info(f"▶ 처리 중: {raw_file.name}")

            try:
                df = pd.read_csv(raw_file, encoding="utf-8-sig")
                original_count = len(df)

                # 텍스트 컬럼 HTML 태그 제거
                text_cols = ["제목", "본문요약", "공고제목", "자격요건", "우대사항",
                             "주요업무", "장점", "단점", "면접질문", "면접내용",
                             "리뷰제목", "포지션명"]
                for col in text_cols:
                    if col in df.columns:
                        df[col] = df[col].apply(self.clean_html_tags)

                # 날짜 정규화
                date_cols = ["작성일", "발행일", "마감일"]
                for col in date_cols:
                    if col in df.columns:
                        df[col] = df[col].apply(self.normalize_date)

                # 연봉 정규화
                if "연봉정보" in df.columns:
                    df["연봉_만원"] = df["연봉정보"].apply(self.normalize_salary)

                if "연봉_만원" in df.columns:
                    df["연봉_만원"] = pd.to_numeric(df["연봉_만원"], errors="coerce")

                # 경력 정규화
                if "경력조건" in df.columns:
                    df["경력구분"] = df["경력조건"].apply(self.normalize_career)

                # 중복 제거
                if "링크" in df.columns:
                    df = self.deduplicate(df, ["링크"])
                elif "URL" in df.columns:
                    df = self.deduplicate(df, ["URL"])

                # 저장
                output_path = DATA_PROCESSED_DIR / f"processed_{raw_file.name}"
                df.to_csv(output_path, index=False, encoding="utf-8-sig")
                logger.info(f"  저장 완료: {output_path.name} ({original_count} → {len(df)}건)")

            except Exception as e:
                logger.error(f"  처리 실패: {raw_file.name} - {e}")

        logger.info("데이터 전처리 완료")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    cleaner = DataCleaner()
    cleaner.process_all_raw_data()

"""
=============================================================
데이터 전처리 및 정제 모듈
=============================================================
수집된 원본 데이터의 HTML 태그 제거, 날짜/연봉/경력 정규화,
마케팅 용어 통일, 중복 제거 등 전처리 수행
=============================================================
"""

import os
import re
import glob
from datetime import datetime

import pandas as pd

from config.settings import DATA_RAW_DIR, DATA_PROCESSED_DIR


class DataCleaner:
    """크롤링 원본 데이터 전처리 및 정제"""

    def __init__(self):
        # 마케팅 용어 정규화 매핑
        self.domain_term_map = {
            "GA4": [r"구글\s*애널리틱스\s*4", r"Google\s*Analytics\s*4", r"GA4", r"ga4"],
            "Google Analytics": [r"구글\s*애널리틱스", r"Google\s*Analytics", r"GA"],
            "SEO": [r"검색엔진최적화", r"검색\s*엔진\s*최적화", r"SEO", r"seo"],
            "SEM": [r"검색엔진마케팅", r"검색\s*엔진\s*마케팅", r"SEM", r"sem"],
            "CRM": [r"고객관계관리", r"고객\s*관계\s*관리", r"CRM", r"crm"],
            "ROAS": [r"광고수익률", r"ROAS", r"roas"],
            "CTR": [r"클릭률", r"클릭\s*률", r"CTR", r"ctr"],
            "CVR": [r"전환율", r"CVR", r"cvr"],
            "CPC": [r"클릭당비용", r"클릭당\s*비용", r"CPC", r"cpc"],
            "CPM": [r"노출당비용", r"노출당\s*비용", r"CPM", r"cpm"],
        }

    def clean_html_tags(self, text: str) -> str:
        if not isinstance(text, str):
            return ""
        clean = re.sub(r"<[^>]+>", "", text)
        clean = re.sub(r"&[a-zA-Z]+;", " ", clean)
        clean = re.sub(r"&#\d+;", " ", clean)
        clean = re.sub(r"\s+", " ", clean)
        return clean.strip()

    def normalize_salary(self, salary_text: str) -> int:
        if not isinstance(salary_text, str):
            return None
        skip_patterns = ["내규", "협의", "면접", "결정", "추후"]
        if any(p in salary_text for p in skip_patterns):
            return None
        numbers = re.findall(r"[\d,]+", salary_text)
        if not numbers:
            return None
        values = []
        for n in numbers:
            try:
                values.append(int(n.replace(",", "")))
            except ValueError:
                continue
        if not values:
            return None
        if "억" in salary_text:
            values = [v * 10000 if v < 100 else v for v in values]
        if len(values) >= 2:
            return int(sum(values[:2]) / 2)
        return values[0]

    def normalize_career(self, career_text: str) -> str:
        if not isinstance(career_text, str):
            return "무관"
        text = career_text.strip()
        if "무관" in text or "경력무관" in text:
            return "무관"
        if "신입" in text and "경력" not in text:
            return "신입"
        years = re.findall(r"(\d+)", text)
        if years:
            years = [int(y) for y in years]
            max_year = max(years)
            if max_year <= 1:
                return "신입"
            elif max_year <= 3:
                return "경력 1~3년"
            elif max_year <= 5:
                return "경력 3~5년"
            else:
                return "경력 5년 이상"
        if "신입" in text:
            return "신입"
        if "경력" in text:
            return "경력 3~5년"
        return "무관"

    def normalize_company_size(self, info: dict) -> str:
        employee_count = info.get("사원수", info.get("직원수", ""))
        if not isinstance(employee_count, str):
            employee_count = str(employee_count)
        numbers = re.findall(r"[\d,]+", employee_count)
        if numbers:
            count = int(numbers[0].replace(",", ""))
            if count < 50:
                return "스타트업"
            elif count < 300:
                return "중소기업"
            elif count < 1000:
                return "중견기업"
            else:
                return "대기업"
        if any(k in employee_count for k in ["대기업", "대규모"]):
            return "대기업"
        if any(k in employee_count for k in ["중견", "중규모"]):
            return "중견기업"
        return "중소기업"

    def normalize_date(self, date_str: str) -> str:
        if not isinstance(date_str, str) or not date_str.strip():
            return ""
        date_str = date_str.strip()
        if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
            return date_str
        if re.match(r"^\d{8}$", date_str):
            try:
                dt = datetime.strptime(date_str, "%Y%m%d")
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                pass
        try:
            dt = datetime.strptime(date_str[:25].strip().rstrip(","), "%a, %d %b %Y %H:%M:%S")
            return dt.strftime("%Y-%m-%d")
        except (ValueError, IndexError):
            pass
        match = re.search(r"(\d{4})[./\-](\d{1,2})[./\-](\d{1,2})", date_str)
        if match:
            y, m, d = match.groups()
            return f"{y}-{int(m):02d}-{int(d):02d}"
        match = re.search(r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일", date_str)
        if match:
            y, m, d = match.groups()
            return f"{y}-{int(m):02d}-{int(d):02d}"
        return date_str

    def normalize_domain_terms(self, text: str) -> str:
        """마케팅 용어 통일 처리"""
        if not isinstance(text, str):
            return ""
        result = text
        for standard_term, variants in self.domain_term_map.items():
            for variant in variants:
                result = re.sub(variant, standard_term, result, flags=re.IGNORECASE)
        return result

    def deduplicate(self, df: pd.DataFrame, subset: list) -> pd.DataFrame:
        if df is None or df.empty:
            return df
        before = len(df)
        df = df.drop_duplicates(subset=subset, keep="first").reset_index(drop=True)
        after = len(df)
        if before != after:
            print(f"  중복 제거: {before} -> {after}건 ({before - after}건 제거)")
        return df

    def _process_single_file(self, filepath: str) -> pd.DataFrame:
        print(f"  처리 중: {os.path.basename(filepath)}")
        try:
            df = pd.read_csv(filepath, encoding="utf-8-sig")
        except UnicodeDecodeError:
            df = pd.read_csv(filepath, encoding="utf-8")
        if df.empty:
            return df
        text_columns = ["제목", "내용요약", "본문", "장점", "단점", "면접경험",
                        "면접질문", "자격요건", "우대사항", "주요업무", "한줄평",
                        "경영진에_바라는점",
                        "포지션명", "기술스택태그", "혜택및복지", "회사소개"]
        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].apply(self.clean_html_tags)
                df[col] = df[col].apply(self.normalize_domain_terms)
        date_columns = ["게시일자", "등록일", "작성일", "마감일", "발행일"]
        for col in date_columns:
            if col in df.columns:
                df[col] = df[col].apply(self.normalize_date)
        salary_columns = ["연봉", "연봉정보", "평균연봉"]
        for col in salary_columns:
            if col in df.columns:
                df[f"{col}_정규화"] = df[col].apply(self.normalize_salary)
        career_columns = ["경력", "경력조건"]
        for col in career_columns:
            if col in df.columns:
                df[f"{col}_정규화"] = df[col].apply(self.normalize_career)
        return df

    def process_all_raw_data(self):
        print("=" * 60)
        print("데이터 전처리 시작")
        print("=" * 60)
        raw_files = glob.glob(os.path.join(DATA_RAW_DIR, "*.csv"))
        if not raw_files:
            print("  data/raw/ 폴더에 CSV 파일이 없습니다.")
            return
        print(f"  발견된 파일: {len(raw_files)}개\n")
        for filepath in raw_files:
            df = self._process_single_file(filepath)
            if df is not None and not df.empty:
                url_cols = [c for c in df.columns if "링크" in c or "URL" in c or "url" in c]
                if url_cols:
                    df = self.deduplicate(df, subset=url_cols[:1])
                filename = os.path.basename(filepath).replace(".csv", "_processed.csv")
                save_path = os.path.join(DATA_PROCESSED_DIR, filename)
                df.to_csv(save_path, index=False, encoding="utf-8-sig")
                print(f"  저장: {save_path} ({len(df)}건)\n")
        print("전처리 완료!")


if __name__ == "__main__":
    cleaner = DataCleaner()
    cleaner.process_all_raw_data()

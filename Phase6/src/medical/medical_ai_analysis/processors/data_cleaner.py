"""
=============================================================
데이터 전처리 및 정제 모듈
=============================================================
수집된 원본 데이터의 HTML 태그 제거, 날짜/연봉/경력 정규화,
의료 용어 통일, 중복 제거 등 전처리 수행
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
        # 의료 용어 정규화 매핑
        self.medical_term_map = {
            "X-ray": [r"엑스레이", r"X레이", r"X-ray", r"Xray", r"x-ray", r"엑스-레이"],
            "CT": [r"씨티", r"CT", r"컴퓨터단층촬영", r"컴퓨터\s*단층"],
            "MRI": [r"엠알아이", r"MRI", r"자기공명영상", r"자기\s*공명"],
            "PACS": [r"팍스", r"PACS", r"의료영상저장전송시스템"],
            "초음파": [r"울트라사운드", r"Ultrasound", r"초음파"],
            "DICOM": [r"다이콤", r"DICOM", r"디콤"],
            "EMR": [r"EMR", r"전자의무기록", r"전자\s*의무\s*기록"],
            "HL7": [r"HL7", r"에이치엘세븐"],
            "FHIR": [r"FHIR", r"파이어"],
        }

    def clean_html_tags(self, text: str) -> str:
        """HTML 태그 및 특수문자 제거"""
        if not isinstance(text, str):
            return ""
        # HTML 태그 제거
        clean = re.sub(r"<[^>]+>", "", text)
        # HTML 엔티티 제거
        clean = re.sub(r"&[a-zA-Z]+;", " ", clean)
        clean = re.sub(r"&#\d+;", " ", clean)
        # 연속 공백 정리
        clean = re.sub(r"\s+", " ", clean)
        return clean.strip()

    def normalize_salary(self, salary_text: str) -> int:
        """
        연봉 텍스트를 정수(만원 단위)로 변환

        예시:
            "3,500만원" → 3500
            "3,500 ~ 4,500만원" → 4000
            "회사 내규에 따름" → None
        """
        if not isinstance(salary_text, str):
            return None

        # "회사 내규", "면접 후 결정", "협의" 등
        skip_patterns = ["내규", "협의", "면접", "결정", "추후"]
        if any(p in salary_text for p in skip_patterns):
            return None

        # 숫자 추출 (콤마 포함)
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

        # "억" 단위 처리
        if "억" in salary_text:
            values = [v * 10000 if v < 100 else v for v in values]

        # 범위가 있으면 평균값
        if len(values) >= 2:
            return int(sum(values[:2]) / 2)
        return values[0]

    def normalize_career(self, career_text: str) -> str:
        """
        경력 조건 통일

        반환: "신입" / "경력 1~3년" / "경력 3~5년" / "경력 5년 이상" / "무관"
        """
        if not isinstance(career_text, str):
            return "무관"

        text = career_text.strip()

        if "무관" in text or "경력무관" in text:
            return "무관"
        if "신입" in text and "경력" not in text:
            return "신입"

        # 숫자 추출
        years = re.findall(r"(\d+)", text)
        if years:
            years = [int(y) for y in years]
            max_year = max(years)
            min_year = min(years)

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
        """
        사원수 기반 기업 규모 분류

        반환: "스타트업" / "중소기업" / "중견기업" / "대기업"
        """
        employee_count = info.get("사원수", info.get("직원수", ""))
        if not isinstance(employee_count, str):
            employee_count = str(employee_count)

        # 숫자 추출
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

        # 키워드 기반 판단
        if any(k in employee_count for k in ["대기업", "대규모"]):
            return "대기업"
        if any(k in employee_count for k in ["중견", "중규모"]):
            return "중견기업"

        return "중소기업"

    def normalize_date(self, date_str: str) -> str:
        """다양한 날짜 포맷을 YYYY-MM-DD로 통일"""
        if not isinstance(date_str, str) or not date_str.strip():
            return ""

        date_str = date_str.strip()

        # 이미 YYYY-MM-DD 형식
        if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
            return date_str

        # YYYYMMDD
        if re.match(r"^\d{8}$", date_str):
            try:
                dt = datetime.strptime(date_str, "%Y%m%d")
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                pass

        # "Mon, DD Mon YYYY HH:MM:SS +0000" (RSS 날짜)
        try:
            dt = datetime.strptime(date_str[:25].strip().rstrip(","), "%a, %d %b %Y %H:%M:%S")
            return dt.strftime("%Y-%m-%d")
        except (ValueError, IndexError):
            pass

        # YYYY.MM.DD 또는 YYYY/MM/DD
        match = re.search(r"(\d{4})[./\-](\d{1,2})[./\-](\d{1,2})", date_str)
        if match:
            y, m, d = match.groups()
            return f"{y}-{int(m):02d}-{int(d):02d}"

        # "YYYY년 MM월 DD일"
        match = re.search(r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일", date_str)
        if match:
            y, m, d = match.groups()
            return f"{y}-{int(m):02d}-{int(d):02d}"

        return date_str

    def normalize_medical_terms(self, text: str) -> str:
        """
        의료 용어 통일 처리 (의료 AI 특화)

        예시:
            "엑스레이" → "X-ray"
            "씨티" → "CT"
            "엠알아이" → "MRI"
        """
        if not isinstance(text, str):
            return ""

        result = text
        for standard_term, variants in self.medical_term_map.items():
            for variant in variants:
                result = re.sub(variant, standard_term, result, flags=re.IGNORECASE)

        return result

    def deduplicate(self, df: pd.DataFrame, subset: list) -> pd.DataFrame:
        """중복 데이터 제거"""
        if df is None or df.empty:
            return df

        before = len(df)
        df = df.drop_duplicates(subset=subset, keep="first").reset_index(drop=True)
        after = len(df)

        if before != after:
            print(f"  중복 제거: {before} → {after}건 ({before - after}건 제거)")

        return df

    def _process_single_file(self, filepath: str) -> pd.DataFrame:
        """단일 CSV 파일 전처리"""
        print(f"  처리 중: {os.path.basename(filepath)}")

        try:
            df = pd.read_csv(filepath, encoding="utf-8-sig")
        except UnicodeDecodeError:
            df = pd.read_csv(filepath, encoding="utf-8")

        if df.empty:
            return df

        # 텍스트 컬럼 HTML 태그 제거
        text_columns = ["제목", "내용요약", "본문", "장점", "단점", "면접경험",
                        "면접질문", "자격요건", "우대사항", "주요업무", "한줄평",
                        "경영진에_바라는점",
                        "포지션명", "기술스택태그", "혜택및복지", "회사소개"]
        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].apply(self.clean_html_tags)
                df[col] = df[col].apply(self.normalize_medical_terms)

        # 날짜 컬럼 정규화
        date_columns = ["게시일자", "등록일", "작성일", "마감일", "발행일"]
        for col in date_columns:
            if col in df.columns:
                df[col] = df[col].apply(self.normalize_date)

        # 연봉 컬럼 정규화
        salary_columns = ["연봉", "연봉정보", "평균연봉"]
        for col in salary_columns:
            if col in df.columns:
                df[f"{col}_정규화"] = df[col].apply(self.normalize_salary)

        # 경력 컬럼 정규화
        career_columns = ["경력", "경력조건"]
        for col in career_columns:
            if col in df.columns:
                df[f"{col}_정규화"] = df[col].apply(self.normalize_career)

        return df

    def process_all_raw_data(self):
        """data/raw/ 폴더의 모든 CSV를 읽어 전처리 후 data/processed/에 저장"""
        print("=" * 60)
        print("🔧 데이터 전처리 시작")
        print("=" * 60)

        raw_files = glob.glob(os.path.join(DATA_RAW_DIR, "*.csv"))

        if not raw_files:
            print("  ⚠️ data/raw/ 폴더에 CSV 파일이 없습니다.")
            return

        print(f"  발견된 파일: {len(raw_files)}개\n")

        for filepath in raw_files:
            df = self._process_single_file(filepath)

            if df is not None and not df.empty:
                # 중복 제거 (URL 기반)
                url_cols = [c for c in df.columns if "링크" in c or "URL" in c or "url" in c]
                if url_cols:
                    df = self.deduplicate(df, subset=url_cols[:1])

                # 저장
                filename = os.path.basename(filepath).replace(".csv", "_processed.csv")
                save_path = os.path.join(DATA_PROCESSED_DIR, filename)
                df.to_csv(save_path, index=False, encoding="utf-8-sig")
                print(f"  ✅ 저장: {save_path} ({len(df)}건)\n")

        print("🔧 전처리 완료!")


if __name__ == "__main__":
    cleaner = DataCleaner()
    cleaner.process_all_raw_data()

"""
연봉 데이터 분석 모듈
기업별, 경력별, 규모별, 기술스택별 연봉 비교 분석
"""

import re
import logging
import numpy as np
import pandas as pd

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from config.settings import TECH_STACK_KEYWORDS

logger = logging.getLogger(__name__)


class SalaryAnalyzer:
    """연봉 데이터 전문 분석"""

    def __init__(self, salary_data: pd.DataFrame = None):
        if salary_data is not None:
            self.data = salary_data.copy()
            self._prepare_data()
        else:
            self.data = pd.DataFrame()

    def _prepare_data(self):
        """연봉 데이터 준비 (숫자 변환)"""
        # 연봉 컬럼 찾기
        salary_col = None
        for col in ["연봉_만원", "연봉(만원)", "연봉"]:
            if col in self.data.columns:
                salary_col = col
                break

        if salary_col and salary_col != "연봉_만원":
            self.data["연봉_만원"] = self.data[salary_col]

        if "연봉_만원" in self.data.columns:
            self.data["연봉_만원"] = pd.to_numeric(self.data["연봉_만원"], errors="coerce")
            before = len(self.data)
            self.data = self.data.dropna(subset=["연봉_만원"])
            logger.info(f"유효한 연봉 데이터: {len(self.data)}/{before}건")

    def load_data(self, df: pd.DataFrame):
        """데이터 로드"""
        self.data = df.copy()
        self._prepare_data()

    def get_salary_stats(self) -> dict:
        """기본 연봉 통계"""
        if self.data.empty or "연봉_만원" not in self.data.columns:
            return {}

        salary = self.data["연봉_만원"]
        stats = {
            "평균": round(salary.mean()),
            "중앙값": round(salary.median()),
            "최소": round(salary.min()),
            "최대": round(salary.max()),
            "표준편차": round(salary.std()),
            "Q1(25%)": round(salary.quantile(0.25)),
            "Q3(75%)": round(salary.quantile(0.75)),
            "데이터수": len(salary),
        }

        logger.info(f"연봉 통계: 평균 {stats['평균']}만원, 중앙값 {stats['중앙값']}만원")
        return stats

    def get_salary_by_company(self) -> pd.DataFrame:
        """기업별 평균 연봉 비교"""
        company_col = None
        for col in ["회사명", "기업명", "company"]:
            if col in self.data.columns:
                company_col = col
                break

        if not company_col or "연봉_만원" not in self.data.columns:
            return pd.DataFrame()

        result = self.data.groupby(company_col)["연봉_만원"].agg(
            평균연봉="mean", 중앙값="median", 최소="min", 최대="max", 데이터수="count"
        ).round(0).sort_values("평균연봉", ascending=False).reset_index()

        result.rename(columns={company_col: "기업명"}, inplace=True)
        logger.info(f"기업별 연봉 분석 완료: {len(result)}개 기업")
        return result

    def get_salary_by_career(self) -> pd.DataFrame:
        """경력별 연봉 분포"""
        career_col = None
        for col in ["경력구분", "경력조건", "경력"]:
            if col in self.data.columns:
                career_col = col
                break

        if not career_col or "연봉_만원" not in self.data.columns:
            return pd.DataFrame()

        # 경력 순서 정의
        career_order = ["신입", "경력 1~3년", "경력 3~5년", "경력 5년 이상", "무관"]

        result = self.data.groupby(career_col)["연봉_만원"].agg(
            평균연봉="mean", 중앙값="median", 최소="min", 최대="max", 데이터수="count"
        ).round(0).reset_index()

        result.rename(columns={career_col: "경력구분"}, inplace=True)

        # 순서 정렬
        result["정렬순서"] = result["경력구분"].apply(
            lambda x: career_order.index(x) if x in career_order else 99
        )
        result = result.sort_values("정렬순서").drop(columns=["정렬순서"]).reset_index(drop=True)

        logger.info(f"경력별 연봉 분석 완료: {len(result)}개 구분")
        return result

    def get_salary_by_company_size(self) -> pd.DataFrame:
        """기업 규모별 연봉 비교"""
        size_col = None
        for col in ["기업규모", "회사규모", "규모"]:
            if col in self.data.columns:
                size_col = col
                break

        if not size_col or "연봉_만원" not in self.data.columns:
            return pd.DataFrame()

        result = self.data.groupby(size_col)["연봉_만원"].agg(
            평균연봉="mean", 중앙값="median", 최소="min", 최대="max", 데이터수="count"
        ).round(0).sort_values("평균연봉", ascending=False).reset_index()

        result.rename(columns={size_col: "기업규모"}, inplace=True)
        logger.info(f"기업 규모별 연봉 분석 완료: {len(result)}개 규모")
        return result

    def get_salary_by_tech_stack(self) -> pd.DataFrame:
        """요구 기술스택별 연봉 차이 분석"""
        if "연봉_만원" not in self.data.columns:
            return pd.DataFrame()

        # 텍스트 컬럼 결합
        text_cols = ["자격요건", "우대사항", "기술스택", "기술스택태그", "주요업무"]
        self.data["_combined_text"] = ""
        for col in text_cols:
            if col in self.data.columns:
                self.data["_combined_text"] += " " + self.data[col].fillna("").astype(str)

        results = []
        major_techs = ["Python", "C++", "ROS", "ROS2", "PyTorch", "TensorFlow",
                       "OpenCV", "SLAM", "LiDAR", "Linux", "Docker", "MATLAB"]

        for tech in major_techs:
            pattern = re.compile(re.escape(tech), re.IGNORECASE)
            mask = self.data["_combined_text"].apply(lambda x: bool(pattern.search(x)))

            with_tech = self.data.loc[mask, "연봉_만원"]
            without_tech = self.data.loc[~mask, "연봉_만원"]

            if len(with_tech) >= 2 and len(without_tech) >= 2:
                results.append({
                    "기술스택": tech,
                    "요구시_평균연봉": round(with_tech.mean()),
                    "미요구시_평균연봉": round(without_tech.mean()),
                    "차이": round(with_tech.mean() - without_tech.mean()),
                    "요구공고수": len(with_tech),
                    "미요구공고수": len(without_tech),
                })

        self.data.drop(columns=["_combined_text"], inplace=True, errors="ignore")

        df = pd.DataFrame(results).sort_values("차이", ascending=False).reset_index(drop=True)
        logger.info(f"기술스택별 연봉 분석 완료: {len(df)}개 기술")
        return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    # 테스트용 샘플 데이터
    sample = pd.DataFrame({
        "회사명": ["A사", "A사", "B사", "B사", "C사"],
        "연봉_만원": [4000, 4500, 3500, 3800, 5000],
        "경력구분": ["신입", "경력 1~3년", "신입", "경력 1~3년", "경력 3~5년"],
    })

    analyzer = SalaryAnalyzer(sample)
    print("기본 통계:", analyzer.get_salary_stats())
    print("\n기업별:\n", analyzer.get_salary_by_company())
    print("\n경력별:\n", analyzer.get_salary_by_career())

"""
=============================================================
연봉 데이터 분석 모듈
=============================================================
연봉 데이터에 대한 기본 통계, 기업별/경력별/도메인별/
기술스택별/투자단계별 분석 수행
=============================================================
"""

import re

import pandas as pd
import numpy as np


class SalaryAnalyzer:
    """연봉 데이터 전문 분석"""

    def __init__(self, salary_data: pd.DataFrame = None):
        self.data = salary_data
        if self.data is not None and not self.data.empty:
            self._ensure_numeric_salary()
            print(f"  💰 연봉 데이터 로드: {len(self.data)}건")
        else:
            print("  ⚠️ 연봉 데이터가 없습니다.")

    def _ensure_numeric_salary(self):
        salary_cols = ["연봉", "연봉(만원)", "연봉_정규화", "평균연봉"]
        self.salary_col = None
        for col in salary_cols:
            if col in self.data.columns:
                self.salary_col = col
                break
        if self.salary_col is None:
            for col in self.data.columns:
                if "연봉" in col or "salary" in col.lower():
                    self.salary_col = col
                    break
        if self.salary_col:
            self.data[self.salary_col] = pd.to_numeric(
                self.data[self.salary_col], errors="coerce"
            )

    def get_salary_stats(self) -> dict:
        if self.data is None or self.salary_col is None:
            return {"error": "연봉 데이터 없음"}
        salary = self.data[self.salary_col].dropna()
        if salary.empty:
            return {"error": "유효한 연봉 데이터 없음"}
        stats = {
            "평균": round(salary.mean(), 1),
            "중앙값": round(salary.median(), 1),
            "최소": round(salary.min(), 1),
            "최대": round(salary.max(), 1),
            "표준편차": round(salary.std(), 1),
            "Q1(25%)": round(salary.quantile(0.25), 1),
            "Q2(50%)": round(salary.quantile(0.50), 1),
            "Q3(75%)": round(salary.quantile(0.75), 1),
            "데이터수": len(salary),
        }
        return stats

    def get_salary_by_company(self) -> pd.DataFrame:
        if self.data is None or self.salary_col is None:
            return pd.DataFrame()
        company_col = self._find_column(["기업명", "회사명", "company"])
        if company_col is None:
            return pd.DataFrame()
        grouped = self.data.groupby(company_col)[self.salary_col].agg(
            평균연봉="mean", 중앙값="median", 최소="min", 최대="max", 데이터수="count",
        ).round(1)
        return grouped.sort_values("평균연봉", ascending=False).reset_index()

    def get_salary_by_career(self) -> pd.DataFrame:
        if self.data is None or self.salary_col is None:
            return pd.DataFrame()
        career_col = self._find_column(["경력", "경력_정규화", "경력조건", "경력조건_정규화"])
        if career_col is None:
            return pd.DataFrame()
        grouped = self.data.groupby(career_col)[self.salary_col].agg(
            평균연봉="mean", 중앙값="median", 데이터수="count",
        ).round(1)
        career_order = ["신입", "경력 1~3년", "경력 3~5년", "경력 5년 이상", "무관"]
        grouped = grouped.reindex([c for c in career_order if c in grouped.index])
        return grouped.reset_index()

    def get_salary_by_company_size(self) -> pd.DataFrame:
        if self.data is None or self.salary_col is None:
            return pd.DataFrame()
        size_col = self._find_column(["기업규모", "company_size", "규모"])
        if size_col is None:
            return pd.DataFrame()
        grouped = self.data.groupby(size_col)[self.salary_col].agg(
            평균연봉="mean", 중앙값="median", 데이터수="count",
        ).round(1)
        return grouped.sort_values("평균연봉", ascending=False).reset_index()

    def get_salary_by_subdomain(self) -> pd.DataFrame:
        if self.data is None or self.salary_col is None:
            return pd.DataFrame()
        domain_col = self._find_column(["도메인", "category", "분야", "세부분야"])
        if domain_col is None:
            return pd.DataFrame()
        grouped = self.data.groupby(domain_col)[self.salary_col].agg(
            평균연봉="mean", 중앙값="median", 데이터수="count",
        ).round(1)
        return grouped.sort_values("평균연봉", ascending=False).reset_index()

    def get_salary_by_tech_stack(self) -> pd.DataFrame:
        if self.data is None or self.salary_col is None:
            return pd.DataFrame()
        tech_col = self._find_column(["기술스택", "tech_stack", "기술"])
        if tech_col is None:
            return pd.DataFrame()
        results = []
        target_techs = [
            "Python", "C++", "PyTorch", "TensorFlow", "Docker", "AWS",
            "DICOM", "HL7", "FHIR", "OpenCV",
        ]
        for tech in target_techs:
            mask = self.data[tech_col].apply(
                lambda x: tech.lower() in str(x).lower() if pd.notna(x) else False
            )
            salary_with_tech = self.data.loc[mask, self.salary_col].dropna()
            if len(salary_with_tech) > 0:
                results.append({
                    "기술스택": tech,
                    "평균연봉": round(salary_with_tech.mean(), 1),
                    "중앙값": round(salary_with_tech.median(), 1),
                    "데이터수": len(salary_with_tech),
                })
        df = pd.DataFrame(results)
        if not df.empty:
            df = df.sort_values("평균연봉", ascending=False).reset_index(drop=True)
        return df

    def get_salary_by_funding_stage(self) -> pd.DataFrame:
        if self.data is None or self.salary_col is None:
            return pd.DataFrame()
        funding_col = self._find_column(["투자단계", "funding_stage", "투자"])
        if funding_col is None:
            return pd.DataFrame()
        grouped = self.data.groupby(funding_col)[self.salary_col].agg(
            평균연봉="mean", 중앙값="median", 데이터수="count",
        ).round(1)
        stage_order = ["시드", "시리즈A", "시리즈B", "시리즈C+", "상장"]
        grouped = grouped.reindex([s for s in stage_order if s in grouped.index])
        return grouped.reset_index()

    def _find_column(self, candidates: list) -> str:
        if self.data is None:
            return None
        for col in candidates:
            if col in self.data.columns:
                return col
        return None


if __name__ == "__main__":
    sample = pd.DataFrame({
        "기업명": ["뷰노", "루닛", "딥노이드", "뷰노", "루닛"],
        "연봉(만원)": [5000, 5500, 4200, 5200, 5800],
        "경력": ["신입", "경력 1~3년", "신입", "경력 3~5년", "경력 1~3년"],
        "기업규모": ["스타트업", "스타트업", "스타트업", "스타트업", "스타트업"],
    })
    analyzer = SalaryAnalyzer(sample)
    print("\n📊 기본 통계:", analyzer.get_salary_stats())
    print("\n📊 기업별 연봉:\n", analyzer.get_salary_by_company())
    print("\n📊 경력별 연봉:\n", analyzer.get_salary_by_career())

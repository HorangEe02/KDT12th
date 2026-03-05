"""
=============================================================
원티드 크롤러 - 의료/제약/바이오 채용 포지션 크롤링
=============================================================
- Wanted API v4 기반 (requests 사용, Selenium 불필요)
- 직군: 의료/제약/바이오 전체 (tag_type_ids=515)
- 수집 대상: 포지션명, 회사명, 기술스택, 자격요건, 우대사항,
             주요업무, 혜택및복지, 연봉범위, 근무지 등
=============================================================
"""

import os
import re
import time
from datetime import datetime

import requests
import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm

from config.settings import (
    DATA_RAW_DIR,
    URL_LIST_DIR,
    USER_AGENT,
    random_delay,
)


class WantedCrawler:
    """원티드 채용 포지션 크롤러 (API 기반)"""

    BASE_URL = "https://www.wanted.co.kr"
    API_BASE = "https://www.wanted.co.kr/api/v4"
    JOBS_API = f"{API_BASE}/jobs"

    # 의료/제약/바이오 직군 카테고리
    CATEGORY_ID = 515

    # 의료/제약/바이오 하위 직무 ID→이름 매핑
    SUBCATEGORY_MAP = {
        739: "연구원", 735: "임상시험 연구원", 740: "생명공학 연구원",
        627: "간호사", 731: "약학 분석 화학자", 630: "물리 치료사",
        736: "임상시험 간호사", 10134: "병원 코디네이터", 626: "임상병리사",
        629: "작업 치료사", 733: "약사", 737: "미생물학자",
        10054: "방사선사", 622: "치과 위생사", 623: "증례 관리자",
        624: "간병인", 625: "조무사", 631: "호흡장애 치료사",
        632: "수의 테크니션", 633: "의사", 634: "수의사",
        635: "간호 조무사", 636: "치과의사", 637: "검안사",
        732: "연구실 기사", 734: "약사 보조원", 738: "유전공학자",
        1040: "한의사", 10135: "의무기록사", 10147: "임상심리사",
    }

    def __init__(self, headless=True):
        """headless 파라미터는 하위 호환용 (API 방식에서는 미사용)"""
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": USER_AGENT,
            "Referer": f"{self.BASE_URL}/wdlist/{self.CATEGORY_ID}",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "ko-KR,ko;q=0.9",
            "wanted-user-country": "KR",
            "wanted-user-language": "ko",
        })
        self.collected_urls = []

    # ─────────────────────────────────────────
    # 1단계: 목록 API로 포지션 ID 전체 수집
    # ─────────────────────────────────────────
    def fetch_job_listings(self, limit: int = 20) -> list:
        """
        의료/제약/바이오 카테고리 전체 포지션 목록을 API로 수집

        Returns:
            list[dict]: 포지션 기본 정보 리스트
        """
        all_jobs = []
        offset = 0

        print(f"\n  📋 목록 수집 시작 (카테고리: 의료/제약/바이오, ID={self.CATEGORY_ID})")

        while True:
            params = {
                "country": "kr",
                "tag_type_ids": self.CATEGORY_ID,
                "job_sort": "job.popularity_order",
                "years": -1,
                "locations": "all",
                "limit": limit,
                "offset": offset,
            }

            try:
                resp = self.session.get(self.JOBS_API, params=params, timeout=15)
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                print(f"    ⚠️ API 호출 실패 (offset={offset}): {e}")
                break

            jobs = data.get("data", [])
            if not jobs:
                break

            all_jobs.extend(jobs)
            print(f"    수집 중... {len(all_jobs)}건 (offset={offset})", end="\r")

            # 다음 페이지 확인
            next_link = data.get("links", {}).get("next")
            if not next_link:
                break

            offset += limit
            time.sleep(0.3)

        print(f"    ✅ 목록 수집 완료: 총 {len(all_jobs)}개 포지션")
        return all_jobs

    # ─────────────────────────────────────────
    # 2단계: 상세 API로 개별 포지션 정보 수집
    # ─────────────────────────────────────────
    def fetch_job_detail(self, job_id: int) -> dict:
        """
        포지션 상세 정보를 API로 수집

        Returns:
            dict: 포지션 상세 정보
        """
        detail_url = f"{self.JOBS_API}/{job_id}"
        try:
            resp = self.session.get(detail_url, timeout=15)
            resp.raise_for_status()
            return resp.json().get("job", resp.json())
        except Exception as e:
            print(f"    ⚠️ 상세 조회 실패 (ID={job_id}): {e}")
            return None

    def _clean_html(self, text: str) -> str:
        """HTML 태그 제거 및 텍스트 정리"""
        if not text:
            return ""
        soup = BeautifulSoup(str(text), "html.parser")
        cleaned = soup.get_text(separator=" ", strip=True)
        # 연속 공백 정리
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned[:2000]

    def parse_job_data(self, listing: dict, detail: dict) -> dict:
        """
        목록 API + 상세 API 데이터를 통합 파싱

        Returns:
            dict: 통합된 포지션 정보
        """
        job_id = listing.get("id", "")
        position_url = f"{self.BASE_URL}/wd/{job_id}"

        result = {
            "포지션ID": job_id,
            "포지션명": listing.get("position", ""),
            "회사명": "",
            "업종": "",
            "근무지": "",
        }

        # 회사 정보 (목록 API)
        company = listing.get("company", {})
        if company:
            result["회사명"] = company.get("name", "")
            result["업종"] = company.get("industry_name", "")

        # 근무지 (목록 API)
        address = listing.get("address", {})
        if address:
            result["근무지"] = address.get("full_location", "")

        # 연봉 범위 (목록 API)
        annual_from = listing.get("annual_from")
        annual_to = listing.get("annual_to")
        if annual_from and annual_to:
            result["연봉범위"] = f"{annual_from}~{annual_to}년차"

        # 상세 정보 (상세 API)
        if detail:
            detail_info = detail.get("detail", {})
            if detail_info:
                result["주요업무"] = self._clean_html(detail_info.get("main_tasks", ""))
                result["자격요건"] = self._clean_html(detail_info.get("requirements", ""))
                result["우대사항"] = self._clean_html(detail_info.get("preferred_points", ""))
                result["혜택및복지"] = self._clean_html(detail_info.get("benefits", ""))
                result["회사소개"] = self._clean_html(detail_info.get("intro", ""))

            # 기술스택 태그
            skill_tags = detail.get("skill_tags", [])
            if skill_tags:
                tag_names = []
                for tag in skill_tags:
                    if isinstance(tag, dict):
                        tag_names.append(tag.get("title", str(tag)))
                    else:
                        tag_names.append(str(tag))
                result["기술스택태그"] = ", ".join(tag_names)

            # 마감일
            due_time = detail.get("due_time")
            if due_time:
                result["마감일"] = due_time

            # 카테고리 태그 (ID → 이름 변환)
            category_tags = detail.get("category_tags", [])
            if category_tags:
                cat_names = []
                for ct in category_tags:
                    if isinstance(ct, dict):
                        tag_id = ct.get("id")
                        name = self.SUBCATEGORY_MAP.get(tag_id, ct.get("title", ""))
                        if name:
                            cat_names.append(name)
                    elif isinstance(ct, str):
                        cat_names.append(ct)
                if cat_names:
                    result["직무카테고리"] = ", ".join(dict.fromkeys(cat_names))

        result["포지션URL"] = position_url
        result["수집일시"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # URL 기록
        self.collected_urls.append({
            "번호": len(self.collected_urls) + 1,
            "URL": position_url,
            "소스": "원티드",
            "검색키워드": "의료/제약/바이오",
            "수집일시": result["수집일시"],
            "데이터유형": "채용공고",
            "비고": f"카테고리ID={self.CATEGORY_ID}",
        })

        return result

    # ─────────────────────────────────────────
    # 전체 크롤링
    # ─────────────────────────────────────────
    def crawl_all(self, category_id=None) -> pd.DataFrame:
        """지정한 카테고리 전체 크롤링

        Args:
            category_id: 원티드 카테고리 ID (None이면 self.CATEGORY_ID 사용)
        """
        orig_category = self.CATEGORY_ID
        if category_id is not None:
            self.CATEGORY_ID = category_id
            self.session.headers["Referer"] = f"{self.BASE_URL}/wdlist/{category_id}"

        # 1단계: 목록 수집
        listings = self.fetch_job_listings()
        if not listings:
            print("  ⚠️ 수집된 포지션이 없습니다.")
            self.CATEGORY_ID = orig_category
            return pd.DataFrame()

        # 2단계: 각 포지션 상세 수집
        all_positions = []
        print(f"\n  📄 상세 정보 수집 시작 ({len(listings)}개)")

        for listing in tqdm(listings, desc="  포지션 상세 수집"):
            job_id = listing.get("id")
            if not job_id:
                continue

            detail = self.fetch_job_detail(job_id)
            position = self.parse_job_data(listing, detail)
            all_positions.append(position)
            time.sleep(0.3)

        self.CATEGORY_ID = orig_category

        if not all_positions:
            return pd.DataFrame()

        df = pd.DataFrame(all_positions)
        print(f"\n  ✅ 총 {len(df)}건 수집 완료")

        # 컬럼 요약 출력
        for col in df.columns:
            non_empty = df[col].astype(str).replace("", pd.NA).dropna().count()
            print(f"    {col}: {non_empty}건 채워짐")

        return df

    def save_data(self, df: pd.DataFrame, filename: str):
        """data/raw/ 저장"""
        if df is None or df.empty:
            print("  ⚠️ 저장할 데이터가 없습니다.")
            return

        path = os.path.join(DATA_RAW_DIR, f"{filename}.csv")
        df.to_csv(path, index=False, encoding="utf-8-sig")
        print(f"  💾 저장: {path} ({len(df)}건)")

    def _save_url_list(self):
        """URL 목록 저장"""
        if not self.collected_urls:
            return
        url_path = os.path.join(URL_LIST_DIR, "crawling_urls.csv")
        df_new = pd.DataFrame(self.collected_urls)
        if os.path.exists(url_path):
            df_existing = pd.read_csv(url_path, encoding="utf-8-sig")
            df_new["번호"] = range(len(df_existing) + 1, len(df_existing) + len(df_new) + 1)
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        else:
            df_combined = df_new
        df_combined.to_csv(url_path, index=False, encoding="utf-8-sig")
        print(f"  📋 URL 목록 저장: {url_path} (총 {len(df_combined)}개)")

    def _run_crawl(self, category_ids, file_suffix="의료AI"):
        """카테고리 ID 목록을 순회하며 크롤링 (내부 공통 로직)

        Args:
            category_ids: 카테고리 ID 리스트
            file_suffix: 저장 파일명 접미사

        Returns:
            DataFrame: 전체 포지션 데이터
        """
        print("=" * 60)
        print("📌 원티드 채용 포지션 크롤링 시작")
        print(f"📅 수집 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📋 대상 카테고리: {len(category_ids)}개 → {category_ids}")
        print("=" * 60)

        all_dfs = []
        for cat_id in category_ids:
            print(f"\n  📂 카테고리 {cat_id} 크롤링...")
            df = self.crawl_all(category_id=cat_id)
            if not df.empty:
                df["카테고리ID"] = cat_id
                all_dfs.append(df)

        if not all_dfs:
            print("\n⚠️ 수집된 데이터가 없습니다.")
            return pd.DataFrame()

        result = pd.concat(all_dfs, ignore_index=True)

        # 중복 포지션 제거
        before = len(result)
        result = result.drop_duplicates(subset=["포지션ID"], keep="first")
        after = len(result)
        if before != after:
            print(f"  🔄 중복 제거: {before} → {after}건")

        self.save_data(result, f"원티드_포지션_{file_suffix}")
        self._save_url_list()

        print(f"\n✅ 원티드 크롤링 완료! (총 {len(result)}건)")
        return result

    def run_all(self, extra_category_ids=None):
        """기본 카테고리 + 추가 카테고리로 크롤링 실행

        Args:
            extra_category_ids: 추가 카테고리 ID 리스트 (선택)

        원티드 주요 카테고리 ID:
            506: IT/웹/통신       507: 금융
            510: 교육             515: 의료/제약/바이오
            518: 게임             660: 모빌리티
        확인 방법: 원티드 웹 → 카테고리 선택 → 개발자도구 Network 탭

        사용 예시:
            # 기본 카테고리만 (의료/제약/바이오)
            crawler.run_all()

            # 기본 + IT/웹/통신 카테고리 추가
            crawler.run_all(extra_category_ids=[506])
        """
        category_ids = [self.CATEGORY_ID]
        if extra_category_ids:
            category_ids.extend(extra_category_ids)
            print(f"📌 추가 카테고리 {len(extra_category_ids)}개 포함")

        return self._run_crawl(category_ids, file_suffix="의료AI")

    def run_custom(self, category_ids, file_suffix="의료AI_추가"):
        """지정한 카테고리만 크롤링 (기본 카테고리 제외)

        Args:
            category_ids: 카테고리 ID 리스트 또는 단일 int
            file_suffix: 저장 파일명 접미사

        사용 예시:
            # IT/웹/통신 카테고리만 크롤링
            crawler.run_custom(506)

            # 여러 카테고리
            crawler.run_custom([506, 507], file_suffix="의료AI_IT금융")
        """
        if isinstance(category_ids, int):
            category_ids = [category_ids]

        if not category_ids:
            print("⚠️ 크롤링할 카테고리 ID가 없습니다.")
            return pd.DataFrame()

        return self._run_crawl(category_ids, file_suffix=file_suffix)

    def close(self):
        """세션 종료 (하위 호환용)"""
        self.session.close()
        print("🔒 세션 종료")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="원티드 의료 AI 채용 포지션 크롤러")
    parser.add_argument(
        "--mode", choices=["all", "custom"], default="all",
        help="실행 모드: all(기본+추가), custom(추가만)",
    )
    parser.add_argument(
        "--extra-category", nargs="+", type=int,
        help="추가 카테고리 ID (예: --extra-category 506 507)",
    )
    parser.add_argument(
        "--suffix", type=str, default="의료AI_추가",
        help="저장 파일명 접미사 (--mode custom 시 사용)",
    )

    args = parser.parse_args()
    crawler = WantedCrawler()

    try:
        if args.mode == "all":
            crawler.run_all(extra_category_ids=args.extra_category)
        elif args.mode == "custom":
            if not args.extra_category:
                print("⚠️ --extra-category 옵션으로 카테고리 ID를 지정해주세요.")
                print("예: python wanted_crawler.py --mode custom --extra-category 506 507")
                print("\n주요 카테고리 ID:")
                print("  506: IT/웹/통신  507: 금융  510: 교육")
                print("  515: 의료/제약/바이오  518: 게임  660: 모빌리티")
            else:
                crawler.run_custom(args.extra_category, file_suffix=args.suffix)
    finally:
        crawler.close()

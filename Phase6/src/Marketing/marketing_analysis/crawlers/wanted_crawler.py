"""
=============================================================
원티드 크롤러 - 마케팅/광고 채용 포지션 크롤링
=============================================================
- Wanted API v4 기반 (requests 사용, Selenium 불필요)
- 직군: 마케팅/광고 (tag_type_ids=523)
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

    # 마케팅/광고 직군 카테고리
    CATEGORY_ID = 523

    # 마케팅/광고 하위 직무 ID -> 이름 매핑
    SUBCATEGORY_MAP = {
        671: "디지털 마케터", 672: "콘텐츠 마케터", 673: "퍼포먼스 마케터",
        674: "브랜드 마케터", 675: "그로스해커", 676: "마케팅 전략 기획",
        677: "CRM 마케터", 678: "광고 기획자(AE)", 679: "미디어 플래너",
        680: "카피라이터", 681: "소셜미디어 마케터", 682: "PR 전문가",
        683: "마케팅 데이터 분석가", 684: "SEO/SEM 마케터",
        685: "이커머스 마케터", 686: "제휴 마케터",
    }

    def __init__(self, headless=True):
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

    def fetch_job_listings(self, limit: int = 20) -> list:
        all_jobs = []
        offset = 0
        print(f"\n  목록 수집 시작 (카테고리: 마케팅/광고, ID={self.CATEGORY_ID})")
        while True:
            params = {
                "country": "kr", "tag_type_ids": self.CATEGORY_ID,
                "job_sort": "job.popularity_order", "years": -1,
                "locations": "all", "limit": limit, "offset": offset,
            }
            try:
                resp = self.session.get(self.JOBS_API, params=params, timeout=15)
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                print(f"    API 호출 실패 (offset={offset}): {e}")
                break
            jobs = data.get("data", [])
            if not jobs:
                break
            all_jobs.extend(jobs)
            print(f"    수집 중... {len(all_jobs)}건 (offset={offset})", end="\r")
            next_link = data.get("links", {}).get("next")
            if not next_link:
                break
            offset += limit
            time.sleep(0.3)
        print(f"    목록 수집 완료: 총 {len(all_jobs)}개 포지션")
        return all_jobs

    def fetch_job_detail(self, job_id: int) -> dict:
        detail_url = f"{self.JOBS_API}/{job_id}"
        try:
            resp = self.session.get(detail_url, timeout=15)
            resp.raise_for_status()
            return resp.json().get("job", resp.json())
        except Exception as e:
            print(f"    상세 조회 실패 (ID={job_id}): {e}")
            return None

    def _clean_html(self, text: str) -> str:
        if not text:
            return ""
        soup = BeautifulSoup(str(text), "html.parser")
        cleaned = soup.get_text(separator=" ", strip=True)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned[:2000]

    def parse_job_data(self, listing: dict, detail: dict) -> dict:
        job_id = listing.get("id", "")
        position_url = f"{self.BASE_URL}/wd/{job_id}"
        result = {
            "포지션ID": job_id, "포지션명": listing.get("position", ""),
            "회사명": "", "업종": "", "근무지": "",
        }
        company = listing.get("company", {})
        if company:
            result["회사명"] = company.get("name", "")
            result["업종"] = company.get("industry_name", "")
        address = listing.get("address", {})
        if address:
            result["근무지"] = address.get("full_location", "")
        annual_from = listing.get("annual_from")
        annual_to = listing.get("annual_to")
        if annual_from and annual_to:
            result["연봉범위"] = f"{annual_from}~{annual_to}년차"
        if detail:
            detail_info = detail.get("detail", {})
            if detail_info:
                result["주요업무"] = self._clean_html(detail_info.get("main_tasks", ""))
                result["자격요건"] = self._clean_html(detail_info.get("requirements", ""))
                result["우대사항"] = self._clean_html(detail_info.get("preferred_points", ""))
                result["혜택및복지"] = self._clean_html(detail_info.get("benefits", ""))
                result["회사소개"] = self._clean_html(detail_info.get("intro", ""))
            skill_tags = detail.get("skill_tags", [])
            if skill_tags:
                tag_names = []
                for tag in skill_tags:
                    if isinstance(tag, dict):
                        tag_names.append(tag.get("title", str(tag)))
                    else:
                        tag_names.append(str(tag))
                result["기술스택태그"] = ", ".join(tag_names)
            due_time = detail.get("due_time")
            if due_time:
                result["마감일"] = due_time
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
        self.collected_urls.append({
            "번호": len(self.collected_urls) + 1,
            "URL": position_url, "소스": "원티드", "검색키워드": "마케팅/광고",
            "수집일시": result["수집일시"], "데이터유형": "채용공고",
            "비고": f"카테고리ID={self.CATEGORY_ID}",
        })
        return result

    def crawl_all(self, category_id=None) -> pd.DataFrame:
        orig_category = self.CATEGORY_ID
        if category_id is not None:
            self.CATEGORY_ID = category_id
            self.session.headers["Referer"] = f"{self.BASE_URL}/wdlist/{category_id}"
        listings = self.fetch_job_listings()
        if not listings:
            print("  수집된 포지션이 없습니다.")
            self.CATEGORY_ID = orig_category
            return pd.DataFrame()
        all_positions = []
        print(f"\n  상세 정보 수집 시작 ({len(listings)}개)")
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
        print(f"\n  총 {len(df)}건 수집 완료")
        for col in df.columns:
            non_empty = df[col].astype(str).replace("", pd.NA).dropna().count()
            print(f"    {col}: {non_empty}건 채워짐")
        return df

    def save_data(self, df: pd.DataFrame, filename: str):
        if df is None or df.empty:
            print("  저장할 데이터가 없습니다.")
            return
        path = os.path.join(DATA_RAW_DIR, f"{filename}.csv")
        df.to_csv(path, index=False, encoding="utf-8-sig")
        print(f"  저장: {path} ({len(df)}건)")

    def _save_url_list(self):
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
        print(f"  URL 목록 저장: {url_path} (총 {len(df_combined)}개)")

    def _run_crawl(self, category_ids, file_suffix="마케팅"):
        print("=" * 60)
        print("원티드 채용 포지션 크롤링 시작")
        print(f"수집 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"대상 카테고리: {len(category_ids)}개 -> {category_ids}")
        print("=" * 60)
        all_dfs = []
        for cat_id in category_ids:
            print(f"\n  카테고리 {cat_id} 크롤링...")
            df = self.crawl_all(category_id=cat_id)
            if not df.empty:
                df["카테고리ID"] = cat_id
                all_dfs.append(df)
        if not all_dfs:
            print("\n수집된 데이터가 없습니다.")
            return pd.DataFrame()
        result = pd.concat(all_dfs, ignore_index=True)
        before = len(result)
        result = result.drop_duplicates(subset=["포지션ID"], keep="first")
        after = len(result)
        if before != after:
            print(f"  중복 제거: {before} -> {after}건")
        self.save_data(result, f"원티드_포지션_{file_suffix}")
        self._save_url_list()
        print(f"\n원티드 크롤링 완료! (총 {len(result)}건)")
        return result

    def run_all(self, extra_category_ids=None):
        category_ids = [self.CATEGORY_ID]
        if extra_category_ids:
            category_ids.extend(extra_category_ids)
        return self._run_crawl(category_ids, file_suffix="마케팅")

    def run_custom(self, category_ids, file_suffix="마케팅_추가"):
        if isinstance(category_ids, int):
            category_ids = [category_ids]
        if not category_ids:
            print("크롤링할 카테고리 ID가 없습니다.")
            return pd.DataFrame()
        return self._run_crawl(category_ids, file_suffix=file_suffix)

    def close(self):
        self.session.close()
        print("세션 종료")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="원티드 마케팅 채용 포지션 크롤러")
    parser.add_argument("--mode", choices=["all", "custom"], default="all")
    parser.add_argument("--extra-category", nargs="+", type=int)
    parser.add_argument("--suffix", type=str, default="마케팅_추가")
    args = parser.parse_args()
    crawler = WantedCrawler()
    try:
        if args.mode == "all":
            crawler.run_all(extra_category_ids=args.extra_category)
        elif args.mode == "custom":
            if not args.extra_category:
                print("--extra-category 옵션으로 카테고리 ID를 지정해주세요.")
            else:
                crawler.run_custom(args.extra_category, file_suffix=args.suffix)
    finally:
        crawler.close()

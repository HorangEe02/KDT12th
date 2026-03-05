"""
=============================================================
📌 Naver OpenAPI 크롤링 - 자율주행·의료 AI 취업 동향 분석
=============================================================
- 블로그, 뉴스 검색 API를 활용하여 취준 동향 데이터 수집
- 1인당 최소 100개 이상 URL 확보
- 수집 데이터: 제목, 본문 요약, 링크, 게시일자
=============================================================
"""

import urllib.request
import urllib.parse
import json
import time
import re
import os
from datetime import datetime
import pandas as pd

# ============================================================
# 1. API 설정
# ============================================================
CLIENT_ID = "아이디"
CLIENT_SECRET = "시크릿코드"

# 저장 경로 설정
SAVE_DIR = "data_naver"
os.makedirs(SAVE_DIR, exist_ok=True)


# ============================================================
# 2. 검색 키워드 정의
# ============================================================
# 블로그 검색 키워드 (취준 동향, 준비 내용 중심)
BLOG_KEYWORDS = [
    "자율주행 취업 준비",
    "자율주행 개발자 취업",
    "자율주행 채용 공고",
    "ADAS 개발자 취업",
    "자율주행 신입 채용",
    "의료 AI 취업 준비",
    "의료AI 개발자 채용",
    "헬스케어 데이터 분석가",
    "헬스케어 AI 취업",
    "의료 데이터 사이언티스트",
    "자율주행 Python",
    "의료AI Python 개발",
    "자율주행 자격증 준비",
    "의료 AI 자격증",
    "자율주행 포트폴리오",
    "헬스케어 데이터 자격증",
    "ROS 자율주행 취업",
    "자율주행 딥러닝 취업",
    "의료 영상 AI 취업",
    "자율주행 스타트업 취업",
]

# 뉴스 검색 키워드 (산업 트렌드, 채용 현황 중심)
NEWS_KEYWORDS = [
    "자율주행 채용",
    "자율주행 인력 수요",
    "ADAS 채용 현황",
    "의료 AI 채용",
    "헬스케어 AI 인력",
    "자율주행 개발자 부족",
    "의료 AI 스타트업 채용",
    "자율주행 기술 인재",
    "디지털 헬스케어 채용",
    "자율주행 산업 전망",
    "의료 AI 산업 전망",
    "모빌리티 개발자 채용",
    "자율주행 연봉",
    "의료AI 연봉",
    "헬스케어 데이터 채용",
]


# ============================================================
# 3. HTML 태그 제거 함수
# ============================================================
def remove_html_tags(text):
    """HTML 태그 및 특수문자 제거"""
    clean = re.sub(r"<[^>]+>", "", text)  # HTML 태그 제거
    clean = re.sub(r"&[a-zA-Z]+;", " ", clean)  # HTML 엔티티 제거
    clean = clean.strip()
    return clean


# ============================================================
# 4. Naver 검색 API 호출 함수
# ============================================================
def search_naver(query, search_type="blog", display=100, start=1, sort="sim"):
    """
    Naver 검색 API 호출

    Parameters:
        query (str): 검색어
        search_type (str): "blog" 또는 "news"
        display (int): 한 번에 가져올 결과 수 (최대 100)
        start (int): 시작 위치 (1~1000)
        sort (str): "sim"(정확도순) 또는 "date"(최신순)

    Returns:
        dict: API 응답 JSON
    """
    base_url = f"https://openapi.naver.com/v1/search/{search_type}.json"

    params = {
        "query": query,
        "display": display,
        "start": start,
        "sort": sort,
    }

    url = base_url + "?" + urllib.parse.urlencode(params)

    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", CLIENT_ID)
    request.add_header("X-Naver-Client-Secret", CLIENT_SECRET)

    try:
        response = urllib.request.urlopen(request)
        if response.getcode() == 200:
            return json.loads(response.read().decode("utf-8"))
        else:
            print(f"  ⚠️ HTTP Error: {response.getcode()}")
            return None
    except urllib.error.URLError as e:
        print(f"  ❌ URL Error: {e}")
        return None
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return None


# ============================================================
# 5. 블로그 크롤링 함수
# ============================================================
def crawl_blog(keywords, max_per_keyword=100):
    """
    블로그 검색 크롤링
    - 키워드별 최대 100개씩 수집
    - 중복 URL 자동 제거
    """
    all_results = []
    seen_links = set()

    print("=" * 60)
    print("📝 블로그 크롤링 시작")
    print("=" * 60)

    for idx, keyword in enumerate(keywords, 1):
        print(f"\n[{idx}/{len(keywords)}] 키워드: '{keyword}'")

        collected = 0
        start = 1

        while collected < max_per_keyword and start <= 1000:
            display = min(100, max_per_keyword - collected)
            result = search_naver(
                keyword, "blog", display=display, start=start, sort="sim"
            )

            if result is None or "items" not in result or len(result["items"]) == 0:
                break

            for item in result["items"]:
                link = item.get("link", "")

                # 중복 URL 제거
                if link in seen_links:
                    continue
                seen_links.add(link)

                row = {
                    "검색키워드": keyword,
                    "제목": remove_html_tags(item.get("title", "")),
                    "내용요약": remove_html_tags(item.get("description", "")),
                    "블로거명": item.get("bloggername", ""),
                    "블로그링크": item.get("bloggerlink", ""),
                    "게시글링크": link,
                    "게시일자": item.get("postdate", ""),
                    "수집일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "출처": "Naver Blog",
                }
                all_results.append(row)
                collected += 1

            start += display
            time.sleep(0.15)  # API 호출 간격 (Rate Limit 방지)

        print(f"  → 수집 완료: {collected}건 (누적 고유: {len(all_results)}건)")

    print(f"\n✅ 블로그 총 수집: {len(all_results)}건 (중복 제거 완료)")
    return all_results


# ============================================================
# 6. 뉴스 크롤링 함수
# ============================================================
def crawl_news(keywords, max_per_keyword=100):
    """
    뉴스 검색 크롤링
    - 키워드별 최대 100개씩 수집
    - 중복 URL 자동 제거
    """
    all_results = []
    seen_links = set()

    print("=" * 60)
    print("📰 뉴스 크롤링 시작")
    print("=" * 60)

    for idx, keyword in enumerate(keywords, 1):
        print(f"\n[{idx}/{len(keywords)}] 키워드: '{keyword}'")

        collected = 0
        start = 1

        while collected < max_per_keyword and start <= 1000:
            display = min(100, max_per_keyword - collected)
            result = search_naver(
                keyword, "news", display=display, start=start, sort="date"
            )

            if result is None or "items" not in result or len(result["items"]) == 0:
                break

            for item in result["items"]:
                link = item.get("originallink", "") or item.get("link", "")

                if link in seen_links:
                    continue
                seen_links.add(link)

                row = {
                    "검색키워드": keyword,
                    "제목": remove_html_tags(item.get("title", "")),
                    "내용요약": remove_html_tags(item.get("description", "")),
                    "원본링크": link,
                    "네이버링크": item.get("link", ""),
                    "게시일자": item.get("pubDate", ""),
                    "수집일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "출처": "Naver News",
                }
                all_results.append(row)
                collected += 1

            start += display
            time.sleep(0.15)

        print(f"  → 수집 완료: {collected}건 (누적 고유: {len(all_results)}건)")

    print(f"\n✅ 뉴스 총 수집: {len(all_results)}건 (중복 제거 완료)")
    return all_results


# ============================================================
# 7. 데이터 저장 함수
# ============================================================
def save_data(data, filename, file_format="both"):
    """
    수집 데이터를 CSV 및 JSON으로 저장

    Parameters:
        data (list): 수집된 데이터 리스트
        filename (str): 파일명 (확장자 제외)
        file_format (str): "csv", "json", "both"
    """
    if not data:
        print("⚠️ 저장할 데이터가 없습니다.")
        return None

    df = pd.DataFrame(data)

    if file_format in ("csv", "both"):
        csv_path = os.path.join(SAVE_DIR, f"{filename}.csv")
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"  💾 CSV 저장 완료: {csv_path} ({len(df)}건)")

    if file_format in ("json", "both"):
        json_path = os.path.join(SAVE_DIR, f"{filename}.json")
        df.to_json(json_path, orient="records", force_ascii=False, indent=2)
        print(f"  💾 JSON 저장 완료: {json_path} ({len(df)}건)")

    return df


# ============================================================
# 8. URL 목록 저장 함수 (프로젝트 요구사항)
# ============================================================
def save_url_list(blog_data, news_data):
    """
    크롤링 URL 목록을 별도 파일로 저장
    - 프로젝트 요구사항: 1인당 최소 100개 URL 명시
    """
    urls = []

    for item in blog_data:
        urls.append(
            {
                "번호": len(urls) + 1,
                "유형": "블로그",
                "검색키워드": item["검색키워드"],
                "제목": item["제목"],
                "URL": item["게시글링크"],
            }
        )

    for item in news_data:
        urls.append(
            {
                "번호": len(urls) + 1,
                "유형": "뉴스",
                "검색키워드": item["검색키워드"],
                "제목": item["제목"],
                "URL": item["원본링크"],
            }
        )

    df = pd.DataFrame(urls)
    url_path = os.path.join(SAVE_DIR, "크롤링_URL_목록_네이버.csv")
    df.to_csv(url_path, index=False, encoding="utf-8-sig")
    print(f"\n📋 URL 목록 저장 완료: {url_path} (총 {len(urls)}개)")

    return df


# ============================================================
# 9. 메인 실행
# ============================================================
def main():
    print("🚀 Naver OpenAPI 크롤링 시작")
    print(f"📅 수집 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 저장 경로: {os.path.abspath(SAVE_DIR)}")
    print()

    # ---- 블로그 크롤링 ----
    blog_data = crawl_blog(BLOG_KEYWORDS, max_per_keyword=30)
    print()

    # ---- 뉴스 크롤링 ----
    news_data = crawl_news(NEWS_KEYWORDS, max_per_keyword=30)
    print()

    # ---- 데이터 저장 ----
    print("=" * 60)
    print("💾 데이터 저장")
    print("=" * 60)

    df_blog = save_data(blog_data, "naver_blog_자율주행_의료AI")
    df_news = save_data(news_data, "naver_news_자율주행_의료AI")

    # ---- URL 목록 저장 ----
    df_urls = save_url_list(blog_data, news_data)

    # ---- 수집 요약 ----
    print()
    print("=" * 60)
    print("📊 수집 결과 요약")
    print("=" * 60)
    print(f"  블로그 수집: {len(blog_data)}건")
    print(f"  뉴스 수집:   {len(news_data)}건")
    print(f"  총 URL 수:   {len(blog_data) + len(news_data)}개")

    if len(blog_data) + len(news_data) >= 100:
        print(f"  ✅ 최소 100개 URL 요구사항 충족!")
    else:
        print(f"  ⚠️ 100개 미달 - 키워드 추가 또는 max_per_keyword 증가 필요")

    # ---- 키워드별 수집 현황 ----
    if df_blog is not None:
        print("\n📝 블로그 키워드별 수집 현황:")
        blog_counts = df_blog["검색키워드"].value_counts()
        for kw, cnt in blog_counts.items():
            print(f"  - {kw}: {cnt}건")

    if df_news is not None:
        print("\n📰 뉴스 키워드별 수집 현황:")
        news_counts = df_news["검색키워드"].value_counts()
        for kw, cnt in news_counts.items():
            print(f"  - {kw}: {cnt}건")

    print("\n🎉 Naver OpenAPI 크롤링 완료!")
    return df_blog, df_news


if __name__ == "__main__":
    df_blog, df_news = main()

import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium
from dotenv import load_dotenv
import os
import hashlib
import math

load_dotenv()
KAKAO_API_KEY = os.getenv("KAKAO_API_KEY")

STADIUM_COORDS = {
    "잠실야구장 (LG·두산)":      {"x": "127.0720", "y": "37.5122"},
    "고척스카이돔 (키움)":        {"x": "126.8674", "y": "37.4982"},
    "인천 SSG랜더스필드 (SSG)":   {"x": "126.6934", "y": "37.4370"},
    "수원 kt wiz파크 (KT)":      {"x": "127.0086", "y": "37.2998"},
    "대전 한화볼파크 (한화)":     {"x": "127.4285", "y": "36.3174"},
    "대구 삼성라이온즈파크 (삼성)":{"x": "128.6814", "y": "35.8408"},
    "창원 NC파크 (NC)":          {"x": "128.5730", "y": "35.2225"},
    "사직야구장 (롯데)":          {"x": "129.0598", "y": "35.1940"},
    "광주 기아챔피언스필드 (KIA)": {"x": "126.8887", "y": "35.1683"},
}

FOOD_CATEGORIES = ["한식", "중식", "일식", "양식", "분식", "치킨", "피자", "술집/야식", "카페"]
STAY_CATEGORIES = ["호텔/콘도", "모텔", "게스트하우스", "펜션"]

CATEGORY_MAP = {
    "한식": "한식", "중식": "중식", "일식": "일식", "양식": "양식",
    "분식": "분식", "치킨": "치킨", "피자": "피자",
    "술집": "술집/야식", "포장마차": "술집/야식",
    "카페": "카페", "제과,베이커리": "카페",
    "호텔,콘도": "호텔/콘도", "모텔": "모텔",
    "게스트하우스": "게스트하우스", "펜션": "펜션",
    "여관,여인숙": "모텔",
}

CATEGORY_EMOJI = {
    "한식": "🍚", "중식": "🥢", "일식": "🍣", "양식": "🍝",
    "분식": "🥚", "치킨": "🍗", "피자": "🍕", "술집/야식": "🍺",
    "카페": "☕", "호텔/콘도": "🏨", "모텔": "🛏️",
    "게스트하우스": "🏠", "펜션": "🏡",
}

MARKER_COLORS = {
    "한식": "red", "중식": "orange", "일식": "purple",
    "양식": "pink", "분식": "beige", "치킨": "lightred",
    "피자": "darkred", "술집/야식": "darkblue", "카페": "cadetblue",
    "호텔/콘도": "blue", "모텔": "darkgreen",
    "게스트하우스": "green", "펜션": "lightgreen",
}

# 더미 이미지 — Unsplash 카테고리별 고정 URL
DUMMY_IMAGES = {
    "한식":      "https://images.unsplash.com/photo-1590301157890-4810ed352733?w=400&q=80",
    "중식":      "https://images.unsplash.com/photo-1563245372-f21724e3856d?w=400&q=80",
    "일식":      "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?w=400&q=80",
    "양식":      "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=400&q=80",
    "분식":      "https://images.unsplash.com/photo-1635363638580-c2809d049eee?w=400&q=80",
    "치킨":      "https://images.unsplash.com/photo-1626082927389-6cd097cdc6ec?w=400&q=80",
    "피자":      "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=400&q=80",
    "술집/야식":  "https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?w=400&q=80",
    "카페":      "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?w=400&q=80",
    "호텔/콘도":  "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=400&q=80",
    "모텔":      "https://images.unsplash.com/photo-1631049307264-da0ec9d70304?w=400&q=80",
    "게스트하우스":"https://images.unsplash.com/photo-1555854877-bab0e564b8d5?w=400&q=80",
    "펜션":      "https://images.unsplash.com/photo-1449158743715-0a90ebb6d2d8?w=400&q=80",
}

def dummy_rating(name: str) -> float:
    h = int(hashlib.md5(name.encode()).hexdigest(), 16)
    return round(3.5 + (h % 16) / 10, 1)

def walk_desc(km: float) -> str:
    mins = int(km / 0.08)
    if mins <= 10:
        return f"도보 {mins}분"
    elif mins <= 30:
        return f"도보 약 {mins}분"
    else:
        return f"차량 약 {int(km/0.5)}분"


# ──────────────────────────────────────────
# 데이터 로딩
# ──────────────────────────────────────────
@st.cache_data(ttl=600)
def fetch_places(x: str, y: str, radius_m: int) -> pd.DataFrame:
    url = "https://dapi.kakao.com/v2/local/search/category.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    results = []
    for code in ["FD6", "CE7", "AD5"]:
        for page in range(1, 4):
            params = {"category_group_code": code, "x": x, "y": y,
                      "radius": radius_m, "size": 15, "page": page, "sort": "distance"}
            res = requests.get(url, headers=headers, params=params)
            if res.status_code != 200:
                break
            docs = res.json().get("documents", [])
            if not docs:
                break
            results.extend(docs)
    if not results:
        return pd.DataFrame()
    df = pd.DataFrame(results)
    df = df.drop_duplicates(subset=["place_url"]).reset_index(drop=True)
    df = df[["place_name","category_name","road_address_name",
             "address_name","phone","distance","place_url","x","y"]].copy()
    df.columns = ["이름","카테고리_원본","도로명주소","지번주소","전화","거리(m)","카카오맵","경도","위도"]
    df["거리(km)"] = df["거리(m)"].astype(float) / 1000
    df["경도"] = df["경도"].astype(float)
    df["위도"] = df["위도"].astype(float)
    df["주소"] = df["도로명주소"].where(df["도로명주소"] != "", df["지번주소"])
    def normalize(raw):
        parts = [p.strip() for p in raw.split(">")]
        for d in [1, 2, 0]:
            if d < len(parts):
                m = CATEGORY_MAP.get(parts[d])
                if m: return m
        return parts[-1]
    df["카테고리"] = df["카테고리_원본"].apply(normalize)
    df["별점"] = df["이름"].apply(dummy_rating)
    df["이미지"] = df["카테고리"].apply(lambda c: DUMMY_IMAGES.get(c, DUMMY_IMAGES["한식"]))
    return df


# ──────────────────────────────────────────
# 지도
# ──────────────────────────────────────────
def build_map(df, cx, cy):
    lat, lng = float(cy), float(cx)
    m = folium.Map(location=[lat, lng], zoom_start=15)
    folium.Marker([lat, lng], tooltip="경기장",
                  popup=folium.Popup("<b>⚾ 경기장</b>", max_width=120),
                  icon=folium.Icon(color="black", icon="star")).add_to(m)
    for _, row in df.iterrows():
        color = MARKER_COLORS.get(row["카테고리"], "gray")
        emoji = CATEGORY_EMOJI.get(row["카테고리"], "📍")
        icon  = "home" if row["카테고리"] in STAY_CATEGORIES else "cutlery"
        popup_html = f"""
        <div style="font-family:'Manrope',sans-serif;width:210px;font-size:13px;line-height:1.6">
          <img src="{row['이미지']}" style="width:100%;height:110px;object-fit:cover;border-radius:6px;margin-bottom:8px"/>
          <b style="font-size:14px;color:#00193c">{emoji} {row['이름']}</b><br>
          <span style="color:#43474f;font-size:12px">{row['카테고리']}</span>
          <span style="float:right;background:#f8f9fa;border-radius:20px;padding:1px 8px;font-size:12px;font-weight:700;color:#00193c">⭐ {row['별점']}</span>
          <hr style="margin:6px 0;border-color:#e1e3e4">
          📍 {row['주소']}<br>
          🚶 경기장까지 {row['거리(km)']:.2f} km<br>
          <a href="{row['카카오맵']}" target="_blank"
             style="display:inline-block;margin-top:8px;background:#FEE500;color:#3C1E1E;
                    padding:4px 12px;border-radius:6px;text-decoration:none;font-size:12px;font-weight:700">
            카카오맵에서 보기
          </a>
        </div>"""
        folium.Marker([row["위도"], row["경도"]],
                      tooltip=f"{emoji} {row['이름']} | ⭐{row['별점']}",
                      popup=folium.Popup(popup_html, max_width=230),
                      icon=folium.Icon(color=color, icon=icon)).add_to(m)
    return m


# ──────────────────────────────────────────
# HTML 카드 그리드
# ──────────────────────────────────────────
def render_cards_html(df: pd.DataFrame) -> str:
    if df.empty:
        return "<p style='color:#747781;font-size:14px;padding:12px'>해당하는 장소가 없습니다.</p>"

    cards = ""
    for _, row in df.iterrows():
        emoji   = CATEGORY_EMOJI.get(row["카테고리"], "📍")
        walk    = walk_desc(row["거리(km)"])
        rating  = row["별점"]
        stars   = int(rating)
        tag_bg  = "#a0f399" if row["카테고리"] in STAY_CATEGORIES else "#d7e2ff"
        tag_col = "#002204" if row["카테고리"] in STAY_CATEGORIES else "#001b3f"

        cards += f"""
        <article style="background:#fff;border-radius:12px;overflow:hidden;
                        box-shadow:0 1px 6px rgba(0,0,0,0.08);display:flex;
                        flex-direction:column;cursor:pointer;transition:box-shadow .2s"
                 onmouseover="this.style.boxShadow='0 4px 20px rgba(0,25,60,0.15)'"
                 onmouseout="this.style.boxShadow='0 1px 6px rgba(0,0,0,0.08)'">
          <div style="position:relative;height:180px;overflow:hidden">
            <a href="{row['카카오맵']}" target="_blank" style="display:block;height:100%">
            <img src="{row['이미지']}" alt="{row['이름']}"
                 style="width:100%;height:100%;object-fit:cover;transition:transform .5s"
                 onmouseover="this.style.transform='scale(1.05)'"
                 onmouseout="this.style.transform='scale(1)'"/>
            </a>
            <div style="position:absolute;top:10px;right:10px;background:rgba(248,249,250,0.85);
                        backdrop-filter:blur(6px);padding:3px 10px;border-radius:20px;
                        font-size:12px;font-weight:700;color:#00193c;display:flex;align-items:center;gap:4px">
              ⭐ {rating}
            </div>
          </div>
          <div style="padding:16px;display:flex;flex-direction:column;flex:1">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:4px">
              <h3 style="margin:0;font-size:15px;font-weight:700;color:#00193c;
                         font-family:'Plus Jakarta Sans',sans-serif">{emoji} {row['이름']}</h3>
            </div>
            <p style="margin:0 0 10px;font-size:12px;color:#43474f">{row['주소']}</p>
            <div style="display:flex;align-items:center;gap:8px;margin-top:auto;flex-wrap:wrap">
              <span style="background:{tag_bg};color:{tag_col};padding:4px 10px;
                           border-radius:8px;font-size:12px;font-weight:700">
                🚶 {walk}
              </span>
              <span style="background:#f3f4f5;color:#43474f;padding:4px 10px;
                           border-radius:8px;font-size:12px;font-weight:600">
                {row['카테고리']}
              </span>
              <a href="{row['카카오맵']}" target="_blank"
                 style="margin-left:auto;background:#FEE500;color:#3C1E1E;padding:4px 12px;
                        border-radius:6px;text-decoration:none;font-size:12px;font-weight:700">
                카카오맵
              </a>
            </div>
          </div>
        </article>"""

    return f"""
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@700;800&family=Manrope:wght@400;600&display=swap" rel="stylesheet"/>
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));
                gap:16px;padding:4px 2px 16px">
      {cards}
    </div>"""


# ──────────────────────────────────────────
# 메인
# ──────────────────────────────────────────
def render_tab3():
    if not KAKAO_API_KEY:
        st.error(".env 파일에 KAKAO_API_KEY가 없습니다.")
        return

    # 사이드바
    with st.sidebar:
        st.markdown("### 경기장 선택")
        stadium = st.selectbox("경기장", list(STADIUM_COORDS.keys()))

    coords = STADIUM_COORDS[stadium]

    # 헤더
    st.markdown(
        "<h2 style='font-family:Plus Jakarta Sans,sans-serif;font-size:28px;"
        "font-weight:800;color:#00193c;margin-bottom:4px'>맛집 · 숙소</h2>"
        "<p style='color:#43474f;margin-bottom:16px'>경기장 주변 추천 장소를 둘러보세요.</p>",
        unsafe_allow_html=True
    )

    # 상단 필터
    dist_col, food_col, stay_col = st.columns([1, 2, 2])
    with dist_col:
        max_dist = st.slider("최대 탐색 거리 (km)", 0.5, 3.0, 2.0, step=0.5)
    with food_col:
        selected_food = st.multiselect("맛집 카테고리", FOOD_CATEGORIES, default=FOOD_CATEGORIES)
    with stay_col:
        selected_stay = st.multiselect("숙소 카테고리", STAY_CATEGORIES, default=STAY_CATEGORIES)

    # 데이터 로드
    with st.spinner("장소 정보를 불러오는 중..."):
        df = fetch_places(coords["x"], coords["y"], int(max_dist * 1000))

    if df.empty:
        st.warning("검색 결과가 없습니다. 탐색 거리를 늘려보세요.")
        return

    selected_cats = selected_food + selected_stay
    filtered = df[(df["카테고리"].isin(selected_cats)) & (df["거리(km)"] <= max_dist)]
    df_food  = filtered[filtered["카테고리"].isin(selected_food)].sort_values("거리(km)")
    df_stay  = filtered[filtered["카테고리"].isin(selected_stay)].sort_values("거리(km)")

    # 요약
    c1, c2, c3 = st.columns(3)
    c1.metric("맛집", f"{len(df_food)}곳")
    c2.metric("숙소", f"{len(df_stay)}곳")
    c3.metric("탐색 반경", f"{max_dist} km")

    st.divider()

    # 지도
    if not filtered.empty:
        fmap = build_map(filtered, coords["x"], coords["y"])
        st_folium(fmap, use_container_width=True, height=480)
        st.caption("⭐ 마커 클릭 시 사진·별점·카카오맵 링크 확인  |  ★ 검정 별 = 경기장")
    else:
        st.info("선택한 카테고리에 해당하는 장소가 없습니다.")

    st.divider()

    # 맛집 expander
    food_label = f"🍽️ 맛집 목록  ({len(df_food)}곳)"
    with st.expander(food_label, expanded=True):
        st.components.v1.html(render_cards_html(df_food), height=600, scrolling=True)

    # 숙소 expander
    stay_label = f"🏨 숙소 목록  ({len(df_stay)}곳)"
    with st.expander(stay_label, expanded=True):
        st.components.v1.html(render_cards_html(df_stay), height=600, scrolling=True)


# ──────────────────────────────────────────
if __name__ == "__main__":
    st.set_page_config(page_title="맛집·숙소", layout="wide")
    render_tab3()

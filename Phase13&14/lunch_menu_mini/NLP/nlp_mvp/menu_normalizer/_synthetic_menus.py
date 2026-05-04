"""
합성 표준 메뉴 100건.

테스트·스모크 검증 전용. Mini nutrition_info DB 미완성 시 사용.
모든 ID 는 menu_test_set.csv 의 expected_id 와 정렬되어야 한다.
"""
from __future__ import annotations

SYNTHETIC_STANDARD_MENUS: list[dict[str, str]] = [
    # 한식 — 찌개/국/탕 (15)
    {"id": "kimchi_jjigae", "name": "김치찌개", "category": "한식"},
    {"id": "doenjang_jjigae", "name": "된장찌개", "category": "한식"},
    {"id": "sundubu_jjigae", "name": "순두부찌개", "category": "한식"},
    {"id": "budae_jjigae", "name": "부대찌개", "category": "한식"},
    {"id": "cheonggukjang_jjigae", "name": "청국장찌개", "category": "한식"},
    {"id": "gukbap", "name": "국밥", "category": "한식"},
    {"id": "sundae_guk", "name": "순댓국", "category": "한식"},
    {"id": "ppyeo_haejangguk", "name": "뼈해장국", "category": "한식"},
    {"id": "kongnamul_gukbap", "name": "콩나물국밥", "category": "한식"},
    {"id": "somerihi_gukbap", "name": "소머리국밥", "category": "한식"},
    {"id": "galbitang", "name": "갈비탕", "category": "한식"},
    {"id": "samgyetang", "name": "삼계탕", "category": "한식"},
    {"id": "seolleongtang", "name": "설렁탕", "category": "한식"},
    {"id": "dongtae_tang", "name": "동태탕", "category": "한식"},
    {"id": "chueotang", "name": "추어탕", "category": "한식"},

    # 한식 — 밥류 표준 (NEW)
    {"id": "ssalbap", "name": "쌀밥", "category": "한식"},
    {"id": "japgokbap", "name": "잡곡밥", "category": "한식"},
    {"id": "gonggibap", "name": "공기밥", "category": "한식"},
    {"id": "hyunmibap", "name": "현미밥", "category": "한식"},

    # 한식 — 갈비류 표준 보강 (NEW)
    {"id": "galbi_jjim", "name": "갈비찜", "category": "한식"},
    {"id": "yangnyeom_galbi", "name": "양념갈비", "category": "한식"},
    {"id": "samgyeopsal_gui", "name": "삼겹살구이", "category": "한식"},

    # 한식 — 볶음/구이/덮밥 (10)
    {"id": "jeyuk_bokkeum", "name": "제육볶음", "category": "한식"},
    {"id": "jeyuk_deopbap", "name": "제육덮밥", "category": "한식"},
    {"id": "bulgogi", "name": "불고기", "category": "한식"},
    {"id": "bulgogi_baekban", "name": "불고기백반", "category": "한식"},
    {"id": "samgyeopsal", "name": "삼겹살", "category": "한식"},
    {"id": "galbi", "name": "갈비", "category": "한식"},
    {"id": "dakgalbi", "name": "닭갈비", "category": "한식"},
    {"id": "ojingeo_bokkeum", "name": "오징어볶음", "category": "한식"},
    {"id": "nakji_bokkeum", "name": "낙지볶음", "category": "한식"},
    {"id": "duruchigi", "name": "두루치기", "category": "한식"},

    # 한식 — 면류 (8)
    {"id": "naengmyeon", "name": "냉면", "category": "한식"},
    {"id": "mul_naengmyeon", "name": "물냉면", "category": "한식"},
    {"id": "bibim_naengmyeon", "name": "비빔냉면", "category": "한식"},
    {"id": "kalguksu", "name": "칼국수", "category": "한식"},
    {"id": "janchi_guksu", "name": "잔치국수", "category": "한식"},
    {"id": "makguksu", "name": "막국수", "category": "한식"},
    {"id": "kongguksu", "name": "콩국수", "category": "한식"},
    {"id": "bibim_guksu", "name": "비빔국수", "category": "한식"},

    # 한식 — 밥류 (10)
    {"id": "bibimbap", "name": "비빔밥", "category": "한식"},
    {"id": "dolsot_bibimbap", "name": "돌솥비빔밥", "category": "한식"},
    {"id": "jeonju_bibimbap", "name": "전주비빔밥", "category": "한식"},
    {"id": "yukhoe_bibimbap", "name": "육회비빔밥", "category": "한식"},
    {"id": "kimbap_baekban", "name": "김밥백반", "category": "한식"},
    {"id": "ssambap", "name": "쌈밥", "category": "한식"},
    {"id": "gimbap", "name": "김밥", "category": "한식"},
    {"id": "chamchi_gimbap", "name": "참치김밥", "category": "한식"},
    {"id": "chicken", "name": "치킨", "category": "한식"},
    {"id": "fried_chicken", "name": "후라이드치킨", "category": "한식"},

    # 한식 — 분식·기타 (5)
    {"id": "yangnyeom_chicken", "name": "양념치킨", "category": "한식"},
    {"id": "tteokbokki", "name": "떡볶이", "category": "분식"},
    {"id": "rabokki", "name": "라볶이", "category": "분식"},
    {"id": "sundae", "name": "순대", "category": "분식"},
    {"id": "twigim", "name": "튀김", "category": "분식"},

    # 분식·기타 (2)
    {"id": "eomuk", "name": "어묵", "category": "분식"},
    {"id": "ramyeon", "name": "라면", "category": "분식"},

    # 중식 (8)
    {"id": "jjajangmyeon", "name": "짜장면", "category": "중식"},
    {"id": "gan_jjajang", "name": "간짜장", "category": "중식"},
    {"id": "jjamppong", "name": "짬뽕", "category": "중식"},
    {"id": "jjamjjamyeon", "name": "짬짜면", "category": "중식"},
    {"id": "tangsuyuk", "name": "탕수육", "category": "중식"},
    {"id": "mapa_tofu", "name": "마파두부", "category": "중식"},
    {"id": "kkanpunggi", "name": "깐풍기", "category": "중식"},
    {"id": "yusanseul", "name": "유산슬", "category": "중식"},

    # 일식 (15)
    {"id": "donkatsu", "name": "돈까스", "category": "일식"},
    {"id": "cheese_donkatsu", "name": "치즈돈까스", "category": "일식"},
    {"id": "ramen", "name": "라멘", "category": "일식"},
    {"id": "udon", "name": "우동", "category": "일식"},
    {"id": "soba", "name": "소바", "category": "일식"},
    {"id": "deopbap", "name": "덮밥", "category": "일식"},
    {"id": "curry_rice", "name": "카레라이스", "category": "일식"},
    {"id": "sushi", "name": "초밥", "category": "일식"},
    {"id": "sashimi", "name": "회", "category": "일식"},
    {"id": "omurice", "name": "오므라이스", "category": "일식"},
    {"id": "gyudon", "name": "규동", "category": "일식"},
    {"id": "katsudon", "name": "카츠동", "category": "일식"},
    {"id": "tendon", "name": "텐동", "category": "일식"},
    {"id": "yakitori", "name": "야키토리", "category": "일식"},
    {"id": "takoyaki", "name": "타코야키", "category": "일식"},

    # 양식 (15)
    {"id": "pasta", "name": "파스타", "category": "양식"},
    {"id": "cream_pasta", "name": "크림파스타", "category": "양식"},
    {"id": "tomato_pasta", "name": "토마토파스타", "category": "양식"},
    {"id": "aglio_olio", "name": "알리오올리오", "category": "양식"},
    {"id": "pizza", "name": "피자", "category": "양식"},
    {"id": "margherita_pizza", "name": "마르게리타피자", "category": "양식"},
    {"id": "pepperoni_pizza", "name": "페퍼로니피자", "category": "양식"},
    {"id": "risotto", "name": "리조또", "category": "양식"},
    {"id": "steak", "name": "스테이크", "category": "양식"},
    {"id": "salad", "name": "샐러드", "category": "양식"},
    {"id": "caesar_salad", "name": "시저샐러드", "category": "양식"},
    {"id": "chicken_salad", "name": "닭가슴살샐러드", "category": "양식"},
    {"id": "sandwich", "name": "샌드위치", "category": "양식"},
    {"id": "club_sandwich", "name": "클럽샌드위치", "category": "양식"},
    {"id": "hamburger", "name": "햄버거", "category": "양식"},

    # 양식 보강 (1)
    {"id": "cheeseburger", "name": "치즈버거", "category": "양식"},

    # 동남아·중남미·중동 (8)
    {"id": "pho", "name": "쌀국수", "category": "동남아"},
    {"id": "pad_thai", "name": "팟타이", "category": "동남아"},
    {"id": "tom_yum_goong", "name": "똠얌꿍", "category": "동남아"},
    {"id": "goi_cuon", "name": "월남쌈", "category": "동남아"},
    {"id": "banh_mi", "name": "반미", "category": "동남아"},
    {"id": "taco", "name": "타코", "category": "중남미"},
    {"id": "burrito", "name": "부리또", "category": "중남미"},
    {"id": "kebab", "name": "케밥", "category": "중동"},
]

# 무결성 검증: ID 유일성
assert len({m["id"] for m in SYNTHETIC_STANDARD_MENUS}) == len(SYNTHETIC_STANDARD_MENUS), \
    "Duplicate IDs in SYNTHETIC_STANDARD_MENUS"

# 100건 ±5 허용
assert 95 <= len(SYNTHETIC_STANDARD_MENUS) <= 105, \
    f"Expected ~100 entries, got {len(SYNTHETIC_STANDARD_MENUS)}"

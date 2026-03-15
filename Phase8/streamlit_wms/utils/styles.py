"""v2 디자인 시스템 — Liquid Glass 아이콘 + 다크 사이드바 + 모던 KPI"""

# ── 색상 팔레트 ────────────────────────────────────────────
COLORS = {
    "bg_dark": "#1a1a2e",
    "bg_sidebar": "#16213e",
    "bg_card": "#ffffff",
    "bg_page": "#f5f7fa",
    "accent_green": "#4CAF50",
    "accent_red": "#F44336",
    "accent_orange": "#FF9800",
    "accent_blue": "#2196F3",
    "accent_purple": "#9C27B0",
    "accent_cyan": "#00BCD4",
    "text_dark": "#1a1a2e",
    "text_light": "#e0e0e0",
    "text_muted": "#6c757d",
    "border": "#e0e0e0",
}

# ── Liquid Glass SVG 아이콘 라이브러리 ─────────────────────
# Apple Liquid Glass 스타일: 반투명 그라디언트 + 내부 광택 + 부드러운 곡선
LIQUID_ICONS = {
    # ── KPI / Dashboard ────────────────────────────────
    "package": """<svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
<defs><linearGradient id="g_pkg" x1="0" y1="0" x2="28" y2="28"><stop offset="0%" stop-color="{c}" stop-opacity="0.9"/><stop offset="100%" stop-color="{c}" stop-opacity="0.5"/></linearGradient></defs>
<rect x="3" y="6" width="22" height="18" rx="3" fill="url(#g_pkg)"/>
<rect x="3" y="6" width="22" height="18" rx="3" fill="white" fill-opacity="0.15"/>
<path d="M3 12h22" stroke="white" stroke-opacity="0.4" stroke-width="1"/>
<path d="M11 6v6h6V6" stroke="white" stroke-opacity="0.5" stroke-width="1"/>
<rect x="4" y="7" width="20" height="4" rx="1" fill="white" fill-opacity="0.1"/>
</svg>""",

    "alert": """<svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
<defs><linearGradient id="g_alert" x1="0" y1="0" x2="28" y2="28"><stop offset="0%" stop-color="{c}" stop-opacity="0.9"/><stop offset="100%" stop-color="{c}" stop-opacity="0.5"/></linearGradient></defs>
<circle cx="14" cy="14" r="11" fill="url(#g_alert)"/>
<circle cx="14" cy="14" r="11" fill="white" fill-opacity="0.12"/>
<circle cx="14" cy="7" r="5" fill="white" fill-opacity="0.08"/>
<path d="M14 9v6" stroke="white" stroke-width="2.5" stroke-linecap="round"/>
<circle cx="14" cy="19" r="1.5" fill="white"/>
</svg>""",

    "warning": """<svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
<defs><linearGradient id="g_warn" x1="0" y1="2" x2="28" y2="26"><stop offset="0%" stop-color="{c}" stop-opacity="0.9"/><stop offset="100%" stop-color="{c}" stop-opacity="0.5"/></linearGradient></defs>
<path d="M14 3L26 25H2L14 3z" fill="url(#g_warn)" stroke="white" stroke-opacity="0.2" stroke-width="0.5"/>
<path d="M14 3L26 25H2L14 3z" fill="white" fill-opacity="0.1"/>
<path d="M6 23L14 5L22 23" fill="white" fill-opacity="0.06"/>
<path d="M14 12v5" stroke="white" stroke-width="2.5" stroke-linecap="round"/>
<circle cx="14" cy="21" r="1.5" fill="white"/>
</svg>""",

    "dollar": """<svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
<defs><linearGradient id="g_dol" x1="0" y1="0" x2="28" y2="28"><stop offset="0%" stop-color="{c}" stop-opacity="0.9"/><stop offset="100%" stop-color="{c}" stop-opacity="0.5"/></linearGradient></defs>
<circle cx="14" cy="14" r="11" fill="url(#g_dol)"/>
<circle cx="14" cy="14" r="11" fill="white" fill-opacity="0.12"/>
<ellipse cx="14" cy="8" rx="8" ry="5" fill="white" fill-opacity="0.08"/>
<path d="M14 7v14M10.5 10.5c0-1.5 1.5-2.5 3.5-2.5s3.5 1 3.5 2.5-1.5 2.2-3.5 2.7-3.5 1.2-3.5 2.8 1.5 2.5 3.5 2.5 3.5-1 3.5-2.5" stroke="white" stroke-width="1.8" stroke-linecap="round"/>
</svg>""",

    "target": """<svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
<defs><linearGradient id="g_tgt" x1="0" y1="0" x2="28" y2="28"><stop offset="0%" stop-color="{c}" stop-opacity="0.9"/><stop offset="100%" stop-color="{c}" stop-opacity="0.5"/></linearGradient></defs>
<circle cx="14" cy="14" r="11" fill="url(#g_tgt)"/>
<circle cx="14" cy="14" r="11" fill="white" fill-opacity="0.12"/>
<ellipse cx="14" cy="8" rx="8" ry="5" fill="white" fill-opacity="0.08"/>
<circle cx="14" cy="14" r="7" stroke="white" stroke-opacity="0.5" stroke-width="1.2"/>
<circle cx="14" cy="14" r="3.5" stroke="white" stroke-opacity="0.7" stroke-width="1.2"/>
<circle cx="14" cy="14" r="1.5" fill="white"/>
</svg>""",

    "chart_up": """<svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
<defs><linearGradient id="g_chu" x1="0" y1="0" x2="28" y2="28"><stop offset="0%" stop-color="{c}" stop-opacity="0.9"/><stop offset="100%" stop-color="{c}" stop-opacity="0.5"/></linearGradient></defs>
<rect x="3" y="3" width="22" height="22" rx="5" fill="url(#g_chu)"/>
<rect x="3" y="3" width="22" height="22" rx="5" fill="white" fill-opacity="0.12"/>
<rect x="4" y="4" width="20" height="8" rx="3" fill="white" fill-opacity="0.07"/>
<polyline points="7,20 11,15 15,17 21,9" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
<polyline points="17,9 21,9 21,13" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>""",

    "search": """<svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
<defs><linearGradient id="g_src" x1="0" y1="0" x2="28" y2="28"><stop offset="0%" stop-color="{c}" stop-opacity="0.9"/><stop offset="100%" stop-color="{c}" stop-opacity="0.5"/></linearGradient></defs>
<rect x="3" y="3" width="22" height="22" rx="5" fill="url(#g_src)"/>
<rect x="3" y="3" width="22" height="22" rx="5" fill="white" fill-opacity="0.12"/>
<rect x="4" y="4" width="20" height="8" rx="3" fill="white" fill-opacity="0.07"/>
<circle cx="12.5" cy="12.5" r="5" stroke="white" stroke-width="2"/>
<path d="M16.5 16.5L21 21" stroke="white" stroke-width="2" stroke-linecap="round"/>
</svg>""",

    "ruler": """<svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
<defs><linearGradient id="g_rul" x1="0" y1="0" x2="28" y2="28"><stop offset="0%" stop-color="{c}" stop-opacity="0.9"/><stop offset="100%" stop-color="{c}" stop-opacity="0.5"/></linearGradient></defs>
<rect x="3" y="3" width="22" height="22" rx="5" fill="url(#g_rul)"/>
<rect x="3" y="3" width="22" height="22" rx="5" fill="white" fill-opacity="0.12"/>
<rect x="4" y="4" width="20" height="8" rx="3" fill="white" fill-opacity="0.07"/>
<path d="M7 21V10M12 21V14M17 21V12M22 21V8" stroke="white" stroke-width="2.2" stroke-linecap="round"/>
</svg>""",

    "tag": """<svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
<defs><linearGradient id="g_tag" x1="0" y1="0" x2="28" y2="28"><stop offset="0%" stop-color="{c}" stop-opacity="0.9"/><stop offset="100%" stop-color="{c}" stop-opacity="0.5"/></linearGradient></defs>
<rect x="3" y="3" width="22" height="22" rx="5" fill="url(#g_tag)"/>
<rect x="3" y="3" width="22" height="22" rx="5" fill="white" fill-opacity="0.12"/>
<rect x="4" y="4" width="20" height="8" rx="3" fill="white" fill-opacity="0.07"/>
<path d="M7 7h7l8 8-7 7-8-8V7z" stroke="white" stroke-width="1.5" fill="white" fill-opacity="0.1"/>
<circle cx="11" cy="11" r="1.5" fill="white"/>
</svg>""",

    "cross": """<svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
<defs><linearGradient id="g_cross" x1="0" y1="0" x2="28" y2="28"><stop offset="0%" stop-color="{c}" stop-opacity="0.9"/><stop offset="100%" stop-color="{c}" stop-opacity="0.5"/></linearGradient></defs>
<circle cx="14" cy="14" r="11" fill="url(#g_cross)"/>
<circle cx="14" cy="14" r="11" fill="white" fill-opacity="0.12"/>
<ellipse cx="14" cy="8" rx="8" ry="5" fill="white" fill-opacity="0.08"/>
<path d="M10 10l8 8M18 10l-8 8" stroke="white" stroke-width="2.5" stroke-linecap="round"/>
</svg>""",

    "check": """<svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
<defs><linearGradient id="g_chk" x1="0" y1="0" x2="28" y2="28"><stop offset="0%" stop-color="{c}" stop-opacity="0.9"/><stop offset="100%" stop-color="{c}" stop-opacity="0.5"/></linearGradient></defs>
<circle cx="14" cy="14" r="11" fill="url(#g_chk)"/>
<circle cx="14" cy="14" r="11" fill="white" fill-opacity="0.12"/>
<ellipse cx="14" cy="8" rx="8" ry="5" fill="white" fill-opacity="0.08"/>
<polyline points="9,14 12.5,18 19,10" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
</svg>""",

    "pie": """<svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
<defs><linearGradient id="g_pie" x1="0" y1="0" x2="28" y2="28"><stop offset="0%" stop-color="{c}" stop-opacity="0.9"/><stop offset="100%" stop-color="{c}" stop-opacity="0.5"/></linearGradient></defs>
<circle cx="14" cy="14" r="11" fill="url(#g_pie)"/>
<circle cx="14" cy="14" r="11" fill="white" fill-opacity="0.12"/>
<ellipse cx="14" cy="8" rx="8" ry="5" fill="white" fill-opacity="0.08"/>
<path d="M14 4v10h10A10 10 0 0 0 14 4z" fill="white" fill-opacity="0.3"/>
<circle cx="14" cy="14" r="7" stroke="white" stroke-opacity="0.4" stroke-width="1"/>
</svg>""",

    "bolt": """<svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
<defs><linearGradient id="g_bolt" x1="0" y1="0" x2="28" y2="28"><stop offset="0%" stop-color="{c}" stop-opacity="0.9"/><stop offset="100%" stop-color="{c}" stop-opacity="0.5"/></linearGradient></defs>
<rect x="3" y="3" width="22" height="22" rx="5" fill="url(#g_bolt)"/>
<rect x="3" y="3" width="22" height="22" rx="5" fill="white" fill-opacity="0.12"/>
<rect x="4" y="4" width="20" height="8" rx="3" fill="white" fill-opacity="0.07"/>
<path d="M15.5 4L9 15h5l-1.5 9L19 13h-5l1.5-9z" fill="white" fill-opacity="0.9"/>
</svg>""",

    "calendar": """<svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
<defs><linearGradient id="g_cal" x1="0" y1="0" x2="28" y2="28"><stop offset="0%" stop-color="{c}" stop-opacity="0.9"/><stop offset="100%" stop-color="{c}" stop-opacity="0.5"/></linearGradient></defs>
<rect x="3" y="5" width="22" height="20" rx="3" fill="url(#g_cal)"/>
<rect x="3" y="5" width="22" height="20" rx="3" fill="white" fill-opacity="0.12"/>
<rect x="3" y="5" width="22" height="6" rx="3" fill="white" fill-opacity="0.15"/>
<path d="M9 3v4M19 3v4" stroke="white" stroke-width="2" stroke-linecap="round"/>
<circle cx="10" cy="17" r="1.5" fill="white"/><circle cx="14" cy="17" r="1.5" fill="white"/><circle cx="18" cy="17" r="1.5" fill="white"/>
</svg>""",

    "lab": """<svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
<defs><linearGradient id="g_lab" x1="0" y1="0" x2="28" y2="28"><stop offset="0%" stop-color="{c}" stop-opacity="0.9"/><stop offset="100%" stop-color="{c}" stop-opacity="0.5"/></linearGradient></defs>
<rect x="3" y="3" width="22" height="22" rx="5" fill="url(#g_lab)"/>
<rect x="3" y="3" width="22" height="22" rx="5" fill="white" fill-opacity="0.12"/>
<rect x="4" y="4" width="20" height="8" rx="3" fill="white" fill-opacity="0.07"/>
<path d="M11 5v8l-4 8h14l-4-8V5" stroke="white" stroke-width="1.5" fill="white" fill-opacity="0.1"/>
<path d="M10 5h8" stroke="white" stroke-width="2" stroke-linecap="round"/>
<circle cx="12" cy="19" r="1" fill="white"/><circle cx="16" cy="17" r="1.5" fill="white" fill-opacity="0.7"/>
</svg>""",

    "cart": """<svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
<defs><linearGradient id="g_cart" x1="0" y1="0" x2="28" y2="28"><stop offset="0%" stop-color="{c}" stop-opacity="0.9"/><stop offset="100%" stop-color="{c}" stop-opacity="0.5"/></linearGradient></defs>
<rect x="3" y="3" width="22" height="22" rx="5" fill="url(#g_cart)"/>
<rect x="3" y="3" width="22" height="22" rx="5" fill="white" fill-opacity="0.12"/>
<rect x="4" y="4" width="20" height="8" rx="3" fill="white" fill-opacity="0.07"/>
<path d="M6 7h2l3 11h8l3-8H9" stroke="white" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
<circle cx="11.5" cy="21.5" r="1.5" fill="white"/><circle cx="18.5" cy="21.5" r="1.5" fill="white"/>
</svg>""",
}

# 각 아이콘 이름 → 유니크 gradient id 충돌 방지용 카운터
_icon_counter = 0


def liquid_icon(name, color, size=28):
    """Liquid Glass SVG 아이콘 생성. 색상을 주입."""
    global _icon_counter
    _icon_counter += 1
    svg = LIQUID_ICONS.get(name, LIQUID_ICONS["package"])
    # gradient id 충돌 방지: 각 호출마다 고유 suffix 부여
    svg = svg.replace("{c}", color)
    # id 유니크화
    import re
    def _unique_id(m):
        global _icon_counter
        return f'id="{m.group(1)}_{_icon_counter}"'
    def _unique_ref(m):
        global _icon_counter
        return f'url(#{m.group(1)}_{_icon_counter})'
    svg_unique = re.sub(r'id="([^"]+)"', _unique_id, svg)
    svg_unique = re.sub(r'url\(#([^)]+)\)', _unique_ref, svg_unique)
    if size != 28:
        svg_unique = svg_unique.replace('width="28"', f'width="{size}"', 1)
        svg_unique = svg_unique.replace('height="28"', f'height="{size}"', 1)
    return svg_unique


# ── KPI / 사이드바 아이콘 매핑 ─────────────────────────────
# 페이지별 사용할 아이콘 이름 + 색상 프리셋
ICON_MAP = {
    # Dashboard KPI
    "total_sku": ("package", "accent_green"),
    "out_of_stock": ("alert", "accent_red"),
    "waste_risk": ("warning", "accent_orange"),
    "eoq_value": ("dollar", "accent_green"),
    # Waste Risk
    "risk_sku": ("alert", "accent_red"),
    "safe_sku": ("check", "accent_green"),
    "risk_rate": ("pie", "accent_orange"),
    "risk_value": ("dollar", "accent_purple"),
    # Inventory Status
    "accuracy": ("target", "accent_green"),
    "class_count": ("tag", "accent_purple"),
    "misclass": ("cross", "accent_red"),
    # Sales Prediction
    "r2": ("target", "accent_green"),
    "rmse": ("ruler", "accent_blue"),
    "mae": ("ruler", "accent_orange"),
    "avg_sales": ("chart_up", "accent_purple"),
    # Reorder Strategy
    "avg_doi": ("calendar", "accent_blue"),
    "urgency": ("bolt", "accent_orange"),
    "urgent_sku": ("alert", "accent_red"),
    "n_clusters": ("lab", "accent_purple"),
    # Data Explorer
    "filter_count": ("search", "accent_blue"),
    "all_sku": ("package", "accent_green"),
    "sales_avg": ("chart_up", "accent_orange"),
    "inv_value": ("dollar", "accent_purple"),
    # WMS 시뮬레이터 — 제품 개요
    "wms_cat": ("tag", "accent_blue"),
    "wms_abc": ("target", "accent_orange"),
    "wms_qoh": ("package", "accent_green"),
    "wms_ads": ("chart_up", "accent_purple"),
    "wms_lt": ("calendar", "accent_red"),
    # WMS 시뮬레이터 — 핵심 지표
    "wms_eoq": ("cart", "accent_blue"),
    "wms_rop": ("bolt", "accent_orange"),
    "wms_ss": ("alert", "accent_red"),
    "wms_cov": ("calendar", "accent_green"),
    # WMS 시뮬레이터 — 시뮬레이션 결과
    "sim_cov": ("calendar", "accent_green"),
    "sim_ord": ("cart", "accent_red"),
    "sim_cost": ("dollar", "accent_blue"),
    "sim_so": ("warning", "accent_orange"),
    # Phase A Optuna
    "cv_base": ("target", "accent_blue"),
    "cv_opt": ("target", "accent_green"),
    "cv_imp": ("chart_up", "accent_orange"),
    "std_imp": ("check", "accent_purple"),
    # Sidebar nav
    "nav_home": ("total_sku", "accent_green"),
    "nav_dashboard": ("chart_up", "accent_green"),
    "nav_explorer": ("search", "accent_blue"),
    "nav_waste": ("warning", "accent_orange"),
    "nav_status": ("package", "accent_purple"),
    "nav_sales": ("chart_up", "accent_blue"),
    "nav_reorder": ("cart", "accent_cyan"),
}


# ── 헬퍼 ──────────────────────────────────────────────────
def _hex_to_rgba(hex_color, alpha=0.12):
    """hex 색상을 rgba로 변환"""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def get_icon_svg(key, size=28):
    """ICON_MAP 키로 완성된 SVG 문자열 반환"""
    name, color_key = ICON_MAP.get(key, ("package", "accent_green"))
    color = COLORS[color_key]
    return liquid_icon(name, color, size)


# ── KPI 카드 HTML (Liquid Glass 아이콘 포함) ───────────────
def kpi_card(title, value, icon_key, color, delta=None, tooltip=None):
    """v2 Liquid Glass KPI 카드.
    icon_key: ICON_MAP 키(str) 또는 기존 이모지(str, 길이<=2)
    tooltip: 마우스 오버 시 표시할 설명 텍스트
    """
    delta_html = ""
    if delta is not None:
        try:
            val = float(str(delta).replace("%", "").replace(",", "").replace("+", ""))
            delta_color = "#4CAF50" if val >= 0 else "#F44336"
        except ValueError:
            delta_color = "#6c757d"
        delta_html = f'<span style="font-size:12px;color:{delta_color};margin-left:8px;">{delta}</span>'

    # 아이콘: ICON_MAP 키면 SVG, 아니면 기존 이모지
    if icon_key in ICON_MAP:
        icon_svg = get_icon_svg(icon_key, size=32)
        icon_cell = f'<div style="width:48px;height:48px;background:{_hex_to_rgba(color, 0.08)};border-radius:14px;text-align:center;line-height:48px;padding-top:8px;">{icon_svg}</div>'
    else:
        icon_bg = _hex_to_rgba(color, 0.12)
        icon_cell = f'<div style="width:48px;height:48px;background:{icon_bg};border-radius:14px;text-align:center;line-height:48px;font-size:24px;">{icon_key}</div>'

    tooltip_attr = f' title="{tooltip}"' if tooltip else ""
    tooltip_icon = ' <span style="font-size:10px;color:#adb5bd;cursor:help;">&#9432;</span>' if tooltip else ""
    return f"""<div style="background:white;border-radius:14px;padding:18px 20px;box-shadow:0 2px 12px rgba(0,0,0,0.07);border-left:4px solid {color};cursor:default;"{tooltip_attr}>
<table style="border:none;border-collapse:collapse;"><tr>
<td style="border:none;vertical-align:middle;padding-right:14px;">
{icon_cell}
</td>
<td style="border:none;vertical-align:middle;">
<div style="font-size:11px;color:#6c757d;text-transform:uppercase;letter-spacing:0.5px;font-weight:600;">{title}{tooltip_icon}</div>
<div style="font-size:26px;font-weight:700;color:#1a1a2e;line-height:1.3;">{value}{delta_html}</div>
</td>
</tr></table>
</div>"""


# ── 섹션 헤더 ──────────────────────────────────────────────
def section_header(title, subtitle=None):
    sub_html = f'<span style="font-size:13px;color:#6c757d;font-weight:400;margin-left:10px;">{subtitle}</span>' if subtitle else ""
    return f"""
    <div style="margin:20px 0 12px 0;">
        <span style="font-size:18px;font-weight:700;color:#1a1a2e;">{title}</span>
        {sub_html}
    </div>
    """


# ── 사이드바 네비 아이콘 HTML 생성 ─────────────────────────
def sidebar_nav_item(icon_key, label):
    """사이드바용 아이콘+라벨 HTML"""
    svg = get_icon_svg(icon_key, size=20)
    return f'{svg} **{label}**'


def sidebar_nav_html(current_page=""):
    """사이드바 네비게이션 전체 HTML — 클릭 시 페이지 이동, 현재 페이지 하이라이트"""
    items = [
        ("nav_home", "홈", "/"),
        ("nav_dashboard", "대시보드 개요", "/Dashboard"),
        ("nav_explorer", "데이터 탐색", "/Data_Explorer"),
        ("nav_status", "재고 상태 분류", "/Inventory_Status"),
        ("nav_sales", "판매량 예측", "/Sales_Prediction"),
        ("nav_waste", "폐기 위험 탐지", "/Waste_Risk"),
        ("nav_reorder", "발주 전략", "/Reorder_Strategy"),
    ]
    rows = ""
    for key, label, href in items:
        svg = get_icon_svg(key, size=18)
        is_active = (href == current_page)
        if is_active:
            style = (
                "display:block;padding:8px 10px;font-size:13px;color:#ffffff;"
                "text-decoration:none;border-radius:6px;"
                "background:rgba(76,175,80,0.25);border-left:3px solid #4CAF50;"
                "font-weight:700;"
            )
            hover_bg = "rgba(76,175,80,0.25)"
        else:
            style = (
                "display:block;padding:8px 10px;font-size:13px;color:#c0c8d8;"
                "text-decoration:none;border-radius:6px;transition:background 0.2s;"
            )
            hover_bg = "rgba(255,255,255,0.08)"
        rows += (
            f'<a href="{href}" target="_self" '
            f'style="{style}"'
            f' onmouseover="this.style.background=\'{hover_bg}\'"'
            f' onmouseout="this.style.background=\'{"rgba(76,175,80,0.25)" if is_active else "transparent"}\'"'
            f'>{svg} &nbsp;{label}</a>\n'
        )
    return f'<div style="margin-top:4px;">{rows}</div>'


def render_common_sidebar(st_mod, current_page=""):
    """모든 페이지에서 공통으로 사용하는 사이드바 렌더링.
    st_mod: streamlit 모듈 참조
    current_page: 현재 페이지 경로 (예: "/Dashboard")"""
    logo_svg = get_icon_svg("total_sku", size=24)
    st_mod.sidebar.markdown(
        f"""
        <div style="text-align:center;padding:10px 0 5px;">
            <div style="font-size:22px;font-weight:800;color:#ffffff;">{logo_svg} E-Grocery WMS</div>
            <div style="font-size:11px;color:#8e9aaf;margin-top:2px;">재고 최적화 시스템</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st_mod.sidebar.divider()
    st_mod.sidebar.markdown(
        """
        <div style="font-size:11px;color:#8e9aaf;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;font-weight:600;">
            목차
        </div>
        """,
        unsafe_allow_html=True,
    )
    st_mod.sidebar.markdown(sidebar_nav_html(current_page), unsafe_allow_html=True)
    st_mod.sidebar.divider()
    st_mod.sidebar.markdown(
        """
        <div style="font-size:11px;color:#8e9aaf;">
            <b>데이터:</b> Kaggle E-Grocery<br>
            <b>SKU 수:</b> 1,000 / 37개 컬럼<br>
            <b>모델:</b> 4개 ML 서브토픽
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── 미니 목차 (페이지 내 앵커 내비게이션) ──────────────────
def section_anchor(section_id):
    """섹션 앵커 마커 — 각 섹션 상단에 배치"""
    return f'<div id="{section_id}" style="scroll-margin-top:60px;"></div>'


def render_mini_toc(sections):
    """플로팅 리모컨 미니 목차 HTML 생성.
    sections: [(section_id, label, icon), ...]  icon은 이모지 문자열
    화면 우측에 고정 — 투명 배경으로 뒤 콘텐츠가 비침.
    <details>/<summary> 네이티브 HTML로 접기/펼치기 구현 (JS 불필요).
    """
    items = ""
    for idx, (sid, label, icon) in enumerate(sections):
        items += (
            f'<a href="#{sid}" class="floating-toc-item">'
            f'{icon} {label}</a>'
        )
    return (
        f'<div class="floating-toc-wrapper">'
        f'  <details class="toc-details" open>'
        f'    <summary class="toc-toggle-btn" title="목차 접기/펼치기">☰</summary>'
        f'    <div class="toc-panel">'
        f'      <div class="toc-panel-header">NAVIGATE</div>'
        f'      {items}'
        f'    </div>'
        f'  </details>'
        f'</div>'
    )


# ── 커스텀 탭 (session_state 기반) ──────────────────────────
def render_custom_tabs(st_mod, tab_names, state_key):
    """session_state 기반 탭 버튼 렌더링.
    Returns: 현재 선택된 탭 인덱스 (int)
    """
    if state_key not in st_mod.session_state:
        st_mod.session_state[state_key] = 0

    cur = st_mod.session_state[state_key]
    cols = st_mod.columns(len(tab_names))
    for i, name in enumerate(tab_names):
        with cols[i]:
            if st_mod.button(
                name, key=f"{state_key}_tab_{i}",
                use_container_width=True,
                type="primary" if i == cur else "secondary",
            ):
                st_mod.session_state[state_key] = i
                st_mod.rerun()
    return cur


# ── 버전 상수 ─────────────────────────────────────────────
APP_VERSION = "v3.5"


def footer_html():
    """공통 푸터 HTML"""
    return f'<div class="footer">E-Grocery WMS {APP_VERSION} | ML 기반 재고 최적화 | Phase8_mini</div>'


# ── 글로벌 CSS ─────────────────────────────────────────────
GLOBAL_CSS = """
<style>
    /* 커스텀 한글 폰트 */
    @font-face {
        font-family: 'A2G';
        src: url('./app/static/A2G-3Light.ttf') format('truetype');
        font-weight: 300;
        font-style: normal;
    }
    html, body, [class*="css"], .stMarkdown, .stText,
    .stSelectbox, .stMultiSelect, .stSlider, .stRadio,
    [data-testid="stMetric"], [data-baseweb="tab"],
    .stDataFrame, input, select, textarea, button,
    .page-title, .page-subtitle, .footer {
        font-family: 'A2G', 'Noto Sans KR', 'Apple SD Gothic Neo', sans-serif !important;
    }

    /* 사이드바 다크 테마 */
    section[data-testid="stSidebar"] {
        background-color: #1a1a2e !important;
    }
    section[data-testid="stSidebar"] * {
        color: #e0e0e0 !important;
    }
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stMultiSelect label,
    section[data-testid="stSidebar"] .stSlider label,
    section[data-testid="stSidebar"] .stRadio label {
        color: #b0b0b0 !important;
        font-size: 13px !important;
    }
    section[data-testid="stSidebar"] hr {
        border-color: #2a2a4e !important;
    }
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #ffffff !important;
    }
    /* 사이드바 폼 입력 요소: 밝은 배경 + 어두운 텍스트 */
    section[data-testid="stSidebar"] [data-baseweb="select"] *,
    section[data-testid="stSidebar"] [data-baseweb="input"] *,
    section[data-testid="stSidebar"] .stTextInput input {
        color: #1a1a2e !important;
    }
    section[data-testid="stSidebar"] [data-baseweb="select"] > div {
        background-color: #f0f2f6 !important;
    }
    section[data-testid="stSidebar"] .stTextInput input {
        background-color: #f0f2f6 !important;
        color: #1a1a2e !important;
    }

    /* 메인 영역 드롭다운/셀렉트박스 텍스트 가시성 */
    [data-baseweb="select"] * {
        color: #1a1a2e !important;
    }
    [data-baseweb="select"] > div {
        background-color: #ffffff !important;
        border: 1px solid #d0d5dd !important;
    }
    /* 드롭다운 팝오버(옵션 목록) */
    [data-baseweb="popover"] * {
        color: #1a1a2e !important;
    }
    [data-baseweb="popover"] [role="listbox"] {
        background-color: #ffffff !important;
    }
    [data-baseweb="popover"] [role="option"] {
        color: #1a1a2e !important;
        background-color: #ffffff !important;
    }
    [data-baseweb="popover"] [role="option"]:hover,
    [data-baseweb="popover"] [role="option"][aria-selected="true"] {
        background-color: #e8f5e9 !important;
    }
    /* 멀티셀렉트 태그 */
    [data-baseweb="tag"] {
        background-color: #e8f5e9 !important;
        color: #1a1a2e !important;
    }
    [data-baseweb="tag"] * {
        color: #1a1a2e !important;
    }

    /* 메인 영역 */
    .main .block-container {
        padding-top: 1.5rem !important;
        max-width: 1200px;
    }

    /* 탭 스타일 (기존 st.tabs 호환) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 8px 20px;
        font-weight: 600;
    }

    /* 커스텀 탭 버튼 — 작은 글씨, 컴팩트 */
    .custom-tab-row .stButton > button {
        font-size: 11.5px !important;
        padding: 5px 8px !important;
        min-height: 32px !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }

    /* 데이터프레임 */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
    }

    /* 메트릭 카드 */
    [data-testid="stMetric"] {
        background: white;
        border-radius: 10px;
        padding: 12px 16px;
        box-shadow: 0 1px 6px rgba(0,0,0,0.05);
    }

    /* 페이지 타이틀 */
    .page-title {
        font-size: 28px;
        font-weight: 800;
        color: #1a1a2e;
        margin-bottom: 4px;
        line-height: 1.2;
    }
    .page-subtitle {
        font-size: 14px;
        color: #6c757d;
        margin-bottom: 16px;
    }

    /* Baseline/Enhanced 토글 */
    .mode-toggle {
        display: inline-flex;
        gap: 0;
        margin-bottom: 16px;
        border-radius: 8px;
        overflow: hidden;
        border: 2px solid #4CAF50;
    }
    .mode-btn {
        padding: 6px 20px;
        font-size: 13px;
        font-weight: 600;
        cursor: pointer;
        border: none;
    }
    .mode-btn.active {
        background: #4CAF50;
        color: white;
    }
    .mode-btn.inactive {
        background: white;
        color: #4CAF50;
    }

    /* 모드 토글 & 일반 버튼 텍스트 최적화 */
    .stButton > button {
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        font-size: 13px !important;
        padding: 6px 12px !important;
        min-height: 38px !important;
    }

    /* Streamlit 기본 페이지 네비게이션 숨김 (커스텀 목차로 대체) */
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] {
        display: none !important;
    }

    /* ── 플로팅 리모컨 TOC ─────────────────────── */
    .floating-toc-wrapper {
        position: fixed;
        right: 18px;
        top: 50%;
        transform: translateY(-50%);
        z-index: 9999;
    }

    /* details 기본 마커 제거 */
    .toc-details {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
    }
    .toc-details > summary {
        list-style: none;
    }
    .toc-details > summary::-webkit-details-marker {
        display: none;
    }

    /* 토글 버튼 (☰) */
    .toc-toggle-btn {
        width: 34px;
        height: 34px;
        border-radius: 50%;
        background: rgba(26, 26, 46, 0.06);
        border: 1px solid rgba(0, 0, 0, 0.08);
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        font-size: 15px;
        color: rgba(26, 26, 46, 0.5);
        transition: all 0.25s ease;
        margin-bottom: 6px;
        user-select: none;
    }
    .toc-toggle-btn:hover {
        background: rgba(76, 175, 80, 0.12);
        color: #2e7d32;
        border-color: rgba(76, 175, 80, 0.3);
    }

    /* 패널 — 투명 배경 */
    .toc-panel {
        background: transparent;
        border: none;
        border-radius: 12px;
        width: 155px;
        display: flex;
        flex-direction: column;
        padding: 4px 0;
    }

    /* 패널 헤더 */
    .toc-panel-header {
        font-size: 9px;
        color: rgba(100, 100, 120, 0.5);
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        padding: 0 8px 5px;
        margin-bottom: 2px;
    }

    /* 각 링크 아이템 — 반투명 pill */
    .floating-toc-item {
        display: block;
        padding: 4px 10px;
        margin: 2px 0;
        font-size: 11px;
        font-weight: 500;
        color: rgba(26, 26, 46, 0.55);
        text-decoration: none;
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.45);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        border: 1px solid rgba(0, 0, 0, 0.04);
        transition: all 0.2s ease;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        line-height: 1.6;
    }
    .floating-toc-item:hover {
        background: rgba(76, 175, 80, 0.13);
        color: #2e7d32;
        border-color: rgba(76, 175, 80, 0.25);
        padding-left: 14px;
    }

    /* 푸터 */
    .footer {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background: #1a1a2e;
        color: #b0b0b0;
        text-align: center;
        padding: 8px;
        font-size: 12px;
        z-index: 999;
    }
</style>
"""

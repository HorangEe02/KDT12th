#!/usr/bin/env python3
"""Markdown report to PDF converter for MagneticTile Segmentation results."""

import re
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib.colors import HexColor, black, white, Color
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle,
    PageBreak, KeepTogether, HRFlowable, Flowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from PIL import Image as PILImage

# ── Paths ──
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PDF = os.path.join(BASE_DIR, "SubTopic_B_MagneticTile_Results_Report.pdf")

# ── Register Korean fonts ──
pdfmetrics.registerFont(TTFont("NanumR", "/Users/yeong/Library/Fonts/NanumSquare_acR.ttf"))
pdfmetrics.registerFont(TTFont("NanumB", "/Users/yeong/Library/Fonts/NanumSquare_acB.ttf"))
pdfmetrics.registerFont(TTFont("NanumEB", "/Users/yeong/Library/Fonts/NanumSquare_acEB.ttf"))
pdfmetrics.registerFont(TTFont("NanumL", "/Users/yeong/Library/Fonts/NanumSquare_acL.ttf"))
pdfmetrics.registerFont(TTFont("D2Coding", "/Users/yeong/Library/Fonts/D2Coding.ttc", subfontIndex=0))

# ── Colors ──
PRIMARY = HexColor("#1a237e")      # Deep blue
ACCENT = HexColor("#0d47a1")       # Blue
LIGHT_BG = HexColor("#e8eaf6")     # Light blue-gray
CODE_BG = HexColor("#f5f5f5")      # Light gray
TABLE_HEADER = HexColor("#283593") # Dark blue
TABLE_ALT = HexColor("#e8eaf6")    # Alternating row
BORDER = HexColor("#bdbdbd")
STAR_COLOR = HexColor("#f9a825")   # Gold for star
QUOTE_BAR = HexColor("#1565c0")    # Blue for blockquote bar
QUOTE_BG = HexColor("#e3f2fd")     # Light blue for blockquote

# ── Page settings ──
PAGE_W, PAGE_H = A4
MARGIN_L = 20 * mm
MARGIN_R = 20 * mm
MARGIN_T = 22 * mm
MARGIN_B = 22 * mm
CONTENT_W = PAGE_W - MARGIN_L - MARGIN_R

# ── Styles ──
def make_styles():
    s = {}
    s['title'] = ParagraphStyle(
        'Title', fontName='NanumEB', fontSize=22, leading=30,
        textColor=PRIMARY, alignment=TA_CENTER, spaceAfter=4*mm
    )
    s['subtitle'] = ParagraphStyle(
        'Subtitle', fontName='NanumR', fontSize=10, leading=14,
        textColor=HexColor("#616161"), alignment=TA_CENTER, spaceAfter=2*mm
    )
    s['h1'] = ParagraphStyle(
        'H1', fontName='NanumEB', fontSize=16, leading=22,
        textColor=PRIMARY, spaceBefore=10*mm, spaceAfter=4*mm,
        borderWidth=0, borderPadding=0,
    )
    s['h2'] = ParagraphStyle(
        'H2', fontName='NanumB', fontSize=13, leading=18,
        textColor=ACCENT, spaceBefore=7*mm, spaceAfter=3*mm,
    )
    s['h3'] = ParagraphStyle(
        'H3', fontName='NanumB', fontSize=11, leading=16,
        textColor=HexColor("#1565c0"), spaceBefore=5*mm, spaceAfter=2*mm,
    )
    s['body'] = ParagraphStyle(
        'Body', fontName='NanumR', fontSize=9.5, leading=15,
        textColor=black, alignment=TA_JUSTIFY, spaceAfter=2*mm,
    )
    s['body_bold'] = ParagraphStyle(
        'BodyBold', fontName='NanumB', fontSize=9.5, leading=15,
        textColor=black, spaceAfter=2*mm,
    )
    s['code'] = ParagraphStyle(
        'Code', fontName='D2Coding', fontSize=8, leading=12,
        textColor=HexColor("#263238"), backColor=CODE_BG,
        borderWidth=0.5, borderColor=BORDER, borderPadding=6,
        spaceAfter=3*mm, leftIndent=4*mm, rightIndent=4*mm,
    )
    s['quote'] = ParagraphStyle(
        'Quote', fontName='NanumR', fontSize=9, leading=14,
        textColor=HexColor("#37474f"), leftIndent=8*mm,
        borderWidth=0, spaceAfter=3*mm,
        backColor=QUOTE_BG, borderPadding=(6, 6, 6, 10),
    )
    s['toc'] = ParagraphStyle(
        'TOC', fontName='NanumR', fontSize=10, leading=16,
        textColor=ACCENT, leftIndent=5*mm, spaceAfter=1*mm,
    )
    s['table_header'] = ParagraphStyle(
        'TableHeader', fontName='NanumB', fontSize=8.5, leading=12,
        textColor=white, alignment=TA_CENTER,
    )
    s['table_cell'] = ParagraphStyle(
        'TableCell', fontName='NanumR', fontSize=8.5, leading=12,
        textColor=black, alignment=TA_CENTER,
    )
    s['table_cell_left'] = ParagraphStyle(
        'TableCellLeft', fontName='NanumR', fontSize=8.5, leading=12,
        textColor=black, alignment=TA_LEFT,
    )
    s['footer'] = ParagraphStyle(
        'Footer', fontName='NanumL', fontSize=7.5, leading=10,
        textColor=HexColor("#9e9e9e"), alignment=TA_CENTER,
    )
    return s

STYLES = make_styles()


# ── Custom Flowables ──
class ColoredHR(Flowable):
    def __init__(self, width, color=PRIMARY, thickness=1):
        Flowable.__init__(self)
        self.width = width
        self.color = color
        self.thickness = thickness
        self.height = thickness + 2*mm

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, self.thickness/2, self.width, self.thickness/2)


class QuoteBlock(Flowable):
    """A blockquote with left colored bar."""
    def __init__(self, text, width, style):
        Flowable.__init__(self)
        self.text = text
        self._width = width
        self.style = style
        # pre-calculate height
        p = Paragraph(text, style)
        pw, ph = p.wrap(width - 12*mm, 10000)
        self.para_height = ph
        self.height = ph + 6*mm

    def draw(self):
        # Background
        self.canv.setFillColor(QUOTE_BG)
        self.canv.roundRect(0, 0, self._width, self.height, 2, fill=1, stroke=0)
        # Left bar
        self.canv.setFillColor(QUOTE_BAR)
        self.canv.rect(0, 0, 3, self.height, fill=1, stroke=0)
        # Text
        p = Paragraph(self.text, self.style)
        p.wrap(self._width - 12*mm, 10000)
        p.drawOn(self.canv, 8*mm, 3*mm)


# ── Helper functions ──
def inline_format(text):
    """Convert markdown inline formatting to reportlab XML tags."""
    # Bold + italic
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<font name="NanumEB"><i>\1</i></font>', text)
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<font name="NanumB">\1</font>', text)
    # Italic
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    # Inline code
    text = re.sub(r'`(.+?)`', r'<font name="D2Coding" size="8" color="#c62828">\1</font>', text)
    # Links (strip to text only)
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
    # Star emoji
    text = text.replace('★', '<font color="#f9a825">★</font>')
    text = text.replace('🏆', '<font color="#f9a825">🏆</font>')
    return text


def make_table(headers, rows, col_widths=None):
    """Create a styled table."""
    style = STYLES
    # Build header row
    header_cells = [Paragraph(inline_format(h), style['table_header']) for h in headers]
    # Build data rows
    data_rows = []
    for row in rows:
        cells = []
        for i, cell in enumerate(row):
            cell_text = inline_format(cell.strip()) if cell else ""
            if i == 0 or len(headers) <= 3:
                cells.append(Paragraph(cell_text, style['table_cell_left']))
            else:
                cells.append(Paragraph(cell_text, style['table_cell']))
        data_rows.append(cells)

    table_data = [header_cells] + data_rows
    n_cols = len(headers)

    if col_widths is None:
        col_widths = [CONTENT_W / n_cols] * n_cols

    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), TABLE_HEADER),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'NanumB'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]
    # Alternate row colors
    for i in range(1, len(table_data)):
        if i % 2 == 0:
            table_style.append(('BACKGROUND', (0, i), (-1, i), TABLE_ALT))
    t.setStyle(TableStyle(table_style))
    return t


def add_image(story, filename, max_width=CONTENT_W, max_height=160*mm):
    """Add an image, scaling to fit."""
    img_path = os.path.join(BASE_DIR, filename)
    if not os.path.exists(img_path):
        story.append(Paragraph(f"[이미지 없음: {filename}]", STYLES['body']))
        return
    pil_img = PILImage.open(img_path)
    img_w, img_h = pil_img.size
    ratio = min(max_width / img_w, max_height / img_h)
    w, h = img_w * ratio, img_h * ratio
    img = Image(img_path, width=w, height=h)
    story.append(img)
    story.append(Spacer(1, 3*mm))


def parse_table_block(lines):
    """Parse markdown table lines into headers and rows."""
    if len(lines) < 2:
        return None, None
    headers = [c.strip() for c in lines[0].strip('|').split('|')]
    rows = []
    for line in lines[2:]:  # skip separator
        cols = [c.strip() for c in line.strip('|').split('|')]
        rows.append(cols)
    return headers, rows


# ── Page number footer ──
def add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont('NanumL', 8)
    canvas.setFillColor(HexColor("#9e9e9e"))
    page_num = canvas.getPageNumber()
    text = f"— {page_num} —"
    canvas.drawCentredString(PAGE_W / 2, 12 * mm, text)
    # Header line
    canvas.setStrokeColor(LIGHT_BG)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN_L, PAGE_H - MARGIN_T + 5*mm, PAGE_W - MARGIN_R, PAGE_H - MARGIN_T + 5*mm)
    canvas.restoreState()


def first_page(canvas, doc):
    add_page_number(canvas, doc)


# ── Build the PDF ──
def build_pdf():
    doc = SimpleDocTemplate(
        OUTPUT_PDF, pagesize=A4,
        leftMargin=MARGIN_L, rightMargin=MARGIN_R,
        topMargin=MARGIN_T, bottomMargin=MARGIN_B,
        title="자석 타일 표면 결함 세그먼테이션 결과 보고서",
        author="K-Digital Training 딥러닝 12기",
    )

    story = []
    st = STYLES

    # ━━━━━━━━━ COVER / TITLE ━━━━━━━━━
    story.append(Spacer(1, 15*mm))
    story.append(Paragraph("소주제 B", st['subtitle']))
    story.append(Paragraph("자석 타일 표면 결함<br/>세그먼테이션 결과 보고서", st['title']))
    story.append(Spacer(1, 4*mm))
    story.append(ColoredHR(CONTENT_W, PRIMARY, 2))
    story.append(Spacer(1, 4*mm))

    # Metadata table
    meta = [
        ["프로젝트", "K-Digital Training 딥러닝 12기 미니프로젝트"],
        ["작성일", "2026-04-01"],
        ["모델", "Vanilla U-Net / Attention U-Net / ResNet34 U-Net"],
        ["데이터셋", "Magnetic Tile Surface Defects (392쌍, 5종 결함)"],
    ]
    meta_cells = [[Paragraph(f'<font name="NanumB" color="#1a237e">{r[0]}</font>', st['body']),
                    Paragraph(r[1], st['body'])] for r in meta]
    mt = Table(meta_cells, colWidths=[35*mm, CONTENT_W - 35*mm])
    mt.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LINEBELOW', (0,0), (-1,-1), 0.3, BORDER),
    ]))
    story.append(mt)
    story.append(Spacer(1, 8*mm))

    # ━━━━━━━━━ TOC ━━━━━━━━━
    story.append(Paragraph("목차", st['h1']))
    toc_items = [
        "1. 프로젝트 개요",
        "2. 핵심 용어 해설 (비전공자용)",
        "3. 데이터셋 소개",
        "4. 왜 이 방법들을 선택했는가?",
        "5. 데이터 시각화 분석",
        "6. 모델별 학습 과정 분석",
        "7. TTA 예측 결과 시각화",
        "8. 결함 유형별 성능 분석",
        "9. 3모델 최종 비교",
        "10. 결과 해석 및 핵심 인사이트",
        "11. 향후 개선 방향",
    ]
    for item in toc_items:
        story.append(Paragraph(item, st['toc']))
    story.append(PageBreak())

    # ━━━━━━━━━ SECTION 1: 프로젝트 개요 ━━━━━━━━━
    story.append(Paragraph("1. 프로젝트 개요", st['h1']))
    story.append(ColoredHR(CONTENT_W, ACCENT, 0.5))

    story.append(Paragraph("무엇을 해결하려 했는가?", st['h2']))
    story.append(Paragraph(
        inline_format("자석 타일(Magnetic Tile)은 모터, 발전기, 스피커 등 다양한 전자·전기 제품에 사용되는 핵심 부품입니다. "
        "제조 과정에서 발생하는 **표면 결함**은 제품 성능 저하 및 파손으로 이어질 수 있어, 품질 검사가 매우 중요합니다."),
        st['body']
    ))
    story.append(Paragraph(
        inline_format("기존에는 사람이 육안으로 검사했지만, 이 프로젝트는 **딥러닝 모델이 자동으로 결함 위치를 찾아내는 것**을 목표로 합니다."),
        st['body']
    ))

    story.append(Paragraph("이 프로젝트가 특별히 어려운 이유", st['h2']))
    story.append(Paragraph(
        inline_format("이 데이터셋은 균열 세그먼테이션(11,298장)과 달리 **단 392장**의 이미지만 존재합니다. "
        "이는 딥러닝에서 매우 적은 데이터량으로, 마치 단어를 10개만 보고 언어를 배우는 것과 같은 도전적인 상황입니다. "
        "또한 결함 종류가 5가지(Blowhole, Break, Crack, Fray, Uneven)로 다양하여 각각의 패턴을 학습해야 합니다."),
        st['body']
    ))

    # ━━━━━━━━━ SECTION 2: 핵심 용어 해설 ━━━━━━━━━
    story.append(Paragraph("2. 핵심 용어 해설 (비전공자용)", st['h1']))
    story.append(ColoredHR(CONTENT_W, ACCENT, 0.5))

    # 2-1 Segmentation
    story.append(Paragraph("2-1. 세그먼테이션(Segmentation)이란?", st['h2']))
    story.append(Paragraph(
        '<font name="D2Coding" size="8.5">분류(Classification)      → "이 타일에 결함이 있나요?"  → Yes/No<br/>'
        '세그먼테이션(Segmentation) → "결함이 정확히 어느 픽셀에 있나요?" → 픽셀별 Yes/No</font>',
        st['code']
    ))
    story.append(Paragraph(
        inline_format("세그먼테이션은 이미지의 모든 픽셀 하나하나에 \"결함이냐 아니냐\"를 판단하는 훨씬 어려운 작업입니다. "
        "결과물은 원본 이미지와 같은 크기의 흑백 마스크로, **흰색 = 결함**, **검정색 = 정상**으로 표현됩니다."),
        st['body']
    ))

    # 2-2 Dice Score
    story.append(Paragraph("2-2. Dice Score (다이스 점수)", st['h2']))
    story.append(Paragraph(
        '<font name="D2Coding" size="8.5">'
        '         2 x (예측한 결함 영역 ∩ 실제 결함 영역)<br/>'
        'Dice = ─────────────────────────────────────────<br/>'
        '         예측한 결함 영역 + 실제 결함 영역</font>',
        st['code']
    ))
    story.append(Paragraph(
        inline_format('**쉬운 비유**: 내가 동그라미를 그렸고, 정답도 동그라미라면 얼마나 겹치는지 비율.'),
        st['body']
    ))
    dice_h = ["Dice 값", "해석"]
    dice_r = [
        ["1.0", "완벽하게 일치"],
        ["0.7~0.9", "실용적으로 활용 가능한 수준"],
        ["0.5~0.7", "기본 탐지 가능, 개선 여지 있음"],
        ["0.1~0.5", "탐지는 하지만 정확도 낮음"],
        ["0.0~0.1", "결함을 거의 찾지 못함"],
    ]
    story.append(make_table(dice_h, dice_r, [30*mm, CONTENT_W - 30*mm]))
    story.append(Spacer(1, 3*mm))

    # 2-3 IoU
    story.append(Paragraph("2-3. IoU (Intersection over Union)", st['h2']))
    story.append(Paragraph(
        '<font name="D2Coding" size="8.5">'
        '        예측한 결함 ∩ 실제 결함 (겹치는 부분)<br/>'
        'IoU = ─────────────────────────────────────────<br/>'
        '        예측한 결함 ∪ 실제 결함 (합친 부분)</font>',
        st['code']
    ))
    story.append(Paragraph(
        inline_format('**쉬운 비유**: 두 동그라미를 겹쳤을 때 "겹친 부분 ÷ 전체 합친 부분". Dice보다 더 엄격한 기준으로, 항상 Dice보다 낮게 나옵니다.'),
        st['body']
    ))

    # 2-4 TTA
    story.append(Paragraph("2-4. TTA (Test-Time Augmentation, 테스트 시 데이터 증강)", st['h2']))
    story.append(Paragraph(
        inline_format('**학습 중 증강**: 학습할 때 이미지를 뒤집고, 회전하고, 밝기를 바꿔가며 다양하게 보여줌<br/>'
        '**TTA**: **테스트(예측) 할 때도** 같은 이미지를 여러 방향으로 변환하여 예측하고, 그 결과를 **평균**냄'),
        st['body']
    ))
    story.append(Paragraph(
        '<font name="D2Coding" size="8.5">'
        'TTA 4방향 앙상블:<br/>'
        '  원본         → 예측₁<br/>'
        '  수평 뒤집기  → 예측₂ (역변환)<br/>'
        '  수직 뒤집기  → 예측₃ (역변환)<br/>'
        '  양쪽 뒤집기  → 예측₄ (역변환)<br/>'
        '                  ─────────<br/>'
        '                   4개 평균 → 최종 예측</font>',
        st['code']
    ))
    story.append(Paragraph(
        inline_format('**효과**: 한 방향에서만 봤을 때의 오류를 여러 방향의 정보로 보정 → 더 안정적인 예측'),
        st['body']
    ))

    # 2-5 기본 Dice vs TTA Dice
    story.append(Paragraph("2-5. 기본 Dice vs TTA Dice 차이", st['h2']))
    t25_h = ["구분", "측정 방법", "특징"]
    t25_r = [
        ["**기본 Dice**", "학습 중 검증 데이터에서 1방향 예측으로 측정", "빠르지만 변동성 있음"],
        ["**TTA Dice**", "학습 완료 후 4방향 앙상블로 측정", "더 안정적, 실제 배포 성능에 가까움"],
    ]
    story.append(make_table(t25_h, t25_r, [30*mm, 60*mm, CONTENT_W - 90*mm]))
    story.append(Spacer(1, 2*mm))
    story.append(QuoteBlock(
        "TTA Dice가 기본 Dice보다 낮게 나오는 경우: 모델이 특정 방향에만 최적화되어 있어 다방향 평균 시 성능이 희석되는 경우. "
        "높게 나오는 경우: 앙상블 효과로 안정성이 향상된 경우.",
        CONTENT_W, st['body']
    ))

    story.append(PageBreak())

    # ━━━━━━━━━ SECTION 3: 데이터셋 소개 ━━━━━━━━━
    story.append(Paragraph("3. 데이터셋 소개", st['h1']))
    story.append(ColoredHR(CONTENT_W, ACCENT, 0.5))

    story.append(Paragraph("기본 정보", st['h2']))
    t3_h = ["항목", "내용"]
    t3_r = [
        ["데이터셋 이름", "Magnetic Tile Surface Defects"],
        ["총 유효 이미지-마스크 쌍", "**392쌍**"],
        ["입력 이미지 크기", "다양 → 224×224로 통일"],
        ["결함 종류", "**5종** (Blowhole, Break, Crack, Fray, Uneven)"],
        ["학습/검증 분할", "313쌍(80%) / 79쌍(20%)"],
    ]
    story.append(make_table(t3_h, t3_r, [45*mm, CONTENT_W - 45*mm]))
    story.append(Spacer(1, 3*mm))

    story.append(Paragraph("데이터 분할 및 클래스 불균형", st['h2']))
    story.append(Paragraph(
        '<font name="D2Coding" size="8.5">'
        '전체 392쌍<br/>'
        '├── 학습(Train)  313쌍 (80%) — 모델 학습용<br/>'
        '└── 검증(Val)    79쌍  (20%) — 성능 모니터링 및 최종 평가<br/><br/>'
        '결함 픽셀 비율: 전체 픽셀의 약 8.44% → 극심한 클래스 불균형!</font>',
        st['code']
    ))
    story.append(QuoteBlock(
        inline_format('**8.44%가 의미하는 것**: 이미지의 약 92%는 정상 픽셀, 8%만 결함 픽셀. '
        '"모두 정상"이라고 예측해도 92% 정확도가 나오므로 단순 정확도로는 평가할 수 없음.'),
        CONTENT_W, st['body']
    ))

    story.append(Paragraph("결함 종류별 분포", st['h2']))
    t3d_h = ["결함 유형", "한국어 의미", "샘플 수", "비율"]
    t3d_r = [
        ["**Blowhole**", "기포 구멍", "115쌍", "29.3%"],
        ["**Break**", "파손/균열", "85쌍", "21.7%"],
        ["**Uneven**", "표면 불균일", "103쌍", "26.3%"],
        ["**Crack**", "균열", "57쌍", "14.5%"],
        ["**Fray**", "올 풀림/마모", "32쌍", "8.2%"],
    ]
    story.append(make_table(t3d_h, t3d_r, [35*mm, 35*mm, 30*mm, CONTENT_W - 100*mm]))
    story.append(Spacer(1, 2*mm))
    story.append(QuoteBlock(
        inline_format('**핵심 어려움**: Fray(32쌍)와 Crack(57쌍)은 데이터가 매우 적어 학습이 어려움. Blowhole(115쌍)도 전체 392장 대비 매우 작은 규모.'),
        CONTENT_W, st['body']
    ))

    # ━━━━━━━━━ SECTION 4: 왜 이 방법들을 선택했는가? ━━━━━━━━━
    story.append(PageBreak())
    story.append(Paragraph("4. 왜 이 방법들을 선택했는가?", st['h1']))
    story.append(ColoredHR(CONTENT_W, ACCENT, 0.5))

    # 4-1
    story.append(Paragraph("4-1. U-Net — 세그먼테이션의 표준 아키텍처", st['h2']))
    story.append(Paragraph(
        '<font name="D2Coding" size="8.5">'
        '인코더 (압축 단계)          디코더 (복원 단계)<br/>'
        '256×256 이미지            256×256 예측 마스크<br/>'
        '   ↓ 점점 작아짐    ←→      ↑ 점점 커짐<br/>'
        '   (패턴 학습)     스킵연결   (위치 복원)</font>',
        st['code']
    ))
    story.append(Paragraph(
        inline_format('**스킵 연결(Skip Connection)의 역할**:<br/>'
        '• 인코더에서 압축하면서 잃어버린 **위치 정보**를 디코더에 직접 전달<br/>'
        '• 마치 큰 그림을 그릴 때 스케치(위치 정보)를 보면서 세부 묘사를 추가하는 것'),
        st['body']
    ))

    # 4-2
    story.append(Paragraph("4-2. Attention U-Net — 중요한 부분에만 집중", st['h2']))
    story.append(Paragraph(
        '<font name="D2Coding" size="8.5">'
        '일반 U-Net:     스킵 연결 → 모든 특징 그대로 전달<br/>'
        'Attention U-Net: 스킵 연결 → [Attention Gate] → 결함 있는 부분만 선택적 전달</font>',
        st['code']
    ))
    story.append(Paragraph(
        inline_format('**Attention Gate 동작 원리**:'),
        st['body']
    ))
    story.append(Paragraph(
        '<font name="D2Coding" size="8.5">'
        '디코더 정보(g)와 인코더 정보(x)를 비교<br/>'
        '       ↓<br/>'
        'α = sigmoid(W_g·g + W_x·x)   ← 0~1 사이의 중요도 점수<br/>'
        '       ↓<br/>'
        '출력 = α × x                  ← 중요한 부분만 통과</font>',
        st['code']
    ))
    story.append(Paragraph(
        inline_format('**왜 사용?**: 자석 타일 결함은 전체 이미지에서 **아주 작은 영역**만 차지. 어텐션을 통해 모델이 넓은 배경 대신 결함 부위에 집중하도록 유도.'),
        st['body']
    ))

    # 4-3
    story.append(Paragraph("4-3. ResNet34 U-Net — 사전학습의 힘 (전이학습)", st['h2']))
    story.append(Paragraph(
        '<font name="D2Coding" size="8.5">'
        'Vanilla U-Net   : 392장으로 처음부터 학습 (빈 종이에서 시작)<br/>'
        'ResNet34 U-Net  : ImageNet 128만 장으로 미리 공부한 후 392장으로 미세조정</font>',
        st['code']
    ))
    story.append(Paragraph(
        inline_format('**전이학습이 중요한 이유**:<br/>'
        '• 392장은 딥러닝이 "패턴을 익히기"에 매우 적은 양<br/>'
        '• ResNet34는 이미 **선, 곡선, 텍스처, 형태** 등 수천 가지 시각 패턴을 알고 있음<br/>'
        '• 이 지식을 결함 탐지에 재활용 → 적은 데이터로도 좋은 성능 기대'),
        st['body']
    ))

    # 4-4
    story.append(Paragraph("4-4. Focal Tversky Loss — 결함 탐지 특화 손실 함수", st['h2']))
    story.append(Paragraph(
        '<font name="D2Coding" size="8.5">'
        '기존 손실: 0.5 × BCE + 0.5 × Dice          ← Vanilla U-Net<br/>'
        '개선 손실: 0.4 × WeightedBCE + 0.6 × FocalTversky  ← Attention &amp; ResNet34</font>',
        st['code']
    ))

    ft_h = ["파라미터", "값", "역할"]
    ft_r = [
        ["α (FP 페널티)", "0.3", '"있다고 했는데 없는 경우" 페널티 (낮게 설정)'],
        ["β (FN 페널티)", "0.7", '**"있는데 못 찾는 경우" 페널티 (높게 설정)**'],
        ["γ (focal 강도)", "0.75", "어려운 샘플에 더 집중"],
    ]
    story.append(make_table(ft_h, ft_r, [35*mm, 20*mm, CONTENT_W - 55*mm]))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        '<font name="D2Coding" size="8.5">'
        '핵심 철학: "결함을 놓치는 것(FN) &gt; 없는걸 결함이라는 것(FP)"<br/>'
        '           산업 안전에서 미탐지가 과탐지보다 훨씬 위험하기 때문</font>',
        st['code']
    ))

    # 4-5
    story.append(Paragraph("4-5. 강화된 데이터 증강 — 392장의 한계 극복", st['h2']))
    story.append(Paragraph(
        inline_format("392장밖에 없어서 동일 이미지를 다양하게 변형하여 학습 데이터를 \"인위적으로 늘리는\" 방법:"),
        st['body']
    ))
    aug_h = ["증강 기법", "설명", "목적"]
    aug_r = [
        ["수평/수직 뒤집기", "이미지 반전", "결함 방향 불변성"],
        ["회전 (±45°)", "이미지 기울이기", "다양한 각도 대응"],
        ["**CLAHE**", "지역별 대비 강화", "어두운 결함 선명화"],
        ["**Grid Distortion**", "격자 형태 왜곡", "결함 형태 다양화"],
        ["**Coarse Dropout**", "무작위 부분 가리기", "부분 가림에 강건성"],
        ["밝기/대비 변화", "조명 조건 변화", "다양한 조명 환경"],
        ["Elastic Transform", "탄성 변형", "불규칙 형태 결함"],
    ]
    story.append(make_table(aug_h, aug_r, [40*mm, 45*mm, CONTENT_W - 85*mm]))

    # ━━━━━━━━━ SECTION 5: 데이터 시각화 분석 ━━━━━━━━━
    story.append(PageBreak())
    story.append(Paragraph("5. 데이터 시각화 분석", st['h1']))
    story.append(ColoredHR(CONTENT_W, ACCENT, 0.5))

    story.append(Paragraph("5-1. 결함 유형별 분포", st['h2']))
    add_image(story, "01_data_distribution.png")
    story.append(Paragraph(
        inline_format('**분석**:<br/>'
        '• 5가지 결함 중 **Blowhole(115쌍)**이 가장 많고, **Fray(32쌍)**가 가장 적음<br/>'
        '• Fray는 Blowhole의 약 28% 수준 → 극단적인 데이터 불균형<br/>'
        '• 전체 392쌍은 딥러닝 기준으로 매우 적은 수량<br/>'
        '• → 전이학습과 강한 데이터 증강이 필수적인 이유'),
        st['body']
    ))

    story.append(Paragraph("5-2. 샘플 이미지 확인", st['h2']))
    add_image(story, "02_sample_images.png")
    story.append(Paragraph(
        inline_format('**이미지 구성**: 1열 — 원본 자석 타일 이미지 / 2열 — 정답 마스크 (흰색=결함, 검정=정상)'),
        st['body']
    ))

    sample_h = ["결함 유형", "특징", "탐지 난이도"]
    sample_r = [
        ["**Blowhole**", "작은 점/구멍 형태, 경계 명확", "중간"],
        ["**Break**", "큰 파손 영역, 뚜렷한 형태", "낮음"],
        ["**Crack**", "매우 가는 선 형태", "높음"],
        ["**Fray**", "불규칙한 마모 흔적", "높음"],
        ["**Uneven**", "넓은 표면 불균일, 경계 불명확", "중간"],
    ]
    story.append(make_table(sample_h, sample_r, [30*mm, 60*mm, CONTENT_W - 90*mm]))

    # ━━━━━━━━━ SECTION 6: 모델별 학습 과정 분석 ━━━━━━━━━
    story.append(PageBreak())
    story.append(Paragraph("6. 모델별 학습 과정 분석", st['h1']))
    story.append(ColoredHR(CONTENT_W, ACCENT, 0.5))

    # 6-1 Vanilla
    story.append(Paragraph("6-1. Vanilla U-Net (손실: BCE + Dice)", st['h2']))
    add_image(story, "03_vanilla_curves.png")
    story.append(Paragraph(
        inline_format('**학습 설정**: 에폭: 40회 | 손실: 0.5×BCE + 0.5×Dice | LR: 1e-4 → 자동 감소'),
        st['body']
    ))
    v_h = ["에폭 구간", "관찰", "원인"]
    v_r = [
        ["1 에폭", "Dice 0.1115 (최고점)", "첫 에폭에 우연히 좋은 예측"],
        ["2~40 에폭", "Dice ≈ 0.0000~0.0069", "**모델 붕괴 (Model Collapse)**"],
        ["LR 감소 후", "개선 없음", "이미 나쁜 Local Minimum에 갇힘"],
    ]
    story.append(make_table(v_h, v_r, [30*mm, 50*mm, CONTENT_W - 80*mm]))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        inline_format('**최종 결과**: Best Val Dice: **0.1115** (1 에폭) | TTA Dice: **0.1108** | TTA IoU: **0.0664**'),
        st['body']
    ))
    story.append(Paragraph(
        inline_format('**왜 이렇게 낮은가? — 모델 붕괴(Model Collapse) 분석**'),
        st['body_bold']
    ))
    story.append(Paragraph(
        '<font name="D2Coding" size="8.5">'
        '"모델이 모든 픽셀을 검정(정상)으로 예측"하면<br/>'
        '  → 픽셀 정확도: ~92% (높아 보임)<br/>'
        '  → Dice Score:   0.000 (결함 픽셀 예측이 0이면 분모도 0)<br/><br/>'
        'BCE Loss만으로는 8%의 결함 픽셀보다 92%의 배경 픽셀에<br/>'
        '더 많은 비중을 두기 때문에 발생.</font>',
        st['code']
    ))

    # 6-2 Attention
    story.append(Paragraph("6-2. Attention U-Net (손실: 0.4×BCE + 0.6×Focal Tversky)", st['h2']))
    add_image(story, "04_attention_curves.png")
    story.append(Paragraph(
        inline_format('**학습 설정**: 에폭: 40회 | 손실: 0.4×BCE + 0.6×FocalTversky | LR: 1e-4 → 자동 감소'),
        st['body']
    ))
    a_h = ["에폭 구간", "Train Dice", "Val Dice", "관찰"]
    a_r = [
        ["1~3 에폭", "0.07~0.12", "0.04~0.09", "초기 학습 신호 존재"],
        ["4~21 에폭", "0.00~0.02", "0.0000~0.01", "불안정한 진동"],
        ["22~40 에폭", "0.003~0.007", "0.03~0.055", "점진적 회복"],
    ]
    story.append(make_table(a_h, a_r, [25*mm, 28*mm, 28*mm, CONTENT_W - 81*mm]))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        inline_format('**최종 결과**: Best Val Dice: **0.0946** (3 에폭) | TTA Dice: **0.0990** (+0.0044) | TTA IoU: **0.0582**'),
        st['body']
    ))
    story.append(Paragraph(
        inline_format('**Vanilla보다 Focal Tversky를 써도 여전히 낮은 이유**:<br/>'
        '• 392장의 절대적인 데이터 부족<br/>'
        '• **처음부터 학습하는 랜덤 초기화**의 한계<br/>'
        '• 어텐션 게이트가 효과를 발휘하려면 인코더가 먼저 의미 있는 특징을 추출해야 함'),
        st['body']
    ))

    # 6-3 ResNet34
    story.append(PageBreak())
    story.append(Paragraph("6-3. ResNet34 U-Net (손실: 0.4×BCE + 0.6×Focal Tversky)", st['h2']))
    add_image(story, "05_resnet34_curves.png")
    story.append(Paragraph(
        inline_format('**학습 설정**: 에폭: 30회 | 손실: 0.4×BCE + 0.6×FocalTversky | LR: 1e-4 → ReduceLROnPlateau'),
        st['body']
    ))
    r_h = ["에폭 구간", "Val Dice", "Val IoU", "특징"]
    r_r = [
        ["1 에폭", "0.1902", "0.1058", "첫 에폭부터 높은 시작점!"],
        ["2 에폭", "0.4939", "0.3319", "급격한 성능 향상"],
        ["3 에폭", "0.6283", "0.4646", "빠른 학습 진행"],
        ["5~6 에폭", "0.6695~0.7203", "0.5060~0.5654", "0.7 돌파"],
        ["10~11 에폭", "0.7433~0.7442", "0.5943~0.5976", "★ Best 연속 갱신"],
        ["17 에폭", "**0.7702**", "0.6300", "최고점 경신"],
        ["25 에폭", "**0.7922**", "0.6581", "LR 감소 후 재도약"],
        ["30 에폭", "**0.8002**", "0.6710", "🏆 최종 최고점"],
    ]
    story.append(make_table(r_h, r_r, [25*mm, 32*mm, 28*mm, CONTENT_W - 85*mm]))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        inline_format('**최종 결과**: Best Val Dice: **0.8002** ← Vanilla(0.1115) 대비 **7배 이상** 높음 | Best Val IoU: **0.6710** | TTA Dice: **0.2321** | TTA IoU: **0.1751**'),
        st['body']
    ))

    # TTA drop analysis
    story.append(Paragraph("ResNet34의 TTA 결과 급락 원인 분석", st['h3']))
    story.append(Paragraph(
        '<font name="D2Coding" size="8.5">'
        '학습 중 검증 Dice : 0.8002  (표준 평가)<br/>'
        'TTA 후 Dice      : 0.2321  (4방향 앙상블)<br/>'
        '차이             : -0.5681  (매우 큰 낙폭)</font>',
        st['code']
    ))
    tta_h = ["원인", "설명"]
    tta_r = [
        ["**이미지 방향 편향**", "결함 마스크가 주로 한 방향에서 학습됨. 뒤집었을 때 모델이 결함 위치를 인식 못함"],
        ["**소규모 데이터의 과적합**", "392장으로 훈련 → 학습 데이터의 특정 방향/각도에 과도하게 최적화"],
        ["**비대칭 결함 형태**", "Blowhole처럼 대칭적인 결함은 TTA에 강하지만, Break처럼 비대칭적 결함은 뒤집으면 형태가 달라짐"],
    ]
    story.append(make_table(tta_h, tta_r, [40*mm, CONTENT_W - 40*mm]))
    story.append(Spacer(1, 2*mm))
    story.append(QuoteBlock(
        inline_format('**이 경우의 실제 성능은 표준 Val Dice 0.8002가 더 신뢰할 수 있는 값**입니다.'),
        CONTENT_W, st['body']
    ))

    # ━━━━━━━━━ SECTION 7: TTA 예측 결과 시각화 ━━━━━━━━━
    story.append(PageBreak())
    story.append(Paragraph("7. TTA 예측 결과 시각화", st['h1']))
    story.append(ColoredHR(CONTENT_W, ACCENT, 0.5))
    add_image(story, "06_predictions.png")
    story.append(Paragraph(
        inline_format('**이미지 구성**:<br/>'
        '• 1열 (원본): 입력된 자석 타일 이미지<br/>'
        '• 2열 (GT 마스크): 사람이 직접 표시한 정답 결함 위치<br/>'
        '• 3열 (TTA 예측): 모델의 TTA 적용 예측 결과<br/>'
        '• 4열 (오류 맵): 노란색(TP)=정확하게 찾은 결함 / 초록색(FN)=미탐지 / 빨간색(FP)=과탐지'),
        st['body']
    ))
    obs_h = ["관찰 내용", "의미"]
    obs_r = [
        ["대부분 이미지에 초록색(FN) 비율 높음", "결함을 제대로 찾지 못함"],
        ["Uneven 결함에서 상대적으로 노란색(TP) 많음", "넓은 결함이 가장 쉽게 탐지됨"],
        ["Blowhole/Crack에서 거의 노란색 없음", "작고 가는 결함은 탐지 실패"],
        ["배경에 빨간색(FP)이 산발적으로 존재", "텍스처를 결함으로 오인하는 경우"],
    ]
    story.append(make_table(obs_h, obs_r, [CONTENT_W * 0.5, CONTENT_W * 0.5]))

    # ━━━━━━━━━ SECTION 8: 결함 유형별 성능 분석 ━━━━━━━━━
    story.append(PageBreak())
    story.append(Paragraph("8. 결함 유형별 성능 분석", st['h1']))
    story.append(ColoredHR(CONTENT_W, ACCENT, 0.5))
    add_image(story, "07_per_defect_metrics.png")

    story.append(Paragraph(
        inline_format('**결함 유형별 TTA 성능 (Vanilla/Attention 모델 기준)**:'),
        st['body_bold']
    ))
    d_h = ["결함 유형", "샘플 수", "TTA Dice", "TTA IoU", "성능 등급"]
    d_r = [
        ["**Blowhole**", "115", "**0.0046**", "0.0024", "매우 낮음"],
        ["**Break**", "85", "0.0578", "0.0317", "낮음"],
        ["**Crack**", "57", "0.0107", "0.0055", "매우 낮음"],
        ["**Fray**", "32", "0.1845", "0.1066", "낮지만 상대적 우수"],
        ["**Uneven**", "103", "**0.2635**", "0.1596", "상대적으로 가장 우수"],
    ]
    story.append(make_table(d_h, d_r, [30*mm, 22*mm, 25*mm, 25*mm, CONTENT_W - 102*mm]))
    story.append(Spacer(1, 2*mm))

    story.append(Paragraph(
        '<font name="D2Coding" size="8.5">'
        '낮은 성능 (Blowhole, Crack):<br/>'
        '  ├── 결함 영역이 작고 경계가 복잡<br/>'
        '  ├── 결함 픽셀이 전체의 1~3%로 매우 적음<br/>'
        '  └── 학습 데이터(115장/57장)가 적어 패턴 일반화 어려움<br/><br/>'
        '상대적으로 높은 성능 (Uneven, Fray):<br/>'
        '  ├── 결함 영역이 상대적으로 넓음<br/>'
        '  ├── 표면 질감 변화로 명확한 패턴 존재<br/>'
        '  └── Uneven은 영역 자체가 커서 예측이 쉬움</font>',
        st['code']
    ))

    # ━━━━━━━━━ SECTION 9: 3모델 최종 비교 ━━━━━━━━━
    story.append(PageBreak())
    story.append(Paragraph("9. 3모델 최종 비교", st['h1']))
    story.append(ColoredHR(CONTENT_W, ACCENT, 0.5))

    story.append(Paragraph("9-1. 비교 시각화", st['h2']))
    add_image(story, "08_model_comparison.png")

    story.append(Paragraph("9-2. 종합 성능 비교표", st['h2']))
    comp_h = ["모델", "손실 함수", "에폭", "Best Val Dice", "Best Val IoU", "TTA Dice", "TTA IoU"]
    comp_r = [
        ["**Vanilla U-Net**", "BCE+Dice", "40", "0.1115", "0.0592", "0.1108", "0.0664"],
        ["**Attention U-Net**", "BCE+FocalTversky", "40", "0.0946", "0.0542", "0.0990", "0.0582"],
        ["**ResNet34 U-Net**", "BCE+FocalTversky", "30", "**0.8002** ★", "**0.6710** ★", "0.2321", "0.1751"],
    ]
    cw = CONTENT_W
    story.append(make_table(comp_h, comp_r, [cw*0.17, cw*0.16, cw*0.07, cw*0.15, cw*0.15, cw*0.15, cw*0.15]))
    story.append(Spacer(1, 3*mm))

    story.append(Paragraph("9-3. 모델 파일 크기", st['h2']))
    sz_h = ["모델", "파일명", "크기"]
    sz_r = [
        ["Vanilla U-Net", "best_unet_vanilla.pth", "119MB"],
        ["Attention U-Net", "best_unet_attention.pth", "126MB"],
        ["ResNet34 U-Net", "best_unet_resnet34.pth", "93MB"],
    ]
    story.append(make_table(sz_h, sz_r, [40*mm, 55*mm, CONTENT_W - 95*mm]))
    story.append(Spacer(1, 2*mm))
    story.append(QuoteBlock(
        inline_format("흥미롭게도 ResNet34가 가장 성능이 좋으면서 파일 크기도 가장 작습니다. 전이학습의 효율성을 보여주는 수치입니다."),
        CONTENT_W, st['body']
    ))

    # ━━━━━━━━━ SECTION 10: 결과 해석 및 핵심 인사이트 ━━━━━━━━━
    story.append(PageBreak())
    story.append(Paragraph("10. 결과 해석 및 핵심 인사이트", st['h1']))
    story.append(ColoredHR(CONTENT_W, ACCENT, 0.5))

    story.append(Paragraph("10-1. 이번 실험의 가장 중요한 발견", st['h2']))
    story.append(Paragraph(
        '<font name="D2Coding" size="8.5">'
        '"392장이라는 극소 데이터셋에서<br/>'
        ' 처음부터 학습(Vanilla, Attention)은 실패에 가깝고,<br/>'
        ' 전이학습(ResNet34)만이 의미 있는 성능(Dice 0.80)을 달성했다."</font>',
        st['code']
    ))

    ins_h = ["상황", "결론"]
    ins_r = [
        ["데이터 수백 장 이하", "**전이학습 필수**"],
        ["데이터 수천 장", "전이학습 권장, 직접 학습도 가능"],
        ["데이터 수만 장 이상", "직접 학습도 충분히 가능"],
    ]
    story.append(make_table(ins_h, ins_r, [45*mm, CONTENT_W - 45*mm]))
    story.append(Spacer(1, 3*mm))

    story.append(Paragraph("10-2. Vanilla U-Net 실패 원인 (모델 붕괴)", st['h2']))
    story.append(Paragraph(
        '<font name="D2Coding" size="8.5">'
        '발생 과정:<br/>'
        '  1. 결함 픽셀 8% vs 배경 92% 불균형<br/>'
        '  2. BCE Loss가 "전부 배경으로 예측"하도록 편향<br/>'
        '  3. Dice Loss 0.5 가중치로도 보정 불충분<br/>'
        '  4. 모델이 "결함 없음"만 예측하는 trivial solution에 수렴</font>',
        st['code']
    ))
    story.append(Paragraph(
        inline_format('**해결책**: Weighted BCE (pos_weight=높게 설정) + Focal Tversky Loss 조합이 필요했음'),
        st['body']
    ))

    story.append(Paragraph("10-3. Attention U-Net이 Vanilla보다 나쁜 이유", st['h2']))
    story.append(Paragraph(
        inline_format('직관적으로 "더 복잡한 모델 = 더 좋은 성능"처럼 보이지만 실제로는 반대:'),
        st['body']
    ))
    story.append(Paragraph(
        '<font name="D2Coding" size="8.5">'
        'Attention U-Net의 어텐션 게이트는 인코더가 먼저<br/>'
        '"의미 있는 특징"을 추출해야 작동함.<br/><br/>'
        '처음부터 학습하는 경우:<br/>'
        '  초기 인코더 = 무작위 특징 추출<br/>'
        '  → 어텐션 게이트 = 무작위 가중치 × 무작위 특징 = 더 혼란스러운 학습<br/>'
        '  → 수렴 속도 오히려 느려짐</font>',
        st['code']
    ))
    story.append(Paragraph(
        inline_format('**결론**: 소규모 데이터에서 복잡한 아키텍처는 사전학습 없이는 오히려 역효과.'),
        st['body']
    ))

    story.append(Paragraph("10-4. ResNet34가 압도적으로 좋은 이유", st['h2']))
    story.append(Paragraph(
        '<font name="D2Coding" size="8.5">'
        'ResNet34 초기 상태 (ImageNet 사전학습):<br/>'
        '  이미 알고 있는 것: 선, 곡선, 텍스처, 경계, 물체 형태...<br/><br/>'
        '392장의 역할:<br/>'
        '  "이런 특징들 중 결함과 관련된 것들에 집중해"라고 미세조정(Fine-tuning)<br/><br/>'
        '결과:<br/>'
        '  1 에폭부터 Dice 0.19  ← 처음부터 높은 시작점<br/>'
        '  30 에폭에서 Dice 0.80 ← 충분한 학습 후</font>',
        st['code']
    ))

    story.append(Paragraph("10-5. 수치가 의미하는 것", st['h2']))
    story.append(Paragraph(
        inline_format('**ResNet34 Best Val Dice 0.8002**: 모델이 예측한 결함 영역의 80%가 실제 결함 영역과 겹친다는 의미.<br/>'
        '• 0.8 이상은 일반적으로 "실용 가능 수준"으로 인정<br/>'
        '• 자석 타일 392장이라는 극소 데이터에서 0.8 달성은 **우수한 성과**'),
        st['body']
    ))
    story.append(Paragraph(
        inline_format('**ResNet34 Best Val IoU 0.6710**: 예측 영역과 정답 영역을 합쳤을 때, 겹치는 부분이 67.1%를 차지.<br/>'
        'Dice보다 엄격한 기준에서도 67%는 실용적 활용이 충분히 가능한 수준.'),
        st['body']
    ))

    # ━━━━━━━━━ SECTION 11: 향후 개선 방향 ━━━━━━━━━
    story.append(PageBreak())
    story.append(Paragraph("11. 향후 개선 방향", st['h1']))
    story.append(ColoredHR(CONTENT_W, ACCENT, 0.5))

    story.append(Paragraph("현재 가장 큰 문제점과 해결책", st['h2']))

    story.append(Paragraph(
        inline_format('**문제 1: TTA 성능 급락 (ResNet34: 0.8002 → 0.2321)**'),
        st['body_bold']
    ))
    p1_h = ["해결책", "방법", "난이도"]
    p1_r = [
        ["다방향 증강 포함 학습", "학습 시 이미지를 모든 방향으로 뒤집어 학습", "낮음"],
        ["TTA 방향 제한", "4방향 → 2방향(수평만)으로 축소", "낮음"],
        ["Mixup TTA", "단순 평균 대신 가중 평균 사용", "중간"],
    ]
    story.append(make_table(p1_h, p1_r, [40*mm, 65*mm, CONTENT_W - 105*mm]))
    story.append(Spacer(1, 3*mm))

    story.append(Paragraph(
        inline_format('**문제 2: Vanilla/Attention 모델 붕괴**'),
        st['body_bold']
    ))
    p2_h = ["해결책", "방법", "예상 개선"]
    p2_r = [
        ["pos_weight 강화", "BCE pos_weight=15~20", "Dice +0.1~0.2"],
        ["학습률 낮추기", "LR 1e-4 → 5e-5", "안정적 수렴"],
        ["Warm-up Scheduler", "초기 5에폭 낮은 LR로 시작", "초기 붕괴 방지"],
    ]
    story.append(make_table(p2_h, p2_r, [40*mm, 55*mm, CONTENT_W - 95*mm]))
    story.append(Spacer(1, 3*mm))

    story.append(Paragraph(
        inline_format('**문제 3: Blowhole/Crack 탐지 실패 (Dice &lt; 0.01)**'),
        st['body_bold']
    ))
    p3_h = ["해결책", "방법", "예상 효과"]
    p3_r = [
        ["고해상도 입력", "224×224 → 448×448", "작은 결함 세밀하게 탐지"],
        ["결함별 별도 모델", "각 결함 유형에 특화된 모델", "유형별 최적화"],
        ["데이터 추가 수집", "특히 Fray(32장), Crack(57장)", "데이터 부족 해소"],
    ]
    story.append(make_table(p3_h, p3_r, [40*mm, 55*mm, CONTENT_W - 95*mm]))
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph("단계별 성능 향상 로드맵", st['h2']))
    story.append(Paragraph(
        '<font name="D2Coding" size="8.5">'
        '현재 Best (ResNet34 Val Dice 0.8002)<br/>'
        '  ↓ TTA 학습 방향 통일           → TTA Dice ~0.70 기대<br/>'
        '  ↓ 해상도 224→384               → Dice +0.02~0.04<br/>'
        '  ↓ EfficientNet-B4 백본          → Dice +0.03~0.05<br/>'
        '  ↓ 5-Fold Cross Validation      → 더 신뢰할 수 있는 평가<br/>'
        '  목표: Val Dice ≥ 0.85</font>',
        st['code']
    ))

    # ━━━━━━━━━ FINAL SUMMARY ━━━━━━━━━
    story.append(Spacer(1, 5*mm))
    story.append(ColoredHR(CONTENT_W, PRIMARY, 2))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("최종 요약", st['h1']))

    fs_h = ["항목", "내용"]
    fs_r = [
        ["**과제**", "자석 타일 표면 5종 결함 픽셀 단위 자동 탐지"],
        ["**데이터**", "극소량 — 392쌍 (5종 결함)"],
        ["**최고 모델**", "**ResNet34 U-Net**"],
        ["**최고 성능**", "Val Dice **0.8002** / Val IoU **0.6710**"],
        ["**핵심 교훈**", "소규모 데이터에서는 **전이학습이 절대적으로 유리**"],
        ["**Vanilla/Attention 실패 원인**", "데이터 부족 + 클래스 불균형 → 모델 붕괴"],
        ["**TTA 주의사항**", "다방향 학습 없이 TTA 적용 시 오히려 성능 하락 가능"],
    ]
    story.append(make_table(fs_h, fs_r, [50*mm, CONTENT_W - 50*mm]))
    story.append(Spacer(1, 5*mm))

    story.append(Paragraph(
        inline_format('**3가지 핵심 메시지**'),
        st['body_bold']
    ))
    msgs = [
        '1. **"데이터가 적을 땐 사전학습 모델을 사용하라"** — ResNet34의 전이학습만이 392장에서 Dice 0.80을 달성.',
        '2. **"복잡한 모델이 항상 좋은 것은 아니다"** — Attention U-Net은 Vanilla보다 구조가 복잡하지만, 소규모 데이터에서는 더 낮은 성능.',
        '3. **"평가 방법이 결과 해석을 바꾼다"** — ResNet34의 TTA 성능 급락은 학습 방식과 평가 방식의 불일치에서 발생.',
    ]
    for m in msgs:
        story.append(QuoteBlock(inline_format(m), CONTENT_W, st['body']))
        story.append(Spacer(1, 2*mm))

    # ━━━━━━━━━ APPENDIX ━━━━━━━━━
    story.append(Spacer(1, 5*mm))
    story.append(ColoredHR(CONTENT_W, ACCENT, 0.5))
    story.append(Paragraph("부록: 프로젝트 파일 구조", st['h2']))
    story.append(Paragraph(
        '<font name="D2Coding" size="8">'
        'SubTopic_B_MagneticTile_Segmentation/<br/>'
        '├── magnetic_tile_segmentation.py         ← 전체 파이프라인 스크립트<br/>'
        '├── models/<br/>'
        '│   ├── best_unet_vanilla.pth             ← Vanilla U-Net (119MB)<br/>'
        '│   ├── best_unet_attention.pth           ← Attention U-Net (126MB)<br/>'
        '│   └── best_unet_resnet34.pth            ← ResNet34 U-Net ★ (93MB)<br/>'
        '└── results/<br/>'
        '    ├── 01~08 PNG 시각화 파일들<br/>'
        '    ├── 09_final_summary.json<br/>'
        '    └── SubTopic_B_MagneticTile_Results_Report.md</font>',
        st['code']
    ))

    story.append(Spacer(1, 8*mm))
    story.append(ColoredHR(CONTENT_W, BORDER, 0.3))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        '<font name="NanumL" size="8" color="#9e9e9e">'
        '보고서 작성: K-Digital Training 딥러닝 12기 미니프로젝트 소주제 B (자석 타일)<br/>'
        '학습 환경: Apple Silicon MPS / Python 3.x / PyTorch 2.10<br/>'
        '데이터: Magnetic Tile Surface Defects (Kaggle)</font>',
        st['footer']
    ))

    # ── Build ──
    doc.build(story, onFirstPage=first_page, onLaterPages=add_page_number)
    print(f"PDF generated: {OUTPUT_PDF}")


if __name__ == "__main__":
    build_pdf()

#!/usr/bin/env python3
"""Markdown report to PDF converter for Casting Classification results (SubTopic A)."""

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
OUTPUT_PDF = os.path.join(BASE_DIR, "SubTopic_A_Casting_Classification_Report.pdf")

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
        p = Paragraph(text, style)
        pw, ph = p.wrap(width - 12*mm, 10000)
        self.para_height = ph
        self.height = ph + 6*mm

    def draw(self):
        self.canv.setFillColor(QUOTE_BG)
        self.canv.roundRect(0, 0, self._width, self.height, 2, fill=1, stroke=0)
        self.canv.setFillColor(QUOTE_BAR)
        self.canv.rect(0, 0, 3, self.height, fill=1, stroke=0)
        p = Paragraph(self.text, self.style)
        p.wrap(self._width - 12*mm, 10000)
        p.drawOn(self.canv, 8*mm, 3*mm)


# ── Helper functions ──
def inline_format(text):
    """Convert markdown inline formatting to reportlab XML tags."""
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<font name="NanumEB"><i>\1</i></font>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<font name="NanumB">\1</font>', text)
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    text = re.sub(r'`(.+?)`', r'<font name="D2Coding" size="8" color="#c62828">\1</font>', text)
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
    text = text.replace('★', '<font color="#f9a825">★</font>')
    return text


def make_table(headers, rows, col_widths=None):
    """Create a styled table."""
    style = STYLES
    header_cells = [Paragraph(inline_format(h), style['table_header']) for h in headers]
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


# ── Page number footer ──
def add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont('NanumL', 8)
    canvas.setFillColor(HexColor("#9e9e9e"))
    page_num = canvas.getPageNumber()
    text = f"— {page_num} —"
    canvas.drawCentredString(PAGE_W / 2, 12 * mm, text)
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
        title="주조 제품 불량/정상 자동 분류 결과 보고서",
        author="K-Digital Training 딥러닝 12기",
    )

    story = []
    st = STYLES
    cw = CONTENT_W

    # ━━━━━━━━━ COVER / TITLE ━━━━━━━━━
    story.append(Spacer(1, 15*mm))
    story.append(Paragraph("소주제 A", st['subtitle']))
    story.append(Paragraph("주조 제품 불량/정상<br/>자동 분류 결과 보고서", st['title']))
    story.append(Spacer(1, 4*mm))
    story.append(ColoredHR(CONTENT_W, PRIMARY, 2))
    story.append(Spacer(1, 4*mm))

    # Metadata table
    meta = [
        ["프로젝트", "AI 기반 스마트 팩토리 품질관리 시스템"],
        ["작성일", "2026-04-02"],
        ["모델", "ResNet50 / VGG16 / EfficientNet-B0 (ImageNet 사전학습) + Grad-CAM"],
        ["데이터셋", "Casting Product Image Data (7,348장, 2클래스)"],
        ["실행 환경", "Apple Silicon MPS, PyTorch 2.10.0"],
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
        "2. 용어 설명",
        "3. 데이터 탐색 (EDA)",
        "4. 데이터 전처리",
        "5. 모델 학습",
        "6. 테스트 성능 평가",
        "7. Grad-CAM 시각화",
        "8. 최종 결과 및 결론",
    ]
    for item in toc_items:
        story.append(Paragraph(item, st['toc']))
    story.append(PageBreak())

    # ━━━━━━━━━ SECTION 1: 프로젝트 개요 ━━━━━━━━━
    story.append(Paragraph("1. 프로젝트 개요", st['h1']))
    story.append(ColoredHR(CONTENT_W, ACCENT, 0.5))

    story.append(Paragraph("1.1 배경 및 목적", st['h2']))
    story.append(Paragraph(
        inline_format("주조(Casting)는 금속을 녹여 틀에 부어 제품을 만드는 제조 공정입니다. "
        "이 과정에서 기포, 수축, 균열 등의 결함이 발생할 수 있으며, 결함이 있는 제품이 출하되면 안전 문제와 비용 손실로 이어집니다."),
        st['body']
    ))
    story.append(Paragraph(
        inline_format("기존에는 작업자가 육안으로 제품 표면을 검사했지만, 이 방법은 느리고 일관성이 떨어집니다. "
        "본 프로젝트에서는 **CNN(합성곱 신경망) 전이학습** 기법을 활용하여 주조 제품 이미지를 자동으로 "
        "**불량(Defective)** 또는 **정상(OK)**으로 분류하는 AI 시스템을 구축했습니다."),
        st['body']
    ))

    story.append(Paragraph("1.2 전이학습이란?", st['h2']))
    story.append(Paragraph(
        inline_format("**전이학습(Transfer Learning)**은 이미 대규모 데이터(ImageNet: 1400만 장, 1000개 분류)로 "
        "학습된 모델의 \"지식\"을 가져와 우리의 작은 데이터셋에 재활용하는 기법입니다."),
        st['body']
    ))
    story.append(QuoteBlock(
        inline_format("**비유**: 영어를 잘하는 사람이 스페인어를 배울 때, 문법 구조나 알파벳에 대한 기존 지식을 활용해 "
        "훨씬 빠르게 배우는 것과 같습니다. 모델도 \"물체의 가장자리, 질감, 패턴\"을 인식하는 기존 능력을 주조 결함 인식에 재활용합니다."),
        CONTENT_W, st['body']
    ))

    story.append(Paragraph("1.3 사용 기술", st['h2']))
    t13_h = ["항목", "내용"]
    t13_r = [
        ["**프레임워크**", "PyTorch 2.10.0"],
        ["**모델**", "ResNet50, VGG16, EfficientNet-B0 (모두 ImageNet 사전학습)"],
        ["**설명 가능 AI**", "Grad-CAM (모델이 어디를 보고 판단했는지 시각화)"],
        ["**실행 환경**", "Apple Silicon MPS"],
        ["**데이터셋**", "Casting Product Image Data (7,348장, 2클래스)"],
        ["**재현성**", "Random Seed 42 고정"],
    ]
    story.append(make_table(t13_h, t13_r, [35*mm, cw - 35*mm]))
    story.append(Spacer(1, 3*mm))

    story.append(Paragraph("1.4 파이프라인 구조", st['h2']))
    story.append(Paragraph(
        '<font name="D2Coding" size="8.5">'
        '[1] 환경 설정 → [2] 데이터 탐색(EDA) → [3] 전처리 &amp; DataLoader<br/>'
        '→ [4] 모델 정의 (3종) → [5] 학습 (Early Stopping)<br/>'
        '→ [6] 학습 곡선 시각화 → [7] 테스트 평가 &amp; 혼동행렬<br/>'
        '→ [8] Grad-CAM 시각화 → [9] 최종 결과 저장</font>',
        st['code']
    ))

    # ━━━━━━━━━ SECTION 2: 용어 설명 ━━━━━━━━━
    story.append(PageBreak())
    story.append(Paragraph("2. 용어 설명", st['h1']))
    story.append(ColoredHR(CONTENT_W, ACCENT, 0.5))

    story.append(Paragraph("2.1 학습 관련 용어", st['h2']))
    t21_h = ["용어", "의미", "쉬운 설명"]
    t21_r = [
        ["**Epoch**", "전체 학습 데이터를 한 번 모두 학습하는 단위", "교과서를 처음부터 끝까지 1번 읽는 것 = 1 Epoch"],
        ["**Batch Size**", "한 번에 모델에 넣는 이미지 수 (본 실험: 32)", "한 번에 32장의 사진을 보고 학습"],
        ["**Learning Rate**", "모델이 한 번에 얼마나 많이 배울지 (0.001)", "너무 크면 핵심을 놓치고, 너무 작으면 학습이 느림"],
        ["**Loss (손실)**", "모델의 예측이 정답과 얼마나 다른지를 나타내는 숫자", "**낮을수록 좋음** — 시험에서 틀린 정도에 비유"],
        ["**Early Stopping**", "성능이 더 이상 좋아지지 않으면 학습을 중단", "5번 연속 성적이 안 오르면 멈추기"],
        ["**Params**", "모델이 학습하는 가중치의 수", "모델의 \"두뇌 크기\""],
        ["**Freeze Backbone**", "사전학습 가중치를 고정하고 분류층만 학습", "이미 배운 지식은 건드리지 않고, 분류만 배우기"],
    ]
    story.append(make_table(t21_h, t21_r, [30*mm, 55*mm, cw - 85*mm]))
    story.append(Spacer(1, 3*mm))

    story.append(Paragraph("2.2 성능 평가 지표", st['h2']))
    story.append(Paragraph(
        inline_format("본 프로젝트는 **이진 분류(불량/정상)** 문제로, 아래 4가지 지표를 사용합니다."),
        st['body']
    ))
    t22_h = ["용어", "의미", "쉬운 설명", "왜 중요한가"]
    t22_r = [
        ["**Accuracy**", "전체 예측 중 맞은 비율", "100문제 중 몇 문제를 맞혔는지", "가장 직관적인 성능 지표"],
        ["**Precision**", "\"불량\"이라고 한 것 중 진짜 불량", "불량 판정의 신뢰도", "낮으면 정상을 불량으로 오분류"],
        ["**Recall**", "실제 불량 중 모델이 찾아낸 비율", "불량을 놓치지 않는 능력", "낮으면 불량 제품이 출하됨"],
        ["**F1-Score**", "Precision과 Recall의 조화 평균", "두 지표의 균형 점수 (0~1)", "불균형 데이터에서 공정한 평가"],
    ]
    story.append(make_table(t22_h, t22_r, [25*mm, 40*mm, 40*mm, cw - 105*mm]))
    story.append(Spacer(1, 2*mm))

    story.append(QuoteBlock(
        inline_format("**제조 현장에서의 해석**:<br/>"
        "• **Precision이 높으면** → 불량 경보가 울리면 진짜 불량일 가능성이 높다 (불필요한 라인 중단 감소)<br/>"
        "• **Recall이 높으면** → 실제 불량 제품을 거의 놓치지 않는다 (불량 유출 방지)<br/>"
        "• **F1-Score** → 두 목표의 균형을 잡는 종합 지표"),
        CONTENT_W, st['body']
    ))

    story.append(Paragraph("2.3 Grad-CAM이란?", st['h2']))
    story.append(Paragraph(
        inline_format("**Grad-CAM (Gradient-weighted Class Activation Mapping)**은 모델이 이미지의 "
        "**어느 부분을 보고** 판단했는지를 히트맵으로 시각화하는 기법입니다."),
        st['body']
    ))
    story.append(QuoteBlock(
        inline_format("**비유**: 시험 문제를 풀 때 밑줄 친 핵심 키워드를 보여주는 것과 같습니다. "
        "모델이 \"이 부분이 결함이라서 불량으로 판단했다\"를 눈으로 확인할 수 있어, AI의 판단을 신뢰할 수 있는지 검증할 수 있습니다."),
        CONTENT_W, st['body']
    ))

    # ━━━━━━━━━ SECTION 3: 데이터 탐색 (EDA) ━━━━━━━━━
    story.append(PageBreak())
    story.append(Paragraph("3. 데이터 탐색 (EDA)", st['h1']))
    story.append(ColoredHR(CONTENT_W, ACCENT, 0.5))

    story.append(Paragraph("3.1 데이터셋 구성", st['h2']))
    story.append(Paragraph(
        inline_format("**Casting Product Image Data for Quality Inspection** 데이터셋은 실제 주조 공장에서 촬영한 제품 상단 이미지로 구성됩니다."),
        st['body']
    ))
    t31_h = ["항목", "값"]
    t31_r = [
        ["**총 이미지 수**", "7,348장"],
        ["**클래스**", "2개 (Defective 불량 / OK 정상)"],
        ["**원본 이미지 크기**", "300x300 픽셀, 그레이스케일(흑백)"],
        ["**입력 크기**", "224x224 (리사이즈)"],
    ]
    story.append(make_table(t31_h, t31_r, [40*mm, cw - 40*mm]))
    story.append(Spacer(1, 3*mm))

    story.append(Paragraph("3.2 샘플 이미지", st['h2']))
    add_image(story, "01_sample_images.png")
    story.append(Paragraph(
        inline_format("**분석**:<br/>"
        "• 상단 행은 **불량(Defective)** 제품으로, 표면에 미세한 기포, 홈, 불규칙한 패턴이 있습니다.<br/>"
        "• 하단 행은 **정상(OK)** 제품으로, 표면이 균일하고 매끄럽습니다.<br/>"
        "• 육안으로 보면 차이가 매우 미묘하여, 숙련된 작업자도 실수할 수 있습니다. 이것이 AI 자동 분류가 필요한 이유입니다.<br/>"
        "• 이미지가 300x300 픽셀 그레이스케일로, 모델 입력 시 224x224로 리사이즈하고 RGB 3채널로 변환됩니다."),
        st['body']
    ))

    story.append(Paragraph("3.3 클래스 분포", st['h2']))
    add_image(story, "02_class_distribution.png")
    story.append(Paragraph(
        inline_format("**분석**:<br/>"
        "• **왼쪽 막대 그래프**: Train과 Test 세트의 클래스별 이미지 수<br/>"
        "  — 불량(Defective): Train ~3,758장 + Test ~453장<br/>"
        "  — 정상(OK): Train ~2,875장 + Test ~262장<br/>"
        "• **오른쪽 파이 차트**: 전체 데이터의 클래스 비율<br/>"
        "  — 불량이 약 57%, 정상이 약 43%로, **약간의 불균형**이 있지만 심각하지 않은 수준<br/>"
        "• 데이터 불균형이 크지 않아 별도의 오버샘플링이나 클래스 가중치 조정 없이 학습을 진행했습니다."),
        st['body']
    ))

    # ━━━━━━━━━ SECTION 4: 데이터 전처리 ━━━━━━━━━
    story.append(PageBreak())
    story.append(Paragraph("4. 데이터 전처리", st['h1']))
    story.append(ColoredHR(CONTENT_W, ACCENT, 0.5))

    story.append(Paragraph("4.1 데이터 분할", st['h2']))
    t41_h = ["분할", "이미지 수", "비율", "용도"]
    t41_r = [
        ["**Train (학습)**", "5,306장", "80%", "모델 학습에 사용"],
        ["**Validation (검증)**", "1,327장", "20%", "학습 중 성능 모니터링 (과적합 감지)"],
        ["**Test (평가)**", "715장", "별도 제공", "최종 성능 평가 (학습에 전혀 미사용)"],
    ]
    story.append(make_table(t41_h, t41_r, [35*mm, 28*mm, 20*mm, cw - 83*mm]))
    story.append(Spacer(1, 3*mm))

    story.append(Paragraph("4.2 데이터 증강 (Data Augmentation)", st['h2']))
    story.append(Paragraph(
        inline_format("학습 데이터에 다양한 변환을 적용하여 모델의 일반화 능력을 높였습니다."),
        st['body']
    ))
    t42_h = ["변환", "설정", "목적"]
    t42_r = [
        ["**Resize**", "300→224", "모델 입력 크기 통일"],
        ["**RandomHorizontalFlip**", "50% 확률", "좌우 대칭 데이터 생성"],
        ["**RandomVerticalFlip**", "30% 확률", "상하 대칭 데이터 생성"],
        ["**RandomRotation**", "±15°", "약간의 회전에 강건한 모델"],
        ["**ColorJitter**", "밝기/대비 ±20%", "조명 변화에 강건한 모델"],
        ["**Normalize**", "ImageNet 평균/표준편차", "사전학습 모델과 동일한 입력 범위"],
    ]
    story.append(make_table(t42_h, t42_r, [40*mm, 45*mm, cw - 85*mm]))
    story.append(Spacer(1, 2*mm))

    story.append(QuoteBlock(
        inline_format("**왜 데이터 증강을 하는가?**: 같은 이미지를 매번 다르게 변환(��집기, 회전 등)하여 모델에게 보여주면, "
        "모델이 \"이미지의 방향과 관계없이 결함의 본질적 특징\"을 학습하게 됩니다. "
        "이를 통해 실제 공장에서 제품이 다양한 각도로 놓여있어도 정확하게 분류할 수 있습니다."),
        CONTENT_W, st['body']
    ))

    # ━━━━━━━━━ SECTION 5: 모델 학습 ━━━━━━━━━
    story.append(PageBreak())
    story.append(Paragraph("5. 모델 학습", st['h1']))
    story.append(ColoredHR(CONTENT_W, ACCENT, 0.5))

    story.append(Paragraph("5.1 세 가지 모델 비교", st['h2']))
    t51_h = ["모델", "특징", "전체 파라미터", "학습 파라미터", "모델 크기"]
    t51_r = [
        ["**ResNet50**", "잔차 연결로 깊은 네트워크 학습 가능", "~25.5M", "~525K", "92 MB"],
        ["**VGG16**", "단순하지만 깊은 구조, 대형 모델", "~138M", "~8.2K", "512 MB"],
        ["**EfficientNet-B0**", "효율적 스케일링으로 최적 성능/크기 비율", "~5.3M", "~2.6K", "16 MB"],
    ]
    story.append(make_table(t51_h, t51_r, [cw*0.18, cw*0.32, cw*0.15, cw*0.15, cw*0.20]))
    story.append(Spacer(1, 2*mm))

    story.append(QuoteBlock(
        inline_format("**왜 3개 모델을 비교하는가?**: 모델마다 장단점이 다릅니다. ResNet50은 깊은 학습에 강하고, "
        "VGG16은 구조가 단순하여 해석이 쉬우며, EfficientNet-B0은 적은 파라미터로 높은 성능을 냅니다. "
        "실제 현장 배포를 고려하면 **모델 크기와 정확도의 균형**이 중요합니다."),
        CONTENT_W, st['body']
    ))

    story.append(Paragraph("5.2 학습 설정", st['h2']))
    t52_h = ["설정 항목", "값", "설명"]
    t52_r = [
        ["**Epoch**", "최대 15 (Early Stopping)", "성능 개선이 없으면 조기 종료"],
        ["**배치 크기**", "32", "한 번에 32장씩 학습"],
        ["**옵티마이저**", "Adam (lr=0.001)", "학습률을 자동 조절하는 최적화 알고리즘"],
        ["**학습률 스케줄러**", "ReduceLROnPlateau (factor=0.5, patience=3)", "3 Epoch 연속 개선 없으면 학습률 절반"],
        ["**손실 함수**", "CrossEntropyLoss", "분류 문제의 표준 손실 함수"],
        ["**Early Stopping**", "patience=5", "5 Epoch 연속 개선 없으면 학습 중단"],
        ["**Backbone 동결**", "True", "사전학습 가중치 고정, 분류층만 학습"],
    ]
    story.append(make_table(t52_h, t52_r, [35*mm, 50*mm, cw - 85*mm]))
    story.append(Spacer(1, 3*mm))

    story.append(Paragraph("5.3 학습 곡선 분석", st['h2']))
    add_image(story, "03_training_curves.png")

    story.append(Paragraph(
        inline_format("**학습 곡선 해석**: 이 그래프는 3개 모델의 학습 과정을 보여줍니다."),
        st['body_bold']
    ))
    story.append(Paragraph(
        inline_format("**왼쪽 (Loss 그래프)** — 값이 내려갈수록 좋음:<br/>"
        "• **EfficientNet-B0** (초록): 가장 빠르게 Loss가 감소하며, 1~2 Epoch 만에 낮은 수준에 도달. 학습 효율이 매우 높음<br/>"
        "• **ResNet50** (빨강): EfficientNet과 비슷한 속도로 수렴하지만, 약간 더 높은 Loss에서 안정화<br/>"
        "• **VGG16** (파랑): 다른 모델 대비 Loss 감소가 느리고 최종 Loss도 상대적으로 높음"),
        st['body']
    ))
    story.append(Paragraph(
        inline_format("**오른쪽 (Accuracy 그래프)** — 값이 올라갈수록 좋음:<br/>"
        "• **EfficientNet-B0**: 가장 높은 검증 정확도에 빠르게 도달<br/>"
        "• Train과 Val 곡선의 간격이 크지 않아 **과적합(Overfitting)이 잘 제어**되고 있음<br/>"
        "• Early Stopping이 작동하여 불필요한 학습을 방지"),
        st['body']
    ))

    # ━━━━━━━━━ SECTION 6: 테스트 성능 평가 ━━━━━━━━━
    story.append(PageBreak())
    story.append(Paragraph("6. 테스트 성능 평가", st['h1']))
    story.append(ColoredHR(CONTENT_W, ACCENT, 0.5))

    story.append(Paragraph("6.1 모델별 성능 비교", st['h2']))
    story.append(Paragraph(
        inline_format("학습에 전혀 사용하지 않은 **715장의 테스트 이미지**로 평가한 결과:"),
        st['body']
    ))
    t61_h = ["모델", "Accuracy", "Precision", "Recall", "F1-Score"]
    t61_r = [
        ["ResNet50", "95.24%", "97.72%", "94.70%", "96.19%"],
        ["VGG16", "90.49%", "95.08%", "89.62%", "92.27%"],
        ["**EfficientNet-B0** ★", "**96.50%**", "**97.98%**", "**96.47%**", "**97.22%**"],
    ]
    story.append(make_table(t61_h, t61_r, [cw*0.25, cw*0.18, cw*0.19, cw*0.19, cw*0.19]))
    story.append(Spacer(1, 3*mm))

    story.append(Paragraph("6.2 결과 해석", st['h2']))
    story.append(Paragraph(
        inline_format("**EfficientNet-B0이 모든 지표에서 최고 성능을 달성했습니다.**"),
        st['body_bold']
    ))
    story.append(Paragraph(
        inline_format("• **Accuracy 96.50%**: 715장 중 690장을 정확히 분류. 25장만 오분류.<br/>"
        "• **Precision 97.98%**: \"불량\"이라고 판정한 제품 중 97.98%가 실제 불량. **오탐(거짓 경보)이 극히 적음** → 불필요한 라인 중단을 최소화.<br/>"
        "• **Recall 96.47%**: 실제 불량 제품 중 96.47%를 성공적으로 탐지. **불량 유출이 3.5%에 불과** → 높은 안전성.<br/>"
        "• **F1-Score 97.22%**: Precision과 Recall의 균형이 매우 우수."),
        st['body']
    ))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        inline_format("**VGG16이 가장 낮은 성능을 보인 이유**:<br/>"
        "VGG16은 138M 파라미터(512MB)의 대형 모델이지만, 분류층만 학습하는 전이학습 환경에서는 과도한 크기가 오히려 비효율적입니다. "
        "EfficientNet-B0은 5.3M 파라미터(16MB)로 VGG16의 **1/26 크기**이면서도 **6%p 높은 정확도**를 달성했습니다."),
        st['body']
    ))

    story.append(Paragraph("6.3 혼동 행렬 (Confusion Matrix)", st['h2']))
    add_image(story, "04_confusion_matrices.png")

    story.append(Paragraph(
        inline_format("**혼동 행렬이란?** 모델의 예측과 실제 정답을 2x2 표로 정리한 것입니다."),
        st['body_bold']
    ))
    tcm_h = ["", "예측: Defective", "예측: OK"]
    tcm_r = [
        ["**실제: Defective**", "True Positive (TP) 정확히 불량 탐지", "False Negative (FN) 불량을 놓침"],
        ["**실제: OK**", "False Positive (FP) 정상을 불량으로 오판", "True Negative (TN) 정확히 정상 판별"],
    ]
    story.append(make_table(tcm_h, tcm_r, [30*mm, (cw - 30*mm)/2, (cw - 30*mm)/2]))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        inline_format("**분석**:<br/>"
        "• **EfficientNet-B0**: TP(불량 정확 탐지)가 가장 높고, FN(불량 놓침)이 가장 적음<br/>"
        "• **VGG16**: FN이 상대적으로 많아, 불량 제품을 정상으로 잘못 분류하는 경우가 더 많음<br/>"
        "• 제조 현장에서는 **FN(불량 놓침)**이 가장 위험하므로, Recall이 높은 EfficientNet-B0이 가장 적합"),
        st['body']
    ))

    # ━━━━━━━━━ SECTION 7: Grad-CAM 시각화 ━━━━━━━━━
    story.append(PageBreak())
    story.append(Paragraph("7. Grad-CAM 시각화", st['h1']))
    story.append(ColoredHR(CONTENT_W, ACCENT, 0.5))

    add_image(story, "05_gradcam_best_model.png")

    story.append(Paragraph(
        inline_format("**Grad-CAM 결과 해석**: 이 시각화는 EfficientNet-B0 모델이 이미지의 **어느 부분을 보고** 불량/정상을 판단했는지를 히트맵으로 보여줍니다."),
        st['body_bold']
    ))
    story.append(Paragraph(
        inline_format("• **빨간색/노란색 영역**: 모델이 **강하게 주목**한 부분 (판단에 가장 큰 영향)<br/>"
        "• **파란색/초록색 영역**: 모델이 **덜 주목**한 부분"),
        st['body']
    ))
    story.append(Spacer(1, 2*mm))

    story.append(Paragraph(
        inline_format("**핵심 발견**:"),
        st['body_bold']
    ))
    story.append(Paragraph(
        inline_format("1. **불량(Defective) 이미지**: 모델이 표면의 기포, 홈, 균열 등 **실제 결함 영역에 정확히 집중**하고 있습니다. "
        "이는 모델이 단순한 패턴 암기가 아닌, 결함의 본질적 특징을 학습했음을 의미합니다.<br/>"
        "2. **정상(OK) 이미지**: 히트맵이 넓게 분산되어 있어, 특정 결함 영역이 없으므로 전체적인 표면 균일성을 보고 정상으로 판단합니다.<br/>"
        "3. **설명 가능성(Explainability)**: Grad-CAM을 통해 AI의 판단 근거를 사람이 이해할 수 있어, 품질 관리자가 AI의 결정을 신뢰하고 검증할 수 있습니다."),
        st['body']
    ))
    story.append(Spacer(1, 2*mm))
    story.append(QuoteBlock(
        inline_format("**왜 Grad-CAM이 중요한가?**: \"AI가 96.5% 정확도로 분류합니다\"라고만 하면 현장에서 신뢰하기 어렵습니다. "
        "하지만 \"AI가 이 부분의 기포를 보고 불량으로 판단했습니다\"라고 시각적 근거를 제시하면, "
        "품질 관리자가 AI의 판단을 납득하고 활용할 수 있습니다."),
        CONTENT_W, st['body']
    ))

    # ━━━━━━━━━ SECTION 8: 최종 결과 및 결론 ━━━━━━━━━
    story.append(PageBreak())
    story.append(Paragraph("8. 최종 결과 및 결론", st['h1']))
    story.append(ColoredHR(CONTENT_W, ACCENT, 0.5))

    story.append(Paragraph("8.1 최종 성능 요약", st['h2']))
    t81_h = ["모델", "Accuracy", "Precision", "Recall", "F1-Score", "모델 크기"]
    t81_r = [
        ["ResNet50", "95.24%", "97.72%", "94.70%", "96.19%", "92 MB"],
        ["VGG16", "90.49%", "95.08%", "89.62%", "92.27%", "512 MB"],
        ["**EfficientNet-B0** ★", "**96.50%**", "**97.98%**", "**96.47%**", "**97.22%**", "**16 MB**"],
    ]
    story.append(make_table(t81_h, t81_r, [cw*0.20, cw*0.14, cw*0.14, cw*0.14, cw*0.14, cw*0.14]))
    story.append(Spacer(1, 3*mm))

    story.append(Paragraph("8.2 주요 발견", st['h2']))
    findings = [
        '1. **EfficientNet-B0이 최고 성능**: 96.5% 정확도, 97.22% F1-Score로 가장 우수하면서도, 모델 크기가 16MB로 가장 가벼움 → **정확도와 효율성 모두 1등**.',
        '2. **모델 크기 ≠ 성능**: VGG16(512MB)은 EfficientNet-B0(16MB)보다 **32배 크지만 성능은 6%p 낮음**. 모델 설계의 효율성이 단순한 크기보다 중요함.',
        '3. **전이학습의 효과**: ImageNet으로 사전학습된 모델을 활용하여, 7,348장의 비교적 적은 데이터로도 96.5%의 높은 정확도를 달성.',
        '4. **Grad-CAM 검증**: 모델이 실제 결함 영역에 정확히 집중하고 있음을 시각적으로 확인. AI의 판단이 사람의 직관과 일치.',
    ]
    for f in findings:
        story.append(QuoteBlock(inline_format(f), CONTENT_W, st['body']))
        story.append(Spacer(1, 2*mm))

    story.append(Paragraph("8.3 실무 적용 제안", st['h2']))
    t83_h = ["시나리오", "추천 모델", "이유"]
    t83_r = [
        ["**일반 품질 검사**", "EfficientNet-B0", "최고 정확도 + 최소 크기(16MB)"],
        ["**엣지 디바이스 배포**", "EfficientNet-B0", "경량 모델로 임베디드 시스템에 적합"],
        ["**해석 가능성 필요**", "EfficientNet-B0 + Grad-CAM", "품질 관리자에게 판단 근거 제공"],
        ["**빠른 프로토타이핑**", "ResNet50", "안정적 성능, 풍부한 커뮤니티 지원"],
    ]
    story.append(make_table(t83_h, t83_r, [40*mm, 45*mm, cw - 85*mm]))
    story.append(Spacer(1, 3*mm))

    story.append(Paragraph("8.4 향후 개선 방안", st['h2']))
    t84_h = ["개선 방안", "설명", "기대 효과"]
    t84_r = [
        ["**Fine-tuning**", "Backbone 전체를 낮은 학습률로 추가 학습", "1~2%p 추가 성능 향상 가능"],
        ["**다중 클래스 분류**", "불량 유형(기포, 수축, 균열 등) 세분화", "결함 원인 분석"],
        ["**TTA**", "추론 시 여러 변환을 적용하여 앙상블 효과", "안정적인 예측"],
        ["**모바일 배포**", "ONNX/TensorRT 변환으로 실시간 추론 최적화", "현장 실시간 적용"],
    ]
    story.append(make_table(t84_h, t84_r, [35*mm, 55*mm, cw - 90*mm]))
    story.append(Spacer(1, 3*mm))

    story.append(Paragraph("8.5 산출물 목록", st['h2']))
    t85_h = ["파일", "설명"]
    t85_r = [
        ["results/01_sample_images.png", "불량/정상 샘플 이미지 (2x5 그리드)"],
        ["results/02_class_distribution.png", "클래스 분포 (막대+파이 차트)"],
        ["results/03_training_curves.png", "3개 모델 학습 곡선 (Loss/Accuracy)"],
        ["results/04_confusion_matrices.png", "3개 모델 혼동 행렬"],
        ["results/05_gradcam_best_model.png", "Grad-CAM 히트맵 (EfficientNet-B0)"],
        ["results/06_final_summary.json", "최종 결과 JSON"],
        ["models/best_efficientnet_b0.pth", "최적 모델 가중치 (16MB)"],
        ["models/best_resnet50.pth", "ResNet50 가중치 (92MB)"],
        ["models/best_vgg16.pth", "VGG16 가중치 (512MB)"],
    ]
    story.append(make_table(t85_h, t85_r, [55*mm, cw - 55*mm]))

    # ━━━━━━━━━ FINAL SUMMARY ━━━━━━━━━
    story.append(Spacer(1, 5*mm))
    story.append(ColoredHR(CONTENT_W, PRIMARY, 2))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("최종 요약", st['h1']))

    fs_h = ["항목", "내용"]
    fs_r = [
        ["**과제**", "주조 제품 이미지를 불량/정상으로 자동 분류"],
        ["**데이터**", "7,348장 (2클래스: Defective / OK)"],
        ["**최고 모델**", "**EfficientNet-B0** (전이학습)"],
        ["**최고 성능**", "Accuracy **96.50%** / F1-Score **97.22%**"],
        ["**핵심 교훈**", "모델 크기 ≠ 성능. 효율적 설계가 핵심"],
        ["**설명 가능성**", "Grad-CAM으로 결함 영역 집중 확인"],
        ["**실무 적용성**", "16MB 경량 모델로 엣지 디바이스 배포 가능"],
    ]
    story.append(make_table(fs_h, fs_r, [40*mm, cw - 40*mm]))
    story.append(Spacer(1, 5*mm))

    story.append(Paragraph(
        inline_format('**3가지 핵심 메시지**'),
        st['body_bold']
    ))
    msgs = [
        '1. **"효율적 모델이 거대한 모델을 이긴다"** — EfficientNet-B0(16MB)이 VGG16(512MB)보다 6%p 높은 정확도를 달성.',
        '2. **"전이학습은 적은 데이터의 구원자"** — ImageNet 사전학습으로 7,348장만으로도 96.5% 정확도 달성.',
        '3. **"설명 가능한 AI가 신뢰를 만든다"** — Grad-CAM을 통해 모델의 판단 근거를 시각적으로 제시하여 현장 신뢰 확보.',
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
        'SubTopic_A_Casting_Classification/<br/>'
        '├── casting_classification.py              ← 전체 파이프라인 스크립트<br/>'
        '├── models/<br/>'
        '│   ├── best_efficientnet_b0.pth           ← EfficientNet-B0 ★ (16MB)<br/>'
        '│   ├── best_resnet50.pth                  ← ResNet50 (92MB)<br/>'
        '│   └── best_vgg16.pth                     ← VGG16 (512MB)<br/>'
        '└── results/<br/>'
        '    ├── 01~05 PNG 시각화 파일들<br/>'
        '    ├── 06_final_summary.json<br/>'
        '    └── SubTopic_A_Results_Report.md</font>',
        st['code']
    ))

    story.append(Spacer(1, 8*mm))
    story.append(ColoredHR(CONTENT_W, BORDER, 0.3))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        '<font name="NanumL" size="8" color="#9e9e9e">'
        '보고서 작성: K-Digital Training 딥러닝 12기 미니프로젝트 소주제 A (주조 제품 분류)<br/>'
        '학습 환경: Apple Silicon MPS / Python 3.x / PyTorch 2.10<br/>'
        '데이터: Casting Product Image Data for Quality Inspection (Kaggle)</font>',
        st['footer']
    ))

    # ── Build ──
    doc.build(story, onFirstPage=first_page, onLaterPages=add_page_number)
    print(f"PDF generated: {OUTPUT_PDF}")


if __name__ == "__main__":
    build_pdf()

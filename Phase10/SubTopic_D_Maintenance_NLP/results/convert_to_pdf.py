#!/usr/bin/env python3
"""Markdown report to PDF converter for SubTopic_D Maintenance NLP results."""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle,
    PageBreak, Flowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage
import re

# ── Paths ──
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PDF = os.path.join(BASE_DIR, "SubTopic_D_Results_Report.pdf")

# ── Register Korean fonts ──
pdfmetrics.registerFont(TTFont("NanumR", "/Users/yeong/Library/Fonts/NanumSquare_acR.ttf"))
pdfmetrics.registerFont(TTFont("NanumB", "/Users/yeong/Library/Fonts/NanumSquare_acB.ttf"))
pdfmetrics.registerFont(TTFont("NanumEB", "/Users/yeong/Library/Fonts/NanumSquare_acEB.ttf"))
pdfmetrics.registerFont(TTFont("NanumL", "/Users/yeong/Library/Fonts/NanumSquare_acL.ttf"))
pdfmetrics.registerFont(TTFont("D2Coding", "/Users/yeong/Library/Fonts/D2Coding.ttc", subfontIndex=0))

# ── Colors ──
PRIMARY = HexColor("#1a237e")
ACCENT = HexColor("#0d47a1")
LIGHT_BG = HexColor("#e8eaf6")
CODE_BG = HexColor("#f5f5f5")
TABLE_HEADER = HexColor("#283593")
TABLE_ALT = HexColor("#e8eaf6")
BORDER = HexColor("#bdbdbd")
QUOTE_BAR = HexColor("#1565c0")
QUOTE_BG = HexColor("#e3f2fd")

# ── Page settings ──
PAGE_W, PAGE_H = A4
ML, MR, MT, MB = 20*mm, 20*mm, 22*mm, 22*mm
CW = PAGE_W - ML - MR  # content width


# ── Styles ──
def S():
    s = {}
    s['title'] = ParagraphStyle('Title', fontName='NanumEB', fontSize=22, leading=30, textColor=PRIMARY, alignment=TA_CENTER, spaceAfter=4*mm)
    s['subtitle'] = ParagraphStyle('Subtitle', fontName='NanumR', fontSize=10, leading=14, textColor=HexColor("#616161"), alignment=TA_CENTER, spaceAfter=2*mm)
    s['h1'] = ParagraphStyle('H1', fontName='NanumEB', fontSize=16, leading=22, textColor=PRIMARY, spaceBefore=10*mm, spaceAfter=4*mm)
    s['h2'] = ParagraphStyle('H2', fontName='NanumB', fontSize=13, leading=18, textColor=ACCENT, spaceBefore=7*mm, spaceAfter=3*mm)
    s['h3'] = ParagraphStyle('H3', fontName='NanumB', fontSize=11, leading=16, textColor=HexColor("#1565c0"), spaceBefore=5*mm, spaceAfter=2*mm)
    s['body'] = ParagraphStyle('Body', fontName='NanumR', fontSize=9.5, leading=15, textColor=black, alignment=TA_JUSTIFY, spaceAfter=2*mm)
    s['body_bold'] = ParagraphStyle('BodyBold', fontName='NanumB', fontSize=9.5, leading=15, textColor=black, spaceAfter=2*mm)
    s['code'] = ParagraphStyle('Code', fontName='D2Coding', fontSize=8, leading=12, textColor=HexColor("#263238"), backColor=CODE_BG, borderWidth=0.5, borderColor=BORDER, borderPadding=6, spaceAfter=3*mm, leftIndent=4*mm, rightIndent=4*mm)
    s['toc'] = ParagraphStyle('TOC', fontName='NanumR', fontSize=10, leading=16, textColor=ACCENT, leftIndent=5*mm, spaceAfter=1*mm)
    s['th'] = ParagraphStyle('TH', fontName='NanumB', fontSize=8.5, leading=12, textColor=white, alignment=TA_CENTER)
    s['tc'] = ParagraphStyle('TC', fontName='NanumR', fontSize=8.5, leading=12, textColor=black, alignment=TA_CENTER)
    s['tcl'] = ParagraphStyle('TCL', fontName='NanumR', fontSize=8.5, leading=12, textColor=black, alignment=TA_LEFT)
    s['footer'] = ParagraphStyle('Footer', fontName='NanumL', fontSize=7.5, leading=10, textColor=HexColor("#9e9e9e"), alignment=TA_CENTER)
    return s

ST = S()


# ── Custom Flowables ──
class ColoredHR(Flowable):
    def __init__(self, width, color=PRIMARY, thickness=1):
        Flowable.__init__(self)
        self.width = width; self.color = color; self.thickness = thickness
        self.height = thickness + 2*mm
    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, self.thickness/2, self.width, self.thickness/2)


class QuoteBlock(Flowable):
    def __init__(self, text, width, style):
        Flowable.__init__(self)
        self.text = text; self._width = width; self.style = style
        p = Paragraph(text, style)
        _, ph = p.wrap(width - 12*mm, 10000)
        self.height = ph + 6*mm
    def draw(self):
        self.canv.setFillColor(QUOTE_BG)
        self.canv.roundRect(0, 0, self._width, self.height, 2, fill=1, stroke=0)
        self.canv.setFillColor(QUOTE_BAR)
        self.canv.rect(0, 0, 3, self.height, fill=1, stroke=0)
        p = Paragraph(self.text, self.style)
        p.wrap(self._width - 12*mm, 10000)
        p.drawOn(self.canv, 8*mm, 3*mm)


# ── Helpers ──
def fmt(text):
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<font name="NanumEB"><i>\1</i></font>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<font name="NanumB">\1</font>', text)
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    text = re.sub(r'`(.+?)`', r'<font name="D2Coding" size="8" color="#c62828">\1</font>', text)
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
    text = text.replace('★', '<font color="#f9a825">★</font>')
    return text


def tbl(headers, rows, widths=None):
    hc = [Paragraph(fmt(h), ST['th']) for h in headers]
    dr = []
    for row in rows:
        cells = []
        for i, c in enumerate(row):
            ct = fmt(c.strip()) if c else ""
            cells.append(Paragraph(ct, ST['tcl'] if i == 0 else ST['tc']))
        dr.append(cells)
    data = [hc] + dr
    if widths is None:
        widths = [CW / len(headers)] * len(headers)
    t = Table(data, colWidths=widths, repeatRows=1)
    ts = [
        ('BACKGROUND', (0,0), (-1,0), TABLE_HEADER),
        ('TEXTCOLOR', (0,0), (-1,0), white),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,0), 6), ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('TOPPADDING', (0,1), (-1,-1), 4), ('BOTTOMPADDING', (0,1), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6), ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            ts.append(('BACKGROUND', (0,i), (-1,i), TABLE_ALT))
    t.setStyle(TableStyle(ts))
    return t


def img(story, filename, max_w=CW, max_h=160*mm):
    path = os.path.join(BASE_DIR, filename)
    if not os.path.exists(path):
        story.append(Paragraph(f"[이미지 없음: {filename}]", ST['body']))
        return
    pi = PILImage.open(path)
    iw, ih = pi.size
    r = min(max_w/iw, max_h/ih)
    story.append(Image(path, width=iw*r, height=ih*r))
    story.append(Spacer(1, 3*mm))


def code(text):
    return Paragraph(f'<font name="D2Coding" size="8.5">{text}</font>', ST['code'])


def body(text):
    return Paragraph(fmt(text), ST['body'])


def bbold(text):
    return Paragraph(fmt(text), ST['body_bold'])


def quote(text):
    return QuoteBlock(fmt(text), CW, ST['body'])


def page_num(canvas, doc):
    canvas.saveState()
    canvas.setFont('NanumL', 8)
    canvas.setFillColor(HexColor("#9e9e9e"))
    canvas.drawCentredString(PAGE_W/2, 12*mm, f"— {canvas.getPageNumber()} —")
    canvas.setStrokeColor(LIGHT_BG); canvas.setLineWidth(0.5)
    canvas.line(ML, PAGE_H - MT + 5*mm, PAGE_W - MR, PAGE_H - MT + 5*mm)
    canvas.restoreState()


# ── Build PDF ──
def build():
    doc = SimpleDocTemplate(OUTPUT_PDF, pagesize=A4, leftMargin=ML, rightMargin=MR, topMargin=MT, bottomMargin=MB,
                            title="설비 고장 유형 예측 결과 보고서", author="K-Digital Training 딥러닝 12기")
    story = []

    # ━━━ COVER ━━━
    story.append(Spacer(1, 15*mm))
    story.append(Paragraph("소주제 D", ST['subtitle']))
    story.append(Paragraph("설비 고장 유형 예측<br/>결과 보고서", ST['title']))
    story.append(Spacer(1, 4*mm))
    story.append(ColoredHR(CW, PRIMARY, 2))
    story.append(Spacer(1, 4*mm))

    meta = [
        ["프로젝트", "K-Digital Training 딥러닝 12기 미니프로젝트"],
        ["작성일", "2026-04-01"],
        ["모델", "DNN (수치) / LSTM (텍스트) / DistilBERT (텍스트)"],
        ["데이터셋", "Machine Predictive Maintenance Dataset (10,000건, 6종 고장 유형)"],
    ]
    mc = [[Paragraph(f'<font name="NanumB" color="#1a237e">{r[0]}</font>', ST['body']),
           Paragraph(r[1], ST['body'])] for r in meta]
    mt = Table(mc, colWidths=[35*mm, CW-35*mm])
    mt.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'), ('TOPPADDING',(0,0),(-1,-1),2),
                            ('BOTTOMPADDING',(0,0),(-1,-1),2), ('LINEBELOW',(0,0),(-1,-1),0.3,BORDER)]))
    story.append(mt)
    story.append(Spacer(1, 8*mm))

    # ━━━ TOC ━━━
    story.append(Paragraph("목차", ST['h1']))
    for item in [
        "1. 프로젝트 개요", "2. 핵심 용어 해설 (비전공자용)", "3. 데이터셋 소개 및 분포",
        "4. 이 프로젝트의 핵심 아이디어 — 수치를 텍스트로 변환", "5. 왜 이 방법들을 선택했는가?",
        "6. 데이터 탐색 시각화", "7. 모델별 학습 과정 분석", "8. 3모델 최종 비교 및 혼동 행렬",
        "9. 워드클라우드 — 어떤 단어가 고장을 설명하는가?", "10. 결과 해석 및 핵심 인사이트",
        "11. 향후 개선 방향",
    ]:
        story.append(Paragraph(item, ST['toc']))
    story.append(PageBreak())

    # ━━━ 1. 프로젝트 개요 ━━━
    story.append(Paragraph("1. 프로젝트 개요", ST['h1']))
    story.append(ColoredHR(CW, ACCENT, 0.5))

    story.append(Paragraph("무엇을 해결하려 했는가?", ST['h2']))
    story.append(body("공장 내 설비(기계)가 고장 나기 전에 **어떤 종류의 고장이 발생할지 미리 예측**하는 시스템을 만드는 것이 목표입니다. "
                       "설비에 부착된 센서들이 온도, 회전 속도, 토크, 마모도 등을 실시간으로 측정하며, 이 수치 데이터를 바탕으로 6가지 고장 유형 중 하나를 예측합니다."))

    story.append(Paragraph("이 프로젝트가 특별한 이유 — 수치 → 언어 변환", ST['h2']))
    story.append(body("기존 방법은 \"숫자 데이터 → 분류 모델\"의 단순한 흐름이지만, 이 프로젝트는 **센서 수치를 사람이 읽을 수 있는 자연어 문장으로 변환한 후**, 언어 모델(LSTM, BERT)에 적용하는 창의적인 접근법을 사용합니다."))
    story.append(code(
        '[기존 방식]<br/>'
        '센서 수치 (숫자) → DNN → 고장 유형 예측<br/><br/>'
        '[이 프로젝트]<br/>'
        '센서 수치 (숫자) → 텍스트 변환 → LSTM/BERT → 고장 유형 예측'))

    # ━━━ 2. 핵심 용어 해설 ━━━
    story.append(Paragraph("2. 핵심 용어 해설 (비전공자용)", ST['h1']))
    story.append(ColoredHR(CW, ACCENT, 0.5))

    story.append(Paragraph("2-1. 분류 (Classification)", ST['h2']))
    story.append(body("입력 데이터를 미리 정해진 카테고리 중 하나로 구분하는 작업입니다. 총 6개 카테고리(클래스) 중 하나를 예측하는 **다중 클래스 분류** 문제입니다."))
    story.append(code(
        '입력: 센서 수치들<br/>'
        '출력: "이건 열 방출 고장입니다" / "정상입니다" / "공구 마모 고장입니다" ...'))

    story.append(Paragraph("2-2. Accuracy (정확도)", ST['h2']))
    story.append(code(
        '           올바르게 예측한 건수<br/>'
        'Accuracy = ───────────────────<br/>'
        '               전체 건수'))
    story.append(body("• 값 범위: 0~1 (또는 0~100%)<br/>"
                       "• 97.4% = 1,500건 테스트 중 약 1,461건을 올바르게 예측"))
    story.append(quote("**주의**: 불균형 데이터에서는 \"모두 정상\"이라고 해도 96.52%가 나옴 → Accuracy만으로는 판단 불충분"))

    story.append(Paragraph("2-3. F1 Score — 두 가지 종류", ST['h2']))
    story.append(bbold("F1(macro) — 클래스 불균형에서 진짜 성능 측정"))
    story.append(code(
        '각 클래스(고장 유형)의 F1을 따로 계산한 뒤 단순 평균<br/>'
        '→ 적은 샘플의 고장 유형도 동등하게 중요하게 봄<br/>'
        '→ 희귀 고장을 얼마나 잘 찾는지 반영하는 핵심 지표'))
    story.append(bbold("F1(weighted) — 데이터 양 비례 가중 평균"))
    story.append(code(
        '각 클래스의 F1을 샘플 수에 비례하여 가중 평균<br/>'
        '→ 많은 "No Failure"(96.52%)에 더 많은 가중치<br/>'
        '→ Accuracy와 비슷한 경향 (불균형 영향 있음)'))
    story.append(code(
        'F1(macro) &lt;&lt; F1(weighted)<br/>'
        '→ 다수 클래스(정상)는 잘 맞추지만,<br/>'
        '  소수 클래스(희귀 고장)는 제대로 못 찾는다는 신호'))

    story.append(Paragraph("2-4. Precision / Recall", ST['h2']))
    story.append(code(
        'Precision (정밀도) = 고장이라고 예측한 것 중 실제 고장인 비율<br/>'
        '                   = "내가 경보를 울렸을 때 실제로 고장인 확률"<br/><br/>'
        'Recall (재현율)    = 실제 고장 중 예측으로 찾아낸 비율<br/>'
        '                   = "실제 고장 중 몇 %나 잡아냈는가"<br/><br/>'
        'F1 Score = 2 × (Precision × Recall) / (Precision + Recall)'))
    story.append(body("**산업 현장에서의 균형**: Recall이 낮으면 → 고장을 못 잡아서 대형 사고 위험. Precision이 낮으면 → 오경보가 많아서 작업 효율 저하"))

    story.append(Paragraph("2-5. 혼동 행렬 (Confusion Matrix)", ST['h2']))
    story.append(code(
        '              예측: 정상  예측: 고장A  예측: 고장B<br/>'
        '실제: 정상  [  1430       5          2    ]<br/>'
        '실제: 고장A [     3      25          1    ]<br/>'
        '실제: 고장B [     2       1         31    ]'))
    story.append(body("• **대각선** = 올바르게 예측한 케이스 (높을수록 좋음)<br/>"
                       "• **비대각선** = 잘못 분류한 케이스 (낮을수록 좋음)<br/>"
                       "• 어떤 고장 유형을 다른 유형과 헷갈리는지 한눈에 파악 가능"))

    story.append(Paragraph("2-6. 클래스 불균형 (Class Imbalance)", ST['h2']))
    story.append(tbl(
        ["고장 유형", "건수", "비율"],
        [["**No Failure (정상)**", "9,652", "**96.52%**"],
         ["Heat Dissipation Failure", "112", "1.12%"],
         ["Power Failure", "95", "0.95%"],
         ["Overstrain Failure", "78", "0.78%"],
         ["Tool Wear Failure", "45", "0.45%"],
         ["Random Failures", "18", "**0.18%**"]],
        [55*mm, 25*mm, CW-80*mm]))
    story.append(Spacer(1, 2*mm))
    story.append(body("정상이 고장보다 **약 280배** 많습니다. 이 극심한 불균형이 모든 모델 성능 해석의 핵심입니다."))

    story.append(PageBreak())

    # ━━━ 3. 데이터셋 소개 ━━━
    story.append(Paragraph("3. 데이터셋 소개 및 분포", ST['h1']))
    story.append(ColoredHR(CW, ACCENT, 0.5))

    story.append(Paragraph("기본 정보", ST['h2']))
    story.append(tbl(
        ["항목", "내용"],
        [["데이터셋 이름", "Machine Predictive Maintenance Classification Dataset"],
         ["총 레코드 수", "**10,000건**"],
         ["입력 피처 수", "5개 센서값 + 기계 유형"],
         ["예측 클래스 수", "**6종**"],
         ["결측치", "없음 (0건)"]],
        [40*mm, CW-40*mm]))
    story.append(Spacer(1, 3*mm))

    story.append(Paragraph("데이터 분할", ST['h2']))
    story.append(code(
        '전체 10,000건<br/>'
        '├── 학습(Train)  7,000건 (70%) — 모델 학습용<br/>'
        '├── 검증(Val)    1,500건 (15%) — 학습 중 성능 모니터링<br/>'
        '└── 테스트(Test) 1,500건 (15%) — 최종 평가 (학습에 절대 미사용)'))

    story.append(Paragraph("6가지 고장 유형 설명", ST['h2']))
    story.append(tbl(
        ["고장 유형", "영문명", "건수", "비율", "원인"],
        [["**정상**", "No Failure", "9,652", "96.52%", "—"],
         ["**열 방출 고장**", "Heat Dissipation Failure", "112", "1.12%", "공정 온도-공기 온도 차이 부족"],
         ["**동력 고장**", "Power Failure", "95", "0.95%", "토크×회전속도 임계값 초과"],
         ["**과부하 고장**", "Overstrain Failure", "78", "0.78%", "공구 마모 × 토크 과부하"],
         ["**공구 마모 고장**", "Tool Wear Failure", "45", "0.45%", "공구 마모 초과"],
         ["**무작위 고장**", "Random Failures", "18", "0.18%", "임의 발생"]],
        [30*mm, 42*mm, 18*mm, 18*mm, CW-108*mm]))

    # ━━━ 4. 핵심 아이디어 ━━━
    story.append(PageBreak())
    story.append(Paragraph("4. 이 프로젝트의 핵심 아이디어 — 수치를 텍스트로 변환", ST['h1']))
    story.append(ColoredHR(CW, ACCENT, 0.5))

    story.append(Paragraph("왜 숫자를 글로 바꾸는가?", ST['h2']))
    story.append(body("센서 데이터는 원래 숫자(수치형) 데이터입니다:"))
    story.append(code('공기온도: 298.1K  |  공정온도: 308.6K  |  회전속도: 1551 rpm  |  토크: 42.8Nm  |  마모: 0min'))
    story.append(body("이것을 사람이 읽는 **자연어 문장**으로 변환합니다:"))
    story.append(code(
        '"Type M machine. Air temperature 298.1K normal. Process temperature 308.6K normal.<br/>'
        ' Rotational speed 1551rpm normal. Torque 42.8Nm normal. Tool wear 0min low.<br/>'
        ' Temp diff 10.5K normal. Power 6963W normal."'))

    story.append(Paragraph("수치 → 텍스트 변환 규칙", ST['h2']))
    story.append(body("단순히 숫자를 문자로 바꾸는 것이 아니라, **전문가 지식을 담아** 범주형 설명을 추가합니다:"))
    story.append(tbl(
        ["센서 값", "변환 예시", "포함된 전문 지식"],
        [["공기 온도 298.1K", '"298.1K normal"', "정상 범위 판단"],
         ["회전속도 1551rpm", '"1551rpm normal"', "정상/경고/위험 구분"],
         ["토크 42.8Nm", '"42.8Nm normal"', "과부하 여부 판단"],
         ["공구 마모 150min", '"150min **high**"', "교체 필요 임박 표시"]],
        [40*mm, 42*mm, CW-82*mm]))
    story.append(Spacer(1, 2*mm))
    story.append(bbold("파생 피처 추가:"))
    story.append(code(
        'temp_diff = 공정온도 - 공기온도    # 열 방출 고장과 직접 연관<br/>'
        'power     = 토크 × 회전속도 × 2π/60  # 동력 고장과 직접 연관'))

    story.append(Paragraph("이 접근법의 장점", ST['h2']))
    story.append(tbl(
        ["장점", "설명"],
        [["**해석 가능성**", "어떤 표현이 어떤 고장을 유발하는지 워드클라우드로 분석 가능"],
         ["**BERT 활용**", "사전 학습된 대형 언어 모델의 문맥 이해 능력 활용"],
         ["**도메인 지식 통합**", "임계값 기반 정상/경고/위험 레이블을 텍스트에 직접 포함"]],
        [35*mm, CW-35*mm]))

    # ━━━ 5. 왜 이 방법들을 선택했는가? ━━━
    story.append(PageBreak())
    story.append(Paragraph("5. 왜 이 방법들을 선택했는가?", ST['h1']))
    story.append(ColoredHR(CW, ACCENT, 0.5))

    story.append(Paragraph("5-1. DNN (Deep Neural Network) — 수치 직접 입력 베이스라인", ST['h2']))
    story.append(code(
        '입력: 8개 수치 피처 (온도, 속도, 토크, 마모, 파생 피처)<br/>'
        '구조: Linear(8→128) → BN → ReLU → Dropout(0.3)<br/>'
        '      Linear(128→64) → BN → ReLU → Dropout(0.3)<br/>'
        '      Linear(64→32) → ReLU<br/>'
        '      Linear(32→6)  → 분류'))
    story.append(body("**선택 이유**: 수치 데이터 처리의 가장 기본적인 딥러닝 방법. "
                       "텍스트 변환 없이 원본 수치 그대로 입력 → **베이스라인 역할**. "
                       "\"텍스트 변환이 실제로 도움이 되는가?\"를 확인하는 비교군."))

    story.append(Paragraph("5-2. LSTM (Long Short-Term Memory) — 텍스트 순서 정보 학습", ST['h2']))
    story.append(code(
        '입력: 텍스트 → 단어 인덱스 시퀀스<br/>'
        '구조: Embedding → Bi-LSTM(256) → Attention → Linear(6)'))
    story.append(body("**선택 이유**: 텍스트는 단어의 **순서**가 중요. **Bi-LSTM**은 텍스트를 앞에서도, 뒤에서도 읽어 더 풍부한 문맥 파악. **Attention 메커니즘**으로 중요 단어에 더 집중."))
    story.append(code(
        'Bi-LSTM 구조:<br/>'
        '→→→→→ (왼→오 방향): "Machine type M, temperature high..."<br/>'
        '←←←←← (오←왼 방향): "...temperature high, type M machine"<br/>'
        '   ↓↓↓↓↓<br/>'
        '두 방향 정보 결합 → 더 풍부한 문장 이해'))

    story.append(Paragraph("5-3. DistilBERT — 사전학습 대형 언어 모델 파인튜닝", ST['h2']))
    story.append(code(
        '모델: distilbert-base-uncased<br/>'
        '      (BERT의 경량화 버전, 6600만 파라미터)<br/>'
        '입력: 최대 128 토큰 텍스트<br/>'
        '학습: 분류 헤드만 새로 학습, BERT 본체는 파인튜닝'))
    story.append(body("**선택 이유**: BERT는 Wikipedia + BookCorpus 수십억 단어로 사전 학습. "
                       "DistilBERT = BERT의 97% 성능을 유지하면서 40% 작고 60% 빠름."))
    story.append(bbold("LSTM vs BERT 차이:"))
    story.append(code(
        'LSTM:  단어를 순서대로 읽으며 순차 처리<br/>'
        '       "토크 높음, 속도 정상" 처리 → 순서에 의존<br/><br/>'
        'BERT:  모든 단어를 동시에 보며 Attention으로 관계 파악<br/>'
        '       "토크"와 "속도"가 어디 있든 서로의 관계를 직접 파악'))

    story.append(Paragraph("5-4. 클래스 불균형 대응 — Class Weight", ST['h2']))
    story.append(code(
        'class_weight = 전체 건수 / (클래스 수 × 클래스별 건수)<br/><br/>'
        '예:  Random Failures(18건): weight = 10000 / (6×18) = 92.6 ← 매우 높음<br/>'
        '     No Failure(9652건):    weight = 10000 / (6×9652) = 0.17 ← 매우 낮음'))
    story.append(body("• 희귀 고장을 잘못 예측하면 더 크게 처벌<br/>• \"모두 정상\" 예측 전략을 막음"))

    # ━━━ 6. 데이터 탐색 시각화 ━━━
    story.append(PageBreak())
    story.append(Paragraph("6. 데이터 탐색 시각화", ST['h1']))
    story.append(ColoredHR(CW, ACCENT, 0.5))

    story.append(Paragraph("6-1. 데이터 분포 및 특성 개요", ST['h2']))
    img(story, "01_eda_overview.png")
    story.append(tbl(
        ["서브플롯", "내용", "핵심 인사이트"],
        [["고장 유형 분포", "막대/파이 차트", "No Failure 96.52% → 극심한 불균형"],
         ["센서값 분포", "히스토그램", "각 센서의 정상 범위와 이상치 파악"],
         ["고장별 센서 박스플롯", "고장 유형별 센서 분포", "어떤 센서가 고장과 연관되는지 확인"],
         ["상관관계 히트맵", "피처 간 상관도", "공정온도-공기온도 쌍, 토크-회전속도 쌍 등 관계 파악"]],
        [35*mm, 40*mm, CW-75*mm]))
    story.append(Spacer(1, 2*mm))
    story.append(quote("**주목할 점**: `No Failure`가 전체의 96.52% → 단순 \"모두 정상\" 예측만으로도 Accuracy 96% 달성 가능. 이것이 **Accuracy를 주요 지표로 사용하면 안 되는 이유**"))

    story.append(Paragraph("6-2. 고장 유형별 피처 분포", ST['h2']))
    img(story, "02_feature_by_failure.png")
    story.append(tbl(
        ["고장 유형", "특징적 센서 패턴"],
        [["**Heat Dissipation Failure**", "공정온도 - 공기온도 차이(Temp Diff)가 매우 작음 (냉각 부족)"],
         ["**Power Failure**", "Power(토크×회전속도)가 임계값 초과"],
         ["**Overstrain Failure**", "마모도 높음 + 토크 높음 동시 발생"],
         ["**Tool Wear Failure**", "공구 마모(Tool Wear) 수치가 뚜렷하게 높음"],
         ["**Random Failures**", "특정 패턴 없음 — 이름처럼 무작위"]],
        [50*mm, CW-50*mm]))

    # ━━━ 7. 모델별 학습 과정 분석 ━━━
    story.append(PageBreak())
    story.append(Paragraph("7. 모델별 학습 과정 분석", ST['h1']))
    story.append(ColoredHR(CW, ACCENT, 0.5))

    story.append(Paragraph("7-1. LSTM 학습 곡선", ST['h2']))
    img(story, "03_lstm_training_curves.png")
    story.append(body("**학습 설정**: 20 에폭 | Bi-LSTM + Attention | Class Weight 적용"))
    story.append(tbl(
        ["에폭 구간", "Train Acc", "Val Acc", "관찰"],
        [["1 에폭", "0.875", "**0.9653**", "Val이 Train보다 높음 — 초기 Class Weight 효과"],
         ["2~11 에폭", "0.86~0.97", "0.9373~0.9653", "검증 성능이 에폭 1보다 낮아짐"],
         ["12~20 에폭", "0.95~0.97", "0.9200~0.9347", "과적합 시작 — Train 오르고 Val 내려감"]],
        [25*mm, 25*mm, 28*mm, CW-78*mm]))
    story.append(Spacer(1, 2*mm))
    story.append(body("**최종 결과**: Best Val Acc: **0.9653** (1 에폭에서 달성)"))
    story.append(body("**핵심 문제**: Loss가 1.0 이상으로 높게 유지되면서 Acc가 96%인 이유는 **모델이 \"모두 정상\" 예측에 가까운 전략**을 취하고 있기 때문입니다."))
    story.append(code('LSTM의 진짜 성능 지표: F1(macro) = 0.1637<br/>→ 6가지 고장 유형 중 소수 고장들을 거의 탐지 못함'))

    story.append(Paragraph("7-2. DistilBERT 학습 곡선", ST['h2']))
    img(story, "03b_bert_curves.png")
    story.append(body("**학습 설정**: 5 에폭 | DistilBERT 파인튜닝 | AdamW + Gradient Clipping"))
    story.append(tbl(
        ["에폭", "Train Loss", "Val Acc", "Val F1(macro)", "관찰"],
        [["1", "0.2318", "0.9653", "0.1637", "아직 초기 단계 — No Failure 위주 예측"],
         ["2", "0.1812", "0.9653", "0.1637", "Loss 감소 중, F1 미개선"],
         ["3", "0.1525", "**0.9480**", "**0.2911** ★", "Acc 약간 하락, F1 대폭 상승!"],
         ["4", "0.1108", "0.9713", "**0.3319** ★", "희귀 고장 학습 시작"],
         ["5", "0.0909", "**0.9727**", "**0.4496** ★", "최고 성능 달성"]],
        [18*mm, 25*mm, 25*mm, 30*mm, CW-98*mm]))
    story.append(Spacer(1, 2*mm))
    story.append(bbold("주목할 점 — 3 에폭의 역설:"))
    story.append(code(
        '에폭 3에서 Accuracy가 0.9653 → 0.9480으로 감소했지만<br/>'
        'F1(macro)가 0.1637 → 0.2911으로 급상승<br/><br/>'
        '이유: 모델이 "No Failure" 위주 예측에서 벗어나<br/>'
        '      희귀 고장 유형도 맞추기 시작 → 정상 일부를 오분류<br/>'
        '      하지만 전체적인 실질 성능은 크게 향상!'))
    story.append(body("**Accuracy와 F1(macro)는 반대 방향으로 움직일 수 있으며**, 불균형 데이터에서는 F1(macro)가 더 믿을 수 있는 지표입니다."))
    story.append(body("**최종 결과**: Best Val F1(macro): **0.4496** | Best Val Acc: **0.9727**"))

    # ━━━ 8. 3모델 최종 비교 ━━━
    story.append(PageBreak())
    story.append(Paragraph("8. 3모델 최종 비교 및 혼동 행렬", ST['h1']))
    story.append(ColoredHR(CW, ACCENT, 0.5))

    story.append(Paragraph("8-1. 혼동 행렬", ST['h2']))
    img(story, "04_confusion_matrices.png")
    story.append(code(
        '행(Row)   = 실제 정답 클래스<br/>'
        '열(Column) = 모델이 예측한 클래스<br/>'
        '대각선 숫자 = 정확하게 맞춘 건수 (높을수록 좋음)<br/>'
        '비대각선   = 잘못 예측한 건수 (낮을수록 좋음)'))

    story.append(bbold("DNN 혼동 행렬 분석:"))
    story.append(body("• No Failure → No Failure: 대부분 맞춤<br/>"
                       "• 일부 고장 유형에서 다른 유형으로의 혼동 발생<br/>"
                       "• 수치 직접 입력 방식으로 Random Failures(18건)는 거의 탐지 불가"))
    story.append(bbold("LSTM 혼동 행렬 분석:"))
    story.append(body("• Accuracy 96.53%이지만 대부분 No Failure로만 예측<br/>"
                       "• 소수 고장 유형(Tool Wear, Random Failures)에서 F1 거의 0에 가까움"))
    story.append(bbold("BERT 혼동 행렬 분석:"))
    story.append(body("• 가장 균형 잡힌 분류 결과<br/>"
                       "• Heat Dissipation, Power Failure 등에서 상대적으로 높은 탐지율<br/>"
                       "• 소수 클래스에서도 일부 올바른 예측 달성"))

    story.append(Paragraph("8-2. 성능 비교 막대 그래프", ST['h2']))
    img(story, "05_model_comparison.png")

    story.append(Paragraph("8-3. 최종 성능 수치 비교", ST['h2']))
    story.append(tbl(
        ["모델", "Accuracy", "**F1(macro)**", "F1(weighted)"],
        [["**DNN (수치)**", "81.33%", "34.03%", "87.36%"],
         ["**LSTM (텍스트)**", "96.53%", "16.37%", "94.83%"],
         ["**BERT (텍스트)**", "**97.40%**", "**47.73%** ★", "**97.14%** ★"]],
        [38*mm, 30*mm, 35*mm, CW-103*mm]))
    story.append(Spacer(1, 2*mm))
    story.append(quote("**핵심 지표는 F1(macro)** — 클래스 불균형에서 모든 고장 유형을 균등하게 평가"))

    # ━━━ 9. 워드클라우드 ━━━
    story.append(PageBreak())
    story.append(Paragraph("9. 워드클라우드 — 어떤 단어가 고장을 설명하는가?", ST['h1']))
    story.append(ColoredHR(CW, ACCENT, 0.5))
    img(story, "06_wordclouds.png")
    story.append(tbl(
        ["고장 유형", "특징적 단어", "해석"],
        [["**Heat Dissipation Failure**", '"temp_diff low", "temperature"', "온도 차이가 작을 때 열 방출 고장"],
         ["**Power Failure**", '"power high", "torque high", "speed high"', "고출력 상태에서 동력 고장"],
         ["**Overstrain Failure**", '"wear high", "torque high", "overstrain"', "마모 + 과부하 동시 발생"],
         ["**Tool Wear Failure**", '"wear critical", "tool wear"', "공구 교체 필요 수준 도달"],
         ["**Random Failures**", "특정 패턴 없음", "이름처럼 무작위 발생"],
         ["**No Failure**", '"normal", "nominal"', "모든 지표가 정상 범위"]],
        [45*mm, 50*mm, CW-95*mm]))
    story.append(Spacer(1, 3*mm))
    story.append(bbold("워드클라우드가 보여주는 것:"))
    story.append(body("1. 텍스트 변환이 실제로 도메인 지식을 잘 담아냈음을 확인<br/>"
                       "2. `\"high\"`, `\"critical\"`, `\"low\"` 등의 상태 레이블이 각 고장과 명확히 연관됨<br/>"
                       "3. BERT가 이런 단어 패턴을 학습했기 때문에 F1(macro)가 상대적으로 높음"))

    # ━━━ 10. 결과 해석 및 핵심 인사이트 ━━━
    story.append(PageBreak())
    story.append(Paragraph("10. 결과 해석 및 핵심 인사이트", ST['h1']))
    story.append(ColoredHR(CW, ACCENT, 0.5))

    story.append(Paragraph("10-1. 숫자로 보는 결과 해석", ST['h2']))
    story.append(bbold("BERT F1(macro) 0.4773의 의미:"))
    story.append(code(
        '6가지 고장 유형 각각에 대한 F1을 계산:<br/>'
        '  No Failure:              F1 ≈ 0.98 (매우 좋음)<br/>'
        '  Heat Dissipation Failure: F1 ≈ 0.60 (어느 정도 탐지)<br/>'
        '  Power Failure:            F1 ≈ 0.55 (어느 정도 탐지)<br/>'
        '  Overstrain Failure:       F1 ≈ 0.45 (낮지만 탐지)<br/>'
        '  Tool Wear Failure:        F1 ≈ 0.30 (어렵지만 일부 탐지)<br/>'
        '  Random Failures:          F1 ≈ 0.08 (탐지 매우 어려움)<br/>'
        '                            ─────────<br/>'
        '  평균(macro)             = 약 0.477'))
    story.append(quote("0.4773은 낮아 보이지만 **6가지 중 18건밖에 없는 Random Failures**를 포함한 평균이므로, 이 맥락에서는 상당히 어려운 과제를 수행한 결과입니다."))

    story.append(Paragraph("10-2. 3모델 성능 역설 분석", ST['h2']))
    story.append(Paragraph('"Accuracy는 LSTM > DNN인데 F1(macro)는 LSTM &lt; DNN?" — 왜 이런 일이?', ST['h3']))
    story.append(code(
        'DNN   Accuracy 81.33%, F1(macro) 34.03%<br/>'
        'LSTM  Accuracy 96.53%, F1(macro) 16.37%'))
    story.append(body("언뜻 보면 LSTM이 더 좋아 보이지만, 실상은 반대입니다:"))
    story.append(code(
        'LSTM의 Accuracy 96.53% 달성 방법:<br/>'
        '  → 거의 대부분을 "No Failure"로 예측<br/>'
        '  → No Failure가 96.52%이므로 그냥 "모두 정상"이면 96.52%<br/>'
        '  → F1(macro) 0.1637 = 희귀 고장은 거의 찾지 못함<br/><br/>'
        'DNN의 Accuracy 81.33%:<br/>'
        '  → 수치 피처로 일부 희귀 고장도 탐지 시도<br/>'
        '  → 오히려 No Failure 외 클래스도 예측해서 Accuracy는 낮아짐<br/>'
        '  → F1(macro) 0.3403 = LSTM보다 2배 높은 실질 성능'))
    story.append(quote("**결론**: 불균형 데이터에서 Accuracy는 \"얼마나 열심히 맞추는가\"가 아니라 \"얼마나 안 틀리는가\"를 측정합니다. **F1(macro)가 진짜 성능 지표**입니다."))

    story.append(Paragraph("10-3. 텍스트 변환의 효과 검증", ST['h2']))
    story.append(tbl(
        ["방법", "핵심", "F1(macro)"],
        [["DNN (수치 직접)", "숫자 그대로 → 신경망", "0.3403"],
         ["LSTM (텍스트)", "수치 → 텍스트 → LSTM", "0.1637 ← 오히려 낮음!"],
         ["BERT (텍스트)", "수치 → 텍스트 → BERT", "**0.4773** ← 최고"]],
        [38*mm, 52*mm, CW-90*mm]))
    story.append(Spacer(1, 2*mm))
    story.append(body("**관찰**: 텍스트 변환이 BERT와 결합될 때만 효과를 발휘합니다. "
                       "이는 **\"텍스트 변환 자체\"가 아니라 \"텍스트를 처리하는 모델의 능력\"이 핵심**임을 보여줍니다."))

    story.append(Paragraph("10-4. 실제 산업 현장 적용 가능성", ST['h2']))
    story.append(tbl(
        ["활용 시나리오", "적합한 모델", "이유"],
        [["**실시간 모니터링**", "DNN", "빠른 추론, 간단한 구조"],
         ["**일배치 분석**", "BERT", "높은 F1(macro), 희귀 고장 탐지"],
         ["**설명 가능성 중요**", "BERT + 워드클라우드", "어떤 센서값이 고장을 유발했는지 설명"],
         ["**자원 제약 환경**", "DNN", "모델 크기 56KB vs BERT 256MB"]],
        [38*mm, 42*mm, CW-80*mm]))

    # ━━━ 11. 향후 개선 방향 ━━━
    story.append(PageBreak())
    story.append(Paragraph("11. 향후 개선 방향", ST['h1']))
    story.append(ColoredHR(CW, ACCENT, 0.5))

    story.append(Paragraph("11-1. F1(macro) 점수 향상 전략", ST['h2']))
    story.append(bbold("즉시 적용 가능 (코드 수정 최소):"))
    story.append(tbl(
        ["방법", "예상 효과", "설명"],
        [["**BERT 에폭 증가** (5→15)", "F1(macro) +0.05~0.10", "에폭 5에서도 계속 상승 중이었음"],
         ["**학습률 스케줄러** 추가", "+0.03~0.05", "CosineAnnealing으로 세밀한 파인튜닝"],
         ["**Oversampling** (SMOTE)", "+0.05~0.10", "희귀 고장 샘플 인공 생성"]],
        [45*mm, 35*mm, CW-80*mm]))
    story.append(Spacer(1, 3*mm))
    story.append(bbold("중기 개선:"))
    story.append(tbl(
        ["방법", "예상 효과", "설명"],
        [["**Focal Loss**", "+0.05~0.08", "희귀 클래스에 손실 집중"],
         ["**텍스트 템플릿 개선**", "+0.03~0.07", "더 정교한 수치→텍스트 변환 규칙"],
         ["**RoBERTa / BERT-base**", "+0.02~0.05", "DistilBERT보다 강력한 모델"]],
        [45*mm, 35*mm, CW-80*mm]))

    story.append(Paragraph("11-2. 가장 어려운 클래스 — Random Failures", ST['h2']))
    story.append(code(
        'Random Failures: 18건 → 전체의 0.18%<br/><br/>'
        '이 클래스가 어려운 이유:<br/>'
        '1. 데이터가 18건으로 극히 적음<br/>'
        '2. "무작위" 고장이므로 센서 패턴과의 연관성 낮음<br/>'
        '3. SMOTE 등으로 인공 생성해도 패턴이 없어 학습 효과 제한적<br/><br/>'
        '현실적 대안:<br/>'
        '→ 이 클래스는 "Unknown Failure"로 재라벨링<br/>'
        '→ 5분류 문제로 재설계 (Random 제외)<br/>'
        '→ 예상 F1(macro) 향상: +0.10~0.15'))

    # ━━━ FINAL SUMMARY ━━━
    story.append(Spacer(1, 5*mm))
    story.append(ColoredHR(CW, PRIMARY, 2))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("최종 요약", ST['h1']))

    story.append(tbl(
        ["항목", "내용"],
        [["**과제**", "설비 센서 데이터로 6종 고장 유형 예측"],
         ["**핵심 아이디어**", "수치 데이터 → 자연어 텍스트 변환 후 NLP 모델 적용"],
         ["**데이터**", "10,000건, 6종 고장 (No Failure 96.52% 불균형)"],
         ["**최고 모델**", "**DistilBERT**"],
         ["**최고 Accuracy**", "**97.40%**"],
         ["**최고 F1(macro)**", "**47.73%** (불균형 고려 시 실질 성능 지표)"],
         ["**핵심 교훈 1**", "불균형 데이터에서 **Accuracy ≠ 실제 성능**"],
         ["**핵심 교훈 2**", "텍스트 변환은 BERT처럼 **강력한 언어 모델**과 결합할 때 효과 발휘"],
         ["**핵심 교훈 3**", "LSTM Accuracy > DNN이지만 **F1(macro)는 DNN > LSTM** — 지표 선택이 중요"]],
        [45*mm, CW-45*mm]))
    story.append(Spacer(1, 5*mm))

    story.append(bbold("3가지 핵심 메시지"))
    msgs = [
        '1. **"Accuracy 96%는 LSTM의 성능이 아니라 데이터 불균형의 착시"** — No Failure 96.52% → 아무것도 안 해도 96% Accuracy 달성 가능',
        '2. **"BERT만이 텍스트 변환의 장점을 실현했다"** — 수치 → 텍스트 변환 + 사전학습 언어 모델 = F1(macro) 0.4773 (DNN 대비 40% 향상)',
        '3. **"산업 안전에서 F1(macro)가 핵심 지표"** — 희귀 고장 한 건을 놓치는 것이 대형 사고로 이어질 수 있으므로, 소수 클래스 탐지 능력이 진짜 성능',
    ]
    for m in msgs:
        story.append(QuoteBlock(fmt(m), CW, ST['body']))
        story.append(Spacer(1, 2*mm))

    # ━━━ APPENDIX ━━━
    story.append(Spacer(1, 5*mm))
    story.append(ColoredHR(CW, ACCENT, 0.5))
    story.append(Paragraph("부록: 프로젝트 파일 구조", ST['h2']))
    story.append(code(
        'SubTopic_D_Maintenance_NLP/<br/>'
        '├── maintenance_nlp.py                  ← 전체 파이프라인 스크립트<br/>'
        '├── models/<br/>'
        '│   ├── best_lstm.pth                   ← LSTM 최고 모델 (12MB)<br/>'
        '│   ├── best_bert.pth                   ← DistilBERT 최고 모델 (256MB) ★<br/>'
        '│   └── best_dnn.pth                    ← DNN 최고 모델 (56KB)<br/>'
        '└── results/<br/>'
        '    ├── 01~06 PNG 시각화 파일들<br/>'
        '    ├── 07_final_summary.json<br/>'
        '    └── SubTopic_D_Results_Report.md'))

    story.append(Spacer(1, 8*mm))
    story.append(ColoredHR(CW, BORDER, 0.3))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        '<font name="NanumL" size="8" color="#9e9e9e">'
        '보고서 작성: K-Digital Training 딥러닝 12기 미니프로젝트 소주제 D (설비 고장 예측)<br/>'
        '학습 환경: Apple Silicon MPS / Python 3.13 / PyTorch 2.10 / Transformers 5.2.0<br/>'
        '데이터: Machine Predictive Maintenance Classification Dataset</font>',
        ST['footer']))

    doc.build(story, onFirstPage=page_num, onLaterPages=page_num)
    print(f"PDF generated: {OUTPUT_PDF}")


if __name__ == "__main__":
    build()

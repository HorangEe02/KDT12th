#!/usr/bin/env python3
"""Markdown report to PDF converter for SubTopic_C PCB Detection results."""

import os, re
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, Flowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PDF = os.path.join(BASE_DIR, "PCB_결함_탐지_결과보고서.pdf")

pdfmetrics.registerFont(TTFont("NanumR", "/Users/yeong/Library/Fonts/NanumSquare_acR.ttf"))
pdfmetrics.registerFont(TTFont("NanumB", "/Users/yeong/Library/Fonts/NanumSquare_acB.ttf"))
pdfmetrics.registerFont(TTFont("NanumEB", "/Users/yeong/Library/Fonts/NanumSquare_acEB.ttf"))
pdfmetrics.registerFont(TTFont("NanumL", "/Users/yeong/Library/Fonts/NanumSquare_acL.ttf"))
pdfmetrics.registerFont(TTFont("D2Coding", "/Users/yeong/Library/Fonts/D2Coding.ttc", subfontIndex=0))

PRIMARY = HexColor("#1a237e")
ACCENT = HexColor("#0d47a1")
LIGHT_BG = HexColor("#e8eaf6")
CODE_BG = HexColor("#f5f5f5")
TABLE_HEADER = HexColor("#283593")
TABLE_ALT = HexColor("#e8eaf6")
BORDER = HexColor("#bdbdbd")
QUOTE_BAR = HexColor("#1565c0")
QUOTE_BG = HexColor("#e3f2fd")

PAGE_W, PAGE_H = A4
ML, MR, MT, MB = 20*mm, 20*mm, 22*mm, 22*mm
CW = PAGE_W - ML - MR

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

class ColoredHR(Flowable):
    def __init__(self, width, color=PRIMARY, thickness=1):
        Flowable.__init__(self); self.width=width; self.color=color; self.thickness=thickness; self.height=thickness+2*mm
    def draw(self):
        self.canv.setStrokeColor(self.color); self.canv.setLineWidth(self.thickness)
        self.canv.line(0, self.thickness/2, self.width, self.thickness/2)

class QuoteBlock(Flowable):
    def __init__(self, text, width, style):
        Flowable.__init__(self); self.text=text; self._width=width; self.style=style
        p=Paragraph(text,style); _,ph=p.wrap(width-12*mm,10000); self.height=ph+6*mm
    def draw(self):
        self.canv.setFillColor(QUOTE_BG); self.canv.roundRect(0,0,self._width,self.height,2,fill=1,stroke=0)
        self.canv.setFillColor(QUOTE_BAR); self.canv.rect(0,0,3,self.height,fill=1,stroke=0)
        p=Paragraph(self.text,self.style); p.wrap(self._width-12*mm,10000); p.drawOn(self.canv,8*mm,3*mm)

def fmt(t):
    t=re.sub(r'\*\*\*(.+?)\*\*\*',r'<font name="NanumEB"><i>\1</i></font>',t)
    t=re.sub(r'\*\*(.+?)\*\*',r'<font name="NanumB">\1</font>',t)
    t=re.sub(r'\*(.+?)\*',r'<i>\1</i>',t)
    t=re.sub(r'`(.+?)`',r'<font name="D2Coding" size="8" color="#c62828">\1</font>',t)
    t=re.sub(r'\[(.+?)\]\(.+?\)',r'\1',t)
    t=t.replace('★','<font color="#f9a825">★</font>')
    return t

def tbl(headers, rows, widths=None):
    hc=[Paragraph(fmt(h),ST['th']) for h in headers]
    dr=[]
    for row in rows:
        cells=[Paragraph(fmt(c.strip()) if c else "",ST['tcl'] if i==0 else ST['tc']) for i,c in enumerate(row)]
        dr.append(cells)
    data=[hc]+dr
    if widths is None: widths=[CW/len(headers)]*len(headers)
    t=Table(data,colWidths=widths,repeatRows=1)
    ts=[('BACKGROUND',(0,0),(-1,0),TABLE_HEADER),('TEXTCOLOR',(0,0),(-1,0),white),
        ('GRID',(0,0),(-1,-1),0.5,BORDER),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('TOPPADDING',(0,0),(-1,0),6),('BOTTOMPADDING',(0,0),(-1,0),6),
        ('TOPPADDING',(0,1),(-1,-1),4),('BOTTOMPADDING',(0,1),(-1,-1),4),
        ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6)]
    for i in range(1,len(data)):
        if i%2==0: ts.append(('BACKGROUND',(0,i),(-1,i),TABLE_ALT))
    t.setStyle(TableStyle(ts)); return t

def add_img(story, fn, max_w=CW, max_h=160*mm):
    path=os.path.join(BASE_DIR,fn)
    if not os.path.exists(path): story.append(Paragraph(f"[이미지 없음: {fn}]",ST['body'])); return
    pi=PILImage.open(path); iw,ih=pi.size; r=min(max_w/iw,max_h/ih)
    story.append(Image(path,width=iw*r,height=ih*r)); story.append(Spacer(1,3*mm))

def body(t): return Paragraph(fmt(t),ST['body'])
def bbold(t): return Paragraph(fmt(t),ST['body_bold'])
def code(t): return Paragraph(f'<font name="D2Coding" size="8.5">{t}</font>',ST['code'])
def quote(t): return QuoteBlock(fmt(t),CW,ST['body'])

def page_num(canvas, doc):
    canvas.saveState(); canvas.setFont('NanumL',8); canvas.setFillColor(HexColor("#9e9e9e"))
    canvas.drawCentredString(PAGE_W/2,12*mm,f"— {canvas.getPageNumber()} —")
    canvas.setStrokeColor(LIGHT_BG); canvas.setLineWidth(0.5)
    canvas.line(ML,PAGE_H-MT+5*mm,PAGE_W-MR,PAGE_H-MT+5*mm); canvas.restoreState()

def build():
    doc=SimpleDocTemplate(OUTPUT_PDF,pagesize=A4,leftMargin=ML,rightMargin=MR,topMargin=MT,bottomMargin=MB,
                          title="PCB 기판 결함 자동 탐지 결과 보고서",author="K-Digital Training 딥러닝 12기")
    story=[]

    # ━━━ COVER ━━━
    story.append(Spacer(1,15*mm))
    story.append(Paragraph("소주제 C",ST['subtitle']))
    story.append(Paragraph("PCB 기판 결함 자동 탐지<br/>결과 보고서",ST['title']))
    story.append(Spacer(1,4*mm))
    story.append(ColoredHR(CW,PRIMARY,2))
    story.append(Spacer(1,4*mm))

    meta=[["프로젝트","AI 기반 스마트 팩토리 품질관리 시스템"],
          ["작성일","2026-04-02"],
          ["모델","Ultralytics YOLOv8 (Nano / Small / Medium 비교)"],
          ["실행 환경","Apple M4 Pro CPU, PyTorch 2.10.0"],
          ["데이터셋","PCB Defects Dataset (693장, 6종 결함)"]]
    mc=[[Paragraph(f'<font name="NanumB" color="#1a237e">{r[0]}</font>',ST['body']),
         Paragraph(r[1],ST['body'])] for r in meta]
    mt=Table(mc,colWidths=[35*mm,CW-35*mm])
    mt.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),2),
                            ('BOTTOMPADDING',(0,0),(-1,-1),2),('LINEBELOW',(0,0),(-1,-1),0.3,BORDER)]))
    story.append(mt); story.append(Spacer(1,8*mm))

    # ━━━ TOC ━━━
    story.append(Paragraph("목차",ST['h1']))
    for item in ["1. 프로젝트 개요","2. 용어 설명","3. 데이터 탐색 (EDA)","4. 데이터 전처리",
                  "5. 모델 학습 — YOLOv8s (메인 모델)","6. 탐지 결과 시각화",
                  "7. 모델 크기별 비교 실험","8. 최종 결과 및 결론"]:
        story.append(Paragraph(item,ST['toc']))
    story.append(PageBreak())

    # ━━━ 1. 프로젝트 개요 ━━━
    story.append(Paragraph("1. 프로젝트 개요",ST['h1']))
    story.append(ColoredHR(CW,ACCENT,0.5))

    story.append(Paragraph("1.1 배경 및 목적",ST['h2']))
    story.append(body("PCB(Printed Circuit Board, 인쇄 회로 기판)는 모든 전자 제품의 핵심 부품입니다. 스마트폰, 노트북, 자동차 전자장치 등 거의 모든 전자기기에 PCB가 들어갑니다. PCB에 결함이 있으면 제품 오작동이나 안전 문제로 이어질 수 있어, 제조 과정에서 결함을 빠르고 정확하게 탐지하는 것이 매우 중요합니다."))
    story.append(body("기존에는 사람이 현미경으로 PCB를 하나씩 확인했지만, 이 방법은 느리고 실수가 발생할 수 있습니다. 본 프로젝트에서는 **딥러닝 기반 객체 탐지 모델(YOLOv8)**을 사용하여 PCB 결함을 자동으로 탐지하는 시스템을 구축했습니다."))

    story.append(Paragraph("1.2 사용 기술",ST['h2']))
    story.append(tbl(["항목","내용"],
        [["**딥러닝 프레임워크**","PyTorch 2.10.0"],
         ["**객체 탐지 모델**","Ultralytics YOLOv8 (v8.4.32)"],
         ["**실행 환경**","Apple M4 Pro (CPU 학습)"],
         ["**데이터셋**","PCB Defects Dataset (693장, 6종 결함)"],
         ["**재현성**","Random Seed 42 고정"]],
        [40*mm,CW-40*mm]))

    story.append(Paragraph("1.3 파이프라인 구조",ST['h2']))
    story.append(body("전체 실험은 8단계 파이프라인으로 구성됩니다:"))
    story.append(code(
        '[1] 환경 설정 → [2] 데이터 탐색(EDA) → [3] XML→YOLO 변환<br/>'
        '→ [4] YOLOv8s 학습(50 epochs) → [5] 그래프 수집<br/>'
        '→ [6] 탐지 결과 시각화 → [7] 모델 비교(n/s/m) → [8] 최종 결과 저장'))

    # ━━━ 2. 용어 설명 ━━━
    story.append(Paragraph("2. 용어 설명",ST['h1']))
    story.append(ColoredHR(CW,ACCENT,0.5))

    story.append(Paragraph("2.1 학습 관련 용어",ST['h2']))
    story.append(tbl(["용어","의미","쉬운 설명"],
        [["**Epoch**","전체 학습 데이터를 한 번 모두 학습하는 단위","교과서를 처음부터 끝까지 1번 읽는 것 = 1 Epoch"],
         ["**Batch Size**","한 번에 모델에 넣는 이미지 수 (본 실험: 16)","한 번에 16장의 사진을 보고 학습"],
         ["**GPU_mem**","학습 시 사용한 GPU 메모리 (0G = CPU 사용)","본 실험은 CPU로 진행하여 0G 표시"],
         ["**Instances**","한 배치에 포함된 객체(결함) 수","16장 이미지 안에 총 몇 개의 결함이 있는지"],
         ["**Size**","입력 이미지 크기 (본 실험: 640x640)","모든 이미지를 640x640 픽셀로 통일하여 학습"],
         ["**Params**","모델의 학습 가능한 매개변수 수",'모델의 "두뇌 크기" — 클수록 복잡한 패턴 학습 가능']],
        [25*mm,50*mm,CW-75*mm]))

    story.append(Paragraph("2.2 손실 함수 (Loss) 용어",ST['h2']))
    story.append(body("손실(Loss)은 모델이 얼마나 틀렸는지를 나타내는 숫자입니다. **낮을수록 좋습니다.**"))
    story.append(tbl(["용어","의미","쉬운 설명"],
        [["**box_loss**","바운딩 박스 위치 손실","결함의 위치를 얼마나 정확하게 잡았는지 (낮을수록 정확)"],
         ["**cls_loss**","분류 손실","결함의 종류를 얼마나 정확하게 맞혔는지 (낮을수록 정확)"],
         ["**dfl_loss**","분포 초점 손실 (Distribution Focal Loss)","바운딩 박스 경계를 더 정밀하게 맞추기 위한 보조 손실"]],
        [25*mm,50*mm,CW-75*mm]))
    story.append(quote('**비유**: 시험 점수에 비유하면, box_loss는 "위치 맞히기 시험", cls_loss는 "종류 맞히기 시험"에서 틀린 정도입니다. 학습이 진행될수록 이 값들이 줄어들어야 합니다.'))

    story.append(Paragraph("2.3 성능 평가 지표",ST['h2']))
    story.append(tbl(["용어","의미","쉬운 설명"],
        [["**Precision (정밀도)**",'모델이 "결함이다"라고 한 것 중 진짜 결함의 비율','"결함이라고 했을 때 맞는 확률" — 높을수록 오탐이 적음'],
         ["**Recall (재현율)**","실제 결함 중 모델이 찾아낸 비율",'"실제 결함을 얼마나 놓치지 않고 찾는지" — 높을수록 누락이 적음'],
         ["**mAP@0.5**","IoU 50% 이상일 때의 평균 정밀도","위치를 절반 이상 맞혔을 때 기준 종합 점수 (0~1)"],
         ["**mAP@0.5:0.95**","IoU 50%~95%까지 다양한 기준의 평균 정밀도","더 엄격한 기준까지 포함한 종합 점수"],
         ["**FPS**","초당 처리 이미지 수","1초에 몇 장의 이미지를 검사할 수 있는지"],
         ["**IoU**","Intersection over Union","예측 박스와 실제 박스가 얼마나 겹치는지의 비율"]],
        [30*mm,45*mm,CW-75*mm]))
    story.append(quote('**mAP 비유**: mAP@0.5는 "대략 맞으면 정답으로 인정하는 시험", mAP@0.5:0.95는 "아주 정확해야 정답으로 인정하는 시험"입니다.'))

    # ━━━ 3. 데이터 탐색 ━━━
    story.append(PageBreak())
    story.append(Paragraph("3. 데이터 탐색 (EDA)",ST['h1']))
    story.append(ColoredHR(CW,ACCENT,0.5))

    story.append(Paragraph("3.1 데이터셋 구성",ST['h2']))
    story.append(body("총 **693장**의 PCB 결함 이미지와 **2,953개**의 바운딩 박스 어노테이션으로 구성됩니다."))
    story.append(bbold("6가지 결함 유형:"))
    story.append(tbl(["결함 유형","한글 의미","이미지 수","설명"],
        [["Missing_hole","구멍 누락","115장","있어야 할 구멍이 빠진 결함"],
         ["Mouse_bite","마우스 바이트","115장","회로 가장자리가 불규칙하게 잘려나간 결함"],
         ["Open_circuit","단선(오픈)","116장","이어져야 할 회로가 끊어진 결함"],
         ["Short","단락(쇼트)","116장","연결되지 않아야 할 회로가 붙은 결함"],
         ["Spur","스퍼(돌기)","115장","회로에서 불필요한 돌출부가 있는 결함"],
         ["Spurious_copper","잉여 구리","116장","불필요한 구리가 남아있는 결함"]],
        [30*mm,28*mm,22*mm,CW-80*mm]))

    story.append(Paragraph("3.2 데이터 분포 시각화",ST['h2']))
    add_img(story,"01_data_distribution.png")
    story.append(body("**분석**: 6개 클래스의 이미지 수가 115~116장으로 매우 균일합니다. 이는 모델 학습에 매우 이상적인 조건으로, 특정 결함에 편향되지 않고 모든 유형을 골고루 학습할 수 있습니다. 바운딩 박스 크기 분포도 다양하게 분포하여, 모델이 작은 결함부터 큰 결함까지 모두 탐지하도록 학습됩니다."))

    story.append(Paragraph("3.3 결함 샘플 이미지",ST['h2']))
    add_img(story,"02_sample_images.png")
    story.append(body("각 결함 유형별 대표 이미지를 Ground Truth 바운딩 박스와 함께 표시했습니다. 결함이 매우 미세하여 육안으로도 구분이 어려운 경우가 많으며, 이것이 바로 AI 자동 탐지가 필요한 이유입니다."))

    # ━━━ 4. 데이터 전처리 ━━━
    story.append(PageBreak())
    story.append(Paragraph("4. 데이터 전처리",ST['h1']))
    story.append(ColoredHR(CW,ACCENT,0.5))

    story.append(Paragraph("4.1 데이터 형식 변환 (XML → YOLO)",ST['h2']))
    story.append(body("원본 데이터는 Pascal VOC XML 형식으로 제공되었으나, YOLOv8은 자체 텍스트 형식을 사용합니다:"))
    story.append(code(
        '[XML 형식]                       [YOLO 형식]<br/>'
        '&lt;xmin&gt;100&lt;/xmin&gt;                 0 0.5 0.5 0.2 0.3<br/>'
        '&lt;ymin&gt;200&lt;/ymin&gt;       →         (클래스ID x중심 y중심 너비 높이)<br/>'
        '&lt;xmax&gt;300&lt;/xmax&gt;                 모두 0~1 사이로 정규화<br/>'
        '&lt;ymax&gt;500&lt;/ymax&gt;'))

    story.append(Paragraph("4.2 데이터 분할",ST['h2']))
    story.append(tbl(["분할","이미지 수","비율","용도"],
        [["**Train (학습)**","485장","70%","모델 학습에 사용"],
         ["**Validation (검증)**","138장","20%","학습 중 성능 모니터링"],
         ["**Test (평가)**","70장","10%","최종 성능 평가 (학습에 미사용)"]],
        [30*mm,25*mm,18*mm,CW-73*mm]))

    story.append(Paragraph("4.3 라벨 변환 검증",ST['h2']))
    add_img(story,"03_label_verification.png")
    story.append(body("XML에서 YOLO 형식으로 변환한 라벨이 올바르게 적용되었는지 시각적으로 확인했습니다. 변환된 바운딩 박스가 실제 결함 위치와 정확히 일치하며, 데이터 전처리 과정에 오류가 없음을 확인했습니다."))

    # ━━━ 5. 모델 학습 ━━━
    story.append(PageBreak())
    story.append(Paragraph("5. 모델 학습 — YOLOv8s (메인 모델)",ST['h1']))
    story.append(ColoredHR(CW,ACCENT,0.5))

    story.append(Paragraph("5.1 YOLOv8이란?",ST['h2']))
    story.append(body("**YOLO (You Only Look Once)**는 이미지에서 객체의 위치와 종류를 동시에 찾는 딥러닝 모델입니다. "
                       "\"한 번만 보면 된다\"는 이름처럼, 이미지를 한 번만 처리하여 빠르게 결과를 얻을 수 있습니다. "
                       "YOLOv8은 2023년 Ultralytics에서 발표한 최신 버전으로, 정확도와 속도 모두 크게 향상되었습니다."))

    story.append(Paragraph("5.2 왜 YOLOv8을 선택했는가?",ST['h2']))
    story.append(tbl(["선택 이유","설명"],
        [["**실시간 탐지 가능**","제조 라인에서 빠른 검사가 필요하므로 속도가 빠른 모델이 필수"],
         ["**높은 정확도**","최신 YOLO 버전으로 소형 객체 탐지 성능이 우수"],
         ["**사전학습 활용**","COCO 데이터셋으로 사전학습된 모델을 전이학습하여 적은 데이터로도 높은 성능 달성"],
         ["**다양한 크기 제공**","Nano/Small/Medium 등 다양한 모델 크기를 제공하여 정확도-속도 트레이드오프 분석 가능"]],
        [38*mm,CW-38*mm]))

    story.append(Paragraph("5.3 학습 설정",ST['h2']))
    story.append(tbl(["설정 항목","값","설명"],
        [["**모델**","YOLOv8s (Small)","11.1M 파라미터, 정확도와 속도의 균형"],
         ["**Epoch**","50","전체 데이터를 50번 반복 학습"],
         ["**이미지 크기**","640x640","모든 이미지를 통일된 크기로 리사이즈"],
         ["**배치 크기**","16","한 번에 16장씩 학습"],
         ["**옵티마이저**","Adam","학습률을 자동 조절하는 최적화 알고리즘"],
         ["**학습률**","0.001 → 0.01*lr0","처음엔 크게, 점점 작게 (Cosine Annealing)"],
         ["**조기 종료**","10 Epoch","10번 연속 성능 개선 없으면 학습 중단"],
         ["**데이터 증강**","활성화","이미지 회전, 색상 변환 등으로 데이터 다양성 확보"],
         ["**사전학습**","COCO 데이터셋","일반 객체 인식 능력을 PCB 결함 탐지로 전이"]],
        [28*mm,35*mm,CW-63*mm]))

    story.append(Paragraph("5.4 학습 과정 분석",ST['h2']))
    add_img(story,"04_training_curves.png")
    story.append(bbold("학습 곡선 해석:"))
    story.append(body("1. **손실(Loss) 그래프** (값이 내려가야 좋음):<br/>"
                       "• `train/box_loss`: 3.327 → 1.372 (약 **59% 감소**) — 결함 위치를 점점 정확하게 예측<br/>"
                       "• `train/cls_loss`: 7.075 → 0.648 (약 **91% 감소**) — 결함 종류 구분이 크게 향상<br/>"
                       "• `train/dfl_loss`: 1.442 → 0.878 (약 **39% 감소**) — 바운딩 박스 경계가 더 정밀해짐"))
    story.append(body("2. **성능 지표 그래프** (값이 올라가야 좋음):<br/>"
                       "• `mAP@0.5`: 거의 0 → **0.942** — 초기에는 아무것도 못 찾다가 학습 후 94% 이상 정확도 달성<br/>"
                       "• `Precision`: 0 → **0.956** — 모델이 결함이라고 판단한 것의 95.6%가 실제 결함<br/>"
                       "• `Recall`: 0 → **0.911** — 실제 결함의 91.1%를 성공적으로 탐지"))
    story.append(body("3. **학습 안정성**: Epoch 20 이후 성능이 안정적으로 수렴하여, 50 Epoch 학습이 적절했음을 확인합니다."))

    story.append(Paragraph("5.5 혼동 행렬 (Confusion Matrix)",ST['h2']))
    add_img(story,"05_confusion_matrix.png")
    story.append(body("**분석**:<br/>"
                       "• `missing_hole`(구멍 누락)은 가장 높은 정확도를 보이며, 거의 완벽하게 탐지됩니다.<br/>"
                       "• `mouse_bite`(마우스 바이트)는 상대적으로 탐지가 어려운 결함으로, 다른 결함과 혼동되는 경우가 일부 있습니다.<br/>"
                       "• 전반적으로 대부분의 결함이 높은 정확도로 올바르게 분류되고 있습니다."))

    story.append(Paragraph("5.6 테스트 성능 (최종 평가)",ST['h2']))
    story.append(body("학습에 전혀 사용하지 않은 **70장의 테스트 이미지**로 평가한 결과:"))
    story.append(tbl(["지표","값","의미"],
        [["**mAP@0.5**","**0.9378 (93.78%)**","결함 위치를 절반 이상 맞혔을 때 종합 정확도"],
         ["**mAP@0.5:0.95**","**0.5111 (51.11%)**","엄격한 기준에서의 종합 정확도"],
         ["**Precision**","**0.9679 (96.79%)**","결함이라고 한 것의 96.8%가 진짜 결함"],
         ["**Recall**","**0.8948 (89.48%)**","실제 결함의 89.5%를 찾아냄"]],
        [32*mm,38*mm,CW-70*mm]))
    story.append(Spacer(1,3*mm))

    story.append(bbold("클래스별 상세 성능:"))
    story.append(tbl(["결함 유형","Precision","Recall","mAP@0.5","mAP@0.5:0.95"],
        [["missing_hole","0.990","1.000","0.995","0.564"],
         ["mouse_bite","0.967","0.755","0.865","0.475"],
         ["open_circuit","0.955","0.929","0.966","0.456"],
         ["short","0.958","1.000","0.944","0.495"],
         ["spur","0.998","0.848","0.940","0.518"],
         ["spurious_copper","0.939","0.905","0.916","0.524"]],
        [32*mm,25*mm,22*mm,25*mm,CW-104*mm]))
    story.append(Spacer(1,2*mm))
    story.append(body("• `missing_hole`은 Recall 100%로 **모든 결함을 빠짐없이 탐지**했습니다.<br/>"
                       "• `short`도 Recall 100%로 매우 우수한 성능을 보입니다.<br/>"
                       "• `mouse_bite`는 Recall 75.5%로 가장 낮은데, 결함이 매우 미세하여 탐지가 어렵기 때문입니다."))

    # ━━━ 6. 탐지 결과 시각화 ━━━
    story.append(PageBreak())
    story.append(Paragraph("6. 탐지 결과 시각화",ST['h1']))
    story.append(ColoredHR(CW,ACCENT,0.5))
    add_img(story,"08_detection_results.png")
    story.append(body("테스트 이미지 8장에 대해 모델이 실제로 탐지한 결과를 시각화했습니다. "
                       "각 이미지 위에 탐지된 결함의 종류와 신뢰도(confidence)가 표시됩니다. "
                       "대부분의 결함이 정확한 위치에, 높은 신뢰도(90% 이상)로 탐지됨을 확인할 수 있습니다. "
                       "바운딩 박스가 결함 영역을 정밀하게 감싸고 있어, 실제 품질 관리 현장에 적용 가능한 수준입니다."))

    # ━━━ 7. 모델 크기별 비교 ━━━
    story.append(Paragraph("7. 모델 크기별 비교 실험",ST['h1']))
    story.append(ColoredHR(CW,ACCENT,0.5))

    story.append(Paragraph("7.1 비교 실험 설계",ST['h2']))
    story.append(body("세 가지 크기의 YOLOv8 모델을 **동일 조건(30 Epoch)**으로 학습하여 성능-속도 트레이드오프를 분석했습니다."))
    story.append(tbl(["모델","파라미터 수","GFLOPs","특징"],
        [["**YOLOv8n** (Nano)","3.0M","8.2","가장 가볍고 빠름, 정확도 상대적 낮음"],
         ["**YOLOv8s** (Small)","11.1M","28.7","정확도와 속도의 균형"],
         ["**YOLOv8m** (Medium)","25.8M","79.1","가장 정확하지만 느림"]],
        [35*mm,28*mm,22*mm,CW-85*mm]))
    story.append(quote('**파라미터 수 비유**: 파라미터 수는 모델의 "두뇌 크기"입니다. 3M(300만)은 작은 노트, 25.8M(2580만)은 백과사전에 비유할 수 있습니다.'))

    story.append(Paragraph("7.2 비교 결과",ST['h2']))
    story.append(tbl(["모델","Params","mAP@0.5","mAP@0.5:0.95","Precision","Recall","FPS"],
        [["**YOLOv8n**","3.0M","0.8359","0.4053","0.8758","0.7773","**15.4**"],
         ["**YOLOv8s**","11.1M","0.9380","0.4723","0.9481","0.8780","12.2"],
         ["**YOLOv8m**","25.8M","**0.9496**","**0.5161**","**0.9626**","**0.9178**","8.3"]],
        [25*mm,18*mm,22*mm,28*mm,22*mm,20*mm,CW-135*mm]))

    story.append(Paragraph("7.3 비교 시각화",ST['h2']))
    add_img(story,"09_model_comparison.png")

    story.append(Paragraph("7.4 상세 분석",ST['h2']))
    story.append(Paragraph("정확도 비교",ST['h3']))
    story.append(body("• **YOLOv8m이 모든 지표에서 최고 성능**: mAP@0.5 94.96%로, Nano(83.59%) 대비 **11.37%p** 높음<br/>"
                       "• **YOLOv8n → YOLOv8s** 성능 향상이 가장 큼 (83.59% → 93.80%, **+10.21%p**)<br/>"
                       "• **YOLOv8s → YOLOv8m** 성능 향상은 상대적으로 작음 (93.80% → 94.96%, +1.16%p)"))
    story.append(body("이는 모델 크기가 작을 때(Nano)는 파라미터 부족으로 PCB 결함의 세밀한 특징을 충분히 학습하지 못하지만, Small 이상에서는 대부분의 패턴을 포착할 수 있음을 의미합니다."))

    story.append(Paragraph("속도 비교",ST['h3']))
    story.append(body("• **YOLOv8n**: 15.4 FPS — 가장 빠르지만, 실시간(30 FPS) 미달<br/>"
                       "• **YOLOv8s**: 12.2 FPS — 중간 속도<br/>"
                       "• **YOLOv8m**: 8.3 FPS — 가장 느림"))
    story.append(quote("**참고**: CPU 환경에서 측정한 FPS입니다. GPU(NVIDIA) 환경에서는 모든 모델이 실시간(30+ FPS) 처리가 가능합니다."))

    story.append(Paragraph("정확도 vs 속도 트레이드오프",ST['h3']))
    story.append(body("• **속도 우선**: YOLOv8n (FPS 15.4, mAP 83.6%) — 빠른 초기 스크리닝에 적합<br/>"
                       "• **균형형**: YOLOv8s (FPS 12.2, mAP 93.8%) — 정확도와 속도의 최적 균형점<br/>"
                       "• **정확도 우선**: YOLOv8m (FPS 8.3, mAP 95.0%) — 최종 품질 검사에 적합"))

    # ━━━ 8. 최종 결과 및 결론 ━━━
    story.append(PageBreak())
    story.append(Paragraph("8. 최종 결과 및 결론",ST['h1']))
    story.append(ColoredHR(CW,ACCENT,0.5))

    story.append(Paragraph("8.1 최종 성능 요약",ST['h2']))
    story.append(bbold("메인 모델 (YOLOv8s, 50 Epoch) — 테스트 셋 기준:"))
    story.append(tbl(["지표","값"],
        [["**mAP@0.5**","**93.78%**"],["**mAP@0.5:0.95**","**51.11%**"],
         ["**Precision**","**96.79%**"],["**Recall**","**89.48%**"]],
        [40*mm,CW-40*mm]))
    story.append(Spacer(1,3*mm))
    story.append(bbold("최고 성능 모델 (YOLOv8m, 30 Epoch) — 검증 셋 기준:"))
    story.append(tbl(["지표","값"],
        [["**mAP@0.5**","**94.96%**"],["**Precision**","**96.26%**"],["**Recall**","**91.78%**"]],
        [40*mm,CW-40*mm]))

    story.append(Paragraph("8.2 주요 발견",ST['h2']))
    story.append(body("1. **높은 탐지 성능 달성**: YOLOv8s 모델이 93.78%의 mAP@0.5를 달성하여, PCB 결함의 대부분을 정확하게 탐지할 수 있음을 확인했습니다."))
    story.append(body("2. **모델 크기에 따른 성능 차이**: Nano → Small로 넘어갈 때 성능 향상이 가장 크고(+10.2%p), Small → Medium은 상대적으로 작은 향상(+1.2%p)을 보여, **YOLOv8s가 가성비가 가장 좋은 모델**입니다."))
    story.append(body("3. **결함 유형별 난이도 차이**: `missing_hole`과 `short`는 거의 완벽하게 탐지되지만, `mouse_bite`는 미세한 특징으로 인해 탐지 난이도가 높습니다."))
    story.append(body("4. **전이학습의 효과**: COCO 데이터셋으로 사전학습된 모델을 활용하여, 700장 미만의 비교적 적은 데이터로도 90% 이상의 정확도를 달성했습니다."))

    story.append(Paragraph("8.3 실무 적용 제안",ST['h2']))
    story.append(tbl(["적용 시나리오","추천 모델","이유"],
        [["**고속 생산 라인 초기 검사**","YOLOv8n","빠른 속도, 기본적 결함 탐지"],
         ["**일반 품질 관리**","YOLOv8s","정확도-속도 최적 균형"],
         ["**정밀 최종 검사**","YOLOv8m","최고 정확도, 미세 결함까지 탐지"],
         ["**다단계 검사 시스템**","YOLOv8n + YOLOv8m","1차(빠른 선별) → 2차(정밀 검사)"]],
        [42*mm,35*mm,CW-77*mm]))

    story.append(Paragraph("8.4 향후 개선 방안",ST['h2']))
    story.append(body("1. **GPU 환경 학습**: GPU를 활용하면 학습 시간을 대폭 단축하고 더 많은 Epoch과 큰 모델을 실험 가능<br/>"
                       "2. **데이터 증강 강화**: `mouse_bite` 등 어려운 결함에 대한 추가 증강 기법 적용<br/>"
                       "3. **앙상블 기법**: 여러 모델의 예측을 결합하여 더 높은 정확도 달성 가능<br/>"
                       "4. **경량화**: TensorRT, ONNX 변환을 통해 추론 속도 최적화"))

    story.append(Paragraph("8.5 산출물 목록",ST['h2']))
    story.append(tbl(["파일","설명"],
        [["results/01_data_distribution.png","데이터 분포 시각화"],
         ["results/02_sample_images.png","결함 유형별 샘플 이미지"],
         ["results/03_label_verification.png","YOLO 라벨 변환 검증"],
         ["results/04_training_curves.png","학습 곡선 (손실/성능)"],
         ["results/05_confusion_matrix.png","혼동 행렬"],
         ["results/08_detection_results.png","탐지 결과 시각화"],
         ["results/09_model_comparison.png","모델 크기별 비교"],
         ["results/10_final_summary.json","최종 결과 JSON"],
         ["models/best_yolov8s.pt","학습된 최적 모델 가중치"]],
        [55*mm,CW-55*mm]))

    # ━━━ CONCLUSION QUOTE ━━━
    story.append(Spacer(1,5*mm))
    story.append(ColoredHR(CW,PRIMARY,2))
    story.append(Spacer(1,3*mm))
    story.append(QuoteBlock(
        fmt("**결론**: YOLOv8 기반 PCB 결함 탐지 시스템은 93.78~94.96%의 높은 정확도를 달성하여, "
            "AI 기반 스마트 팩토리 품질관리에 충분히 활용 가능한 수준임을 확인했습니다. "
            "특히 Precision 96.79%는 오탐(거짓 경보)이 매우 적음을 의미하여, "
            "실제 생산 현장에서 불필요한 라인 중단을 최소화할 수 있습니다."),
        CW, ST['body']))

    story.append(Spacer(1,8*mm))
    story.append(ColoredHR(CW,BORDER,0.3))
    story.append(Spacer(1,3*mm))
    story.append(Paragraph(
        '<font name="NanumL" size="8" color="#9e9e9e">'
        '보고서 작성: K-Digital Training 딥러닝 12기 미니프로젝트 소주제 C (PCB 결함 탐지)<br/>'
        '학습 환경: Apple M4 Pro CPU / Python 3.x / PyTorch 2.10.0 / Ultralytics YOLOv8<br/>'
        '데이터: PCB Defects Dataset (693장, 6종 결함)</font>',
        ST['footer']))

    doc.build(story, onFirstPage=page_num, onLaterPages=page_num)
    print(f"PDF generated: {OUTPUT_PDF}")

if __name__ == "__main__":
    build()

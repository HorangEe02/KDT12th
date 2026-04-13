"""
Markdown → PDF 일괄 변환 스크립트
docs/ 폴더의 모든 .md 파일을 PDF로 변환합니다.
"""
import os, re, sys
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether, Preformatted
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ─── 한글 폰트 ───
FONT = "Helvetica"
for path, name in [
    ("/System/Library/Fonts/AppleSDGothicNeo.ttc", "AppleSD"),
    ("/System/Library/Fonts/Supplemental/AppleGothic.ttf", "AppleGothic"),
]:
    if os.path.exists(path):
        try:
            pdfmetrics.registerFont(TTFont(name, path, subfontIndex=0))
            FONT = name; break
        except:
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                FONT = name; break
            except: continue

# ─── 색상 ───
NEON = HexColor("#2e7d32")
TEXT = HexColor("#1a1a1a")
TEXT_SUB = HexColor("#5a5a5a")
CARD_BG = HexColor("#e8e8e3")
BORDER = HexColor("#c8c8c8")
CODE_BG = HexColor("#f0f0eb")
QUOTE_BG = HexColor("#e8f5e9")
W = A4[0] - 40 * mm

# ─── 스타일 ───
def S(name, size, color=TEXT, align=TA_LEFT, sb=0, sa=4, leading=None):
    return ParagraphStyle(name, fontName=FONT, fontSize=size, textColor=color,
                          alignment=align, spaceBefore=sb, spaceAfter=sa,
                          leading=leading or size * 1.5, wordWrap='CJK')

STYLES = {
    'title':    S('T', 20, NEON, TA_CENTER, sa=4),
    'subtitle': S('ST', 10, TEXT_SUB, TA_CENTER, sa=10),
    'h1':       S('H1', 15, NEON, sb=16, sa=6),
    'h2':       S('H2', 12, TEXT, sb=12, sa=4),
    'h3':       S('H3', 10, NEON, sb=8, sa=3),
    'h4':       S('H4', 9, TEXT_SUB, sb=6, sa=2),
    'body':     S('B', 9, TEXT, sa=3, leading=14),
    'bullet':   S('BL', 9, TEXT, sa=2, leading=13),
    'code':     S('CD', 7.5, HexColor("#333"), sa=1, leading=10),
    'quote':    S('Q', 9, TEXT_SUB, sa=3, leading=13),
    'cell':     S('CL', 7.5, TEXT, leading=10),
    'cellh':    S('CH', 7.5, white, leading=10),
    'footer':   S('FT', 7, TEXT_SUB, TA_CENTER),
}


def escape_xml(text):
    """XML 특수문자 이스케이프"""
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text


def md_inline(text):
    """인라인 마크다운 → reportlab XML 변환"""
    text = escape_xml(text)
    # **bold**
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    # *italic*
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<i>\1</i>', text)
    # `code`
    text = re.sub(r'`([^`]+)`', r'<font color="#2e7d32">\1</font>', text)
    # ~~strikethrough~~
    text = re.sub(r'~~(.+?)~~', r'<strike>\1</strike>', text)
    return text


def parse_table(lines):
    """마크다운 테이블 파싱 → (headers, rows)"""
    rows = []
    for line in lines:
        line = line.strip()
        if line.startswith('|'):
            cells = [c.strip() for c in line.split('|')[1:-1]]
            rows.append(cells)
    if len(rows) < 2:
        return None, None
    headers = rows[0]
    # 구분선(---) 제거
    data_rows = [r for r in rows[1:] if not all(set(c.strip()) <= set('-: ') for c in r)]
    return headers, data_rows


def build_table(headers, rows):
    """reportlab Table 생성"""
    n = len(headers)
    if n == 0:
        return None
    # 열 폭 자동 계산
    if n == 2:
        col_w = [W * 0.28, W * 0.72]
    elif n == 3:
        col_w = [W * 0.2, W * 0.35, W * 0.45]
    elif n == 4:
        col_w = [W / n] * n
    else:
        col_w = [W / n] * n

    data = [[Paragraph(md_inline(h), STYLES['cellh']) for h in headers]]
    for row in rows:
        # 열 수 맞추기
        while len(row) < n:
            row.append('')
        data.append([Paragraph(md_inline(c), STYLES['cell']) for c in row[:n]])

    t = Table(data, colWidths=col_w, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NEON),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 0), (-1, -1), 7.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, CARD_BG]),
        ('GRID', (0, 0), (-1, -1), 0.4, BORDER),
    ]))
    return t


def add_header_footer(canvas, doc, title_text="HelChangGPT"):
    canvas.saveState()
    canvas.setFont(FONT, 7)
    canvas.setFillColor(NEON)
    canvas.drawString(20 * mm, A4[1] - 12 * mm, title_text)
    canvas.setFillColor(TEXT_SUB)
    canvas.drawRightString(A4[0] - 20 * mm, A4[1] - 12 * mm, "AI Fitness Life Coach")
    canvas.drawCentredString(A4[0] / 2, 15 * mm, f"- {doc.page} -")
    canvas.restoreState()


def md_to_story(md_text, filename=""):
    """마크다운 텍스트를 reportlab story 리스트로 변환"""
    lines = md_text.split('\n')
    story = []
    i = 0
    in_code = False
    code_lines = []
    in_table = False
    table_lines = []
    first_h1 = True

    while i < len(lines):
        line = lines[i]

        # ── 코드 블록 ──
        if line.strip().startswith('```'):
            if in_code:
                # 코드 블록 끝
                code_text = '\n'.join(code_lines)
                if code_text.strip():
                    # 코드 블록: 긴 코드도 페이지를 넘길 수 있도록 줄 단위로 출력
                    MAX_CHUNK = 40  # 한 블록당 최대 줄 수
                    chunks = []
                    for ci in range(0, len(code_lines), MAX_CHUNK):
                        chunks.append('\n'.join(code_lines[ci:ci + MAX_CHUNK]))
                    for chunk in chunks:
                        if not chunk.strip():
                            continue
                        code_para = Preformatted(chunk, STYLES['code'])
                        t = Table([[code_para]], colWidths=[W])
                        t.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, -1), CODE_BG),
                            ('LEFTPADDING', (0, 0), (-1, -1), 8),
                            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                            ('TOPPADDING', (0, 0), (-1, -1), 4),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                            ('BOX', (0, 0), (-1, -1), 0.3, BORDER),
                        ]))
                        story.append(t)
                    story.append(Spacer(1, 3 * mm))
                code_lines = []
                in_code = False
            else:
                # 코드 블록 시작
                in_code = True
            i += 1
            continue

        if in_code:
            code_lines.append(line)
            i += 1
            continue

        # ── 테이블 ──
        stripped = line.strip()
        if stripped.startswith('|') and '|' in stripped[1:]:
            if not in_table:
                in_table = True
                table_lines = []
            table_lines.append(line)
            i += 1
            continue
        elif in_table:
            # 테이블 끝
            headers, rows = parse_table(table_lines)
            if headers and rows:
                t = build_table(headers, rows)
                if t:
                    story.append(t)
                    story.append(Spacer(1, 3 * mm))
            in_table = False
            table_lines = []
            # 현재 줄은 다시 처리
            continue

        # ── 빈 줄 ──
        if not stripped:
            i += 1
            continue

        # ── 수평선 ──
        if stripped in ('---', '***', '___'):
            story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceBefore=6, spaceAfter=6))
            i += 1
            continue

        # ── 헤더 ──
        if stripped.startswith('# '):
            text = md_inline(stripped[2:])
            if first_h1:
                # 첫 번째 H1 = 표지 제목
                story.append(Spacer(1, 30 * mm))
                story.append(Paragraph(text, STYLES['title']))
                story.append(Spacer(1, 4 * mm))
                first_h1 = False
            else:
                story.append(Paragraph(text, STYLES['h1']))
            i += 1
            continue

        if stripped.startswith('## '):
            story.append(Paragraph(md_inline(stripped[3:]), STYLES['h1']))
            i += 1
            continue

        if stripped.startswith('### '):
            story.append(Paragraph(md_inline(stripped[4:]), STYLES['h2']))
            i += 1
            continue

        if stripped.startswith('#### '):
            story.append(Paragraph(md_inline(stripped[5:]), STYLES['h3']))
            i += 1
            continue

        if stripped.startswith('##### '):
            story.append(Paragraph(md_inline(stripped[6:]), STYLES['h4']))
            i += 1
            continue

        # ── 인용 ──
        if stripped.startswith('>'):
            quote_text = md_inline(stripped.lstrip('> '))
            q_para = Paragraph(quote_text, STYLES['quote'])
            t = Table([[q_para]], colWidths=[W - 10 * mm])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), QUOTE_BG),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(t)
            story.append(Spacer(1, 2 * mm))
            i += 1
            continue

        # ── 불릿 리스트 ──
        bullet_match = re.match(r'^(\s*)[*\-+]\s+(.*)', line)
        if bullet_match:
            indent = len(bullet_match.group(1))
            prefix = "&nbsp;&nbsp;" * (indent // 2) + "&bull; " if indent < 4 else "&nbsp;&nbsp;&nbsp;&nbsp;- "
            story.append(Paragraph(prefix + md_inline(bullet_match.group(2)), STYLES['bullet']))
            i += 1
            continue

        # ── 번호 리스트 ──
        num_match = re.match(r'^(\s*)\d+\.\s+(.*)', line)
        if num_match:
            indent = len(num_match.group(1))
            # 번호 추출
            num = re.match(r'(\d+)\.', stripped).group(1)
            prefix = "&nbsp;&nbsp;" * (indent // 2) + f"{num}. "
            story.append(Paragraph(prefix + md_inline(num_match.group(2)), STYLES['bullet']))
            i += 1
            continue

        # ── 일반 텍스트 ──
        story.append(Paragraph(md_inline(stripped), STYLES['body']))
        i += 1

    # 마지막 테이블 처리
    if in_table and table_lines:
        headers, rows = parse_table(table_lines)
        if headers and rows:
            t = build_table(headers, rows)
            if t:
                story.append(t)

    return story


def convert_md_to_pdf(md_path, pdf_path, header_title="HelChangGPT"):
    """단일 MD 파일을 PDF로 변환"""
    with open(md_path, 'r', encoding='utf-8') as f:
        md_text = f.read()

    doc = SimpleDocTemplate(
        pdf_path, pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=18 * mm, bottomMargin=20 * mm,
    )

    story = md_to_story(md_text, os.path.basename(md_path))

    # 푸터
    story.append(Spacer(1, 10 * mm))
    story.append(HRFlowable(width="30%", thickness=1, color=NEON, spaceBefore=0, spaceAfter=6))
    story.append(Paragraph(f"HelChangGPT v1.1 | {os.path.basename(md_path)}", STYLES['footer']))

    def _hf(canvas, doc):
        add_header_footer(canvas, doc, header_title)

    doc.build(story, onFirstPage=_hf, onLaterPages=_hf)


def main():
    docs_dir = Path(__file__).parent
    md_files = sorted(docs_dir.glob("*.md"))

    if not md_files:
        print("변환할 .md 파일이 없습니다.")
        return

    # 파일명 매핑 (한글 PDF 이름)
    name_map = {
        "final_report.md": "최종_보고서",
        "experiment_report.md": "실험_결과_분석",
        "feature_01_my_body.md": "기능설명서_01_내몸알기",
        "feature_02_diet.md": "기능설명서_02_오늘뭐먹지",
        "feature_03_workout.md": "기능설명서_03_오늘뭐하지",
        "feature_04_diary.md": "기능설명서_04_운동일기",
    }

    print(f"=== {len(md_files)}개 MD 파일 → PDF 변환 시작 ===\n")

    for md_file in md_files:
        fname = md_file.name
        pdf_name = name_map.get(fname, fname.replace('.md', ''))
        pdf_path = docs_dir / f"{pdf_name}.pdf"

        print(f"  [{fname}] → {pdf_path.name} ... ", end="", flush=True)
        try:
            convert_md_to_pdf(str(md_file), str(pdf_path))
            size_kb = os.path.getsize(pdf_path) / 1024
            # 페이지 수 확인
            from pypdf import PdfReader
            pages = len(PdfReader(str(pdf_path)).pages)
            print(f"OK ({pages}p, {size_kb:.0f}KB)")
        except Exception as e:
            print(f"ERROR: {e}")

    print(f"\n=== 변환 완료 ===")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""README.md → PDF 변환 스크립트 (Malgun Gothic — 완전한 Unicode 지원)"""

import re
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── Fonts (Malgun Gothic: 박스문자·한자·수학기호 모두 지원) ──
pdfmetrics.registerFont(TTFont('Malgun', '/Users/yeong/Library/Fonts/malgun.ttf'))
pdfmetrics.registerFont(TTFont('MalgunBold', '/Users/yeong/Library/Fonts/malgunbd.ttf'))
pdfmetrics.registerFontFamily('Malgun', normal='Malgun', bold='MalgunBold',
                              italic='Malgun', boldItalic='MalgunBold')

FONT = 'Malgun'
FONT_BOLD = 'MalgunBold'

# ── Colors ──
C_PRIMARY = HexColor('#1a365d')
C_ACCENT = HexColor('#2b6cb0')
C_CODE_BG = HexColor('#1e293b')
C_CODE_FG = HexColor('#e2e8f0')
C_TABLE_HEADER = HexColor('#2d3748')
C_TABLE_ROW_ALT = HexColor('#f0f4f8')
C_BORDER = HexColor('#cbd5e0')
C_BLOCKQUOTE = HexColor('#4a5568')

# ── Styles ──
styles = {
    'title': ParagraphStyle('Title', fontName=FONT_BOLD, fontSize=22, leading=28,
                            textColor=C_PRIMARY, spaceAfter=4, alignment=TA_CENTER),
    'subtitle': ParagraphStyle('Subtitle', fontName=FONT, fontSize=11, leading=16,
                               textColor=C_ACCENT, spaceAfter=16, alignment=TA_CENTER),
    'h2': ParagraphStyle('H2', fontName=FONT_BOLD, fontSize=15, leading=20,
                         textColor=C_PRIMARY, spaceBefore=18, spaceAfter=8),
    'h3': ParagraphStyle('H3', fontName=FONT_BOLD, fontSize=12, leading=17,
                         textColor=C_ACCENT, spaceBefore=12, spaceAfter=6),
    'h4': ParagraphStyle('H4', fontName=FONT_BOLD, fontSize=11, leading=15,
                         textColor=HexColor('#2c5282'), spaceBefore=10, spaceAfter=4),
    'body': ParagraphStyle('Body', fontName=FONT, fontSize=9, leading=14,
                           textColor=HexColor('#2d3748'), spaceAfter=6),
    'bold_body': ParagraphStyle('BoldBody', fontName=FONT, fontSize=9, leading=14,
                                textColor=HexColor('#1a202c'), spaceAfter=6),
    'bullet': ParagraphStyle('Bullet', fontName=FONT, fontSize=9, leading=14,
                             textColor=HexColor('#2d3748'), leftIndent=16,
                             bulletIndent=4, spaceAfter=3),
    'blockquote': ParagraphStyle('Blockquote', fontName=FONT, fontSize=10, leading=15,
                                 textColor=C_BLOCKQUOTE, leftIndent=12, spaceAfter=10,
                                 borderPadding=6),
    'code': ParagraphStyle('Code', fontName=FONT, fontSize=7, leading=10,
                           textColor=C_CODE_FG, backColor=C_CODE_BG,
                           leftIndent=8, rightIndent=8, spaceBefore=4, spaceAfter=8,
                           borderPadding=(8, 8, 8, 8)),
    'table_header': ParagraphStyle('TH', fontName=FONT_BOLD, fontSize=8, leading=12,
                                   textColor=white, alignment=TA_CENTER),
    'table_cell': ParagraphStyle('TC', fontName=FONT, fontSize=8, leading=12,
                                 textColor=HexColor('#2d3748')),
    'table_cell_center': ParagraphStyle('TCC', fontName=FONT, fontSize=8, leading=12,
                                        textColor=HexColor('#2d3748'), alignment=TA_CENTER),
}


def escape_xml(text):
    """XML 특수문자 이스케이프"""
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text


def format_inline(text):
    """인라인 마크다운 → reportlab XML"""
    text = escape_xml(text)
    # bold+italic
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<b><i>\1</i></b>', text)
    # bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    # italic
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    # inline code
    text = re.sub(r'`(.+?)`', rf'<font face="{FONT}" size="8" color="#c53030">\1</font>', text)
    # links - show text only
    text = re.sub(r'\[(.+?)\]\((.+?)\)', r'<font color="#2b6cb0"><u>\1</u></font>', text)
    return text


def parse_table(lines):
    """마크다운 테이블 파싱"""
    rows = []
    for line in lines:
        line = line.strip()
        if line.startswith('|') and line.endswith('|'):
            cells = [c.strip() for c in line.split('|')[1:-1]]
            if all(re.match(r'^[-:]+$', c) for c in cells):
                continue
            rows.append(cells)
    return rows


def build_table_flowable(rows):
    """테이블 행 → reportlab Table"""
    if not rows:
        return None

    n_cols = len(rows[0])
    page_width = A4[0] - 2 * 2 * cm
    col_width = page_width / n_cols

    header = [Paragraph(format_inline(c), styles['table_header']) for c in rows[0]]
    data = [header]

    for row in rows[1:]:
        cells = []
        for c in row:
            c_stripped = c.strip()
            if re.match(r'^[\d%+~≥≤.·×μ\s\-−]+$', c_stripped) or c_stripped.startswith('**'):
                cells.append(Paragraph(format_inline(c), styles['table_cell_center']))
            else:
                cells.append(Paragraph(format_inline(c), styles['table_cell']))
        while len(cells) < n_cols:
            cells.append(Paragraph('', styles['table_cell']))
        data.append(cells[:n_cols])

    tbl = Table(data, colWidths=[col_width] * n_cols, repeatRows=1)

    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), C_TABLE_HEADER),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, -1), FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, C_BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style_cmds.append(('BACKGROUND', (0, i), (-1, i), C_TABLE_ROW_ALT))

    tbl.setStyle(TableStyle(style_cmds))
    return tbl


def is_directory_tree(code_lines):
    """디렉토리 트리 구조인지 판별.
    '├── name' 패턴(트리)과 '├──────┤' 패턴(박스 테두리)을 구분."""
    # ├── 또는 └── 뒤에 공백+텍스트가 오면 디렉토리 트리
    tree_pattern = re.compile(r'[├└]──\s+\S')
    tree_count = sum(1 for line in code_lines if tree_pattern.search(line))
    return tree_count >= 3


def parse_ascii_box_to_table(code_lines):
    """
    ASCII 박스 테이블 (┌─┐│└┘ 사용) → reportlab Table 변환.
    디렉토리 트리는 제외.
    """
    # 디렉토리 트리는 일반 코드 블록으로 처리
    if is_directory_tree(code_lines):
        return None

    corner_chars = set('┌┐└┘')
    has_corners = any(any(c in corner_chars for c in line) for line in code_lines)
    if not has_corners:
        return None

    box_chars = set('┌┐└┘│─├┤┬┴┼')

    # │ ... │ 형태의 내용 줄에서 텍스트 추출
    content_lines = []
    title_line = None
    for line in code_lines:
        stripped = line.strip()
        # 테두리 줄 무시
        if stripped and all(c in box_chars | {' '} for c in stripped):
            continue
        # │ ... │ 형태의 내용 줄
        if stripped.startswith('│') and stripped.endswith('│'):
            inner = stripped[1:-1].strip()
            if inner:
                # [AS-IS] / [TO-BE] 제목 감지
                if inner.startswith('[') and ']' in inner:
                    title_line = inner
                else:
                    content_lines.append(inner)

    if not content_lines:
        return None

    # 키-값 테이블로 구성 (· leader dots 기준 분리, 1개 이상)
    rows = []
    if title_line:
        rows.append(('__title__', title_line))

    for line in content_lines:
        # leader dots (·) 1개 이상으로 분리
        if '·' in line:
            parts = re.split(r'·+', line, maxsplit=1)
            if len(parts) == 2 and parts[1].strip():
                rows.append((parts[0].strip(), parts[1].strip()))
                continue
        rows.append((line, ''))

    if not rows:
        return None

    page_width = A4[0] - 2 * 2 * cm
    has_title = rows and rows[0][0] == '__title__'

    data = []
    for idx, (key, val) in enumerate(rows):
        if key == '__title__':
            data.append([
                Paragraph(escape_xml(val), ParagraphStyle(
                    'BoxTitle', fontName=FONT_BOLD, fontSize=9, leading=13,
                    textColor=white, alignment=TA_CENTER)),
                Paragraph('', styles['table_cell'])
            ])
        elif val:
            data.append([
                Paragraph(escape_xml(key), ParagraphStyle(
                    'BoxKey', fontName=FONT, fontSize=8, leading=12,
                    textColor=HexColor('#e2e8f0'))),
                Paragraph(escape_xml(val), ParagraphStyle(
                    'BoxVal', fontName=FONT_BOLD, fontSize=8, leading=12,
                    textColor=HexColor('#fbd38d')))
            ])
        else:
            data.append([
                Paragraph(escape_xml(key), ParagraphStyle(
                    'BoxSingle', fontName=FONT, fontSize=8, leading=12,
                    textColor=HexColor('#e2e8f0'))),
                Paragraph('', styles['table_cell'])
            ])

    if not data:
        return None

    tbl = Table(data, colWidths=[page_width * 0.45, page_width * 0.55])

    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, -1), C_CODE_BG),
        ('TEXTCOLOR', (0, 0), (-1, -1), C_CODE_FG),
        ('FONTNAME', (0, 0), (-1, -1), FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, HexColor('#2d3748')),
        ('ROUNDEDCORNERS', [6, 6, 6, 6]),
    ]

    if has_title:
        style_cmds.extend([
            ('SPAN', (0, 0), (1, 0)),
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2b6cb0')),
            ('LINEBELOW', (0, 0), (-1, 0), 1, HexColor('#3182ce')),
        ])

    tbl.setStyle(TableStyle(style_cmds))
    return tbl


def parse_comparison_box_to_table(code_lines):
    """
    Before/After 비교 코드 블록 → 3열 비교 테이블.
    형식: label │ before_val │ → │ after_val │
    """
    # Before ... After 패턴 감지
    header_line = None
    for line in code_lines:
        if 'Before' in line and 'After' in line:
            header_line = line.strip()
            break

    if not header_line:
        return None

    box_chars = set('┌┐└┘│─├┤┬┴┼')
    data_lines = []
    for line in code_lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped == header_line:
            continue
        # 테두리만 있는 줄 무시
        if all(c in box_chars | {' '} for c in stripped):
            continue

        # "label │ before │ → │ after │" 형식 파싱
        if '│' in stripped and '→' in stripped:
            # │ 로 분리 후 빈 항목/→ 제거
            segments = [s.strip() for s in stripped.split('│')]
            segments = [s for s in segments if s and s != '→']
            if len(segments) >= 3:
                data_lines.append(segments[:3])
            elif len(segments) == 2:
                data_lines.append([segments[0], segments[1], ''])

    if not data_lines:
        return None

    page_width = A4[0] - 2 * 2 * cm

    hdr_style = ParagraphStyle('CmpHdr', fontName=FONT_BOLD, fontSize=9, leading=13,
                               textColor=white, alignment=TA_CENTER)
    tbl_data = [[Paragraph('항목', hdr_style),
                 Paragraph('Before (수작업)', hdr_style),
                 Paragraph('After (AI)', hdr_style)]]

    val_style = ParagraphStyle('CmpVal', fontName=FONT, fontSize=8, leading=12,
                               textColor=HexColor('#e2e8f0'))
    val_style_bold = ParagraphStyle('CmpValB', fontName=FONT_BOLD, fontSize=8, leading=12,
                                     textColor=HexColor('#fbd38d'))

    for parts in data_lines:
        tbl_data.append([
            Paragraph(escape_xml(parts[0]), val_style),
            Paragraph(escape_xml(parts[1]), val_style),
            Paragraph(escape_xml(parts[2]) if len(parts) > 2 else '', val_style_bold),
        ])

    if len(tbl_data) <= 1:
        return None

    tbl = Table(tbl_data, colWidths=[page_width * 0.3, page_width * 0.35, page_width * 0.35])
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2b6cb0')),
        ('BACKGROUND', (0, 1), (-1, -1), C_CODE_BG),
        ('TEXTCOLOR', (0, 0), (-1, -1), white),
        ('FONTNAME', (0, 0), (-1, -1), FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#2d3748')),
        ('ROUNDEDCORNERS', [6, 6, 6, 6]),
    ]))
    return tbl


def build_code_block(code_lines):
    """코드 블록을 최적 방식으로 렌더링"""
    # 1) Before/After 비교표 감지
    tbl = parse_comparison_box_to_table(code_lines)
    if tbl:
        return tbl

    # 2) ASCII 박스 테이블 감지
    tbl = parse_ascii_box_to_table(code_lines)
    if tbl:
        return tbl

    # 3) 일반 코드 블록 — 텍스트로 렌더링
    code_text = escape_xml('\n'.join(code_lines))
    if code_text.strip():
        return Paragraph(code_text.replace('\n', '<br/>'), styles['code'])
    return None


def parse_md_to_flowables(md_text):
    """마크다운 텍스트 → flowable 리스트"""
    story = []
    lines = md_text.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # 빈 줄
        if not stripped:
            i += 1
            continue

        # 수평선
        if stripped in ('---', '***', '___'):
            story.append(Spacer(1, 4))
            story.append(HRFlowable(width="100%", thickness=1, color=C_BORDER,
                                    spaceBefore=4, spaceAfter=8))
            i += 1
            continue

        # 제목 (# ~ ####)
        m = re.match(r'^(#{1,4})\s+(.*)', stripped)
        if m:
            level = len(m.group(1))
            text = format_inline(m.group(2))
            if level == 1:
                clean = re.sub(r'[🏭🔧📊💡🎯]', '', text).strip()
                story.append(Spacer(1, 20))
                story.append(Paragraph(clean, styles['title']))
            elif level == 2:
                story.append(Paragraph(text, styles['h2']))
            elif level == 3:
                story.append(Paragraph(text, styles['h3']))
            elif level == 4:
                story.append(Paragraph(text, styles['h4']))
            i += 1
            continue

        # 인용문 (>)
        if stripped.startswith('>'):
            quote_text = format_inline(stripped.lstrip('> '))
            story.append(Paragraph(f'<font color="{C_BLOCKQUOTE}">{quote_text}</font>',
                                   styles['blockquote']))
            i += 1
            continue

        # 코드 블록 (```)
        if stripped.startswith('```'):
            i += 1
            code_lines = []
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1
            i += 1  # skip closing ```

            flowable = build_code_block(code_lines)
            if flowable:
                story.append(Spacer(1, 4))
                story.append(flowable)
                story.append(Spacer(1, 4))
            continue

        # 테이블
        if stripped.startswith('|'):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                table_lines.append(lines[i])
                i += 1
            rows = parse_table(table_lines)
            tbl = build_table_flowable(rows)
            if tbl:
                story.append(Spacer(1, 4))
                story.append(tbl)
                story.append(Spacer(1, 8))
            continue

        # 불릿 리스트
        m_bullet = re.match(r'^[-*]\s+(.*)', stripped)
        if m_bullet:
            text = format_inline(m_bullet.group(1))
            story.append(Paragraph(f'• {text}', styles['bullet']))
            i += 1
            continue

        # 굵은 텍스트로 시작하는 단락
        if stripped.startswith('**'):
            text = format_inline(stripped)
            story.append(Paragraph(text, styles['bold_body']))
            i += 1
            continue

        # 일반 단락
        para_lines = [stripped]
        i += 1
        while i < len(lines):
            next_stripped = lines[i].strip()
            if (not next_stripped or next_stripped.startswith('#') or
                next_stripped.startswith('|') or next_stripped.startswith('```') or
                next_stripped.startswith('-') or next_stripped.startswith('*') or
                next_stripped.startswith('>') or next_stripped == '---'):
                break
            para_lines.append(next_stripped)
            i += 1

        text = format_inline(' '.join(para_lines))
        story.append(Paragraph(text, styles['body']))

    return story


def add_page_number(canvas_obj, doc):
    """페이지 번호 & 하단 라인"""
    canvas_obj.saveState()
    canvas_obj.setStrokeColor(C_BORDER)
    canvas_obj.setLineWidth(0.5)
    canvas_obj.line(2 * cm, 1.5 * cm, A4[0] - 2 * cm, 1.5 * cm)
    canvas_obj.setFont(FONT, 8)
    canvas_obj.setFillColor(HexColor('#718096'))
    canvas_obj.drawCentredString(A4[0] / 2, 1.1 * cm, f"- {doc.page} -")
    canvas_obj.restoreState()


def main():
    input_path = '/Users/yeong/00_work_out/01_KNU/main_class/Phase10/mini_10/README.md'
    output_path = '/Users/yeong/00_work_out/01_KNU/main_class/Phase10/mini_10/README.pdf'

    with open(input_path, 'r', encoding='utf-8') as f:
        md_text = f.read()

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        title='AI 기반 스마트 팩토리 품질관리 시스템',
        author='K-Digital Training 딥러닝 12기',
    )

    story = parse_md_to_flowables(md_text)
    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    print(f'PDF 생성 완료: {output_path}')


if __name__ == '__main__':
    main()

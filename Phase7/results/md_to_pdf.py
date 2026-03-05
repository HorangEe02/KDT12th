#!/usr/bin/env python3
"""
Markdown to PDF converter — LaTeX math rendered as images via matplotlib.
Korean text inside \\text{} is rendered with Apple SD Gothic Neo font.
Pipeline: Markdown → (extract math → render PNG) → HTML → PDF (WeasyPrint)
"""
import sys, os, re, hashlib, tempfile, shutil
import markdown
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from weasyprint import HTML

# ── Korean detection ────────────────────────────────────────────────

_KR_RE = re.compile(r'[\uac00-\ud7a3]')
_KR_FONT = 'Apple SD Gothic Neo'

def _has_korean(text):
    return bool(_KR_RE.search(text))


# ── LaTeX pre-processing ───────────────────────────────────────────

def _preprocess_latex(tex):
    """Fix LaTeX commands not supported by matplotlib mathtext."""
    # \xrightarrow{text} → \stackrel{text}{→}  (mathtext doesn't support \xrightarrow)
    tex = re.sub(r'\\xrightarrow\{([^}]*)\}', r'\\stackrel{\\mathrm{\1}}{\\longrightarrow}', tex)
    # \quad → \;\;\;  (mathtext supports \; as thick space)
    tex = tex.replace(r'\quad', r'\;\;\;')
    # Fix escaped percent in text mode
    tex = tex.replace(r'\%', '%')
    return tex


# ── Math image rendering ───────────────────────────────────────────

def _get_cache_path(latex_str, display, cache_dir):
    key = hashlib.md5((latex_str + str(display)).encode()).hexdigest()[:12]
    return os.path.join(cache_dir, f'math_{key}.png')


def _render_pure_math(tex, display, dpi, cache_dir):
    """Render a pure (no-Korean) LaTeX formula with matplotlib mathtext."""
    out_path = _get_cache_path(tex, display, cache_dir)
    if os.path.exists(out_path):
        return out_path

    tex = _preprocess_latex(tex.strip())
    if not tex.startswith('$'):
        tex = f'${tex}$'

    fontsize = 14 if display else 11
    est_w = max(3.0, min(12.0, len(tex) * 0.075))
    est_h = 0.9 if display else 0.5

    # Count nested fractions / sums for taller figure
    if r'\frac' in tex or r'\sum' in tex:
        est_h = max(est_h, 1.2)

    fig, ax = plt.subplots(figsize=(est_w, est_h))
    ax.axis('off')
    try:
        ax.text(0.5, 0.5, tex, fontsize=fontsize, ha='center', va='center',
                transform=ax.transAxes, math_fontfamily='cm')
        fig.savefig(out_path, dpi=dpi, bbox_inches='tight', pad_inches=0.08,
                    transparent=False, facecolor='#FFFDE7')
    except Exception:
        plt.close(fig)
        fig, ax = plt.subplots(figsize=(est_w, est_h))
        ax.axis('off')
        ax.text(0.5, 0.5, tex.replace('$', ''), fontsize=10, ha='center', va='center',
                transform=ax.transAxes, family='monospace', color='#333')
        fig.savefig(out_path, dpi=dpi, bbox_inches='tight', pad_inches=0.08,
                    transparent=False, facecolor='#FFFDE7')
    finally:
        plt.close(fig)
    return out_path


def _render_korean_math(latex_str, display, dpi, cache_dir):
    """
    Render a LaTeX formula containing Korean text.
    Strategy: split by \\text{Korean...} → render Korean as regular text,
    math parts with $...$, all in a single matplotlib text() call using
    a Korean-capable font.
    """
    out_path = _get_cache_path(latex_str + '_kr', display, cache_dir)
    if os.path.exists(out_path):
        return out_path

    tex = _preprocess_latex(latex_str.strip())

    # Split by \text{...} that contains Korean
    # Pattern captures the content inside \text{...}
    segments = []
    last_end = 0

    for m in re.finditer(r'\\text\{([^}]*)\}', tex):
        content = m.group(1)
        if _has_korean(content):
            # Math segment before this Korean \text
            math_before = tex[last_end:m.start()].strip()
            if math_before:
                segments.append(('math', math_before))
            # Korean text segment
            segments.append(('kr', content.replace('\\%', '%')))
            last_end = m.end()

    # Remaining math after last Korean \text
    math_after = tex[last_end:].strip()
    if math_after:
        segments.append(('math', math_after))

    # Build mixed string: Korean as plain text, math in $...$
    parts = []
    for seg_type, content in segments:
        if seg_type == 'math':
            c = content.strip()
            # Remove leading/trailing operators that look odd alone
            if c:
                parts.append(f'${c}$')
        else:
            # Korean text rendered as-is (no $ delimiters)
            parts.append(f' {content} ')

    mixed_text = ''.join(parts)
    # Clean up double spaces
    mixed_text = re.sub(r'  +', ' ', mixed_text).strip()

    fontsize = 13 if display else 11
    est_w = max(4.0, min(12.0, len(mixed_text) * 0.07))
    est_h = 1.0 if display else 0.5

    if r'\frac' in mixed_text or r'\sum' in mixed_text:
        est_h = max(est_h, 1.3)

    fig, ax = plt.subplots(figsize=(est_w, est_h))
    ax.axis('off')
    try:
        ax.text(0.5, 0.5, mixed_text, fontsize=fontsize, ha='center', va='center',
                transform=ax.transAxes, fontfamily=_KR_FONT)
        fig.savefig(out_path, dpi=dpi, bbox_inches='tight', pad_inches=0.08,
                    transparent=False, facecolor='#FFFDE7')
    except Exception as e:
        plt.close(fig)
        # Fallback: plain text
        fig, ax = plt.subplots(figsize=(est_w, est_h))
        ax.axis('off')
        plain = latex_str.replace('\\text{', '').replace('}', ' ')
        plain = re.sub(r'\\[a-zA-Z]+', '', plain).replace('{', '').replace('$', '')
        ax.text(0.5, 0.5, plain, fontsize=10, ha='center', va='center',
                transform=ax.transAxes, fontfamily=_KR_FONT, color='#333')
        fig.savefig(out_path, dpi=dpi, bbox_inches='tight', pad_inches=0.08,
                    transparent=False, facecolor='#FFFDE7')
    finally:
        plt.close(fig)
    return out_path


def _render_math_image(latex_str, display=True, dpi=180, cache_dir=None):
    """Route to Korean or pure math renderer."""
    if _has_korean(latex_str):
        return _render_korean_math(latex_str, display, dpi, cache_dir)
    else:
        return _render_pure_math(latex_str, display, dpi, cache_dir)


# ── Markdown math extraction ───────────────────────────────────────

def _process_math_in_markdown(md_text, cache_dir):
    """Replace $$...$$ and $...$ with <img> tags pointing to rendered PNGs."""
    counter = {'display': 0, 'inline': 0, 'errors': 0}

    def _replace_display(match):
        latex = match.group(1).strip()
        if not latex:
            return match.group(0)
        try:
            counter['display'] += 1
            img_path = _render_math_image(latex, display=True, cache_dir=cache_dir)
            return (f'\n\n<div class="math-display">'
                    f'<img src="file://{img_path}" alt="math" class="math-img-display">'
                    f'</div>\n\n')
        except Exception as e:
            counter['errors'] += 1
            return f'\n\n<div class="math-fallback"><code>{latex}</code></div>\n\n'

    md_text = re.sub(r'\$\$(.*?)\$\$', _replace_display, md_text, flags=re.DOTALL)

    def _replace_inline(match):
        latex = match.group(1).strip()
        if not latex or len(latex) < 2:
            return match.group(0)
        # Skip currency-like patterns
        if re.match(r'^\d+[\.,]?\d*$', latex):
            return match.group(0)
        try:
            counter['inline'] += 1
            img_path = _render_math_image(latex, display=False, cache_dir=cache_dir)
            return f'<img src="file://{img_path}" alt="math" class="math-img-inline">'
        except Exception as e:
            counter['errors'] += 1
            return f'<code class="math-fallback-inline">{latex}</code>'

    md_text = re.sub(
        r'(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)',
        _replace_inline,
        md_text,
    )

    print(f"  Rendered: {counter['display']} display + {counter['inline']} inline"
          f" ({counter['errors']} errors)")
    return md_text


# ── HTML + CSS + PDF generation ─────────────────────────────────────

_CSS = """
@page {
    size: A4;
    margin: 1.5cm 1.8cm;
    @bottom-center {
        content: counter(page) " / " counter(pages);
        font-size: 9pt;
        color: #888;
    }
}

body {
    font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', 'Noto Sans KR', sans-serif;
    font-size: 10pt;
    line-height: 1.55;
    color: #1a1a1a;
}

h1 {
    font-size: 18pt; color: #1a237e;
    border-bottom: 3px solid #1a237e;
    padding-bottom: 6px; margin-top: 28px; margin-bottom: 12px;
}
h2 {
    font-size: 14pt; color: #283593;
    border-bottom: 1.5px solid #c5cae9;
    padding-bottom: 4px; margin-top: 22px; margin-bottom: 8px;
    page-break-after: avoid;
}
h3 {
    font-size: 12pt; color: #3949ab;
    margin-top: 14px; margin-bottom: 6px;
    page-break-after: avoid;
}
h4 {
    font-size: 10.5pt; color: #5c6bc0;
    margin-top: 10px; margin-bottom: 4px;
    page-break-after: avoid;
}

p { margin: 4px 0; orphans: 3; widows: 3; }

/* Tables */
table {
    border-collapse: collapse; width: 100%;
    margin: 8px 0; font-size: 9pt;
    page-break-inside: avoid;
}
th {
    background-color: #e8eaf6; border: 1px solid #9fa8da;
    padding: 5px 8px; text-align: left;
    font-weight: bold; color: #1a237e;
}
td {
    border: 1px solid #c5cae9; padding: 4px 8px; text-align: left;
}
tr:nth-child(even) { background-color: #f5f5ff; }

/* Blockquotes */
blockquote {
    border-left: 4px solid #7986cb; background-color: #e8eaf6;
    margin: 8px 0; padding: 6px 12px;
    font-size: 9.5pt; color: #333;
    page-break-inside: avoid;
}
blockquote > blockquote {
    border-left-color: #9fa8da; background-color: #ede7f6;
}

/* Code */
code {
    font-family: 'SF Mono', 'Menlo', 'Monaco', monospace;
    font-size: 8.5pt; background-color: #f0f0f0;
    padding: 1px 4px; border-radius: 3px;
}
pre {
    background-color: #263238; color: #eeffff;
    padding: 10px; border-radius: 5px; font-size: 8pt;
    overflow-x: auto; page-break-inside: avoid;
}
pre code { background-color: transparent; color: inherit; padding: 0; }

/* Math images */
.math-display {
    text-align: center; margin: 10px 0; page-break-inside: avoid;
}
img.math-img-display {
    max-width: 95%; max-height: 90px; height: auto;
    display: inline-block; border: none; border-radius: 4px;
    margin: 0 auto; vertical-align: middle;
}
img.math-img-inline {
    max-height: 24px; height: 20px;
    display: inline; vertical-align: middle;
    border: none; margin: 0 2px;
}

/* Math fallback (code) */
.math-fallback {
    text-align: center; margin: 8px 0;
    background-color: #fff8e1; border: 1px solid #ffe082;
    border-radius: 4px; padding: 6px 10px;
    page-break-inside: avoid;
}
.math-fallback code, code.math-fallback-inline {
    background-color: #fff8e1; border: 1px solid #ffe082;
    color: #333; font-size: 8.5pt;
}

/* Figure images */
img:not(.math-img-display):not(.math-img-inline) {
    max-width: 100%; height: auto;
    display: block; margin: 10px auto;
    border: 1px solid #ddd; border-radius: 4px;
    page-break-inside: avoid;
}

hr { border: none; border-top: 1px solid #c5cae9; margin: 16px 0; }
ul, ol { margin: 4px 0; padding-left: 20px; }
li { margin: 2px 0; }
strong { color: #1a237e; }
em { color: #555; }
"""


def convert_md_to_pdf(md_path, pdf_path):
    """Convert a Markdown file to PDF with Korean fonts + LaTeX math images."""
    print(f"Reading {md_path} ...")
    with open(md_path, 'r', encoding='utf-8') as f:
        md_text = f.read()

    math_cache = os.path.join(os.path.dirname(os.path.abspath(pdf_path)), '.math_cache')
    os.makedirs(math_cache, exist_ok=True)

    print("Rendering LaTeX math expressions ...")
    md_text = _process_math_in_markdown(md_text, math_cache)

    print("Converting Markdown → HTML ...")
    html_body = markdown.markdown(md_text, extensions=['tables', 'fenced_code', 'toc'])

    # Fix figure image paths to absolute
    base_dir = os.path.dirname(os.path.abspath(md_path))

    def _fix_img(m):
        tag, src = m.group(0), m.group(1)
        if src.startswith(('http://', 'https://', 'file://')):
            return tag
        abs_p = os.path.abspath(os.path.join(base_dir, src))
        return tag.replace(f'src="{src}"', f'src="file://{abs_p}"')

    html_body = re.sub(r'<img[^>]+src="([^"]+)"[^>]*>', _fix_img, html_body)

    full_html = (f'<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">'
                 f'<style>{_CSS}</style></head><body>{html_body}</body></html>')

    print("Generating PDF ...")
    HTML(string=full_html, base_url=base_dir).write_pdf(pdf_path)

    size_mb = os.path.getsize(pdf_path) / 1024 / 1024
    print(f"Done! {pdf_path} ({size_mb:.1f} MB)")

    shutil.rmtree(math_cache, ignore_errors=True)


if __name__ == '__main__':
    if len(sys.argv) >= 3:
        convert_md_to_pdf(sys.argv[1], sys.argv[2])
    elif len(sys.argv) == 2:
        md_path = sys.argv[1]
        convert_md_to_pdf(md_path, os.path.splitext(md_path)[0] + '.pdf')
    else:
        d = os.path.dirname(os.path.abspath(__file__))
        convert_md_to_pdf(os.path.join(d, 'ppt_README.md'), os.path.join(d, 'ppt_README.pdf'))

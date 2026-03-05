#!/usr/bin/env python3
"""Batch convert all .md files in results/ to PDF using md_to_pdf.py"""
import os, sys, time, glob

# Add current dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from md_to_pdf import convert_md_to_pdf

def main():
    results_dir = os.path.dirname(os.path.abspath(__file__))
    md_files = sorted(glob.glob(os.path.join(results_dir, '*.md')))

    # Skip ppt_README.md (already converted)
    skip = {'ppt_README.md'}
    md_files = [f for f in md_files if os.path.basename(f) not in skip]

    print(f"Found {len(md_files)} MD files to convert:\n")
    for f in md_files:
        print(f"  - {os.path.basename(f)}")
    print()

    results = []
    for i, md_path in enumerate(md_files, 1):
        name = os.path.basename(md_path)
        pdf_path = os.path.splitext(md_path)[0] + '.pdf'
        print(f"\n{'='*60}")
        print(f"[{i}/{len(md_files)}] {name}")
        print(f"{'='*60}")
        t0 = time.time()
        try:
            convert_md_to_pdf(md_path, pdf_path)
            elapsed = time.time() - t0
            size_mb = os.path.getsize(pdf_path) / 1024 / 1024
            results.append((name, 'OK', f'{size_mb:.1f} MB', f'{elapsed:.1f}s'))
        except Exception as e:
            elapsed = time.time() - t0
            results.append((name, 'FAIL', str(e)[:60], f'{elapsed:.1f}s'))

    # Summary
    print(f"\n\n{'='*60}")
    print("CONVERSION SUMMARY")
    print(f"{'='*60}")
    print(f"{'File':<30} {'Status':<8} {'Size':<12} {'Time':<8}")
    print('-'*60)
    for name, status, info, elapsed in results:
        print(f"{name:<30} {status:<8} {info:<12} {elapsed:<8}")

    ok = sum(1 for _, s, _, _ in results if s == 'OK')
    print(f"\n{ok}/{len(results)} files converted successfully.")

if __name__ == '__main__':
    main()

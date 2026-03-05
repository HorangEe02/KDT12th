#!/usr/bin/env python3
"""
PPT 가시성 향상을 위한 fontsize 자동 수정 스크립트
- 대상: comparison, conclusion, logistic, diagnostics 관련 그래프 함수
- 제목(suptitle, set_title, fig.text 제목) 유지
- 내용(본문, 라벨, 범례, 테이블, 주석 등) fontsize 키우기
"""
import re
import os

# ========== 대상 파일 및 함수 매핑 ==========
BASE = os.path.dirname(os.path.abspath(__file__))

TARGET_FUNCTIONS = {
    os.path.join(BASE, 'team_e_item_optimization.py'): [
        'plot_e8_comparison_bar',     # fig_e8
        'plot_e10_conclusion',        # fig_e10
        'plot_e13_cv_conclusion',     # fig_e13
        'plot_e14_advanced_comparison',# fig_e14
        'plot_e15_logistic_regression',# fig_e15
        'plot_e16_logistic_diagnostics',# fig_e16
    ],
    os.path.join(BASE, 'team_d_survey_compare.py'): [
        'analyze_score_comparison',       # fig_d5
        'create_conclusion_infographic',  # fig_d12
        'analyze_logistic_prediction',    # fig_d13
        'analyze_logistic_diagnostics',   # fig_d14
    ],
    os.path.join(BASE, 'team_b_survey.py'): [
        'analyze_dimension_comparison',     # fig_bs2
        'create_survey_conclusion',         # fig_bs10
        'analyze_logistic_crossval',        # fig_bs11
        'analyze_logistic_diagnostics_b',   # fig_bs12
    ],
    os.path.join(BASE, 'team_b_interest.py'): [
        'create_conclusion_infographic',  # fig_b15
    ],
    os.path.join(BASE, 'team_a_demographics.py'): [
        'analyze_age_by_mbti',            # fig_a4
        'create_conclusion_infographic',  # fig_a12
    ],
    os.path.join(BASE, 'team_a_survey.py'): [
        'analyze_effect_size_comparison',  # fig_as6
        'create_conclusion_infographic',   # fig_as7
    ],
    os.path.join(BASE, 'team_c_korea_blood.py'): [
        'analyze_scientific_evidence',  # fig_c13
    ],
    os.path.join(BASE, 'team_c_survey.py'): [
        'analyze_trust_comparison',        # fig_cs2
        'create_conclusion_infographic',   # fig_cs7
    ],
}

# ========== fontsize 증가 매핑 ==========
# "내용" fontsize만 키움. 제목 등은 유지.
FONTSIZE_MAP = {
    7: 12,
    8: 13,
    9: 14,
    10: 15,
    11: 16,
    12: 16,
    13: 17,
    14: 18,
    15: 19,
    16: 20,
    17: 21,
    18: 22,
    19: 23,
    # 20 이상은 이미 큰 편 → 소폭 증가
    20: 24,
}

# 제목으로 간주하는 패턴 (이 줄에서는 fontsize를 바꾸지 않음)
TITLE_PATTERNS = [
    r'\.suptitle\(',
    r'\.set_title\(',
    r'fig\.text\(.+fontsize=\d+.+fontweight=.bold.',  # fig.text with bold = title
    r"fig\.text\(.+fontsize=2[6-9]",  # fig.text with fontsize >= 26 = title
    r"fig\.text\(.+fontsize=3\d",     # fig.text with fontsize >= 30 = title
    r"'핵심 결과'",
    r"'차원별 최적화 결과'",
    r"'결론'",
    r"'주의사항'",
    r"'종합 판정'",
    r"'분석 방법 요약'",
    r"'과적합 심각'",
    r"'부분적 과적합'",
    r"'과적합 미미'",
]


def is_title_line(line):
    """이 줄이 제목(title/suptitle) 관련인지 확인"""
    for pat in TITLE_PATTERNS:
        if re.search(pat, line):
            return True
    return False


def extract_functions(lines, func_names):
    """파일에서 대상 함수의 라인 범위를 추출"""
    ranges = []
    for i, line in enumerate(lines):
        for fname in func_names:
            if re.match(rf'^def {fname}\(', line):
                # 함수 시작 찾음, 끝은 다음 def 또는 파일 끝
                end = len(lines)
                for j in range(i + 1, len(lines)):
                    if re.match(r'^def ', lines[j]) or re.match(r'^class ', lines[j]):
                        end = j
                        break
                ranges.append((i, end, fname))
                break
    return ranges


def increase_fontsize_in_range(lines, start, end, func_name):
    """지정된 범위 내에서 fontsize 값을 증가"""
    changes = 0
    for i in range(start, end):
        line = lines[i]

        # fontsize= 패턴이 있는지 확인
        match = re.search(r'fontsize=(\d+)', line)
        if not match:
            continue

        old_size = int(match.group(1))

        # 제목 라인이면 스킵
        if is_title_line(line):
            continue

        # suptitle, set_title은 무조건 스킵
        if '.suptitle(' in line or '.set_title(' in line:
            continue

        # 이미 충분히 큰 경우 (24 이상) 제목급이므로 스킵
        if old_size >= 24:
            continue

        # 매핑에 있으면 변환
        if old_size in FONTSIZE_MAP:
            new_size = FONTSIZE_MAP[old_size]
            lines[i] = line.replace(f'fontsize={old_size}', f'fontsize={new_size}', 1)
            changes += 1

    return changes


def process_file(filepath, func_names):
    """파일을 읽고, 대상 함수 내 fontsize를 수정하여 저장"""
    if not os.path.exists(filepath):
        print(f"  [SKIP] 파일 없음: {filepath}")
        return 0

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 대상 함수 범위 추출
    ranges = extract_functions(lines, func_names)
    if not ranges:
        print(f"  [SKIP] 대상 함수 없음: {os.path.basename(filepath)}")
        return 0

    total_changes = 0
    for start, end, fname in ranges:
        n = increase_fontsize_in_range(lines, start, end, fname)
        total_changes += n
        print(f"  [{fname}] L{start+1}~L{end}: {n}개 fontsize 변경")

    if total_changes > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"  ✅ {os.path.basename(filepath)}: 총 {total_changes}개 변경 완료")
    else:
        print(f"  ⚠️ {os.path.basename(filepath)}: 변경사항 없음")

    return total_changes


def main():
    print("=" * 60)
    print("PPT 가시성 향상 — fontsize 자동 증가 스크립트")
    print("=" * 60)

    grand_total = 0
    for filepath, func_names in TARGET_FUNCTIONS.items():
        fname = os.path.basename(filepath)
        print(f"\n📄 {fname} ({len(func_names)}개 함수)")
        n = process_file(filepath, func_names)
        grand_total += n

    print(f"\n{'=' * 60}")
    print(f"총 {grand_total}개 fontsize 값 수정 완료")
    print("=" * 60)


if __name__ == '__main__':
    main()

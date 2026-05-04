"""
menu_test_set.csv 기반 정규화 성능 평가.

pandas 미설치 시 csv 모듈로 폴백.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Optional

from nlp_mvp.menu_normalizer.normalizer import MenuNormalizer
from nlp_mvp.shared.logger import get_logger

logger = get_logger(__name__)


def _load_test_csv(path: Path) -> list[dict[str, str]]:
    """pandas → csv 폴백."""
    try:
        import pandas as pd  # type: ignore
        df = pd.read_csv(path)
        return df.to_dict(orient="records")
    except ImportError:
        import csv
        with open(path, "r", encoding="utf-8") as f:
            return list(csv.DictReader(f))


def evaluate_on_test_set(
    test_csv: str | Path | None = None,
    normalizer: Optional[MenuNormalizer] = None,
) -> dict[str, Any]:
    """평가 지표 계산."""
    if test_csv is None:
        test_csv = Path(__file__).parent.parent / "data" / "menu_test_set.csv"
    test_csv = Path(test_csv)

    rows = _load_test_csv(test_csv)
    if not rows:
        raise ValueError(f"No rows loaded from {test_csv}")
    if "raw_name" not in rows[0] or "expected_id" not in rows[0]:
        raise ValueError("Test CSV must have columns: raw_name, expected_id")

    normalizer = normalizer or MenuNormalizer()

    correct = 0
    matched = 0
    method_counter: Counter = Counter()
    failures: list[dict] = []

    for row in rows:
        raw = row["raw_name"]
        expected = row["expected_id"]
        result = normalizer.normalize(raw)
        method_counter[result.method] += 1

        is_matched = result.matched_id is not None
        is_correct = is_matched and result.matched_id == expected

        if is_matched:
            matched += 1
        if is_correct:
            correct += 1
        else:
            failures.append({
                "raw": raw,
                "expected": expected,
                "predicted": result.matched_id,
                "method": result.method,
                "confidence": round(result.confidence, 3),
            })

    total = len(rows)
    accuracy = correct / total if total else 0.0
    precision = correct / matched if matched else 0.0
    recall = correct / total if total else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    report = {
        "total": total,
        "matched": matched,
        "correct": correct,
        "accuracy": round(accuracy, 3),
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "method_dist": dict(method_counter),
        "failures_top20": failures[:20],
    }

    logger.info(
        f"Evaluation: total={total}, accuracy={accuracy:.3f}, "
        f"precision={precision:.3f}, recall={recall:.3f}, f1={f1:.3f}"
    )
    return report


def print_report(report: dict[str, Any]) -> None:
    print("\n" + "=" * 60)
    print("📊 Menu Normalizer Evaluation Report")
    print("=" * 60)
    print(f"Total:      {report['total']}")
    print(f"Matched:    {report['matched']}")
    print(f"Correct:    {report['correct']}")
    print(f"Accuracy:   {report['accuracy']:.3f}")
    print(f"Precision:  {report['precision']:.3f}")
    print(f"Recall:     {report['recall']:.3f}")
    print(f"F1:         {report['f1']:.3f}")
    print("\n방법별 분포:")
    for method, count in sorted(report["method_dist"].items()):
        print(f"  {method:15s}: {count}")
    print("\n실패 케이스 상위 20:")
    for f in report["failures_top20"]:
        print(
            f"  {f['raw']:20s} → expected={f['expected']}, "
            f"predicted={f['predicted']} ({f['method']}, conf={f['confidence']})"
        )
    print("=" * 60)


def main():
    import argparse
    import json

    parser = argparse.ArgumentParser()
    parser.add_argument("--test-csv", type=str, default=None)
    parser.add_argument("--json", action="store_true", help="JSON 출력")
    parser.add_argument("--disable-embedding", action="store_true")
    args = parser.parse_args()

    normalizer = MenuNormalizer(enable_embedding=not args.disable_embedding)
    report = evaluate_on_test_set(args.test_csv, normalizer=normalizer)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_report(report)


if __name__ == "__main__":
    main()

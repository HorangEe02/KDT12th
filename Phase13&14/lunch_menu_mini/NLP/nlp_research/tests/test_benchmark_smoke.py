"""Smoke test for the unified benchmark harness."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from nlp_research.evaluation.benchmark import parse_args, run, write_summary


def _make_args(tmp_path: Path, module: str = "all"):
    sys.argv = [
        "benchmark",
        "--module", module,
        "--smoke",
        "--output-dir", str(tmp_path),
    ]
    return parse_args()


def test_benchmark_all_modules_smoke(tmp_path: Path):
    args = _make_args(tmp_path, module="all")
    summary = run(args)
    assert "results" in summary
    assert "a2" in summary["results"]
    assert "b2" in summary["results"]
    assert "e1" in summary["results"]
    assert summary["table"], "table should have at least one row"

    write_summary(summary, tmp_path)
    assert (tmp_path / "summary.md").exists()
    parsed = json.loads((tmp_path / "summary.json").read_text())
    assert parsed["smoke"] is True


def test_benchmark_a2_only_smoke(tmp_path: Path):
    args = _make_args(tmp_path, module="a2")
    summary = run(args)
    assert "a2" in summary["results"]
    assert "b2" not in summary["results"]
    assert "e1" not in summary["results"]
    write_summary(summary, tmp_path)
    assert (tmp_path / "a2_vs_a1.md").exists()


def test_benchmark_b2_only_smoke(tmp_path: Path):
    args = _make_args(tmp_path, module="b2")
    summary = run(args)
    assert summary["results"]["b2"]["b1"]
    assert summary["results"]["b2"]["b2"]
    write_summary(summary, tmp_path)
    assert (tmp_path / "b2_vs_b1.md").exists()


def test_benchmark_e1_only_smoke(tmp_path: Path):
    args = _make_args(tmp_path, module="e1")
    summary = run(args)
    e1 = summary["results"]["e1"]
    assert "popular" in e1
    assert "e1" in e1
    write_summary(summary, tmp_path)
    assert (tmp_path / "e1_vs_popular.md").exists()

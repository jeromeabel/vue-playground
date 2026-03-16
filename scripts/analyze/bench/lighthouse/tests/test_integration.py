"""Integration tests - run against real Lighthouse report files."""

import json
from pathlib import Path

import pytest

from bench.lighthouse.extract import extract_metrics

INPUTS_DIR = Path(__file__).resolve().parents[3] / "inputs" / "lighthouse"


def _load_report(name: str) -> dict:
    path = INPUTS_DIR / name
    if not path.exists():
        pytest.skip(f"{name} not present in inputs/lighthouse/")
    with open(path) as file:
        return json.load(file)


@pytest.mark.slow
class TestRealReports:
    def test_basic_report(self):
        metrics = extract_metrics(_load_report("basic.json"))
        assert set(metrics.keys()) == {
            "Score",
            "FCP",
            "LCP",
            "TBT",
            "TTI",
            "SI",
            "Max FID",
            "CLS",
            "DOM Size",
            "MT Work",
        }
        assert isinstance(metrics["Score"], (int, float))
        assert metrics["DOM Size"] > 0

    def test_primevue_report(self):
        metrics = extract_metrics(_load_report("primevue.json"))
        assert metrics["Score"] is not None
        assert metrics["DOM Size"] < 1000

    def test_tanstack_report(self):
        metrics = extract_metrics(_load_report("tanstack.json"))
        assert metrics["Score"] is not None
        assert metrics["DOM Size"] < 1000

    def test_devtools_export_format(self):
        """DevTools-exported reports (v13 format) should also work."""
        metrics = extract_metrics(_load_report("basic-devtools.json"))
        assert "Score" in metrics
        assert metrics["DOM Size"] > 0

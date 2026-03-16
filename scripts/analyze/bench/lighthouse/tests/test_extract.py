"""Tests for bench.lighthouse.extract - metric extraction."""

import pytest

from bench.lighthouse.extract import THRESHOLDS, extract_metrics, status_for

from .conftest import _make_report


class TestExtractMetrics:
    def test_basic_extraction(self):
        report = _make_report(
            fcp=508.9,
            lcp=508.9,
            tbt=0,
            tti=508.9,
            si=508.9,
            fid=16,
            cls_val=0,
            dom_size=80038,
            mt_work=1956.2,
            score=1.0,
        )
        metrics = extract_metrics(report)
        assert metrics["Score"] == 100
        assert metrics["FCP"] == 508.9
        assert metrics["TBT"] == 0.0
        assert metrics["DOM Size"] == 80038

    def test_lcp_error_returns_none(self):
        report = _make_report(lcp_error="NO_LCP: Something went wrong")
        metrics = extract_metrics(report)
        assert metrics["LCP"] is None

    def test_dom_size_v13_fallback(self):
        report = _make_report(dom_size=5000, dom_key="dom-size-insight")
        metrics = extract_metrics(report)
        assert metrics["DOM Size"] == 5000

    def test_dom_size_missing_returns_zero(self):
        report = _make_report()
        del report["audits"]["dom-size"]
        metrics = extract_metrics(report)
        assert metrics["DOM Size"] == 0

    def test_none_score(self):
        report = _make_report()
        report["categories"]["performance"]["score"] = None
        metrics = extract_metrics(report)
        assert metrics["Score"] is None

    def test_rounding(self):
        report = _make_report(fcp=1234.5678, cls_val=0.12345678)
        metrics = extract_metrics(report)
        assert metrics["FCP"] == 1234.6
        assert metrics["CLS"] == 0.1235

    def test_all_keys_present(self):
        metrics = extract_metrics(_make_report())
        expected = {
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
        assert set(metrics.keys()) == expected


class TestThresholds:
    def test_has_all_metrics(self):
        expected = {
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
        assert set(THRESHOLDS.keys()) == expected

    def test_each_has_good_poor_unit(self):
        for metric, threshold in THRESHOLDS.items():
            assert "good" in threshold, f"{metric} missing 'good'"
            assert "poor" in threshold, f"{metric} missing 'poor'"
            assert "unit" in threshold, f"{metric} missing 'unit'"


class TestStatusFor:
    @pytest.mark.parametrize(
        "metric,value,expected",
        [
            ("TBT", 100, "pass"),
            ("TBT", 200, "pass"),
            ("TBT", 201, "warn"),
            ("TBT", 600, "warn"),
            ("TBT", 601, "fail"),
            ("DOM Size", 1500, "pass"),
            ("DOM Size", 3001, "fail"),
            ("Score", 95, "pass"),
            ("Score", 50, "warn"),
            ("Score", 49, "fail"),
        ],
    )
    def test_thresholds(self, metric, value, expected):
        assert status_for(metric, value) == expected

    def test_none_value(self):
        assert status_for("TBT", None) == "error"

    def test_unknown_metric(self):
        assert status_for("UnknownMetric", 42) is None

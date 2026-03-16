"""Tests for analyze_lighthouse.py — metric extraction and formatting."""
import pytest
from analyze_lighthouse import extract_metrics, status_emoji, score_emoji, format_value, to_json, _generate_insights


# -- Fixtures ----------------------------------------------------------------

def _make_audit(numeric_value=None, error_message=None):
    """Build a minimal Lighthouse audit dict."""
    audit = {"id": "test"}
    if numeric_value is not None:
        audit["numericValue"] = numeric_value
    if error_message is not None:
        audit["errorMessage"] = error_message
    return audit


def _make_report(
    *,
    fcp=500, lcp=500, tbt=0, tti=500, si=500, fid=16, cls=0,
    dom_size=1000, dom_key="dom-size", mt_work=200, score=1.0,
    lcp_error=None,
):
    """Build a minimal Lighthouse report dict."""
    audits = {
        "first-contentful-paint": _make_audit(fcp),
        "largest-contentful-paint": _make_audit(lcp, error_message=lcp_error),
        "total-blocking-time": _make_audit(tbt),
        "interactive": _make_audit(tti),
        "speed-index": _make_audit(si),
        "max-potential-fid": _make_audit(fid),
        "cumulative-layout-shift": _make_audit(cls),
        dom_key: _make_audit(dom_size),
        "mainthread-work-breakdown": _make_audit(mt_work),
    }
    return {
        "audits": audits,
        "categories": {"performance": {"score": score}},
    }


# -- extract_metrics ---------------------------------------------------------

class TestExtractMetrics:
    def test_basic_extraction(self):
        report = _make_report(fcp=508.9, lcp=508.9, tbt=0, tti=508.9,
                              si=508.9, fid=16, cls=0, dom_size=80038,
                              mt_work=1956.2, score=1.0)
        m = extract_metrics(report)

        assert m["Score"] == 100
        assert m["FCP"] == 508.9
        assert m["LCP"] == 508.9
        assert m["TBT"] == 0.0
        assert m["DOM Size"] == 80038
        assert m["CLS"] == 0.0

    def test_lcp_error_returns_none(self):
        """When LCP can't be detected (NO_LCP), it should return None."""
        report = _make_report(lcp_error="NO_LCP: Something went wrong")
        m = extract_metrics(report)
        assert m["LCP"] is None

    def test_dom_size_v13_fallback(self):
        """Lighthouse 13 uses 'dom-size-insight' instead of 'dom-size'."""
        report = _make_report(dom_size=5000, dom_key="dom-size-insight")
        m = extract_metrics(report)
        assert m["DOM Size"] == 5000

    def test_dom_size_missing_returns_zero(self):
        """If neither dom-size key exists, return 0."""
        report = _make_report()
        del report["audits"]["dom-size"]
        m = extract_metrics(report)
        assert m["DOM Size"] == 0

    def test_none_score(self):
        """Score can be None if performance category is missing."""
        report = _make_report()
        report["categories"]["performance"]["score"] = None
        m = extract_metrics(report)
        assert m["Score"] is None

    def test_rounding(self):
        """Numeric values should be rounded appropriately."""
        report = _make_report(fcp=1234.5678, cls=0.12345678)
        m = extract_metrics(report)
        assert m["FCP"] == 1234.6  # 1 decimal
        assert m["CLS"] == 0.1235  # 4 decimals


# -- status_emoji / score_emoji ----------------------------------------------

class TestStatusEmoji:
    @pytest.mark.parametrize("metric,value,expected", [
        ("TBT", 100, "pass"),
        ("TBT", 200, "pass"),     # at boundary = pass
        ("TBT", 201, "warn"),
        ("TBT", 600, "warn"),     # at boundary = warn
        ("TBT", 601, "FAIL"),
        ("LCP", 2500, "pass"),
        ("LCP", 4001, "FAIL"),
        ("CLS", 0.05, "pass"),
        ("CLS", 0.15, "warn"),
        ("CLS", 0.30, "FAIL"),
        ("DOM Size", 1500, "pass"),
        ("DOM Size", 3001, "FAIL"),
    ])
    def test_thresholds(self, metric, value, expected):
        assert status_emoji(metric, value) == expected

    def test_none_value(self):
        assert status_emoji("TBT", None) == "ERR"

    def test_unknown_metric(self):
        assert status_emoji("UnknownMetric", 42) == ""

    @pytest.mark.parametrize("score,expected", [
        (95, "pass"),
        (90, "pass"),
        (89, "warn"),
        (50, "warn"),
        (49, "FAIL"),
        (None, ""),
    ])
    def test_score_emoji(self, score, expected):
        assert score_emoji(score) == expected


# -- format_value ------------------------------------------------------------

class TestFormatValue:
    def test_none(self):
        assert format_value("TBT", None) == "N/A"

    def test_score(self):
        assert format_value("Score", 95.0) == "95/100"

    def test_cls(self):
        assert format_value("CLS", 0.1234) == "0.1234"

    def test_dom_size(self):
        assert format_value("DOM Size", 80038) == "80,038"

    def test_time_metric_with_seconds(self):
        """FCP/LCP/TTI/SI show both ms and seconds."""
        result = format_value("FCP", 2500)
        assert "2,500 ms" in result
        assert "2.50s" in result

    def test_plain_ms_metric(self):
        """TBT, Max FID show only ms."""
        result = format_value("TBT", 150)
        assert result == "150 ms"


# -- to_json -----------------------------------------------------------------

class TestToJson:
    def test_envelope_structure(self):
        data = {"basic": extract_metrics(_make_report())}
        result = to_json(data)

        assert result["version"] == 1
        assert "generatedAt" in result
        assert "config" in result
        assert "thresholds" in result
        assert "approaches" in result
        assert "basic" in result["approaches"]

    def test_metrics_filter(self):
        data = {"basic": extract_metrics(_make_report())}
        result = to_json(data, metrics_filter=["TBT", "LCP"])

        approach = result["approaches"]["basic"]
        assert set(approach.keys()) == {"TBT", "LCP"}

    def test_thresholds_included(self):
        data = {"basic": extract_metrics(_make_report())}
        result = to_json(data)

        assert "TBT" in result["thresholds"]
        assert result["thresholds"]["TBT"]["good"] == 200
        assert result["thresholds"]["TBT"]["poor"] == 600


# -- _generate_insights ------------------------------------------------------

class TestInsights:
    def test_ratio_insight(self):
        """When one approach is 2x+ worse, an insight should be generated."""
        data = {
            "fast": extract_metrics(_make_report(tbt=100)),
            "slow": extract_metrics(_make_report(tbt=500)),
        }
        insights = _generate_insights(data, ["fast", "slow"])
        tbt_insights = [i for i in insights if "Total Blocking Time" in i]
        assert len(tbt_insights) >= 1
        assert "slow" in tbt_insights[0]

    def test_no_ratio_insight_when_close(self):
        """No ratio insight when values are similar."""
        data = {
            "a": extract_metrics(_make_report(tbt=100)),
            "b": extract_metrics(_make_report(tbt=150)),
        }
        insights = _generate_insights(data, ["a", "b"])
        tbt_insights = [i for i in insights if "Total Blocking Time" in i]
        assert len(tbt_insights) == 0

    def test_unmeasured_lcp_insight(self):
        """When LCP is None, insight should mention NO_LCP."""
        data = {
            "ok": extract_metrics(_make_report(lcp=2000)),
            "broken": extract_metrics(_make_report(lcp_error="NO_LCP")),
        }
        insights = _generate_insights(data, ["ok", "broken"])
        lcp_insights = [i for i in insights if "NO_LCP" in i]
        assert len(lcp_insights) >= 1

    def test_fail_flagging(self):
        """Approaches that fail thresholds should be flagged."""
        data = {
            "bad": extract_metrics(_make_report(tbt=1000, dom_size=5000)),
        }
        insights = _generate_insights(data, ["bad"])
        fail_insights = [i for i in insights if "fails on" in i]
        assert len(fail_insights) >= 1


# -- Integration: real report file -------------------------------------------

class TestRealReport:
    """Run against the actual report files to catch format drift."""

    @pytest.fixture
    def basic_report(self):
        import json
        from pathlib import Path
        p = Path(__file__).parent / "reports" / "basic.json"
        if not p.exists():
            pytest.skip("basic.json not present")
        with open(p) as f:
            return json.load(f)

    def test_extract_from_real_report(self, basic_report):
        m = extract_metrics(basic_report)
        # Must have all expected keys
        expected_keys = {"Score", "FCP", "LCP", "TBT", "TTI", "SI", "Max FID", "CLS", "DOM Size", "MT Work"}
        assert set(m.keys()) == expected_keys
        # Score should be a number
        assert isinstance(m["Score"], (int, float))
        # DOM Size should be positive for basic-table (renders 3000 rows)
        assert m["DOM Size"] > 0

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analyze_lighthouse import extract_metrics, status_emoji


def test_returns_all_ten_keys(lighthouse_basic):
    metrics = extract_metrics(lighthouse_basic)
    expected_keys = {"Score", "FCP", "LCP", "TBT", "TTI", "SI", "Max FID", "CLS", "DOM Size", "MT Work"}
    assert set(metrics.keys()) == expected_keys


def test_score_is_percentage(lighthouse_basic):
    metrics = extract_metrics(lighthouse_basic)
    assert isinstance(metrics["Score"], int)
    assert 0 <= metrics["Score"] <= 100


def test_known_basic_values(lighthouse_basic):
    """Validate extraction against CLI lighthouse@12 report (no CPU throttling)."""
    metrics = extract_metrics(lighthouse_basic)
    assert metrics["Score"] == 100
    assert metrics["DOM Size"] == 80038
    assert 400 <= metrics["FCP"] <= 600


def test_known_primevue_values(lighthouse_primevue):
    metrics = extract_metrics(lighthouse_primevue)
    assert metrics["Score"] == 99
    assert metrics["DOM Size"] == 495


def test_known_tanstack_values(lighthouse_tanstack):
    metrics = extract_metrics(lighthouse_tanstack)
    assert metrics["Score"] == 99
    assert metrics["DOM Size"] == 327


def test_missing_audit_returns_none():
    """Missing audits return None (not 0) to distinguish from measured zeros."""
    report = {"audits": {}, "categories": {"performance": {"score": 0.5}}}
    metrics = extract_metrics(report)
    assert metrics["FCP"] is None
    assert metrics["LCP"] is None
    assert metrics["TBT"] is None
    assert metrics["TTI"] is None
    assert metrics["SI"] is None


def test_error_audit_returns_none():
    """Audits with errorMessage (e.g. NO_LCP) return None."""
    report = {
        "audits": {
            "largest-contentful-paint": {"errorMessage": "NO_LCP"},
            "total-blocking-time": {"errorMessage": "NO_LCP"},
            "first-contentful-paint": {"numericValue": 475.5},
        },
        "categories": {"performance": {"score": None}},
    }
    metrics = extract_metrics(report)
    assert metrics["LCP"] is None
    assert metrics["TBT"] is None
    assert metrics["FCP"] == 475.5


def test_dom_size_fallback_to_insight():
    """When dom-size audit is missing, fall back to dom-size-insight (Lighthouse 13)."""
    report = {
        "audits": {
            "dom-size-insight": {"numericValue": 497},
        },
        "categories": {"performance": {"score": 0.98}},
    }
    metrics = extract_metrics(report)
    assert metrics["DOM Size"] == 497


def test_dom_size_prefers_dom_size_over_insight():
    """When both exist, prefer dom-size (Lighthouse 12)."""
    report = {
        "audits": {
            "dom-size": {"numericValue": 80038},
            "dom-size-insight": {"numericValue": 40},
        },
        "categories": {"performance": {"score": 1.0}},
    }
    metrics = extract_metrics(report)
    assert metrics["DOM Size"] == 80038


def test_missing_score_returns_none():
    report = {"audits": {}}
    metrics = extract_metrics(report)
    assert metrics["Score"] is None


def test_status_emoji_thresholds():
    assert status_emoji("FCP", 1000) == "pass"
    assert status_emoji("FCP", 2500) == "warn"
    assert status_emoji("FCP", 4000) == "FAIL"
    assert status_emoji("Score", 50) == ""


def test_status_emoji_none_returns_err():
    assert status_emoji("LCP", None) == "ERR"

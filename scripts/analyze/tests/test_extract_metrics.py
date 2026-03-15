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
    metrics = extract_metrics(lighthouse_basic)
    assert metrics["Score"] == 92
    assert metrics["DOM Size"] == 382
    assert 900 <= metrics["FCP"] <= 1200


def test_known_primevue_values(lighthouse_primevue):
    metrics = extract_metrics(lighthouse_primevue)
    assert metrics["Score"] == 72
    assert metrics["DOM Size"] == 407


def test_known_tanstack_values(lighthouse_tanstack):
    metrics = extract_metrics(lighthouse_tanstack)
    assert metrics["Score"] == 74
    assert metrics["DOM Size"] == 671


def test_missing_audit_returns_zero():
    report = {"audits": {}, "categories": {"performance": {"score": 0.5}}}
    metrics = extract_metrics(report)
    assert metrics["FCP"] == 0
    assert metrics["LCP"] == 0
    assert metrics["TBT"] == 0
    assert metrics["TTI"] == 0
    assert metrics["SI"] == 0


def test_missing_score_returns_none():
    report = {"audits": {}}
    metrics = extract_metrics(report)
    assert metrics["Score"] is None


def test_status_emoji_thresholds():
    assert status_emoji("FCP", 1000) == "pass"
    assert status_emoji("FCP", 2500) == "warn"
    assert status_emoji("FCP", 4000) == "FAIL"
    assert status_emoji("Score", 50) == ""

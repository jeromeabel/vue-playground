import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analyze_lighthouse import extract_metrics, status_emoji


def test_returns_all_ten_keys(lighthouse_before):
    metrics = extract_metrics(lighthouse_before)
    expected_keys = {"Score", "FCP", "LCP", "TBT", "TTI", "SI", "Max FID", "CLS", "DOM Size", "MT Work"}
    assert set(metrics.keys()) == expected_keys


def test_score_is_percentage(lighthouse_before):
    metrics = extract_metrics(lighthouse_before)
    assert isinstance(metrics["Score"], int)
    assert 0 <= metrics["Score"] <= 100


def test_known_baseline_values(lighthouse_before):
    metrics = extract_metrics(lighthouse_before)
    assert metrics["Score"] == 33
    assert metrics["DOM Size"] == 6366
    assert 5900 <= metrics["FCP"] <= 6100


def test_known_phase3_values(lighthouse_phase3):
    metrics = extract_metrics(lighthouse_phase3)
    assert metrics["Score"] == 42
    assert metrics["DOM Size"] == 1705


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

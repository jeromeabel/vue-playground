import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analyze_lighthouse import to_json as lighthouse_to_json, extract_metrics
from analyze_trace import to_json as trace_to_json
import pytest


def test_lighthouse_to_json_schema(lighthouse_before):
    metrics = extract_metrics(lighthouse_before)
    result = lighthouse_to_json({"before": metrics})
    assert set(result.keys()) == {"version", "generatedAt", "config", "thresholds", "approaches", "metrics"}
    assert result["version"] == 1
    assert isinstance(result["config"], dict)
    assert "iterations" in result["config"]


@pytest.mark.slow
def test_trace_to_json_schema(trace_before_path):
    from analyze_trace import analyze_trace
    trace_metrics = analyze_trace(trace_before_path)
    result = trace_to_json({"before": trace_metrics})
    assert set(result.keys()) == {"version", "generatedAt", "config", "thresholds", "approaches", "metrics"}


def test_thresholds_included(lighthouse_before):
    metrics = extract_metrics(lighthouse_before)
    result = lighthouse_to_json({"before": metrics})
    assert "FCP" in result["thresholds"]
    assert set(result["thresholds"]["FCP"].keys()) == {"good", "poor", "unit"}


def test_json_is_parseable(lighthouse_before):
    metrics = extract_metrics(lighthouse_before)
    result = lighthouse_to_json({"before": metrics})
    serialized = json.dumps(result)
    restored = json.loads(serialized)
    assert restored == result


def test_metrics_filter(lighthouse_before):
    metrics = extract_metrics(lighthouse_before)
    result = lighthouse_to_json({"before": metrics}, metrics_filter=["Score", "TBT"])
    for approach_metrics in result["approaches"].values():
        assert set(approach_metrics.keys()) == {"Score", "TBT"}

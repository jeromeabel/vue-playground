import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analyze_lighthouse import to_json as lighthouse_to_json, extract_metrics


def test_lighthouse_to_json_schema(lighthouse_basic):
    metrics = extract_metrics(lighthouse_basic)
    result = lighthouse_to_json({"basic": metrics})
    assert set(result.keys()) == {"version", "generatedAt", "config", "thresholds", "approaches", "metrics"}
    assert result["version"] == 1
    assert isinstance(result["config"], dict)
    assert "iterations" in result["config"]


def test_thresholds_included(lighthouse_basic):
    metrics = extract_metrics(lighthouse_basic)
    result = lighthouse_to_json({"basic": metrics})
    assert "FCP" in result["thresholds"]
    assert set(result["thresholds"]["FCP"].keys()) == {"good", "poor", "unit"}


def test_json_is_parseable(lighthouse_basic):
    metrics = extract_metrics(lighthouse_basic)
    result = lighthouse_to_json({"basic": metrics})
    serialized = json.dumps(result)
    restored = json.loads(serialized)
    assert restored == result


def test_metrics_filter(lighthouse_basic):
    metrics = extract_metrics(lighthouse_basic)
    result = lighthouse_to_json({"basic": metrics}, metrics_filter=["Score", "TBT"])
    for approach_metrics in result["approaches"].values():
        assert set(approach_metrics.keys()) == {"Score", "TBT"}

"""Tests for bench.formats — JSON envelope builders."""
import json
from bench.formats import analysis_to_json, comparison_to_json


class TestAnalysisToJson:
    def test_envelope_structure(self):
        result = analysis_to_json(
            metrics={"Score": 100, "TBT": 0},
            source={"filename": "basic.json", "url": "http://localhost:4173/"},
            analysis_type="lighthouse",
            thresholds={"Score": {"good": 90, "poor": 50, "unit": "points"}},
        )
        assert result["version"] == 1
        assert result["type"] == "lighthouse"
        assert "generatedAt" in result
        assert result["source"]["filename"] == "basic.json"
        assert result["metrics"]["Score"] == 100
        assert result["thresholds"]["Score"]["good"] == 90

    def test_roundtrip_json(self):
        result = analysis_to_json(
            metrics={"fps": 60.0},
            source={"filename": "trace.json"},
            analysis_type="trace",
            thresholds={},
        )
        serialized = json.dumps(result)
        restored = json.loads(serialized)
        assert restored == result


class TestComparisonToJson:
    def test_envelope_structure(self):
        result = comparison_to_json(
            approaches={"Basic": {"TBT": 0}, "PrimeVue": {"TBT": 73}},
            config={"iterations": 1, "aggregation": "single", "preset": "desktop"},
            thresholds={"TBT": {"good": 200, "poor": 600, "unit": "ms"}},
            metric_keys=["TBT"],
        )
        assert result["version"] == 1
        assert "generatedAt" in result
        assert result["config"]["preset"] == "desktop"
        assert result["approaches"]["Basic"]["TBT"] == 0
        assert result["metrics"] == ["TBT"]
        assert "TBT" in result["thresholds"]

    def test_thresholds_filtered_to_included_metrics(self):
        result = comparison_to_json(
            approaches={"A": {"TBT": 100}},
            config={},
            thresholds={
                "TBT": {"good": 200, "poor": 600, "unit": "ms"},
                "LCP": {"good": 2500, "poor": 4000, "unit": "ms"},
            },
            metric_keys=["TBT"],
        )
        assert "TBT" in result["thresholds"]
        assert "LCP" not in result["thresholds"]

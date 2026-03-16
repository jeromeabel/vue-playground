"""Tests for the packaged bench CLI."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bench.cli import main
from bench.lighthouse.tests.conftest import _make_report
from bench.trace.tests.conftest import _make_events


def _read_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


class TestMain:
    def test_prints_help_when_no_command(self, capsys):
        with pytest.raises(SystemExit) as error:
            main([])

        captured = capsys.readouterr()
        assert error.value.code == 1
        assert "usage: bench" in captured.out


class TestAnalyze:
    def test_analyze_lighthouse_writes_analysis_json(self, tmp_path, capsys):
        input_path = tmp_path / "basic.json"
        input_path.write_text(json.dumps(_make_report()), encoding="utf-8")
        output_path = tmp_path / "basic.lighthouse.json"

        main(["analyze", "lighthouse", str(input_path), "--name", "basic", "-o", str(output_path)])

        payload = _read_json(output_path)
        captured = capsys.readouterr()
        assert payload["type"] == "lighthouse"
        assert payload["source"]["filename"] == "basic.json"
        assert payload["metrics"]["Score"] == 100
        assert "Saved lighthouse analysis" in captured.err

    def test_analyze_trace_requires_name(self):
        with pytest.raises(SystemExit) as error:
            main(["analyze", "trace", "trace.json"])

        assert error.value.code == 2

    def test_analyze_trace_writes_analysis_json(self, tmp_path, capsys):
        input_path = tmp_path / "Trace-basic.json"
        input_path.write_text(json.dumps({"traceEvents": _make_events()}), encoding="utf-8")
        output_path = tmp_path / "basic.trace.json"

        main(["analyze", "trace", str(input_path), "--name", "basic", "-o", str(output_path)])

        payload = _read_json(output_path)
        captured = capsys.readouterr()
        assert payload["type"] == "trace"
        assert payload["source"]["filename"] == "Trace-basic.json"
        assert payload["metrics"]["frames_committed"] >= 1
        assert "Saved trace analysis" in captured.err


class TestCompare:
    def test_compare_writes_json_with_display_labels(self, tmp_path):
        first = tmp_path / "basic.lighthouse.json"
        second = tmp_path / "primevue.lighthouse.json"
        config_path = tmp_path / "benchmark-config.json"
        output_path = tmp_path / "comparison.json"

        first.write_text(json.dumps({
            "version": 1,
            "type": "lighthouse",
            "generatedAt": "2026-01-01T00:00:00Z",
            "source": {"filename": "basic.json"},
            "metrics": {"Score": 100, "TBT": 0, "LCP": 500, "DOM Size": 1000},
            "thresholds": {},
        }), encoding="utf-8")
        second.write_text(json.dumps({
            "version": 1,
            "type": "lighthouse",
            "generatedAt": "2026-01-01T00:00:00Z",
            "source": {"filename": "primevue.json"},
            "metrics": {"Score": 98, "TBT": 70, "LCP": 650, "DOM Size": 500},
            "thresholds": {},
        }), encoding="utf-8")
        config_path.write_text(json.dumps({
            "capture": {"iterations": 5, "aggregation": "median", "preset": "desktop"},
            "display": {
                "lighthouse": {"primary": ["Score", "TBT"], "secondary": ["LCP"], "hidden": ["DOM Size"]},
                "trace": {"primary": [], "secondary": [], "hidden": []},
            },
            "approaches": {
                "basic": {"label": "Basic Table"},
                "primevue": {"label": "PrimeVue DataTable"},
            },
        }), encoding="utf-8")

        main([
            "compare",
            str(first),
            str(second),
            "--config",
            str(config_path),
            "--json-out",
            str(output_path),
            "--no-markdown",
        ])

        payload = _read_json(output_path)
        assert payload["config"]["aggregation"] == "median"
        assert set(payload["approaches"]) == {"Basic Table", "PrimeVue DataTable"}
        assert payload["metrics"] == ["Score", "TBT", "LCP"]
        assert "DOM Size" not in payload["approaches"]["Basic Table"]

    def test_compare_rejects_mixed_analysis_types(self, tmp_path, capsys):
        lighthouse = tmp_path / "basic.lighthouse.json"
        trace = tmp_path / "basic.trace.json"

        lighthouse.write_text(json.dumps({
            "version": 1,
            "type": "lighthouse",
            "generatedAt": "2026-01-01T00:00:00Z",
            "source": {"filename": "basic.json"},
            "metrics": {"Score": 100},
            "thresholds": {},
        }), encoding="utf-8")
        trace.write_text(json.dumps({
            "version": 1,
            "type": "trace",
            "generatedAt": "2026-01-01T00:00:00Z",
            "source": {"filename": "basic.json"},
            "metrics": {"fps": 60},
            "thresholds": {},
        }), encoding="utf-8")

        with pytest.raises(SystemExit) as error:
            main(["compare", str(lighthouse), str(trace), "--no-markdown"])

        captured = capsys.readouterr()
        assert error.value.code == 1
        assert "cannot compare analyses of different types" in captured.err

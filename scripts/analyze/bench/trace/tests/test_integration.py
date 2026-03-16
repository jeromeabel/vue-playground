"""Integration tests - run against real Chrome trace files."""

import json
from pathlib import Path

import pytest

from bench.trace.extract import analyze_trace

INPUTS_DIR = Path(__file__).resolve().parents[3] / "inputs" / "traces"


def _load_trace(pattern: str) -> list[dict]:
    """Load the first trace matching the glob pattern."""
    matches = sorted(INPUTS_DIR.glob(pattern))
    if not matches:
        pytest.skip(f"No trace matching {pattern} in inputs/traces/")
    with open(matches[0]) as file:
        data = json.load(file)
    return data if isinstance(data, list) else data.get("traceEvents", [])


@pytest.mark.slow
class TestRealTraces:
    def test_basic_trace(self):
        events = _load_trace("*basic*")
        result = analyze_trace(events)
        assert result is not None
        assert result["source"]["duration_s"] > 0
        assert isinstance(result["metrics"]["long_tasks_count"], int)
        assert isinstance(result["source"]["has_interaction"], bool)

    def test_lighthouse_json_returns_none(self):
        """A Lighthouse report has no CrRendererMain - should return None."""
        lighthouse_dir = INPUTS_DIR.parent / "lighthouse"
        basic = lighthouse_dir / "basic.json"
        if not basic.exists():
            pytest.skip("basic.json not present")
        with open(basic) as file:
            data = json.load(file)
        events = data if isinstance(data, list) else data.get("traceEvents", [])
        assert analyze_trace(events) is None

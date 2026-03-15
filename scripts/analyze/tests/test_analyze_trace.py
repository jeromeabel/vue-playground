import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analyze_trace import analyze_trace, _is_profiler_artifact
import pytest


@pytest.mark.slow
def test_returns_dict_for_valid_trace(trace_before_path):
    result = analyze_trace(trace_before_path)
    assert result is not None
    assert isinstance(result, dict)


@pytest.mark.slow
def test_returns_none_for_lighthouse_json(lighthouse_before, tmp_path):
    tmp_file = tmp_path / "lighthouse.json"
    tmp_file.write_text(json.dumps(lighthouse_before))
    result = analyze_trace(str(tmp_file))
    assert result is None


@pytest.mark.slow
def test_known_baseline_fps(trace_before_path):
    result = analyze_trace(trace_before_path)
    assert 40 <= result["fps"] <= 55


@pytest.mark.slow
def test_known_baseline_longest_task(trace_before_path):
    result = analyze_trace(trace_before_path)
    assert 200 <= result["longest_task_ms"] <= 300


@pytest.mark.slow
def test_long_tasks_sorted_descending(trace_before_path):
    result = analyze_trace(trace_before_path)
    tasks = result["top_long_tasks_ms"]
    for i in range(len(tasks) - 1):
        assert tasks[i] >= tasks[i + 1]


@pytest.mark.slow
def test_category_breakdown_positive(trace_before_path):
    result = analyze_trace(trace_before_path)
    assert result["scripting_ms"] + result["rendering_ms"] + result["painting_ms"] > 0


def test_profiler_artifact_filtering():
    parent = {"pid": 1, "tid": 1, "ph": "X", "name": "RunTask", "ts": 100, "dur": 5000}
    profiler_event = {"pid": 1, "tid": 1, "ph": "X", "name": "CpuProfiler::StartProfiling", "ts": 200, "dur": 4000}
    events = [parent, profiler_event]
    assert _is_profiler_artifact(parent, events) is True

    non_profiler = {"pid": 1, "tid": 1, "ph": "X", "name": "SomeOtherTask", "ts": 200, "dur": 4000}
    assert _is_profiler_artifact(parent, [parent, non_profiler]) is False

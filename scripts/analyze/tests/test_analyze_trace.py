import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analyze_trace import analyze_trace, _is_profiler_artifact


def test_returns_none_for_lighthouse_json(lighthouse_basic, tmp_path):
    tmp_file = tmp_path / "lighthouse.json"
    tmp_file.write_text(json.dumps(lighthouse_basic))
    result = analyze_trace(str(tmp_file))
    assert result is None


def test_profiler_artifact_filtering():
    parent = {"pid": 1, "tid": 1, "ph": "X", "name": "RunTask", "ts": 100, "dur": 5000}
    profiler_event = {"pid": 1, "tid": 1, "ph": "X", "name": "CpuProfiler::StartProfiling", "ts": 200, "dur": 4000}
    events = [parent, profiler_event]
    assert _is_profiler_artifact(parent, events) is True

    non_profiler = {"pid": 1, "tid": 1, "ph": "X", "name": "SomeOtherTask", "ts": 200, "dur": 4000}
    assert _is_profiler_artifact(parent, [parent, non_profiler]) is False

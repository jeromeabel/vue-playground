import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analyze_trace import analyze_trace, _is_profiler_artifact, normalize_traces


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


def test_normalize_traces_skips_single_trace():
    data = {"A": {"duration_s": 5.0, "long_tasks_count": 3, "scripting_ms": 500.0}}
    result, ref = normalize_traces(data)
    assert ref is None
    assert result is data


def test_normalize_traces_skips_within_tolerance():
    data = {
        "A": {"duration_s": 5.00, "long_tasks_count": 3, "scripting_ms": 500.0},
        "B": {"duration_s": 5.04, "long_tasks_count": 4, "scripting_ms": 600.0},
    }
    result, ref = normalize_traces(data, tolerance_pct=1.0)
    assert ref is None


def test_normalize_traces_scales_counts_and_totals():
    data = {
        "Short": {
            "duration_s": 5.0,
            "scripting_ms": 500.0,
            "rendering_ms": 100.0,
            "painting_ms": 50.0,
            "long_tasks_count": 4,
            "frames_committed": 200,
            "fps": 40.0,
        },
        "Long": {
            "duration_s": 10.0,
            "scripting_ms": 1000.0,
            "rendering_ms": 200.0,
            "painting_ms": 100.0,
            "long_tasks_count": 8,
            "frames_committed": 400,
            "fps": 40.0,
        },
    }
    result, ref = normalize_traces(data, tolerance_pct=1.0)

    assert ref == 5.0
    # Short trace unchanged (it IS the reference)
    assert result["Short"]["long_tasks_count"] == 4
    assert result["Short"]["scripting_ms"] == 500.0

    # Long trace scaled down by 0.5
    assert result["Long"]["long_tasks_count"] == 4  # 8 * 0.5
    assert result["Long"]["scripting_ms"] == 500.0  # 1000 * 0.5
    assert result["Long"]["frames_committed"] == 200  # 400 * 0.5
    assert result["Long"]["duration_s"] == 5.0
    assert result["Long"]["original_duration_s"] == 10.0

    # FPS (rate metric) is preserved — not scaled
    assert result["Long"]["fps"] == 40.0


def test_normalize_traces_preserves_peak_metrics():
    data = {
        "A": {"duration_s": 5.0, "longest_task_ms": 300.0, "long_tasks_count": 3,
               "scripting_ms": 400.0, "rendering_ms": 80.0, "painting_ms": 30.0},
        "B": {"duration_s": 10.0, "longest_task_ms": 150.0, "long_tasks_count": 6,
               "scripting_ms": 800.0, "rendering_ms": 160.0, "painting_ms": 60.0},
    }
    result, _ = normalize_traces(data, tolerance_pct=1.0)

    # Peak metric NOT scaled
    assert result["B"]["longest_task_ms"] == 150.0

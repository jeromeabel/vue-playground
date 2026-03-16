"""Tests for bench.trace.extract - trace parsing and metrics."""

import pytest

from bench.trace.extract import (
    THRESHOLDS,
    _is_profiler_artifact,
    analyze_trace,
    categorize,
    find_main_threads,
)

from .conftest import _duration_event, _make_events, _thread_name_event


class TestFindMainThreads:
    def test_finds_renderer_main(self):
        events = [
            _thread_name_event(100, 1, "CrRendererMain"),
            _thread_name_event(100, 2, "Compositor"),
            _thread_name_event(200, 1, "CrBrowserMain"),
        ]
        assert find_main_threads(events) == {(100, 1)}

    def test_multiple_renderer_mains(self):
        events = [
            _thread_name_event(100, 1, "CrRendererMain"),
            _thread_name_event(200, 1, "CrRendererMain"),
        ]
        assert len(find_main_threads(events)) == 2

    def test_empty_events(self):
        assert find_main_threads([]) == set()


class TestCategorize:
    @pytest.mark.parametrize(
        "name,expected",
        [
            ("FunctionCall", "Scripting"),
            ("EvaluateScript", "Scripting"),
            ("Layout", "Rendering"),
            ("RecalculateStyles", "Rendering"),
            ("Paint", "Painting"),
            ("CompositeLayers", "Painting"),
            ("SomeRandomEvent", "Other"),
        ],
    )
    def test_categories(self, name, expected):
        assert categorize(name) == expected


class TestIsProfilerArtifact:
    def test_detects_profiler_artifact(self):
        pid, tid = 100, 1
        parent = _duration_event(pid, tid, "RunTask", 1000, 60_000)
        child = _duration_event(pid, tid, "CpuProfiler::StartProfiling", 2000, 50_000)
        assert _is_profiler_artifact(parent, [parent, child]) is True

    def test_normal_task_not_artifact(self):
        pid, tid = 100, 1
        parent = _duration_event(pid, tid, "RunTask", 1000, 60_000)
        child = _duration_event(pid, tid, "FunctionCall", 2000, 50_000)
        assert _is_profiler_artifact(parent, [parent, child]) is False


class TestAnalyzeTrace:
    def test_basic_trace(self):
        events = _make_events(num_tasks=3)
        result = analyze_trace(events)
        assert result is not None
        assert result["source"]["duration_s"] > 0
        assert result["metrics"]["scripting_ms"] > 0
        assert result["metrics"]["rendering_ms"] > 0
        assert result["metrics"]["painting_ms"] > 0
        assert result["metrics"]["fps"] > 0

    def test_long_task_detection(self):
        events = _make_events(include_long_task=True)
        result = analyze_trace(events)
        assert result["metrics"]["long_tasks_count"] >= 1
        assert result["metrics"]["longest_task_ms"] >= 200

    def test_no_long_tasks(self):
        events = _make_events(num_tasks=3, task_dur_us=30_000)
        result = analyze_trace(events)
        assert result["metrics"]["long_tasks_count"] == 0
        assert result["metrics"]["longest_task_ms"] == 0

    def test_empty_events_returns_none(self):
        assert analyze_trace([]) is None

    def test_no_main_thread_returns_none(self):
        events = [_thread_name_event(100, 1, "Compositor")]
        assert analyze_trace(events) is None

    def test_profiler_artifacts_excluded(self):
        pid, tid = 100, 1
        events = [
            _thread_name_event(pid, tid, "CrRendererMain"),
            _duration_event(pid, tid, "RunTask", 1_000_000, 100_000),
            _duration_event(pid, tid, "CpuProfiler::StartProfiling", 1_001_000, 98_000),
            _duration_event(pid, tid, "FunctionCall", 1_200_000, 10_000),
        ]
        result = analyze_trace(events)
        assert result["metrics"]["long_tasks_count"] == 0

    def test_null_for_absent_optional_metrics(self):
        """Absent rAF/AF metrics should be null, not omitted."""
        events = _make_events(num_tasks=2)
        result = analyze_trace(events)
        metrics = result["metrics"]
        assert "raf_count" in metrics
        assert "af_count" in metrics
        assert metrics["raf_total_ms"] is None
        assert metrics["af_mean_ms"] is None

    def test_source_and_metrics_separated(self):
        """Result has distinct source and metrics dicts."""
        events = _make_events(num_tasks=2)
        result = analyze_trace(events)
        assert "source" in result
        assert "metrics" in result
        assert "duration_s" not in result["metrics"]
        assert "has_interaction" not in result["metrics"]
        assert "has_scroll" not in result["metrics"]

    def test_scroll_interaction_detection(self):
        pid, tid = 100, 1
        events = [
            _thread_name_event(pid, tid, "CrRendererMain"),
            _duration_event(pid, tid, "FunctionCall", 1_000_000, 30_000),
            {
                "ph": "X",
                "name": "EventDispatch",
                "pid": pid,
                "tid": tid,
                "ts": 1_050_000,
                "dur": 1000,
                "args": {"data": {"type": "scroll"}},
            },
        ]
        result = analyze_trace(events)
        assert result["source"]["has_scroll"] is True
        assert result["source"]["has_interaction"] is True

    def test_load_only_trace(self):
        events = _make_events(num_tasks=2)
        result = analyze_trace(events)
        assert result["source"]["has_scroll"] is False
        assert result["source"]["has_interaction"] is False


class TestThresholds:
    def test_has_expected_keys(self):
        assert "longest_task_ms" in THRESHOLDS
        assert "fps" in THRESHOLDS
        assert "long_tasks_count" in THRESHOLDS
        assert "scripting_ms_per_s" in THRESHOLDS

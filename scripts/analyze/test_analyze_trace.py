"""Tests for analyze_trace.py — trace parsing and metric computation."""
import pytest
from analyze_trace import (
    analyze_trace, find_main_threads, categorize, normalize_traces,
    to_json, _generate_trace_insights, _is_profiler_artifact, _fps_comparable,
)


# -- Helpers -----------------------------------------------------------------

def _thread_name_event(pid, tid, name):
    return {"ph": "M", "name": "thread_name", "pid": pid, "tid": tid,
            "args": {"name": name}}


def _duration_event(pid, tid, name, ts, dur):
    return {"ph": "X", "name": name, "pid": pid, "tid": tid,
            "ts": ts, "dur": dur}


def _make_trace(events, *, as_dict=True):
    """Build a minimal Chrome trace structure."""
    if as_dict:
        return {"traceEvents": events}
    return events


def _make_basic_trace(*, num_tasks=5, task_dur_us=100_000, include_long_task=False):
    """Build a trace with a CrRendererMain thread and some RunTask events."""
    pid, tid = 100, 1
    events = [
        _thread_name_event(pid, tid, "CrRendererMain"),
    ]
    ts = 1_000_000  # start at 1s

    for i in range(num_tasks):
        # RunTask parent
        events.append(_duration_event(pid, tid, "RunTask", ts, task_dur_us))
        # FunctionCall child (categorized as Scripting)
        events.append(_duration_event(pid, tid, "FunctionCall", ts + 1000, task_dur_us - 2000))
        ts += task_dur_us + 10_000  # gap between tasks

    if include_long_task:
        long_dur = 200_000  # 200ms — well above 50ms threshold
        events.append(_duration_event(pid, tid, "RunTask", ts, long_dur))
        events.append(_duration_event(pid, tid, "EvaluateScript", ts + 1000, long_dur - 2000))
        ts += long_dur + 10_000

    # Add some rendering
    events.append(_duration_event(pid, tid, "Layout", ts, 5_000))
    events.append(_duration_event(pid, tid, "Paint", ts + 6_000, 2_000))

    # Commit events for FPS
    for i in range(3):
        events.append(_duration_event(pid, tid, "Commit", ts + 10_000 * i, 1_000))

    return _make_trace(events)


# -- find_main_threads -------------------------------------------------------

class TestFindMainThreads:
    def test_finds_renderer_main(self):
        events = [
            _thread_name_event(100, 1, "CrRendererMain"),
            _thread_name_event(100, 2, "Compositor"),
            _thread_name_event(200, 1, "CrBrowserMain"),
        ]
        threads = find_main_threads(events)
        assert threads == {(100, 1)}

    def test_multiple_renderer_mains(self):
        events = [
            _thread_name_event(100, 1, "CrRendererMain"),
            _thread_name_event(200, 1, "CrRendererMain"),
        ]
        threads = find_main_threads(events)
        assert len(threads) == 2

    def test_empty_events(self):
        assert find_main_threads([]) == set()


# -- categorize --------------------------------------------------------------

class TestCategorize:
    @pytest.mark.parametrize("name,expected", [
        ("FunctionCall", "Scripting"),
        ("EvaluateScript", "Scripting"),
        ("Layout", "Rendering"),
        ("RecalculateStyles", "Rendering"),
        ("Paint", "Painting"),
        ("CompositeLayers", "Painting"),
        ("SomeRandomEvent", "Other"),
    ])
    def test_categories(self, name, expected):
        assert categorize(name) == expected


# -- _is_profiler_artifact ---------------------------------------------------

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

    def test_profiler_outside_parent_not_artifact(self):
        pid, tid = 100, 1
        parent = _duration_event(pid, tid, "RunTask", 1000, 60_000)
        # child starts after parent ends
        child = _duration_event(pid, tid, "CpuProfiler::StartProfiling", 100_000, 50_000)
        assert _is_profiler_artifact(parent, [parent, child]) is False


# -- analyze_trace -----------------------------------------------------------

class TestAnalyzeTrace:
    def test_basic_trace(self, tmp_path):
        import json
        trace = _make_basic_trace(num_tasks=3)
        p = tmp_path / "trace.json"
        p.write_text(json.dumps(trace))

        result = analyze_trace(str(p))
        assert result is not None
        assert result["duration_s"] > 0
        assert result["scripting_ms"] > 0
        assert result["rendering_ms"] > 0
        assert result["painting_ms"] > 0
        assert result["fps"] > 0

    def test_long_task_detection(self, tmp_path):
        import json
        trace = _make_basic_trace(include_long_task=True)
        p = tmp_path / "trace.json"
        p.write_text(json.dumps(trace))

        result = analyze_trace(str(p))
        assert result["long_tasks_count"] >= 1
        assert result["longest_task_ms"] >= 200

    def test_no_long_tasks(self, tmp_path):
        import json
        # All tasks under 50ms
        trace = _make_basic_trace(num_tasks=3, task_dur_us=30_000)
        p = tmp_path / "trace.json"
        p.write_text(json.dumps(trace))

        result = analyze_trace(str(p))
        assert result["long_tasks_count"] == 0
        assert result["longest_task_ms"] == 0

    def test_invalid_trace_returns_none(self, tmp_path):
        import json
        # A JSON file with no CrRendererMain thread
        p = tmp_path / "bad.json"
        p.write_text(json.dumps({"traceEvents": []}))

        result = analyze_trace(str(p))
        assert result is None

    def test_array_format_trace(self, tmp_path):
        """Traces can be a bare array instead of {traceEvents: [...]}."""
        import json
        pid, tid = 100, 1
        events = [
            _thread_name_event(pid, tid, "CrRendererMain"),
            _duration_event(pid, tid, "RunTask", 1_000_000, 30_000),
            _duration_event(pid, tid, "FunctionCall", 1_001_000, 28_000),
        ]
        p = tmp_path / "trace.json"
        p.write_text(json.dumps(events))

        result = analyze_trace(str(p))
        assert result is not None

    def test_profiler_artifacts_excluded_from_long_tasks(self, tmp_path):
        """RunTask events dominated by CpuProfiler::StartProfiling should not count as long tasks."""
        import json
        pid, tid = 100, 1
        events = [
            _thread_name_event(pid, tid, "CrRendererMain"),
            # A RunTask >50ms that IS a profiler artifact
            _duration_event(pid, tid, "RunTask", 1_000_000, 100_000),
            _duration_event(pid, tid, "CpuProfiler::StartProfiling", 1_001_000, 98_000),
            # A normal short task so we have duration
            _duration_event(pid, tid, "FunctionCall", 1_200_000, 10_000),
        ]
        trace = _make_trace(events)
        p = tmp_path / "trace.json"
        p.write_text(json.dumps(trace))

        result = analyze_trace(str(p))
        assert result["long_tasks_count"] == 0


# -- normalize_traces --------------------------------------------------------

class TestNormalizeTraces:
    def test_no_normalization_when_similar(self):
        data = {
            "a": {"duration_s": 5.0, "long_tasks_count": 3, "scripting_ms": 500},
            "b": {"duration_s": 5.02, "long_tasks_count": 4, "scripting_ms": 600},
        }
        result, ref = normalize_traces(data)
        assert ref is None  # within 1% tolerance
        assert result["a"]["long_tasks_count"] == 3  # unchanged

    def test_normalization_scales_counts(self):
        data = {
            "short": {"duration_s": 5.0, "long_tasks_count": 5, "scripting_ms": 500,
                       "rendering_ms": 100, "painting_ms": 50, "frames_committed": 300},
            "long": {"duration_s": 10.0, "long_tasks_count": 10, "scripting_ms": 1000,
                      "rendering_ms": 200, "painting_ms": 100, "frames_committed": 600},
        }
        result, ref = normalize_traces(data)
        assert ref == 5.0
        # "long" should be scaled down by 0.5
        assert result["long"]["long_tasks_count"] == 5
        assert result["long"]["frames_committed"] == 300
        assert result["long"]["scripting_ms"] == 500.0
        # "short" stays the same
        assert result["short"]["long_tasks_count"] == 5

    def test_single_trace_no_normalization(self):
        data = {"only": {"duration_s": 5.0, "long_tasks_count": 3}}
        result, ref = normalize_traces(data)
        assert ref is None


# -- to_json -----------------------------------------------------------------

class TestToJson:
    def test_envelope_structure(self):
        data = {"basic": {"duration_s": 5.0, "fps": 60, "scripting_ms": 200}}
        result = to_json(data)
        assert result["version"] == 1
        assert "generatedAt" in result
        assert "basic" in result["approaches"]

    def test_metrics_filter(self):
        data = {"basic": {"duration_s": 5.0, "fps": 60, "scripting_ms": 200}}
        result = to_json(data, metrics_filter=["fps"])
        assert set(result["approaches"]["basic"].keys()) == {"fps"}

    def test_normalized_duration_in_config(self):
        data = {"basic": {"duration_s": 5.0, "fps": 60}}
        result = to_json(data, normalized_duration=5.0)
        assert result["config"]["normalizedToSeconds"] == 5.0


# -- _generate_trace_insights ------------------------------------------------

class TestInteractionDetection:
    def test_scroll_trace(self, tmp_path):
        """Traces with scroll EventDispatch should set has_scroll=True."""
        import json
        pid, tid = 100, 1
        events = [
            _thread_name_event(pid, tid, "CrRendererMain"),
            _duration_event(pid, tid, "RunTask", 1_000_000, 30_000),
            _duration_event(pid, tid, "FunctionCall", 1_001_000, 28_000),
            {"ph": "X", "name": "EventDispatch", "pid": pid, "tid": tid,
             "ts": 1_050_000, "dur": 1000, "args": {"data": {"type": "scroll"}}},
        ]
        p = tmp_path / "trace.json"
        p.write_text(json.dumps({"traceEvents": events}))

        result = analyze_trace(str(p))
        assert result["has_scroll"] is True
        assert result["has_interaction"] is True

    def test_load_only_trace(self, tmp_path):
        """Traces with only lifecycle events should have has_interaction=False."""
        import json
        pid, tid = 100, 1
        events = [
            _thread_name_event(pid, tid, "CrRendererMain"),
            _duration_event(pid, tid, "RunTask", 1_000_000, 30_000),
            _duration_event(pid, tid, "FunctionCall", 1_001_000, 28_000),
            {"ph": "X", "name": "EventDispatch", "pid": pid, "tid": tid,
             "ts": 1_050_000, "dur": 1000, "args": {"data": {"type": "load"}}},
        ]
        p = tmp_path / "trace.json"
        p.write_text(json.dumps({"traceEvents": events}))

        result = analyze_trace(str(p))
        assert result["has_scroll"] is False
        assert result["has_interaction"] is False


# -- _fps_comparable ---------------------------------------------------------

class TestFpsComparable:
    def test_all_interactive(self):
        data = {
            "a": {"has_interaction": True, "raf_count": 100},
            "b": {"has_interaction": True, "raf_count": 200},
        }
        assert _fps_comparable(data, ["a", "b"]) is True

    def test_mixed_raf_no_raf_load_only(self):
        """Load-only traces where some have rAF and others don't → not comparable."""
        data = {
            "basic": {"has_interaction": False, "raf_count": 0},
            "tanstack": {"has_interaction": False, "raf_count": 264},
        }
        assert _fps_comparable(data, ["basic", "tanstack"]) is False

    def test_all_load_only_with_raf(self):
        data = {
            "primevue": {"has_interaction": False, "raf_count": 187},
            "tanstack": {"has_interaction": False, "raf_count": 264},
        }
        assert _fps_comparable(data, ["primevue", "tanstack"]) is True

    def test_mixed_interaction_types(self):
        data = {
            "scrolled": {"has_interaction": True, "raf_count": 100},
            "load_only": {"has_interaction": False, "raf_count": 0},
        }
        assert _fps_comparable(data, ["scrolled", "load_only"]) is False


# -- _generate_trace_insights ------------------------------------------------

class TestTraceInsights:
    def test_fps_comparison_when_comparable(self):
        """FPS insight generated when all traces have interaction."""
        data = {
            "smooth": {"fps": 60, "scripting_ms": 100, "rendering_ms": 50,
                       "painting_ms": 20, "longest_task_ms": 30, "frames_committed": 300,
                       "has_interaction": True, "raf_count": 300},
            "janky": {"fps": 15, "scripting_ms": 800, "rendering_ms": 200,
                      "painting_ms": 100, "longest_task_ms": 400, "frames_committed": 75,
                      "has_interaction": True, "raf_count": 75},
        }
        insights = _generate_trace_insights(data, ["smooth", "janky"])
        fps_insights = [i for i in insights if "FPS" in i and "achieves" in i]
        assert len(fps_insights) >= 1

    def test_fps_not_compared_when_incomparable(self):
        """FPS insight replaced by explanation when rAF patterns differ."""
        data = {
            "basic": {"fps": 0.8, "scripting_ms": 570, "rendering_ms": 54,
                      "painting_ms": 6, "longest_task_ms": 131, "frames_committed": 4,
                      "has_interaction": False, "raf_count": 0},
            "tanstack": {"fps": 50.7, "scripting_ms": 644, "rendering_ms": 100,
                         "painting_ms": 23, "longest_task_ms": 323, "frames_committed": 268,
                         "has_interaction": False, "raf_count": 264},
        }
        insights = _generate_trace_insights(data, ["basic", "tanstack"])
        # Should NOT generate a "tanstack achieves 50.7 fps vs basic" insight
        bad_insights = [i for i in insights if "achieves" in i]
        assert len(bad_insights) == 0
        # Should explain why FPS is not comparable
        explain = [i for i in insights if "not comparable" in i.lower()]
        assert len(explain) >= 1

    def test_scripting_dominance_insight(self):
        data = {
            "heavy": {"fps": 30, "scripting_ms": 800, "rendering_ms": 50,
                      "painting_ms": 20, "longest_task_ms": 100, "frames_committed": 150,
                      "has_interaction": False, "raf_count": 0},
        }
        insights = _generate_trace_insights(data, ["heavy"])
        script_insights = [i for i in insights if "scripting dominates" in i]
        assert len(script_insights) >= 1

    def test_severe_jank_insight(self):
        data = {
            "bad": {"fps": 20, "scripting_ms": 500, "rendering_ms": 100,
                    "painting_ms": 50, "longest_task_ms": 500, "frames_committed": 100,
                    "has_interaction": False, "raf_count": 0},
        }
        insights = _generate_trace_insights(data, ["bad"])
        jank_insights = [i for i in insights if "severe jank" in i]
        assert len(jank_insights) >= 1

    def test_per_frame_budget_only_for_meaningful_frames(self):
        """Per-frame budget insight should NOT fire for load-only traces with few frames."""
        data = {
            "basic": {"fps": 0.8, "scripting_ms": 570, "rendering_ms": 54,
                      "painting_ms": 6, "longest_task_ms": 131, "frames_committed": 4,
                      "has_interaction": False, "raf_count": 0},
        }
        insights = _generate_trace_insights(data, ["basic"])
        budget_insights = [i for i in insights if "budget" in i]
        assert len(budget_insights) == 0

    def test_per_frame_budget_fires_for_interactive(self):
        data = {
            "over_budget": {"fps": 30, "scripting_ms": 2000, "rendering_ms": 500,
                           "painting_ms": 200, "longest_task_ms": 50, "frames_committed": 50,
                           "has_interaction": True, "raf_count": 50},
        }
        insights = _generate_trace_insights(data, ["over_budget"])
        budget_insights = [i for i in insights if "budget" in i]
        assert len(budget_insights) >= 1

    def test_raf_cost_comparison(self):
        """When rAF cost differs significantly, insight should flag it."""
        data = {
            "heavy_raf": {"fps": 35, "scripting_ms": 3000, "rendering_ms": 100,
                          "painting_ms": 20, "longest_task_ms": 200, "frames_committed": 190,
                          "has_interaction": False, "raf_count": 187, "raf_total_ms": 700},
            "light_raf": {"fps": 51, "scripting_ms": 600, "rendering_ms": 100,
                          "painting_ms": 20, "longest_task_ms": 100, "frames_committed": 268,
                          "has_interaction": False, "raf_count": 264, "raf_total_ms": 60},
        }
        insights = _generate_trace_insights(data, ["heavy_raf", "light_raf"])
        raf_insights = [i for i in insights if "rAF cost" in i]
        assert len(raf_insights) >= 1


# -- Integration: real trace file --------------------------------------------

class TestRealTrace:
    """Run against actual trace files to catch format drift."""

    def test_analyze_real_trace(self):
        from pathlib import Path
        p = Path(__file__).parent / "traces" / "Trace-20260315T111552-basic.json"
        if not p.exists():
            pytest.skip("basic trace not present")

        result = analyze_trace(str(p))
        assert result is not None
        assert result["duration_s"] > 0
        assert result["scripting_ms"] >= 0
        assert result["frames_committed"] >= 0
        assert isinstance(result["long_tasks_count"], int)
        # New fields
        assert isinstance(result["has_interaction"], bool)
        assert isinstance(result["has_scroll"], bool)
        # This trace is load-only (no scrolling was recorded)
        assert result["has_scroll"] is False

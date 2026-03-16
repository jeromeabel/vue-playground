"""Tests for bench.compare — comparison logic, normalization, insights."""
import pytest
from bench.compare import (
    normalize_traces, compare, _fps_comparable,
    _generate_lighthouse_insights, _generate_trace_insights,
)


class TestNormalizeTraces:
    def test_no_normalization_when_similar(self):
        data = {
            "a": {"duration_s": 5.0, "long_tasks_count": 3, "scripting_ms": 500},
            "b": {"duration_s": 5.02, "long_tasks_count": 4, "scripting_ms": 600},
        }
        result, ref = normalize_traces(data)
        assert ref is None
        assert result["a"]["long_tasks_count"] == 3

    def test_normalization_scales_counts(self):
        data = {
            "short": {"duration_s": 5.0, "long_tasks_count": 5, "scripting_ms": 500,
                       "rendering_ms": 100, "painting_ms": 50, "frames_committed": 300},
            "long": {"duration_s": 10.0, "long_tasks_count": 10, "scripting_ms": 1000,
                      "rendering_ms": 200, "painting_ms": 100, "frames_committed": 600},
        }
        result, ref = normalize_traces(data)
        assert ref == 5.0
        assert result["long"]["long_tasks_count"] == 5
        assert result["long"]["frames_committed"] == 300
        assert result["long"]["scripting_ms"] == 500.0
        assert result["short"]["long_tasks_count"] == 5

    def test_single_trace_no_normalization(self):
        data = {"only": {"duration_s": 5.0, "long_tasks_count": 3}}
        result, ref = normalize_traces(data)
        assert ref is None

    def test_preserves_rate_metrics(self):
        data = {
            "a": {"duration_s": 5.0, "fps": 40.0, "long_tasks_count": 4,
                   "scripting_ms": 500, "rendering_ms": 100, "painting_ms": 50},
            "b": {"duration_s": 10.0, "fps": 40.0, "long_tasks_count": 8,
                   "scripting_ms": 1000, "rendering_ms": 200, "painting_ms": 100},
        }
        result, _ = normalize_traces(data)
        assert result["b"]["fps"] == 40.0

    def test_preserves_null_optional_totals(self):
        data = {
            "a": {"duration_s": 5.0, "scripting_ms": 500, "rendering_ms": 100, "painting_ms": 50, "raf_total_ms": None},
            "b": {"duration_s": 10.0, "scripting_ms": 1000, "rendering_ms": 200, "painting_ms": 100, "raf_total_ms": None},
        }
        result, ref = normalize_traces(data)
        assert ref == 5.0
        assert result["a"]["raf_total_ms"] is None
        assert result["b"]["raf_total_ms"] is None


class TestFpsComparable:
    def test_all_interactive(self):
        data = {
            "a": {"has_interaction": True, "raf_count": 100},
            "b": {"has_interaction": True, "raf_count": 200},
        }
        assert _fps_comparable(data, ["a", "b"]) is True

    def test_mixed_raf_no_raf_load_only(self):
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


class TestLighthouseInsights:
    def test_ratio_insight(self):
        data = {
            "fast": {"TBT": 100, "LCP": 500, "DOM Size": 300, "Score": 99},
            "slow": {"TBT": 500, "LCP": 500, "DOM Size": 300, "Score": 50},
        }
        insights = _generate_lighthouse_insights(data, ["fast", "slow"])
        tbt = [i for i in insights if "Total Blocking Time" in i]
        assert len(tbt) >= 1

    def test_unmeasured_lcp(self):
        data = {
            "ok": {"TBT": 0, "LCP": 2000, "DOM Size": 300, "Score": 100},
            "broken": {"TBT": 0, "LCP": None, "DOM Size": 80000, "Score": None},
        }
        insights = _generate_lighthouse_insights(data, ["ok", "broken"])
        lcp = [i for i in insights if "NO_LCP" in i]
        assert len(lcp) >= 1


class TestTraceInsights:
    def test_fps_when_comparable(self):
        data = {
            "smooth": {"fps": 60, "scripting_ms": 100, "rendering_ms": 50,
                       "painting_ms": 20, "longest_task_ms": 30, "frames_committed": 300,
                       "has_interaction": True, "raf_count": 300},
            "janky": {"fps": 15, "scripting_ms": 800, "rendering_ms": 200,
                      "painting_ms": 100, "longest_task_ms": 400, "frames_committed": 75,
                      "has_interaction": True, "raf_count": 75},
        }
        insights = _generate_trace_insights(data, ["smooth", "janky"])
        fps = [i for i in insights if "FPS" in i and "achieves" in i]
        assert len(fps) >= 1

    def test_fps_not_compared_when_incomparable(self):
        data = {
            "basic": {"fps": 0.8, "scripting_ms": 570, "rendering_ms": 54,
                      "painting_ms": 6, "longest_task_ms": 131, "frames_committed": 4,
                      "has_interaction": False, "raf_count": 0},
            "tanstack": {"fps": 50.7, "scripting_ms": 644, "rendering_ms": 100,
                         "painting_ms": 23, "longest_task_ms": 323, "frames_committed": 268,
                         "has_interaction": False, "raf_count": 264},
        }
        insights = _generate_trace_insights(data, ["basic", "tanstack"])
        bad = [i for i in insights if "achieves" in i]
        assert len(bad) == 0
        explain = [i for i in insights if "not comparable" in i.lower()]
        assert len(explain) >= 1

    def test_severe_jank(self):
        data = {
            "bad": {"fps": 20, "scripting_ms": 500, "rendering_ms": 100,
                    "painting_ms": 50, "longest_task_ms": 500, "frames_committed": 100,
                    "has_interaction": False, "raf_count": 0},
        }
        insights = _generate_trace_insights(data, ["bad"])
        jank = [i for i in insights if "severe jank" in i]
        assert len(jank) >= 1


class TestCompare:
    """Tests for the main compare() orchestration function."""

    def _make_analysis(self, name, metrics, *, analysis_type="lighthouse"):
        return {
            "version": 1,
            "type": analysis_type,
            "generatedAt": "2026-01-01T00:00:00Z",
            "source": {"filename": f"{name}.json"},
            "metrics": metrics,
            "thresholds": {},
        }

    def test_returns_comparison_result(self):
        analyses = {
            "basic": self._make_analysis("basic", {"Score": 100, "TBT": 0, "LCP": 500}),
            "primevue": self._make_analysis("primevue", {"Score": 99, "TBT": 73, "LCP": 630}),
        }
        display = {"primary": ["Score", "TBT"], "secondary": ["LCP"], "hidden": []}
        result = compare(analyses, display=display)
        assert hasattr(result, "approaches")
        assert hasattr(result, "insights")
        assert hasattr(result, "metric_keys")

    def test_filters_to_primary_and_secondary(self):
        analyses = {
            "a": self._make_analysis("a", {"Score": 100, "TBT": 0, "CLS": 0.01}),
        }
        display = {"primary": ["Score"], "secondary": ["TBT"], "hidden": ["CLS"]}
        result = compare(analyses, display=display)
        # CLS should be excluded
        assert "CLS" not in result.approaches["a"]
        # Score and TBT should be included
        assert "Score" in result.approaches["a"]
        assert "TBT" in result.approaches["a"]
        assert set(result.metric_keys) == {"Score", "TBT"}

    def test_hidden_metrics_excluded(self):
        analyses = {
            "a": self._make_analysis("a", {"Score": 100, "Max FID": 16}),
        }
        display = {"primary": ["Score"], "secondary": [], "hidden": ["Max FID"]}
        result = compare(analyses, display=display)
        assert "Max FID" not in result.approaches["a"]

    def test_insights_generated(self):
        analyses = {
            "fast": self._make_analysis("fast", {"TBT": 100, "LCP": 500, "DOM Size": 300, "Score": 99}),
            "slow": self._make_analysis("slow", {"TBT": 500, "LCP": 500, "DOM Size": 300, "Score": 50}),
        }
        display = {"primary": ["TBT", "LCP", "DOM Size", "Score"], "secondary": [], "hidden": []}
        result = compare(analyses, display=display)
        assert len(result.insights) > 0

    def test_trace_compare_normalizes_and_excludes_source_keys(self):
        """Trace comparison merges source for normalization but keeps approaches clean."""
        trace_metrics = {
            "scripting_ms": 500, "rendering_ms": 100, "painting_ms": 50,
            "longest_task_ms": 200, "long_tasks_count": 3, "fps": 30,
            "frames_committed": 150, "raf_count": 100, "raf_total_ms": 50,
        }
        # Source uses camelCase (matching extract_source() envelope output)
        trace_source = {
            "filename": "basic.json", "durationS": 5.0,
            "hasInteraction": False, "hasScroll": False,
        }
        analyses = {
            "basic": {
                "version": 1, "type": "trace",
                "generatedAt": "2026-01-01T00:00:00Z",
                "source": trace_source, "metrics": trace_metrics, "thresholds": {},
            },
        }
        result = compare(analyses)
        # Source metadata must not leak into approaches (neither camelCase nor snake_case)
        assert "durationS" not in result.approaches["basic"]
        assert "duration_s" not in result.approaches["basic"]
        assert "hasInteraction" not in result.approaches["basic"]
        assert "has_interaction" not in result.approaches["basic"]
        assert "filename" not in result.approaches["basic"]
        # Actual metrics must be present
        assert "scripting_ms" in result.approaches["basic"]
        assert "fps" in result.approaches["basic"]

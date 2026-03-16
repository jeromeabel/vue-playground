"""Compare multiple analysis results — filtering, normalization, insights."""
from __future__ import annotations
import sys
from dataclasses import dataclass, field

from bench.lighthouse.extract import THRESHOLDS as _LH_THRESHOLDS, status_for as _lh_status_for


@dataclass
class ComparisonResult:
    """Result of comparing N analyses."""

    approaches: dict[str, dict]     # name → filtered metrics
    metric_keys: list[str]          # ordered list of included metric keys
    insights: list[str]             # generated insight strings
    sources: dict[str, dict] = field(default_factory=dict)  # name → source metadata


def compare(
    analyses: dict[str, dict],
    *,
    display: dict | None = None,
) -> ComparisonResult:
    """Compare N analysis envelopes.

    Args:
        analyses: name → analysis envelope (with metrics, source, type)
        display: {"primary": [...], "secondary": [...], "hidden": [...]}
                 If None, all metrics are included.

    Returns:
        ComparisonResult with filtered approaches, metric keys, and insights.
    """
    first = next(iter(analyses.values()))
    analysis_type = first.get("type", "lighthouse")

    raw_metrics = {name: dict(a["metrics"]) for name, a in analyses.items()}
    sources = {name: a.get("source", {}) for name, a in analyses.items()}

    _CAMEL_TO_SNAKE = {
        "durationS": "duration_s",
        "hasInteraction": "has_interaction",
        "hasScroll": "has_scroll",
    }
    _SOURCE_KEYS = {
        "filename", "duration_s", "durationS", "has_interaction",
        "hasInteraction", "has_scroll", "hasScroll", "original_duration_s",
    }

    if analysis_type == "trace":
        for name in raw_metrics:
            src = {_CAMEL_TO_SNAKE.get(k, k): v for k, v in sources[name].items()}
            raw_metrics[name] = {**raw_metrics[name], **src}
        raw_metrics, _ = normalize_traces(raw_metrics)

    if display:
        included = display.get("primary", []) + display.get("secondary", [])
    else:
        included = [
            k for k in next(iter(raw_metrics.values())).keys()
            if k not in _SOURCE_KEYS
        ]

    filtered = {}
    for name, metrics in raw_metrics.items():
        filtered[name] = {k: v for k, v in metrics.items() if k in included}

    names = list(raw_metrics.keys())
    if analysis_type == "trace":
        insights = _generate_trace_insights(raw_metrics, names)
    else:
        insights = _generate_lighthouse_insights(raw_metrics, names)

    return ComparisonResult(
        approaches=filtered,
        metric_keys=included,
        insights=insights,
        sources=sources,
    )


def normalize_traces(
    data: dict[str, dict],
    tolerance_pct: float = 1.0,
) -> tuple[dict[str, dict], float | None]:
    """Normalize count/total metrics when trace durations differ.

    Scales duration-dependent metrics to the shortest trace so that raw counts
    (long_tasks_count, frames_committed) are comparable.  Rate metrics
    (scripting_ms_per_s, fps, …) are mathematically unchanged by the scaling,
    so they are left as-is.

    Returns (normalised_data, reference_duration) — reference_duration is None
    when all traces are within *tolerance_pct* of each other.
    """
    if len(data) < 2:
        return data, None

    durations = [d["duration_s"] for d in data.values()]
    ref = min(durations)

    if ref <= 0:
        return data, None

    max_diff = (max(durations) - ref) / ref * 100
    if max_diff <= tolerance_pct:
        return data, None

    print(
        f"Warning: trace durations differ by {max_diff:.1f}% "
        f"(range: {min(durations):.2f}s – {max(durations):.2f}s). "
        f"Normalizing counts and totals to {ref:.2f}s.",
        file=sys.stderr,
    )

    SCALE_COUNTS = {"long_tasks_count", "frames_committed", "raf_count", "af_count"}
    SCALE_TOTALS = {"scripting_ms", "rendering_ms", "painting_ms", "raf_total_ms"}

    normalized = {}
    for name, d in data.items():
        nd = dict(d)
        scale = ref / d["duration_s"]

        nd["original_duration_s"] = d["duration_s"]
        nd["duration_s"] = round(ref, 2)

        for m in SCALE_COUNTS:
            if m in nd:
                nd[m] = round(nd[m] * scale)

        for m in SCALE_TOTALS:
            if m in nd:
                nd[m] = round(nd[m] * scale, 1)

        normalized[name] = nd

    return normalized, ref


def _fps_comparable(data: dict[str, dict], names: list[str]) -> bool:
    """Check if FPS is comparable across traces.

    FPS is only comparable when all traces have the same interaction pattern:
    either all have user interaction, or all are load-only with similar rAF usage.
    """
    has_raf = [data[n].get("raf_count", 0) > 0 for n in names]
    has_interaction = [data[n].get("has_interaction", False) for n in names]

    if all(has_interaction) or not any(has_interaction):
        # Within load-only, rAF vs no-rAF is also not comparable
        if not any(has_interaction) and any(has_raf) and not all(has_raf):
            return False
        return True
    return False


def _generate_lighthouse_insights(data: dict[str, dict], names: list[str]) -> list[str]:
    """Auto-generate actionable insights from lighthouse data."""
    insights = []

    for metric, label in [
        ("TBT", "Total Blocking Time"),
        ("LCP", "Largest Contentful Paint"),
        ("DOM Size", "DOM Size"),
    ]:
        values = {n: data[n][metric] for n in names if data[n].get(metric) is not None}
        if len(values) < 2:
            unmeasured = [n for n in names if data[n].get(metric) is None]
            if unmeasured:
                insights.append(
                    f"**{label}**: {', '.join(unmeasured)} could not be measured (NO_LCP)"
                )
            continue
        best = min(values, key=values.get)
        worst = max(values, key=values.get)
        if values[worst] > 0 and values[best] > 0:
            ratio = values[worst] / values[best]
            if ratio > 2:
                insights.append(
                    f"**{label}**: {worst} is {ratio:.0f}x worse than {best} "
                    f"({values[worst]:,.0f} vs {values[best]:,.0f})"
                )

    for name in names:
        fails = [
            m for m in _LH_THRESHOLDS
            if _lh_status_for(m, data[name].get(m)) in ("fail", "error")
        ]
        if fails:
            insights.append(f"**{name}** fails on: {', '.join(fails)}")

    scores = {n: data[n]["Score"] for n in names if data[n].get("Score") is not None}
    if scores:
        best = max(scores, key=scores.get)
        worst = min(scores, key=scores.get)
        if scores[best] != scores[worst]:
            insights.append(
                f"**Performance score range**: {scores[worst]} ({worst}) to {scores[best]} ({best})"
            )

    return insights


def _generate_trace_insights(data: dict[str, dict], names: list[str]) -> list[str]:
    """Auto-generate insights from trace comparison."""
    insights = []

    fps_comparable = _fps_comparable(data, names)

    if fps_comparable:
        fps_vals = {n: data[n]["fps"] for n in names}
        best_fps = max(fps_vals, key=fps_vals.get)
        worst_fps = min(fps_vals, key=fps_vals.get)
        if fps_vals[best_fps] > fps_vals[worst_fps] * 1.1:
            insights.append(
                f"**FPS**: {best_fps} achieves {fps_vals[best_fps]} fps vs "
                f"{worst_fps} at {fps_vals[worst_fps]} fps"
            )
    else:
        raf_names = [n for n in names if data[n].get("raf_count", 0) > 0]
        no_raf_names = [n for n in names if data[n].get("raf_count", 0) == 0]
        if raf_names and no_raf_names:
            insights.append(
                f"**FPS not comparable**: {', '.join(raf_names)} use rAF "
                f"({', '.join(str(data[n]['frames_committed']) + ' frames' for n in raf_names)}) "
                f"while {', '.join(no_raf_names)} rendered only initial frames "
                f"({', '.join(str(data[n]['frames_committed']) + ' frames' for n in no_raf_names)}). "
                f"rAF-driven components commit frames during initialization even without user scrolling"
            )

    raf_names = [n for n in names if data[n].get("raf_count", 0) > 0]
    if len(raf_names) >= 2:
        raf_totals = {n: data[n].get("raf_total_ms", 0) for n in raf_names}
        heaviest = max(raf_totals, key=raf_totals.get)
        lightest = min(raf_totals, key=raf_totals.get)
        if raf_totals[lightest] > 0:
            ratio = raf_totals[heaviest] / raf_totals[lightest]
            if ratio > 2:
                insights.append(
                    f"**rAF cost**: {heaviest} spends {raf_totals[heaviest]:.0f}ms in rAF callbacks "
                    f"vs {lightest} at {raf_totals[lightest]:.0f}ms "
                    f"({ratio:.0f}x more) — reflects virtual scroll initialization overhead"
                )

    for name in names:
        d = data[name]
        total = d["scripting_ms"] + d["rendering_ms"] + d["painting_ms"]
        if total > 0:
            script_pct = d["scripting_ms"] / total * 100
            if script_pct > 70:
                insights.append(
                    f"**{name}**: scripting dominates at {script_pct:.0f}% of main-thread time"
                )

    for name in names:
        d = data[name]
        if d["longest_task_ms"] > 200:
            insights.append(
                f"**{name}**: longest task ({d['longest_task_ms']}ms) is "
                f"{d['longest_task_ms'] / 50:.0f}x the long-task threshold — severe jank"
            )

    for name in names:
        d = data[name]
        if d["frames_committed"] > 10 and (d.get("has_interaction") or d.get("raf_count", 0) > 0):
            total_ms = d["scripting_ms"] + d["rendering_ms"] + d["painting_ms"]
            per_frame = total_ms / d["frames_committed"]
            budget = 16.67
            if per_frame > budget:
                insights.append(
                    f"**{name}**: per-frame cost {per_frame:.1f}ms exceeds "
                    f"16.67ms budget (60fps) by {per_frame - budget:.1f}ms"
                )

    return insights

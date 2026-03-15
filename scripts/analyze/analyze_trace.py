#!/usr/bin/env python3
"""
Analyze Chrome Performance trace JSON files.

Outputs:
  1. Markdown report to stdout (per-trace breakdown + comparison table)
  2. PNG comparison chart (visual storytelling)

Usage:
    python analyze_trace.py trace-basic.json trace-tanstack.json -o trace-comparison.png

Export traces from Chrome DevTools: Performance tab > Save Profile.
"""
import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns


# -- Thresholds for key trace metrics ----------------------------------------
# Higher is better for fps; lower is better for everything else.
TRACE_THRESHOLDS = {
    "longest_task_ms":    (50,  200, "ms"),
    "fps":                (55,  30,  "fps"),
    "long_tasks_count":   (3,   10,  "count"),
    "scripting_ms_per_s": (200, 500, "ms/s"),
}


# -- Category mapping (matches Chrome DevTools Summary panel) ----------------

CATEGORY_MAP = {
    "Scripting": {
        "FunctionCall", "v8.callFunction", "EvaluateScript", "v8.compile",
        "FireAnimationFrame", "EventDispatch", "RunMicrotasks", "TimerFire",
    },
    "Rendering": {
        "UpdateLayoutTree", "Layout", "RecalculateStyles", "PrePaint",
        "Layerize", "Commit", "HitTest",
        "IntersectionObserverController::computeIntersections",
    },
    "Painting": {
        "Paint", "CompositeLayers", "RasterTask", "Decode Image",
    },
}

_NAME_TO_CATEGORY = {}
for _cat, _names in CATEGORY_MAP.items():
    for _name in _names:
        _NAME_TO_CATEGORY[_name] = _cat


def categorize(name: str) -> str:
    return _NAME_TO_CATEGORY.get(name, "Other")


# -- Trace analysis ----------------------------------------------------------

def find_main_threads(events: list) -> set:
    """Find (pid, tid) pairs for CrRendererMain threads."""
    threads = set()
    for e in events:
        if e.get("ph") == "M" and e.get("name") == "thread_name":
            if e.get("args", {}).get("name") == "CrRendererMain":
                threads.add((e["pid"], e["tid"]))
    return threads


def _is_profiler_artifact(parent: dict, events: list) -> bool:
    """Check if a RunTask is dominated by CpuProfiler::StartProfiling (DevTools overhead)."""
    p_start = parent["ts"]
    p_end = parent["ts"] + parent.get("dur", 0)
    p_pid = parent["pid"]
    p_tid = parent["tid"]
    for e in events:
        if (
            e.get("pid") == p_pid
            and e.get("tid") == p_tid
            and e.get("ph") == "X"
            and e.get("name") == "CpuProfiler::StartProfiling"
            and e.get("ts", 0) >= p_start
            and e.get("ts", 0) + e.get("dur", 0) <= p_end
        ):
            return True
    return False


def analyze_trace(trace_path: str) -> dict | None:
    """Analyze a single Chrome trace file. Returns None if not a valid trace."""
    with open(trace_path) as f:
        data = json.load(f)

    events = data if isinstance(data, list) else data.get("traceEvents", [])

    # Validate: a real trace has metadata events with thread names
    main_threads = find_main_threads(events)
    if not main_threads:
        return None

    # Time range (main thread only, duration events)
    timestamps = []
    max_end = 0
    for e in events:
        if (e.get("pid"), e.get("tid")) not in main_threads:
            continue
        if e.get("ph") != "X":
            continue
        ts = e.get("ts", 0)
        dur = e.get("dur", 0)
        timestamps.append(ts)
        end = ts + dur
        if end > max_end:
            max_end = end

    if not timestamps:
        return None

    trace_start = min(timestamps)
    trace_end = max(max_end, max(timestamps))
    duration_us = trace_end - trace_start
    duration_s = duration_us / 1_000_000

    # Category breakdown (main thread only)
    totals = defaultdict(float)
    for e in events:
        if (e.get("pid"), e.get("tid")) not in main_threads:
            continue
        if e.get("ph") != "X":
            continue
        name = e.get("name", "")
        cat = categorize(name)
        if cat != "Other":
            totals[cat] += e.get("dur", 0) / 1000  # us -> ms

    # Long tasks (RunTask > 50ms, excluding profiler artifacts)
    long_tasks = []
    for e in events:
        if (e.get("pid"), e.get("tid")) not in main_threads:
            continue
        if e.get("ph") != "X" or e.get("name") != "RunTask":
            continue
        dur_ms = e.get("dur", 0) / 1000
        if dur_ms > 50 and not _is_profiler_artifact(e, events):
            long_tasks.append(dur_ms)
    long_tasks.sort(reverse=True)

    # Frame counting
    frame_events = Counter()
    for e in events:
        if (e.get("pid"), e.get("tid")) not in main_threads:
            continue
        name = e.get("name", "")
        if name in ("BeginMainThreadFrame", "Commit", "Paint"):
            frame_events[name] += 1

    commits = frame_events.get("Commit", frame_events.get("BeginMainThreadFrame", 0))
    fps = commits / duration_s if duration_s > 0 else 0

    # AnimationFrame stats
    af_durs = []
    for e in events:
        if (e.get("pid"), e.get("tid")) not in main_threads:
            continue
        if e.get("ph") == "X" and e.get("name") == "AnimationFrame":
            af_durs.append(e.get("dur", 0) / 1000)
    af_durs.sort()

    # FireAnimationFrame (rAF callback) stats
    raf_durs = []
    for e in events:
        if (e.get("pid"), e.get("tid")) not in main_threads:
            continue
        if e.get("ph") == "X" and e.get("name") == "FireAnimationFrame":
            raf_durs.append(e.get("dur", 0) / 1000)

    safe_dur = max(duration_s, 0.01)

    result = {
        "duration_s": round(duration_s, 2),
        "scripting_ms": round(totals.get("Scripting", 0), 1),
        "rendering_ms": round(totals.get("Rendering", 0), 1),
        "painting_ms": round(totals.get("Painting", 0), 1),
        "scripting_ms_per_s": round(totals.get("Scripting", 0) / safe_dur, 1),
        "rendering_ms_per_s": round(totals.get("Rendering", 0) / safe_dur, 1),
        "painting_ms_per_s": round(totals.get("Painting", 0) / safe_dur, 1),
        "long_tasks_count": len(long_tasks),
        "long_tasks_per_s": round(len(long_tasks) / safe_dur, 2),
        "longest_task_ms": round(long_tasks[0], 1) if long_tasks else 0,
        "top_long_tasks_ms": [round(t, 1) for t in long_tasks[:5]],
        "frames_committed": commits,
        "fps": round(fps, 1),
    }

    if af_durs:
        result["af_count"] = len(af_durs)
        result["af_mean_ms"] = round(sum(af_durs) / len(af_durs), 2)
        result["af_p95_ms"] = round(af_durs[int(len(af_durs) * 0.95)], 2)
        result["af_max_ms"] = round(af_durs[-1], 2)

    if raf_durs:
        result["raf_count"] = len(raf_durs)
        result["raf_total_ms"] = round(sum(raf_durs), 1)
        result["raf_mean_ms"] = round(sum(raf_durs) / len(raf_durs), 2)

    return result


# -- Markdown output ----------------------------------------------------------

def print_markdown(data: dict[str, dict]) -> None:
    """Print markdown comparison report to stdout."""
    names = list(data.keys())

    print("# Chrome Trace Comparison\n")

    # Per-trace summary
    for name in names:
        d = data[name]
        print(f"## {name}\n")
        print(f"- **Duration**: {d['duration_s']}s")
        print(f"- **Frames committed**: {d['frames_committed']} ({d['fps']} fps)")
        print(f"- **Scripting**: {d['scripting_ms']} ms ({d['scripting_ms_per_s']} ms/s)")
        print(f"- **Rendering**: {d['rendering_ms']} ms ({d['rendering_ms_per_s']} ms/s)")
        print(f"- **Painting**: {d['painting_ms']} ms ({d['painting_ms_per_s']} ms/s)")
        print(f"- **Long tasks (>50ms)**: {d['long_tasks_count']} ({d['long_tasks_per_s']}/s)")
        if d["longest_task_ms"] > 0:
            print(f"- **Longest task**: {d['longest_task_ms']} ms")
            if d["top_long_tasks_ms"]:
                top = ", ".join(f"{t}ms" for t in d["top_long_tasks_ms"])
                print(f"- **Top 5 long tasks**: {top}")
        if "af_count" in d:
            print(f"- **AnimationFrame**: {d['af_count']} (mean {d['af_mean_ms']}ms, p95 {d['af_p95_ms']}ms, max {d['af_max_ms']}ms)")
        if "raf_count" in d:
            print(f"- **rAF callbacks**: {d['raf_count']} (total {d['raf_total_ms']}ms, mean {d['raf_mean_ms']}ms)")
        print()

    # Comparison table
    if len(names) > 1:
        print("## Comparison Table\n")
        header = "| Metric | " + " | ".join(names) + " |"
        sep = "|--------|" + "|".join(["--------"] * len(names)) + "|"
        print(header)
        print(sep)

        rows = [
            ("Duration (s)",       "duration_s"),
            ("FPS",                "fps"),
            ("Scripting (ms/s)",   "scripting_ms_per_s"),
            ("Rendering (ms/s)",   "rendering_ms_per_s"),
            ("Painting (ms/s)",    "painting_ms_per_s"),
            ("Long tasks",         "long_tasks_count"),
            ("Longest task (ms)",  "longest_task_ms"),
        ]
        for label, key in rows:
            cells = [f"{data[n].get(key, 'N/A')}" for n in names]
            print(f"| {label} | " + " | ".join(cells) + " |")

        print()

        # Insights
        print("## Key Insights\n")
        insights = _generate_trace_insights(data, names)
        for insight in insights:
            print(f"- {insight}")

    print("\n---")


def _generate_trace_insights(data: dict[str, dict], names: list[str]) -> list[str]:
    """Auto-generate insights from trace comparison."""
    insights = []

    # FPS comparison
    fps_vals = {n: data[n]["fps"] for n in names}
    best_fps = max(fps_vals, key=fps_vals.get)
    worst_fps = min(fps_vals, key=fps_vals.get)
    if fps_vals[best_fps] > fps_vals[worst_fps] * 1.1:
        insights.append(
            f"**FPS**: {best_fps} achieves {fps_vals[best_fps]} fps vs "
            f"{worst_fps} at {fps_vals[worst_fps]} fps"
        )

    # Scripting dominance
    for name in names:
        d = data[name]
        total = d["scripting_ms"] + d["rendering_ms"] + d["painting_ms"]
        if total > 0:
            script_pct = d["scripting_ms"] / total * 100
            if script_pct > 70:
                insights.append(
                    f"**{name}**: scripting dominates at {script_pct:.0f}% of main-thread time"
                )

    # Long task severity
    for name in names:
        d = data[name]
        if d["longest_task_ms"] > 200:
            insights.append(
                f"**{name}**: longest task ({d['longest_task_ms']}ms) is "
                f"{d['longest_task_ms'] / 50:.0f}x the long-task threshold — severe jank"
            )

    # Per-frame render cost
    for name in names:
        d = data[name]
        if d["frames_committed"] > 0:
            total_ms = d["scripting_ms"] + d["rendering_ms"] + d["painting_ms"]
            per_frame = total_ms / d["frames_committed"]
            budget = 16.67
            if per_frame > budget:
                insights.append(
                    f"**{name}**: per-frame cost {per_frame:.1f}ms exceeds "
                    f"16.67ms budget (60fps) by {per_frame - budget:.1f}ms"
                )

    return insights


# -- JSON output -------------------------------------------------------------

def to_json(
    data: dict[str, dict],
    config: dict | None = None,
    metrics_filter: list[str] | None = None,
) -> dict:
    """Return a structured JSON envelope for the trace benchmark data."""
    if config is None:
        config = {"iterations": 1, "aggregation": "single", "preset": "desktop"}

    thresholds = {
        metric: {"good": good, "poor": poor, "unit": unit}
        for metric, (good, poor, unit) in TRACE_THRESHOLDS.items()
    }

    approaches = {}
    for name, metrics in data.items():
        if metrics_filter is not None:
            approaches[name] = {k: v for k, v in metrics.items() if k in metrics_filter}
        else:
            approaches[name] = dict(metrics)

    metric_keys = list(next(iter(approaches.values())).keys()) if approaches else []

    return {
        "version": 1,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "config": config,
        "thresholds": thresholds,
        "approaches": approaches,
        "metrics": metric_keys,
    }


# -- Chart output -------------------------------------------------------------

def save_chart(data: dict[str, dict], output_path: str) -> None:
    """Generate a comparison bar chart PNG."""
    metrics = [
        ("scripting_ms_per_s", "Scripting (ms/s)"),
        ("rendering_ms_per_s", "Rendering (ms/s)"),
        ("painting_ms_per_s",  "Painting (ms/s)"),
        ("long_tasks_count",   "Long Tasks (>50ms)"),
        ("longest_task_ms",    "Longest Task (ms)"),
        ("fps",                "FPS"),
    ]

    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    flat_axes = axes.flatten()
    names = list(data.keys())
    colors = sns.color_palette("muted", len(names))

    for i, (key, label) in enumerate(metrics):
        ax = flat_axes[i]
        values = [data[n].get(key, 0) for n in names]
        ax.bar(names, values, color=colors)
        ax.set_title(label, fontsize=11, fontweight="bold")
        ax.tick_params(axis="x", rotation=15)
        for j, v in enumerate(values):
            ax.text(j, v, f"{v:,.1f}", ha="center", va="bottom", fontsize=9)

        # Add 50ms threshold line for longest task
        if key == "longest_task_ms" and max(values) > 0:
            ax.axhline(y=50, color="#4caf50", linestyle="--", alpha=0.5, linewidth=1)

    plt.suptitle(
        "Chrome Trace Comparison",
        fontsize=14, fontweight="bold",
    )
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")


# -- Main --------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Analyze Chrome traces — outputs markdown report + PNG chart"
    )
    parser.add_argument("traces", nargs="+", help="Chrome trace JSON files")
    parser.add_argument("-o", "--output", default="trace-comparison.png",
                        help="Output PNG path (default: trace-comparison.png)")
    parser.add_argument("--no-chart", action="store_true",
                        help="Skip chart generation, only print markdown")
    parser.add_argument("--json", action="store_true",
                        help="Output JSON to stdout (replaces markdown)")
    parser.add_argument("--json-out", metavar="PATH",
                        help="Write JSON output to file")
    parser.add_argument("--metrics", metavar="M1,M2,...",
                        help="Filter which metrics to include (comma-separated)")
    parser.add_argument("--names", metavar="N1,N2,...",
                        help="Custom labels for approaches (comma-separated, must match number of traces)")
    args = parser.parse_args()

    # Parse optional filters
    metrics_filter = [m.strip() for m in args.metrics.split(",")] if args.metrics else None
    custom_names = [n.strip() for n in args.names.split(",")] if args.names else None

    if custom_names is not None and len(custom_names) != len(args.traces):
        print(
            f"Error: --names has {len(custom_names)} value(s) but {len(args.traces)} trace(s) were provided",
            file=sys.stderr,
        )
        sys.exit(1)

    data = {}
    skipped = []
    for i, path_str in enumerate(args.traces):
        path = Path(path_str)
        if not path.exists():
            print(f"Error: {path_str} not found", file=sys.stderr)
            sys.exit(1)
        name = custom_names[i] if custom_names is not None else path.stem
        result = analyze_trace(path_str)
        if result is None:
            skipped.append(path_str)
        else:
            data[name] = result

    if skipped:
        for s in skipped:
            print(f"Warning: {s} is not a Chrome trace (no CrRendererMain thread found), skipping", file=sys.stderr)

    if not data:
        print("Error: no valid Chrome traces found. Are these Lighthouse reports instead?", file=sys.stderr)
        print("  Use analyze_lighthouse.py for Lighthouse JSON files.", file=sys.stderr)
        sys.exit(1)

    # JSON mode
    if args.json or args.json_out:
        result = to_json(data, metrics_filter=metrics_filter)
        if args.json:
            print(json.dumps(result, indent=2))
        if args.json_out:
            with open(args.json_out, "w") as f:
                json.dump(result, f, indent=2)
            print(f"JSON saved to {args.json_out}", file=sys.stderr)
        return

    # Markdown to stdout
    print_markdown(data)

    # Chart to file
    if not args.no_chart:
        save_chart(data, args.output)
        print(f"\nChart saved to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()

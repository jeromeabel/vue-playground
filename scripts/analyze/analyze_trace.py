#!/usr/bin/env python3
"""
Analyze Chrome Performance trace JSON files.

Usage:
    python analyze_trace.py trace-basic.json trace-tanstack.json -o trace-comparison.png

Export traces from Chrome DevTools: Performance tab > Save Profile.
"""
import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns


CATEGORY_MAP = {
    "Scripting": [
        "EvaluateScript",
        "v8.compile",
        "FunctionCall",
        "EventDispatch",
        "TimerFire",
        "FireAnimationFrame",
    ],
    "Rendering": [
        "UpdateLayoutTree",
        "Layout",
        "RecalculateStyles",
        "HitTest",
    ],
    "Painting": [
        "Paint",
        "CompositeLayers",
        "RasterTask",
        "Decode Image",
    ],
}


def categorize(name: str) -> str:
    for cat, names in CATEGORY_MAP.items():
        if name in names:
            return cat
    return "Other"


def analyze_trace(trace_path: str) -> dict:
    with open(trace_path) as f:
        data = json.load(f)

    events = data if isinstance(data, list) else data.get("traceEvents", [])

    totals: dict[str, float] = {
        "Scripting": 0,
        "Rendering": 0,
        "Painting": 0,
        "Other": 0,
    }
    trace_start = float("inf")
    trace_end = 0.0
    long_tasks = 0

    for ev in events:
        if ev.get("ph") != "X":
            continue
        dur = ev.get("dur", 0) / 1000  # microseconds to ms
        ts = ev.get("ts", 0) / 1000
        name = ev.get("name", "")

        trace_start = min(trace_start, ts)
        trace_end = max(trace_end, ts + dur)

        cat = categorize(name)
        totals[cat] += dur

        if dur > 50:
            long_tasks += 1

    duration_s = (trace_end - trace_start) / 1000
    safe_dur = max(duration_s, 0.01)
    return {
        "duration_s": round(duration_s, 2),
        "scripting_ms_per_s": round(totals["Scripting"] / safe_dur, 1),
        "rendering_ms_per_s": round(totals["Rendering"] / safe_dur, 1),
        "painting_ms_per_s": round(totals["Painting"] / safe_dur, 1),
        "long_tasks": long_tasks,
        "long_tasks_per_s": round(long_tasks / safe_dur, 2),
    }


def main():
    parser = argparse.ArgumentParser(description="Analyze Chrome traces")
    parser.add_argument("traces", nargs="+", help="Chrome trace JSON files")
    parser.add_argument("-o", "--output", default="trace-comparison.png")
    args = parser.parse_args()

    data = {}
    for path_str in args.traces:
        name = Path(path_str).stem
        data[name] = analyze_trace(path_str)
        print(f"\n{name}:")
        for k, v in data[name].items():
            print(f"  {k}: {v}")

    metrics = [
        "scripting_ms_per_s",
        "rendering_ms_per_s",
        "painting_ms_per_s",
        "long_tasks_per_s",
    ]
    labels = [
        "Scripting (ms/s)",
        "Rendering (ms/s)",
        "Painting (ms/s)",
        "Long Tasks (/s)",
    ]

    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, len(metrics), figsize=(14, 5))

    for i, (metric, label) in enumerate(zip(metrics, labels)):
        ax = axes[i]
        names = list(data.keys())
        values = [data[n][metric] for n in names]
        colors = sns.color_palette("muted", len(names))
        ax.bar(names, values, color=colors)
        ax.set_title(label, fontsize=11, fontweight="bold")
        ax.tick_params(axis="x", rotation=15)
        for j, v in enumerate(values):
            ax.text(j, v, f"{v:.1f}", ha="center", va="bottom", fontsize=9)

    plt.suptitle(
        "Chrome Trace Comparison (per-second normalized)",
        fontsize=14,
        fontweight="bold",
    )
    plt.tight_layout()
    plt.savefig(args.output, dpi=150, bbox_inches="tight")
    print(f"\nSaved to {args.output}")


if __name__ == "__main__":
    main()

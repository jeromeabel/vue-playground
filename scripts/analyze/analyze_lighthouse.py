#!/usr/bin/env python3
"""
Compare Lighthouse reports across benchmark approaches.

Outputs:
  1. Markdown comparison table to stdout (paste into docs/blog posts)
  2. PNG bar chart (visual storytelling)

Usage:
    python analyze_lighthouse.py basic.json primevue.json tanstack.json -o comparison.png

Each JSON is a Lighthouse report exported via:
    lighthouse http://localhost:5173/benchmark/basic-table --output json --output-path basic.json
"""
import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns


# -- Core Web Vitals thresholds (good, needs-improvement) --------------------
# Source: https://web.dev/articles/vitals
THRESHOLDS = {
    "FCP":       (1800,  3000,  "ms"),
    "LCP":       (2500,  4000,  "ms"),
    "TBT":       (200,   600,   "ms"),
    "TTI":       (3800,  7300,  "ms"),
    "SI":        (3400,  5800,  "ms"),
    "Max FID":   (100,   300,   "ms"),
    "CLS":       (0.1,   0.25,  ""),
    "DOM Size":  (1500,  3000,  "elements"),
    "MT Work":   (2000,  4000,  "ms"),
}


def status_emoji(metric: str, value: float) -> str:
    """Return status emoji based on Core Web Vitals thresholds."""
    t = THRESHOLDS.get(metric)
    if t is None:
        return ""
    good, needs_improvement, _ = t
    if value <= good:
        return "pass"
    if value <= needs_improvement:
        return "warn"
    return "FAIL"


def extract_metrics(report: dict) -> dict:
    """Extract all relevant metrics from a Lighthouse report."""
    audits = report.get("audits", {})
    perf_score = report.get("categories", {}).get("performance", {}).get("score")

    def audit_val(key: str) -> float:
        return audits.get(key, {}).get("numericValue", 0)

    return {
        "Score":    round(perf_score * 100) if perf_score is not None else None,
        "FCP":      round(audit_val("first-contentful-paint"), 1),
        "LCP":      round(audit_val("largest-contentful-paint"), 1),
        "TBT":      round(audit_val("total-blocking-time"), 1),
        "TTI":      round(audit_val("interactive"), 1),
        "SI":       round(audit_val("speed-index"), 1),
        "Max FID":  round(audit_val("max-potential-fid"), 1),
        "CLS":      round(audit_val("cumulative-layout-shift"), 4),
        "DOM Size": round(audit_val("dom-size-insight")),
        "MT Work":  round(audit_val("mainthread-work-breakdown"), 1),
    }


def score_emoji(score: float | None) -> str:
    if score is None:
        return ""
    if score >= 90:
        return "pass"
    if score >= 50:
        return "warn"
    return "FAIL"


# -- Markdown output ---------------------------------------------------------

def format_value(metric: str, value: float) -> str:
    """Format a metric value with appropriate units."""
    if metric == "Score":
        return f"{value:.0f}/100" if value is not None else "N/A"
    if metric == "CLS":
        return f"{value:.4f}"
    if metric == "DOM Size":
        return f"{value:,.0f}"
    if metric in ("FCP", "LCP", "TTI", "SI"):
        return f"{value:,.0f} ms ({value / 1000:.2f}s)"
    return f"{value:,.0f} ms"


def print_markdown(data: dict[str, dict]) -> None:
    """Print a markdown comparison table with thresholds and status."""
    names = list(data.keys())

    print("# Lighthouse Benchmark Comparison\n")

    # Score summary
    print("## Performance Scores\n")
    for name in names:
        score = data[name]["Score"]
        emoji = score_emoji(score)
        print(f"- **{name}**: {score}/100 [{emoji}]")
    print()

    # Comparison table
    print("## Metrics Comparison\n")
    header = "| Metric | " + " | ".join(names) + " | Threshold |"
    sep = "|--------|" + "|".join(["--------"] * len(names)) + "|-----------|"
    print(header)
    print(sep)

    metrics_to_show = ["FCP", "LCP", "TBT", "TTI", "SI", "Max FID", "CLS", "DOM Size", "MT Work"]
    for metric in metrics_to_show:
        t = THRESHOLDS.get(metric)
        if t:
            good, needs, unit = t
            threshold_str = f"< {good:g} {unit}".strip()
        else:
            threshold_str = ""

        cells = []
        for name in names:
            val = data[name][metric]
            status = status_emoji(metric, val)
            formatted = format_value(metric, val)
            cells.append(f"{formatted} [{status}]")

        row = f"| {metric} | " + " | ".join(cells) + f" | {threshold_str} |"
        print(row)

    print()

    # Key insights
    print("## Key Insights\n")
    insights = _generate_insights(data, names)
    for insight in insights:
        print(f"- {insight}")

    print("\n---")
    print("*Status: pass = good | warn = needs improvement | FAIL = poor*")


def _generate_insights(data: dict[str, dict], names: list[str]) -> list[str]:
    """Auto-generate actionable insights from the data."""
    insights = []

    # Find best/worst for key metrics
    for metric, label in [("TBT", "Total Blocking Time"), ("LCP", "Largest Contentful Paint"), ("DOM Size", "DOM Size")]:
        values = {n: data[n][metric] for n in names}
        best = min(values, key=values.get)
        worst = max(values, key=values.get)
        if values[worst] > 0 and values[best] > 0:
            ratio = values[worst] / values[best]
            if ratio > 2:
                insights.append(
                    f"**{label}**: {worst} is {ratio:.0f}x worse than {best} "
                    f"({values[worst]:,.0f} vs {values[best]:,.0f})"
                )

    # Flag any FAIL metrics
    for name in names:
        fails = [m for m in THRESHOLDS if status_emoji(m, data[name][m]) == "FAIL"]
        if fails:
            insights.append(f"**{name}** fails on: {', '.join(fails)}")

    # Score comparison
    scores = {n: data[n]["Score"] for n in names if data[n]["Score"] is not None}
    if scores:
        best = max(scores, key=scores.get)
        worst = min(scores, key=scores.get)
        if scores[best] != scores[worst]:
            insights.append(
                f"**Performance score range**: {scores[worst]} ({worst}) to {scores[best]} ({best})"
            )

    return insights


# -- Chart output -------------------------------------------------------------

CHART_METRICS = [
    ("TBT",      "TBT (ms)"),
    ("LCP",      "LCP (ms)"),
    ("DOM Size", "DOM Size"),
    ("SI",       "Speed Index (ms)"),
    ("FCP",      "FCP (ms)"),
    ("Max FID",  "Max FID (ms)"),
]


def save_chart(data: dict[str, dict], output_path: str) -> None:
    """Generate a comparison bar chart PNG."""
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    flat_axes = axes.flatten()
    names = list(data.keys())
    colors = sns.color_palette("muted", len(names))

    for i, (metric_key, chart_label) in enumerate(CHART_METRICS):
        ax = flat_axes[i]
        values = [data[n][metric_key] for n in names]

        bar_colors = []
        for v in values:
            status = status_emoji(metric_key, v)
            if status == "pass":
                bar_colors.append("#4caf50")
            elif status == "warn":
                bar_colors.append("#ff9800")
            elif status == "FAIL":
                bar_colors.append("#f44336")
            else:
                bar_colors.append(colors[0])

        ax.bar(names, values, color=bar_colors)
        ax.set_title(chart_label, fontsize=11, fontweight="bold")
        ax.tick_params(axis="x", rotation=15)
        for j, v in enumerate(values):
            ax.text(j, v, f"{v:,.0f}", ha="center", va="bottom", fontsize=9)

        # Draw threshold lines
        t = THRESHOLDS.get(metric_key)
        if t and max(values) > 0:
            good, needs, _ = t
            if good < max(values) * 1.5:
                ax.axhline(y=good, color="#4caf50", linestyle="--", alpha=0.5, linewidth=1)
            if needs < max(values) * 1.5:
                ax.axhline(y=needs, color="#f44336", linestyle="--", alpha=0.5, linewidth=1)

    plt.suptitle("Lighthouse Benchmark Comparison", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")


# -- Main --------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Compare Lighthouse reports — outputs markdown table + PNG chart"
    )
    parser.add_argument("reports", nargs="+", help="Lighthouse JSON files")
    parser.add_argument("-o", "--output", default="lighthouse-comparison.png",
                        help="Output PNG path (default: lighthouse-comparison.png)")
    parser.add_argument("--no-chart", action="store_true",
                        help="Skip chart generation, only print markdown")
    args = parser.parse_args()

    # Load reports
    data = {}
    for path_str in args.reports:
        path = Path(path_str)
        if not path.exists():
            print(f"Error: {path_str} not found", file=sys.stderr)
            sys.exit(1)
        name = path.stem
        with open(path) as f:
            report = json.load(f)
        if "audits" not in report:
            print(f"Error: {path_str} does not look like a Lighthouse report (no 'audits' key)", file=sys.stderr)
            sys.exit(1)
        data[name] = extract_metrics(report)

    # Markdown to stdout
    print_markdown(data)

    # Chart to file
    if not args.no_chart:
        save_chart(data, args.output)
        print(f"\nChart saved to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()

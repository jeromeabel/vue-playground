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

WARNING: Run against a production build (`pnpm build && pnpm preview`), not `pnpm dev`.
Vite's dev server adds HMR overhead, unoptimized modules, and source maps that inflate
TBT, LCP, and DOM Size — producing metrics that don't reflect real-world performance.
"""
import argparse
import json
import sys
from datetime import datetime, timezone
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


def status_emoji(metric: str, value: float | None) -> str:
    """Return status emoji based on Core Web Vitals thresholds."""
    if value is None:
        return "ERR"
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
    """Extract all relevant metrics from a Lighthouse report.

    Handles both Lighthouse 12 (CLI) and 13 (DevTools) JSON formats.
    Key differences:
      - DOM Size: v12 uses "dom-size", v13 uses "dom-size-insight"
      - NO_LCP: when LCP can't be detected (e.g. 80k DOM nodes blocking
        the main thread), audits report errorMessage instead of numericValue
    """
    audits = report.get("audits", {})
    perf_score = report.get("categories", {}).get("performance", {}).get("score")

    def audit_val(key: str) -> float | None:
        audit = audits.get(key, {})
        if audit.get("errorMessage"):
            return None
        return audit.get("numericValue")

    def dom_size_val() -> float:
        """Try v12 'dom-size' first, fall back to v13 'dom-size-insight'."""
        for key in ("dom-size", "dom-size-insight"):
            val = audits.get(key, {}).get("numericValue")
            if val is not None:
                return val
        return 0

    def safe_round(val: float | None, ndigits: int = 0) -> float | None:
        return round(val, ndigits) if val is not None else None

    return {
        "Score":    round(perf_score * 100) if perf_score is not None else None,
        "FCP":      safe_round(audit_val("first-contentful-paint"), 1),
        "LCP":      safe_round(audit_val("largest-contentful-paint"), 1),
        "TBT":      safe_round(audit_val("total-blocking-time"), 1),
        "TTI":      safe_round(audit_val("interactive"), 1),
        "SI":       safe_round(audit_val("speed-index"), 1),
        "Max FID":  safe_round(audit_val("max-potential-fid"), 1),
        "CLS":      safe_round(audit_val("cumulative-layout-shift"), 4),
        "DOM Size": round(dom_size_val()),
        "MT Work":  safe_round(audit_val("mainthread-work-breakdown"), 1),
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

def format_value(metric: str, value: float | None) -> str:
    """Format a metric value with appropriate units."""
    if value is None:
        return "N/A"
    if metric == "Score":
        return f"{value:.0f}/100"
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
        values = {n: data[n][metric] for n in names if data[n][metric] is not None}
        if len(values) < 2:
            # Flag approaches that couldn't be measured
            unmeasured = [n for n in names if data[n][metric] is None]
            if unmeasured:
                insights.append(f"**{label}**: {', '.join(unmeasured)} could not be measured (NO_LCP)")
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

    # Flag any FAIL or ERR metrics
    for name in names:
        fails = [m for m in THRESHOLDS if status_emoji(m, data[name][m]) in ("FAIL", "ERR")]
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


# -- JSON output -------------------------------------------------------------

def to_json(
    data: dict[str, dict],
    config: dict | None = None,
    metrics_filter: list[str] | None = None,
) -> dict:
    """Return a structured JSON envelope for the benchmark data."""
    if config is None:
        config = {"iterations": 1, "aggregation": "single", "preset": "desktop"}

    thresholds = {
        metric: {"good": good, "poor": poor, "unit": unit}
        for metric, (good, poor, unit) in THRESHOLDS.items()
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
        raw_values = [data[n][metric_key] for n in names]
        # Replace None with 0 for charting; mark as unmeasurable
        values = [v if v is not None else 0 for v in raw_values]

        bar_colors = []
        for v, raw in zip(values, raw_values):
            if raw is None:
                bar_colors.append("#9e9e9e")  # grey for unmeasurable
            else:
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
        for j, (v, raw) in enumerate(zip(values, raw_values)):
            label = "N/A" if raw is None else f"{v:,.0f}"
            ax.text(j, v, label, ha="center", va="bottom", fontsize=9)

        # Draw threshold lines
        t = THRESHOLDS.get(metric_key)
        measurable = [v for v in values if v > 0]
        if t and measurable:
            good, needs, _ = t
            max_val = max(measurable)
            if good < max_val * 1.5:
                ax.axhline(y=good, color="#4caf50", linestyle="--", alpha=0.5, linewidth=1)
            if needs < max_val * 1.5:
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
    parser.add_argument("--json", action="store_true",
                        help="Output JSON to stdout (replaces markdown)")
    parser.add_argument("--json-out", metavar="PATH",
                        help="Write JSON output to file")
    parser.add_argument("--metrics", metavar="M1,M2,...",
                        help="Filter which metrics to include (comma-separated)")
    parser.add_argument("--names", metavar="N1,N2,...",
                        help="Custom labels for approaches (comma-separated, must match number of reports)")
    args = parser.parse_args()

    # Parse optional filters
    metrics_filter = [m.strip() for m in args.metrics.split(",")] if args.metrics else None
    custom_names = [n.strip() for n in args.names.split(",")] if args.names else None

    if custom_names is not None and len(custom_names) != len(args.reports):
        print(
            f"Error: --names has {len(custom_names)} value(s) but {len(args.reports)} report(s) were provided",
            file=sys.stderr,
        )
        sys.exit(1)

    # Load reports
    data = {}
    for i, path_str in enumerate(args.reports):
        path = Path(path_str)
        if not path.exists():
            print(f"Error: {path_str} not found", file=sys.stderr)
            sys.exit(1)
        name = custom_names[i] if custom_names is not None else path.stem
        with open(path) as f:
            report = json.load(f)
        if "audits" not in report:
            print(f"Error: {path_str} does not look like a Lighthouse report (no 'audits' key)", file=sys.stderr)
            sys.exit(1)
        url = report.get("requestedUrl", "") or report.get("finalUrl", "")
        if ":5173" in url:
            print(
                f"Warning: {path_str} was captured against a dev server ({url}).\n"
                "  Results will be inflated. Use `pnpm build && pnpm preview` for accurate metrics.",
                file=sys.stderr,
            )
        data[name] = extract_metrics(report)

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

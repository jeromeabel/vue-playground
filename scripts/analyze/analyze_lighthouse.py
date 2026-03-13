#!/usr/bin/env python3
"""
Compare Lighthouse reports across benchmark approaches.

Usage:
    python analyze_lighthouse.py basic.json primevue.json tanstack.json -o comparison.png

Each JSON is a Lighthouse report exported via:
    lighthouse http://localhost:5173/benchmark/basic-table --output json --output-path basic.json
"""
import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns


def extract_metrics(report: dict) -> dict:
    audits = report.get("audits", {})
    return {
        "Performance Score": report.get("categories", {})
        .get("performance", {})
        .get("score", 0)
        * 100,
        "TBT (ms)": audits.get("total-blocking-time", {}).get("numericValue", 0),
        "FCP (ms)": audits.get("first-contentful-paint", {}).get("numericValue", 0),
        "LCP (ms)": audits.get("largest-contentful-paint", {}).get("numericValue", 0),
        "CLS": audits.get("cumulative-layout-shift", {}).get("numericValue", 0),
        "DOM Size": audits.get("dom-size", {}).get("numericValue", 0),
    }


def main():
    parser = argparse.ArgumentParser(description="Compare Lighthouse reports")
    parser.add_argument("reports", nargs="+", help="Lighthouse JSON files")
    parser.add_argument("-o", "--output", default="lighthouse-comparison.png")
    args = parser.parse_args()

    data = {}
    for path_str in args.reports:
        name = Path(path_str).stem
        with open(path_str) as f:
            report = json.load(f)
        data[name] = extract_metrics(report)

    metrics = list(next(iter(data.values())).keys())

    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    flat_axes = axes.flatten()

    for i, metric in enumerate(metrics):
        ax = flat_axes[i]
        names = list(data.keys())
        values = [data[n][metric] for n in names]
        colors = sns.color_palette("muted", len(names))
        ax.bar(names, values, color=colors)
        ax.set_title(metric, fontsize=11, fontweight="bold")
        ax.tick_params(axis="x", rotation=15)
        for j, v in enumerate(values):
            ax.text(j, v, f"{v:.0f}", ha="center", va="bottom", fontsize=9)

    plt.suptitle("Lighthouse Benchmark Comparison", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(args.output, dpi=150, bbox_inches="tight")
    print(f"Saved to {args.output}")


if __name__ == "__main__":
    main()

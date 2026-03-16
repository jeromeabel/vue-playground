"""Lighthouse comparison bar chart."""
import matplotlib.pyplot as plt
import seaborn as sns

from bench.lighthouse.extract import THRESHOLDS, status_for

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
        raw_values = [data[n].get(metric_key) for n in names]
        # Replace None with 0 for charting; mark as unmeasurable
        values = [v if v is not None else 0 for v in raw_values]

        bar_colors = []
        for v, raw in zip(values, raw_values):
            if raw is None:
                bar_colors.append("#9e9e9e")  # grey for unmeasurable
            else:
                status = status_for(metric_key, v)
                if status == "pass":
                    bar_colors.append("#4caf50")
                elif status == "warn":
                    bar_colors.append("#ff9800")
                elif status == "fail":
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
            good = t["good"]
            needs = t["poor"]
            max_val = max(measurable)
            if good < max_val * 1.5:
                ax.axhline(y=good, color="#4caf50", linestyle="--", alpha=0.5, linewidth=1)
            if needs < max_val * 1.5:
                ax.axhline(y=needs, color="#f44336", linestyle="--", alpha=0.5, linewidth=1)

    plt.suptitle("Lighthouse Benchmark Comparison", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")

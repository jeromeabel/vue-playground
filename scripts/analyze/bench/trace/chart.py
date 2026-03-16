"""Trace comparison bar chart."""
import matplotlib.pyplot as plt
import seaborn as sns


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

    plt.suptitle("Chrome Trace Comparison", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")

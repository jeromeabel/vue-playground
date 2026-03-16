"""Compare analysis JSON files and emit markdown, JSON, and charts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from bench.compare import compare
from bench.config import load_config
from bench.formats import comparison_to_json
from bench.lighthouse.chart import save_chart as save_lighthouse_chart
from bench.lighthouse.extract import THRESHOLDS as LIGHTHOUSE_THRESHOLDS
from bench.lighthouse.extract import status_for as lighthouse_status_for
from bench.trace.chart import save_chart as save_trace_chart
from bench.trace.extract import THRESHOLDS as TRACE_THRESHOLDS

SCRIPTS_ANALYZE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = SCRIPTS_ANALYZE_DIR / "benchmark-config.json"


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register the compare command."""
    parser = subparsers.add_parser(
        "compare",
        description="Compare analysis JSON files of the same type",
    )
    parser.add_argument("files", nargs="+", help="Analysis JSON files to compare")
    parser.add_argument("--chart", help="Optional chart output path")
    parser.add_argument("--json-out", help="Optional combined JSON output path")
    parser.add_argument("--no-markdown", action="store_true", help="Suppress markdown output")
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG_PATH),
        help="Config file path (default: scripts/analyze/benchmark-config.json)",
    )
    parser.set_defaults(func=_run_compare)


def _run_compare(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    analyses_by_label, raw_metrics_by_label, analysis_type = _load_analyses(args.files, config)
    display = config.get("display", {}).get(analysis_type)
    result = compare(analyses_by_label, display=display)
    thresholds = LIGHTHOUSE_THRESHOLDS if analysis_type == "lighthouse" else TRACE_THRESHOLDS
    capture_config = dict(config.get("capture", {}))

    if not args.no_markdown:
        print(_render_markdown(analysis_type, result.approaches, result.metric_keys, thresholds, result.insights, result.sources))

    if args.chart:
        chart_path = Path(args.chart)
        chart_path.parent.mkdir(parents=True, exist_ok=True)
        if analysis_type == "lighthouse":
            save_lighthouse_chart(raw_metrics_by_label, str(chart_path))
        else:
            save_trace_chart(raw_metrics_by_label, str(chart_path))
        print(f"Saved {analysis_type} chart to {chart_path}", file=sys.stderr)

    if args.json_out:
        output_path = Path(args.json_out)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = comparison_to_json(
            approaches=result.approaches,
            config=capture_config,
            thresholds=thresholds,
            metric_keys=result.metric_keys,
        )
        with output_path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, indent=2)
            file.write("\n")
        print(f"Saved comparison JSON to {output_path}", file=sys.stderr)


def _load_analyses(files: list[str], config: dict) -> tuple[dict[str, dict], dict[str, dict], str]:
    analyses_with_names: list[tuple[str, str, dict]] = []
    seen_types: set[str] = set()
    for value in files:
        path = Path(value)
        if not path.exists():
            print(f"Error: {value} not found", file=sys.stderr)
            raise SystemExit(1)

        with path.open(encoding="utf-8") as file:
            analysis = json.load(file)

        analysis_type = analysis.get("type")
        if analysis_type not in {"lighthouse", "trace"}:
            print(f"Error: {path} is missing a valid analysis type", file=sys.stderr)
            raise SystemExit(1)

        seen_types.add(analysis_type)
        raw_name = _derive_approach_name(path, analysis_type)
        label = config.get("approaches", {}).get(raw_name, {}).get("label", raw_name)
        analyses_with_names.append((label, raw_name, analysis))

    if len(seen_types) != 1:
        found = ", ".join(sorted(seen_types))
        print(
            f"Error: cannot compare analyses of different types (found: {found}).\nRun separate comparisons per type.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    analysis_type = next(iter(seen_types))
    analyses_by_label = {label: analysis for label, _, analysis in analyses_with_names}
    raw_metrics_by_label = {label: dict(analysis["metrics"]) for label, _, analysis in analyses_with_names}
    return analyses_by_label, raw_metrics_by_label, analysis_type


def _derive_approach_name(path: Path, analysis_type: str) -> str:
    suffix = f".{analysis_type}.json"
    if path.name.endswith(suffix):
        return path.name[: -len(suffix)]
    return path.stem


def _render_markdown(
    analysis_type: str,
    approaches: dict[str, dict],
    metric_keys: list[str],
    thresholds: dict,
    insights: list[str],
    sources: dict[str, dict],
) -> str:
    lines: list[str] = []
    title = "Lighthouse Benchmark Comparison" if analysis_type == "lighthouse" else "Chrome Trace Comparison"
    lines.append(f"# {title}")
    lines.append("")

    if analysis_type == "trace":
        lines.append("## Trace Types")
        lines.append("")
        for name, source in sources.items():
            trace_type = _trace_type(source)
            duration = source.get("durationS")
            duration_text = f" ({duration}s)" if duration is not None else ""
            lines.append(f"- **{name}**: {trace_type}{duration_text}")
        lines.append("")

    lines.append("## Metrics Comparison")
    lines.append("")
    header = "| Metric | " + " | ".join(approaches.keys()) + " | Threshold |"
    separator = "|--------|" + "|".join(["--------"] * len(approaches)) + "|-----------|"
    lines.append(header)
    lines.append(separator)

    for metric in metric_keys:
        threshold_text = _threshold_text(metric, thresholds.get(metric))
        cells = []
        for values in approaches.values():
            cells.append(_format_markdown_cell(analysis_type, metric, values.get(metric), thresholds))
        lines.append(f"| {metric} | " + " | ".join(cells) + f" | {threshold_text} |")

    if insights:
        lines.append("")
        lines.append("## Key Insights")
        lines.append("")
        for insight in insights:
            lines.append(f"- {insight}")

    return "\n".join(lines)


def _format_markdown_cell(analysis_type: str, metric: str, value: object, thresholds: dict) -> str:
    if value is None:
        return "N/A"

    if analysis_type == "lighthouse":
        status = lighthouse_status_for(metric, value)
        label = _format_lighthouse_value(metric, value)
        return f"{label} [{status}]" if status else label

    return _format_trace_value(metric, value)


def _format_lighthouse_value(metric: str, value: object) -> str:
    number = value
    if metric == "Score":
        return f"{number:.0f}/100"
    if metric == "CLS":
        return f"{number:.4f}"
    if metric == "DOM Size":
        return f"{number:,.0f}"
    return f"{number:,.1f}" if isinstance(number, float) and not number.is_integer() else f"{number:,.0f}"


def _format_trace_value(metric: str, value: object) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    if isinstance(value, float):
        return f"{value:,.2f}" if not value.is_integer() else f"{value:,.0f}"
    return str(value)


def _threshold_text(metric: str, threshold: dict | None) -> str:
    if not threshold:
        return ""

    good = threshold.get("good")
    unit = threshold.get("unit", "")
    higher_is_better = threshold.get("higher_is_better", False)
    comparator = ">=" if higher_is_better else "<="
    return f"{comparator} {good:g} {unit}".strip()


def _trace_type(source: dict) -> str:
    if source.get("hasScroll"):
        return "load + scroll"
    if source.get("hasInteraction"):
        return "load + interaction"
    return "load only"

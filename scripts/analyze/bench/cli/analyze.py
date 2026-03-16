"""Analyze a single Lighthouse report or Chrome trace into JSON."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from bench.formats import analysis_to_json
from bench.lighthouse.extract import THRESHOLDS as LIGHTHOUSE_THRESHOLDS
from bench.lighthouse.extract import extract_metrics as extract_lighthouse_metrics
from bench.lighthouse.extract import extract_source as extract_lighthouse_source
from bench.trace.extract import THRESHOLDS as TRACE_THRESHOLDS
from bench.trace.extract import analyze_trace
from bench.trace.extract import extract_source as extract_trace_source

SCRIPTS_ANALYZE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_ANALYSES_DIR = SCRIPTS_ANALYZE_DIR / "outputs" / "analyses"


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register the analyze command and its type subcommands."""
    parser = subparsers.add_parser(
        "analyze",
        description="Analyze one raw benchmark file into an analysis JSON envelope",
    )
    analyze_subparsers = parser.add_subparsers(dest="analysis_type")

    lighthouse = analyze_subparsers.add_parser(
        "lighthouse",
        help="Analyze one Lighthouse JSON report",
    )
    lighthouse.add_argument("file", help="Lighthouse report JSON file")
    lighthouse.add_argument("--name", help="Output name override")
    lighthouse.add_argument(
        "-o",
        "--output",
        help="Output JSON path (default: scripts/analyze/outputs/analyses/{name}.lighthouse.json)",
    )
    lighthouse.set_defaults(func=_run_lighthouse)

    trace = analyze_subparsers.add_parser(
        "trace",
        help="Analyze one Chrome Performance trace JSON",
    )
    trace.add_argument("file", help="Trace JSON file or quoted glob pattern")
    trace.add_argument("--name", required=True, help="Output name for the trace analysis")
    trace.add_argument(
        "-o",
        "--output",
        help="Output JSON path (default: scripts/analyze/outputs/analyses/{name}.trace.json)",
    )
    trace.set_defaults(func=_run_trace)


def _resolve_input_path(value: str) -> Path:
    path = Path(value)
    if path.exists():
        return path

    if not any(token in value for token in "*?["):
        print(f"Error: {value} not found", file=sys.stderr)
        raise SystemExit(1)

    matches = sorted(Path().glob(value))
    if not matches:
        print(f"Error: no files matched {value}", file=sys.stderr)
        raise SystemExit(1)

    if len(matches) > 1:
        selected = max(matches, key=lambda match: match.stat().st_mtime)
        print(
            f"Warning: {value} matched {len(matches)} files; using latest {selected}",
            file=sys.stderr,
        )
        return selected

    return matches[0]


def _default_output(name: str, analysis_type: str) -> Path:
    return DEFAULT_ANALYSES_DIR / f"{name}.{analysis_type}.json"


def _write_json(output_path: Path, payload: dict) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2)
        file.write("\n")


def _run_lighthouse(args: argparse.Namespace) -> None:
    input_path = _resolve_input_path(args.file)
    with input_path.open(encoding="utf-8") as file:
        report = json.load(file)

    if "audits" not in report:
        print(
            f"Error: {input_path} does not look like a Lighthouse report (no 'audits' key)",
            file=sys.stderr,
        )
        raise SystemExit(1)

    source = extract_lighthouse_source(report, input_path.name)
    if ":5173" in source.get("url", ""):
        print(
            "Warning: report was captured against a dev server; use `pnpm build && pnpm preview` for accurate metrics.",
            file=sys.stderr,
        )

    name = args.name or input_path.stem
    output_path = Path(args.output) if args.output else _default_output(name, "lighthouse")
    payload = analysis_to_json(
        metrics=extract_lighthouse_metrics(report),
        source=source,
        analysis_type="lighthouse",
        thresholds=LIGHTHOUSE_THRESHOLDS,
    )
    _write_json(output_path, payload)
    print(f"Saved lighthouse analysis to {output_path}", file=sys.stderr)


def _run_trace(args: argparse.Namespace) -> None:
    input_path = _resolve_input_path(args.file)
    with input_path.open(encoding="utf-8") as file:
        raw_data = json.load(file)

    events = raw_data if isinstance(raw_data, list) else raw_data.get("traceEvents", [])
    result = analyze_trace(events)
    if result is None:
        print(
            f"Error: {input_path} is not a valid Chrome trace (no CrRendererMain thread found)",
            file=sys.stderr,
        )
        raise SystemExit(1)

    output_path = Path(args.output) if args.output else _default_output(args.name, "trace")
    payload = analysis_to_json(
        metrics=result["metrics"],
        source=extract_trace_source(result, input_path.name),
        analysis_type="trace",
        thresholds=TRACE_THRESHOLDS,
    )
    _write_json(output_path, payload)
    print(f"Saved trace analysis to {output_path}", file=sys.stderr)

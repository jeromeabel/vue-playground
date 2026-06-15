#!/usr/bin/env python
"""Aggregate N Lighthouse runs per approach into a median analysis envelope.

Lighthouse scores vary 5-15% between runs (GC timing, background processes,
thermal throttling). A single run is an anecdote. This reads every
`runs/{approach}-*.json` capture, extracts metrics with the shared bench
extractor, takes the per-metric median across runs, and writes the same
`outputs/analyses/{approach}.lighthouse.json` envelope that `bench compare`
already consumes -- so the "5 runs, median" the config claims is actually true.

Usage:
    aggregate_lighthouse.py basic primevue tanstack
"""

from __future__ import annotations

import statistics
import sys
from pathlib import Path

from bench.formats import analysis_to_json
from bench.lighthouse.extract import THRESHOLDS
from bench.lighthouse.extract import extract_metrics, extract_source
from bench.cli.analyze import _write_json  # reuse the pretty-printer

SCRIPTS_ANALYZE_DIR = Path(__file__).resolve().parent
RUNS_DIR = SCRIPTS_ANALYZE_DIR / "inputs" / "lighthouse" / "runs"
ANALYSES_DIR = SCRIPTS_ANALYZE_DIR / "outputs" / "analyses"


def _load_report(path: Path) -> dict:
    import json

    with path.open(encoding="utf-8") as file:
        return json.load(file)


def median_metrics(reports: list[dict]) -> dict:
    """Per-metric median across runs. None when every run is missing the metric."""
    per_run = [extract_metrics(report) for report in reports]
    keys = per_run[0].keys()
    out: dict[str, float | None] = {}
    for key in keys:
        values = [run[key] for run in per_run if run[key] is not None]
        out[key] = statistics.median(values) if values else None
    return out


def aggregate(approach: str) -> Path:
    runs = sorted(RUNS_DIR.glob(f"{approach}-*.json"))
    if not runs:
        print(f"Error: no runs matched {RUNS_DIR}/{approach}-*.json", file=sys.stderr)
        raise SystemExit(1)

    reports = [_load_report(path) for path in runs]
    metrics = median_metrics(reports)
    source = extract_source(reports[0], f"{approach} (median of {len(runs)} runs)")
    source["runs"] = len(runs)

    payload = analysis_to_json(
        metrics=metrics,
        source=source,
        analysis_type="lighthouse",
        thresholds=THRESHOLDS,
    )
    output_path = ANALYSES_DIR / f"{approach}.lighthouse.json"
    _write_json(output_path, payload)
    print(f"Aggregated {len(runs)} runs -> {output_path}", file=sys.stderr)
    return output_path


def main(argv: list[str]) -> None:
    approaches = argv or ["basic", "primevue", "tanstack"]
    for approach in approaches:
        aggregate(approach)


if __name__ == "__main__":
    main(sys.argv[1:])

# Benchmark Analysis

The analysis tooling now follows a two-stage pipeline:

```text
raw report/trace -> bench analyze -> analysis JSON
analysis JSONs -> bench compare -> markdown + chart + app JSON
```

That split is deliberate. `bench analyze` is exhaustive and lossless for one input file. `bench compare` is where filtering, labels, insights, charts, and the Vue app output schema happen.

## Setup

Install `uv` once, then create the Python environment from the repo root:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
pnpm setup:python
```

This creates `scripts/analyze/.venv/` and installs the `bench` package in editable mode with test dependencies.

## Important: Use a Production Build

Do not benchmark against `pnpm dev`. The Vite dev server adds HMR overhead, unoptimized modules, and source maps that inflate load and scripting metrics.

Always capture against a production build:

```bash
pnpm build && pnpm preview
```

The Lighthouse analyzer warns if it detects a `:5173` dev-server URL in the report.

## Directory Layout

```text
scripts/analyze/
├── benchmark-config.json
├── bench/
│   ├── cli/
│   ├── lighthouse/
│   ├── trace/
│   ├── compare.py
│   ├── config.py
│   └── formats.py
├── inputs/
│   ├── lighthouse/
│   └── traces/
└── outputs/
    ├── analyses/
    └── comparisons/
```

`inputs/` holds raw captures. `outputs/analyses/` holds one JSON envelope per raw file. `outputs/comparisons/` holds generated charts and any comparison artifacts you want to keep around locally.

## CLI Usage

### Analyze one Lighthouse report

```bash
scripts/analyze/.venv/bin/bench analyze lighthouse \
  scripts/analyze/inputs/lighthouse/basic.json \
  --name basic
```

This writes `scripts/analyze/outputs/analyses/basic.lighthouse.json` by default.

### Analyze one trace

```bash
scripts/analyze/.venv/bin/bench analyze trace \
  scripts/analyze/inputs/traces/Trace-20260315T111552-basic.json \
  --name basic
```

This writes `scripts/analyze/outputs/analyses/basic.trace.json` by default.

Trace names require `--name` because trace filenames usually carry timestamps rather than stable approach names.

### Compare analyses

```bash
scripts/analyze/.venv/bin/bench compare \
  scripts/analyze/outputs/analyses/*.lighthouse.json \
  --chart scripts/analyze/outputs/comparisons/lighthouse-comparison.png \
  --json-out public/data/benchmark-results.json
```

By default, `bench compare` prints markdown to stdout. Add `--no-markdown` to suppress that.

### Key CLI options

| Command | Option | Purpose |
|---------|--------|---------|
| `bench analyze lighthouse` | `--name` | Override the output name |
| `bench analyze lighthouse` | `-o`, `--output` | Override the analysis JSON path |
| `bench analyze trace` | `--name` | Required stable approach name |
| `bench analyze trace` | `-o`, `--output` | Override the analysis JSON path |
| `bench compare` | `--chart PATH` | Generate a PNG chart |
| `bench compare` | `--json-out PATH` | Write the combined app JSON |
| `bench compare` | `--no-markdown` | Suppress markdown output |
| `bench compare` | `--config PATH` | Load a different config file |

## pnpm Shortcuts

From the repo root:

```bash
pnpm analyze:lighthouse
pnpm compare:lighthouse

pnpm analyze:trace
pnpm compare:trace
```

`analyze:*` generates per-approach analysis JSON files. `compare:*` generates the combined JSON consumed by the Vue app and, when requested, comparison charts under `scripts/analyze/outputs/comparisons/`.

## Config File

`benchmark-config.json` drives presentation rather than extraction.

- `capture` becomes the flat `config` object embedded in the final comparison JSON.
- `display` decides which metrics are primary, secondary, or hidden for each analysis type.
- `approaches` maps internal names like `basic` to display labels like `Basic Table`.

If the config file is missing, the package falls back to defaults and shows all metrics.

## Why Two Tools?

Lighthouse and Chrome traces measure fundamentally different things. Using only one gives an incomplete picture.

Lighthouse captures a simulated page load. It is strongest at first-load metrics: FCP, LCP, TBT, main-thread work, and DOM size.

Chrome Performance traces capture what happens during and after load. They show scripting cost, long tasks, frame production, rendering, painting, and virtual-scroll initialization overhead.

The basic table is the clearest example of why both matter. It can score perfectly on Lighthouse while still creating an 80,000-node DOM that turns scroll performance into a runtime problem. The trace data exposes that gap.

## Which Metrics Matter?

Primary metrics for this benchmark:

- `DOM Size` is the strongest early warning for runtime pain on large tables.
- `TBT` shows whether the main thread is blocked during load.
- `longest_task_ms` reveals visible freezes.
- `scripting_ms_per_s` makes load-only traces comparable even when total durations differ.

Secondary metrics:

- `raf_total_ms` and `raf_mean_ms` help compare virtual-scroll initialization overhead.
- `LCP` is useful, but it is not the main differentiator in this benchmark.
- `CLS` is usually low-value here because the table layout is stable.

Metrics that require matched interaction patterns:

- `fps` is only meaningful when the traces cover the same kind of interaction. The compare logic explicitly refuses to treat mixed load-only and rAF-driven traces as directly comparable.

## Capture Notes

### Lighthouse

Use the provided shortcuts:

```bash
pnpm lighthouse:all
```

Reports are written to `scripts/analyze/inputs/lighthouse/`.

The capture parameters stay aligned with `benchmark-config.json`:

| Flag | Value | Why |
|------|-------|-----|
| `--preset=desktop` | desktop | Desktop viewport, no mobile emulation |
| `--chrome-flags='--incognito'` | `--incognito` | Reduces extension noise |
| `--throttling.cpuSlowdownMultiplier=4` | `4` | Simulates a mid-tier device |
| `--only-categories=performance` | performance | Keeps runs focused and faster |

### Chrome traces

1. Open a benchmark page in Chrome.
2. Record in the Performance panel.
3. Save the trace into `scripts/analyze/inputs/traces/`.

Record with CPU `4x` slowdown and use an Incognito window so the conditions match Lighthouse as closely as possible.

## Tests

```bash
pnpm test:python:fast
pnpm test:python
```

The Python tests live under `scripts/analyze/bench/` and cover extraction, comparison, JSON envelopes, CLI behavior, and slow integration checks against real input files.

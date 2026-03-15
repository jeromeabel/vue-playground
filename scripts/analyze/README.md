# Benchmark Analysis

Scripts to analyze Lighthouse reports and Chrome traces for the benchmark pages.

## Setup

Install [uv](https://docs.astral.sh/uv/) (one-time), then create the Python environment:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
pnpm setup:python
```

This creates a venv at `scripts/analyze/.venv/` with all dependencies.

## Important: Use a Production Build

**Do not benchmark against `pnpm dev`.** Vite's dev server adds HMR overhead, unoptimized modules, and source maps that inflate TBT, LCP, DOM Size, scripting time, and long tasks.

Always benchmark against a production build:

```bash
pnpm build && pnpm preview
```

This serves the optimized build on `http://localhost:4173`. The `pnpm lighthouse:*` scripts already target port 5173 — update them if you switch to preview mode, or run Lighthouse manually against `:4173`.

## Lighthouse Analysis

### Capture Reports

```bash
pnpm lighthouse:all
```

Or individually: `pnpm lighthouse:basic`, `pnpm lighthouse:primevue`, `pnpm lighthouse:tanstack`.

Reports are saved to `scripts/analyze/reports/`.

### Compare Reports

Markdown + PNG chart:

```bash
pnpm analyze:lighthouse
```

JSON output (for the benchmark page):

```bash
pnpm analyze:lighthouse:json
```

This writes `public/data/benchmark-results.json`, which the benchmark index page loads via TanStack Query.

### CLI Options

| Flag | Purpose |
|------|---------|
| `--no-chart` | Skip PNG chart, only print markdown |
| `--json` | Output JSON to stdout |
| `--json-out PATH` | Write JSON to file |
| `--metrics M1,M2,...` | Filter metrics (comma-separated) |
| `--names N1,N2,...` | Custom labels for approaches |

## Chrome Trace Analysis

### Capture Traces

1. Open a benchmark page in Chrome (e.g., `http://localhost:4173/benchmark/basic-table`)
2. DevTools > **Performance** tab > **Record** > interact ~10 seconds > **Stop**
3. **Save profile** > move to `scripts/analyze/reports/` (e.g., `trace-basic.json`)

### Compare Traces

```bash
scripts/analyze/.venv/bin/python scripts/analyze/analyze_trace.py \
  scripts/analyze/reports/trace-basic.json \
  scripts/analyze/reports/trace-tanstack.json \
  -o scripts/analyze/reports/trace-comparison.png
```

Supports the same `--json`, `--json-out`, `--metrics`, `--names` flags as the Lighthouse script.

### What Trace Analysis Measures

- FPS estimation from frame commits
- Scripting / rendering / painting breakdown (ms and ms/s)
- Long task detection (>50ms) with profiler artifact filtering
- AnimationFrame and rAF callback stats

## Benchmark Config

`benchmark-config.json` documents recommended capture settings for reproducible results:

- Run 5+ iterations and take the median
- Use Chrome Incognito with extensions disabled
- Close other tabs and avoid heavy background tasks
- Desktop preset uses no network throttling

See the file for the full list of meaningful metrics (primary vs secondary).

## What Each Script Measures

| Script | Input | Key Metrics |
|---|---|---|
| `analyze_lighthouse.py` | Lighthouse JSON | Performance score, FCP, LCP, TBT, TTI, CLS, DOM Size, Main Thread Work |
| `analyze_trace.py` | Chrome trace JSON | FPS, scripting/rendering/painting breakdown, long tasks, rAF cost |

| Concern | Lighthouse | Trace |
|---|---|---|
| Page load performance | Yes | No |
| Runtime rendering perf | No | Yes |
| DOM size impact | Yes | Partially |
| Frame drops during interaction | No | Yes |
| Core Web Vitals thresholds | Yes | No |

## Tests

```bash
pnpm test:python:fast   # all tests (~0.4s)
pnpm test:python        # includes slow tests if trace files exist
```

Tests use the project's own Lighthouse reports in `scripts/analyze/reports/` as sample data.

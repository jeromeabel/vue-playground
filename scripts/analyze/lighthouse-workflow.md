# Benchmark Analysis Workflow

This folder contains scripts to analyze Lighthouse reports and Chrome traces for benchmark pages.

## Prerequisites

- Run the app in a separate terminal:

```bash
pnpm dev
```

- Install uv (one-time):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Lighthouse Analysis

### Capture Reports

Generate one report per benchmark page:

```bash
pnpm lighthouse:basic
pnpm lighthouse:primevue
pnpm lighthouse:tanstack
```

Or run all three:

```bash
pnpm lighthouse:all
```

Reports are written to `scripts/analyze/reports/`.

### Compare Reports

```bash
pnpm analyze:lighthouse
```

This outputs:
- **Markdown comparison table** to stdout (paste into docs/blog posts)
- **PNG chart** to `scripts/analyze/reports/lighthouse-comparison.png`

Options:
- `--no-chart` — skip chart generation, only print markdown

## Chrome Trace Analysis

### Capture Traces

1. Open a benchmark page in Chrome (e.g., `http://localhost:5173/benchmark/basic-table`)
2. Open DevTools > **Performance** tab
3. Click **Record**, interact with the page for ~10 seconds, then **Stop**
4. Click the **Save profile** button — saves a `.json` trace file
5. Move the file to `scripts/analyze/reports/` (e.g., `trace-basic.json`)

### Compare Traces

```bash
uv run --with-requirements scripts/analyze/requirements.txt \
  python3 scripts/analyze/analyze_trace.py \
  scripts/analyze/reports/trace-basic.json \
  scripts/analyze/reports/trace-tanstack.json \
  -o scripts/analyze/reports/trace-comparison.png
```

This outputs:
- **Markdown report** to stdout (per-trace breakdown + comparison table)
- **PNG chart** to the specified output path

Features:
- Properly identifies CrRendererMain thread (ignores worker/GPU events)
- Filters out CpuProfiler::StartProfiling artifacts (DevTools overhead, not app code)
- Frame counting and FPS estimation
- AnimationFrame and rAF callback stats
- Long task detection with hierarchical breakdown

## What Each Script Measures

| Script | Input | Key Metrics |
|---|---|---|
| `analyze_lighthouse.py` | Lighthouse JSON | Performance score, FCP, LCP, TBT, TTI, CLS, DOM Size, Main Thread Work |
| `analyze_trace.py` | Chrome trace JSON | FPS, scripting/rendering/painting breakdown, long tasks, rAF cost |

These are **two different tools** measuring different things:

| Concern | Use Lighthouse | Use Trace |
|---|---|---|
| Page load performance | Yes | No |
| Runtime rendering perf | No | Yes |
| DOM size impact | Yes | Partially |
| Frame drops during interaction | No | Yes |
| Core Web Vitals thresholds | Yes | No |

## Notes

- Scripts use `uv run --with-requirements ...`, so they do not install into your system Python.
- For consistent results, close other tabs and avoid heavy background tasks while benchmarking.
- Run Lighthouse 3-5 times and use the median for reliable numbers.

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

## How the Pipeline Works

The pipeline has three stages: **capture**, **analyze**, and **compare**. Each stage has a clear responsibility and a well-defined input/output boundary.

### Stage 1: Raw Data Capture

Raw data is captured manually outside of the `bench` tool.

**Lighthouse reports** are captured with the Lighthouse CLI (or `pnpm lighthouse:all`). The CLI runs a simulated page load against a production build (`pnpm preview`) and produces a single JSON file per approach. Each report contains full audit results: numeric metric values, score breakdowns, and metadata like the requested URL and Lighthouse version.

**Chrome traces** are captured from the Chrome DevTools Performance panel. You hit Record, interact with (or just load) the page, then save the trace JSON. Each file contains thousands of low-level trace events — function calls, layout recalculations, paints, frame commits, and more — tagged with process IDs, thread IDs, timestamps (`ts` in microseconds), and durations (`dur`).

Both file types land in `inputs/lighthouse/` or `inputs/traces/`.

### Stage 2: `bench analyze` — Extract Metrics From One File

`bench analyze` reads one raw file and produces one analysis JSON envelope. It is exhaustive and lossless: every metric the tool knows about gets extracted, regardless of config.

#### Lighthouse extraction (`bench/lighthouse/extract.py`)

The extractor reads the Lighthouse JSON and pulls numeric values from the `audits` map:

| Metric | Lighthouse audit key | Notes |
|--------|---------------------|-------|
| Score | `categories.performance.score` | Multiplied by 100 (0–100 scale) |
| FCP | `first-contentful-paint` | `numericValue` in ms |
| LCP | `largest-contentful-paint` | `numericValue` in ms |
| TBT | `total-blocking-time` | `numericValue` in ms |
| TTI | `interactive` | `numericValue` in ms |
| SI | `speed-index` | `numericValue` in ms |
| Max FID | `max-potential-fid` | `numericValue` in ms |
| CLS | `cumulative-layout-shift` | Unitless score |
| DOM Size | `dom-size` or `dom-size-insight` | Element count (checks both keys for LH 12/13 compat) |
| MT Work | `mainthread-work-breakdown` | Total main-thread work in ms |

If an audit has an `errorMessage` (e.g. `NO_LCP`), the value is set to `None`.

Source metadata (filename, URL, Lighthouse version) is also captured.

#### Trace extraction (`bench/trace/extract.py`)

The extractor processes the raw trace event array:

1. **Find main threads**: scans for `thread_name` metadata events (`ph: "M"`) where `args.name == "CrRendererMain"`. All subsequent analysis is filtered to these `(pid, tid)` pairs only.

2. **Compute trace duration**: from the min and max timestamps of complete events (`ph: "X"`) on main threads.

3. **Categorize events**: each complete event is classified into Scripting, Rendering, Painting, or Other based on its `name` field. For example, `FunctionCall` and `EvaluateScript` map to Scripting; `Layout` and `RecalculateStyles` map to Rendering; `Paint` and `CompositeLayers` map to Painting. Durations are summed per category.

4. **Find long tasks**: filters for `RunTask` events longer than 50ms. Profiler-setup artifacts (`CpuProfiler::StartProfiling`) are excluded to avoid false positives.

5. **Count frames**: counts `Commit` events (or `BeginMainThreadFrame` as fallback) to derive FPS.

6. **Detect interactions**: scans `EventDispatch` events for user interaction types (scroll, click, pointer, keyboard). This is stored as `has_interaction` and `has_scroll` flags — important for later comparability checks.

7. **Measure animation frames**: collects durations of `AnimationFrame` (af) and `FireAnimationFrame` (raf) events. These reveal virtual-scroll initialization overhead.

8. **Compute derived metrics**: absolute totals are divided by trace duration to produce rate metrics (`scripting_ms_per_s`, `rendering_ms_per_s`, `painting_ms_per_s`). This makes traces of different durations comparable.

#### Output envelope (`bench/formats.py`)

Both extractors wrap their output in the same envelope shape:

```json
{
  "version": 1,
  "type": "lighthouse" | "trace",
  "generatedAt": "2026-03-15T...",
  "source": { /* filename, url, duration, interaction flags */ },
  "metrics": { /* all extracted metric key-value pairs */ },
  "thresholds": { /* good/poor thresholds per metric */ }
}
```

Thresholds come from static dictionaries in each extractor module. For lighthouse metrics, they follow the Web Vitals thresholds (e.g., TBT good ≤ 200ms, poor > 600ms). For trace metrics, they are project-specific (e.g., `longest_task_ms` good ≤ 50ms).

Each metric can also be classified as `pass`, `warn`, `fail`, or `error` using `status_for()`. Higher-is-better metrics (Score, FPS) have inverted comparisons.

### Stage 3: `bench compare` — Combine, Filter, Normalize, and Output

`bench compare` loads multiple analysis envelopes of the same type and produces comparison outputs.

#### Loading and labeling

Analysis files are loaded and their approach name is derived from the filename (e.g., `basic.lighthouse.json` → `basic`). The config file's `approaches` map translates internal names to display labels (e.g., `basic` → `"Basic Table"`).

If the files have mixed types (lighthouse and trace), the tool errors out — you must compare like with like.

#### Display filtering (config-driven)

The config file's `display` section controls which metrics appear:

- **primary**: shown in the comparison table
- **secondary**: also shown, after primary metrics
- **hidden**: extracted during analyze, but excluded from compare output

Only `primary + secondary` metrics pass through to the final output. This keeps the Vue app focused on the metrics that matter for the benchmark story, while the raw analysis envelopes retain everything.

#### Trace normalization

When comparing traces, durations can differ (e.g., one trace is 3.5s, another is 5.2s). Count-based metrics like `long_tasks_count` and `frames_committed` would be unfairly inflated for the longer trace.

The `normalize_traces()` function handles this:

1. Finds the shortest trace duration as the reference.
2. If durations differ by more than 1%, scales count metrics (`long_tasks_count`, `frames_committed`, `raf_count`, `af_count`) and total metrics (`scripting_ms`, `rendering_ms`, `painting_ms`, `raf_total_ms`) by the ratio `reference / actual_duration`.
3. **Rate metrics** (`scripting_ms_per_s`, `fps`, etc.) are left untouched — they are already duration-independent by construction.
4. The original duration is preserved in `original_duration_s` for transparency.

#### FPS comparability check

FPS is only meaningful when traces share the same interaction pattern. The `_fps_comparable()` function checks:

- If all traces have user interaction, or all are load-only → comparable.
- If some use `requestAnimationFrame` (rAF) and some don't → **not comparable**. rAF-driven virtual scrollers commit frames during initialization even without user scrolling, inflating their frame count.

When FPS is not comparable, the insight engine explains why instead of producing a misleading ranking.

#### Insight generation

The compare module auto-generates human-readable insight strings:

**Lighthouse insights**:
- Flags metrics where the worst approach is ≥ 2x the best (e.g., "TBT: basic is 8x worse than tanstack").
- Lists approaches that fail threshold checks.
- Reports the performance score range across approaches.

**Trace insights**:
- Reports FPS differences (only when comparable).
- Compares rAF initialization cost between virtual-scroll approaches.
- Flags approaches where scripting dominates (> 70% of main-thread time).
- Warns about longest tasks exceeding 200ms (severe jank).
- Calculates per-frame cost vs. the 16.67ms budget (60fps target).

#### Outputs

`bench compare` can produce three outputs:

1. **Markdown table** (stdout): a formatted comparison table with metric values, threshold status indicators (`[pass]`, `[warn]`, `[fail]`), and an insights section. Suppressed with `--no-markdown`.

2. **PNG chart** (`--chart`): a 2×3 subplot bar chart. Lighthouse charts color bars by threshold status (green/orange/red). Trace charts show the six most important trace metrics with a 50ms long-task threshold line.

3. **App JSON** (`--json-out`): the final JSON consumed by the Vue app (`BenchmarkTable`, `TraceTable`). Shaped as:

```json
{
  "version": 1,
  "generatedAt": "...",
  "config": { /* capture settings from benchmark-config.json */ },
  "thresholds": { /* only thresholds for included metrics */ },
  "approaches": { "Basic Table": { "TBT": 150, ... }, ... },
  "metrics": ["TBT", "LCP", ...]
}
```

This JSON is written to `public/data/` so the Vue dev server and production build serve it as a static asset.

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

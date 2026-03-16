# Benchmark Analysis

Scripts to analyze Lighthouse reports and Chrome Performance traces for the table-rendering benchmark — comparing three approaches to rendering 10,000 botanical species rows.

## The Three Approaches

| Approach | Strategy | DOM elements | Virtual scroll? |
|----------|----------|-------------|-----------------|
| **Basic Table** | Plain `v-for` over all 10K rows | ~80,000 | No |
| **PrimeVue DataTable** | Component library with built-in virtual scroll | ~500 | Yes |
| **TanStack Table** | Headless table logic + `@tanstack/vue-virtual` | ~330 | Yes |

## Why Two Tools?

Lighthouse and Chrome traces measure fundamentally different things. Using only one gives a dangerously incomplete picture.

**Lighthouse** captures a simulated page load — it navigates to the URL, waits for the page to become interactive, and scores it. It excels at measuring first-load metrics: how fast does the user see content (FCP, LCP), how much does the main thread block during load (TBT), and how large is the resulting DOM.

**Chrome Performance traces** capture what happens *after* the page loads — during scrolling, filtering, and interaction. They reveal frame rates, runtime scripting cost, long tasks that cause visible jank, and how the browser spends its time between scripting, rendering, and painting.

### The Blind Spot: When Lighthouse Lies

The basic table scores a **perfect 100** on Lighthouse. Zero TBT. Fast LCP. Lighthouse sees a simple page that renders quickly with no JavaScript overhead.

But during page load, trace analysis tells a different story. All three approaches were recorded as **load-only traces** (no user scrolling), yet they behave very differently:

| Metric | Basic | PrimeVue | TanStack | Source |
|--------|-------|----------|----------|--------|
| Lighthouse score | 100 | 99 | 99 | Lighthouse |
| DOM elements | 80,038 | 495 | 327 | Lighthouse |
| TBT | 0 ms | 73 ms | 0 ms | Lighthouse |
| Scripting (ms/s) | 108 | 633 | 122 | Trace (load) |
| Long tasks | 2 | 9 | 5 | Trace (load) |
| Longest task | 131 ms | 1,017 ms | 323 ms | Trace (load) |
| rAF callbacks | 0 | 180 (678 ms) | 264 (61 ms) | Trace (load) |

### The rAF Gap: What "FPS" Really Means During Load

The raw frame counts differ dramatically: basic commits 4 frames during load, while PrimeVue commits 183 and TanStack commits 268. This looks like a performance difference, but it's an **architectural difference**.

A plain `v-for` renders 80,000 DOM nodes synchronously in a single pass — no `requestAnimationFrame`, no frame loop. The browser commits a few paint frames and is done. The 80K nodes sit in the DOM, waiting to punish the first scroll event.

Virtual scroll components (PrimeVue and TanStack) use rAF loops during initialization to measure row heights, calculate the visible viewport, and render only the visible slice. This produces hundreds of frame commits before the user touches anything — not because they're "faster," but because their architecture requires frame-by-frame measurement.

The real insight is the **cost per rAF callback**: PrimeVue spends 678ms across 180 callbacks (3.78ms/callback), while TanStack spends 61ms across 264 callbacks (0.23ms/callback) — an **11× difference** in initialization overhead. PrimeVue's virtual scroll does more work per frame because the component manages sorting, selection, keyboard navigation, and accessibility state. TanStack's headless approach defers all of that to userland.

### The Trade-off Triangle

Each approach occupies a different position in the trade-off space:

**Basic Table** optimizes for simplicity and initial load. No library overhead, no virtual scroll complexity, minimal JavaScript during page load (108 ms/s scripting). The cost is invisible until the user scrolls — then the browser pays for every DOM node on every frame. This is the "it works on my MacBook Pro" trap: powerful hardware masks the problem that 4× CPU throttling reveals.

**PrimeVue DataTable** trades scripting cost for DOM size. Virtual scroll keeps the DOM small (~500 nodes), but the component library adds significant JavaScript weight: 633 ms/s scripting during load, with a single long task exceeding 1 second. The library does a lot — sortable columns, selection, keyboard navigation — and you pay for features whether you use them or not.

**TanStack Table** takes the headless approach: logic without rendering opinions. It achieves the smallest DOM (327 elements), low scripting cost (122 ms/s), and the cheapest rAF callbacks (0.23ms each). The trade-off is integration complexity — you wire up your own templates, manage your own styling, and compose virtual scrolling yourself. It's more code to write, but less code to ship.

### Which Metrics Actually Matter?

Not all metrics are equally useful for table-rendering benchmarks. The scripts extract everything, but here's what drives decisions:

**Primary metrics** (the ones that change your architecture):
- **DOM Size** — the single strongest predictor of runtime performance for large datasets. Once you cross ~3,000 elements, style recalculation and layout become the bottleneck, not JavaScript.
- **TBT** (Total Blocking Time) — measures main-thread blockage during load. High TBT means the page appears loaded but ignores user input.
- **Longest task** — a single 1,000ms task means the UI freezes for a full second. Users notice at 100ms.
- **Scripting ms/s** — how much JavaScript work per second of trace. Directly comparable across load-only traces regardless of rAF usage.

**Secondary metrics** (useful for fine-tuning, less decisive):
- **rAF callback cost** — reveals virtual scroll initialization overhead. Comparable between approaches that use rAF (PrimeVue vs TanStack), but meaningless for approaches that don't (Basic).
- **LCP** — important for content-heavy pages, but all three approaches load fast enough that LCP isn't the differentiator here.
- **CLS** — not meaningful for these benchmarks since the table layout is stable once rendered.

**Metrics that require matched traces** (not valid from load-only recordings):
- **FPS** — only meaningful when all traces include the same user interaction (e.g., scrolling). The script detects this and flags FPS as non-comparable when interaction patterns differ.

## Techniques: How the Scripts Work

### Lighthouse Analysis (`analyze_lighthouse.py`)

Parses Lighthouse JSON reports and extracts `numericValue` from each audit. Key techniques:

**Dual-format handling** — Lighthouse 12 (CLI) uses the audit key `dom-size`; Lighthouse 13 (DevTools export) renamed it to `dom-size-insight`. The script tries both keys, making it safe to mix reports from different capture methods.

**NO_LCP graceful degradation** — When a page has so many DOM nodes that Chrome can't determine the Largest Contentful Paint (the basic table sometimes triggers this under heavy throttling), the audit returns an `errorMessage` instead of `numericValue`. The script returns `None` and propagates it through formatting and insights without crashing.

**Threshold-based status** — Each metric is compared against Core Web Vitals thresholds (source: web.dev/vitals). Values are classified as `pass`, `warn`, or `FAIL` — this makes the markdown output scannable at a glance.

### Trace Analysis (`analyze_trace.py`)

Parses Chrome DevTools Performance trace JSON — arrays of timestamped events with phase (`ph`), name, process/thread IDs, and duration.

**Main thread isolation** — Chrome traces contain events from multiple processes (browser, GPU, renderer) and threads (main, compositor, workers). The script filters to `CrRendererMain` threads only, because that's where JavaScript execution and DOM manipulation happen. Events on other threads (compositor, workers) would dilute the signal.

**Category mapping** — Each trace event name is mapped to a DevTools Summary category (Scripting, Rendering, Painting) using the same classification Chrome DevTools uses internally. `FunctionCall` and `EvaluateScript` → Scripting; `Layout` and `RecalculateStyles` → Rendering; `Paint` and `CompositeLayers` → Painting. Unmapped events are ignored to avoid counting infrastructure noise.

**Profiler artifact filtering** — When DevTools starts profiling, it emits a `CpuProfiler::StartProfiling` event inside a `RunTask`. This task often exceeds 50ms (the long-task threshold) purely from profiling overhead. The script detects and excludes these artifacts so they don't inflate long-task counts — otherwise you'd be measuring the measurement tool.

**Duration normalization** — When comparing traces of different lengths (e.g., one 5s recording vs one 10s recording), raw counts (long tasks, frame commits) are misleading. The script normalizes count-based and total-based metrics to the shortest trace duration. Rate metrics (ms/s, fps) are mathematically unaffected by duration, so they're left as-is.

**Interaction detection** — The script classifies each trace as "load only", "load + interaction", or "load + scroll" by scanning `EventDispatch` events for user-initiated types (scroll, mousedown, keydown, etc.) vs page lifecycle types (load, DOMContentLoaded). This classification gates FPS comparisons: the script refuses to compare FPS across traces with different interaction patterns and explains why, preventing misleading conclusions from architecturally different frame behaviors (rAF-driven virtual scroll init vs static render).

**FPS estimation** — Estimated from `Commit` event counts divided by trace duration. This undercounts compared to the compositor's actual frame output (some frames are produced without a main-thread commit), but it correctly captures *main-thread-driven* frames, which is the bottleneck we're measuring. The FPS value is annotated with context: "(rAF-driven, no user interaction)" or "(initial render only — no rAF, no interaction)" so the number is never presented without its meaning.

## Setup

Install [uv](https://docs.astral.sh/uv/) (one-time), then create the Python environment:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
pnpm setup:python
```

This creates a venv at `scripts/analyze/.venv/` with all dependencies.

## Important: Use a Production Build

**Do not benchmark against `pnpm dev`.** Vite's dev server adds HMR overhead, unoptimized modules, and source maps that inflate TBT, LCP, DOM Size, scripting time, and long tasks. The scripts warn if they detect a `:5173` URL in the report.

Always benchmark against a production build:

```bash
pnpm build && pnpm preview
```

This serves the optimized build on `http://localhost:4173`.

## Lighthouse Analysis

### Capture Reports

```bash
pnpm lighthouse:all
```

Or individually: `pnpm lighthouse:basic`, `pnpm lighthouse:primevue`, `pnpm lighthouse:tanstack`.

Reports are saved to `scripts/analyze/reports/`.

### Capture Parameters

Every `pnpm lighthouse:*` script uses four flags that must stay in sync. See `benchmark-config.json` for the rationale behind each.

| Flag | Value | Why |
|------|-------|-----|
| `--preset=desktop` | desktop | 1350×940 viewport, no mobile emulation, no network throttling — matches a real browser viewing a data table |
| `--chrome-flags='--incognito'` | `--incognito` | Disables all Chrome extensions (analytics, ad-blockers, devtools panels) that would inflate scripting time and skew TBT |
| `--throttling.cpuSlowdownMultiplier=4` | `4` | Simulates a mid-tier device; desktop preset defaults to 1× (no throttle) — explicit 4× makes results comparable across machines and blog posts |
| `--only-categories=performance` | performance | Skips accessibility, best-practices, and SEO audits — cuts run time ~60% and avoids false failures from benchmark pages |

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
3. **Save profile** > save to `scripts/analyze/traces/` (e.g., `Trace-basic.json`)

> Record with **CPU 4× slowdown** (Performance tab > gear icon) and use an **Incognito** window to match Lighthouse capture conditions.

### Compare Traces

```bash
scripts/analyze/.venv/bin/python scripts/analyze/analyze_trace.py \
  scripts/analyze/traces/Trace-basic.json \
  scripts/analyze/traces/Trace-tanstack.json \
  -o scripts/analyze/traces/trace-comparison.png
```

Supports the same `--json`, `--json-out`, `--metrics`, `--names` flags as the Lighthouse script.

## Tests

```bash
pnpm test:python:fast   # all tests (~2s)
pnpm test:python        # includes slow tests if trace files exist
```

70 tests covering metric extraction, threshold classification, edge cases (NO_LCP, missing audits, profiler artifacts), duration normalization, insight generation, and integration against real report/trace files. The integration tests act as format-drift detectors — they break when Chrome or Lighthouse changes their JSON structure.

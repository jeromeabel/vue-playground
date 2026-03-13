# Plan 3: Virtual Table + Performance Benchmark

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build three benchmark pages comparing table rendering approaches (basic v-for, PrimeVue DataTable, TanStack Table + Virtual) with a shared MetricsPanel and Python analysis scripts for generating performance comparison graphs.

**Architecture:** Each benchmark page loads the same 3000-item local JSON dataset and renders it in a table. A shared `MetricsPanel` composable measures DOM node count, mount time, and FPS. Python scripts parse Lighthouse JSON and Chrome traces to produce comparison charts.

**Tech Stack:** @tanstack/vue-table, @tanstack/vue-virtual, PrimeVue (isolated to one route), matplotlib, seaborn

**Spec:** `docs/superpowers/specs/2026-03-13-vue-playground-reset-design.md` — see "Feature 2: Virtualization Benchmark"

**Prerequisite:** Plan 2 (Minimal Setup) must be completed first. The app should be running with `pnpm dev`, `public/data/species-3000.json` should exist.

---

## Chunk 1: Metrics Composable + Basic Table

### Task 1: DOM Metrics Composable

**Files:**
- Create: `src/composables/useDomMetrics.ts`
- Create: `src/composables/__tests__/useDomMetrics.test.ts`

- [ ] **Step 1: Write the test**

```typescript
// src/composables/__tests__/useDomMetrics.test.ts
import { describe, it, expect, vi } from 'vitest'
import { useDomMetrics } from '../useDomMetrics'

describe('useDomMetrics', () => {
  it('measures mount time', () => {
    const { mountTimeMs, markBeforeMount, markAfterMount } = useDomMetrics()

    vi.spyOn(performance, 'now')
      .mockReturnValueOnce(100)
      .mockReturnValueOnce(115)

    markBeforeMount()
    markAfterMount()

    expect(mountTimeMs.value).toBe(15)
  })

  it('counts DOM nodes', () => {
    const container = document.createElement('div')
    const span1 = document.createElement('span')
    const span2 = document.createElement('span')
    container.appendChild(span1)
    container.appendChild(span2)
    document.body.appendChild(container)

    const { domNodeCount, startObserving } = useDomMetrics()
    startObserving(container)

    // 2 span elements inside the container
    expect(domNodeCount.value).toBe(2)

    document.body.removeChild(container)
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pnpm test:run src/composables/__tests__/useDomMetrics.test.ts`
Expected: FAIL — module not found

- [ ] **Step 3: Implement useDomMetrics**

```typescript
// src/composables/useDomMetrics.ts
import { onUnmounted, ref } from 'vue'

export function useDomMetrics() {
  const mountTimeMs = ref(0)
  const domNodeCount = ref(0)
  const fps = ref(0)

  let t0 = 0
  let observer: MutationObserver | null = null
  let rafId = 0
  let frameCount = 0
  let lastFpsTime = 0

  function markBeforeMount() {
    t0 = performance.now()
  }

  function markAfterMount() {
    mountTimeMs.value = Math.round(performance.now() - t0)
  }

  function countNodes(root: Element): number {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT)
    let count = 0
    while (walker.nextNode()) count++
    return count
  }

  function startObserving(container: HTMLElement) {
    domNodeCount.value = countNodes(container)

    observer = new MutationObserver(() => {
      domNodeCount.value = countNodes(container)
    })
    observer.observe(container, { childList: true, subtree: true })
  }

  function startFpsCounter() {
    lastFpsTime = performance.now()
    frameCount = 0

    function tick() {
      frameCount++
      const now = performance.now()
      const elapsed = now - lastFpsTime
      if (elapsed >= 1000) {
        fps.value = Math.round((frameCount * 1000) / elapsed)
        frameCount = 0
        lastFpsTime = now
      }
      rafId = requestAnimationFrame(tick)
    }
    rafId = requestAnimationFrame(tick)
  }

  function stopFpsCounter() {
    if (rafId) cancelAnimationFrame(rafId)
  }

  onUnmounted(() => {
    observer?.disconnect()
    stopFpsCounter()
  })

  return {
    mountTimeMs,
    domNodeCount,
    fps,
    markBeforeMount,
    markAfterMount,
    startObserving,
    startFpsCounter,
    stopFpsCounter,
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pnpm test:run src/composables/__tests__/useDomMetrics.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/composables/useDomMetrics.ts src/composables/__tests__/useDomMetrics.test.ts
git commit -m "feat: add useDomMetrics composable for benchmark measurements"
```

---

### Task 2: MetricsPanel Component

**Files:**
- Create: `src/components/MetricsPanel.vue`

- [ ] **Step 1: Create MetricsPanel.vue**

```vue
<script setup lang="ts">
defineProps<{
  mountTimeMs: number
  domNodeCount: number
  fps: number
}>()
</script>

<template>
  <div class="mb-4 flex gap-4 rounded-lg bg-surface-dark px-4 py-2 text-sm font-mono">
    <div>
      <span class="text-text-muted">Mount:</span>
      <span class="ml-1 font-semibold">{{ mountTimeMs }}ms</span>
    </div>
    <div>
      <span class="text-text-muted">DOM:</span>
      <span class="ml-1 font-semibold">{{ domNodeCount.toLocaleString() }}</span>
    </div>
    <div>
      <span class="text-text-muted">FPS:</span>
      <span class="ml-1 font-semibold">{{ fps }}</span>
    </div>
  </div>
</template>
```

- [ ] **Step 2: Commit**

```bash
git add src/components/MetricsPanel.vue
git commit -m "feat: add MetricsPanel component for benchmark pages"
```

---

### Task 3: Basic Table Benchmark Page

**Files:**
- Create: `src/pages/benchmark/basic-table.vue`

- [ ] **Step 1: Create the page**

```vue
<script setup lang="ts">
import { onBeforeMount, onMounted, ref, useTemplateRef } from 'vue'
import type { GbifSpeciesSummary } from '@/api/gbif'
import { useDomMetrics } from '@/composables/useDomMetrics'
import MetricsPanel from '@/components/MetricsPanel.vue'

const species = ref<GbifSpeciesSummary[]>([])
const tableContainer = useTemplateRef('tableContainer')

const {
  mountTimeMs,
  domNodeCount,
  fps,
  markBeforeMount,
  markAfterMount,
  startObserving,
  startFpsCounter,
} = useDomMetrics()

onBeforeMount(() => {
  markBeforeMount()
})

onMounted(async () => {
  const res = await fetch('/data/species-3000.json')
  species.value = await res.json()

  requestAnimationFrame(() => {
    markAfterMount()
    if (tableContainer.value) {
      startObserving(tableContainer.value)
    }
    startFpsCounter()
  })
})
</script>

<template>
  <div>
    <RouterLink
      to="/benchmark"
      class="mb-4 inline-block text-sm text-primary hover:underline"
    >
      &larr; Back to benchmarks
    </RouterLink>

    <h1 class="mb-4 text-2xl font-bold">
      Basic Table (v-for)
    </h1>

    <MetricsPanel
      :mount-time-ms="mountTimeMs"
      :dom-node-count="domNodeCount"
      :fps="fps"
    />

    <div
      ref="tableContainer"
      class="max-h-[600px] overflow-auto rounded border border-surface-dark"
    >
      <table class="w-full text-left text-sm">
        <thead class="sticky top-0 bg-white">
          <tr class="border-b border-surface-dark">
            <th class="px-3 py-2">Scientific Name</th>
            <th class="px-3 py-2">Family</th>
            <th class="px-3 py-2">Genus</th>
            <th class="px-3 py-2">Order</th>
            <th class="px-3 py-2">Class</th>
            <th class="px-3 py-2">Status</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="s in species"
            :key="s.key"
            class="border-b border-surface-dark/50"
          >
            <td class="px-3 py-2 italic">{{ s.canonicalName }}</td>
            <td class="px-3 py-2">{{ s.family }}</td>
            <td class="px-3 py-2">{{ s.genus }}</td>
            <td class="px-3 py-2">{{ s.order }}</td>
            <td class="px-3 py-2">{{ s.class }}</td>
            <td class="px-3 py-2">{{ s.taxonomicStatus }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
```

- [ ] **Step 2: Verify in browser**

Run: `pnpm dev`
Navigate to `/benchmark/basic-table`
Expected: 3000 rows render. MetricsPanel shows high DOM count (~18,000+), mount time, and FPS.

- [ ] **Step 3: Commit**

```bash
git add src/pages/benchmark/basic-table.vue
git commit -m "feat: add basic table benchmark page (v-for baseline)"
```

---

## Chunk 2: PrimeVue + TanStack Table Benchmarks

### Task 4: PrimeVue DataTable Benchmark Page

**Files:**
- Create: `src/pages/benchmark/primevue-table.vue`

- [ ] **Step 1: Install PrimeVue**

```bash
pnpm add primevue
```

- [ ] **Step 2: Create the page**

Note: PrimeVue is imported directly in this route only — it is NOT registered globally in `main.ts`.

```vue
<script setup lang="ts">
import { onBeforeMount, onMounted, ref, useTemplateRef } from 'vue'
import type { GbifSpeciesSummary } from '@/api/gbif'
import { useDomMetrics } from '@/composables/useDomMetrics'
import MetricsPanel from '@/components/MetricsPanel.vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'

const species = ref<GbifSpeciesSummary[]>([])
const tableContainer = useTemplateRef('tableContainer')

const {
  mountTimeMs,
  domNodeCount,
  fps,
  markBeforeMount,
  markAfterMount,
  startObserving,
  startFpsCounter,
} = useDomMetrics()

onBeforeMount(() => {
  markBeforeMount()
})

onMounted(async () => {
  const res = await fetch('/data/species-3000.json')
  species.value = await res.json()

  requestAnimationFrame(() => {
    markAfterMount()
    if (tableContainer.value) {
      startObserving(tableContainer.value)
    }
    startFpsCounter()
  })
})
</script>

<template>
  <div>
    <RouterLink
      to="/benchmark"
      class="mb-4 inline-block text-sm text-primary hover:underline"
    >
      &larr; Back to benchmarks
    </RouterLink>

    <h1 class="mb-4 text-2xl font-bold">
      PrimeVue DataTable
    </h1>

    <MetricsPanel
      :mount-time-ms="mountTimeMs"
      :dom-node-count="domNodeCount"
      :fps="fps"
    />

    <div ref="tableContainer">
      <DataTable
        :value="species"
        scrollable
        scroll-height="600px"
        :virtual-scroller-options="{ itemSize: 40 }"
        class="text-sm"
      >
        <Column
          field="canonicalName"
          header="Scientific Name"
        />
        <Column
          field="family"
          header="Family"
        />
        <Column
          field="genus"
          header="Genus"
        />
        <Column
          field="order"
          header="Order"
        />
        <Column
          field="class"
          header="Class"
        />
        <Column
          field="taxonomicStatus"
          header="Status"
        />
      </DataTable>
    </div>
  </div>
</template>
```

- [ ] **Step 3: Verify in browser**

Navigate to `/benchmark/primevue-table`
Expected: PrimeVue DataTable renders with virtual scrolling. DOM count should be lower than basic table.

- [ ] **Step 4: Commit**

```bash
git add src/pages/benchmark/primevue-table.vue package.json pnpm-lock.yaml
git commit -m "feat: add PrimeVue DataTable benchmark page"
```

---

### Task 5: TanStack Table + Virtual Benchmark Page

**Files:**
- Create: `src/pages/benchmark/tanstack-table.vue`

- [ ] **Step 1: Install TanStack Table and Virtual**

```bash
pnpm add @tanstack/vue-table @tanstack/vue-virtual
```

- [ ] **Step 2: Create the page**

```vue
<script setup lang="ts">
import { computed, onBeforeMount, onMounted, ref, useTemplateRef } from 'vue'
import {
  createColumnHelper,
  FlexRender,
  getCoreRowModel,
  useVueTable,
} from '@tanstack/vue-table'
import { useVirtualizer } from '@tanstack/vue-virtual'
import type { GbifSpeciesSummary } from '@/api/gbif'
import { useDomMetrics } from '@/composables/useDomMetrics'
import MetricsPanel from '@/components/MetricsPanel.vue'

const species = ref<GbifSpeciesSummary[]>([])
const tableContainer = useTemplateRef('tableContainer')
const scrollContainer = useTemplateRef('scrollContainer')

const {
  mountTimeMs,
  domNodeCount,
  fps,
  markBeforeMount,
  markAfterMount,
  startObserving,
  startFpsCounter,
} = useDomMetrics()

const columnHelper = createColumnHelper<GbifSpeciesSummary>()

const columns = [
  columnHelper.accessor('canonicalName', { header: 'Scientific Name' }),
  columnHelper.accessor('family', { header: 'Family' }),
  columnHelper.accessor('genus', { header: 'Genus' }),
  columnHelper.accessor('order', { header: 'Order' }),
  columnHelper.accessor('class', { header: 'Class' }),
  columnHelper.accessor('taxonomicStatus', { header: 'Status' }),
]

const table = useVueTable({
  get data() { return species.value },
  columns,
  getCoreRowModel: getCoreRowModel(),
})

const rows = computed(() => table.getRowModel().rows)

const virtualizerOptions = computed(() => ({
  count: rows.value.length,
  estimateSize: () => 40,
  getScrollElement: () => scrollContainer.value ?? null,
  overscan: 20,
}))

const virtualizer = useVirtualizer(virtualizerOptions)
const virtualRows = computed(() => virtualizer.value.getVirtualItems())
const totalSize = computed(() => virtualizer.value.getTotalSize())

onBeforeMount(() => {
  markBeforeMount()
})

onMounted(async () => {
  const res = await fetch('/data/species-3000.json')
  species.value = await res.json()

  requestAnimationFrame(() => {
    markAfterMount()
    if (tableContainer.value) {
      startObserving(tableContainer.value)
    }
    startFpsCounter()
  })
})
</script>

<template>
  <div>
    <RouterLink
      to="/benchmark"
      class="mb-4 inline-block text-sm text-primary hover:underline"
    >
      &larr; Back to benchmarks
    </RouterLink>

    <h1 class="mb-4 text-2xl font-bold">
      TanStack Table + Virtual
    </h1>

    <MetricsPanel
      :mount-time-ms="mountTimeMs"
      :dom-node-count="domNodeCount"
      :fps="fps"
    />

    <div ref="tableContainer">
      <div
        ref="scrollContainer"
        class="max-h-[600px] overflow-auto rounded border border-surface-dark"
      >
        <table class="w-full text-left text-sm">
          <thead class="sticky top-0 bg-white">
            <tr
              v-for="headerGroup in table.getHeaderGroups()"
              :key="headerGroup.id"
              class="border-b border-surface-dark"
            >
              <th
                v-for="header in headerGroup.headers"
                :key="header.id"
                class="px-3 py-2"
              >
                <FlexRender
                  :render="header.column.columnDef.header"
                  :props="header.getContext()"
                />
              </th>
            </tr>
          </thead>
          <tbody>
            <tr :style="{ height: `${totalSize}px`, position: 'relative' }">
              <td
                colspan="100%"
                class="p-0"
              >
                <div
                  v-for="virtualRow in virtualRows"
                  :key="virtualRow.index"
                  :style="{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '100%',
                    height: `${virtualRow.size}px`,
                    transform: `translateY(${virtualRow.start}px)`,
                    display: 'flex',
                  }"
                  class="border-b border-surface-dark/50"
                >
                  <div
                    v-for="cell in rows[virtualRow.index]?.getVisibleCells()"
                    :key="cell.id"
                    class="flex-1 px-3 py-2"
                  >
                    <FlexRender
                      :render="cell.column.columnDef.cell"
                      :props="cell.getContext()"
                    />
                  </div>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 3: Verify in browser**

Navigate to `/benchmark/tanstack-table`
Expected: Virtual scrolling renders only ~20-40 visible rows. DOM count should be dramatically lower than basic table.

- [ ] **Step 4: Commit**

```bash
git add src/pages/benchmark/tanstack-table.vue package.json pnpm-lock.yaml
git commit -m "feat: add TanStack Table + Virtual benchmark page"
```

---

## Chunk 3: Python Analysis Scripts

### Task 6: Python Requirements and Lighthouse Analyzer

**Files:**
- Create: `scripts/analyze/requirements.txt`
- Create: `scripts/analyze/analyze_lighthouse.py`

- [ ] **Step 1: Create requirements.txt**

```text
matplotlib>=3.8
seaborn>=0.13
json5>=0.9
```

- [ ] **Step 2: Create analyze_lighthouse.py**

This script reads Lighthouse JSON reports (exported from Chrome DevTools or Lighthouse CLI) and generates comparison bar charts.

```python
#!/usr/bin/env python3
"""
Compare Lighthouse reports across benchmark approaches.

Usage:
    python analyze_lighthouse.py basic.json primevue.json tanstack.json -o comparison.png

Each JSON is a Lighthouse report exported via:
    lighthouse http://localhost:5173/benchmark/basic-table --output json --output-path basic.json
"""
import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns


def extract_metrics(report: dict) -> dict:
    audits = report.get("audits", {})
    return {
        "Performance Score": report.get("categories", {})
        .get("performance", {})
        .get("score", 0)
        * 100,
        "TBT (ms)": audits.get("total-blocking-time", {}).get("numericValue", 0),
        "FCP (ms)": audits.get("first-contentful-paint", {}).get("numericValue", 0),
        "LCP (ms)": audits.get("largest-contentful-paint", {}).get("numericValue", 0),
        "CLS": audits.get("cumulative-layout-shift", {}).get("numericValue", 0),
        "DOM Size": audits.get("dom-size", {}).get("numericValue", 0),
    }


def main():
    parser = argparse.ArgumentParser(description="Compare Lighthouse reports")
    parser.add_argument("reports", nargs="+", help="Lighthouse JSON files")
    parser.add_argument("-o", "--output", default="lighthouse-comparison.png")
    args = parser.parse_args()

    data = {}
    for path_str in args.reports:
        name = Path(path_str).stem
        with open(path_str) as f:
            report = json.load(f)
        data[name] = extract_metrics(report)

    metrics = list(next(iter(data.values())).keys())

    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    flat_axes = axes.flatten()

    for i, metric in enumerate(metrics):
        ax = flat_axes[i]
        names = list(data.keys())
        values = [data[n][metric] for n in names]
        colors = sns.color_palette("muted", len(names))
        ax.bar(names, values, color=colors)
        ax.set_title(metric, fontsize=11, fontweight="bold")
        ax.tick_params(axis="x", rotation=15)
        for j, v in enumerate(values):
            ax.text(j, v, f"{v:.0f}", ha="center", va="bottom", fontsize=9)

    plt.suptitle("Lighthouse Benchmark Comparison", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(args.output, dpi=150, bbox_inches="tight")
    print(f"Saved to {args.output}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Commit**

```bash
mkdir -p scripts/analyze
git add scripts/analyze/requirements.txt scripts/analyze/analyze_lighthouse.py
git commit -m "feat: add Lighthouse comparison chart script"
```

---

### Task 7: Chrome Trace Analyzer

**Files:**
- Create: `scripts/analyze/analyze_trace.py`

- [ ] **Step 1: Create analyze_trace.py**

```python
#!/usr/bin/env python3
"""
Analyze Chrome Performance trace JSON files.

Usage:
    python analyze_trace.py trace-basic.json trace-tanstack.json -o trace-comparison.png

Export traces from Chrome DevTools: Performance tab > Save Profile.
"""
import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns


CATEGORY_MAP = {
    "Scripting": [
        "EvaluateScript",
        "v8.compile",
        "FunctionCall",
        "EventDispatch",
        "TimerFire",
        "FireAnimationFrame",
    ],
    "Rendering": [
        "UpdateLayoutTree",
        "Layout",
        "RecalculateStyles",
        "HitTest",
    ],
    "Painting": [
        "Paint",
        "CompositeLayers",
        "RasterTask",
        "Decode Image",
    ],
}


def categorize(name: str) -> str:
    for cat, names in CATEGORY_MAP.items():
        if name in names:
            return cat
    return "Other"


def analyze_trace(trace_path: str) -> dict:
    with open(trace_path) as f:
        data = json.load(f)

    events = data if isinstance(data, list) else data.get("traceEvents", [])

    totals: dict[str, float] = {
        "Scripting": 0, "Rendering": 0, "Painting": 0, "Other": 0,
    }
    trace_start = float("inf")
    trace_end = 0.0
    long_tasks = 0

    for ev in events:
        if ev.get("ph") != "X":
            continue
        dur = ev.get("dur", 0) / 1000  # microseconds to ms
        ts = ev.get("ts", 0) / 1000
        name = ev.get("name", "")

        trace_start = min(trace_start, ts)
        trace_end = max(trace_end, ts + dur)

        cat = categorize(name)
        totals[cat] += dur

        if dur > 50:
            long_tasks += 1

    duration_s = (trace_end - trace_start) / 1000
    safe_dur = max(duration_s, 0.01)
    return {
        "duration_s": round(duration_s, 2),
        "scripting_ms_per_s": round(totals["Scripting"] / safe_dur, 1),
        "rendering_ms_per_s": round(totals["Rendering"] / safe_dur, 1),
        "painting_ms_per_s": round(totals["Painting"] / safe_dur, 1),
        "long_tasks": long_tasks,
        "long_tasks_per_s": round(long_tasks / safe_dur, 2),
    }


def main():
    parser = argparse.ArgumentParser(description="Analyze Chrome traces")
    parser.add_argument("traces", nargs="+", help="Chrome trace JSON files")
    parser.add_argument("-o", "--output", default="trace-comparison.png")
    args = parser.parse_args()

    data = {}
    for path_str in args.traces:
        name = Path(path_str).stem
        data[name] = analyze_trace(path_str)
        print(f"\n{name}:")
        for k, v in data[name].items():
            print(f"  {k}: {v}")

    metrics = [
        "scripting_ms_per_s", "rendering_ms_per_s",
        "painting_ms_per_s", "long_tasks_per_s",
    ]
    labels = [
        "Scripting (ms/s)", "Rendering (ms/s)",
        "Painting (ms/s)", "Long Tasks (/s)",
    ]

    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, len(metrics), figsize=(14, 5))

    for i, (metric, label) in enumerate(zip(metrics, labels)):
        ax = axes[i]
        names = list(data.keys())
        values = [data[n][metric] for n in names]
        colors = sns.color_palette("muted", len(names))
        ax.bar(names, values, color=colors)
        ax.set_title(label, fontsize=11, fontweight="bold")
        ax.tick_params(axis="x", rotation=15)
        for j, v in enumerate(values):
            ax.text(j, v, f"{v:.1f}", ha="center", va="bottom", fontsize=9)

    plt.suptitle(
        "Chrome Trace Comparison (per-second normalized)",
        fontsize=14, fontweight="bold",
    )
    plt.tight_layout()
    plt.savefig(args.output, dpi=150, bbox_inches="tight")
    print(f"\nSaved to {args.output}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
git add scripts/analyze/analyze_trace.py
git commit -m "feat: add Chrome trace analysis script"
```

---

### Task 8: Verify All Benchmark Pages

- [ ] **Step 1: Run dev server and test all 3 benchmark pages**

Run: `pnpm dev`

Navigate to each page and note the MetricsPanel values:

| Page | Expected DOM Count | Expected Behavior |
|------|-------------------|-------------------|
| `/benchmark/basic-table` | ~18,000+ | All 3000 rows in DOM, slow initial render |
| `/benchmark/primevue-table` | Lower | PrimeVue virtual scroll renders fewer rows |
| `/benchmark/tanstack-table` | Lowest (~500-1000) | Only ~20-40 visible rows in DOM |

- [ ] **Step 2: Run lint**

Run: `pnpm lint`
Expected: No errors

- [ ] **Step 3: Run tests**

Run: `pnpm test:run`
Expected: useDomMetrics tests pass

- [ ] **Step 4: Build**

Run: `pnpm build`
Expected: Builds successfully. PrimeVue should be in a separate chunk (verify with `ls -la dist/assets/`)

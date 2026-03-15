<script setup lang="ts">
import { computed } from "vue";
import BenchmarkTable from "../components/benchmark-table.vue";
import TraceTable from "../components/trace-table.vue";
import { useBenchmarkResults } from "../composables/use-benchmark-results";
import { useTraceResults } from "../composables/use-trace-results";

const { data, isPending, isError } = useBenchmarkResults();
const { data: traceData, isPending: traceIsPending, isError: traceIsError } = useTraceResults();

function formatRunInfo(config: { iterations: number; aggregation: string }): string {
    if (config.iterations > 1) return `${config.iterations} runs · ${config.aggregation}`;
    return "single run";
}

const lighthouseSubtitle = computed(() => {
    const preset = data.value?.config.preset ?? "desktop";
    const runs = data.value ? formatRunInfo(data.value.config) : "";
    return [
        `Lighthouse ${preset} preset`,
        runs,
        "Chrome Incognito",
        "10,000 species dataset",
    ].filter(Boolean).join(" · ");
});

const traceSubtitle = computed(() => {
    const runs = traceData.value ? formatRunInfo(traceData.value.config) : "";
    return [
        "Chrome DevTools Performance trace",
        "CPU 4× slowdown",
        "Incognito",
        runs,
        "10,000 species dataset",
    ].filter(Boolean).join(" · ");
});
</script>

<template>
  <div>
    <h1 class="mb-4 text-2xl font-bold">
      Benchmark
    </h1>
    <p class="mb-6 text-text-muted">
      Compare table rendering approaches with 10,000 botanical species.
    </p>
    <div class="grid gap-4 sm:grid-cols-3">
      <RouterLink
        to="/benchmark/basic-table"
        class="rounded-lg border border-surface-dark p-6 hover:border-primary hover:shadow-sm"
      >
        <h2 class="mb-1 font-semibold">
          Basic Table
        </h2>
        <p class="text-sm text-text-muted">
          Plain v-for — the baseline.
        </p>
      </RouterLink>
      <RouterLink
        to="/benchmark/primevue-table"
        class="rounded-lg border border-surface-dark p-6 hover:border-primary hover:shadow-sm"
      >
        <h2 class="mb-1 font-semibold">
          PrimeVue DataTable
        </h2>
        <p class="text-sm text-text-muted">
          Component library with virtual scroll.
        </p>
      </RouterLink>
      <RouterLink
        to="/benchmark/tanstack-table"
        class="rounded-lg border border-surface-dark p-6 hover:border-primary hover:shadow-sm"
      >
        <h2 class="mb-1 font-semibold">
          TanStack Table
        </h2>
        <p class="text-sm text-text-muted">
          Headless table + virtual scrolling.
        </p>
      </RouterLink>
    </div>

    <section class="mt-10">
      <h2 class="mb-1 text-xl font-bold">
        Benchmark Results
      </h2>
      <p class="mb-4 text-sm text-text-muted">
        {{ lighthouseSubtitle }}
      </p>

      <template v-if="isPending">
        <p class="text-sm text-text-muted">
          Loading benchmark results...
        </p>
      </template>
      <template v-else-if="isError">
        <p class="text-sm text-text-muted">
          No benchmark data found. Run <code class="rounded bg-surface-dark/30 px-1">pnpm analyze:lighthouse:json</code> to generate results.
        </p>
      </template>
      <template v-else-if="data">
        <BenchmarkTable :results="data" />
        <p class="mt-2 text-xs text-text-muted">
          Generated {{ new Date(data.generatedAt).toLocaleDateString() }}.
          Re-run <code class="rounded bg-surface-dark/30 px-1">pnpm lighthouse:all && pnpm analyze:lighthouse:json</code> to update.
        </p>
      </template>
    </section>

    <section class="mt-10">
      <h2 class="mb-1 text-xl font-bold">
        Runtime Trace Results
      </h2>
      <p class="mb-4 text-sm text-text-muted">
        {{ traceSubtitle }}
      </p>

      <template v-if="traceIsPending">
        <p class="text-sm text-text-muted">
          Loading trace results...
        </p>
      </template>
      <template v-else-if="traceIsError">
        <p class="text-sm text-text-muted">
          No trace data found. Run <code class="rounded bg-surface-dark/30 px-1">pnpm analyze:trace:json</code> to generate results.
        </p>
      </template>
      <template v-else-if="traceData">
        <TraceTable :results="traceData" />
        <p class="mt-2 text-xs text-text-muted">
          Generated {{ new Date(traceData.generatedAt).toLocaleDateString() }}.
          Re-run <code class="rounded bg-surface-dark/30 px-1">pnpm analyze:trace:json</code> to update.
        </p>
      </template>
    </section>
  </div>
</template>

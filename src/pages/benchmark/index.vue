<script setup lang="ts">
import BenchmarkTable from "@/components/benchmark-table.vue";
import { useBenchmarkResults } from "@/composables/use-benchmark-results";

const { data, isPending, isError } = useBenchmarkResults();
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
        Lighthouse desktop preset · 5 runs · median · Chrome Incognito · 10,000 species dataset
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
  </div>
</template>

<script setup lang="ts">
import { onBeforeMount, onMounted, ref, useTemplateRef } from "vue";

import type { GbifSpeciesSummary } from "@/api/gbif";
import MetricsPanel from "@/components/metrics-panel.vue";
import { useDomMetrics } from "@/composables/use-dom-metrics";

type BenchmarkedSpecies = GbifSpeciesSummary & { benchmarkOrder: number };

const species = ref<BenchmarkedSpecies[]>([]);
const tableContainer = useTemplateRef("tableContainer");

const {
    mountTimeMs,
    domNodeCount,
    fps,
    markBeforeMount,
    markAfterMount,
    startObserving,
    startFpsCounter,
} = useDomMetrics();

onBeforeMount(() => {
    markBeforeMount();
});

onMounted(async () => {
    const res = await fetch("/data/species-3000.json");
    const data = await res.json() as GbifSpeciesSummary[];
    species.value = data.map((item, index) => ({
        ...item,
        benchmarkOrder: index + 1,
    }));

    requestAnimationFrame(() => {
        markAfterMount();
        if (tableContainer.value) {
            startObserving(tableContainer.value);
        }
        startFpsCounter();
    });
});
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
      class="relative isolate max-h-[600px] overflow-auto rounded border border-surface-dark"
    >
      <table class="w-full text-left text-sm">
        <thead class="sticky top-0 z-20 bg-sand-50">
          <tr class="border-b border-surface-dark">
            <th class="px-3 py-2">
              ID
            </th>
            <th class="px-3 py-2">
              Scientific Name
            </th>
            <th class="px-3 py-2">
              Family
            </th>
            <th class="px-3 py-2">
              Genus
            </th>
            <th class="px-3 py-2">
              Order
            </th>
            <th class="px-3 py-2">
              Class
            </th>
            <th class="px-3 py-2">
              Status
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="s in species"
            :key="s.key"
            class="border-b border-surface-dark/50"
          >
            <td class="px-3 py-2 font-mono text-text-muted">
              {{ s.benchmarkOrder }}
            </td>
            <td class="px-3 py-2 italic">
              {{ s.canonicalName }}
            </td>
            <td class="px-3 py-2">
              {{ s.family }}
            </td>
            <td class="px-3 py-2">
              {{ s.genus }}
            </td>
            <td class="px-3 py-2">
              {{ s.order }}
            </td>
            <td class="px-3 py-2">
              {{ s.class }}
            </td>
            <td class="px-3 py-2">
              {{ s.taxonomicStatus }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

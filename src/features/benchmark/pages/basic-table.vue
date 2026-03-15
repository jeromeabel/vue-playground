<script setup lang="ts">
import { computed, onBeforeMount, onMounted, ref, useTemplateRef } from "vue";

import { refDebounced } from "@vueuse/core";
import type { GbifSpeciesSummary } from "@/features/species/types";
import MetricsPanel from "../components/metrics-panel.vue";
import { useDomMetrics } from "../composables/use-dom-metrics";
import type { BenchmarkedSpecies } from "../types";

const species = ref<BenchmarkedSpecies[]>([]);
const tableContainer = useTemplateRef("tableContainer");
const searchInput = ref("");
const query = refDebounced(searchInput, 300);

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
    const res = await fetch("/data/species-10000.json");
    const data = await res.json() as GbifSpeciesSummary[];
    species.value = data.map((item, index) => ({
        ...item,
        benchmarkOrder: index + 1,
        vernacularNames: item.vernacularNames ?? [],
    }));

    requestAnimationFrame(() => {
        markAfterMount();
        if (tableContainer.value) {
            startObserving(tableContainer.value);
        }
        startFpsCounter();
    });
});

const filteredSpecies = computed(() => {
    if (!query.value) return species.value;
    const q = query.value.toLowerCase();
    return species.value.filter(s =>
        s.canonicalName.toLowerCase().includes(q)
        || s.family.toLowerCase().includes(q)
        || s.genus.toLowerCase().includes(q)
        || s.vernacularNames.some(v => v.vernacularName.toLowerCase().includes(q)),
    );
});

function matchedVernaculars(s: BenchmarkedSpecies) {
    if (!query.value) return [];
    const q = query.value.toLowerCase();
    return s.vernacularNames.filter(v => v.vernacularName.toLowerCase().includes(q));
}

function highlight(text: string): string {
    if (!query.value) return text;
    const q = query.value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    return text.replace(new RegExp(`(${q})`, "gi"), "<mark>$1</mark>");
}
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

    <div class="mb-3 flex items-center gap-3">
      <input
        v-model="searchInput"
        type="search"
        placeholder="Search name, family, genus, common name…"
        class="w-full max-w-md rounded border border-surface-dark bg-white px-3 py-1.5 text-sm outline-none focus:border-primary"
      >
      <span class="text-sm text-text-muted">
        {{ filteredSpecies.length.toLocaleString() }} / {{ species.length.toLocaleString() }}
      </span>
    </div>

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
          <template
            v-for="s in filteredSpecies"
            :key="s.key"
          >
            <tr class="border-b border-surface-dark/50">
              <td class="px-3 py-2 font-mono text-text-muted">
                {{ s.benchmarkOrder }}
              </td>
              <td
                class="px-3 py-2 italic"
                v-html="highlight(s.canonicalName)"
              />
              <td
                class="px-3 py-2"
                v-html="highlight(s.family)"
              />
              <td
                class="px-3 py-2"
                v-html="highlight(s.genus)"
              />
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
            <tr
              v-for="v in matchedVernaculars(s)"
              :key="`${s.key}-${v.vernacularName}`"
              class="border-b border-surface-dark/30 bg-surface-50"
            >
              <td
                colspan="7"
                class="px-8 py-1 text-sm text-text-muted"
              >
                <span v-html="highlight(v.vernacularName)" />
                <span class="ml-1 text-xs opacity-60">({{ v.language }})</span>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
:deep(mark) {
  background: oklch(94% 0.12 100);
  border-radius: 2px;
  padding: 0 1px;
}
</style>

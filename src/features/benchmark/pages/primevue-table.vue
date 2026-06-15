<script setup lang="ts">
import { computed, onBeforeMount, onMounted, ref, useTemplateRef, watch } from "vue";
import DataTable from "primevue/datatable";
import Column from "primevue/column";

import { refDebounced } from "@vueuse/core";
import type { GbifSpeciesSummary } from "@/features/species/types";
import MetricsPanel from "../components/metrics-panel.vue";
import { useDomMetrics } from "../composables/use-dom-metrics";
import type { BenchmarkedSpecies } from "../types";

const species = ref<BenchmarkedSpecies[]>([]);
const tableContainer = useTemplateRef("tableContainer");
const searchInput = ref("");
const query = refDebounced(searchInput, 300);
const virtualScrollEnabled = ref(true);
const expandedRows = ref<BenchmarkedSpecies[]>([]);

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
    return text.replace(
        new RegExp(`(${q})`, "gi"),
        "<mark class=\"rounded-[2px] bg-[oklch(94%_0.12_100)] px-px\">$1</mark>",
    );
}

// Auto-expand rows whose vernacular names match the search
watch([filteredSpecies, query], () => {
    if (!query.value) {
        expandedRows.value = [];
        return;
    }
    const q = query.value.toLowerCase();
    expandedRows.value = filteredSpecies.value.filter(s =>
        s.vernacularNames.some(v => v.vernacularName.toLowerCase().includes(q)),
    );
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
      PrimeVue DataTable
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
      <label class="flex cursor-pointer items-center gap-1.5 text-sm">
        <input
          v-model="virtualScrollEnabled"
          type="checkbox"
          class="accent-primary"
        >
        Virtual scroll
      </label>
    </div>

    <div
      ref="tableContainer"
      class="overflow-hidden rounded border border-surface-dark"
    >
      <DataTable
        v-model:expanded-rows="expandedRows"
        :value="filteredSpecies"
        scrollable
        scroll-height="600px"
        :virtual-scroller-options="virtualScrollEnabled ? { itemSize: 40 } : undefined"
        class="text-sm"
      >
        <Column
          expander
          style="width: 3rem"
        />
        <Column
          field="benchmarkOrder"
          header="ID"
          style="width: 72px"
        >
          <template #body="slotProps">
            <span class="font-mono text-text-muted">{{ slotProps.data.benchmarkOrder }}</span>
          </template>
        </Column>
        <Column
          field="canonicalName"
          header="Scientific Name"
        >
          <template #body="slotProps">
            <span
              class="italic"
              v-html="highlight(slotProps.data.canonicalName)"
            />
          </template>
        </Column>
        <Column
          field="family"
          header="Family"
          style="width: 170px"
        />
        <Column
          field="genus"
          header="Genus"
          style="width: 150px"
        />
        <Column
          field="order"
          header="Order"
          style="width: 170px"
        />
        <Column
          field="class"
          header="Class"
          style="width: 160px"
        />
        <Column
          field="taxonomicStatus"
          header="Status"
          style="width: 150px"
        />
        <template #expansion="{ data }">
          <div class="px-4 py-2">
            <div
              v-for="v in matchedVernaculars(data)"
              :key="v.vernacularName"
              class="text-sm text-text-muted"
            >
              <span v-html="highlight(v.vernacularName)" />
              <span class="ml-1 text-xs opacity-60">({{ v.language }})</span>
            </div>
            <div
              v-if="matchedVernaculars(data).length === 0"
              class="text-xs text-text-muted opacity-50"
            >
              No matching common names
            </div>
          </div>
        </template>
      </DataTable>
    </div>
  </div>
</template>

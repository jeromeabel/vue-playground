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
      class="benchmark-primevue-table relative isolate overflow-hidden rounded border border-surface-dark"
    >
      <DataTable
        v-model:expanded-rows="expandedRows"
        :value="filteredSpecies"
        scrollable
        scroll-height="600px"
        :virtual-scroller-options="virtualScrollEnabled ? { itemSize: 40 } : undefined"
        class="benchmark-table text-sm"
      >
        <Column
          expander
          style="width: 3rem"
        />
        <Column
          field="benchmarkOrder"
          header="ID"
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
            <span class="italic">{{ slotProps.data.canonicalName }}</span>
          </template>
        </Column>
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
        <template #expansion="{ data }">
          <div class="px-4 py-2">
            <div
              v-for="v in matchedVernaculars(data)"
              :key="v.vernacularName"
              class="text-sm text-text-muted"
            >
              {{ v.vernacularName }}
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

<style scoped>
.benchmark-primevue-table :deep(.p-datatable-table-container) {
    position: relative;
    isolation: isolate;
}

.benchmark-primevue-table :deep(.p-datatable-table) {
    width: 100%;
    border-collapse: collapse;
}

.benchmark-primevue-table :deep(.p-datatable-thead > tr > th) {
    padding: 0.5rem 0.75rem;
    text-align: left;
    font-weight: 600;
    position: sticky;
    top: 0;
    z-index: 20;
    background: var(--color-sand-50);
    border-bottom: 1px solid var(--color-surface-dark);
}

.benchmark-primevue-table :deep(.p-datatable-tbody > tr > td) {
    padding: 0.5rem 0.75rem;
    border-bottom: 1px solid rgb(214 221 207 / 50%);
}

.benchmark-primevue-table :deep(.p-virtualscroller-content) {
    position: relative;
    z-index: 0;
}
</style>

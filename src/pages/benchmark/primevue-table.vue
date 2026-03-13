<script setup lang="ts">
import { onBeforeMount, onMounted, ref, useTemplateRef } from "vue";
import DataTable from "primevue/datatable";
import Column from "primevue/column";

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
      PrimeVue DataTable
    </h1>

    <MetricsPanel
      :mount-time-ms="mountTimeMs"
      :dom-node-count="domNodeCount"
      :fps="fps"
    />

    <div
      ref="tableContainer"
      class="benchmark-primevue-table relative isolate overflow-hidden rounded border border-surface-dark"
    >
      <DataTable
        :value="species"
        scrollable
        scroll-height="600px"
        :virtual-scroller-options="{ itemSize: 40 }"
        class="benchmark-table text-sm"
      >
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

<script setup lang="ts">
import { computed, onBeforeMount, onMounted, ref, useTemplateRef } from "vue";
import {
    createColumnHelper,
    FlexRender,
    getCoreRowModel,
    useVueTable,
} from "@tanstack/vue-table";
import { useVirtualizer } from "@tanstack/vue-virtual";

import type { GbifSpeciesSummary } from "@/api/gbif";
import MetricsPanel from "@/components/metrics-panel.vue";
import { useDomMetrics } from "@/composables/use-dom-metrics";

type BenchmarkedSpecies = GbifSpeciesSummary & { benchmarkOrder: number };

const species = ref<BenchmarkedSpecies[]>([]);
const tableContainer = useTemplateRef("tableContainer");
const scrollContainer = useTemplateRef("scrollContainer");

const {
    mountTimeMs,
    domNodeCount,
    fps,
    markBeforeMount,
    markAfterMount,
    startObserving,
    startFpsCounter,
} = useDomMetrics();

const columnHelper = createColumnHelper<BenchmarkedSpecies>();

const columns = [
    columnHelper.accessor("benchmarkOrder", {
        header: "ID",
        size: 72,
        minSize: 72,
        maxSize: 90,
    }),
    columnHelper.accessor("canonicalName", {
        header: "Scientific Name",
        size: 240,
        minSize: 220,
        maxSize: 320,
    }),
    columnHelper.accessor("family", {
        header: "Family",
        size: 170,
        minSize: 150,
        maxSize: 260,
    }),
    columnHelper.accessor("genus", {
        header: "Genus",
        size: 150,
        minSize: 130,
        maxSize: 240,
    }),
    columnHelper.accessor("order", {
        header: "Order",
        size: 170,
        minSize: 140,
        maxSize: 260,
    }),
    columnHelper.accessor("class", {
        header: "Class",
        size: 160,
        minSize: 140,
        maxSize: 240,
    }),
    columnHelper.accessor("taxonomicStatus", {
        header: "Status",
        size: 150,
        minSize: 130,
        maxSize: 220,
    }),
];

const table = useVueTable({
    get data() { return species.value; },
    columns,
    getCoreRowModel: getCoreRowModel(),
});

const rows = computed(() => table.getRowModel().rows);
// canonicalName is the single flex-grow column; all others use fixed px sizes.
const GROW_COLUMN = "canonicalName";

const virtualizerOptions = computed(() => ({
    count: rows.value.length,
    estimateSize: () => 40,
    getScrollElement: () => scrollContainer.value ?? null,
    overscan: 20,
}));

const virtualizer = useVirtualizer(virtualizerOptions);
const virtualRows = computed(() => virtualizer.value.getVirtualItems());
const totalSize = computed(() => virtualizer.value.getTotalSize());

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
        class="relative isolate max-h-150 overflow-auto rounded border border-surface-dark"
      >
        <table class="w-full table-fixed text-left text-sm">
          <colgroup>
            <col
              v-for="header in table.getHeaderGroups()[0]?.headers"
              :key="header.id"
              :style="header.column.id !== GROW_COLUMN ? { width: `${header.getSize()}px` } : {}"
            >
          </colgroup>
          <thead class="sticky top-0 z-20 bg-sand-50">
            <tr
              v-for="headerGroup in table.getHeaderGroups()"
              :key="headerGroup.id"
              class="border-b border-surface-dark"
            >
              <th
                v-for="header in headerGroup.headers"
                :key="header.id"
                class="px-3 py-2 font-semibold whitespace-nowrap overflow-hidden text-ellipsis"
              >
                <FlexRender
                  :render="header.column.columnDef.header"
                  :props="header.getContext()"
                />
              </th>
            </tr>
          </thead>
          <tbody :style="{ height: `${totalSize}px`, position: 'relative' }">
            <tr
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
              class="relative z-0 border-b border-surface-dark/50"
            >
              <td
                v-for="cell in rows[virtualRow.index]?.getVisibleCells()"
                :key="cell.id"
                class="px-3 py-2 overflow-hidden text-ellipsis"
                :class="{
                  'font-mono text-text-muted': cell.column.id === 'benchmarkOrder',
                  'italic whitespace-nowrap': cell.column.id === GROW_COLUMN,
                }"
                :style="cell.column.id !== GROW_COLUMN
                  ? { flex: 'none', width: `${cell.column.getSize()}px`, minWidth: `${cell.column.getSize()}px` }
                  : { flex: '1', minWidth: '0' }"
              >
                <FlexRender
                  :render="cell.column.columnDef.cell"
                  :props="cell.getContext()"
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

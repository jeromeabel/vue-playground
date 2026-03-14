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
import { useDebounce } from "@/composables/use-debounce";

type BenchmarkedSpecies = GbifSpeciesSummary & { benchmarkOrder: number };
type VernacularRow = { type: "vernacular"; data: { vernacularName: string; language: string }; parentKey: number };
type SpeciesRow = { type: "species"; data: BenchmarkedSpecies };
type FlatRow = SpeciesRow | VernacularRow;

const species = ref<BenchmarkedSpecies[]>([]);
const tableContainer = useTemplateRef("tableContainer");
const scrollContainer = useTemplateRef("scrollContainer");
const searchInput = ref("");
const query = useDebounce(searchInput, 300);

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

const flattenedRows = computed<FlatRow[]>(() => {
    if (!query.value) {
        return filteredSpecies.value.map(s => ({ type: "species" as const, data: s }));
    }
    const q = query.value.toLowerCase();
    const rows: FlatRow[] = [];
    for (const s of filteredSpecies.value) {
        rows.push({ type: "species", data: s });
        const matched = s.vernacularNames.filter(v =>
            v.vernacularName.toLowerCase().includes(q),
        );
        for (const v of matched) {
            rows.push({ type: "vernacular", data: v, parentKey: s.key });
        }
    }
    return rows;
});

const table = useVueTable({
    get data() { return filteredSpecies.value; },
    columns,
    getCoreRowModel: getCoreRowModel(),
});

// canonicalName is the single flex-grow column; all others use fixed px sizes.
const GROW_COLUMN = "canonicalName";

const virtualizerOptions = computed(() => ({
    count: flattenedRows.value.length,
    estimateSize: (index: number) => flattenedRows.value[index]?.type === "vernacular" ? 32 : 40,
    getScrollElement: () => scrollContainer.value ?? null,
    overscan: 20,
}));

const virtualizer = useVirtualizer(virtualizerOptions);
const virtualItems = computed(() => virtualizer.value.getVirtualItems());
const totalSize = computed(() => virtualizer.value.getTotalSize());

const headerGroups = computed(() => table.getHeaderGroups());
const columnCount = computed(() => columns.length);

// O(1) lookup: species key → TanStack row (used in template for cell rendering)
const rowByKey = computed(() => {
    const map = new Map<number, ReturnType<typeof table.getRowModel>["rows"][number]>();
    for (const row of table.getRowModel().rows) {
        map.set(row.original.key, row);
    }
    return map;
});

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

    <div ref="tableContainer">
      <div
        ref="scrollContainer"
        class="relative isolate max-h-150 overflow-auto rounded border border-surface-dark"
      >
        <table class="w-full table-fixed text-left text-sm">
          <colgroup>
            <col
              v-for="header in headerGroups[0]?.headers"
              :key="header.id"
              :style="header.column.id !== GROW_COLUMN ? { width: `${header.getSize()}px` } : {}"
            >
          </colgroup>
          <thead class="sticky top-0 z-20 bg-sand-50">
            <tr
              v-for="headerGroup in headerGroups"
              :key="headerGroup.id"
              class="border-b border-surface-dark"
            >
              <th
                v-for="header in headerGroup.headers"
                :key="header.id"
                class="overflow-hidden text-ellipsis whitespace-nowrap px-3 py-2 font-semibold"
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
              v-for="virtualRow in virtualItems"
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
              :class="{
                'bg-surface-50': flattenedRows[virtualRow.index]?.type === 'vernacular',
              }"
            >
              <template v-if="flattenedRows[virtualRow.index]?.type === 'species'">
                <td
                  v-for="cell in rowByKey.get((flattenedRows[virtualRow.index] as SpeciesRow).data.key)?.getVisibleCells()"
                  :key="cell.id"
                  class="overflow-hidden text-ellipsis px-3 py-2"
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
              </template>
              <template v-else-if="flattenedRows[virtualRow.index]?.type === 'vernacular'">
                <td
                  :colspan="columnCount"
                  class="px-8 py-1 text-sm text-text-muted"
                  style="flex: 1; min-width: 0;"
                >
                  {{ (flattenedRows[virtualRow.index] as VernacularRow).data.vernacularName }}
                  <span class="ml-1 text-xs opacity-60">
                    ({{ (flattenedRows[virtualRow.index] as VernacularRow).data.language }})
                  </span>
                </td>
              </template>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

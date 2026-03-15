<script setup lang="ts">
import type { BenchmarkResults } from "@/api/benchmark-types";

const props = defineProps<{
    results: BenchmarkResults;
}>();

const DISPLAY_METRICS = ["Score", "TBT", "DOM Size", "LCP"];

const displayMetrics = DISPLAY_METRICS.filter(m => props.results.metrics.includes(m));

const approachNames = Object.keys(props.results.approaches);

function getColorClass(metric: string, value: number): string {
    if (metric === "Score") {
        if (value >= 90) return "text-green-600";
        if (value >= 50) return "text-yellow-600";
        return "text-red-600";
    }

    const threshold = props.results.thresholds[metric];
    if (!threshold) {
    // No threshold — fall back to score logic (higher is better)
        if (value >= 90) return "text-green-600";
        if (value >= 50) return "text-yellow-600";
        return "text-red-600";
    }

    if (value <= threshold.good) return "text-green-600";
    if (value <= threshold.poor) return "text-yellow-600";
    return "text-red-600";
}

function formatValue(metric: string, value: number): string {
    if (metric === "Score") {
        return String(value);
    }
    if (metric === "DOM Size") {
        return value.toLocaleString();
    }
    return value.toLocaleString() + " ms";
}

function getThresholdDisplay(metric: string): string {
    if (metric === "Score") return "> 90";
    const threshold = props.results.thresholds[metric];
    if (!threshold) return "—";
    const formatted = threshold.good.toLocaleString();
    return `< ${formatted} ${threshold.unit}`;
}
</script>

<template>
  <div class="overflow-auto rounded border border-surface-dark">
    <table class="w-full text-left text-sm">
      <thead class="bg-sand-50">
        <tr class="border-b border-surface-dark">
          <th class="px-4 py-3 font-semibold">
            Metric
          </th>
          <th
            v-for="approach in approachNames"
            :key="approach"
            class="px-4 py-3 font-semibold"
          >
            {{ approach }}
          </th>
          <th class="px-4 py-3 font-semibold text-text-muted">
            Threshold
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(metric, index) in displayMetrics"
          :key="metric"
          :class="index < displayMetrics.length - 1 ? 'border-b border-surface-dark/50' : ''"
        >
          <td class="px-4 py-2.5 font-medium">
            {{ metric }}
          </td>
          <td
            v-for="approach in approachNames"
            :key="approach"
            class="px-4 py-2.5"
          >
            <span
              class="font-mono"
              :class="getColorClass(metric, results.approaches[approach][metric])"
            >
              {{ formatValue(metric, results.approaches[approach][metric]) }}
            </span>
          </td>
          <td class="px-4 py-2.5 text-text-muted">
            {{ getThresholdDisplay(metric) }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

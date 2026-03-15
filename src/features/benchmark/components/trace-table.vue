<script setup lang="ts">
import type { BenchmarkResults } from "../types";

const props = defineProps<{
    results: BenchmarkResults;
}>();

const DISPLAY_METRICS = ["fps", "longest_task_ms", "scripting_ms_per_s", "long_tasks_count"];

const displayMetrics = DISPLAY_METRICS.filter(m => props.results.metrics.includes(m));

const approachNames = Object.keys(props.results.approaches);

const METRIC_LABELS: Record<string, string> = {
    fps: "FPS",
    longest_task_ms: "Longest Task",
    scripting_ms_per_s: "Scripting",
    long_tasks_count: "Long Tasks (>50ms)",
};

function isHigherBetter(metric: string): boolean {
    const threshold = props.results.thresholds[metric];
    return threshold ? threshold.good > threshold.poor : false;
}

function getColorClass(metric: string, value: number): string {
    const threshold = props.results.thresholds[metric];
    if (!threshold) return "";

    if (isHigherBetter(metric)) {
        if (value >= threshold.good) return "text-green-600";
        if (value >= threshold.poor) return "text-yellow-600";
        return "text-red-600";
    }

    if (value <= threshold.good) return "text-green-600";
    if (value <= threshold.poor) return "text-yellow-600";
    return "text-red-600";
}

function formatValue(metric: string, value: number): string {
    const threshold = props.results.thresholds[metric];
    const unit = threshold?.unit ?? "";
    if (unit === "fps") return `${value} fps`;
    if (unit === "ms/s") return `${value.toLocaleString()} ms/s`;
    if (unit === "ms") return `${value.toLocaleString()} ms`;
    return String(value);
}

function getThresholdDisplay(metric: string): string {
    const threshold = props.results.thresholds[metric];
    if (!threshold) return "—";
    const sign = isHigherBetter(metric) ? ">" : "<";
    return `${sign} ${threshold.good.toLocaleString()} ${threshold.unit}`;
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
            {{ METRIC_LABELS[metric] ?? metric }}
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

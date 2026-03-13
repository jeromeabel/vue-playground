<script setup lang="ts">
defineProps<{
    mountTimeMs: number;
    domNodeCount: number;
    fps: number;
}>();
</script>

<template>
  <div class="mb-4 flex gap-4 rounded-lg bg-surface-dark px-4 py-2 text-sm font-mono">
    <div>
      <span class="text-text-muted">Mount:</span>
      <span class="ml-1 font-semibold">{{ mountTimeMs }}ms</span>
    </div>
    <div>
      <span class="text-text-muted">DOM:</span>
      <span class="ml-1 font-semibold">{{ domNodeCount.toLocaleString() }}</span>
    </div>
    <div>
      <span class="text-text-muted">FPS:</span>
      <span class="ml-1 font-semibold">{{ fps }}</span>
    </div>
  </div>
</template>

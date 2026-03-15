<template>
  <div>
    <div class="mb-1 h-8 w-64 animate-pulse rounded bg-surface-dark" />
    <div class="mb-4 h-5 w-40 animate-pulse rounded bg-surface-dark/60" />
    <div class="mb-6 flex flex-wrap gap-2">
      <div
        v-for="i in 6"
        :key="i"
        class="h-4 w-20 animate-pulse rounded bg-surface-dark/40"
      />
    </div>
    <div class="mb-6 h-60 w-80 animate-pulse rounded-lg bg-surface-dark/30" />
    <div class="grid grid-cols-2 gap-2">
      <div
        v-for="i in 4"
        :key="i"
        class="h-4 animate-pulse rounded bg-surface-dark/40"
      />
    </div>
  </div>
</template>

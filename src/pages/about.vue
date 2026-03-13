<template>
  <div class="max-w-2xl">
    <h1 class="mb-4 text-2xl font-bold">
      About
    </h1>
    <p class="mb-4 text-text-muted">
      This playground demonstrates Vue performance patterns for technical blog posts.
      It uses real botanical data from the GBIF Species API.
    </p>
    <ul class="list-inside list-disc space-y-2 text-sm text-text-muted">
      <li>TanStack Query caching: staleTime, initialData, prefetching, dependent queries</li>
      <li>Virtualization: comparing naive tables, PrimeVue DataTable, and TanStack Virtual</li>
      <li>Chunk error handling: surviving SPA deploys with Vite</li>
    </ul>
  </div>
</template>

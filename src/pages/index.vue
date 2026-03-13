<template>
  <div>
    <h1 class="mb-4 text-3xl font-bold">
      Botanical Explorer
    </h1>
    <p class="mb-8 text-text-muted">
      A Vue playground for exploring performance patterns with real botanical data.
    </p>
    <div class="grid gap-4 sm:grid-cols-3">
      <RouterLink
        to="/species"
        class="rounded-lg border border-surface-dark p-6 hover:border-primary hover:shadow-sm"
      >
        <h2 class="mb-1 font-semibold">
          Species Explorer
        </h2>
        <p class="text-sm text-text-muted">
          Browse plants from GBIF with TanStack Query caching.
        </p>
      </RouterLink>
      <RouterLink
        to="/benchmark"
        class="rounded-lg border border-surface-dark p-6 hover:border-primary hover:shadow-sm"
      >
        <h2 class="mb-1 font-semibold">
          Benchmark
        </h2>
        <p class="text-sm text-text-muted">
          Compare table rendering approaches with 3000 items.
        </p>
      </RouterLink>
      <RouterLink
        to="/about"
        class="rounded-lg border border-surface-dark p-6 hover:border-primary hover:shadow-sm"
      >
        <h2 class="mb-1 font-semibold">
          About
        </h2>
        <p class="text-sm text-text-muted">
          Why this playground exists.
        </p>
      </RouterLink>
    </div>
  </div>
</template>

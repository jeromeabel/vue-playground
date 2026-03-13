<template>
  <div>
    <h1 class="mb-4 text-2xl font-bold">
      Benchmark
    </h1>
    <p class="mb-6 text-text-muted">
      Compare table rendering approaches with 3000 botanical species.
    </p>
    <div class="grid gap-4 sm:grid-cols-3">
      <RouterLink
        to="/benchmark/basic-table"
        class="rounded-lg border border-surface-dark p-6 hover:border-primary hover:shadow-sm"
      >
        <h2 class="mb-1 font-semibold">
          Basic Table
        </h2>
        <p class="text-sm text-text-muted">
          Plain v-for - the baseline.
        </p>
      </RouterLink>
      <RouterLink
        to="/benchmark/primevue-table"
        class="rounded-lg border border-surface-dark p-6 hover:border-primary hover:shadow-sm"
      >
        <h2 class="mb-1 font-semibold">
          PrimeVue DataTable
        </h2>
        <p class="text-sm text-text-muted">
          Component library with virtual scroll.
        </p>
      </RouterLink>
      <RouterLink
        to="/benchmark/tanstack-table"
        class="rounded-lg border border-surface-dark p-6 hover:border-primary hover:shadow-sm"
      >
        <h2 class="mb-1 font-semibold">
          TanStack Table
        </h2>
        <p class="text-sm text-text-muted">
          Headless table + virtual scrolling.
        </p>
      </RouterLink>
    </div>
  </div>
</template>

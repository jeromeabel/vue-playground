<template>
  <div>
    <h1 class="mb-4 text-2xl font-bold">
      Benchmark
    </h1>
    <p class="mb-6 text-text-muted">
      Compare table rendering approaches with 10,000 botanical species.
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
          Plain v-for — the baseline.
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

    <section class="mt-10">
      <h2 class="mb-1 text-xl font-bold">
        Benchmark Results
      </h2>
      <p class="mb-4 text-sm text-text-muted">
        Lighthouse desktop preset · 5 runs · median · Chrome Incognito · 10,000 species dataset
      </p>

      <div class="overflow-auto rounded border border-surface-dark">
        <table class="w-full text-left text-sm">
          <thead class="bg-sand-50">
            <tr class="border-b border-surface-dark">
              <th class="px-4 py-3 font-semibold">
                Metric
              </th>
              <th class="px-4 py-3 font-semibold">
                Basic
              </th>
              <th class="px-4 py-3 font-semibold">
                PrimeVue
              </th>
              <th class="px-4 py-3 font-semibold">
                TanStack
              </th>
              <th class="px-4 py-3 font-semibold text-text-muted">
                Threshold
              </th>
            </tr>
          </thead>
          <tbody>
            <tr class="border-b border-surface-dark/50">
              <td class="px-4 py-2.5 font-medium">
                Performance Score
              </td>
              <td class="px-4 py-2.5">
                <span class="font-mono text-red-600">56</span>
              </td>
              <td class="px-4 py-2.5">
                <span class="font-mono text-yellow-600">74</span>
              </td>
              <td class="px-4 py-2.5">
                <span class="font-mono text-green-600">76</span>
              </td>
              <td class="px-4 py-2.5 text-text-muted">
                &gt; 90
              </td>
            </tr>
            <tr class="border-b border-surface-dark/50">
              <td class="px-4 py-2.5 font-medium">
                TBT (ms)
              </td>
              <td class="px-4 py-2.5">
                <span class="font-mono text-red-600">472</span>
              </td>
              <td class="px-4 py-2.5">
                <span class="font-mono text-yellow-600">44</span>
              </td>
              <td class="px-4 py-2.5">
                <span class="font-mono text-green-600">4</span>
              </td>
              <td class="px-4 py-2.5 text-text-muted">
                &lt; 200
              </td>
            </tr>
            <tr class="border-b border-surface-dark/50">
              <td class="px-4 py-2.5 font-medium">
                DOM Size
              </td>
              <td class="px-4 py-2.5">
                <span class="font-mono text-red-600">80,379</span>
              </td>
              <td class="px-4 py-2.5">
                <span class="font-mono text-green-600">708</span>
              </td>
              <td class="px-4 py-2.5">
                <span class="font-mono text-green-600">668</span>
              </td>
              <td class="px-4 py-2.5 text-text-muted">
                &lt; 1,500
              </td>
            </tr>
            <tr>
              <td class="px-4 py-2.5 font-medium">
                LCP (ms)
              </td>
              <td class="px-4 py-2.5">
                <span class="font-mono text-red-600">4,472</span>
              </td>
              <td class="px-4 py-2.5">
                <span class="font-mono text-red-600">5,154</span>
              </td>
              <td class="px-4 py-2.5">
                <span class="font-mono text-red-600">4,601</span>
              </td>
              <td class="px-4 py-2.5 text-text-muted">
                &lt; 2,500
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p class="mt-2 text-xs text-text-muted">
        Numbers captured before search feature was added. Re-run <code class="rounded bg-surface-dark/30 px-1">pnpm lighthouse:all && pnpm analyze:lighthouse</code> to update.
      </p>
    </section>
  </div>
</template>

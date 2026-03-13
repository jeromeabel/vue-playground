<script setup lang="ts">
const showcaseAreas = [
    {
        title: "Data Fetching",
        summary: "Examples focused on query lifecycles, caching, and API ergonomics.",
        state: "Planned",
    },
    {
        title: "Rendering Benchmarks",
        summary: "Comparisons for large lists, virtualization tradeoffs, and table performance.",
        state: "Planned",
    },
    {
        title: "Runtime Resilience",
        summary: "Experiments around chunk failures, upgrades, and deployment-safe UX patterns.",
        state: "Planned",
    },
] as const;

const setupHighlights = [
    "Vue 3 + TypeScript with strict checking",
    "Vue Router scaffold for route-level examples",
    "Vitest + Vue Test Utils for component coverage",
    "Tailwind v4 baseline with project-wide design tokens",
];
</script>

<template>
  <section class="grid gap-8 lg:grid-cols-[minmax(0,1.5fr)_minmax(320px,0.9fr)] lg:items-start">
    <div class="rounded-4xl border border-white/70 bg-white/70 p-8 shadow-[0_24px_80px_rgba(24,33,38,0.08)] backdrop-blur-xl sm:p-10">
      <p class="text-sm font-semibold uppercase tracking-[0.34em] text-moss-600">
        Technical writing, but runnable
      </p>
      <h1 class="mt-4 max-w-3xl text-4xl font-semibold tracking-tight text-slate-950 sm:text-5xl">
        A Vue sandbox for turning blog post ideas into concrete, inspectable examples.
      </h1>
      <p class="mt-5 max-w-2xl text-base leading-8 text-slate-700 sm:text-lg">
        This project is being shaped as a focused playground: each future route will isolate a single technical subject, keep the UI intentionally small, and make the implementation details easy to inspect while writing or reading a post.
      </p>

      <div class="mt-8 grid gap-4 sm:grid-cols-3">
        <article
          v-for="area in showcaseAreas"
          :key="area.title"
          class="rounded-3xl border border-slate-200/80 bg-sand-50 p-5 shadow-sm"
        >
          <div class="flex items-center justify-between gap-3">
            <h2 class="text-lg font-semibold text-slate-900">
              {{ area.title }}
            </h2>
            <span class="rounded-full bg-white px-2.5 py-1 text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">
              {{ area.state }}
            </span>
          </div>
          <p class="mt-3 text-sm leading-6 text-slate-600">
            {{ area.summary }}
          </p>
        </article>
      </div>
    </div>

    <aside class="space-y-6">
      <section class="rounded-4xl border border-moss-600/10 bg-moss-600 p-7 text-white shadow-[0_20px_60px_rgba(72,96,69,0.28)]">
        <p class="text-sm font-semibold uppercase tracking-[0.28em] text-white/70">
          What is wired today
        </p>
        <ul class="mt-5 space-y-3 text-sm leading-6 text-white/90">
          <li
            v-for="highlight in setupHighlights"
            :key="highlight"
          >
            {{ highlight }}
          </li>
        </ul>
      </section>

      <section class="rounded-[2rem] border border-white/70 bg-white/75 p-7 shadow-[0_20px_60px_rgba(24,33,38,0.06)] backdrop-blur-xl">
        <p class="text-sm font-semibold uppercase tracking-[0.28em] text-slate-500">
          Next move
        </p>
        <p class="mt-4 text-lg font-medium text-slate-900">
          The next routes will be added as focused demos instead of a generic product shell.
        </p>
        <p class="mt-3 text-sm leading-7 text-slate-600">
          That keeps the repository aligned with its real job: supporting blog posts with examples that are small enough to understand quickly and real enough to measure.
        </p>
      </section>
    </aside>
  </section>
</template>

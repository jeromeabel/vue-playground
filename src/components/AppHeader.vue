<script setup lang="ts">
import { RouterLink } from "vue-router";
</script>

<template>
  <header class="sticky top-0 z-10 border-b border-white/60 bg-white/75 backdrop-blur-xl">
    <div class="mx-auto flex max-w-6xl items-center justify-between gap-4 px-6 py-4 sm:px-8 lg:px-10">
      <RouterLink
        class="flex items-center gap-3"
        to="/"
      >
        <div class="flex h-11 w-11 items-center justify-center rounded-2xl bg-moss-600 text-sm font-semibold uppercase tracking-[0.2em] text-white shadow-lg shadow-moss-600/20">
          VP
        </div>
        <div>
          <p class="text-sm font-semibold uppercase tracking-[0.28em] text-moss-600">
            Vue Playground
          </p>
          <p class="text-sm text-slate-600">
            Technical demos shaped for blog posts.
          </p>
        </div>
      </RouterLink>

      <div class="flex items-center gap-3 text-sm text-slate-600">
        <span class="rounded-full border border-moss-600/15 bg-moss-600/8 px-3 py-1 font-medium text-moss-600">
          Minimal setup
        </span>
        <span class="hidden sm:inline">Home route live, feature routes next.</span>
      </div>
    </div>
  </header>
</template>

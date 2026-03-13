<script setup lang="ts">
import { RouterLink } from "vue-router";
</script>

<template>
  <header class="border-b border-surface-dark bg-white px-6 py-3">
    <nav class="mx-auto flex max-w-6xl items-center gap-6">
      <RouterLink
        to="/"
        class="text-lg font-semibold text-primary"
      >
        Vue Playground
      </RouterLink>

      <div class="flex gap-4 text-sm">
        <RouterLink
          to="/species"
          active-class="text-primary font-medium"
          class="text-text-muted hover:text-text"
        >
          Species
        </RouterLink>
        <RouterLink
          to="/benchmark"
          active-class="text-primary font-medium"
          class="text-text-muted hover:text-text"
        >
          Benchmark
        </RouterLink>
        <RouterLink
          to="/about"
          active-class="text-primary font-medium"
          class="text-text-muted hover:text-text"
        >
          About
        </RouterLink>
      </div>
    </nav>
  </header>
</template>

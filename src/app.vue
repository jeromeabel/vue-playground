<script setup lang="ts">
import { VueQueryDevtools } from "@tanstack/vue-query-devtools";

import AppHeader from "@/shared/components/app-header.vue";
</script>

<template>
  <div class="min-h-screen">
    <AppHeader />
    <main class="mx-auto max-w-6xl px-6 py-8">
      <RouterView />
    </main>
  </div>
  <VueQueryDevtools />
</template>

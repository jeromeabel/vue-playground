<script setup lang="ts">
import { RouterView } from "vue-router";

import AppHeader from "@/components/AppHeader.vue";
</script>

<template>
  <div class="min-h-screen">
    <AppHeader />
    <main class="mx-auto w-full max-w-6xl px-6 pb-16 pt-8 sm:px-8 lg:px-10">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>

<template>
  <header class="border-b">
    <div class="container py-4 flex justify-between items-center">
      <RouterLink to="/">
        <img alt="Vue logo" class="h-12 w-12 bg-green-200 p-2 rounded-full" src="@/assets/logo.svg"
      /></RouterLink>
      <nav class="flex gap-8 font-bold uppercase tracking-wide text-gray-700">
        <RouterLink to="/">Home</RouterLink>
        <RouterLink to="/products">Products</RouterLink>
      </nav>
    </div>
  </header>
</template>

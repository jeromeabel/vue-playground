<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <header class="border-b border-gray-400">
    <div class="container py-8 flex justify-between items-center">
      <img alt="Vue logo" class="h-12" src="@/assets/logo.svg" />
      <nav>
        <RouterLink to="/">Home</RouterLink>
      </nav>
    </div>
  </header>
  <RouterView />
</template>

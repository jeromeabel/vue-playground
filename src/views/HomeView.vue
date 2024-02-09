<script setup lang="ts">
import { useOpticalStore } from '@/stores/OpticalStore'
const opticalStore = useOpticalStore()
opticalStore.fetchProducts()
</script>

<template>
  <main class="container py-8">
    <h1 class="text-5xl uppercase font-bold">Welcome To Vue Shop!</h1>
    {{ opticalStore.products }}
  </main>
</template>

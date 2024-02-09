<script setup lang="ts">
import ProductList from '@/components/ProductList.vue'
import { useOpticalStore } from '@/stores/OpticalStore'
const opticalStore = useOpticalStore()
opticalStore.fetchProducts()
</script>

<template>
  <main class="container py-8">
    <h1 class="text-5xl uppercase font-bold">Welcome To Vue Shop!</h1>
    <ProductList :products="opticalStore.shortProductsList" />
  </main>
</template>

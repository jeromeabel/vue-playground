<script setup lang="ts">
import type { Product } from '@/entities/Products.interface'
import ProductCard from '@/components/ProductCard.vue'

defineProps({
  products: {
    type: Array<Product>,
    required: true
  }
})
</script>

<template>
  <ul class="grid grid-cols-3 gap-4 py-8">
    <li v-for="product in products" :key="`product-${product.id}`">
      <ProductCard :product="product" />
    </li>
  </ul>
</template>

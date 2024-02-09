<script setup lang="ts">
import type { PropType } from 'vue'
import type { Product } from '@/entities/Products.interface'
import { RouterLink } from 'vue-router'

defineProps({
  product: {
    type: Object as PropType<Product>,
    required: true
  }
})

// defineProps<Product>() // ??
</script>

<template>
  <RouterLink :to="'/products/' + product.id">
    <div class="border p-4 bg-gray-200 rounded">
      <p class="text-xl font-bold tracking-wider">{{ product.name }}</p>
      <p>{{ product.material }}</p>
      <p>{{ product.price }}€</p>
    </div>
  </RouterLink>
</template>

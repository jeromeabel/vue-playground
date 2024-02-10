<script setup lang="ts">
import type { PropType } from 'vue'
import type { Product } from '@/entities/Products.interface'
import { useCartStore } from '@/stores/CartStore'

import { RouterLink } from 'vue-router'

const cartStore = useCartStore()

defineProps({
  product: {
    type: Object as PropType<Product>,
    required: true
  }
})

// defineProps<Product>() // ??
</script>

<template>
  <div class="border p-4 bg-gray-200 rounded">
    <RouterLink :to="'/products/' + product.id">
      <div class="hover:bg-gray-300">
        <p class="text-xl font-bold tracking-wider">{{ product.name }}</p>
        <p>{{ product.material }}</p>
        <p>{{ product.price }}€</p>
      </div>
    </RouterLink>

    <button
      @click="cartStore.addProduct(product)"
      class="my-4 px-4 py-2 bg-green-300 rounded border hover:text-white hover:bg-green-900"
    >
      Add To Cart
    </button>
  </div>
</template>

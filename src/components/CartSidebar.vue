<script setup lang="ts">
import { useCartStore } from '@/stores/CartStore'
const cartStore = useCartStore()
</script>

<template>
  <div class="p-8 bg-purple-300 mt-8">
    <h2 class="uppercase font-bold border-b border-black mb-4">Basket</h2>
    <ul class="flex flex-col gap-2">
      <li
        v-for="(product, index) in cartStore.products"
        :key="`cart-item-${index}`"
        class="text-purple-800 font-bold border-s border-purple-500 ps-2"
      >
        {{ product.name }}: {{ product.price }}€
      </li>
    </ul>
  </div>
</template>

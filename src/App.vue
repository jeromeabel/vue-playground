<script setup lang="ts">
import { RouterView } from 'vue-router'
import BaseHeader from '@/components/BaseHeader.vue'
import CartSidebar from '@/components/CartSidebar.vue'
import { onMounted } from 'vue'

onMounted(() => {
  console.log('mounted')
})
</script>

<template>
  <BaseHeader />
  <div class="container grid grid-cols-4">
    <div class="col-span-3"><RouterView /></div>
    <CartSidebar />
  </div>
</template>

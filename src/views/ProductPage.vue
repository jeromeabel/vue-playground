<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { useRoute } from 'vue-router'
import { useOpticalStore } from '@/stores/OpticalStore'
const route = useRoute()
const opticalStore = useOpticalStore()
opticalStore.fetchProducts()
const { getProductById } = storeToRefs(opticalStore)

// Vérifiez si route.params.id est une chaîne de caractères avant de l'utiliser
const productId = Array.isArray(route.params.id) ? route.params.id[0] : route.params.id

// const actualGetProductById = getProductById.value // ??
const product = getProductById.value(productId) //valeur réelle de la référence calculée
</script>

<template>
  <main class="container py-8">
    <h1 class="text-5xl uppercase font-bold">{{ product?.name }}</h1>
    <p><strong>Brand</strong>: {{ product?.brand }}</p>
    <p><strong>Material</strong>: {{ product?.material }}</p>
    <p><strong>Color</strong>: {{ product?.color }}</p>
    <p><strong>Price</strong>: {{ product?.price }}€</p>
  </main>
</template>

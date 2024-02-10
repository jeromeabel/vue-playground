import { defineStore } from 'pinia'
import type { Product } from '@/entities/Products.interface'

export const useCartStore = defineStore('CartStore', {
  state: () => ({
    products: [] as Product[]
  }),
  actions: {
    addProduct(newProduct: Product) {
      this.products.push(newProduct)
    }
  }
})

import { defineStore } from 'pinia'
import type { Product } from '@/entities/Products.interface'

export const useOpticalStore = defineStore('OpticalStore', {
  state: () => ({
    products: [] as Product[]
  }),
  getters: {
    shortProductsList: (state) => {
      return state.products.splice(0, 5) // équivalent de la function computed
    }
  },
  actions: {
    async fetchProducts() {
      const response = await fetch('http://localhost:3000/products').then((response) =>
        response.json()
      )
      this.products = response // => global store
    }
  }
})

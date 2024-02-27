import { defineStore } from 'pinia'
import type { Product } from '@/entities/Products.interface'

export const useOpticalStore = defineStore('OpticalStore', {
  state: () => ({
    products: [] as Product[]
  }),
  getters: {
    shortProductsList: (state) => {
      return state.products.slice(0, 9) as Product[] // équivalent de la function computed
    },
    getProductById: (state) => {
      return (productId: string) => state.products.find((product) => product.id === productId)
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

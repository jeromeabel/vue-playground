import { defineStore } from 'pinia'
import type { Product } from '@/entities/Products.interface'

export const useOpticalStore = defineStore('OpticalStore', {
  state: () => ({
    products: [] as Product[]
  }),
  getters: {
    shortProductsList: (state) => {
      return state.products.splice(0, 9) // équivalent de la function computed
    },
    numberOfProducts: (state) => {
      return state.products.length
    },
    getProduct: (): Product => {
      return {
        name: 'Lunettes de soleil aviateur',
        brand: 'Ray-Ban',
        material: 'Acier inoxydable',
        color: 'Doré',
        price: 150,
        id: '0dvc'
      }
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

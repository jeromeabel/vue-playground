import HomeView from '@/views/HomeView.vue'
import { mount } from '@vue/test-utils'

describe('HomeView', () => {
  it('Should render the component', async () => {
    mount(HomeView)
  })
})

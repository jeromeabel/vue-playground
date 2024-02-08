import { mount } from '@vue/test-utils'

// The component to test
const MessageComponent = {
  template: '<p>{{ msg }}</p>',
  props: ['msg']
}

describe('Hello World: testing the test config with a dummy Vue component', () => {
  it('Should display a message', () => {
    const wrapper = mount(MessageComponent, {
      props: {
        msg: 'Hello world'
      }
    })

    // Assert the rendered text of the component
    expect(wrapper.text()).toContain('Hello world')
  })
})

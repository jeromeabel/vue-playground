import { mount } from "@vue/test-utils"
import { createMemoryHistory, createRouter } from "vue-router"
import { defineComponent } from "vue"

import App from "@/app.vue"

const StubPage = defineComponent({ template: "<div>stub</div>" })

describe("App", () => {
    it("renders the app shell with navigation", async () => {
        const router = createRouter({
            history: createMemoryHistory(),
            routes: [
                { path: "/", component: StubPage },
                { path: "/species", component: StubPage },
                { path: "/benchmark", component: StubPage },
                { path: "/about", component: StubPage },
            ],
        })

        router.push("/")
        await router.isReady()

        const wrapper = mount(App, {
            global: {
                plugins: [router],
                stubs: { VueQueryDevtools: true },
            },
        })

        expect(wrapper.text()).toContain("Vue Playground")

        wrapper.unmount()
    })
})

import { mount } from "@vue/test-utils";
import { createMemoryHistory, createRouter } from "vue-router";

import App from "@/app.vue";
import HomePage from "@/pages/home-page.vue";

describe("App", () => {
    it("renders the routed home page scaffold", async () => {
        const router = createRouter({
            history: createMemoryHistory(),
            routes: [
                {
                    path: "/",
                    component: HomePage,
                },
                {
                    path: "/species",
                    component: HomePage,
                },
                {
                    path: "/benchmark",
                    component: HomePage,
                },
                {
                    path: "/about",
                    component: HomePage,
                },
            ],
        });

        router.push("/");
        await router.isReady();

        const wrapper = mount(App, {
            global: {
                plugins: [router],
                stubs: {
                    VueQueryDevtools: true,
                },
            },
        });

        expect(wrapper.text()).toContain("Vue Playground");
        expect(wrapper.text()).toContain("Technical writing, but runnable");
        expect(wrapper.text()).toContain("What is wired today");

        wrapper.unmount();
    });
});

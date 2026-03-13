import { mount } from "@vue/test-utils";
import { createMemoryHistory, createRouter } from "vue-router";

import App from "@/App.vue";
import HomePage from "@/pages/HomePage.vue";

describe("App", () => {
    it("renders the routed home page scaffold", async () => {
        const router = createRouter({
            history: createMemoryHistory(),
            routes: [
                {
                    path: "/",
                    component: HomePage,
                },
            ],
        });

        router.push("/");
        await router.isReady();

        const wrapper = mount(App, {
            global: {
                plugins: [router],
            },
        });

        expect(wrapper.text()).toContain("Vue Playground");
        expect(wrapper.text()).toContain("Technical writing, but runnable");
        expect(wrapper.text()).toContain("What is wired today");

        wrapper.unmount();
    });
});

import { mount } from "@vue/test-utils";
import { VueQueryPlugin } from "@tanstack/vue-query";

import App from "@/app.vue";

describe("App", () => {
    it("mounts without errors", () => {
        const wrapper = mount(App, {
            global: {
                plugins: [VueQueryPlugin],
                stubs: {
                    RouterView: true,
                    RouterLink: true,
                    VueQueryDevtools: true,
                },
            },
        });

        expect(wrapper.exists()).toBe(true);
    });
});

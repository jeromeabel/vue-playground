import { createApp } from "vue";
import { VueQueryPlugin } from "@tanstack/vue-query";
import PrimeVue from "primevue/config";
import Aura from "@primeuix/themes/aura";
import { definePreset } from "@primeuix/themes";
import App from "./app.vue";
import { router } from "./router";
import "./assets/main.css";

// Tune the Aura preset so the styled DataTable visually matches the raw-Tailwind
// benchmark tables (basic-table, tanstack-table): identical sand-50 header,
// surface-dark rules, and px-3 py-2 (0.5rem 0.75rem) cell padding. Aura's default
// cell padding is 0.75rem 1rem, which made PrimeVue rows look roomier than the
// others. Column-title weight is left at Aura's default 600 (= font-semibold).
const BenchmarkAura = definePreset(Aura, {
    components: {
        datatable: {
            headerCell: {
                background: "#fbf8f2", // sand-50
                color: "#182126", // text
                borderColor: "#d6ddcf", // surface-dark
                padding: "0.5rem 0.75rem",
            },
            bodyCell: {
                borderColor: "rgb(214 221 207 / 50%)", // surface-dark/50
                padding: "0.5rem 0.75rem",
            },
            // The Tailwind tables set no row background, so the page's light
            // gradient shows through. Aura defaults rows to white {content.background}.
            row: {
                background: "transparent",
                hoverBackground: "transparent",
            },
        },
    },
});

const app = createApp(App);

// Styled mode with the Aura preset (mirrors production use of the full PrimeVue
// toolkit). cssLayer keeps PrimeVue's styles in a layer that Tailwind utilities
// can override — see the @layer order in assets/main.css.
app.use(PrimeVue, {
    theme: {
        preset: BenchmarkAura,
        options: {
            // App is light-only; without this Aura follows the OS and renders
            // dark surfaces when the system is in dark mode.
            darkModeSelector: false,
            cssLayer: {
                name: "primevue",
                order: "theme, base, primevue",
            },
        },
    },
});

app.use(VueQueryPlugin, {
    queryClientConfig: {
        defaultOptions: {
            queries: {
                staleTime: 1000 * 60 * 5,
            },
        },
    },
});

app.use(router);
app.mount("#app");

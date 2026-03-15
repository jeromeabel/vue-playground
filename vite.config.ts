import { fileURLToPath, URL } from "node:url";
import vue from "@vitejs/plugin-vue";
import tailwindcss from "@tailwindcss/vite";
import VueRouter from "unplugin-vue-router/vite";
import { defineConfig } from "vitest/config";

// https://vite.dev/config/
export default defineConfig({
    plugins: [
        VueRouter({
            routesFolder: [
                { src: "src/features/species/pages", path: "species/" },
                { src: "src/features/benchmark/pages", path: "benchmark/" },
                "src/pages",
            ],
            dts: "./typed-router.d.ts",
            extensions: [".vue"],
            importMode: "async",
        }),
        vue(),
        tailwindcss(),
    ],
    resolve: {
        alias: {
            "@": fileURLToPath(new URL("./src", import.meta.url)),
        },
    },
    test: {
        environment: "happy-dom",
        globals: true,
        css: true,
    },
});

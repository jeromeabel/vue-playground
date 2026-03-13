import js from "@eslint/js";
import stylistic from "@stylistic/eslint-plugin";
import globals from "globals";
import pluginVue from "eslint-plugin-vue";
import unicorn from "eslint-plugin-unicorn";
import tseslint from "typescript-eslint";

export default tseslint.config(
    {
        ignores: ["dist", "coverage", "node_modules"],
    },
    js.configs.recommended,
    ...tseslint.configs.recommended,
    ...pluginVue.configs["flat/recommended"],
    stylistic.configs.customize({
        indent: 4,
        quotes: "double",
        semi: true,
        commaDangle: "always-multiline",
        jsx: false,
    }),
    {
        files: ["**/*.{js,mjs,cjs,ts,tsx,vue}"],
        plugins: {
            unicorn,
        },
        languageOptions: {
            ecmaVersion: "latest",
            sourceType: "module",
            globals: {
                ...globals.browser,
                ...globals.node,
            },
        },
        rules: {
            "vue/multi-word-component-names": "off",
            "unicorn/filename-case": [
                "error",
                {
                    cases: {
                        kebabCase: true,
                    },
                    ignore: ["^\\[.+\\]$"],
                    multipleFileExtensions: true,
                },
            ],
        },
    },
    {
        files: ["**/*.vue"],
        languageOptions: {
            parserOptions: {
                parser: tseslint.parser,
            },
        },
    },
    {
        files: ["**/*.{test,spec}.{ts,tsx}"],
        rules: {
            "@typescript-eslint/no-floating-promises": "off",
        },
    },
);

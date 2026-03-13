# Plan 2: Minimal Setup for AI

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffold a working Vue app with the full toolchain (Vite, TypeScript, Vue Router file-based, Tailwind CSS v4, ESLint 10, TanStack Query, Vitest), shell pages, GBIF API client, species list/detail pages, and a CLAUDE.md so an AI agent can immediately start building features.

**Architecture:** Manual project setup (not `create-vue` scaffold) since we need precise control over each tool's config. File-based routing via Unplugin Vue Router. TanStack Query for all server state. Tailwind v4 CSS-first config. No Pinia, no Prettier.

**Tech Stack:** pnpm, Vite 7, Vue 3.5+, TypeScript 5.8+, Vue Router 4.5+ (Unplugin Vue Router), @tanstack/vue-query, Tailwind CSS 4, ESLint 10 + @stylistic, Vitest 4.1.0

**Spec:** `docs/superpowers/specs/2026-03-13-vue-playground-reset-design.md`

---

## Chunk 1: Project Scaffold & Tooling

### Task 1: Initialize package.json and Install Dependencies

**Files:**
- Create: `package.json`

- [ ] **Step 1: Create package.json**

```bash
pnpm init
```

Edit `package.json` to set:
```json
{
  "name": "vue-playground",
  "version": "0.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc --build --force && vite build",
    "preview": "vite preview",
    "test": "vitest",
    "test:run": "vitest run",
    "lint": "eslint .",
    "lint:fix": "eslint . --fix"
  }
}
```

- [ ] **Step 2: Install production dependencies**

```bash
pnpm add vue vue-router@latest @tanstack/vue-query
```

- [ ] **Step 3: Install dev dependencies**

```bash
pnpm add -D vite @vitejs/plugin-vue unplugin-vue-router vue-tsc typescript
pnpm add -D tailwindcss @tailwindcss/vite
pnpm add -D eslint jiti @eslint/js typescript-eslint eslint-plugin-vue @stylistic/eslint-plugin globals
pnpm add -D vitest@4.1.0 @vue/test-utils happy-dom @tanstack/vue-query-devtools
```

- [ ] **Step 4: Verify install**

Run: `pnpm ls --depth 0`
Expected: All packages listed without errors

- [ ] **Step 5: Commit**

```bash
git add package.json pnpm-lock.yaml
git commit -m "setup: initialize package.json with all dependencies"
```

---

### Task 2: TypeScript Configuration

**Files:**
- Create: `tsconfig.json`
- Create: `tsconfig.app.json`
- Create: `tsconfig.node.json`
- Create: `env.d.ts`

- [ ] **Step 1: Create tsconfig.json**

```json
{
  "files": [],
  "references": [
    { "path": "./tsconfig.app.json" },
    { "path": "./tsconfig.node.json" }
  ]
}
```

- [ ] **Step 2: Create tsconfig.app.json**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "moduleResolution": "Bundler",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedIndexedAccess": true,
    "jsx": "preserve",
    "jsxImportSource": "vue",
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    },
    "types": ["unplugin-vue-router/client"]
  },
  "include": [
    "env.d.ts",
    "src/**/*",
    "src/**/*.vue",
    "typed-router.d.ts"
  ],
  "exclude": ["src/**/__tests__/*"]
}
```

- [ ] **Step 3: Create tsconfig.node.json**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "strict": true,
    "noEmit": true
  },
  "include": [
    "vite.config.ts",
    "eslint.config.ts",
    "scripts/**/*.ts"
  ]
}
```

- [ ] **Step 4: Create env.d.ts**

```typescript
/// <reference types="vite/client" />
/// <reference types="unplugin-vue-router/client" />
```

- [ ] **Step 5: Commit**

```bash
git add tsconfig.json tsconfig.app.json tsconfig.node.json env.d.ts
git commit -m "setup: add TypeScript configuration"
```

---

### Task 3: Vite Configuration

**Files:**
- Create: `vite.config.ts`

- [ ] **Step 1: Create vite.config.ts**

```typescript
/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import Vue from '@vitejs/plugin-vue'
import VueRouter from 'unplugin-vue-router/vite'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    VueRouter({
      routesFolder: 'src/pages',
      dts: './typed-router.d.ts',
      extensions: ['.vue'],
      importMode: 'async',
    }),
    Vue(),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      '@': new URL('./src', import.meta.url).pathname,
    },
  },
  test: {
    globals: true,
    environment: 'happy-dom',
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
  },
})
```

- [ ] **Step 2: Commit**

```bash
git add vite.config.ts
git commit -m "setup: add Vite config with Vue Router, Tailwind, Vitest"
```

---

### Task 4: ESLint Configuration

**Files:**
- Create: `eslint.config.ts`

- [ ] **Step 1: Create eslint.config.ts**

```typescript
import eslint from '@eslint/js'
import tseslint from 'typescript-eslint'
import pluginVue from 'eslint-plugin-vue'
import stylistic from '@stylistic/eslint-plugin'
import globals from 'globals'

export default tseslint.config(
  { ignores: ['dist', 'typed-router.d.ts'] },

  eslint.configs.recommended,

  ...tseslint.configs.recommended,

  ...pluginVue.configs['flat/recommended'],

  stylistic.configs.customize({
    indent: 2,
    quotes: 'single',
    semi: false,
    jsx: true,
  }),

  {
    files: ['**/*.{ts,vue}'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: globals.browser,
      parserOptions: {
        parser: tseslint.parser,
      },
    },
    rules: {
      '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
      'vue/multi-word-component-names': 'off',
    },
  },

  {
    files: ['**/*.js'],
    ...tseslint.configs.disableTypeChecked,
  },
)
```

Note: We use `tseslint.config()` (from `typescript-eslint`) instead of ESLint's `defineConfig()` — it handles the array spreading and type-checking config composition correctly.

- [ ] **Step 2: Run lint to verify config loads**

Run: `pnpm lint`
Expected: No errors (no source files yet), exits cleanly

- [ ] **Step 3: Commit**

```bash
git add eslint.config.ts
git commit -m "setup: add ESLint 10 flat config with stylistic + Vue + TS"
```

---

### Task 5: Tailwind CSS + Base Styles

**Files:**
- Create: `src/assets/main.css`

- [ ] **Step 1: Create src/assets/main.css**

```bash
mkdir -p src/assets
```

```css
@import "tailwindcss";

@theme {
  --color-primary: oklch(0.55 0.15 160);
  --color-primary-light: oklch(0.75 0.12 160);
  --color-surface: oklch(0.98 0.005 160);
  --color-surface-dark: oklch(0.93 0.01 160);
  --color-text: oklch(0.25 0.02 260);
  --color-text-muted: oklch(0.55 0.02 260);

  --font-sans: Inter, system-ui, sans-serif;
  --font-mono: "JetBrains Mono", ui-monospace, monospace;
}

body {
  @apply bg-surface text-text font-sans antialiased;
}
```

- [ ] **Step 2: Commit**

```bash
git add src/assets/main.css
git commit -m "setup: add Tailwind CSS v4 with botanical theme"
```

---

### Task 6: Entry Point + App Shell

**Files:**
- Create: `index.html`
- Create: `src/main.ts`
- Create: `src/router.ts`
- Create: `src/App.vue`
- Create: `src/components/AppHeader.vue`

- [ ] **Step 1: Create index.html**

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Vue Playground — Botanical Explorer</title>
    <link rel="icon" href="/favicon.ico" />
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>
```

- [ ] **Step 2: Create src/router.ts**

```typescript
import { createRouter, createWebHistory } from 'vue-router'
import { routes, handleHotUpdate } from 'vue-router/auto-routes'

export const router = createRouter({
  history: createWebHistory(),
  routes,
})

if (import.meta.hot) {
  handleHotUpdate(router)
}
```

- [ ] **Step 3: Create src/main.ts**

```typescript
import { createApp } from 'vue'
import { VueQueryPlugin } from '@tanstack/vue-query'
import { router } from './router'
import App from './App.vue'
import './assets/main.css'

const app = createApp(App)

app.use(VueQueryPlugin, {
  queryClientConfig: {
    defaultOptions: {
      queries: {
        staleTime: 1000 * 60 * 5,
      },
    },
  },
})

app.use(router)
app.mount('#app')
```

- [ ] **Step 4: Create src/components/AppHeader.vue**

```vue
<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>

<template>
  <header class="border-b border-surface-dark bg-white px-6 py-3">
    <nav class="mx-auto flex max-w-6xl items-center gap-6">
      <RouterLink
        to="/"
        class="text-lg font-semibold text-primary"
      >
        Vue Playground
      </RouterLink>
      <div class="flex gap-4 text-sm">
        <RouterLink
          to="/species"
          active-class="text-primary font-medium"
          class="text-text-muted hover:text-text"
        >
          Species
        </RouterLink>
        <RouterLink
          to="/benchmark"
          active-class="text-primary font-medium"
          class="text-text-muted hover:text-text"
        >
          Benchmark
        </RouterLink>
        <RouterLink
          to="/about"
          active-class="text-primary font-medium"
          class="text-text-muted hover:text-text"
        >
          About
        </RouterLink>
      </div>
    </nav>
  </header>
</template>
```

- [ ] **Step 5: Create src/App.vue**

```vue
<script setup lang="ts">
import { VueQueryDevtools } from '@tanstack/vue-query-devtools'
import AppHeader from './components/AppHeader.vue'
</script>

<template>
  <div class="min-h-screen">
    <AppHeader />
    <main class="mx-auto max-w-6xl px-6 py-8">
      <RouterView />
    </main>
  </div>
  <VueQueryDevtools />
</template>
```

- [ ] **Step 6: Commit**

```bash
git add index.html src/main.ts src/router.ts src/App.vue src/components/AppHeader.vue
git commit -m "setup: add entry point, router, App shell with header"
```

---

### Task 7: Shell Pages

**Files:**
- Create: `src/pages/index.vue`
- Create: `src/pages/about.vue`
- Create: `src/pages/species/index.vue`
- Create: `src/pages/species/[id].vue`
- Create: `src/pages/benchmark/index.vue`

- [ ] **Step 1: Create src/pages/index.vue**

```vue
<template>
  <div>
    <h1 class="mb-4 text-3xl font-bold">
      Botanical Explorer
    </h1>
    <p class="mb-8 text-text-muted">
      A Vue playground for exploring performance patterns with real botanical data.
    </p>
    <div class="grid gap-4 sm:grid-cols-3">
      <RouterLink
        to="/species"
        class="rounded-lg border border-surface-dark p-6 hover:border-primary hover:shadow-sm"
      >
        <h2 class="mb-1 font-semibold">
          Species Explorer
        </h2>
        <p class="text-sm text-text-muted">
          Browse plants from GBIF with TanStack Query caching.
        </p>
      </RouterLink>
      <RouterLink
        to="/benchmark"
        class="rounded-lg border border-surface-dark p-6 hover:border-primary hover:shadow-sm"
      >
        <h2 class="mb-1 font-semibold">
          Benchmark
        </h2>
        <p class="text-sm text-text-muted">
          Compare table rendering approaches with 3000 items.
        </p>
      </RouterLink>
      <RouterLink
        to="/about"
        class="rounded-lg border border-surface-dark p-6 hover:border-primary hover:shadow-sm"
      >
        <h2 class="mb-1 font-semibold">
          About
        </h2>
        <p class="text-sm text-text-muted">
          Why this playground exists.
        </p>
      </RouterLink>
    </div>
  </div>
</template>
```

- [ ] **Step 2: Create src/pages/about.vue**

```vue
<template>
  <div class="max-w-2xl">
    <h1 class="mb-4 text-2xl font-bold">
      About
    </h1>
    <p class="mb-4 text-text-muted">
      This playground demonstrates Vue performance patterns for technical blog posts.
      It uses real botanical data from the GBIF Species API.
    </p>
    <ul class="list-inside list-disc space-y-2 text-sm text-text-muted">
      <li>TanStack Query caching: staleTime, initialData, prefetching, dependent queries</li>
      <li>Virtualization: comparing naive tables, PrimeVue DataTable, and TanStack Virtual</li>
      <li>Chunk error handling: surviving SPA deploys with Vite</li>
    </ul>
  </div>
</template>
```

- [ ] **Step 3: Create src/pages/species/index.vue (placeholder)**

```vue
<template>
  <div>
    <h1 class="mb-4 text-2xl font-bold">
      Species
    </h1>
    <p class="text-text-muted">
      Species list coming soon — TanStack Query caching demo.
    </p>
  </div>
</template>
```

- [ ] **Step 4: Create src/pages/species/[id].vue (placeholder)**

```vue
<script setup lang="ts">
import { useRoute } from 'vue-router'

const route = useRoute()
</script>

<template>
  <div>
    <h1 class="mb-4 text-2xl font-bold">
      Species #{{ route.params.id }}
    </h1>
    <p class="text-text-muted">
      Species detail coming soon.
    </p>
  </div>
</template>
```

- [ ] **Step 5: Create src/pages/benchmark/index.vue (placeholder)**

```vue
<template>
  <div>
    <h1 class="mb-4 text-2xl font-bold">
      Benchmark
    </h1>
    <p class="mb-6 text-text-muted">
      Compare table rendering approaches with 3000 botanical species.
    </p>
    <div class="grid gap-4 sm:grid-cols-3">
      <RouterLink
        to="/benchmark/basic-table"
        class="rounded-lg border border-surface-dark p-6 hover:border-primary hover:shadow-sm"
      >
        <h2 class="mb-1 font-semibold">
          Basic Table
        </h2>
        <p class="text-sm text-text-muted">
          Plain v-for — the baseline.
        </p>
      </RouterLink>
      <RouterLink
        to="/benchmark/primevue-table"
        class="rounded-lg border border-surface-dark p-6 hover:border-primary hover:shadow-sm"
      >
        <h2 class="mb-1 font-semibold">
          PrimeVue DataTable
        </h2>
        <p class="text-sm text-text-muted">
          Component library with virtual scroll.
        </p>
      </RouterLink>
      <RouterLink
        to="/benchmark/tanstack-table"
        class="rounded-lg border border-surface-dark p-6 hover:border-primary hover:shadow-sm"
      >
        <h2 class="mb-1 font-semibold">
          TanStack Table
        </h2>
        <p class="text-sm text-text-muted">
          Headless table + virtual scrolling.
        </p>
      </RouterLink>
    </div>
  </div>
</template>
```

- [ ] **Step 6: Commit**

```bash
mkdir -p src/pages/species src/pages/benchmark
git add src/pages/
git commit -m "setup: add shell pages for all routes"
```

---

## Chunk 2: GBIF API Client, Species Feature & Netlify

### Task 8: GBIF API Types and Client

**Files:**
- Create: `src/api/gbif.ts`

- [ ] **Step 1: Create src/api/gbif.ts**

```typescript
const BASE_URL = 'https://api.gbif.org/v1'

// --- Types ---

export interface GbifSpeciesSummary {
  key: number
  scientificName: string
  canonicalName: string
  kingdom: string
  phylum: string
  class: string
  order: string
  family: string
  genus: string
  taxonomicStatus: string
  rank: string
}

export interface GbifSpeciesDetail extends GbifSpeciesSummary {
  authorship: string
  publishedIn?: string
  nameType: string
  numDescendants: number
}

export interface GbifSearchResponse {
  offset: number
  limit: number
  endOfRecords: boolean
  count: number
  results: GbifSpeciesSummary[]
}

export interface GbifMediaItem {
  type: string
  identifier: string
  title?: string
  creator?: string
  license?: string
}

export interface GbifMediaResponse {
  results: GbifMediaItem[]
}

export interface GbifVernacularName {
  vernacularName: string
  language: string
  source?: string
}

export interface GbifVernacularNamesResponse {
  results: GbifVernacularName[]
}

// --- Fetch functions ---

export async function searchSpecies(
  offset = 0,
  limit = 20,
): Promise<GbifSearchResponse> {
  const params = new URLSearchParams({
    rank: 'SPECIES',
    highertaxon_key: '6',
    status: 'ACCEPTED',
    limit: String(limit),
    offset: String(offset),
  })
  const res = await fetch(`${BASE_URL}/species/search?${params}`)
  if (!res.ok) throw new Error(`GBIF search failed: ${res.status}`)
  return res.json()
}

export async function getSpecies(key: number): Promise<GbifSpeciesDetail> {
  const res = await fetch(`${BASE_URL}/species/${key}`)
  if (!res.ok) throw new Error(`GBIF species ${key} failed: ${res.status}`)
  return res.json()
}

export async function getSpeciesMedia(key: number): Promise<GbifMediaResponse> {
  const res = await fetch(`${BASE_URL}/species/${key}/media`)
  if (!res.ok) throw new Error(`GBIF media ${key} failed: ${res.status}`)
  return res.json()
}

export async function getVernacularNames(
  key: number,
): Promise<GbifVernacularNamesResponse> {
  const res = await fetch(`${BASE_URL}/species/${key}/vernacularNames`)
  if (!res.ok) throw new Error(`GBIF names ${key} failed: ${res.status}`)
  return res.json()
}
```

- [ ] **Step 2: Commit**

```bash
mkdir -p src/api
git add src/api/gbif.ts
git commit -m "feat: add typed GBIF Species API client"
```

---

### Task 9: Species List Composable + Page

**Files:**
- Create: `src/composables/useSpeciesList.ts`
- Create: `src/components/SpeciesCard.vue`
- Modify: `src/pages/species/index.vue`

- [ ] **Step 1: Create src/composables/useSpeciesList.ts**

```typescript
import { computed, type Ref } from 'vue'
import { keepPreviousData, useQuery, useQueryClient } from '@tanstack/vue-query'
import { searchSpecies } from '@/api/gbif'

const PAGE_SIZE = 20

export function useSpeciesList(page: Ref<number>) {
  const queryClient = useQueryClient()

  const query = useQuery({
    queryKey: computed(() => ['species', 'list', page.value]),
    queryFn: () => searchSpecies(page.value * PAGE_SIZE, PAGE_SIZE),
    placeholderData: keepPreviousData,
  })

  // Prefetch next page
  const prefetchNext = () => {
    const currentPage = page.value
    queryClient.prefetchQuery({
      queryKey: ['species', 'list', currentPage + 1],
      queryFn: () => searchSpecies((currentPage + 1) * PAGE_SIZE, PAGE_SIZE),
    })
  }

  const totalPages = computed(() => {
    const count = query.data.value?.count ?? 0
    return Math.ceil(count / PAGE_SIZE)
  })

  return {
    ...query,
    totalPages,
    prefetchNext,
    PAGE_SIZE,
  }
}
```

- [ ] **Step 2: Create src/components/SpeciesCard.vue**

```vue
<script setup lang="ts">
import type { GbifSpeciesSummary } from '@/api/gbif'
import { useQueryClient } from '@tanstack/vue-query'
import { getSpecies, getSpeciesMedia } from '@/api/gbif'

const props = defineProps<{
  species: GbifSpeciesSummary
}>()

const queryClient = useQueryClient()

function prefetchDetail() {
  queryClient.prefetchQuery({
    queryKey: ['species', 'detail', props.species.key],
    queryFn: () => getSpecies(props.species.key),
  })
  queryClient.prefetchQuery({
    queryKey: ['species', 'media', props.species.key],
    queryFn: () => getSpeciesMedia(props.species.key),
  })
}
</script>

<template>
  <RouterLink
    :to="`/species/${species.key}`"
    class="block rounded-lg border border-surface-dark p-4 hover:border-primary hover:shadow-sm"
    @mouseenter="prefetchDetail"
  >
    <h3 class="font-medium italic">
      {{ species.canonicalName }}
    </h3>
    <p class="mt-1 text-xs text-text-muted">
      {{ species.family }} · {{ species.genus }}
    </p>
  </RouterLink>
</template>
```

- [ ] **Step 3: Replace src/pages/species/index.vue**

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { useSpeciesList } from '@/composables/useSpeciesList'
import SpeciesCard from '@/components/SpeciesCard.vue'

const page = ref(0)
const { data, isPending, isError, error, refetch, totalPages, prefetchNext } =
  useSpeciesList(page)
</script>

<template>
  <div>
    <h1 class="mb-6 text-2xl font-bold">
      Species Explorer
    </h1>

    <div
      v-if="isPending"
      class="text-text-muted"
    >
      Loading species...
    </div>

    <div
      v-else-if="isError"
      class="text-red-600"
    >
      <p>Error: {{ error?.message }}</p>
      <button
        class="mt-2 rounded bg-primary px-3 py-1 text-sm text-white"
        @click="() => refetch()"
      >
        Retry
      </button>
    </div>

    <template v-else>
      <div class="mb-4 text-sm text-text-muted">
        {{ data?.count?.toLocaleString() }} species found
      </div>

      <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <SpeciesCard
          v-for="species in data?.results"
          :key="species.key"
          :species="species"
        />
      </div>

      <div class="mt-6 flex items-center gap-4">
        <button
          :disabled="page === 0"
          class="rounded border px-3 py-1 text-sm disabled:opacity-40"
          @click="page--"
        >
          Previous
        </button>
        <span class="text-sm text-text-muted">
          Page {{ page + 1 }} of {{ totalPages }}
        </span>
        <button
          :disabled="data?.endOfRecords"
          class="rounded border px-3 py-1 text-sm disabled:opacity-40"
          @click="page++; prefetchNext()"
        >
          Next
        </button>
      </div>
    </template>
  </div>
</template>
```

- [ ] **Step 4: Commit**

```bash
mkdir -p src/composables
git add src/composables/useSpeciesList.ts src/components/SpeciesCard.vue src/pages/species/index.vue
git commit -m "feat: add species list with paginated TanStack Query"
```

---

### Task 10: Species Detail Composables + Page

**Files:**
- Create: `src/composables/useSpeciesDetail.ts`
- Create: `src/composables/useSpeciesMedia.ts`
- Create: `src/composables/useVernacularNames.ts`
- Modify: `src/pages/species/[id].vue`

- [ ] **Step 1: Create src/composables/useSpeciesDetail.ts**

```typescript
import { computed, type Ref } from 'vue'
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import { getSpecies, type GbifSpeciesSummary } from '@/api/gbif'

export function useSpeciesDetail(id: Ref<number>) {
  const queryClient = useQueryClient()

  return useQuery({
    queryKey: computed(() => ['species', 'detail', id.value]),
    queryFn: () => getSpecies(id.value),
    initialData: () => {
      // Try to populate from list cache
      const queries = queryClient.getQueriesData<{ results: GbifSpeciesSummary[] }>({
        queryKey: ['species', 'list'],
      })
      for (const [, data] of queries) {
        const match = data?.results.find((s) => s.key === id.value)
        if (match) return match as ReturnType<typeof getSpecies> extends Promise<infer T> ? T : never
      }
      return undefined
    },
  })
}
```

- [ ] **Step 2: Create src/composables/useSpeciesMedia.ts**

```typescript
import { computed, type Ref } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { getSpeciesMedia } from '@/api/gbif'

export function useSpeciesMedia(id: Ref<number>, enabled: Ref<boolean>) {
  return useQuery({
    queryKey: computed(() => ['species', 'media', id.value]),
    queryFn: () => getSpeciesMedia(id.value),
    enabled,
  })
}
```

- [ ] **Step 3: Create src/composables/useVernacularNames.ts**

```typescript
import { computed, type Ref } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { getVernacularNames } from '@/api/gbif'

export function useVernacularNames(id: Ref<number>, enabled: Ref<boolean>) {
  return useQuery({
    queryKey: computed(() => ['species', 'vernacular', id.value]),
    queryFn: () => getVernacularNames(id.value),
    enabled,
  })
}
```

- [ ] **Step 4: Replace src/pages/species/[id].vue**

```vue
<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useSpeciesDetail } from '@/composables/useSpeciesDetail'
import { useSpeciesMedia } from '@/composables/useSpeciesMedia'
import { useVernacularNames } from '@/composables/useVernacularNames'

const route = useRoute()
const id = computed(() => Number(route.params.id))

const { data: species, isPending, isError, error, refetch } = useSpeciesDetail(id)

const detailLoaded = computed(() => !!species.value)
const { data: media } = useSpeciesMedia(id, detailLoaded)
const { data: names } = useVernacularNames(id, detailLoaded)

const frenchName = computed(() =>
  names.value?.results.find((n) => n.language === 'fra')?.vernacularName,
)
const englishName = computed(() =>
  names.value?.results.find((n) => n.language === 'eng')?.vernacularName,
)
const firstImage = computed(() =>
  media.value?.results.find((m) => m.type === 'StillImage')?.identifier,
)
</script>

<template>
  <div>
    <RouterLink
      to="/species"
      class="mb-4 inline-block text-sm text-primary hover:underline"
    >
      &larr; Back to list
    </RouterLink>

    <div
      v-if="isPending"
      class="text-text-muted"
    >
      Loading species...
    </div>

    <div
      v-else-if="isError"
      class="text-red-600"
    >
      <p>Error: {{ error?.message }}</p>
      <button
        class="mt-2 rounded bg-primary px-3 py-1 text-sm text-white"
        @click="() => refetch()"
      >
        Retry
      </button>
    </div>

    <template v-else-if="species">
      <h1 class="mb-1 text-2xl font-bold italic">
        {{ species.canonicalName }}
      </h1>

      <div
        v-if="frenchName || englishName"
        class="mb-4 text-text-muted"
      >
        {{ frenchName ?? englishName }}
      </div>

      <div class="mb-6 flex flex-wrap gap-2 text-xs text-text-muted">
        <span>{{ species.kingdom }}</span>
        <span>&rsaquo;</span>
        <span>{{ species.phylum }}</span>
        <span>&rsaquo;</span>
        <span>{{ species.class }}</span>
        <span>&rsaquo;</span>
        <span>{{ species.order }}</span>
        <span>&rsaquo;</span>
        <span>{{ species.family }}</span>
        <span>&rsaquo;</span>
        <span class="font-medium">{{ species.genus }}</span>
      </div>

      <img
        v-if="firstImage"
        :src="firstImage"
        :alt="species.canonicalName"
        class="mb-6 max-h-80 rounded-lg object-cover"
      >

      <dl class="grid grid-cols-2 gap-2 text-sm">
        <dt class="text-text-muted">
          Author
        </dt>
        <dd>{{ species.authorship }}</dd>
        <dt class="text-text-muted">
          Status
        </dt>
        <dd>{{ species.taxonomicStatus }}</dd>
        <template v-if="species.publishedIn">
          <dt class="text-text-muted">
            Published in
          </dt>
          <dd>{{ species.publishedIn }}</dd>
        </template>
      </dl>
    </template>
  </div>
</template>
```

- [ ] **Step 5: Commit**

```bash
git add src/composables/useSpeciesDetail.ts src/composables/useSpeciesMedia.ts src/composables/useVernacularNames.ts src/pages/species/\[id\].vue
git commit -m "feat: add species detail with dependent queries and initialData"
```

---

### Task 11: Fetch Script for Local Dataset

**Files:**
- Create: `scripts/fetch-species.ts`

- [ ] **Step 1: Create scripts/fetch-species.ts**

```typescript
import { writeFileSync, mkdirSync } from 'node:fs'
import { resolve } from 'node:path'
import type { GbifSpeciesSummary } from '../src/api/gbif'

const BASE_URL = 'https://api.gbif.org/v1'
const OUTPUT = resolve(import.meta.dirname, '../public/data/species-3000.json')
const LIMIT = 1000
const PAGES = 3
const DELAY_MS = 100

async function fetchPage(offset: number): Promise<GbifSpeciesSummary[]> {
  const params = new URLSearchParams({
    rank: 'SPECIES',
    highertaxon_key: '6',
    status: 'ACCEPTED',
    limit: String(LIMIT),
    offset: String(offset),
  })
  const res = await fetch(`${BASE_URL}/species/search?${params}`)
  if (!res.ok) throw new Error(`GBIF failed: ${res.status}`)
  const data = await res.json()
  return data.results.map((r: Record<string, unknown>) => ({
    key: r.key,
    scientificName: r.scientificName,
    canonicalName: r.canonicalName,
    kingdom: r.kingdom,
    phylum: r.phylum,
    class: r.class,
    order: r.order,
    family: r.family,
    genus: r.genus,
    taxonomicStatus: r.taxonomicStatus,
    rank: r.rank,
  }))
}

async function main() {
  const all: SpeciesSummary[] = []

  for (let i = 0; i < PAGES; i++) {
    console.log(`Fetching page ${i + 1}/${PAGES} (offset=${i * LIMIT})...`)
    const page = await fetchPage(i * LIMIT)
    all.push(...page)
    if (i < PAGES - 1) {
      await new Promise((r) => setTimeout(r, DELAY_MS))
    }
  }

  mkdirSync(resolve(import.meta.dirname, '../public/data'), { recursive: true })
  writeFileSync(OUTPUT, JSON.stringify(all, null, 2))
  console.log(`Wrote ${all.length} species to ${OUTPUT}`)
}

main().catch((e) => {
  console.error(e)
  process.exit(1)
})
```

- [ ] **Step 2: Add script to package.json**

Add to `scripts`:
```json
"fetch-data": "tsx scripts/fetch-species.ts"
```

- [ ] **Step 3: Run to generate dataset**

Run: `pnpm fetch-data`
Expected: `Wrote 3000 species to .../public/data/species-3000.json`

- [ ] **Step 4: Add data file to .gitignore (optional — large file)**

Add to `.gitignore`:
```
# Large generated dataset — regenerate with `pnpm fetch-data`
# public/data/species-3000.json
```

Note: Decide whether to commit the JSON (convenient for offline dev) or gitignore it (smaller repo). Either is fine.

- [ ] **Step 5: Commit**

```bash
pnpm add -D tsx
mkdir -p scripts
git add scripts/fetch-species.ts package.json pnpm-lock.yaml public/data/species-3000.json
git commit -m "feat: add GBIF fetch script and 3000-species dataset"
```

---

### Task 12: Netlify Config

**Files:**
- Create: `netlify.toml`
- Create: `public/version` (placeholder)

- [ ] **Step 1: Create netlify.toml**

```toml
[build]
  command = "pnpm build"
  publish = "dist"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200

[[headers]]
  for = "/assets/*"
  [headers.values]
    Cache-Control = "public, max-age=31536000, immutable"
```

- [ ] **Step 2: Create public/version placeholder**

```bash
echo "dev" > public/version
```

- [ ] **Step 3: Commit**

```bash
git add netlify.toml public/version
git commit -m "setup: add Netlify config with SPA fallback and immutable caching"
```

---

### Task 13: CLAUDE.md for AI Context

**Files:**
- Create: `CLAUDE.md`

- [ ] **Step 1: Create CLAUDE.md**

```markdown
# Vue Playground

Botanical data explorer built with Vue 3, showcasing performance patterns for blog posts.

## Stack

- **Runtime**: Vue 3.5+ / TypeScript 5.8+ / Vite 7
- **Routing**: Vue Router 4.5+ with file-based routing (Unplugin Vue Router) — pages in `src/pages/`
- **Server state**: TanStack Query (`@tanstack/vue-query`) — no Pinia
- **Styling**: Tailwind CSS v4 (CSS-first config in `src/assets/main.css`)
- **Linting**: ESLint 10 flat config + @stylistic (no Prettier) — `eslint.config.ts`
- **Testing**: Vitest 4.1.0 + Vue Test Utils + happy-dom

## Commands

- `pnpm dev` — start dev server
- `pnpm build` — type-check + build
- `pnpm test` — run tests in watch mode
- `pnpm test:run` — run tests once
- `pnpm lint` / `pnpm lint:fix` — lint / auto-fix
- `pnpm fetch-data` — regenerate `public/data/species-3000.json` from GBIF

## Architecture

- `src/api/gbif.ts` — typed GBIF Species API client
- `src/composables/` — TanStack Query composables (useSpeciesList, useSpeciesDetail, etc.)
- `src/components/` — shared Vue components
- `src/pages/` — file-based routes (auto-generated by Unplugin Vue Router)
- `src/utils/` — utilities (chunk-reload handler, etc.)
- `scripts/` — build scripts (fetch-species, generate-version, analyze)
- `public/data/species-3000.json` — pre-fetched 3000-species dataset for benchmarks

## Conventions

- All packages at `@latest` unless pinned for a reason
- No Pinia — use TanStack Query for server state, `ref`/`computed` for local state
- No Prettier — ESLint Stylistic handles formatting (2 spaces, single quotes, no semicolons)
- PrimeVue is only used in `/benchmark/primevue-table` — do not import it elsewhere
- File-based routing: add pages to `src/pages/`, routes auto-generate
- Tests go in `src/**/__tests__/` or colocated as `*.test.ts`
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add CLAUDE.md for AI agent context"
```

---

### Task 14: Smoke Test

**Files:**
- Create: `src/__tests__/App.test.ts`

- [ ] **Step 1: Write smoke test**

```typescript
// src/__tests__/App.test.ts
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { VueQueryPlugin } from '@tanstack/vue-query'
import App from '../App.vue'

describe('App', () => {
  it('mounts without errors', () => {
    const wrapper = mount(App, {
      global: {
        plugins: [VueQueryPlugin],
        stubs: {
          RouterView: true,
          RouterLink: true,
          VueQueryDevtools: true,
        },
      },
    })
    expect(wrapper.text()).toContain('Vue Playground')
  })
})
```

- [ ] **Step 2: Run test**

Run: `pnpm test:run`
Expected: 1 test passes

- [ ] **Step 3: Commit**

```bash
git add src/__tests__/App.test.ts
git commit -m "test: add App smoke test"
```

---

### Task 15: Verify Everything Works

- [ ] **Step 1: Run dev server**

Run: `pnpm dev`
Expected: Vite dev server starts, no errors. Visit `http://localhost:5173/` and see the home page.

- [ ] **Step 2: Navigate all routes**

Visit:
- `/` — home with 3 cards
- `/species` — species list loads from GBIF
- `/species/<any-key>` — detail page
- `/benchmark` — benchmark hub with 3 cards
- `/about` — about page

- [ ] **Step 3: Run lint**

Run: `pnpm lint`
Expected: No errors

- [ ] **Step 4: Run tests**

Run: `pnpm test:run`
Expected: 1 test passes (App smoke test)

- [ ] **Step 5: Build**

Run: `pnpm build`
Expected: Builds successfully to `dist/`

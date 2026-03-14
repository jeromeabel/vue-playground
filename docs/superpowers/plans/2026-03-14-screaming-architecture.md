# Screaming Architecture Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reorganize the Vue playground from layer-first to feature-first folders, add Zod validation, VueUse debounce, skeleton loading, and species search.

**Architecture:** Feature folders under `src/features/{species,benchmark}` each contain their own pages, components, composables, API, and types. Shared app-wide code goes in `src/shared/`. Unplugin Vue Router scans multiple `routesFolder` entries. Zod validates at API boundaries. VueUse replaces the custom debounce composable.

**Tech Stack:** Vue 3.5+ / TypeScript 5.8+ / Vite 8 / Unplugin Vue Router / TanStack Query / Zod / VueUse / Vitest / Tailwind CSS v4

**Spec:** `docs/superpowers/specs/2026-03-14-screaming-architecture-design.md`

---

## Chunk 1: Dependencies and Species Types with Zod

### Task 1: Install new dependencies

**Files:**
- Modify: `package.json`

- [ ] **Step 1: Install @vueuse/core and zod**

```bash
pnpm add @vueuse/core zod
```

- [ ] **Step 2: Verify installation**

```bash
pnpm ls @vueuse/core zod
```

Expected: both packages listed with versions.

- [ ] **Step 3: Commit**

```bash
git add package.json pnpm-lock.yaml
git commit -m "chore: add @vueuse/core and zod dependencies"
```

---

### Task 2: Create species Zod schemas and inferred types

**Files:**
- Create: `src/features/species/types.ts`
- Test: `src/features/species/__tests__/types.test.ts`

- [ ] **Step 1: Write the failing test**

```ts
// src/features/species/__tests__/types.test.ts
import { describe, expect, it } from "vitest"

import {
    GbifMediaResponseSchema,
    GbifSearchResponseSchema,
    GbifSpeciesDetailSchema,
    GbifSpeciesSummarySchema,
    GbifVernacularNamesResponseSchema,
} from "../types"

describe("GbifSpeciesSummarySchema", () => {
    const validSummary = {
        key: 12345,
        scientificName: "Quercus robur L.",
        canonicalName: "Quercus robur",
        kingdom: "Plantae",
        phylum: "Tracheophyta",
        class: "Magnoliopsida",
        order: "Fagales",
        family: "Fagaceae",
        genus: "Quercus",
        taxonomicStatus: "ACCEPTED",
        rank: "SPECIES",
        vernacularNames: [{ vernacularName: "English Oak", language: "eng" }],
    }

    it("parses valid species data", () => {
        const result = GbifSpeciesSummarySchema.parse(validSummary)
        expect(result.key).toBe(12345)
        expect(result.canonicalName).toBe("Quercus robur")
    })

    it("defaults vernacularNames to empty array when missing", () => {
        const { vernacularNames: _, ...withoutNames } = validSummary
        const result = GbifSpeciesSummarySchema.parse(withoutNames)
        expect(result.vernacularNames).toEqual([])
    })

    it("rejects data with missing required fields", () => {
        expect(() => GbifSpeciesSummarySchema.parse({ key: 1 })).toThrow()
    })
})

describe("GbifSpeciesDetailSchema", () => {
    it("extends summary with detail fields", () => {
        const detail = {
            key: 1,
            scientificName: "Quercus robur L.",
            canonicalName: "Quercus robur",
            kingdom: "Plantae",
            phylum: "Tracheophyta",
            class: "Magnoliopsida",
            order: "Fagales",
            family: "Fagaceae",
            genus: "Quercus",
            taxonomicStatus: "ACCEPTED",
            rank: "SPECIES",
            vernacularNames: [],
            authorship: "L.",
            nameType: "SCIENTIFIC",
            numDescendants: 0,
        }
        const result = GbifSpeciesDetailSchema.parse(detail)
        expect(result.authorship).toBe("L.")
        expect(result.publishedIn).toBeUndefined()
    })
})

describe("GbifSearchResponseSchema", () => {
    it("parses search response with results array", () => {
        const response = {
            offset: 0,
            limit: 20,
            endOfRecords: false,
            count: 100,
            results: [{
                key: 1,
                scientificName: "Quercus robur L.",
                canonicalName: "Quercus robur",
                kingdom: "Plantae",
                phylum: "Tracheophyta",
                class: "Magnoliopsida",
                order: "Fagales",
                family: "Fagaceae",
                genus: "Quercus",
                taxonomicStatus: "ACCEPTED",
                rank: "SPECIES",
                vernacularNames: [],
            }],
        }
        const result = GbifSearchResponseSchema.parse(response)
        expect(result.count).toBe(100)
        expect(result.results).toHaveLength(1)
    })
})

describe("GbifMediaResponseSchema", () => {
    it("parses media response", () => {
        const response = {
            results: [{ type: "StillImage", identifier: "https://example.com/img.jpg" }],
        }
        const result = GbifMediaResponseSchema.parse(response)
        expect(result.results[0].type).toBe("StillImage")
    })
})

describe("GbifVernacularNamesResponseSchema", () => {
    it("parses vernacular names response", () => {
        const response = {
            results: [{ vernacularName: "Oak", language: "eng" }],
        }
        const result = GbifVernacularNamesResponseSchema.parse(response)
        expect(result.results[0].vernacularName).toBe("Oak")
    })
})
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pnpm vitest run src/features/species/__tests__/types.test.ts
```

Expected: FAIL — cannot find module `../types`.

- [ ] **Step 3: Write the implementation**

```ts
// src/features/species/types.ts
import { z } from "zod"

const VernacularNameSchema = z.object({
    vernacularName: z.string(),
    language: z.string(),
})

export const GbifSpeciesSummarySchema = z.object({
    key: z.number(),
    scientificName: z.string(),
    canonicalName: z.string(),
    kingdom: z.string(),
    phylum: z.string(),
    class: z.string(),
    order: z.string(),
    family: z.string(),
    genus: z.string(),
    taxonomicStatus: z.string(),
    rank: z.string(),
    vernacularNames: z.array(VernacularNameSchema).default([]),
})

export type GbifSpeciesSummary = z.infer<typeof GbifSpeciesSummarySchema>

export const GbifSpeciesDetailSchema = GbifSpeciesSummarySchema.extend({
    authorship: z.string(),
    publishedIn: z.string().optional(),
    nameType: z.string(),
    numDescendants: z.number(),
})

export type GbifSpeciesDetail = z.infer<typeof GbifSpeciesDetailSchema>

export const GbifSearchResponseSchema = z.object({
    offset: z.number(),
    limit: z.number(),
    endOfRecords: z.boolean(),
    count: z.number(),
    results: z.array(GbifSpeciesSummarySchema),
})

export type GbifSearchResponse = z.infer<typeof GbifSearchResponseSchema>

export const GbifMediaItemSchema = z.object({
    type: z.string(),
    identifier: z.string(),
    title: z.string().optional(),
    creator: z.string().optional(),
    license: z.string().optional(),
})

export type GbifMediaItem = z.infer<typeof GbifMediaItemSchema>

export const GbifMediaResponseSchema = z.object({
    results: z.array(GbifMediaItemSchema),
})

export type GbifMediaResponse = z.infer<typeof GbifMediaResponseSchema>

export const GbifVernacularNameSchema = z.object({
    vernacularName: z.string(),
    language: z.string(),
    source: z.string().optional(),
})

export type GbifVernacularName = z.infer<typeof GbifVernacularNameSchema>

export const GbifVernacularNamesResponseSchema = z.object({
    results: z.array(GbifVernacularNameSchema),
})

export type GbifVernacularNamesResponse = z.infer<typeof GbifVernacularNamesResponseSchema>
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pnpm vitest run src/features/species/__tests__/types.test.ts
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/features/species/types.ts src/features/species/__tests__/types.test.ts
git commit -m "feat(species): add Zod schemas and inferred types for GBIF API"
```

---

### Task 3: Create species API with Zod validation

**Files:**
- Create: `src/features/species/api.ts`
- Test: `src/features/species/__tests__/api.test.ts`

- [ ] **Step 1: Write the failing test**

```ts
// src/features/species/__tests__/api.test.ts
import { afterEach, describe, expect, it, vi } from "vitest"

import { getSpecies, getSpeciesMedia, getVernacularNames, searchSpecies } from "../api"

const mockFetch = vi.fn()
vi.stubGlobal("fetch", mockFetch)

afterEach(() => {
    vi.clearAllMocks()
})

describe("searchSpecies", () => {
    const validResponse = {
        offset: 0,
        limit: 20,
        endOfRecords: false,
        count: 1,
        results: [{
            key: 1,
            scientificName: "Quercus robur L.",
            canonicalName: "Quercus robur",
            kingdom: "Plantae",
            phylum: "Tracheophyta",
            class: "Magnoliopsida",
            order: "Fagales",
            family: "Fagaceae",
            genus: "Quercus",
            taxonomicStatus: "ACCEPTED",
            rank: "SPECIES",
            vernacularNames: [],
        }],
    }

    it("calls the correct endpoint with default params", async () => {
        mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(validResponse) })
        await searchSpecies()

        const url = new URL(mockFetch.mock.calls[0][0])
        expect(url.pathname).toBe("/v1/species/search")
        expect(url.searchParams.get("offset")).toBe("0")
        expect(url.searchParams.get("limit")).toBe("20")
        expect(url.searchParams.has("q")).toBe(false)
    })

    it("passes query parameter when provided", async () => {
        mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(validResponse) })
        await searchSpecies(0, 20, "quercus")

        const url = new URL(mockFetch.mock.calls[0][0])
        expect(url.searchParams.get("q")).toBe("quercus")
    })

    it("validates response with Zod", async () => {
        mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({ bad: "data" }) })
        await expect(searchSpecies()).rejects.toThrow()
    })

    it("throws on non-OK response", async () => {
        mockFetch.mockResolvedValueOnce({ ok: false, status: 500 })
        await expect(searchSpecies()).rejects.toThrow("GBIF search failed: 500")
    })
})

describe("getSpecies", () => {
    it("calls the correct endpoint", async () => {
        const detail = {
            key: 42,
            scientificName: "Quercus robur L.",
            canonicalName: "Quercus robur",
            kingdom: "Plantae",
            phylum: "Tracheophyta",
            class: "Magnoliopsida",
            order: "Fagales",
            family: "Fagaceae",
            genus: "Quercus",
            taxonomicStatus: "ACCEPTED",
            rank: "SPECIES",
            vernacularNames: [],
            authorship: "L.",
            nameType: "SCIENTIFIC",
            numDescendants: 0,
        }
        mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(detail) })
        const result = await getSpecies(42)

        expect(mockFetch.mock.calls[0][0]).toContain("/v1/species/42")
        expect(result.authorship).toBe("L.")
    })
})

describe("getSpeciesMedia", () => {
    it("calls the correct endpoint", async () => {
        const media = { results: [{ type: "StillImage", identifier: "https://example.com/img.jpg" }] }
        mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(media) })
        const result = await getSpeciesMedia(42)

        expect(mockFetch.mock.calls[0][0]).toContain("/v1/species/42/media")
        expect(result.results[0].type).toBe("StillImage")
    })
})

describe("getVernacularNames", () => {
    it("calls the correct endpoint", async () => {
        const names = { results: [{ vernacularName: "Oak", language: "eng" }] }
        mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(names) })
        const result = await getVernacularNames(42)

        expect(mockFetch.mock.calls[0][0]).toContain("/v1/species/42/vernacularNames")
        expect(result.results[0].vernacularName).toBe("Oak")
    })
})
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pnpm vitest run src/features/species/__tests__/api.test.ts
```

Expected: FAIL — cannot find module `../api`.

- [ ] **Step 3: Write the implementation**

```ts
// src/features/species/api.ts
import {
    GbifMediaResponseSchema,
    GbifSearchResponseSchema,
    GbifSpeciesDetailSchema,
    GbifVernacularNamesResponseSchema,
} from "./types"

const BASE_URL = "https://api.gbif.org/v1"

export async function searchSpecies(offset = 0, limit = 20, query?: string) {
    const params = new URLSearchParams({
        rank: "SPECIES",
        highertaxon_key: "6",
        status: "ACCEPTED",
        limit: String(limit),
        offset: String(offset),
        ...(query ? { q: query } : {}),
    })

    const res = await fetch(`${BASE_URL}/species/search?${params}`)
    if (!res.ok) {
        throw new Error(`GBIF search failed: ${res.status}`)
    }

    return GbifSearchResponseSchema.parse(await res.json())
}

export async function getSpecies(key: number) {
    const res = await fetch(`${BASE_URL}/species/${key}`)
    if (!res.ok) {
        throw new Error(`GBIF species ${key} failed: ${res.status}`)
    }

    return GbifSpeciesDetailSchema.parse(await res.json())
}

export async function getSpeciesMedia(key: number) {
    const res = await fetch(`${BASE_URL}/species/${key}/media`)
    if (!res.ok) {
        throw new Error(`GBIF media ${key} failed: ${res.status}`)
    }

    return GbifMediaResponseSchema.parse(await res.json())
}

export async function getVernacularNames(key: number) {
    const res = await fetch(`${BASE_URL}/species/${key}/vernacularNames`)
    if (!res.ok) {
        throw new Error(`GBIF names ${key} failed: ${res.status}`)
    }

    return GbifVernacularNamesResponseSchema.parse(await res.json())
}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pnpm vitest run src/features/species/__tests__/api.test.ts
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/features/species/api.ts src/features/species/__tests__/api.test.ts
git commit -m "feat(species): add API client with Zod validation"
```

---

## Chunk 2: Move Species Feature Files

> **Important:** Tasks 4 through 7 move files and update imports. The app will NOT compile between these tasks because some files still reference old paths. This is expected — Task 8 brings everything back to a compilable state with the Vite config update. If you prefer, Tasks 4-7 can be squashed into a single commit.

### Task 4: Move species composables

**Files:**
- Move: `src/composables/use-species-list.ts` → `src/features/species/composables/use-species-list.ts`
- Move: `src/composables/use-species-detail.ts` → `src/features/species/composables/use-species-detail.ts`
- Move: `src/composables/use-species-media.ts` → `src/features/species/composables/use-species-media.ts`
- Move: `src/composables/use-vernacular-names.ts` → `src/features/species/composables/use-vernacular-names.ts`

- [ ] **Step 1: Create directory and move files**

```bash
mkdir -p src/features/species/composables
mv src/composables/use-species-list.ts src/features/species/composables/
mv src/composables/use-species-detail.ts src/features/species/composables/
mv src/composables/use-species-media.ts src/features/species/composables/
mv src/composables/use-vernacular-names.ts src/features/species/composables/
```

- [ ] **Step 2: Update imports in all four composables**

Each file currently imports from `@/api/gbif`. Update to use the new relative paths:

**`src/features/species/composables/use-species-list.ts`:**
```ts
// Change: import { searchSpecies } from "@/api/gbif"
// To:
import { searchSpecies } from "../api"
```

**`src/features/species/composables/use-species-detail.ts`:**
```ts
// Change: import { getSpecies, type GbifSpeciesSummary } from "@/api/gbif"
// To:
import { getSpecies } from "../api"
import type { GbifSpeciesSummary } from "../types"
```

**`src/features/species/composables/use-species-media.ts`:**
```ts
// Change: import { getSpeciesMedia } from "@/api/gbif"
// To:
import { getSpeciesMedia } from "../api"
```

**`src/features/species/composables/use-vernacular-names.ts`:**
```ts
// Change: import { getVernacularNames } from "@/api/gbif"
// To:
import { getVernacularNames } from "../api"
```

- [ ] **Step 3: Verify types compile**

```bash
pnpm vue-tsc --noEmit -p tsconfig.app.json 2>&1 | head -20
```

Note: There will be errors from files still referencing old paths. That's expected — we fix them in later tasks.

- [ ] **Step 4: Commit**

```bash
git add src/features/species/composables/ src/composables/use-species-list.ts src/composables/use-species-detail.ts src/composables/use-species-media.ts src/composables/use-vernacular-names.ts
git commit -m "refactor(species): move composables into feature folder"
```

---

### Task 5: Move species component and pages

**Files:**
- Move: `src/components/species-card.vue` → `src/features/species/components/species-card.vue`
- Move: `src/pages/species/index.vue` → `src/features/species/pages/index.vue`
- Move: `src/pages/species/[id].vue` → `src/features/species/pages/[id].vue`

- [ ] **Step 1: Create directories and move files**

```bash
mkdir -p src/features/species/components
mkdir -p src/features/species/pages
mv src/components/species-card.vue src/features/species/components/
mv src/pages/species/index.vue src/features/species/pages/
mv src/pages/species/\[id\].vue src/features/species/pages/
rmdir src/pages/species
```

- [ ] **Step 2: Update imports in species-card.vue**

```ts
// Change:
// import { getSpecies, getSpeciesMedia, type GbifSpeciesSummary } from "@/api/gbif"
// To:
import { getSpecies, getSpeciesMedia } from "../api"
import type { GbifSpeciesSummary } from "../types"
```

- [ ] **Step 3: Update imports in species pages/index.vue**

```ts
// Change:
// import SpeciesCard from "@/components/species-card.vue"
// import { useSpeciesList } from "@/composables/use-species-list"
// To:
import SpeciesCard from "../components/species-card.vue"
import { useSpeciesList } from "../composables/use-species-list"
```

- [ ] **Step 4: Update imports in species pages/[id].vue**

```ts
// Change:
// import { useSpeciesDetail } from "@/composables/use-species-detail"
// import { useSpeciesMedia } from "@/composables/use-species-media"
// import { useVernacularNames } from "@/composables/use-vernacular-names"
// To:
import { useSpeciesDetail } from "../composables/use-species-detail"
import { useSpeciesMedia } from "../composables/use-species-media"
import { useVernacularNames } from "../composables/use-vernacular-names"
```

- [ ] **Step 5: Commit**

```bash
git add src/features/species/components/ src/features/species/pages/ src/components/species-card.vue src/pages/species/
git commit -m "refactor(species): move component and pages into feature folder"
```

---

## Chunk 3: Move Benchmark Feature Files

### Task 6: Move benchmark composables, component, and pages

**Files:**
- Move: `src/composables/use-dom-metrics.ts` → `src/features/benchmark/composables/use-dom-metrics.ts`
- Move: `src/composables/__tests__/use-dom-metrics.test.ts` → `src/features/benchmark/composables/__tests__/use-dom-metrics.test.ts`
- Move: `src/components/metrics-panel.vue` → `src/features/benchmark/components/metrics-panel.vue`
- Move: `src/pages/benchmark/*.vue` → `src/features/benchmark/pages/`
- Create: `src/features/benchmark/types.ts`

- [ ] **Step 1: Create directories and move files**

```bash
mkdir -p src/features/benchmark/composables/__tests__
mkdir -p src/features/benchmark/components
mkdir -p src/features/benchmark/pages
mv src/composables/use-dom-metrics.ts src/features/benchmark/composables/
mv src/composables/__tests__/use-dom-metrics.test.ts src/features/benchmark/composables/__tests__/
mv src/components/metrics-panel.vue src/features/benchmark/components/
mv src/pages/benchmark/index.vue src/features/benchmark/pages/
mv src/pages/benchmark/basic-table.vue src/features/benchmark/pages/
mv src/pages/benchmark/primevue-table.vue src/features/benchmark/pages/
mv src/pages/benchmark/tanstack-table.vue src/features/benchmark/pages/
rmdir src/pages/benchmark
```

- [ ] **Step 2: Create benchmark types file**

```ts
// src/features/benchmark/types.ts
import type { GbifSpeciesSummary } from "@/features/species/types"

export type BenchmarkedSpecies = GbifSpeciesSummary & { benchmarkOrder: number }
```

- [ ] **Step 3: Update imports in all three benchmark table pages**

For each of `basic-table.vue`, `primevue-table.vue`, `tanstack-table.vue`:

```ts
// Change:
// import type { GbifSpeciesSummary } from "@/api/gbif"
// import MetricsPanel from "@/components/metrics-panel.vue"
// import { useDomMetrics } from "@/composables/use-dom-metrics"
// import { useDebounce } from "@/composables/use-debounce"
// type BenchmarkedSpecies = GbifSpeciesSummary & { benchmarkOrder: number }
// To:
import { refDebounced } from "@vueuse/core"
import type { GbifSpeciesSummary } from "@/features/species/types"
import MetricsPanel from "../components/metrics-panel.vue"
import { useDomMetrics } from "../composables/use-dom-metrics"
import type { BenchmarkedSpecies } from "../types"
```

Also in each page, change the debounce call:

```ts
// Change: const query = useDebounce(searchInput, 300)
// To:     const query = refDebounced(searchInput, 300)
```

Remove the inline `type BenchmarkedSpecies` definition from each page.

Keep the `vernacularNames: item.vernacularNames ?? []` fallback — benchmark pages load from static JSON (not Zod-validated), so the fallback is still needed. The `GbifSpeciesSummary` import (now type-only from species) is only used for type-casting the JSON, not for Zod parsing.

- [ ] **Step 4: Run the existing dom-metrics test to verify it still passes**

```bash
pnpm vitest run src/features/benchmark/composables/__tests__/use-dom-metrics.test.ts
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/features/benchmark/ src/composables/use-dom-metrics.ts src/composables/__tests__/ src/components/metrics-panel.vue src/pages/benchmark/
git commit -m "refactor(benchmark): move all benchmark files into feature folder"
```

---

### Task 7: Move shared component, clean up dead files, update app shell

**Files:**
- Move: `src/components/app-header.vue` → `src/shared/components/app-header.vue`
- Modify: `src/app.vue`
- Modify: `src/app.spec.ts`
- Delete: `src/composables/use-debounce.ts`
- Delete: `src/api/gbif.ts`
- Delete: `src/router/index.ts`
- Delete: `src/pages/home-page.vue`
- Delete: `src/__tests__/app.test.ts`

- [ ] **Step 1: Move app-header to shared**

```bash
mkdir -p src/shared/components
mv src/components/app-header.vue src/shared/components/
```

- [ ] **Step 2: Update app.vue import**

```ts
// Change: import AppHeader from "@/components/app-header.vue"
// To:
import AppHeader from "@/shared/components/app-header.vue"
```

- [ ] **Step 3: Update app.spec.ts — remove dead home-page.vue import**

Replace the entire `app.spec.ts` with:

```ts
// src/app.spec.ts
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
```

- [ ] **Step 4: Delete dead files**

```bash
rm src/composables/use-debounce.ts
rm src/api/gbif.ts
rmdir src/api
rm src/router/index.ts
rmdir src/router
rm src/pages/home-page.vue
rm src/__tests__/app.test.ts
rmdir src/__tests__
rmdir src/composables/__tests__ 2>/dev/null || true
rmdir src/composables 2>/dev/null || true
rmdir src/components 2>/dev/null || true
```

- [ ] **Step 5: Verify app.spec.ts passes**

```bash
pnpm vitest run src/app.spec.ts
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "refactor: move shared components, clean up dead files and legacy code"
```

---

## Chunk 4: Vite Router Config and Verification

### Task 8: Update Vite routesFolder configuration

**Files:**
- Modify: `vite.config.ts`

- [ ] **Step 1: Update routesFolder to scan feature folders**

Change `vite.config.ts`:

```ts
// Change:
// VueRouter({
//     routesFolder: "src/pages",
//     ...
// }),
// To:
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
```

- [ ] **Step 2: Run type check**

```bash
pnpm vue-tsc --noEmit -p tsconfig.app.json
```

Expected: no errors (or only pre-existing ones unrelated to this change).

- [ ] **Step 3: Run all tests**

```bash
pnpm vitest run
```

Expected: all tests PASS.

- [ ] **Step 4: Start dev server and verify routes**

```bash
pnpm dev &
sleep 3
curl -s http://localhost:5173/species | head -5
curl -s http://localhost:5173/benchmark | head -5
curl -s http://localhost:5173/ | head -5
kill %1
```

Expected: each URL returns HTML (the SPA shell).

- [ ] **Step 5: Run build**

```bash
pnpm build
```

Expected: build succeeds without errors.

- [ ] **Step 6: Commit**

```bash
git add vite.config.ts typed-router.d.ts
git commit -m "feat: configure multi-folder file-based routing for feature architecture"
```

---

## Chunk 5: Species Search Composable

### Task 9: Create use-species-search composable

**Files:**
- Create: `src/features/species/composables/use-species-search.ts`
- Test: `src/features/species/__tests__/use-species-search.test.ts`

- [ ] **Step 1: Write the failing test**

```ts
// src/features/species/__tests__/use-species-search.test.ts
import { describe, expect, it, vi } from "vitest"
import { ref } from "vue"

import { useSpeciesSearch } from "../composables/use-species-search"

// Mock the API module
vi.mock("../api", () => ({
    searchSpecies: vi.fn().mockResolvedValue({
        offset: 0,
        limit: 20,
        endOfRecords: false,
        count: 1,
        results: [],
    }),
}))

// Mock TanStack Query to avoid needing a QueryClient
vi.mock("@tanstack/vue-query", () => ({
    useQuery: vi.fn(({ enabled, queryKey }) => ({
        data: ref(null),
        isPending: ref(false),
        isError: ref(false),
        error: ref(null),
        _enabled: enabled,
        _queryKey: queryKey,
    })),
    keepPreviousData: Symbol("keepPreviousData"),
}))

describe("useSpeciesSearch", () => {
    it("returns a query object", () => {
        const rawQuery = ref("")
        const result = useSpeciesSearch(rawQuery)
        expect(result).toHaveProperty("data")
        expect(result).toHaveProperty("isPending")
    })

    it("disables query when input is empty", () => {
        const rawQuery = ref("")
        const result = useSpeciesSearch(rawQuery) as any
        // The enabled computed should resolve to false for empty input
        expect(result._enabled.value).toBe(false)
    })
})
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pnpm vitest run src/features/species/__tests__/use-species-search.test.ts
```

Expected: FAIL — cannot find module.

- [ ] **Step 3: Write the implementation**

```ts
// src/features/species/composables/use-species-search.ts
import { computed, type Ref } from "vue"
import { refDebounced } from "@vueuse/core"
import { keepPreviousData, useQuery } from "@tanstack/vue-query"

import { searchSpecies } from "../api"

export function useSpeciesSearch(rawQuery: Ref<string>) {
    const query = refDebounced(rawQuery, 300)

    return useQuery({
        queryKey: computed(() => ["species", "search", query.value]),
        queryFn: () => searchSpecies(0, 20, query.value),
        enabled: computed(() => query.value.length > 0),
        placeholderData: keepPreviousData,
    })
}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pnpm vitest run src/features/species/__tests__/use-species-search.test.ts
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/features/species/composables/use-species-search.ts src/features/species/__tests__/use-species-search.test.ts
git commit -m "feat(species): add server-side search composable with debounce"
```

---

## Chunk 6: Skeleton Components

### Task 10: Create species skeleton components

**Files:**
- Create: `src/features/species/components/species-card-skeleton.vue`
- Create: `src/features/species/components/species-detail-skeleton.vue`
- Modify: `src/features/species/pages/index.vue`
- Modify: `src/features/species/pages/[id].vue`

- [ ] **Step 1: Create species-card-skeleton.vue**

```vue
<!-- src/features/species/components/species-card-skeleton.vue -->
<template>
  <div class="block rounded-lg border border-surface-dark p-4">
    <div class="h-5 w-3/4 animate-pulse rounded bg-surface-dark" />
    <div class="mt-2 h-3 w-1/2 animate-pulse rounded bg-surface-dark/60" />
  </div>
</template>
```

- [ ] **Step 2: Create species-detail-skeleton.vue**

```vue
<!-- src/features/species/components/species-detail-skeleton.vue -->
<template>
  <div>
    <div class="mb-1 h-8 w-64 animate-pulse rounded bg-surface-dark" />
    <div class="mb-4 h-5 w-40 animate-pulse rounded bg-surface-dark/60" />
    <div class="mb-6 flex flex-wrap gap-2">
      <div
        v-for="i in 6"
        :key="i"
        class="h-4 w-20 animate-pulse rounded bg-surface-dark/40"
      />
    </div>
    <div class="mb-6 h-60 w-80 animate-pulse rounded-lg bg-surface-dark/30" />
    <div class="grid grid-cols-2 gap-2">
      <div
        v-for="i in 4"
        :key="i"
        class="h-4 animate-pulse rounded bg-surface-dark/40"
      />
    </div>
  </div>
</template>
```

- [ ] **Step 3: Update species list page to use skeleton**

In `src/features/species/pages/index.vue`, replace the loading text:

```vue
<!-- Change:
    <div v-if="isPending" class="text-text-muted">
      Loading species...
    </div>
-->
<!-- To: -->
    <div
      v-if="isPending"
      class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4"
    >
      <SpeciesCardSkeleton
        v-for="i in 8"
        :key="i"
      />
    </div>
```

Add the import:

```ts
import SpeciesCardSkeleton from "../components/species-card-skeleton.vue"
```

- [ ] **Step 4: Update species detail page to use skeleton**

In `src/features/species/pages/[id].vue`, replace the loading text:

```vue
<!-- Change:
    <div v-if="isPending" class="text-text-muted">
      Loading species...
    </div>
-->
<!-- To: -->
    <SpeciesDetailSkeleton v-if="isPending" />
```

Add the import:

```ts
import SpeciesDetailSkeleton from "../components/species-detail-skeleton.vue"
```

- [ ] **Step 5: Verify the dev server renders skeletons**

Start the dev server and visually verify that `/species` shows skeleton cards and `/species/1` shows a skeleton detail layout while loading.

- [ ] **Step 6: Commit**

```bash
git add src/features/species/components/species-card-skeleton.vue src/features/species/components/species-detail-skeleton.vue src/features/species/pages/
git commit -m "feat(species): add skeleton loading components for list and detail pages"
```

---

## Chunk 7: Final Verification

### Task 11: Full verification pass

- [ ] **Step 1: Run all tests**

```bash
pnpm vitest run
```

Expected: all tests PASS.

- [ ] **Step 2: Run linter**

```bash
pnpm lint
```

Expected: no errors (run `pnpm lint:fix` if there are auto-fixable issues).

- [ ] **Step 3: Run type check**

```bash
pnpm vue-tsc --noEmit -p tsconfig.app.json
```

Expected: no errors.

- [ ] **Step 4: Run production build**

```bash
pnpm build
```

Expected: build succeeds.

- [ ] **Step 5: Verify no old import paths remain**

```bash
# Should return no results:
grep -r '"@/api/gbif"' src/ || echo "CLEAN"
grep -r '"@/composables/' src/ || echo "CLEAN"
grep -r '"@/components/' src/ --include="*.vue" --include="*.ts" | grep -v shared || echo "CLEAN"
```

Expected: "CLEAN" for all three.

- [ ] **Step 6: Verify folder structure matches spec**

```bash
find src/features -type f | sort
find src/shared -type f | sort
find src/pages -type f | sort
```

Expected output should match the target folder structure from the spec.

- [ ] **Step 7: Commit any lint fixes**

```bash
git add -A
git status
# Only commit if there are changes from lint:fix
git diff --cached --quiet || git commit -m "style: fix lint issues from architecture migration"
```

---

## Deferred Tests

The spec's testing strategy lists tests for `use-species-list.ts`, `use-species-detail.ts`, and `species-card.vue` that are **not included in this plan**. These tests should be written in a follow-up cycle after the migration is complete and stable. The plan covers only the tests that exercise new code (Zod schemas, species API with validation, species search composable, skeleton components) to keep the migration focused.

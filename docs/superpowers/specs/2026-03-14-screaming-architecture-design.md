# Screaming Architecture: Feature-First Folder Structure

## Summary

Reorganize the Vue playground from a layer-first structure (`api/`, `composables/`, `components/`, `pages/`) to a feature-first structure where each feature folder contains its own pages, components, composables, API client, and types. The folder structure should "scream" what the app does (species explorer, benchmarks), not what tech layers it uses.

Additionally: add Zod for runtime validation at API boundaries, replace the custom `use-debounce` with VueUse's `refDebounced`, add skeleton loading components, and separate the species list/search data flows.

## Goals

- **Discoverability:** New developers find code faster by looking at feature folders.
- **Colocation:** Related code lives together — delete a folder, delete a feature.
- **Change isolation:** Modifying a feature doesn't require touching multiple layer folders.
- **Low coupling between features, high cohesion within a feature.**

## New Dependencies

### `@vueuse/core` — Replace custom `use-debounce`

VueUse's `refDebounced` is a drop-in replacement for the custom `use-debounce.ts` composable. Tree-shakeable (~2KB for this single function). Eliminates the custom composable entirely and removes the placement compromise.

```ts
// Before (custom):
import { useDebounce } from "@/composables/use-debounce"
const query = useDebounce(searchInput, 300)

// After (VueUse):
import { refDebounced } from "@vueuse/core"
const query = refDebounced(searchInput, 300)
```

The custom `src/composables/use-debounce.ts` is deleted — not moved to any feature folder.

Both `@vueuse/core` and `zod` must be added to `package.json` as dependencies (`pnpm add @vueuse/core zod`).

### `zod` — Runtime validation at API boundaries

Zod validates GBIF API responses and static JSON at runtime boundaries. If GBIF changes their API shape, the app gets a clear validation error instead of `undefined` propagating into components.

**Where it applies:**
- `src/features/species/api.ts` — validate each GBIF response against a Zod schema

**Where it does NOT apply:**
- Internal composable-to-component data flow (already typed by TypeScript)
- TanStack Query cache operations
- Benchmark static JSON (`public/data/species-10000.json`) — this is a checked-in file under project control, not an external boundary. TypeScript typing is sufficient.

**Schema location:** Zod schemas live alongside the types they validate in `src/features/species/types.ts`. The types are inferred from schemas (`z.infer<typeof SpeciesSummarySchema>`) rather than hand-written separately. All 7 current interfaces become Zod schemas:

| Current interface | Zod schema |
|---|---|
| `GbifSpeciesSummary` | `GbifSpeciesSummarySchema` |
| `GbifSpeciesDetail` | `GbifSpeciesDetailSchema` (extends `GbifSpeciesSummarySchema.extend({...})`) |
| `GbifSearchResponse` | `GbifSearchResponseSchema` |
| `GbifMediaItem` | `GbifMediaItemSchema` |
| `GbifMediaResponse` | `GbifMediaResponseSchema` |
| `GbifVernacularName` | `GbifVernacularNameSchema` |
| `GbifVernacularNamesResponse` | `GbifVernacularNamesResponseSchema` |

**Behavioral note:** The `vernacularNames` field uses `.default([])` in the schema because the GBIF API sometimes omits it (evidenced by `?? []` fallbacks in current code). With Zod, consumers no longer need the `?? []` fallback — the schema guarantees the array.

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

// ... remaining schemas follow the same pattern
```

```ts
// src/features/species/api.ts
import { GbifSearchResponseSchema } from "./types"

export async function searchSpecies(offset = 0, limit = 20, query?: string) {
  // query parameter is optional — omit for paginated list, provide for search
  const params = new URLSearchParams({
    rank: "SPECIES",
    highertaxon_key: "6",
    status: "ACCEPTED",
    limit: String(limit),
    offset: String(offset),
    ...(query ? { q: query } : {}),
  })
  const res = await fetch(`${BASE_URL}/species/search?${params}`)
  if (!res.ok) throw new Error(`GBIF search failed: ${res.status}`)
  return GbifSearchResponseSchema.parse(await res.json())
}
```

### Why NOT a Result pattern (neverthrow, Effect, Boxed)

TanStack Query already encodes the success/error/loading state for every async operation (`{ data, error, isPending }`). Wrapping API functions in a `Result<T, E>` would add a layer that TanStack Query then unwraps — indirection for no gain at this scale. If the app grows beyond TanStack Query (e.g., complex mutations, orchestration), revisit neverthrow or Boxed then.

## Features Identified

### `species` — Botanical species explorer
- Pages: list (`/species`) and detail (`/species/:id`)
- Components: `species-card`, `species-card-skeleton`, `species-detail-skeleton`
- Composables: `use-species-list`, `use-species-search`, `use-species-detail`, `use-species-media`, `use-vernacular-names`
- API: GBIF client functions (`searchSpecies`, `getSpecies`, `getSpeciesMedia`, `getVernacularNames`)
- Types/Schemas: Zod schemas + inferred types for all GBIF response shapes

### `benchmark` — Table rendering performance comparison
- Pages: index (`/benchmark`), `basic-table`, `primevue-table`, `tanstack-table`
- Components: `metrics-panel`
- Composables: `use-dom-metrics`
- Types: `BenchmarkedSpecies` in `benchmark/types.ts` — a plain TypeScript type (not a Zod schema), importing `GbifSpeciesSummary` type-only from species
- Cross-feature type import: `GbifSpeciesSummary` from species (type-only)

### `shared` — App-wide code
- Components: `app-header`

### Top-level (no feature) — App shell and generic pages
- `app.vue`, `main.ts`, `router.ts`
- Pages: `index.vue` (home), `about.vue`
- Tests: `app.spec.ts`

## Species List vs Search: Separate Data Flows

The species list and species search are architecturally distinct operations:

**Species list** — paginated, server-driven:
- Loads via `searchSpecies(offset, limit)` on page mount
- Pagination controls trigger new API calls
- Composable: `use-species-list.ts` (existing, moved)

**Species search** — server-driven, debounced:
- Triggered when the user types characters
- Calls the GBIF search API with a query parameter: `searchSpecies(offset, limit, query)`
- Debounced with VueUse's `refDebounced` to avoid excessive API calls
- Composable: `use-species-search.ts` (new)
- Returns different results than the list — filtered server-side by the query

**Benchmark search** — client-side, stays as-is:
- Filters the 10K static JSON dataset client-side
- Uses VueUse's `refDebounced` (replacing custom `useDebounce`)
- No API call, no composable — inline in each benchmark page

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

## Skeleton Loading Components

Skeleton screens replace plain "Loading..." text to improve perceived performance by showing the shape of content before data arrives.

### Species feature skeletons

**`species-card-skeleton.vue`** — matches `species-card.vue` layout:
- Same card dimensions and border radius
- Animated pulse placeholder for species name and taxonomy line
- Used in species list page grid while `isPending`

**`species-detail-skeleton.vue`** — matches `[id].vue` detail layout:
- Placeholder blocks for: title, vernacular name, taxonomy breadcrumb, image area, definition list
- Used in species detail page while `isPending`

### Where skeletons are NOT needed

- **Benchmark pages** — data loads from local JSON (`/data/species-10000.json`), renders in <100ms. A skeleton would flash and disappear, worsening perceived performance.
- **Home and about pages** — static content, no async data.

### Skeleton implementation approach

Skeletons are feature-scoped components using Tailwind's `animate-pulse` on neutral background blocks. No skeleton library dependency — just styled `<div>` elements matching the shape of real content.

## Target Folder Structure

```
src/
├── features/
│   ├── species/
│   │   ├── pages/
│   │   │   ├── index.vue              → /species
│   │   │   └── [id].vue              → /species/:id
│   │   ├── components/
│   │   │   ├── species-card.vue
│   │   │   ├── species-card-skeleton.vue
│   │   │   └── species-detail-skeleton.vue
│   │   ├── composables/
│   │   │   ├── use-species-list.ts
│   │   │   ├── use-species-search.ts
│   │   │   ├── use-species-detail.ts
│   │   │   ├── use-species-media.ts
│   │   │   └── use-vernacular-names.ts
│   │   ├── api.ts
│   │   └── types.ts
│   └── benchmark/
│       ├── pages/
│       │   ├── index.vue              → /benchmark
│       │   ├── basic-table.vue        → /benchmark/basic-table
│       │   ├── primevue-table.vue     → /benchmark/primevue-table
│       │   └── tanstack-table.vue     → /benchmark/tanstack-table
│       ├── components/
│       │   └── metrics-panel.vue
│       ├── composables/
│       │   └── use-dom-metrics.ts
│       └── types.ts
├── shared/
│   └── components/
│       └── app-header.vue
├── pages/
│   ├── index.vue                      → /
│   └── about.vue                      → /about
├── app.spec.ts
├── app.vue
├── main.ts
├── router.ts
├── env.d.ts
├── style.css
└── assets/
    └── main.css
```

## File Moves

| Current path | New path |
|---|---|
| `src/api/gbif.ts` | Split → `src/features/species/types.ts` (Zod schemas + inferred types) + `src/features/species/api.ts` (functions with Zod validation) |
| `src/composables/use-species-list.ts` | `src/features/species/composables/use-species-list.ts` |
| `src/composables/use-species-detail.ts` | `src/features/species/composables/use-species-detail.ts` |
| `src/composables/use-species-media.ts` | `src/features/species/composables/use-species-media.ts` |
| `src/composables/use-vernacular-names.ts` | `src/features/species/composables/use-vernacular-names.ts` |
| `src/components/species-card.vue` | `src/features/species/components/species-card.vue` |
| `src/pages/species/index.vue` | `src/features/species/pages/index.vue` |
| `src/pages/species/[id].vue` | `src/features/species/pages/[id].vue` |
| `src/composables/use-dom-metrics.ts` | `src/features/benchmark/composables/use-dom-metrics.ts` |
| `src/components/metrics-panel.vue` | `src/features/benchmark/components/metrics-panel.vue` |
| `src/pages/benchmark/index.vue` | `src/features/benchmark/pages/index.vue` |
| `src/pages/benchmark/basic-table.vue` | `src/features/benchmark/pages/basic-table.vue` |
| `src/pages/benchmark/primevue-table.vue` | `src/features/benchmark/pages/primevue-table.vue` |
| `src/pages/benchmark/tanstack-table.vue` | `src/features/benchmark/pages/tanstack-table.vue` |
| `src/components/app-header.vue` | `src/shared/components/app-header.vue` |
| `src/composables/__tests__/use-dom-metrics.test.ts` | `src/features/benchmark/composables/__tests__/use-dom-metrics.test.ts` |

**New files:**
- `src/features/species/components/species-card-skeleton.vue`
- `src/features/species/components/species-detail-skeleton.vue`
- `src/features/species/composables/use-species-search.ts`
- `src/features/benchmark/types.ts` (extracted `BenchmarkedSpecies`)

**Deleted:**
- `src/composables/use-debounce.ts` — replaced by VueUse's `refDebounced`
- `src/api/` (empty after split)
- `src/composables/` (empty after moves)
- `src/components/` (empty after moves)
- `src/pages/species/` (empty, routes now served from feature folder)
- `src/pages/benchmark/` (empty, routes now served from feature folder)
- `src/router/index.ts` — legacy manual router, superseded by `src/router.ts` (`main.ts` imports from `./router.ts`, not the directory)
- `src/pages/home-page.vue` — dead file, superseded by `src/pages/index.vue` (`app.spec.ts` imports this and must be updated)
- `src/__tests__/app.test.ts` — skipped, not part of the new test strategy
- `src/__tests__/` — directory removed after `app.test.ts` deletion

## Vite Configuration

```ts
VueRouter({
  routesFolder: [
    { src: 'src/features/species/pages', path: 'species/' },
    { src: 'src/features/benchmark/pages', path: 'benchmark/' },
    'src/pages',
  ],
  dts: './typed-router.d.ts',
  extensions: ['.vue'],
  importMode: 'async',
}),
```

Routes generated:
- `src/features/species/pages/index.vue` → `/species`
- `src/features/species/pages/[id].vue` → `/species/:id`
- `src/features/benchmark/pages/index.vue` → `/benchmark`
- `src/features/benchmark/pages/basic-table.vue` → `/benchmark/basic-table`
- `src/pages/index.vue` → `/`
- `src/pages/about.vue` → `/about`

## Import Conventions

**Within a feature:** Use relative imports.
```ts
// src/features/species/composables/use-species-list.ts
import { searchSpecies } from "../api"
import type { GbifSearchResponse } from "../types"
```

**Crossing feature boundaries:** Use absolute `@/` imports, type-only.
```ts
// src/features/benchmark/pages/basic-table.vue
import type { GbifSpeciesSummary } from "@/features/species/types"
```

**Reaching into shared:** Use absolute `@/` imports.
```ts
// src/app.vue
import AppHeader from "@/shared/components/app-header.vue"
```

## Dependency Rules

```
shared/  ← species  ← benchmark
```

**Allowed:**
- Any feature → `shared/`
- `benchmark` → `species/types` (type imports only)
- Within a feature → relative imports freely

**Forbidden:**
- `species` → `benchmark`
- `shared/` → any feature
- Cross-feature imports of composables, components, or API functions (only types)

**Enforcement:** Folder structure makes violations visible. `eslint-plugin-boundaries` can be added later for automated enforcement.

## Export Strategy

No barrel files (`index.ts`). Import from specific files directly. This keeps the dependency graph explicit and avoids re-export indirection.

```ts
// Do this:
import type { GbifSpeciesSummary } from "@/features/species/types"

// Not this:
import type { GbifSpeciesSummary } from "@/features/species"
```

## Testing Strategy

Pragmatic, feature-scoped testing with Vitest + Vue Test Utils + happy-dom.

### What to test

**Species feature:**
- `types.ts` — Zod schemas validate correct data and reject malformed data
- `api.ts` — API functions call correct endpoints, pass query param, and validate responses (mock `fetch`)
- `use-species-list.ts` — composable returns paginated data, handles prefetching
- `use-species-search.ts` — composable debounces query, enables/disables based on input length
- `use-species-detail.ts` — composable seeds initial data from list cache, triggers dependent queries
- `species-card.vue` — renders species name and taxonomy, prefetches on hover

**Not tested (thin wrappers):**
- `use-species-media.ts`, `use-vernacular-names.ts` — trivially thin: a single `useQuery` call with `enabled` flag. The enabling logic is tested via `use-species-detail.ts` which orchestrates them.

**Benchmark feature:**
- `use-dom-metrics.ts` — existing test, moved (mount time, DOM count, FPS tracking)

**App shell:**
- `app.spec.ts` — stays at root, updated to remove `home-page.vue` import (dead file being deleted). Tests the app shell renders with router.

### What NOT to test

- Skeleton components (pure visual, no logic)
- Benchmark page components (integration-heavy, better covered by Lighthouse)
- VueUse's `refDebounced` (tested by VueUse)

### Test file location

Tests live next to the code they test:
```
src/features/species/
├── __tests__/
│   ├── api.test.ts
│   ├── types.test.ts
│   ├── use-species-list.test.ts
│   ├── use-species-search.test.ts
│   └── use-species-detail.test.ts
├── components/
│   └── __tests__/
│       └── species-card.test.ts
```

### Test naming convention

Files: `<module-name>.test.ts` (kebab-case, matching the source file name).

## What Does NOT Change

- `src/router.ts` — consumes auto-generated routes, no changes needed
- `src/app.vue` — only the `app-header` import path changes
- `src/main.ts` — no changes
- `src/style.css` — global styles, stays at root
- `public/data/` — static datasets stay in public
- `scripts/` — build scripts stay at root

## Future Considerations

- **Domain layer:** If a third feature needs `GbifSpeciesSummary`, extract a `src/domain/` layer with shared types. Not needed at current scale.
- **ESLint boundaries:** Add `eslint-plugin-boundaries` to enforce dependency rules at lint time.
- **Result pattern:** If the app grows beyond TanStack Query (complex mutations, orchestration), revisit neverthrow or Boxed for explicit error encoding.

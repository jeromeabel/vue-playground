# Screaming Architecture: Feature-First Folder Structure

## Summary

Reorganize the Vue playground from a layer-first structure (`api/`, `composables/`, `components/`, `pages/`) to a feature-first structure where each feature folder contains its own pages, components, composables, API client, and types. The folder structure should "scream" what the app does (species explorer, benchmarks), not what tech layers it uses.

## Goals

- **Discoverability:** New developers find code faster by looking at feature folders.
- **Colocation:** Related code lives together — delete a folder, delete a feature.
- **Change isolation:** Modifying a feature doesn't require touching multiple layer folders.
- **Low coupling between features, high cohesion within a feature.**

## Features Identified

### `species` — Botanical species explorer
- Pages: list (`/species`) and detail (`/species/:id`)
- Components: `species-card`
- Composables: `use-species-list`, `use-species-detail`, `use-species-media`, `use-vernacular-names`
- API: GBIF client functions (`searchSpecies`, `getSpecies`, `getSpeciesMedia`, `getVernacularNames`)
- Types: `GbifSpeciesSummary`, `GbifSpeciesDetail`, `GbifSearchResponse`, `GbifMediaItem`, `GbifMediaResponse`, `GbifVernacularName`, `GbifVernacularNamesResponse`

### `benchmark` — Table rendering performance comparison
- Pages: index (`/benchmark`), `basic-table`, `primevue-table`, `tanstack-table`
- Components: `metrics-panel`
- Composables: `use-dom-metrics`, `use-debounce`
- Cross-feature type import: `GbifSpeciesSummary` from species (type-only)

### `shared` — App-wide code
- Components: `app-header`

### Top-level (no feature) — App shell and generic pages
- `app.vue`, `main.ts`, `router.ts`
- Pages: `index.vue` (home), `about.vue`
- Tests: `app.spec.ts`, `__tests__/app.test.ts`

## Target Folder Structure

```
src/
├── features/
│   ├── species/
│   │   ├── pages/
│   │   │   ├── index.vue              → /species
│   │   │   └── [id].vue              → /species/:id
│   │   ├── components/
│   │   │   └── species-card.vue
│   │   ├── composables/
│   │   │   ├── use-species-list.ts
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
│       └── composables/
│           ├── use-dom-metrics.ts
│           └── use-debounce.ts
├── shared/
│   └── components/
│       └── app-header.vue
├── pages/
│   ├── index.vue                      → /
│   └── about.vue                      → /about
├── __tests__/
│   └── app.test.ts
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
| `src/api/gbif.ts` | Split → `src/features/species/types.ts` (interfaces) + `src/features/species/api.ts` (functions) |
| `src/composables/use-species-list.ts` | `src/features/species/composables/use-species-list.ts` |
| `src/composables/use-species-detail.ts` | `src/features/species/composables/use-species-detail.ts` |
| `src/composables/use-species-media.ts` | `src/features/species/composables/use-species-media.ts` |
| `src/composables/use-vernacular-names.ts` | `src/features/species/composables/use-vernacular-names.ts` |
| `src/components/species-card.vue` | `src/features/species/components/species-card.vue` |
| `src/pages/species/index.vue` | `src/features/species/pages/index.vue` |
| `src/pages/species/[id].vue` | `src/features/species/pages/[id].vue` |
| `src/composables/use-dom-metrics.ts` | `src/features/benchmark/composables/use-dom-metrics.ts` |
| `src/composables/use-debounce.ts` | `src/features/benchmark/composables/use-debounce.ts` |
| `src/components/metrics-panel.vue` | `src/features/benchmark/components/metrics-panel.vue` |
| `src/pages/benchmark/index.vue` | `src/features/benchmark/pages/index.vue` |
| `src/pages/benchmark/basic-table.vue` | `src/features/benchmark/pages/basic-table.vue` |
| `src/pages/benchmark/primevue-table.vue` | `src/features/benchmark/pages/primevue-table.vue` |
| `src/pages/benchmark/tanstack-table.vue` | `src/features/benchmark/pages/tanstack-table.vue` |
| `src/components/app-header.vue` | `src/shared/components/app-header.vue` |
| `src/composables/__tests__/use-dom-metrics.test.ts` | `src/features/benchmark/composables/__tests__/use-dom-metrics.test.ts` |

**Deleted after moves:**
- `src/api/` (empty)
- `src/composables/` (empty)
- `src/components/` (empty)
- `src/pages/species/` (empty, routes now served from feature folder)
- `src/pages/benchmark/` (empty, routes now served from feature folder)
- `src/router/index.ts` — legacy manual router, superseded by `src/router.ts` with file-based routing
- `src/pages/home-page.vue` — dead file, superseded by `src/pages/index.vue`

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

## What Does NOT Change

- `src/router.ts` — consumes auto-generated routes, no changes needed
- `src/app.vue` — only the `app-header` import path changes
- `src/main.ts` — no changes
- `src/style.css` — global styles, stays at root
- `src/__tests__/app.test.ts`, `src/app.spec.ts` — stay at root, test the app shell
- `public/data/` — static datasets stay in public
- `scripts/` — build scripts stay at root

## Known Compromises

- **`use-debounce` in benchmark:** This is a generic utility (debounces any `Ref<T>`) placed inside the benchmark feature because it's its only consumer today. If the species feature later needs debouncing, move it to `src/shared/composables/use-debounce.ts`.
- **`BenchmarkedSpecies` type duplication:** All three benchmark table pages define `type BenchmarkedSpecies = GbifSpeciesSummary & { benchmarkOrder: number }` inline. Could be extracted to `src/features/benchmark/types.ts` during implementation.

## Future Considerations

- **Domain layer:** If a third feature needs `GbifSpeciesSummary`, extract a `src/domain/` layer with shared types. Not needed at current scale.
- **ESLint boundaries:** Add `eslint-plugin-boundaries` to enforce dependency rules at lint time.
- **Feature-scoped tests:** Feature tests can live in `src/features/<name>/__tests__/` — not part of this refactor.

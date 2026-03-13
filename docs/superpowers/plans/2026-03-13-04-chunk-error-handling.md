# Plan 4: Chunk Error Handling & New Deployments

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the `vite:preloadError` chunk reload handler with navigation bridge, infinite-reload guard, non-blocking version banner, and build-time version generation. Full test coverage for the 6 key behaviors.

**Architecture:** A single `vite:preloadError` listener handles both lazy route and lazy component failures. A plain-object navigation bridge (written by router guards, read by the error listener) determines whether to `reload()` or `assign()`. A `sessionStorage` guard prevents infinite loops. A `VersionBanner` component polls a build-generated `/version` file.

**Tech Stack:** Vite (preload error events), Vue Router guards, sessionStorage, Vitest

**Spec:** `docs/superpowers/specs/2026-03-13-vue-playground-reset-design.md` — see "Feature 3: Chunk Error Handling"

**Prerequisite:** Plan 2 (Minimal Setup) must be completed first. The app should have a working router and at least one lazy route.

**Reference:** `draft-for-blogs/blog-post-the-chunk-that-wasnt-there.md` contains the full blog post with implementation details.

---

## Chunk 1: Navigation Bridge + Reload Guard + Listener

### Task 1: Write Tests for Chunk Reload Handler

**Files:**
- Create: `src/utils/__tests__/chunk-reload.test.ts`

- [ ] **Step 1: Write all 6 tests**

```typescript
// src/utils/__tests__/chunk-reload.test.ts
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  createNavigation,
  createReloadGuard,
  registerChunkReload,
} from '../chunk-reload'

describe('chunk-reload', () => {
  let reloadSpy: ReturnType<typeof vi.fn>
  let assignSpy: ReturnType<typeof vi.fn>
  let preventDefaultSpy: ReturnType<typeof vi.fn>

  function firePreloadError() {
    preventDefaultSpy = vi.fn()
    const event = new Event('vite:preloadError') as Event & { payload: Error }
    event.payload = new Error('Failed to fetch dynamically imported module')
    event.preventDefault = preventDefaultSpy
    window.dispatchEvent(event)
  }

  beforeEach(() => {
    reloadSpy = vi.fn()
    assignSpy = vi.fn()
    Object.defineProperty(window, 'location', {
      value: { reload: reloadSpy, assign: assignSpy },
      writable: true,
    })
    sessionStorage.clear()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('with registerChunkReload', () => {
    let navigation: ReturnType<typeof createNavigation>
    let cleanup: () => void

    beforeEach(() => {
      navigation = createNavigation()
      const guard = createReloadGuard('test-chunk-reload')
      cleanup = registerChunkReload(navigation, guard)
    })

    afterEach(() => {
      cleanup()
    })

    it('reloads the current page when no navigation is pending', () => {
      firePreloadError()

      expect(reloadSpy).toHaveBeenCalled()
      expect(assignSpy).not.toHaveBeenCalled()
      expect(preventDefaultSpy).toHaveBeenCalled()
    })

    it('navigates to the target URL when a route change is pending', () => {
      navigation.begin({ fullPath: '/dashboard', href: '/app/dashboard' })

      firePreloadError()

      expect(assignSpy).toHaveBeenCalledWith('/app/dashboard')
      expect(reloadSpy).not.toHaveBeenCalled()
      expect(preventDefaultSpy).toHaveBeenCalled()
    })

    it('does not reload twice for the same path', () => {
      // First error — should reload
      firePreloadError()
      expect(reloadSpy).toHaveBeenCalledTimes(1)

      // Second error for same path — should bail
      reloadSpy.mockClear()
      firePreloadError()
      expect(reloadSpy).not.toHaveBeenCalled()
      expect(preventDefaultSpy).not.toHaveBeenCalled()
    })

    it('still reloads when sessionStorage throws', () => {
      vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
        throw new DOMException('quota')
      })
      vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
        throw new DOMException('quota')
      })

      firePreloadError()

      expect(reloadSpy).toHaveBeenCalled()
    })
  })

  describe('reloadGuard lifecycle', () => {
    it('clears guard when navigating to a different path', () => {
      const guard = createReloadGuard('test-lifecycle')
      guard.mark('/')

      expect(guard.alreadySeen('/')).toBe(true)

      guard.clearIfNavigatedAway('/about')

      expect(guard.alreadySeen('/')).toBe(false)
    })

    it('preserves guard when staying on the same path', () => {
      const guard = createReloadGuard('test-lifecycle-same')
      guard.mark('/settings')

      guard.clearIfNavigatedAway('/settings')

      expect(guard.alreadySeen('/settings')).toBe(true)
    })
  })
})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pnpm test:run src/utils/__tests__/chunk-reload.test.ts`
Expected: FAIL — module not found

- [ ] **Step 3: Commit failing tests**

```bash
mkdir -p src/utils/__tests__
git add src/utils/__tests__/chunk-reload.test.ts
git commit -m "test: add 6 tests for chunk reload handler"
```

---

### Task 2: Implement Chunk Reload Handler

**Files:**
- Create: `src/utils/chunk-reload.ts`

- [ ] **Step 1: Implement the module**

```typescript
// src/utils/chunk-reload.ts

export interface PendingNav {
  fullPath: string
  href: string
}

export function createNavigation() {
  let currentFullPath = '/'
  let pending: PendingNav | null = null

  return {
    begin(nav: PendingNav) {
      pending = nav
    },
    finish(fullPath: string) {
      pending = null
      currentFullPath = fullPath
    },
    get pending() {
      return pending
    },
    get currentFullPath() {
      return currentFullPath
    },
  }
}

export function createReloadGuard(key: string) {
  return {
    alreadySeen(fullPath: string): boolean {
      try {
        return sessionStorage.getItem(key) === fullPath
      }
      catch {
        return false
      }
    },
    mark(fullPath: string): void {
      try {
        sessionStorage.setItem(key, fullPath)
      }
      catch {
        // Private browsing or quota — reload anyway
      }
    },
    clearIfNavigatedAway(fullPath: string): void {
      try {
        const stored = sessionStorage.getItem(key)
        if (stored && stored !== fullPath) {
          sessionStorage.removeItem(key)
        }
      }
      catch {
        // Ignore
      }
    },
  }
}

export type Navigation = ReturnType<typeof createNavigation>
export type ReloadGuard = ReturnType<typeof createReloadGuard>

export function registerChunkReload(
  navigation: Navigation,
  guard: ReloadGuard,
): () => void {
  function handler(event: Event) {
    const nav = navigation.pending
    const fullPath = nav?.fullPath ?? navigation.currentFullPath

    if (guard.alreadySeen(fullPath)) {
      // Bail — don't call preventDefault, let the error propagate
      return
    }

    guard.mark(fullPath)
    event.preventDefault()

    if (nav) {
      window.location.assign(nav.href)
    }
    else {
      window.location.reload()
    }
  }

  window.addEventListener('vite:preloadError', handler)

  return () => {
    window.removeEventListener('vite:preloadError', handler)
  }
}
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `pnpm test:run src/utils/__tests__/chunk-reload.test.ts`
Expected: All 6 tests PASS

- [ ] **Step 3: Commit**

```bash
git add src/utils/chunk-reload.ts
git commit -m "feat: add chunk reload handler with navigation bridge and reload guard"
```

---

### Task 3: Wire Chunk Reload into Router

**Files:**
- Modify: `src/router.ts`

- [ ] **Step 1: Update router.ts to integrate chunk reload**

```typescript
// src/router.ts
import { createRouter, createWebHistory } from 'vue-router'
import { routes, handleHotUpdate } from 'vue-router/auto-routes'
import {
  createNavigation,
  createReloadGuard,
  registerChunkReload,
} from './utils/chunk-reload'

export const router = createRouter({
  history: createWebHistory(),
  routes,
})

// --- Chunk reload handling ---
const navigation = createNavigation()
const reloadGuard = createReloadGuard('chunk-reload-target')

router.beforeEach((to) => {
  navigation.begin({
    fullPath: to.fullPath,
    href: router.resolve(to).href,
  })
})

router.afterEach((to) => {
  navigation.finish(to.fullPath)
  reloadGuard.clearIfNavigatedAway(to.fullPath)
})

registerChunkReload(navigation, reloadGuard)

// --- HMR ---
if (import.meta.hot) {
  handleHotUpdate(router)
}
```

- [ ] **Step 2: Verify app still works**

Run: `pnpm dev`
Navigate between pages — no errors, all routes load.

- [ ] **Step 3: Commit**

```bash
git add src/router.ts
git commit -m "feat: wire chunk reload handler into router guards"
```

---

## Chunk 2: Version Banner + Build Script

### Task 4: Generate Version Script

**Files:**
- Create: `scripts/generate-version.ts`

- [ ] **Step 1: Create the script**

Note: This is a build-time script with hardcoded commands — no user input is involved.

```typescript
// scripts/generate-version.ts
import { execFileSync } from 'node:child_process'
import { mkdirSync, writeFileSync } from 'node:fs'
import { resolve } from 'node:path'

const OUTPUT = resolve(import.meta.dirname, '../public/version')

function getVersion(): string {
  // Netlify environment variables
  const deployId = process.env.DEPLOY_ID
  if (deployId) return deployId

  const commitRef = process.env.COMMIT_REF
  if (commitRef) return commitRef.slice(0, 8)

  // Fallback: git short SHA
  try {
    return execFileSync('git', ['rev-parse', '--short', 'HEAD'], {
      encoding: 'utf-8',
    }).trim()
  }
  catch {
    return 'dev'
  }
}

const version = getVersion()
mkdirSync(resolve(import.meta.dirname, '../public'), { recursive: true })
writeFileSync(OUTPUT, version)
console.log(`Version: ${version} -> ${OUTPUT}`)
```

- [ ] **Step 2: Add to package.json build script**

Update the `build` script in `package.json`:
```json
"build": "tsx scripts/generate-version.ts && vue-tsc --build --force && vite build"
```

- [ ] **Step 3: Test the script**

Run: `tsx scripts/generate-version.ts`
Expected: Writes git short SHA to `public/version`

Run: `cat public/version`
Expected: Something like `72f2ebd`

- [ ] **Step 4: Add `public/version` to .gitignore**

Append to `.gitignore`:
```
# Generated at build time
public/version
```

- [ ] **Step 5: Commit**

```bash
git add scripts/generate-version.ts package.json .gitignore
git commit -m "feat: add build-time version generation script"
```

---

### Task 5: Version Banner Component

**Files:**
- Create: `src/components/VersionBanner.vue`
- Modify: `src/App.vue`

- [ ] **Step 1: Create VersionBanner.vue**

```vue
<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'

const buildVersion = ref('')
const latestVersion = ref('')
const dismissed = ref(false)
let intervalId: ReturnType<typeof setInterval> | null = null

const updateAvailable = computed(
  () =>
    !dismissed.value
    && buildVersion.value !== ''
    && latestVersion.value !== ''
    && buildVersion.value !== latestVersion.value,
)

async function fetchVersion(): Promise<string> {
  const res = await fetch('/version', { cache: 'no-cache' })
  return (await res.text()).trim()
}

function refresh() {
  window.location.reload()
}

onMounted(async () => {
  if (import.meta.env.DEV) return

  try {
    buildVersion.value = await fetchVersion()
  }
  catch {
    return
  }

  intervalId = setInterval(async () => {
    try {
      latestVersion.value = await fetchVersion()
    }
    catch {
      // Network error — skip this poll cycle
    }
  }, 60_000)
})

onUnmounted(() => {
  if (intervalId) clearInterval(intervalId)
})
</script>

<template>
  <div
    v-if="updateAvailable"
    class="border-b border-primary/20 bg-primary-light/20 px-4 py-2 text-center text-sm"
  >
    A new version is available.
    <button
      class="ml-2 font-medium text-primary underline"
      @click="refresh"
    >
      Refresh
    </button>
    <button
      class="ml-2 text-text-muted"
      @click="dismissed = true"
    >
      Dismiss
    </button>
  </div>
</template>
```

- [ ] **Step 2: Add VersionBanner to App.vue**

Update `src/App.vue` to include the banner above the header:

```vue
<script setup lang="ts">
import { VueQueryDevtools } from '@tanstack/vue-query-devtools'
import AppHeader from './components/AppHeader.vue'
import VersionBanner from './components/VersionBanner.vue'
</script>

<template>
  <div class="min-h-screen">
    <VersionBanner />
    <AppHeader />
    <main class="mx-auto max-w-6xl px-6 py-8">
      <RouterView />
    </main>
  </div>
  <VueQueryDevtools />
</template>
```

- [ ] **Step 3: Commit**

```bash
git add src/components/VersionBanner.vue src/App.vue
git commit -m "feat: add non-blocking version banner with polling"
```

---

### Task 6: Final Verification

- [ ] **Step 1: Run all tests**

Run: `pnpm test:run`
Expected: All chunk-reload tests pass (6 tests). Other tests from Plan 3 may also pass if that plan was completed first.

- [ ] **Step 2: Run lint**

Run: `pnpm lint`
Expected: No errors

- [ ] **Step 3: Build**

Run: `pnpm build`
Expected: Builds successfully. `public/version` contains a git SHA. `dist/` is populated.

- [ ] **Step 4: Preview and verify version banner behavior**

Run: `pnpm preview`

The version banner should NOT appear (build version matches latest version). To test it:
1. Change `public/version` to a different value manually
2. Wait 60 seconds or refresh — banner should appear

- [ ] **Step 5: Verify chunk reload does not interfere with normal navigation**

Navigate between all routes in the preview build — no unexpected reloads.

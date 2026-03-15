import { describe, expect, it, vi } from "vitest";
import { ref } from "vue";

import { useSpeciesSearch } from "../composables/use-species-search";

// Mock the API module
vi.mock("../api", () => ({
    searchSpecies: vi.fn().mockResolvedValue({
        offset: 0,
        limit: 20,
        endOfRecords: false,
        count: 1,
        results: [],
    }),
}));

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
}));

describe("useSpeciesSearch", () => {
    it("returns a query object", () => {
        const rawQuery = ref("");
        const result = useSpeciesSearch(rawQuery);
        expect(result).toHaveProperty("data");
        expect(result).toHaveProperty("isPending");
    });

    it("disables query when input is empty", () => {
        const rawQuery = ref("");
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const result = useSpeciesSearch(rawQuery) as any;
        // The enabled computed should resolve to false for empty input
        expect(result._enabled.value).toBe(false);
    });
});

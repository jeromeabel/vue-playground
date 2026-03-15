import { useQuery } from "@tanstack/vue-query";
import type { BenchmarkResults } from "../types";

export function useTraceResults() {
    return useQuery({
        queryKey: ["trace-results"],
        queryFn: async (): Promise<BenchmarkResults> => {
            const response = await fetch("/data/trace-results.json");
            if (!response.ok) {
                throw new Error(`Failed to load trace results: ${response.status}`);
            }
            const contentType = response.headers.get("content-type") ?? "";
            if (!contentType.includes("json")) {
                throw new Error("trace-results.json not found (got SPA fallback). Rebuild with pnpm build.");
            }
            return response.json();
        },
        staleTime: Infinity,
    });
}

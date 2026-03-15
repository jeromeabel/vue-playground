import { useQuery } from "@tanstack/vue-query";
import type { BenchmarkResults } from "../types";

export function useBenchmarkResults() {
    return useQuery({
        queryKey: ["benchmark-results"],
        queryFn: async (): Promise<BenchmarkResults> => {
            const response = await fetch("/data/benchmark-results.json");
            if (!response.ok) {
                throw new Error(`Failed to load benchmark results: ${response.status}`);
            }
            return response.json();
        },
        staleTime: Infinity,
    });
}

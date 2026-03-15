import { computed, type Ref } from "vue";
import { useQuery, useQueryClient } from "@tanstack/vue-query";

import { getSpecies } from "../api";
import type { GbifSpeciesSummary } from "../types";

export function useSpeciesDetail(id: Ref<number>) {
    const queryClient = useQueryClient();

    return useQuery({
        queryKey: computed(() => ["species", "detail", id.value]),
        queryFn: () => getSpecies(id.value),
        initialData: () => {
            const queries = queryClient.getQueriesData<{ results: GbifSpeciesSummary[] }>({
                queryKey: ["species", "list"],
            });

            for (const [, data] of queries) {
                const match = data?.results.find(species => species.key === id.value);
                if (match) {
                    return match as Awaited<ReturnType<typeof getSpecies>>;
                }
            }

            return undefined;
        },
    });
}

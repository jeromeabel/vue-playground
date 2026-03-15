import { computed, type Ref } from "vue";
import { keepPreviousData, useQuery, useQueryClient } from "@tanstack/vue-query";

import { searchSpecies } from "../api";

const PAGE_SIZE = 20;

export function useSpeciesList(page: Ref<number>) {
    const queryClient = useQueryClient();

    const query = useQuery({
        queryKey: computed(() => ["species", "list", page.value]),
        queryFn: () => searchSpecies(page.value * PAGE_SIZE, PAGE_SIZE),
        placeholderData: keepPreviousData,
    });

    const prefetchNext = () => {
        const currentPage = page.value;
        queryClient.prefetchQuery({
            queryKey: ["species", "list", currentPage + 1],
            queryFn: () => searchSpecies((currentPage + 1) * PAGE_SIZE, PAGE_SIZE),
        });
    };

    const totalPages = computed(() => {
        const count = query.data.value?.count ?? 0;
        return Math.ceil(count / PAGE_SIZE);
    });

    return {
        ...query,
        totalPages,
        prefetchNext,
        PAGE_SIZE,
    };
}

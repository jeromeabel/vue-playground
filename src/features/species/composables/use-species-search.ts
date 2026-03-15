import { computed, type Ref } from "vue";
import { refDebounced } from "@vueuse/core";
import { keepPreviousData, useQuery } from "@tanstack/vue-query";

import { searchSpecies } from "../api";

export function useSpeciesSearch(rawQuery: Ref<string>) {
    const query = refDebounced(rawQuery, 300);

    return useQuery({
        queryKey: computed(() => ["species", "search", query.value]),
        queryFn: () => searchSpecies(0, 20, query.value),
        enabled: computed(() => query.value.length > 0),
        placeholderData: keepPreviousData,
    });
}

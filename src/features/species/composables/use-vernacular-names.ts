import { computed, type Ref } from "vue";
import { useQuery } from "@tanstack/vue-query";

import { getVernacularNames } from "../api";

export function useVernacularNames(id: Ref<number>, enabled: Ref<boolean>) {
    return useQuery({
        queryKey: computed(() => ["species", "vernacular", id.value]),
        queryFn: () => getVernacularNames(id.value),
        enabled,
    });
}

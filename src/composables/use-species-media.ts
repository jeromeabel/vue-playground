import { computed, type Ref } from "vue";
import { useQuery } from "@tanstack/vue-query";

import { getSpeciesMedia } from "@/api/gbif";

export function useSpeciesMedia(id: Ref<number>, enabled: Ref<boolean>) {
    return useQuery({
        queryKey: computed(() => ["species", "media", id.value]),
        queryFn: () => getSpeciesMedia(id.value),
        enabled,
    });
}

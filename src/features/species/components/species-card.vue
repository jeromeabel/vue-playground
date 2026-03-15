<script setup lang="ts">
import { useQueryClient } from "@tanstack/vue-query";

import { getSpecies, getSpeciesMedia } from "../api";
import type { GbifSpeciesSummary } from "../types";

const props = defineProps<{
    species: GbifSpeciesSummary;
}>();

const queryClient = useQueryClient();

function prefetchDetail() {
    queryClient.prefetchQuery({
        queryKey: ["species", "detail", props.species.key],
        queryFn: () => getSpecies(props.species.key),
    });
    queryClient.prefetchQuery({
        queryKey: ["species", "media", props.species.key],
        queryFn: () => getSpeciesMedia(props.species.key),
    });
}
</script>

<template>
  <RouterLink
    :to="`/species/${species.key}`"
    class="block rounded-lg border border-surface-dark p-4 hover:border-primary hover:shadow-sm"
    @mouseenter="prefetchDetail"
  >
    <h3 class="font-medium italic">
      {{ species.canonicalName }}
    </h3>
    <p class="mt-1 text-xs text-text-muted">
      {{ species.family }} · {{ species.genus }}
    </p>
  </RouterLink>
</template>

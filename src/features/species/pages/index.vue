<script setup lang="ts">
import { ref } from "vue";

import SpeciesCard from "../components/species-card.vue";
import SpeciesCardSkeleton from "../components/species-card-skeleton.vue";
import { useSpeciesList } from "../composables/use-species-list";

const page = ref(0);
const { data, isPending, isError, error, refetch, totalPages, prefetchNext } = useSpeciesList(page);
</script>

<template>
  <div>
    <h1 class="mb-6 text-2xl font-bold">
      Species Explorer
    </h1>

    <div
      v-if="isPending"
      class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4"
    >
      <SpeciesCardSkeleton
        v-for="i in 8"
        :key="i"
      />
    </div>

    <div
      v-else-if="isError"
      class="text-red-600"
    >
      <p>Error: {{ error?.message }}</p>
      <button
        class="mt-2 rounded bg-primary px-3 py-1 text-sm text-white"
        @click="() => refetch()"
      >
        Retry
      </button>
    </div>

    <template v-else>
      <div class="mb-4 text-sm text-text-muted">
        {{ data?.count?.toLocaleString() }} species found
      </div>

      <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <SpeciesCard
          v-for="species in data?.results"
          :key="species.key"
          :species="species"
        />
      </div>

      <div class="mt-6 flex items-center gap-4">
        <button
          :disabled="page === 0"
          class="rounded border px-3 py-1 text-sm disabled:opacity-40"
          @click="page--"
        >
          Previous
        </button>
        <span class="text-sm text-text-muted">
          Page {{ page + 1 }} of {{ totalPages }}
        </span>
        <button
          :disabled="data?.endOfRecords"
          class="rounded border px-3 py-1 text-sm disabled:opacity-40"
          @click="page++; prefetchNext()"
        >
          Next
        </button>
      </div>
    </template>
  </div>
</template>

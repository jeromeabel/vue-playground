<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

import { useSpeciesDetail } from "@/composables/use-species-detail";
import { useSpeciesMedia } from "@/composables/use-species-media";
import { useVernacularNames } from "@/composables/use-vernacular-names";

const route = useRoute();
const id = computed(() => Number(route.params.id));

const { data: species, isPending, isError, error, refetch } = useSpeciesDetail(id);

const detailLoaded = computed(() => !!species.value);
const { data: media } = useSpeciesMedia(id, detailLoaded);
const { data: names } = useVernacularNames(id, detailLoaded);

const frenchName = computed(() => names.value?.results.find(name => name.language === "fra")?.vernacularName);
const englishName = computed(() => names.value?.results.find(name => name.language === "eng")?.vernacularName);
const firstImage = computed(() => media.value?.results.find(item => item.type === "StillImage")?.identifier);
</script>

<template>
  <div>
    <RouterLink
      to="/species"
      class="mb-4 inline-block text-sm text-primary hover:underline"
    >
      &larr; Back to list
    </RouterLink>

    <div
      v-if="isPending"
      class="text-text-muted"
    >
      Loading species...
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

    <template v-else-if="species">
      <h1 class="mb-1 text-2xl font-bold italic">
        {{ species.canonicalName }}
      </h1>

      <div
        v-if="frenchName || englishName"
        class="mb-4 text-text-muted"
      >
        {{ frenchName ?? englishName }}
      </div>

      <div class="mb-6 flex flex-wrap gap-2 text-xs text-text-muted">
        <span>{{ species.kingdom }}</span>
        <span>&rsaquo;</span>
        <span>{{ species.phylum }}</span>
        <span>&rsaquo;</span>
        <span>{{ species.class }}</span>
        <span>&rsaquo;</span>
        <span>{{ species.order }}</span>
        <span>&rsaquo;</span>
        <span>{{ species.family }}</span>
        <span>&rsaquo;</span>
        <span class="font-medium">{{ species.genus }}</span>
      </div>

      <img
        v-if="firstImage"
        :src="firstImage"
        :alt="species.canonicalName"
        class="mb-6 max-h-80 rounded-lg object-cover"
      >

      <dl class="grid grid-cols-2 gap-2 text-sm">
        <dt class="text-text-muted">
          Author
        </dt>
        <dd>{{ species.authorship }}</dd>
        <dt class="text-text-muted">
          Status
        </dt>
        <dd>{{ species.taxonomicStatus }}</dd>
        <template v-if="species.publishedIn">
          <dt class="text-text-muted">
            Published in
          </dt>
          <dd>{{ species.publishedIn }}</dd>
        </template>
      </dl>
    </template>
  </div>
</template>

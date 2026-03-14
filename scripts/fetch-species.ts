import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import type { GbifSpeciesSummary } from "../src/api/gbif";

const BASE_URL = "https://api.gbif.org/v1";
const LIMIT = 1000;
const PAGES = 10;
const DELAY_MS = 100;
const VERNACULAR_BATCH_SIZE = 50;
const VERNACULAR_BATCH_DELAY_MS = 200;

const scriptDir = dirname(fileURLToPath(import.meta.url));
const outputDir = resolve(scriptDir, "../public/data");
const outputPath = resolve(outputDir, "species-10000.json");

interface GbifSearchPayload {
    results: Array<Partial<GbifSpeciesSummary>>;
}

interface GbifVernacularPayload {
    results: Array<{ vernacularName: string; language: string }>;
}

async function fetchPage(offset: number): Promise<GbifSpeciesSummary[]> {
    const params = new URLSearchParams({
        rank: "SPECIES",
        highertaxon_key: "6",
        status: "ACCEPTED",
        limit: String(LIMIT),
        offset: String(offset),
    });

    const res = await fetch(`${BASE_URL}/species/search?${params}`);
    if (!res.ok) {
        throw new Error(`GBIF failed: ${res.status}`);
    }

    const data = (await res.json()) as GbifSearchPayload;

    return data.results.map(result => ({
        key: result.key ?? 0,
        scientificName: result.scientificName ?? "",
        canonicalName: result.canonicalName ?? "",
        kingdom: result.kingdom ?? "",
        phylum: result.phylum ?? "",
        class: result.class ?? "",
        order: result.order ?? "",
        family: result.family ?? "",
        genus: result.genus ?? "",
        taxonomicStatus: result.taxonomicStatus ?? "",
        rank: result.rank ?? "",
        vernacularNames: [],
    }));
}

async function fetchVernacularNames(key: number): Promise<{ vernacularName: string; language: string }[]> {
    const res = await fetch(`${BASE_URL}/species/${key}/vernacularNames?limit=10`);
    if (!res.ok) {
        return [];
    }
    const data = (await res.json()) as GbifVernacularPayload;
    return data.results
        .filter(v => v.vernacularName && v.language)
        .map(v => ({ vernacularName: v.vernacularName, language: v.language }))
        .slice(0, 10);
}

async function delay(ms: number): Promise<void> {
    await new Promise(resolve => setTimeout(resolve, ms));
}

async function fetchVernacularsBatch(species: GbifSpeciesSummary[]): Promise<void> {
    const totalBatches = Math.ceil(species.length / VERNACULAR_BATCH_SIZE);
    for (let i = 0; i < species.length; i += VERNACULAR_BATCH_SIZE) {
        const batch = species.slice(i, i + VERNACULAR_BATCH_SIZE);
        const batchNum = Math.floor(i / VERNACULAR_BATCH_SIZE) + 1;
        console.log(`  Vernacular batch ${batchNum}/${totalBatches}...`);

        const results = await Promise.all(batch.map(s => fetchVernacularNames(s.key)));
        for (let j = 0; j < batch.length; j++) {
            batch[j].vernacularNames = results[j];
        }

        if (i + VERNACULAR_BATCH_SIZE < species.length) {
            await delay(VERNACULAR_BATCH_DELAY_MS);
        }
    }
}

async function main() {
    const all: GbifSpeciesSummary[] = [];

    for (let i = 0; i < PAGES; i++) {
        console.log(`Fetching page ${i + 1}/${PAGES} (offset=${i * LIMIT})...`);
        const page = await fetchPage(i * LIMIT);
        all.push(...page);
        if (i < PAGES - 1) {
            await delay(DELAY_MS);
        }
    }

    console.log(`\nFetching vernacular names for ${all.length} species...`);
    await fetchVernacularsBatch(all);

    const withNames = all.filter(s => s.vernacularNames.length > 0).length;
    console.log(`${withNames}/${all.length} species have vernacular names`);

    mkdirSync(outputDir, { recursive: true });
    writeFileSync(outputPath, JSON.stringify(all, null, 2));
    console.log(`Wrote ${all.length} species to ${outputPath}`);
}

main().catch((error) => {
    console.error(error);
    process.exit(1);
});

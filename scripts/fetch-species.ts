import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import type { GbifSpeciesSummary } from "../src/api/gbif";

const BASE_URL = "https://api.gbif.org/v1";
const LIMIT = 1000;
const PAGES = 3;
const DELAY_MS = 100;

const scriptDir = dirname(fileURLToPath(import.meta.url));
const outputDir = resolve(scriptDir, "../public/data");
const outputPath = resolve(outputDir, "species-3000.json");

interface GbifSearchPayload {
    results: Array<Partial<GbifSpeciesSummary>>;
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
    }));
}

async function main() {
    const all: GbifSpeciesSummary[] = [];

    for (let i = 0; i < PAGES; i++) {
        console.log(`Fetching page ${i + 1}/${PAGES} (offset=${i * LIMIT})...`);
        const page = await fetchPage(i * LIMIT);
        all.push(...page);
        if (i < PAGES - 1) {
            await new Promise(resolveDelay => setTimeout(resolveDelay, DELAY_MS));
        }
    }

    mkdirSync(outputDir, { recursive: true });
    writeFileSync(outputPath, JSON.stringify(all, null, 2));
    console.log(`Wrote ${all.length} species to ${outputPath}`);
}

main().catch((error) => {
    console.error(error);
    process.exit(1);
});

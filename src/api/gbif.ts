const BASE_URL = "https://api.gbif.org/v1";

export interface GbifSpeciesSummary {
    key: number;
    scientificName: string;
    canonicalName: string;
    kingdom: string;
    phylum: string;
    class: string;
    order: string;
    family: string;
    genus: string;
    taxonomicStatus: string;
    rank: string;
    vernacularNames: { vernacularName: string; language: string }[];
}

export interface GbifSpeciesDetail extends GbifSpeciesSummary {
    authorship: string;
    publishedIn?: string;
    nameType: string;
    numDescendants: number;
}

export interface GbifSearchResponse {
    offset: number;
    limit: number;
    endOfRecords: boolean;
    count: number;
    results: GbifSpeciesSummary[];
}

export interface GbifMediaItem {
    type: string;
    identifier: string;
    title?: string;
    creator?: string;
    license?: string;
}

export interface GbifMediaResponse {
    results: GbifMediaItem[];
}

export interface GbifVernacularName {
    vernacularName: string;
    language: string;
    source?: string;
}

export interface GbifVernacularNamesResponse {
    results: GbifVernacularName[];
}

export async function searchSpecies(offset = 0, limit = 20): Promise<GbifSearchResponse> {
    const params = new URLSearchParams({
        rank: "SPECIES",
        highertaxon_key: "6",
        status: "ACCEPTED",
        limit: String(limit),
        offset: String(offset),
    });

    const res = await fetch(`${BASE_URL}/species/search?${params}`);
    if (!res.ok) {
        throw new Error(`GBIF search failed: ${res.status}`);
    }

    return res.json();
}

export async function getSpecies(key: number): Promise<GbifSpeciesDetail> {
    const res = await fetch(`${BASE_URL}/species/${key}`);
    if (!res.ok) {
        throw new Error(`GBIF species ${key} failed: ${res.status}`);
    }

    return res.json();
}

export async function getSpeciesMedia(key: number): Promise<GbifMediaResponse> {
    const res = await fetch(`${BASE_URL}/species/${key}/media`);
    if (!res.ok) {
        throw new Error(`GBIF media ${key} failed: ${res.status}`);
    }

    return res.json();
}

export async function getVernacularNames(key: number): Promise<GbifVernacularNamesResponse> {
    const res = await fetch(`${BASE_URL}/species/${key}/vernacularNames`);
    if (!res.ok) {
        throw new Error(`GBIF names ${key} failed: ${res.status}`);
    }

    return res.json();
}

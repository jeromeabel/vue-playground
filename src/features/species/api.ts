import {
    GbifMediaResponseSchema,
    GbifSearchResponseSchema,
    GbifSpeciesDetailSchema,
    GbifVernacularNamesResponseSchema,
} from "./types"

const BASE_URL = "https://api.gbif.org/v1"

export async function searchSpecies(offset = 0, limit = 20, query?: string) {
    const params = new URLSearchParams({
        rank: "SPECIES",
        highertaxon_key: "6",
        status: "ACCEPTED",
        limit: String(limit),
        offset: String(offset),
        ...(query ? { q: query } : {}),
    })

    const res = await fetch(`${BASE_URL}/species/search?${params}`)
    if (!res.ok) {
        throw new Error(`GBIF search failed: ${res.status}`)
    }

    return GbifSearchResponseSchema.parse(await res.json())
}

export async function getSpecies(key: number) {
    const res = await fetch(`${BASE_URL}/species/${key}`)
    if (!res.ok) {
        throw new Error(`GBIF species ${key} failed: ${res.status}`)
    }

    return GbifSpeciesDetailSchema.parse(await res.json())
}

export async function getSpeciesMedia(key: number) {
    const res = await fetch(`${BASE_URL}/species/${key}/media`)
    if (!res.ok) {
        throw new Error(`GBIF media ${key} failed: ${res.status}`)
    }

    return GbifMediaResponseSchema.parse(await res.json())
}

export async function getVernacularNames(key: number) {
    const res = await fetch(`${BASE_URL}/species/${key}/vernacularNames`)
    if (!res.ok) {
        throw new Error(`GBIF names ${key} failed: ${res.status}`)
    }

    return GbifVernacularNamesResponseSchema.parse(await res.json())
}

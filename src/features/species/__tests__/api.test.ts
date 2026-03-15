import { afterEach, describe, expect, it, vi } from "vitest"

import { getSpecies, getSpeciesMedia, getVernacularNames, searchSpecies } from "../api"

const mockFetch = vi.fn()
vi.stubGlobal("fetch", mockFetch)

afterEach(() => {
    vi.clearAllMocks()
})

describe("searchSpecies", () => {
    const validResponse = {
        offset: 0,
        limit: 20,
        endOfRecords: false,
        count: 1,
        results: [{
            key: 1,
            scientificName: "Quercus robur L.",
            canonicalName: "Quercus robur",
            kingdom: "Plantae",
            phylum: "Tracheophyta",
            class: "Magnoliopsida",
            order: "Fagales",
            family: "Fagaceae",
            genus: "Quercus",
            taxonomicStatus: "ACCEPTED",
            rank: "SPECIES",
            vernacularNames: [],
        }],
    }

    it("calls the correct endpoint with default params", async () => {
        mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(validResponse) })
        await searchSpecies()

        const url = new URL(mockFetch.mock.calls[0][0])
        expect(url.pathname).toBe("/v1/species/search")
        expect(url.searchParams.get("offset")).toBe("0")
        expect(url.searchParams.get("limit")).toBe("20")
        expect(url.searchParams.has("q")).toBe(false)
    })

    it("passes query parameter when provided", async () => {
        mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(validResponse) })
        await searchSpecies(0, 20, "quercus")

        const url = new URL(mockFetch.mock.calls[0][0])
        expect(url.searchParams.get("q")).toBe("quercus")
    })

    it("validates response with Zod", async () => {
        mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({ bad: "data" }) })
        await expect(searchSpecies()).rejects.toThrow()
    })

    it("throws on non-OK response", async () => {
        mockFetch.mockResolvedValueOnce({ ok: false, status: 500 })
        await expect(searchSpecies()).rejects.toThrow("GBIF search failed: 500")
    })
})

describe("getSpecies", () => {
    it("calls the correct endpoint", async () => {
        const detail = {
            key: 42,
            scientificName: "Quercus robur L.",
            canonicalName: "Quercus robur",
            kingdom: "Plantae",
            phylum: "Tracheophyta",
            class: "Magnoliopsida",
            order: "Fagales",
            family: "Fagaceae",
            genus: "Quercus",
            taxonomicStatus: "ACCEPTED",
            rank: "SPECIES",
            vernacularNames: [],
            authorship: "L.",
            nameType: "SCIENTIFIC",
            numDescendants: 0,
        }
        mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(detail) })
        const result = await getSpecies(42)

        expect(mockFetch.mock.calls[0][0]).toContain("/v1/species/42")
        expect(result.authorship).toBe("L.")
    })
})

describe("getSpeciesMedia", () => {
    it("calls the correct endpoint", async () => {
        const media = { results: [{ type: "StillImage", identifier: "https://example.com/img.jpg" }] }
        mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(media) })
        const result = await getSpeciesMedia(42)

        expect(mockFetch.mock.calls[0][0]).toContain("/v1/species/42/media")
        expect(result.results[0].type).toBe("StillImage")
    })
})

describe("getVernacularNames", () => {
    it("calls the correct endpoint", async () => {
        const names = { results: [{ vernacularName: "Oak", language: "eng" }] }
        mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(names) })
        const result = await getVernacularNames(42)

        expect(mockFetch.mock.calls[0][0]).toContain("/v1/species/42/vernacularNames")
        expect(result.results[0].vernacularName).toBe("Oak")
    })
})

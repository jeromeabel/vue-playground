import { describe, expect, it } from "vitest"

import {
    GbifMediaResponseSchema,
    GbifSearchResponseSchema,
    GbifSpeciesDetailSchema,
    GbifSpeciesSummarySchema,
    GbifVernacularNamesResponseSchema,
} from "../types"

describe("GbifSpeciesSummarySchema", () => {
    const validSummary = {
        key: 12345,
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
        vernacularNames: [{ vernacularName: "English Oak", language: "eng" }],
    }

    it("parses valid species data", () => {
        const result = GbifSpeciesSummarySchema.parse(validSummary)
        expect(result.key).toBe(12345)
        expect(result.canonicalName).toBe("Quercus robur")
    })

    it("defaults vernacularNames to empty array when missing", () => {
        const { vernacularNames: _, ...withoutNames } = validSummary
        const result = GbifSpeciesSummarySchema.parse(withoutNames)
        expect(result.vernacularNames).toEqual([])
    })

    it("rejects data with missing required fields", () => {
        expect(() => GbifSpeciesSummarySchema.parse({ key: 1 })).toThrow()
    })
})

describe("GbifSpeciesDetailSchema", () => {
    it("extends summary with detail fields", () => {
        const detail = {
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
            authorship: "L.",
            nameType: "SCIENTIFIC",
            numDescendants: 0,
        }
        const result = GbifSpeciesDetailSchema.parse(detail)
        expect(result.authorship).toBe("L.")
        expect(result.publishedIn).toBeUndefined()
    })
})

describe("GbifSearchResponseSchema", () => {
    it("parses search response with results array", () => {
        const response = {
            offset: 0,
            limit: 20,
            endOfRecords: false,
            count: 100,
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
        const result = GbifSearchResponseSchema.parse(response)
        expect(result.count).toBe(100)
        expect(result.results).toHaveLength(1)
    })
})

describe("GbifMediaResponseSchema", () => {
    it("parses media response", () => {
        const response = {
            results: [{ type: "StillImage", identifier: "https://example.com/img.jpg" }],
        }
        const result = GbifMediaResponseSchema.parse(response)
        expect(result.results[0].type).toBe("StillImage")
    })
})

describe("GbifVernacularNamesResponseSchema", () => {
    it("parses vernacular names response", () => {
        const response = {
            results: [{ vernacularName: "Oak", language: "eng" }],
        }
        const result = GbifVernacularNamesResponseSchema.parse(response)
        expect(result.results[0].vernacularName).toBe("Oak")
    })
})

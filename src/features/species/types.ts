import { z } from "zod"

const VernacularNameSchema = z.object({
    vernacularName: z.string(),
    language: z.string(),
})

export const GbifSpeciesSummarySchema = z.object({
    key: z.number(),
    scientificName: z.string(),
    canonicalName: z.string(),
    kingdom: z.string(),
    phylum: z.string(),
    class: z.string(),
    order: z.string(),
    family: z.string(),
    genus: z.string(),
    taxonomicStatus: z.string(),
    rank: z.string(),
    vernacularNames: z.array(VernacularNameSchema).default([]),
})

export type GbifSpeciesSummary = z.infer<typeof GbifSpeciesSummarySchema>

export const GbifSpeciesDetailSchema = GbifSpeciesSummarySchema.extend({
    authorship: z.string(),
    publishedIn: z.string().optional(),
    nameType: z.string(),
    numDescendants: z.number(),
})

export type GbifSpeciesDetail = z.infer<typeof GbifSpeciesDetailSchema>

export const GbifSearchResponseSchema = z.object({
    offset: z.number(),
    limit: z.number(),
    endOfRecords: z.boolean(),
    count: z.number(),
    results: z.array(GbifSpeciesSummarySchema),
})

export type GbifSearchResponse = z.infer<typeof GbifSearchResponseSchema>

export const GbifMediaItemSchema = z.object({
    type: z.string(),
    identifier: z.string(),
    title: z.string().optional(),
    creator: z.string().optional(),
    license: z.string().optional(),
})

export type GbifMediaItem = z.infer<typeof GbifMediaItemSchema>

export const GbifMediaResponseSchema = z.object({
    results: z.array(GbifMediaItemSchema),
})

export type GbifMediaResponse = z.infer<typeof GbifMediaResponseSchema>

export const GbifVernacularNameSchema = z.object({
    vernacularName: z.string(),
    language: z.string(),
    source: z.string().optional(),
})

export type GbifVernacularName = z.infer<typeof GbifVernacularNameSchema>

export const GbifVernacularNamesResponseSchema = z.object({
    results: z.array(GbifVernacularNameSchema),
})

export type GbifVernacularNamesResponse = z.infer<typeof GbifVernacularNamesResponseSchema>

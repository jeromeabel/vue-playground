export interface BenchmarkThreshold {
    good: number;
    poor: number;
    unit: string;
}

export interface BenchmarkResults {
    version: number;
    generatedAt: string;
    config: { iterations: number; aggregation: string; preset: string };
    thresholds: Record<string, BenchmarkThreshold>;
    approaches: Record<string, Record<string, number>>;
    metrics: string[];
}

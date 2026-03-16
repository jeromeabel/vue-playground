"""JSON envelope builders for analysis and comparison outputs."""
from datetime import datetime, timezone


def analysis_to_json(
    *,
    metrics: dict,
    source: dict,
    analysis_type: str,
    thresholds: dict,
) -> dict:
    """Wrap a single analysis in its self-describing envelope."""
    return {
        "version": 1,
        "type": analysis_type,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "metrics": metrics,
        "thresholds": thresholds,
    }


def comparison_to_json(
    *,
    approaches: dict[str, dict],
    config: dict,
    thresholds: dict,
    metric_keys: list[str],
) -> dict:
    """Wrap a comparison in the Vue app envelope.

    This produces the exact shape consumed by BenchmarkTable and TraceTable:
    { version, generatedAt, config, thresholds, approaches, metrics }
    """
    filtered_thresholds = {
        k: v for k, v in thresholds.items() if k in metric_keys
    }
    return {
        "version": 1,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "config": config,
        "thresholds": filtered_thresholds,
        "approaches": approaches,
        "metrics": metric_keys,
    }

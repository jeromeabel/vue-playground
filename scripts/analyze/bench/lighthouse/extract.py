"""Extract metrics from Lighthouse JSON reports."""

# Core Web Vitals + Lighthouse audit thresholds
# Source: https://web.dev/articles/vitals
THRESHOLDS = {
    "Score": {"good": 90, "poor": 50, "unit": "points", "higher_is_better": True},
    "FCP": {"good": 1800, "poor": 3000, "unit": "ms"},
    "LCP": {"good": 2500, "poor": 4000, "unit": "ms"},
    "TBT": {"good": 200, "poor": 600, "unit": "ms"},
    "TTI": {"good": 3800, "poor": 7300, "unit": "ms"},
    "SI": {"good": 3400, "poor": 5800, "unit": "ms"},
    "Max FID": {"good": 100, "poor": 300, "unit": "ms"},
    "CLS": {"good": 0.1, "poor": 0.25, "unit": ""},
    "DOM Size": {"good": 1500, "poor": 3000, "unit": "elements"},
    "MT Work": {"good": 2000, "poor": 4000, "unit": "ms"},
}


def status_for(metric: str, value: float | None) -> str | None:
    """Classify a metric value as pass/warn/fail/error.

    Handles both lower-is-better and higher-is-better metrics.
    Returns None for unknown metrics.
    """
    if value is None:
        return "error"

    threshold = THRESHOLDS.get(metric)
    if threshold is None:
        return None

    if threshold.get("higher_is_better"):
        if value >= threshold["good"]:
            return "pass"
        if value >= threshold["poor"]:
            return "warn"
        return "fail"

    if value <= threshold["good"]:
        return "pass"
    if value <= threshold["poor"]:
        return "warn"
    return "fail"


def extract_metrics(report: dict) -> dict:
    """Extract all relevant metrics from a Lighthouse report.

    Handles both Lighthouse 12 (CLI) and 13 (DevTools) JSON formats.
    """
    audits = report.get("audits", {})
    perf_score = report.get("categories", {}).get("performance", {}).get("score")

    def audit_val(key: str) -> float | None:
        audit = audits.get(key, {})
        if audit.get("errorMessage"):
            return None
        return audit.get("numericValue")

    def dom_size_val() -> float:
        for key in ("dom-size", "dom-size-insight"):
            val = audits.get(key, {}).get("numericValue")
            if val is not None:
                return val
        return 0

    def safe_round(val: float | None, ndigits: int = 0) -> float | None:
        return round(val, ndigits) if val is not None else None

    return {
        "Score": round(perf_score * 100) if perf_score is not None else None,
        "FCP": safe_round(audit_val("first-contentful-paint"), 1),
        "LCP": safe_round(audit_val("largest-contentful-paint"), 1),
        "TBT": safe_round(audit_val("total-blocking-time"), 1),
        "TTI": safe_round(audit_val("interactive"), 1),
        "SI": safe_round(audit_val("speed-index"), 1),
        "Max FID": safe_round(audit_val("max-potential-fid"), 1),
        "CLS": safe_round(audit_val("cumulative-layout-shift"), 4),
        "DOM Size": round(dom_size_val()),
        "MT Work": safe_round(audit_val("mainthread-work-breakdown"), 1),
    }


def extract_source(report: dict, filename: str) -> dict:
    """Extract source metadata from a Lighthouse report."""
    url = report.get("requestedUrl", "") or report.get("finalUrl", "")
    lh_version = report.get("lighthouseVersion", "")
    return {
        "filename": filename,
        "url": url,
        "lighthouseVersion": lh_version,
    }

"""Shared fixtures for lighthouse tests."""


def _make_audit(numeric_value=None, error_message=None):
    """Build a minimal Lighthouse audit dict."""
    audit = {"id": "test"}
    if numeric_value is not None:
        audit["numericValue"] = numeric_value
    if error_message is not None:
        audit["errorMessage"] = error_message
    return audit


def _make_report(
    *,
    fcp=500,
    lcp=500,
    tbt=0,
    tti=500,
    si=500,
    fid=16,
    cls_val=0,
    dom_size=1000,
    dom_key="dom-size",
    mt_work=200,
    score=1.0,
    lcp_error=None,
):
    """Build a minimal Lighthouse report dict."""
    audits = {
        "first-contentful-paint": _make_audit(fcp),
        "largest-contentful-paint": _make_audit(lcp, error_message=lcp_error),
        "total-blocking-time": _make_audit(tbt),
        "interactive": _make_audit(tti),
        "speed-index": _make_audit(si),
        "max-potential-fid": _make_audit(fid),
        "cumulative-layout-shift": _make_audit(cls_val),
        dom_key: _make_audit(dom_size),
        "mainthread-work-breakdown": _make_audit(mt_work),
    }
    return {
        "audits": audits,
        "categories": {"performance": {"score": score}},
    }

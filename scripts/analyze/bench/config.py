"""Load and merge benchmark configuration."""
import copy
import json
from pathlib import Path

# All lighthouse metrics — default to showing everything
_ALL_LIGHTHOUSE = ["Score", "FCP", "LCP", "TBT", "TTI", "SI", "Max FID", "CLS", "DOM Size", "MT Work"]
_ALL_TRACE = [
    "scripting_ms", "rendering_ms", "painting_ms",
    "scripting_ms_per_s", "rendering_ms_per_s", "painting_ms_per_s",
    "longest_task_ms", "long_tasks_count", "long_tasks_per_s",
    "top_long_tasks_ms",
    "fps", "frames_committed",
    "raf_count", "raf_total_ms", "raf_mean_ms",
    "af_count", "af_mean_ms", "af_p95_ms", "af_max_ms",
]

DEFAULT_DISPLAY = {
    "lighthouse": {"primary": list(_ALL_LIGHTHOUSE), "secondary": [], "hidden": []},
    "trace": {"primary": list(_ALL_TRACE), "secondary": [], "hidden": []},
}

_DEFAULTS = {
    "capture": {
        "preset": "desktop",
        "chromeFlags": "--incognito",
        "cpuSlowdownMultiplier": 4,
        "onlyCategories": "performance",
        "iterations": 3,
        "aggregation": "single",
    },
    "display": DEFAULT_DISPLAY,
    "approaches": {},
}


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base, returning a new dict."""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(path: str | None) -> dict:
    """Load config from file, deep-merged with defaults.

    If path is None or the file doesn't exist, returns a deep copy of defaults.
    Deep copy prevents callers from mutating the shared _DEFAULTS dict.
    """
    if path is None:
        return copy.deepcopy(_DEFAULTS)

    config_path = Path(path)
    if not config_path.exists():
        return copy.deepcopy(_DEFAULTS)

    with open(config_path) as f:
        user_config = json.load(f)

    return _deep_merge(copy.deepcopy(_DEFAULTS), user_config)

"""Extract metrics from Chrome Performance trace events."""

from collections import Counter, defaultdict

THRESHOLDS = {
    "longest_task_ms": {"good": 50, "poor": 200, "unit": "ms"},
    "fps": {"good": 55, "poor": 30, "unit": "fps"},
    "long_tasks_count": {"good": 3, "poor": 10, "unit": "count"},
    "scripting_ms_per_s": {"good": 200, "poor": 500, "unit": "ms/s"},
}

CATEGORY_MAP = {
    "Scripting": {
        "FunctionCall",
        "v8.callFunction",
        "EvaluateScript",
        "v8.compile",
        "FireAnimationFrame",
        "EventDispatch",
        "RunMicrotasks",
        "TimerFire",
    },
    "Rendering": {
        "UpdateLayoutTree",
        "Layout",
        "RecalculateStyles",
        "PrePaint",
        "Layerize",
        "Commit",
        "HitTest",
        "IntersectionObserverController::computeIntersections",
    },
    "Painting": {
        "Paint",
        "CompositeLayers",
        "RasterTask",
        "Decode Image",
    },
}

_NAME_TO_CATEGORY = {}
for _category, _names in CATEGORY_MAP.items():
    for _name in _names:
        _NAME_TO_CATEGORY[_name] = _category


def categorize(name: str) -> str:
    return _NAME_TO_CATEGORY.get(name, "Other")


def find_main_threads(events: list) -> set:
    """Find (pid, tid) pairs for CrRendererMain threads."""
    threads = set()
    for event in events:
        if event.get("ph") == "M" and event.get("name") == "thread_name":
            if event.get("args", {}).get("name") == "CrRendererMain":
                threads.add((event["pid"], event["tid"]))
    return threads


def _is_profiler_artifact(parent: dict, events: list) -> bool:
    """Check if a RunTask is dominated by CpuProfiler::StartProfiling."""
    parent_start = parent["ts"]
    parent_end = parent["ts"] + parent.get("dur", 0)
    parent_pid = parent["pid"]
    parent_tid = parent["tid"]
    for event in events:
        if (
            event.get("pid") == parent_pid
            and event.get("tid") == parent_tid
            and event.get("ph") == "X"
            and event.get("name") == "CpuProfiler::StartProfiling"
            and event.get("ts", 0) >= parent_start
            and event.get("ts", 0) + event.get("dur", 0) <= parent_end
        ):
            return True
    return False


def analyze_trace(events: list[dict]) -> dict | None:
    """Analyze Chrome trace events. Returns None if not a valid trace."""
    main_threads = find_main_threads(events)
    if not main_threads:
        return None

    timestamps = []
    max_end = 0
    for event in events:
        if (event.get("pid"), event.get("tid")) not in main_threads:
            continue
        if event.get("ph") != "X":
            continue
        timestamp = event.get("ts", 0)
        duration = event.get("dur", 0)
        timestamps.append(timestamp)
        end = timestamp + duration
        if end > max_end:
            max_end = end

    if not timestamps:
        return None

    trace_start = min(timestamps)
    trace_end = max(max_end, max(timestamps))
    duration_us = trace_end - trace_start
    duration_s = duration_us / 1_000_000

    totals = defaultdict(float)
    for event in events:
        if (event.get("pid"), event.get("tid")) not in main_threads:
            continue
        if event.get("ph") != "X":
            continue
        category = categorize(event.get("name", ""))
        if category != "Other":
            totals[category] += event.get("dur", 0) / 1000

    long_tasks = []
    for event in events:
        if (event.get("pid"), event.get("tid")) not in main_threads:
            continue
        if event.get("ph") != "X" or event.get("name") != "RunTask":
            continue
        duration_ms = event.get("dur", 0) / 1000
        if duration_ms > 50 and not _is_profiler_artifact(event, events):
            long_tasks.append(duration_ms)
    long_tasks.sort(reverse=True)

    frame_events = Counter()
    for event in events:
        if (event.get("pid"), event.get("tid")) not in main_threads:
            continue
        name = event.get("name", "")
        if name in ("BeginMainThreadFrame", "Commit", "Paint"):
            frame_events[name] += 1

    commits = frame_events.get("Commit", frame_events.get("BeginMainThreadFrame", 0))
    fps = commits / duration_s if duration_s > 0 else 0

    interaction_types = {
        "scroll",
        "scrollend",
        "wheel",
        "mousedown",
        "mouseup",
        "click",
        "dblclick",
        "pointerdown",
        "pointerup",
        "pointermove",
        "keydown",
        "keyup",
        "keypress",
        "touchstart",
        "touchmove",
        "touchend",
    }
    has_scroll = False
    has_interaction = False
    for event in events:
        if (event.get("pid"), event.get("tid")) not in main_threads:
            continue
        if event.get("name") == "EventDispatch":
            event_type = event.get("args", {}).get("data", {}).get("type", "")
            if event_type in interaction_types:
                has_interaction = True
            if event_type in ("scroll", "scrollend", "wheel"):
                has_scroll = True

    af_durations = []
    for event in events:
        if (event.get("pid"), event.get("tid")) not in main_threads:
            continue
        if event.get("ph") == "X" and event.get("name") == "AnimationFrame":
            af_durations.append(event.get("dur", 0) / 1000)
    af_durations.sort()

    raf_durations = []
    for event in events:
        if (event.get("pid"), event.get("tid")) not in main_threads:
            continue
        if event.get("ph") == "X" and event.get("name") == "FireAnimationFrame":
            raf_durations.append(event.get("dur", 0) / 1000)

    safe_duration = max(duration_s, 0.01)

    return {
        "source": {
            "duration_s": round(duration_s, 2),
            "has_interaction": has_interaction,
            "has_scroll": has_scroll,
        },
        "metrics": {
            "scripting_ms": round(totals.get("Scripting", 0), 1),
            "rendering_ms": round(totals.get("Rendering", 0), 1),
            "painting_ms": round(totals.get("Painting", 0), 1),
            "scripting_ms_per_s": round(totals.get("Scripting", 0) / safe_duration, 1),
            "rendering_ms_per_s": round(totals.get("Rendering", 0) / safe_duration, 1),
            "painting_ms_per_s": round(totals.get("Painting", 0) / safe_duration, 1),
            "long_tasks_count": len(long_tasks),
            "long_tasks_per_s": round(len(long_tasks) / safe_duration, 2),
            "longest_task_ms": round(long_tasks[0], 1) if long_tasks else 0,
            "top_long_tasks_ms": [round(task, 1) for task in long_tasks[:5]],
            "frames_committed": commits,
            "fps": round(fps, 1),
            "af_count": len(af_durations) if af_durations else 0,
            "af_mean_ms": round(sum(af_durations) / len(af_durations), 2) if af_durations else None,
            "af_p95_ms": round(af_durations[int(len(af_durations) * 0.95)], 2) if af_durations else None,
            "af_max_ms": round(af_durations[-1], 2) if af_durations else None,
            "raf_count": len(raf_durations) if raf_durations else 0,
            "raf_total_ms": round(sum(raf_durations), 1) if raf_durations else None,
            "raf_mean_ms": round(sum(raf_durations) / len(raf_durations), 2) if raf_durations else None,
        },
    }


def extract_source(result: dict, filename: str) -> dict:
    """Build source metadata from analyze_trace result and filename."""
    source = result["source"]
    return {
        "filename": filename,
        "durationS": source["duration_s"],
        "hasInteraction": source["has_interaction"],
        "hasScroll": source["has_scroll"],
    }

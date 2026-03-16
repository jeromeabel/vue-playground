"""Shared fixtures for trace tests."""


def _thread_name_event(pid, tid, name):
    return {
        "ph": "M",
        "name": "thread_name",
        "pid": pid,
        "tid": tid,
        "args": {"name": name},
    }


def _duration_event(pid, tid, name, ts, dur):
    return {
        "ph": "X",
        "name": name,
        "pid": pid,
        "tid": tid,
        "ts": ts,
        "dur": dur,
    }


def _make_events(*, num_tasks=5, task_dur_us=100_000, include_long_task=False):
    """Build trace events with a CrRendererMain thread and RunTask events."""
    pid, tid = 100, 1
    events = [_thread_name_event(pid, tid, "CrRendererMain")]
    timestamp = 1_000_000

    for _ in range(num_tasks):
        events.append(_duration_event(pid, tid, "RunTask", timestamp, task_dur_us))
        events.append(
            _duration_event(
                pid,
                tid,
                "FunctionCall",
                timestamp + 1000,
                task_dur_us - 2000,
            )
        )
        timestamp += task_dur_us + 10_000

    if include_long_task:
        long_duration = 200_000
        events.append(_duration_event(pid, tid, "RunTask", timestamp, long_duration))
        events.append(
            _duration_event(
                pid,
                tid,
                "EvaluateScript",
                timestamp + 1000,
                long_duration - 2000,
            )
        )
        timestamp += long_duration + 10_000

    events.append(_duration_event(pid, tid, "Layout", timestamp, 5_000))
    events.append(_duration_event(pid, tid, "Paint", timestamp + 6_000, 2_000))
    for i in range(3):
        events.append(_duration_event(pid, tid, "Commit", timestamp + 10_000 * i, 1_000))

    return events

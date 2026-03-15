import json
from pathlib import Path

import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: marks tests that load large trace files (deselect with -m 'not slow')")

SAMPLE_DIR = Path(__file__).resolve().parents[3] / ".docs" / "resources" / "epic-performance" / "sc-63108-call-details-performance"

@pytest.fixture
def lighthouse_before():
    """Load the before-optimization Lighthouse report as a dict."""
    path = next((SAMPLE_DIR / "performance-before").glob("localhost_3000-*.json"))
    with open(path) as f:
        return json.load(f)

@pytest.fixture
def lighthouse_phase3():
    """Load the phase3-optimization Lighthouse report as a dict."""
    path = next((SAMPLE_DIR / "performance-phase3").glob("localhost_3000-*.json"))
    with open(path) as f:
        return json.load(f)

@pytest.fixture
def trace_before_path():
    """Return path string to before-optimization trace file (70-80MB, don't load in fixture)."""
    path = next((SAMPLE_DIR / "performance-before").glob("Trace-*.json"))
    return str(path)

@pytest.fixture
def trace_phase3_path():
    """Return path string to phase3-optimization trace file."""
    path = next((SAMPLE_DIR / "performance-phase3").glob("Trace-*.json"))
    return str(path)

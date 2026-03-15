import json
from pathlib import Path

import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: marks tests that load large trace files (deselect with -m 'not slow')")

REPORTS_DIR = Path(__file__).resolve().parents[1] / "reports"

@pytest.fixture
def lighthouse_basic():
    """Load the basic-table Lighthouse report as a dict."""
    with open(REPORTS_DIR / "basic.json") as f:
        return json.load(f)

@pytest.fixture
def lighthouse_primevue():
    """Load the primevue-table Lighthouse report as a dict."""
    with open(REPORTS_DIR / "primevue.json") as f:
        return json.load(f)

@pytest.fixture
def lighthouse_tanstack():
    """Load the tanstack-table Lighthouse report as a dict."""
    with open(REPORTS_DIR / "tanstack.json") as f:
        return json.load(f)

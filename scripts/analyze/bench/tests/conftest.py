"""Shared fixtures for bench-level (non-domain) tests."""
import json
import pytest
from pathlib import Path


@pytest.fixture
def config_file(tmp_path):
    """Write a temporary benchmark-config.json and return its path."""
    def _write(data: dict) -> str:
        p = tmp_path / "benchmark-config.json"
        p.write_text(json.dumps(data))
        return str(p)
    return _write

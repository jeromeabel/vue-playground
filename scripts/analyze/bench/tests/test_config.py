"""Tests for bench.config — config loading and merging."""
import json
import pytest
from bench.config import load_config, DEFAULT_DISPLAY


class TestLoadConfig:
    def test_loads_valid_config(self, config_file):
        path = config_file({
            "capture": {"preset": "mobile"},
            "display": {
                "lighthouse": {"primary": ["Score", "TBT"]},
            },
            "approaches": {"a": {"label": "Approach A"}},
        })
        cfg = load_config(path)
        assert cfg["capture"]["preset"] == "mobile"
        assert cfg["display"]["lighthouse"]["primary"] == ["Score", "TBT"]
        assert cfg["approaches"]["a"]["label"] == "Approach A"

    def test_missing_file_returns_defaults(self):
        cfg = load_config("/nonexistent/path.json")
        assert "capture" in cfg
        assert "display" in cfg
        assert "approaches" in cfg

    def test_none_path_returns_defaults(self):
        cfg = load_config(None)
        assert "capture" in cfg

    def test_partial_config_merges_with_defaults(self, config_file):
        path = config_file({"capture": {"preset": "mobile"}})
        cfg = load_config(path)
        # Custom value
        assert cfg["capture"]["preset"] == "mobile"
        # Default values preserved
        assert "display" in cfg
        assert "lighthouse" in cfg["display"]

    def test_default_display_shows_all_as_primary(self):
        """Without a config file, no metrics are hidden."""
        cfg = load_config(None)
        assert cfg["display"]["lighthouse"]["hidden"] == []
        assert cfg["display"]["trace"]["hidden"] == []

    def test_none_returns_independent_copies(self):
        """Each call returns a fresh deep copy — mutating one must not affect the next."""
        cfg1 = load_config(None)
        cfg1["display"]["lighthouse"]["hidden"].append("Score")
        cfg2 = load_config(None)
        assert cfg2["display"]["lighthouse"]["hidden"] == []

    def test_file_load_returns_independent_copies(self, config_file):
        """File-loaded configs must also be independent of _DEFAULTS."""
        path = config_file({"capture": {"preset": "mobile"}})
        cfg1 = load_config(path)
        cfg1["display"]["trace"]["hidden"].append("fps")
        cfg2 = load_config(path)
        assert cfg2["display"]["trace"]["hidden"] == []


class TestDefaultDisplay:
    def test_has_lighthouse_and_trace(self):
        assert "lighthouse" in DEFAULT_DISPLAY
        assert "trace" in DEFAULT_DISPLAY

    def test_each_has_primary_secondary_hidden(self):
        for key in ("lighthouse", "trace"):
            d = DEFAULT_DISPLAY[key]
            assert "primary" in d
            assert "secondary" in d
            assert "hidden" in d

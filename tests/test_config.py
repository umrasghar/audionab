"""Tests for audionab.config — no GUI or FFmpeg required."""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audionab.config import Config


class TestConfig:
    def setup_method(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp.close()
        self.config_path = self.tmp.name

    def teardown_method(self):
        try:
            os.unlink(self.config_path)
        except Exception:
            pass

    def test_defaults(self):
        config = Config(self.config_path)
        assert config.get("bitrate") == "192k"
        assert config.get("output_same_folder") is True
        assert config.get("appearance_mode") == "Dark"

    def test_set_and_get(self):
        config = Config(self.config_path)
        config.set("bitrate", "320k")
        assert config.get("bitrate") == "320k"

    def test_persistence(self):
        config1 = Config(self.config_path)
        config1.set("bitrate", "256k")

        config2 = Config(self.config_path)
        assert config2.get("bitrate") == "256k"

    def test_missing_key_returns_none(self):
        config = Config(self.config_path)
        assert config.get("nonexistent_key") is None

    def test_corrupt_file(self):
        with open(self.config_path, "w") as f:
            f.write("not valid json{{{")
        config = Config(self.config_path)
        assert config.get("bitrate") == "192k"  # Falls back to defaults

    def test_nonexistent_path(self):
        config = Config(os.path.join(tempfile.gettempdir(), "nonexistent_audionab_cfg.json"))
        assert config.get("bitrate") == "192k"

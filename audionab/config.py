"""Application configuration management."""

import json
import logging
import os

from . import DEFAULT_BITRATE, DEFAULT_OUTPUT_POSTFIX

logger = logging.getLogger(__name__)


class Config:
    DEFAULTS = {
        "bitrate": DEFAULT_BITRATE,
        "output_format": "MP3",
        "output_postfix": DEFAULT_OUTPUT_POSTFIX,
        "output_same_folder": True,
        "custom_output_folder": "",
        "context_menu_installed": False,
        "appearance_mode": "Dark",
        "deepgram_api_key": "",
        "auto_transcribe": False,
        "watch_folder": "",
        "watch_enabled": False,
        "minimize_to_tray": False,
        "close_to_tray": False,
    }

    def __init__(self, config_path):
        self.path = config_path
        self.data = dict(self.DEFAULTS)
        self.load()

    def load(self):
        try:
            if os.path.exists(self.path):
                with open(self.path, "r") as f:
                    self.data.update(json.load(f))
        except Exception:
            logger.warning("Failed to load config from %s", self.path, exc_info=True)

    def save(self):
        try:
            with open(self.path, "w") as f:
                json.dump(self.data, f, indent=2)
        except Exception:
            logger.warning("Failed to save config to %s", self.path, exc_info=True)

    def get(self, key):
        return self.data.get(key, self.DEFAULTS.get(key))

    def set(self, key, value):
        self.data[key] = value
        self.save()

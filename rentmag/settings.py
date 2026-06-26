"""User settings persistence (config.json)."""

import json
from pathlib import Path

CONFIG_FILE = Path(__file__).parent.parent / "config.json"

DEFAULTS: dict = {
    # Google Sheets
    "credentials_path": "",
    "sheet_name":       "物件管理番号マスター",
    # File paths
    "last_input_dir":   "",
    "last_output_dir":  "",
    "last_logo_path":   "",
    # Property fields (mirrors the inline form on the main screen)
    "last_management_number": "",
    "last_property":          "",
    "last_building":          "",
    "last_room":              "",
    "last_display_name":      "",
    "last_city":              "",
    "last_type":              "",
    "last_status":            "",
    "last_hiragana":          "",
    "last_station":           "",
    "last_image_type":        "リビング",
    "last_notes":             "",
    "last_wp_id":             "",
    "last_wp_url":            "",
}


class SettingsManager:
    """Thin JSON-backed key-value store for user preferences."""

    def __init__(self):
        self._data = dict(DEFAULTS)
        self._load()

    def _load(self) -> None:
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, encoding="utf-8") as f:
                    self._data.update(json.load(f))
        except Exception:
            pass

    def save(self) -> None:
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def get(self, key: str, default: str = "") -> str:
        return self._data.get(key, DEFAULTS.get(key, default))

    def set(self, key: str, value) -> None:
        self._data[key] = value

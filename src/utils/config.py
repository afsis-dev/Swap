# Histórico de Alterações:
#   Data       | Desenvolvedor  | Ticket | Observação
#   -----------|----------------|--------|-------------------
#   2026-05-13 | AFSIS Dev      | #001   | Implementação v1.1.0


import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

from src.utils.logger import get_logger

logger = get_logger(__name__)

CONFIG_DIR = Path.home() / ".fileconverter"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "output_dir": str(Path.home() / "FileConverter"),
    "max_workers": 4,
    "default_format": "",
    "theme_mode": "system",
    "language": "pt-BR",
    "quality_jpeg": 85,
    "dpi": 150,
    "csv_separator": ",",
    "csv_encoding": "utf-8",
}


def _ensure_config_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    _ensure_config_dir()
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            merged = {**DEFAULT_CONFIG, **config}
            logger.info("Config loaded from %s", CONFIG_FILE)
            return merged
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to load config, using defaults: %s", e)
    return {**DEFAULT_CONFIG}


def save_config(config: dict) -> None:
    _ensure_config_dir()
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        logger.info("Config saved to %s", CONFIG_FILE)
    except OSError as e:
        logger.error("Failed to save config: %s", e)


def get_setting(key: str, default=None):
    config = load_config()
    return config.get(key, default)


def set_setting(key: str, value) -> None:
    config = load_config()
    config[key] = value
    save_config(config)

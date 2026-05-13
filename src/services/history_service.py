# Histórico de Alterações:
#   Data       | Desenvolvedor  | Ticket | Observação
#   -----------|----------------|--------|-------------------
#   2026-05-13 | AFSIS Dev      | #001   | Implementação v1.1.0


import json
import os
import uuid
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.converters.base import ConversionResult
from src.utils.logger import get_logger

logger = get_logger(__name__)

MAX_HISTORY = 100

HISTORY_DIR = Path.home() / ".fileconverter"
HISTORY_FILE = HISTORY_DIR / "history.json"


def _ensure_dir():
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def load_history() -> list[dict]:
    _ensure_dir()
    if not HISTORY_FILE.exists():
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to load history: %s", e)
        return []


def save_history(entries: list[dict]) -> None:
    _ensure_dir()
    limited = entries[-MAX_HISTORY:]
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(limited, f, indent=2, ensure_ascii=False, default=str)
    except OSError as e:
        logger.error("Failed to save history: %s", e)


def add_conversion(result: ConversionResult | dict) -> None:
    history = load_history()

    if isinstance(result, dict):
        entry = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "input_file": result.get("input_file", ""),
            "output_file": result.get("output_file", ""),
            "format": result.get("format", ""),
            "status": result.get("status", "success"),
            "duration_ms": result.get("duration_ms", 0),
        }
    else:
        entry = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "input_file": str(result.input_path),
            "output_file": str(result.output_path) if result.output_path else "",
            "format": result.output_path.suffix.lower() if result.output_path else "",
            "status": "success" if result.success else "error",
            "duration_ms": result.duration_ms,
        }

    history.append(entry)
    save_history(history)


def clear_history() -> None:
    _ensure_dir()
    if HISTORY_FILE.exists():
        HISTORY_FILE.unlink()


def get_entries(limit: int = 50, offset: int = 0) -> list[dict]:
    history = load_history()
    reversed_history = list(reversed(history))
    return reversed_history[offset:offset + limit]


def count() -> int:
    return len(load_history())


def delete(entry_id: str) -> bool:
    history = load_history()
    new_history = [e for e in history if e.get("id") != entry_id]
    if len(new_history) == len(history):
        return False
    save_history(new_history)
    return True


def get_recent_conversions(limit: int = 20) -> list[dict]:
    history = load_history()
    return list(reversed(history[-limit:]))

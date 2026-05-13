# Histórico de Alterações:
#   Data       | Desenvolvedor  | Ticket | Observação
#   -----------|----------------|--------|-------------------
#   2026-05-13 | AFSIS Dev      | #001   | Implementação v1.1.0


import pytest
import tempfile
import json
from pathlib import Path
from src.utils.config import load_config, save_config, get_setting, set_setting, CONFIG_FILE, DEFAULT_CONFIG
from src.utils.file_utils import (
    ensure_output_dir,
    unique_filename,
    get_output_path,
    validate_input_file,
    format_size,
    format_duration,
)


class TestConfig:

    def setup_method(self):
        if CONFIG_FILE.exists():
            CONFIG_FILE.unlink()

    def teardown_method(self):
        if CONFIG_FILE.exists():
            CONFIG_FILE.unlink()

    def test_load_default_config(self):
        config = load_config()
        assert config == DEFAULT_CONFIG

    def test_save_and_load_config(self):
        custom = {**DEFAULT_CONFIG, "max_workers": 8, "quality_jpeg": 90}
        save_config(custom)
        loaded = load_config()
        assert loaded["max_workers"] == 8
        assert loaded["quality_jpeg"] == 90

    def test_get_setting(self):
        save_config({**DEFAULT_CONFIG, "dpi": 300})
        assert get_setting("dpi") == 300
        assert get_setting("nonexistent", "fallback") == "fallback"

    def test_set_setting(self):
        set_setting("theme_mode", "dark")
        assert get_setting("theme_mode") == "dark"

    def test_config_file_created(self):
        save_config(DEFAULT_CONFIG)
        assert CONFIG_FILE.exists()
        content = json.loads(CONFIG_FILE.read_text())
        assert content["max_workers"] == 4


class TestFileUtils:

    def test_ensure_output_dir(self, tmp_path):
        new_dir = tmp_path / "a" / "b" / "c"
        result = ensure_output_dir(new_dir)
        assert result.exists()
        assert result.is_dir()

    def test_ensure_existing_dir(self, tmp_path):
        existing = tmp_path / "exists"
        existing.mkdir()
        result = ensure_output_dir(existing)
        assert result == existing

    def test_unique_filename_no_conflict(self, tmp_path):
        path = tmp_path / "test.txt"
        result = unique_filename(path)
        assert result == path

    def test_unique_filename_conflict(self, tmp_path):
        path = tmp_path / "test.txt"
        path.touch()
        result = unique_filename(path)
        assert result.name == "test_1.txt"
        assert result != path

    def test_unique_filename_multiple_conflicts(self, tmp_path):
        path = tmp_path / "test.txt"
        path.touch()
        (tmp_path / "test_1.txt").touch()
        (tmp_path / "test_2.txt").touch()
        result = unique_filename(path)
        assert result.name == "test_3.txt"

    def test_get_output_path(self, tmp_path):
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        input_file = input_dir / "photo.jpg"
        input_file.touch()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        result = get_output_path(input_file, output_dir, ".png")
        assert result == output_dir / "photo.png"

    def test_validate_input_file(self, tmp_path):
        valid = tmp_path / "valid.txt"
        valid.write_text("content")
        assert validate_input_file(valid) is True

        nonexistent = tmp_path / "nope.txt"
        assert validate_input_file(nonexistent) is False

    def test_format_size(self):
        assert format_size(500) == "500.0 B"
        assert format_size(1024) == "1.0 KB"
        assert format_size(1048576) == "1.0 MB"
        assert format_size(1073741824) == "1.0 GB"

    def test_format_duration(self):
        assert format_duration(500) == "500 ms"
        assert format_duration(1500) == "1.5 s"
        assert format_duration(65000) == "1m 5s"

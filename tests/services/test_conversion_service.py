# Histórico de Alterações:
#   Data       | Desenvolvedor  | Ticket | Observação
#   -----------|----------------|--------|-------------------
#   2026-05-13 | AFSIS Dev      | #001   | Implementação v1.1.0


import pytest
import tempfile
import time
from pathlib import Path
from src.services.conversion_service import ConversionService, BatchProgress
from src.services.history_service import (
    load_history,
    save_history,
    add_conversion,
    clear_history,
    get_recent_conversions,
)
from src.converters.base import ConversionResult


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def sample_files(tmp_dir):
    from PIL import Image
    files = []
    for i in range(3):
        img = Image.new("RGB", (50, 50), color=(i * 80, 100, 100))
        path = tmp_dir / f"test_{i}.jpg"
        img.save(str(path), "JPEG")
        files.append(path)
    return files


class TestConversionService:

    def test_convert_single(self, tmp_dir, sample_files):
        service = ConversionService(max_workers=2)
        output_dir = tmp_dir / "output"
        output_dir.mkdir()

        result = service.convert_single(
            sample_files[0], output_dir, ".png"
        )
        assert result.success is True
        assert result.output_path is not None
        assert result.output_path.exists()

    def test_batch_conversion(self, tmp_dir, sample_files):
        service = ConversionService(max_workers=2)
        output_dir = tmp_dir / "output"
        output_dir.mkdir()

        progress_calls = []

        def on_progress(bp: BatchProgress):
            progress_calls.append(bp)

        results = service.convert_batch(
            sample_files, output_dir, ".png", progress_callback=on_progress
        )

        assert len(results) == 3
        assert all(r.success for r in results)
        assert len(progress_calls) == 3

    def test_batch_partial_failure(self, tmp_dir, sample_files):
        service = ConversionService(max_workers=2)
        output_dir = tmp_dir / "output"
        output_dir.mkdir()

        files = sample_files + [tmp_dir / "nonexistent.jpg"]

        results = service.convert_batch(files, output_dir, ".png")

        success_count = sum(1 for r in results if r.success)
        error_count = sum(1 for r in results if not r.success)

        assert success_count == 3
        assert error_count == 1

    def test_progress_callback_called(self, tmp_dir, sample_files):
        service = ConversionService(max_workers=1)
        output_dir = tmp_dir / "output"
        output_dir.mkdir()

        progress_calls = []

        def on_progress(bp: BatchProgress):
            progress_calls.append(bp)

        service.convert_batch(
            sample_files, output_dir, ".png", progress_callback=on_progress
        )

        assert len(progress_calls) == len(sample_files)


class TestHistoryService:

    def setup_method(self):
        clear_history()

    def test_add_and_load(self, tmp_path):
        result = ConversionResult(
            success=True,
            input_path=tmp_path / "in.jpg",
            output_path=tmp_path / "out.png",
            duration_ms=150.0,
            input_size=1024,
            output_size=2048,
        )
        add_conversion(result)

        history = load_history()
        assert len(history) == 1
        assert history[0]["status"] == "success"
        assert history[0]["input_file"] == str(tmp_path / "in.jpg")

    def test_history_persist_reload(self, tmp_path):
        result = ConversionResult(
            success=True,
            input_path=tmp_path / "a.jpg",
            output_path=tmp_path / "b.png",
            duration_ms=100.0,
        )
        add_conversion(result)

        history = load_history()
        assert len(history) == 1

        history2 = load_history()
        assert len(history2) == 1

    def test_max_history(self, tmp_path):
        for i in range(120):
            result = ConversionResult(
                success=True,
                input_path=tmp_path / f"file_{i}.jpg",
                output_path=tmp_path / f"file_{i}.png",
                duration_ms=50.0,
            )
            add_conversion(result)

        history = load_history()
        assert len(history) == 100

    def test_get_recent_conversions(self, tmp_path):
        for i in range(10):
            result = ConversionResult(
                success=True,
                input_path=tmp_path / f"f{i}.jpg",
                output_path=tmp_path / f"f{i}.png",
                duration_ms=50.0,
            )
            add_conversion(result)

        recent = get_recent_conversions(limit=5)
        assert len(recent) == 5

    def test_clear_history(self, tmp_path):
        result = ConversionResult(
            success=True,
            input_path=tmp_path / "x.jpg",
            output_path=tmp_path / "x.png",
            duration_ms=50.0,
        )
        add_conversion(result)
        clear_history()
        assert len(load_history()) == 0

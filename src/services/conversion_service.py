# Histórico de Alterações:
#   Data       | Desenvolvedor  | Ticket | Observação
#   -----------|----------------|--------|-------------------
#   2026-05-13 | AFSIS Dev      | #001   | Implementação v1.1.0


import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from src.converters.base import ConversionResult, UnsupportedFormatError
from src.services.format_registry import get_converter, get_output_formats_for
from src.services.history_service import add_conversion
from src.utils.config import get_setting
from src.utils.file_utils import ensure_output_dir, get_output_path, format_size
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class BatchProgress:
    file_name: str
    current: int
    total: int
    status: str  # "pending", "converting", "done", "error"
    percent: float = 0.0


ProgressCallback = Callable[[BatchProgress], None]


class ConversionService:

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers

    def convert_single(
        self,
        input_path: Path,
        output_dir: Path,
        target_ext: str,
        options: Optional[dict] = None,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> ConversionResult:
        start_time = time.perf_counter()
        input_size = input_path.stat().st_size if input_path.exists() else 0

        try:
            converter = get_converter(input_path)
            converter.options = options or {}
            output_path = get_output_path(input_path, output_dir, target_ext)
            ensure_output_dir(output_path.parent)

            converter.convert(input_path, output_path, progress_callback)

            duration_ms = (time.perf_counter() - start_time) * 1000
            output_size = output_path.stat().st_size if output_path.exists() else 0

            result = ConversionResult(
                success=True,
                input_path=input_path,
                output_path=output_path,
                duration_ms=duration_ms,
                input_size=input_size,
                output_size=output_size,
            )
            add_conversion(result)
            logger.info(
                "Converted %s → %s (%.0f ms, %s → %s)",
                input_path.name, output_path.name, duration_ms,
                format_size(input_size), format_size(output_size),
            )
            return result

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            result = ConversionResult(
                success=False,
                input_path=input_path,
                duration_ms=duration_ms,
                input_size=input_size,
                error=str(e),
            )
            add_conversion(result)
            logger.error("Failed to convert %s: %s", input_path.name, e)
            return result

    def convert_batch(
        self,
        files: list[Path],
        output_dir: Path,
        target_ext: str,
        options: Optional[dict] = None,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> list[ConversionResult]:
        total = len(files)
        max_workers = min(self.max_workers, total, os.cpu_count() or 4)

        results: list[Optional[ConversionResult]] = [None] * total

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            for i, file_path in enumerate(files):
                future = executor.submit(
                    self.convert_single,
                    file_path,
                    output_dir,
                    target_ext,
                    options,
                )
                futures[future] = i

            completed = 0
            for future in as_completed(futures):
                idx = futures[future]
                completed += 1
                try:
                    result = future.result()
                    results[idx] = result
                except Exception as e:
                    results[idx] = ConversionResult(
                        success=False,
                        input_path=files[idx],
                        error=str(e),
                    )

                if progress_callback:
                    bp = BatchProgress(
                        file_name=files[idx].name,
                        current=completed,
                        total=total,
                        status="done" if results[idx].success else "error",
                        percent=completed / total,
                    )
                    progress_callback(bp)

        return [r for r in results if r is not None]

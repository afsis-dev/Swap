# Histórico de Alterações:
#   Data       | Desenvolvedor  | Ticket | Observação
#   -----------|----------------|--------|-------------------
#   2026-05-13 | AFSIS Dev      | #001   | Implementação v1.1.0


from pathlib import Path
from typing import Optional


def ensure_output_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def unique_filename(output_path: Path) -> Path:
    if not output_path.exists():
        return output_path
    stem = output_path.stem
    suffix = output_path.suffix
    parent = output_path.parent
    counter = 1
    while True:
        new_path = parent / f"{stem}_{counter}{suffix}"
        if not new_path.exists():
            return new_path
        counter += 1


def get_output_path(input_path: Path, output_dir: Path, target_ext: str) -> Path:
    new_name = input_path.stem + target_ext
    output_path = output_dir / new_name
    return unique_filename(output_path)


def validate_input_file(file_path: Path) -> bool:
    return file_path.is_file() and file_path.stat().st_size > 0


def format_size(size_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def format_duration(ms: float) -> str:
    if ms < 1000:
        return f"{ms:.0f} ms"
    elif ms < 60000:
        return f"{ms / 1000:.1f} s"
    else:
        minutes = int(ms / 60000)
        seconds = int((ms % 60000) / 1000)
        return f"{minutes}m {seconds}s"

# Histórico de Alterações:
#   Data       | Desenvolvedor  | Ticket | Observação
#   -----------|----------------|--------|-------------------
#   2026-05-13 | AFSIS Dev      | #001   | Implementação v1.1.0


import shutil
import tempfile
from pathlib import Path
from typing import Callable, Optional

from src.converters.base import BaseConverter, ConversionError
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _find_libreoffice() -> Optional[str]:
    for name in ["libreoffice", "soffice"]:
        path = shutil.which(name)
        if path:
            return path
    for loc in [
        "/usr/bin/libreoffice",
        "/usr/bin/soffice",
        "/opt/libreoffice/program/soffice",
        "/snap/bin/libreoffice",
    ]:
        if Path(loc).exists():
            return loc
    return None


def _lo_convert(input_path: Path, output_dir: Path, target_format: str) -> Path:
    from src.converters.document import _libreoffice_convert
    return _libreoffice_convert(input_path, output_dir, target_format)


class PresentationConverter(BaseConverter):

    def supported_input_formats(self) -> list[str]:
        return [".ppt", ".pptx", ".odp", ".pps", ".ppsx", ".pptm", ".pot", ".potx", ".potm", ".ppsm"]

    def supported_output_formats(self) -> list[str]:
        outputs = [".pdf"]
        lo = _find_libreoffice()
        if lo:
            outputs.extend([".pptx", ".odp", ".png"])
        return outputs

    def category(self) -> str:
        return "Apresentacao"

    def get_options_schema(self) -> dict:
        return {
            "dpi": {"type": "int", "min": 72, "max": 600, "default": 150, "label": "DPI (para imagem)"},
        }

    def convert(
        self,
        input_path: Path,
        output_path: Path,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> None:
        ext_in = input_path.suffix.lower()
        ext_out = output_path.suffix.lower()

        if not self.can_convert(ext_in, ext_out):
            raise ConversionError(f"Nao e possivel converter {ext_in} -> {ext_out}")

        if ext_in == ext_out:
            shutil.copy2(input_path, output_path)
            if progress_callback:
                progress_callback(1.0)
            return

        libreoffice = _find_libreoffice()
        if not libreoffice:
            raise ConversionError(
                "LibreOffice nao encontrado. Para converter apresentacoes, instale:\n"
                "  Ubuntu/Debian: sudo apt install libreoffice-impress\n"
                "  Fedora: sudo dnf install libreoffice-impress\n"
                "  macOS: brew install libreoffice"
            )

        if ext_out == ".png":
            self._to_images(input_path, output_path, progress_callback)
            return

        lo_format = ext_out.lstrip(".")
        format_map = {
            "pptx": "pptx",
            "odp": "odp",
            "pdf": "pdf",
        }
        lo_format = format_map.get(lo_format, lo_format)

        if progress_callback:
            progress_callback(0.2)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_p = Path(tmpdir)
            result = _lo_convert(input_path, tmpdir_p, lo_format)
            if progress_callback:
                progress_callback(0.8)

            if result.suffix.lower() != output_path.suffix.lower():
                result = result.rename(output_path)
            else:
                shutil.move(str(result), str(output_path))

            if progress_callback:
                progress_callback(1.0)

    def _to_images(
        self,
        input_path: Path,
        output_path: Path,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> None:
        from src.converters.document import _libreoffice_convert

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_p = Path(tmpdir)
            if progress_callback:
                progress_callback(0.2)

            result = _lo_convert(input_path, tmpdir_p, "pdf")
            if progress_callback:
                progress_callback(0.5)

            try:
                import fitz
                dpi = self.options.get("dpi", 150)
                zoom = dpi / 72
                doc = fitz.open(str(result))
                if len(doc) == 1:
                    page = doc[0]
                    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
                    pix.save(str(output_path))
                else:
                    page = doc[0]
                    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
                    pix.save(str(output_path))
                doc.close()
            except ImportError:
                shutil.copy2(result, output_path.with_suffix(".pdf"))

            if progress_callback:
                progress_callback(1.0)
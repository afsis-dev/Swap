# Histórico de Alterações:
#   Data       | Desenvolvedor  | Ticket | Observação
#   -----------|----------------|--------|-------------------
#   2026-05-13 | AFSIS Dev      | #001   | Implementação v1.1.0


import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable, Optional

from src.converters.base import BaseConverter, ConversionError
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PDFConverter(BaseConverter):

    def __init__(self, options: Optional[dict] = None):
        super().__init__(options)
        self._has_fitz = False
        try:
            import fitz
            self._has_fitz = True
        except ImportError:
            pass

        self._has_pdf2docx = False
        try:
            import pdf2docx
            self._has_pdf2docx = True
        except ImportError:
            pass

    def supported_input_formats(self) -> list[str]:
        return [".pdf"]

    def supported_output_formats(self) -> list[str]:
        return [".png", ".docx", ".txt"]

    def category(self) -> str:
        return "PDF"

    def get_options_schema(self) -> dict:
        return {
            "dpi": {"type": "int", "min": 72, "max": 600, "default": 150, "label": "DPI"},
            "page_range": {"type": "str", "default": "", "label": "Páginas (ex: 1-3,5)"},
        }

    def convert(
        self,
        input_path: Path,
        output_path: Path,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> None:
        ext_out = output_path.suffix.lower()

        if not self._has_fitz:
            raise ConversionError("PyMuPDF (fitz) não está instalado. Instale com: pip install PyMuPDF")

        if ext_out == ".png":
            self._pdf_to_png(input_path, output_path, progress_callback)
        elif ext_out == ".docx":
            self._pdf_to_docx(input_path, output_path, progress_callback)
        elif ext_out == ".txt":
            self._pdf_to_txt(input_path, output_path, progress_callback)
        else:
            raise ConversionError(f"Formato de saída não suportado: {ext_out}")

    def _parse_page_range(self) -> Optional[list[int]]:
        page_range_str = self.options.get("page_range", "").strip()
        if not page_range_str:
            return None
        pages = []
        for part in page_range_str.split(","):
            part = part.strip()
            if "-" in part:
                try:
                    start, end = part.split("-", 1)
                    pages.extend(range(int(start), int(end) + 1))
                except ValueError:
                    pass
            else:
                try:
                    pages.append(int(part))
                except ValueError:
                    pass
        return [p - 1 for p in pages] if pages else None

    def _pdf_to_png(
        self,
        input_path: Path,
        output_path: Path,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> None:
        import fitz

        dpi = self.options.get("dpi", 150)
        zoom = dpi / 72.0

        try:
            doc = fitz.open(str(input_path))
            selected_pages = self._parse_page_range()
            total_pages = len(selected_pages) if selected_pages else len(doc)
            page_indices = selected_pages or range(len(doc))

            if total_pages == 1:
                for page_idx in page_indices:
                    page = doc[page_idx]
                    mat = fitz.Matrix(zoom, zoom)
                    pix = page.get_pixmap(matrix=mat)
                    pix.save(str(output_path))
                    if progress_callback:
                        progress_callback(1.0)
            else:
                base = output_path.stem
                suffix = output_path.suffix
                parent = output_path.parent
                for i, page_idx in enumerate(page_indices):
                    page = doc[page_idx]
                    mat = fitz.Matrix(zoom, zoom)
                    pix = page.get_pixmap(matrix=mat)
                    page_output = parent / f"{base}_page_{i + 1:03d}{suffix}"
                    pix.save(str(page_output))
                    if progress_callback:
                        progress_callback((i + 1) / total_pages)

            doc.close()
        except Exception as e:
            raise ConversionError(f"Erro ao converter PDF para PNG: {e}")

    def _pdf_to_docx(
        self,
        input_path: Path,
        output_path: Path,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> None:
        if not self._has_pdf2docx:
            raise ConversionError(
                "pdf2docx não está instalado. Instale com: pip install pdf2docx"
            )

        try:
            from pdf2docx import Converter
            if progress_callback:
                progress_callback(0.1)
            cv = Converter(str(input_path))
            cv.convert(str(output_path), start=0, end=None)
            cv.close()
            if progress_callback:
                progress_callback(1.0)
        except Exception as e:
            raise ConversionError(f"Erro ao converter PDF para DOCX: {e}")

    def _pdf_to_txt(
        self,
        input_path: Path,
        output_path: Path,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> None:
        import fitz

        try:
            doc = fitz.open(str(input_path))
            selected_pages = self._parse_page_range()
            pages = selected_pages or range(len(doc))
            total = len(pages) if selected_pages else len(doc)

            text_parts = []
            for i, page_idx in enumerate(pages):
                page = doc[page_idx]
                text_parts.append(page.get_text())
                if progress_callback:
                    progress_callback((i + 1) / total)

            doc.close()

            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n\n".join(text_parts))

        except Exception as e:
            raise ConversionError(f"Erro ao converter PDF para TXT: {e}")

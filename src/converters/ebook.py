# Histórico de Alterações:
#   Data       | Desenvolvedor  | Ticket | Observação
#   -----------|----------------|--------|-------------------
#   2026-05-13 | AFSIS Dev      | #001   | Implementação v1.1.0


import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Callable, Optional

from src.converters.base import BaseConverter, ConversionError
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _find_calibre() -> Optional[str]:
    for name in ["ebook-convert"]:
        path = shutil.which(name)
        if path:
            return path
    return None


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


class EbookConverter(BaseConverter):

    def supported_input_formats(self) -> list[str]:
        return [".epub", ".mobi", ".azw3", ".fb2", ".lrf", ".rb", ".tcr", ".snb", ".pdb"]

    def supported_output_formats(self) -> list[str]:
        outputs = [".epub", ".pdf", ".txt", ".mobi"]
        return outputs

    def category(self) -> str:
        return "Ebook"

    def get_options_schema(self) -> dict:
        return {
            "encoding": {"type": "str", "default": "utf-8", "label": "Encoding"},
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
            import shutil as sh
            sh.copy2(input_path, output_path)
            if progress_callback:
                progress_callback(1.0)
            return

        if ext_out == ".txt":
            self._to_txt(input_path, output_path, progress_callback)
            return

        calibre = _find_calibre()
        if calibre:
            self._convert_via_calibre(input_path, output_path, ext_out, progress_callback)
            return

        lo = _find_libreoffice()
        if lo and ext_out == ".pdf":
            self._convert_via_libreoffice(input_path, output_path, progress_callback)
            return

        if ext_in == ".epub" and ext_out in (".pdf", ".mobi"):
            import zipfile
            self._epub_fallback(input_path, output_path, ext_out, progress_callback)
            return

        raise ConversionError(
            "Instale Calibre (ebook-convert) ou LibreOffice para conversoes de ebook.\n"
            "  Ubuntu: sudo apt install calibre\n"
            "  macOS: brew install calibre"
        )

    def _to_txt(
        self,
        input_path: Path,
        output_path: Path,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> None:
        ext_in = input_path.suffix.lower()

        if ext_in == ".epub":
            self._epub_to_txt(input_path, output_path, progress_callback)
            return

        calibre = _find_calibre()
        if calibre:
            self._convert_via_calibre(input_path, output_path, ".txt", progress_callback)
            return

        lo = _find_libreoffice()
        if lo:
            with tempfile.TemporaryDirectory() as tmpdir:
                tmpdir_p = Path(tmpdir)
                from src.converters.document import _libreoffice_convert
                result = _libreoffice_convert(input_path, tmpdir_p, "txt")
                import shutil as sh
                sh.move(str(result), str(output_path))
            if progress_callback:
                progress_callback(1.0)
            return

        raise ConversionError("Nao foi possivel converter para TXT. Instale Calibre ou LibreOffice.")

    def _epub_to_txt(
        self,
        input_path: Path,
        output_path: Path,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> None:
        import zipfile
        from html.parser import HTMLParser

        class TextExtractor(HTMLParser):
            def __init__(self):
                super().__init__()
                self.text: list[str] = []

            def handle_data(self, data):
                t = data.strip()
                if t:
                    self.text.append(t)

        try:
            if progress_callback:
                progress_callback(0.2)

            text_parts = []
            with zipfile.ZipFile(input_path, "r") as z:
                html_files = [f for f in z.namelist() if f.endswith((".html", ".xhtml", ".htm"))]
                html_files.sort()

                for html_file in html_files:
                    try:
                        content = z.read(html_file).decode("utf-8", errors="ignore")
                        extractor = TextExtractor()
                        extractor.feed(content)
                        text_parts.extend(extractor.text)
                    except Exception:
                        continue

            encoding = self.options.get("encoding", "utf-8")
            with open(output_path, "w", encoding=encoding) as f:
                f.write("\n".join(text_parts))

            if progress_callback:
                progress_callback(1.0)
        except Exception as e:
            raise ConversionError(f"Erro ao extrair texto do EPUB: {e}")

    def _convert_via_calibre(
        self,
        input_path: Path,
        output_path: Path,
        ext_out: str,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> None:
        calibre = _find_calibre()
        if not calibre:
            raise ConversionError("Calibre (ebook-convert) nao encontrado")

        if progress_callback:
            progress_callback(0.2)

        format_map = {
            ".epub": "epub", ".mobi": "mobi", ".pdf": "pdf",
            ".txt": "txt", ".azw3": "azw3", ".fb2": "fb2",
        }
        out_fmt = format_map.get(ext_out, ext_out.lstrip("."))

        cmd = [calibre, str(input_path), str(output_path), "--output-format", out_fmt]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                raise ConversionError(f"Calibre falhou: {result.stderr.strip()}")
            if not output_path.exists():
                raise ConversionError("Arquivo de saida do Calibre nao encontrado")
            if progress_callback:
                progress_callback(1.0)
        except subprocess.TimeoutExpired:
            raise ConversionError("Conversao via Calibre excedeu o tempo limite")
        except ConversionError:
            raise
        except Exception as e:
            raise ConversionError(f"Erro na conversao via Calibre: {e}")

    def _convert_via_libreoffice(
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
            result = _libreoffice_convert(input_path, tmpdir_p, "pdf")
            import shutil as sh
            sh.move(str(result), str(output_path))
        if progress_callback:
            progress_callback(1.0)

    def _epub_fallback(
        self,
        input_path: Path,
        output_path: Path,
        ext_out: str,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> None:
        raise ConversionError(
            "Conversao de EPUB requer Calibre ou LibreOffice instalados.\n"
            "Instale um deles para continuar."
        )
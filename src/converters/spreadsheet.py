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
from src.converters.document import _find_libreoffice
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _libreoffice_sheet_convert(input_path: Path, output_dir: Path, target_format: str) -> Path:
    libreoffice = _find_libreoffice()
    if not libreoffice:
        raise ConversionError(
            "LibreOffice não encontrado. Instale o LibreOffice para continuar."
        )

    # Copy file into output_dir first — avoids path/permission issues
    local_copy = output_dir / input_path.name
    if not local_copy.exists():
        shutil.copy2(input_path, local_copy)

    cmd = [
        libreoffice,
        "--headless",
        "--convert-to",
        target_format,
        "--outdir",
        str(output_dir),
        str(local_copy),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip() or "erro desconhecido"
            raise ConversionError(f"LibreOffice falhou: {error_msg}")

        expected_name = local_copy.stem + "." + target_format
        output_path = output_dir / expected_name
        if output_path.exists():
            local_copy.unlink(missing_ok=True)
            return output_path

        for f in output_dir.iterdir():
            if f.stem == local_copy.stem and f.suffix.lower() == f".{target_format}":
                local_copy.unlink(missing_ok=True)
                return f

        raise ConversionError("Arquivo de saída do LibreOffice não encontrado")
    except subprocess.TimeoutExpired:
        raise ConversionError("Conversão via LibreOffice excedeu o tempo limite")


class SpreadsheetConverter(BaseConverter):

    def supported_input_formats(self) -> list[str]:
        return [".xlsx", ".csv", ".ods"]

    def supported_output_formats(self) -> list[str]:
        return [".xlsx", ".csv", ".pdf"]

    def category(self) -> str:
        return "Planilha"

    def get_options_schema(self) -> dict:
        return {
            "csv_separator": {"type": "str", "default": ",", "label": "Separador CSV"},
            "csv_encoding": {"type": "str", "default": "utf-8", "label": "Encoding CSV"},
            "sheet_name": {"type": "str", "default": "", "label": "Nome da aba (XLSX/ODS)"},
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
            raise ConversionError(f"Não é possível converter {ext_in} → {ext_out}")

        if ext_out == ".pdf":
            self._to_pdf(input_path, output_path, progress_callback)
        elif ext_out == ".csv":
            self._to_csv(input_path, output_path, progress_callback)
        elif ext_out == ".xlsx":
            self._to_xlsx(input_path, output_path, progress_callback)
        else:
            raise ConversionError(f"Formato de saída não suportado: {ext_out}")

    def _to_csv(
        self,
        input_path: Path,
        output_path: Path,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> None:
        import pandas as pd

        sep = self.options.get("csv_separator", ",")
        encoding = self.options.get("csv_encoding", "utf-8")
        sheet = self.options.get("sheet_name", "").strip() or 0

        try:
            if progress_callback:
                progress_callback(0.3)

            ext_in = input_path.suffix.lower()
            if ext_in == ".csv":
                df = pd.read_csv(input_path, sep=None, engine="python", encoding=encoding)
            else:
                read_kwargs = {"sheet_name": sheet}
                df = pd.read_excel(input_path, **read_kwargs)

            if progress_callback:
                progress_callback(0.7)

            df.to_csv(output_path, sep=sep, index=False, encoding=encoding)

            if progress_callback:
                progress_callback(1.0)
        except Exception as e:
            raise ConversionError(f"Erro ao converter para CSV: {e}")

    def _to_xlsx(
        self,
        input_path: Path,
        output_path: Path,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> None:
        import pandas as pd

        sep = self.options.get("csv_separator", ",")
        encoding = self.options.get("csv_encoding", "utf-8")

        try:
            if progress_callback:
                progress_callback(0.3)

            ext_in = input_path.suffix.lower()
            if ext_in == ".csv":
                df = pd.read_csv(input_path, sep=sep, encoding=encoding)
            elif ext_in == ".ods":
                df = pd.read_excel(input_path, engine="odf")
            else:
                # XLSX → XLSX: copy
                shutil.copy2(input_path, output_path)
                if progress_callback:
                    progress_callback(1.0)
                return

            if progress_callback:
                progress_callback(0.7)

            df.to_excel(output_path, index=False, engine="openpyxl")

            if progress_callback:
                progress_callback(1.0)
        except Exception as e:
            raise ConversionError(f"Erro ao converter para XLSX: {e}")

    def _to_pdf(
        self,
        input_path: Path,
        output_path: Path,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> None:
        if progress_callback:
            progress_callback(0.2)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_p = Path(tmpdir)
            result = _libreoffice_sheet_convert(input_path, tmpdir_p, "pdf")
            if progress_callback:
                progress_callback(0.8)

            if result.suffix.lower() != ".pdf":
                final = result.rename(output_path)
            else:
                shutil.move(str(result), str(output_path))

            if progress_callback:
                progress_callback(1.0)

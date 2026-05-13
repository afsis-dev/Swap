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


class VectorConverter(BaseConverter):

    def __init__(self, options: Optional[dict] = None):
        super().__init__(options)
        self._has_cairosvg = False
        try:
            import cairosvg
            self._has_cairosvg = True
        except ImportError:
            pass

    def supported_input_formats(self) -> list[str]:
        fmts = [".svg"]
        if self._has_cairosvg:
            pass
        return fmts

    def supported_output_formats(self) -> list[str]:
        outputs = [".png", ".pdf"]
        if self._has_cairosvg:
            outputs.extend([".jpg", ".jpeg", ".webp"])
        return outputs

    def category(self) -> str:
        return "Vetor"

    def get_options_schema(self) -> dict:
        return {
            "dpi": {"type": "int", "min": 72, "max": 600, "default": 150, "label": "DPI"},
            "scale": {"type": "int", "min": 1, "max": 10, "default": 1, "label": "Escala"},
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

        if not self._has_cairosvg:
            raise ConversionError(
                "cairosvg nao esta instalado. Instale com:\n"
                "  pip install cairosvg\n"
                "  Ubuntu: sudo apt install libcairo2-dev\n"
                "  macOS: brew install cairo"
            )

        if ext_in == ".svg":
            self._convert_svg(input_path, output_path, ext_out, progress_callback)
        else:
            raise ConversionError(f"Formato de vetor nao suportado: {ext_in}")

    def _convert_svg(
        self,
        input_path: Path,
        output_path: Path,
        target_ext: str,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> None:
        import cairosvg

        dpi = self.options.get("dpi", 150)
        scale = self.options.get("scale", 1)

        if progress_callback:
            progress_callback(0.3)

        try:
            if target_ext == ".png":
                cairosvg.svg2png(
                    url=str(input_path),
                    write_to=str(output_path),
                    dpi=dpi * scale,
                )
            elif target_ext == ".pdf":
                cairosvg.svg2pdf(
                    url=str(input_path),
                    write_to=str(output_path),
                    dpi=dpi * scale,
                )
            elif target_ext in (".jpg", ".jpeg"):
                temp_png = output_path.with_suffix(".png")
                cairosvg.svg2png(
                    url=str(input_path),
                    write_to=str(temp_png),
                    dpi=dpi * scale,
                )
                from PIL import Image
                img = Image.open(temp_png)
                if img.mode in ("RGBA", "P", "LA"):
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                    img = background
                else:
                    img = img.convert("RGB")
                quality = self.options.get("quality", 85)
                img.save(str(output_path), "JPEG", quality=quality)
                if temp_png.exists():
                    temp_png.unlink()
            elif target_ext == ".webp":
                from PIL import Image
                temp_png = output_path.with_suffix(".png")
                cairosvg.svg2png(
                    url=str(input_path),
                    write_to=str(temp_png),
                    dpi=dpi * scale,
                )
                img = Image.open(temp_png)
                img.save(str(output_path), "WEBP", quality=self.options.get("quality", 85))
                if temp_png.exists():
                    temp_png.unlink()
            else:
                raise ConversionError(f"Conversao SVG -> {target_ext} nao suportada")

            if progress_callback:
                progress_callback(1.0)

        except ConversionError:
            raise
        except Exception as e:
            raise ConversionError(f"Erro ao converter SVG: {e}")
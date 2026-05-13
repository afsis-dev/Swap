# Histórico de Alterações:
#   Data       | Desenvolvedor  | Ticket | Observação
#   -----------|----------------|--------|-------------------
#   2026-05-13 | AFSIS Dev      | #001   | Implementação v1.1.0


from pathlib import Path
from typing import Callable, Optional

from PIL import Image

from src.converters.base import BaseConverter, ConversionError
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ImageConverter(BaseConverter):

    def __init__(self, options: Optional[dict] = None):
        super().__init__(options)
        # Try to import cairosvg for SVG support
        self._has_cairosvg = False
        try:
            import cairosvg
            self._has_cairosvg = True
        except ImportError:
            pass

    def supported_input_formats(self) -> list[str]:
        fmts = [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".tif", ".webp", ".ico", ".ppm"]
        if self._has_cairosvg:
            fmts.append(".svg")
        return fmts

    def supported_output_formats(self) -> list[str]:
        return [".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif", ".ico", ".pdf"]

    def category(self) -> str:
        return "Imagem"

    def get_options_schema(self) -> dict:
        return {
            "quality": {"type": "int", "min": 1, "max": 95, "default": 85, "label": "Qualidade JPEG"},
            "dpi": {"type": "int", "min": 72, "max": 600, "default": 150, "label": "DPI"},
            "resize_width": {"type": "int", "min": 0, "max": 10000, "default": 0, "label": "Largura (0 = original)"},
            "resize_height": {"type": "int", "min": 0, "max": 10000, "default": 0, "label": "Altura (0 = original)"},
            "ico_sizes": {"type": "str", "default": "16,32,48,64,128,256", "label": "Tamanhos ICO"},
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
            raise ConversionError(
                f"Não é possível converter {ext_in} → {ext_out}"
            )

        if ext_in == ".svg" and self._has_cairosvg:
            self._convert_svg(input_path, output_path, ext_out, progress_callback)
        else:
            self._convert_raster(input_path, output_path, ext_out, progress_callback)

    def _convert_svg(
        self,
        input_path: Path,
        output_path: Path,
        target_ext: str,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> None:
        import cairosvg
        dpi = self.options.get("dpi", 150)

        if target_ext in (".png", ".pdf"):
            if progress_callback:
                progress_callback(0.5)
            try:
                if target_ext == ".pdf":
                    cairosvg.svg2pdf(
                        url=str(input_path),
                        write_to=str(output_path),
                        dpi=dpi,
                    )
                else:
                    cairosvg.svg2png(
                        url=str(input_path),
                        write_to=str(output_path),
                        dpi=dpi,
                    )
                if progress_callback:
                    progress_callback(1.0)
            except Exception as e:
                raise ConversionError(f"Erro ao converter SVG: {e}")
        else:
            # SVG → PNG first, then convert to target
            temp_png = output_path.with_suffix(".png")
            try:
                cairosvg.svg2png(
                    url=str(input_path),
                    write_to=str(temp_png),
                    dpi=dpi,
                )
                if progress_callback:
                    progress_callback(0.5)
                self._convert_raster(temp_png, output_path, target_ext, progress_callback)
            finally:
                if temp_png.exists() and temp_png != output_path:
                    temp_png.unlink()

    def _convert_raster(
        self,
        input_path: Path,
        output_path: Path,
        target_ext: str,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> None:
        quality = self.options.get("quality", 85)
        dpi_val = self.options.get("dpi", 150)

        try:
            with Image.open(input_path) as img:
                # Preserve EXIF orientation
                exif = img.info.get("exif")
                icc_profile = img.info.get("icc_profile")

                # Handle resize
                resize_w = self.options.get("resize_width", 0)
                resize_h = self.options.get("resize_height", 0)
                if resize_w > 0 and resize_h > 0:
                    img = img.resize((resize_w, resize_h), Image.LANCZOS)
                elif resize_w > 0:
                    ratio = resize_w / img.width
                    new_h = int(img.height * ratio)
                    img = img.resize((resize_w, new_h), Image.LANCZOS)
                elif resize_h > 0:
                    ratio = resize_h / img.height
                    new_w = int(img.width * ratio)
                    img = img.resize((new_w, resize_h), Image.LANCZOS)

                if progress_callback:
                    progress_callback(0.5)

                img, save_kwargs = self._build_save_kwargs(
                    target_ext, img, quality, dpi_val, exif, icc_profile
                )

                if target_ext == ".ico":
                    self._save_ico(img, output_path)
                else:
                    img.save(str(output_path), **save_kwargs)

                if progress_callback:
                    progress_callback(1.0)

        except Exception as e:
            raise ConversionError(f"Erro ao converter imagem: {e}")

    def _build_save_kwargs(self, target_ext: str, img, quality, dpi_val, exif, icc):
        kwargs = {}

        if target_ext in (".jpg", ".jpeg"):
            if img.mode in ("RGBA", "P", "LA"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                img = background

            kwargs["quality"] = quality
            kwargs["optimize"] = True
            if exif:
                kwargs["exif"] = exif
        elif target_ext == ".png":
            kwargs["optimize"] = True
        elif target_ext == ".webp":
            kwargs["quality"] = quality
        elif target_ext == ".tiff" or target_ext == ".tif":
            kwargs["compression"] = "tiff_lzw"

        if dpi_val and target_ext not in (".ico",):
            kwargs["dpi"] = (dpi_val, dpi_val)

        if icc and target_ext in (".jpg", ".jpeg", ".png"):
            kwargs["icc_profile"] = icc

        return img, kwargs

    def _save_ico(self, img, output_path: Path) -> None:
        sizes_str = self.options.get("ico_sizes", "16,32,48,64,128,256")
        sizes = [int(s.strip()) for s in sizes_str.split(",") if s.strip().isdigit()]
        if not sizes:
            sizes = [16, 32, 48, 64, 128, 256]

        if img.mode != "RGBA":
            img = img.convert("RGBA")

        img.save(str(output_path), format="ICO", sizes=[(s, s) for s in sizes])

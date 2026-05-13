# Histórico de Alterações:
#   Data       | Desenvolvedor  | Ticket | Observação
#   -----------|----------------|--------|-------------------
#   2026-05-13 | AFSIS Dev      | #001   | Implementação v1.1.0


import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Callable, Optional

from PIL import Image

from src.converters.base import BaseConverter, ConversionError
from src.utils.logger import get_logger

logger = get_logger(__name__)

SUPPORTED_IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.tif'}


def _find_executable(*names: str) -> Optional[str]:
    for name in names:
        path = shutil.which(name)
        if path:
            return path
    return None


def _extract_cbz(archive_path: Path, dest_dir: Path) -> list[Path]:
    images = []
    with zipfile.ZipFile(archive_path, 'r') as zf:
        for name in sorted(zf.namelist()):
            ext = Path(name).suffix.lower()
            if ext in SUPPORTED_IMAGE_EXTS:
                target = dest_dir / Path(name).name
                with zf.open(name) as src, open(target, 'wb') as dst:
                    dst.write(src.read())
                images.append(target)
    return images


def _extract_rar(archive_path: Path, dest_dir: Path) -> list[Path]:
    unrar = _find_executable('unrar', 'rar')
    if not unrar:
        raise ConversionError(
            "Para converter CBR é necessário instalar o 'unrar' (sudo apt install unrar)"
        )
    subprocess.run(
        [unrar, 'x', '-o+', str(archive_path), str(dest_dir) + '/'],
        check=True, capture_output=True, timeout=120,
    )
    images = sorted(
        [f for f in dest_dir.iterdir() if f.suffix.lower() in SUPPORTED_IMAGE_EXTS],
        key=lambda f: f.name.lower(),
    )
    return images


def _extract_7z(archive_path: Path, dest_dir: Path) -> list[Path]:
    seven_zip = _find_executable('7z', '7za', '7zz')
    if not seven_zip:
        raise ConversionError(
            "Para converter CB7/7Z é necessário instalar o 'p7zip-full' (sudo apt install p7zip-full)"
        )
    subprocess.run(
        [seven_zip, 'x', f'-o{str(dest_dir)}', '-y', str(archive_path)],
        check=True, capture_output=True, timeout=120,
    )
    images = sorted(
        [f for f in dest_dir.iterdir() if f.suffix.lower() in SUPPORTED_IMAGE_EXTS],
        key=lambda f: f.name.lower(),
    )
    return images


def _extract_images(archive_path: Path, dest_dir: Path) -> list[Path]:
    ext = archive_path.suffix.lower()
    if ext in ('.cbz', '.zip'):
        return _extract_cbz(archive_path, dest_dir)
    elif ext in ('.cbr', '.rar'):
        return _extract_rar(archive_path, dest_dir)
    elif ext in ('.cb7', '.7z'):
        return _extract_7z(archive_path, dest_dir)
    else:
        raise ConversionError(f"Formato de arquivo não suportado: {ext}")


def _images_to_pdf(images: list[Path], output_path: Path, progress_callback=None):
    if not images:
        raise ConversionError("Nenhuma imagem encontrada no arquivo")

    rgb_images = []
    for img_path in images:
        img = Image.open(img_path)
        if img.mode not in ('RGB', 'RGBA'):
            img = img.convert('RGB')
        rgb_images.append(img)

    first = rgb_images[0]
    rest = rgb_images[1:] if len(rgb_images) > 1 else []
    first.save(
        output_path,
        save_all=True,
        append_images=rest,
    )

    if progress_callback:
        progress_callback(1.0)


def _images_to_cbz(images: list[Path], output_path: Path, progress_callback=None):
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for i, img_path in enumerate(images):
            zf.write(img_path, img_path.name)
            if progress_callback:
                progress_callback((i + 1) / len(images))


class ComicConverter(BaseConverter):

    def supported_input_formats(self) -> list[str]:
        fmts = ['.cbz', '.zip']
        if _find_executable('unrar', 'rar'):
            fmts.append('.cbr')
            fmts.append('.rar')
        if _find_executable('7z', '7za', '7zz'):
            fmts.append('.cb7')
            fmts.append('.7z')
        return fmts

    def supported_output_formats(self) -> list[str]:
        return ['.pdf', '.cbz']

    def category(self) -> str:
        return "Quadrinhos"

    def get_options_schema(self) -> dict:
        return {
            "resize_width": {
                "type": "int", "min": 0, "max": 10000, "default": 0,
                "label": "Largura (0 = original)",
            },
            "resize_height": {
                "type": "int", "min": 0, "max": 10000, "default": 0,
                "label": "Altura (0 = original)",
            },
            "quality": {
                "type": "int", "min": 1, "max": 95, "default": 85,
                "label": "Qualidade JPEG",
            },
            "grayscale": {
                "type": "bool", "default": False,
                "label": "Converter para preto e branco",
            },
        }

    def convert(
        self,
        input_path: Path,
        output_path: Path,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> None:
        output_ext = output_path.suffix.lower()

        with tempfile.TemporaryDirectory(prefix='swap_comic_') as tmp:
            tmp_dir = Path(tmp)
            images = _extract_images(input_path, tmp_dir)

            if not images:
                raise ConversionError("Nenhuma imagem encontrada no arquivo")

            resize_w = int(self.options.get('resize_width', 0))
            resize_h = int(self.options.get('resize_height', 0))
            do_grayscale = self.options.get('grayscale', False)

            if resize_w > 0 or resize_h > 0 or do_grayscale:
                for i, img_path in enumerate(images):
                    img = Image.open(img_path)

                    if do_grayscale:
                        img = img.convert('L')

                    if resize_w > 0 or resize_h > 0:
                        orig_w, orig_h = img.size
                        new_w = resize_w if resize_w > 0 else orig_w
                        new_h = resize_h if resize_h > 0 else orig_h
                        if resize_w > 0 and resize_h == 0:
                            new_h = int(orig_h * (new_w / orig_w))
                        elif resize_h > 0 and resize_w == 0:
                            new_w = int(orig_w * (new_h / orig_h))
                        img = img.resize((new_w, new_h), Image.LANCZOS)

                    img.save(str(img_path))
                    if progress_callback:
                        progress_callback(0.1 + 0.4 * (i + 1) / len(images))

            if output_ext == '.pdf':
                _images_to_pdf(images, output_path, progress_callback)
            elif output_ext == '.cbz':
                _images_to_cbz(images, output_path, progress_callback)
            else:
                raise ConversionError(f"Formato de saída não suportado: {output_ext}")

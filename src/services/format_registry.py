# Histórico de Alterações:
#   Data       | Desenvolvedor  | Ticket | Observação
#   -----------|----------------|--------|-------------------
#   2026-05-13 | AFSIS Dev      | #001   | Implementação v1.1.0


from pathlib import Path
from typing import Optional

from src.converters.base import BaseConverter, UnsupportedFormatError
from src.converters.image import ImageConverter
from src.converters.pdf import PDFConverter
from src.converters.document import DocumentConverter
from src.converters.spreadsheet import SpreadsheetConverter
from src.converters.ebook import EbookConverter
from src.converters.presentation import PresentationConverter
from src.converters.vector import VectorConverter
from src.converters.comic import ComicConverter
from src.utils.logger import get_logger

logger = get_logger(__name__)

_registry: dict[str, BaseConverter] = {}

_CONVERTER_CLASSES = [
    ImageConverter,
    PDFConverter,
    DocumentConverter,
    SpreadsheetConverter,
    EbookConverter,
    PresentationConverter,
    VectorConverter,
    ComicConverter,
]


def _converter_for_extension(ext: str) -> Optional[BaseConverter]:
    ext = ext.lower()
    if not ext.startswith("."):
        ext = f".{ext}"

    if ext in _registry:
        return _registry[ext]

    for cls in _CONVERTER_CLASSES:
        try:
            converter = cls()
            if ext in converter.supported_input_formats():
                _registry[ext] = converter
                return converter
        except Exception as e:
            logger.debug(f"Skipping converter {cls.__name__}: {e}")

    return None


def get_converter(input_path: Path) -> BaseConverter:
    ext = input_path.suffix.lower()
    converter = _converter_for_extension(ext)
    if converter is None:
        raise UnsupportedFormatError(f"Formato nao suportado: {ext}")
    return converter


def get_supported_input_formats() -> list[str]:
    result = []
    for cls in _CONVERTER_CLASSES:
        try:
            result.extend(cls().supported_input_formats())
        except Exception:
            pass
    return result


def get_output_formats_for(input_ext: str) -> list[str]:
    converter = _converter_for_extension(input_ext)
    if converter:
        return converter.supported_output_formats()
    return []


def can_convert(input_ext: str, output_ext: str) -> bool:
    converter = _converter_for_extension(input_ext)
    if not converter:
        return False
    return converter.can_convert(input_ext, output_ext)


def clear_cache() -> None:
    _registry.clear()
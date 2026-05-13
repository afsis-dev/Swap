# Histórico de Alterações:
#   Data       | Desenvolvedor  | Ticket | Observação
#   -----------|----------------|--------|-------------------
#   2026-05-13 | AFSIS Dev      | #001   | Implementação v1.1.0


import pytest
import tempfile
from pathlib import Path
from src.services.format_registry import (
    get_converter,
    get_supported_input_formats,
    get_output_formats_for,
    can_convert,
    UnsupportedFormatError,
    clear_cache,
)


class TestFormatRegistry:

    def setup_method(self):
        clear_cache()

    def test_get_converter_image(self, tmp_path):
        jpg = tmp_path / "test.jpg"
        jpg.touch()
        converter = get_converter(jpg)
        assert converter.category() == "Imagem"

    def test_get_converter_pdf(self, tmp_path):
        pdf = tmp_path / "test.pdf"
        pdf.touch()
        converter = get_converter(pdf)
        assert converter.category() == "PDF"

    def test_get_converter_document(self, tmp_path):
        docx = tmp_path / "test.docx"
        docx.touch()
        converter = get_converter(docx)
        assert converter.category() == "Documento"

    def test_get_converter_spreadsheet(self, tmp_path):
        xlsx = tmp_path / "test.xlsx"
        xlsx.touch()
        converter = get_converter(xlsx)
        assert converter.category() == "Planilha"

    def test_unknown_format(self, tmp_path):
        unknown = tmp_path / "test.xyz"
        unknown.touch()
        with pytest.raises(UnsupportedFormatError):
            get_converter(unknown)

    def test_supported_input_formats(self):
        fmts = get_supported_input_formats()
        assert ".jpg" in fmts
        assert ".png" in fmts
        assert ".pdf" in fmts
        assert ".docx" in fmts
        assert ".xlsx" in fmts

    def test_output_formats_for_image(self):
        fmts = get_output_formats_for(".jpg")
        assert ".png" in fmts
        assert ".webp" in fmts

    def test_output_formats_for_pdf(self):
        fmts = get_output_formats_for(".pdf")
        assert ".png" in fmts
        assert ".docx" in fmts
        assert ".txt" in fmts

    def test_can_convert(self):
        assert can_convert(".jpg", ".png") is True
        assert can_convert(".pdf", ".png") is True
        assert can_convert(".xyz", ".png") is False

    def test_clear_cache(self):
        clear_cache()
        assert len(getattr(__import__("src.services.format_registry", fromlist=["_registry"]), "_registry")) == 0

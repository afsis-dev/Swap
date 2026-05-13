# Histórico de Alterações:
#   Data       | Desenvolvedor  | Ticket | Observação
#   -----------|----------------|--------|-------------------
#   2026-05-13 | AFSIS Dev      | #001   | Implementação v1.1.0


import pytest
import tempfile
from pathlib import Path
from src.converters.base import (
    BaseConverter,
    ConversionError,
    UnsupportedFormatError,
    ConversionResult,
    FormatInfo,
)


class ConcreteConverter(BaseConverter):

    def convert(self, input_path, output_path, progress_callback=None):
        output_path.write_text("converted")

    def supported_input_formats(self):
        return [".txt", ".log"]

    def supported_output_formats(self):
        return [".txt", ".md"]

    def category(self):
        return "Test"


class TestBaseConverter:

    def test_can_convert_true(self):
        converter = ConcreteConverter()
        assert converter.can_convert(".txt", ".md") is True

    def test_can_convert_false_input(self):
        converter = ConcreteConverter()
        assert converter.can_convert(".pdf", ".md") is False

    def test_can_convert_false_output(self):
        converter = ConcreteConverter()
        assert converter.can_convert(".txt", ".pdf") is False

    def test_options_default(self):
        converter = ConcreteConverter()
        assert converter.options == {}

    def test_options_custom(self):
        converter = ConcreteConverter(options={"key": "value"})
        assert converter.options == {"key": "value"}

    def test_get_options_schema_default(self):
        converter = ConcreteConverter()
        assert converter.get_options_schema() == {}

    def test_conversion_result_success(self, tmp_path):
        result = ConversionResult(
            success=True,
            input_path=tmp_path / "in.txt",
            output_path=tmp_path / "out.md",
            duration_ms=100.0,
            input_size=500,
            output_size=300,
        )
        assert result.success is True
        assert result.error is None

    def test_conversion_result_error(self, tmp_path):
        result = ConversionResult(
            success=False,
            input_path=tmp_path / "in.txt",
            error="Something went wrong",
            duration_ms=50.0,
        )
        assert result.success is False
        assert result.error == "Something went wrong"
        assert result.output_path is None

    def test_conversion_error(self):
        err = ConversionError("test error")
        assert str(err) == "test error"

    def test_unsupported_format_error(self):
        err = UnsupportedFormatError(".xyz")
        assert str(err) == ".xyz"
        assert isinstance(err, ConversionError)

    def test_format_info(self):
        info = FormatInfo(extension=".jpg", description="JPEG Image", category="Imagem")
        assert info.extension == ".jpg"
        assert info.description == "JPEG Image"
        assert info.category == "Imagem"

# Histórico de Alterações:
#   Data       | Desenvolvedor  | Ticket | Observação
#   -----------|----------------|--------|-------------------
#   2026-05-13 | AFSIS Dev      | #001   | Implementação v1.1.0


import pytest
import tempfile
from pathlib import Path
from src.converters.document import DocumentConverter, _find_libreoffice
from src.converters.base import ConversionError


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


class TestDocumentConverterEdgeCases:

    def test_html_to_txt(self, tmp_dir):
        html_path = tmp_dir / "test.html"
        html_path.write_text("<html><body><p>Hello</p><p>World</p></body></html>", encoding="utf-8")

        converter = DocumentConverter()
        output = tmp_dir / "output.txt"
        converter.convert(html_path, output)
        assert output.exists()
        content = output.read_text()
        assert "Hello" in content
        assert "World" in content

    def test_htm_to_txt(self, tmp_dir):
        html_path = tmp_dir / "test.htm"
        html_path.write_text("<p>Test content</p>", encoding="utf-8")

        converter = DocumentConverter()
        output = tmp_dir / "output.txt"
        converter.convert(html_path, output)
        assert output.exists()

    def test_html_to_txt_empty(self, tmp_dir):
        html_path = tmp_dir / "empty.html"
        html_path.write_text("<html><body></body></html>", encoding="utf-8")

        converter = DocumentConverter()
        output = tmp_dir / "output.txt"
        converter.convert(html_path, output)
        assert output.exists()

    def test_txt_to_txt_copy(self, tmp_dir):
        txt_path = tmp_dir / "input.txt"
        txt_path.write_text("Some text content", encoding="utf-8")

        converter = DocumentConverter()
        output = tmp_dir / "output.txt"
        converter.convert(txt_path, output)
        assert output.exists()
        assert output.read_text() == "Some text content"

    def test_libreoffice_detection(self):
        result = _find_libreoffice()
        if result is not None:
            assert Path(result).exists()

    def test_unsupported_conversion(self, tmp_dir):
        txt_path = tmp_dir / "input.txt"
        txt_path.write_text("test", encoding="utf-8")

        converter = DocumentConverter()
        output = tmp_dir / "output.xlsx"
        with pytest.raises(ConversionError):
            converter.convert(txt_path, output)

    def test_options_schema(self):
        converter = DocumentConverter()
        schema = converter.get_options_schema()
        assert "encoding" in schema

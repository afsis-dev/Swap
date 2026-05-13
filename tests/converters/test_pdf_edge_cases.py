# Histórico de Alterações:
#   Data       | Desenvolvedor  | Ticket | Observação
#   -----------|----------------|--------|-------------------
#   2026-05-13 | AFSIS Dev      | #001   | Implementação v1.1.0


import pytest
import tempfile
from pathlib import Path
from src.converters.pdf import PDFConverter
from src.converters.base import ConversionError


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def sample_pdf(tmp_dir):
    try:
        import fitz
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Hello PDF", fontsize=12)
        path = tmp_dir / "test.pdf"
        doc.save(str(path))
        doc.close()
        return path
    except ImportError:
        pytest.skip("PyMuPDF not installed")


class TestPDFConverterEdgeCases:

    def test_options_schema(self):
        converter = PDFConverter()
        schema = converter.get_options_schema()
        assert "dpi" in schema
        assert "page_range" in schema

    def test_progress_callback(self, sample_pdf, tmp_dir):
        calls = []
        converter = PDFConverter()
        output = tmp_dir / "output.png"
        converter.convert(sample_pdf, output, progress_callback=lambda p: calls.append(p))
        assert len(calls) >= 1

    def test_empty_page_range(self):
        converter = PDFConverter(options={"page_range": ""})
        result = converter._parse_page_range()
        assert result is None

    def test_invalid_page_range(self):
        converter = PDFConverter(options={"page_range": "abc"})
        result = converter._parse_page_range()
        assert result is None

    def test_page_range_single(self):
        converter = PDFConverter(options={"page_range": "3"})
        result = converter._parse_page_range()
        assert result == [2]

    def test_page_range_mixed(self):
        converter = PDFConverter(options={"page_range": "1,3-5,8"})
        result = converter._parse_page_range()
        assert result == [0, 2, 3, 4, 7]

    def test_unsupported_output_format(self, sample_pdf, tmp_dir):
        converter = PDFConverter()
        output = tmp_dir / "output.xyz"
        with pytest.raises(ConversionError):
            converter.convert(sample_pdf, output)

    def test_pdf_to_txt_content(self, sample_pdf, tmp_dir):
        converter = PDFConverter()
        output = tmp_dir / "output.txt"
        converter.convert(sample_pdf, output)
        content = output.read_text()
        assert "Hello PDF" in content

    def test_can_convert(self):
        converter = PDFConverter()
        assert converter.can_convert(".pdf", ".png") is True
        assert converter.can_convert(".pdf", ".docx") is True
        assert converter.can_convert(".pdf", ".txt") is True
        assert converter.can_convert(".jpg", ".png") is False

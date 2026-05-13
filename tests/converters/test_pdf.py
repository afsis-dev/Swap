# Histórico de Alterações:
#   Data       | Desenvolvedor  | Ticket | Observação
#   -----------|----------------|--------|-------------------
#   2026-05-13 | AFSIS Dev      | #001   | Implementação v1.1.0


import pytest
import tempfile
from pathlib import Path
from src.converters.base import ConversionError
from src.converters.pdf import PDFConverter


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
        page.insert_text((72, 72), "Test PDF content", fontsize=12)
        path = tmp_dir / "test.pdf"
        doc.save(str(path))
        doc.close()
        return path
    except ImportError:
        pytest.skip("PyMuPDF not installed")


class TestPDFConverter:

    def test_pdf_to_png(self, sample_pdf, tmp_dir):
        converter = PDFConverter()
        output = tmp_dir / "output.png"
        converter.convert(sample_pdf, output)
        assert output.exists()

    def test_pdf_to_png_multipage(self, tmp_dir):
        try:
            import fitz
        except ImportError:
            pytest.skip("PyMuPDF not installed")

        doc = fitz.open()
        for i in range(3):
            page = doc.new_page()
            page.insert_text((72, 72), f"Page {i + 1}", fontsize=12)
        pdf_path = tmp_dir / "multipage.pdf"
        doc.save(str(pdf_path))
        doc.close()

        converter = PDFConverter()
        output = tmp_dir / "output.png"
        converter.convert(pdf_path, output)

        output_files = list(tmp_dir.glob("output_page_*.png"))
        assert len(output_files) == 3

    def test_pdf_to_txt(self, sample_pdf, tmp_dir):
        converter = PDFConverter()
        output = tmp_dir / "output.txt"
        converter.convert(sample_pdf, output)
        assert output.exists()
        content = output.read_text()
        assert "Test PDF content" in content

    def test_pdf_to_docx(self, sample_pdf, tmp_dir):
        try:
            import pdf2docx
        except ImportError:
            pytest.skip("pdf2docx not installed")

        converter = PDFConverter()
        output = tmp_dir / "output.docx"
        converter.convert(sample_pdf, output)
        assert output.exists()

    def test_page_range(self, tmp_dir):
        try:
            import fitz
        except ImportError:
            pytest.skip("PyMuPDF not installed")

        doc = fitz.open()
        for i in range(5):
            page = doc.new_page()
            page.insert_text((72, 72), f"Page {i + 1}", fontsize=12)
        pdf_path = tmp_dir / "range.pdf"
        doc.save(str(pdf_path))
        doc.close()

        converter = PDFConverter(options={"page_range": "1,3,5"})
        output = tmp_dir / "output.png"
        converter.convert(pdf_path, output)

        output_files = list(tmp_dir.glob("output_page_*.png"))
        assert len(output_files) == 3

    def test_supported_formats(self):
        converter = PDFConverter()
        assert ".pdf" in converter.supported_input_formats()
        assert ".png" in converter.supported_output_formats()
        assert ".docx" in converter.supported_output_formats()
        assert ".txt" in converter.supported_output_formats()
        assert converter.category() == "PDF"

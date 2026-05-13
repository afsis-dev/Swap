# Histórico de Alterações:
#   Data       | Desenvolvedor  | Ticket | Observação
#   -----------|----------------|--------|-------------------
#   2026-05-13 | AFSIS Dev      | #001   | Implementação v1.1.0


import pytest
import tempfile
from pathlib import Path
from src.converters.spreadsheet import SpreadsheetConverter


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def sample_xlsx(tmp_dir):
    try:
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["Name", "Age", "City"])
        ws.append(["Alice", 30, "São Paulo"])
        ws.append(["Bob", 25, "Rio de Janeiro"])
        path = tmp_dir / "test.xlsx"
        wb.save(str(path))
        return path
    except ImportError:
        pytest.skip("openpyxl not installed")


@pytest.fixture
def sample_csv(tmp_dir):
    csv_path = tmp_dir / "test.csv"
    csv_path.write_text("Name,Age,City\nAlice,30,São Paulo\nBob,25,Rio\n", encoding="utf-8")
    return csv_path


class TestSpreadsheetConverter:

    def test_xlsx_to_csv(self, sample_xlsx, tmp_dir):
        converter = SpreadsheetConverter()
        output = tmp_dir / "output.csv"
        converter.convert(sample_xlsx, output)
        assert output.exists()
        content = output.read_text(encoding="utf-8")
        assert "Name" in content
        assert "Alice" in content

    def test_csv_to_xlsx(self, sample_csv, tmp_dir):
        converter = SpreadsheetConverter()
        output = tmp_dir / "output.xlsx"
        converter.convert(sample_csv, output)
        assert output.exists()

    def test_csv_encoding(self, tmp_dir):
        csv_path = tmp_dir / "latin1.csv"
        csv_path.write_text("Nome,Cidade\nSão Paulo,Rio\n", encoding="utf-8")

        converter = SpreadsheetConverter(options={"csv_encoding": "utf-8"})
        output = tmp_dir / "output.xlsx"
        converter.convert(csv_path, output)
        assert output.exists()

    def test_supported_formats(self):
        converter = SpreadsheetConverter()
        assert ".xlsx" in converter.supported_input_formats()
        assert ".csv" in converter.supported_input_formats()
        assert ".ods" in converter.supported_input_formats()
        assert ".csv" in converter.supported_output_formats()
        assert ".xlsx" in converter.supported_output_formats()
        assert converter.category() == "Planilha"

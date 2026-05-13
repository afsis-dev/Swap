# Histórico de Alterações:
#   Data       | Desenvolvedor  | Ticket | Observação
#   -----------|----------------|--------|-------------------
#   2026-05-13 | AFSIS Dev      | #001   | Implementação v1.1.0


import pytest
import tempfile
from pathlib import Path
from src.converters.base import ConversionError, UnsupportedFormatError
from src.converters.image import ImageConverter


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def sample_jpg(tmp_dir):
    from PIL import Image
    img = Image.new("RGB", (100, 100), color="red")
    path = tmp_dir / "test.jpg"
    img.save(str(path), "JPEG")
    return path


@pytest.fixture
def sample_png(tmp_dir):
    from PIL import Image
    img = Image.new("RGBA", (50, 50), color=(0, 255, 0, 128))
    path = tmp_dir / "test.png"
    img.save(str(path), "PNG")
    return path


class TestImageConverter:

    def test_jpg_to_png(self, sample_jpg, tmp_dir):
        converter = ImageConverter()
        output = tmp_dir / "output.png"
        converter.convert(sample_jpg, output)
        assert output.exists()
        from PIL import Image
        with Image.open(output) as img:
            assert img.format == "PNG"

    def test_png_to_jpg(self, sample_png, tmp_dir):
        converter = ImageConverter()
        output = tmp_dir / "output.jpg"
        converter.convert(sample_png, output)
        assert output.exists()
        from PIL import Image
        with Image.open(output) as img:
            assert img.format == "JPEG"

    def test_png_to_webp(self, sample_png, tmp_dir):
        converter = ImageConverter()
        output = tmp_dir / "output.webp"
        converter.convert(sample_png, output)
        assert output.exists()
        from PIL import Image
        with Image.open(output) as img:
            assert img.format == "WEBP"

    def test_png_to_bmp(self, sample_png, tmp_dir):
        converter = ImageConverter()
        output = tmp_dir / "output.bmp"
        converter.convert(sample_png, output)
        assert output.exists()

    def test_png_to_tiff(self, sample_png, tmp_dir):
        converter = ImageConverter()
        output = tmp_dir / "output.tiff"
        converter.convert(sample_png, output)
        assert output.exists()

    def test_png_to_ico(self, sample_png, tmp_dir):
        converter = ImageConverter(options={"ico_sizes": "16,32,48"})
        output = tmp_dir / "output.ico"
        converter.convert(sample_png, output)
        assert output.exists()

    def test_quality_param(self, sample_png, tmp_dir):
        conv_low = ImageConverter(options={"quality": 10})
        conv_high = ImageConverter(options={"quality": 95})

        out_low = tmp_dir / "low.jpg"
        out_high = tmp_dir / "high.jpg"

        conv_low.convert(sample_png, out_low)
        conv_high.convert(sample_png, out_high)

        assert out_low.stat().st_size < out_high.stat().st_size

    def test_invalid_format(self, sample_png, tmp_dir):
        converter = ImageConverter()
        output = tmp_dir / "output.xyz"
        with pytest.raises(ConversionError):
            converter.convert(sample_png, output)

    def test_resize(self, sample_png, tmp_dir):
        converter = ImageConverter(options={"resize_width": 25, "resize_height": 25})
        output = tmp_dir / "resized.png"
        converter.convert(sample_png, output)
        from PIL import Image
        with Image.open(output) as img:
            assert img.size == (25, 25)

    def test_supported_formats(self):
        converter = ImageConverter()
        assert ".jpg" in converter.supported_input_formats()
        assert ".png" in converter.supported_input_formats()
        assert ".png" in converter.supported_output_formats()
        assert ".jpg" in converter.supported_output_formats()
        assert converter.category() == "Imagem"

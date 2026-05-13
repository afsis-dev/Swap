# Histórico de Alterações:
#   Data       | Desenvolvedor  | Ticket | Observação
#   -----------|----------------|--------|-------------------
#   2026-05-13 | AFSIS Dev      | #001   | Implementação v1.1.0


import pytest
import tempfile
from pathlib import Path
from src.converters.image import ImageConverter
from src.converters.base import ConversionError


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def sample_rgba_png(tmp_dir):
    from PIL import Image
    img = Image.new("RGBA", (64, 64), color=(255, 0, 0, 128))
    path = tmp_dir / "rgba.png"
    img.save(str(path), "PNG")
    return path


@pytest.fixture
def sample_gray_png(tmp_dir):
    from PIL import Image
    img = Image.new("L", (32, 32), color=128)
    path = tmp_dir / "gray.png"
    img.save(str(path), "PNG")
    return path


@pytest.fixture
def sample_palette_png(tmp_dir):
    from PIL import Image
    img = Image.new("P", (32, 32))
    path = tmp_dir / "palette.png"
    img.save(str(path), "PNG")
    return path


class TestImageConverterEdgeCases:

    def test_rgba_to_jpg(self, sample_rgba_png, tmp_dir):
        converter = ImageConverter()
        output = tmp_dir / "output.jpg"
        converter.convert(sample_rgba_png, output)
        assert output.exists()
        from PIL import Image
        with Image.open(output) as img:
            assert img.format == "JPEG"
            assert img.mode == "RGB"

    def test_palette_to_jpg(self, sample_palette_png, tmp_dir):
        converter = ImageConverter()
        output = tmp_dir / "output.jpg"
        converter.convert(sample_palette_png, output)
        assert output.exists()

    def test_gray_to_jpg(self, sample_gray_png, tmp_dir):
        converter = ImageConverter()
        output = tmp_dir / "output.jpg"
        converter.convert(sample_gray_png, output)
        assert output.exists()

    def test_resize_width_only(self, sample_rgba_png, tmp_dir):
        converter = ImageConverter(options={"resize_width": 20})
        output = tmp_dir / "output.png"
        converter.convert(sample_rgba_png, output)
        from PIL import Image
        with Image.open(output) as img:
            assert img.width == 20

    def test_resize_height_only(self, sample_rgba_png, tmp_dir):
        converter = ImageConverter(options={"resize_height": 16})
        output = tmp_dir / "output.png"
        converter.convert(sample_rgba_png, output)
        from PIL import Image
        with Image.open(output) as img:
            assert img.height == 16

    def test_ico_default_sizes(self, sample_rgba_png, tmp_dir):
        converter = ImageConverter()
        output = tmp_dir / "output.ico"
        converter.convert(sample_rgba_png, output)
        assert output.exists()

    def test_webp_quality(self, sample_rgba_png, tmp_dir):
        conv_low = ImageConverter(options={"quality": 10})
        conv_high = ImageConverter(options={"quality": 95})

        out_low = tmp_dir / "low.webp"
        out_high = tmp_dir / "high.webp"

        conv_low.convert(sample_rgba_png, out_low)
        conv_high.convert(sample_rgba_png, out_high)

        assert out_low.exists()
        assert out_high.exists()

    def test_progress_callback(self, sample_rgba_png, tmp_dir):
        calls = []
        converter = ImageConverter()
        output = tmp_dir / "output.png"
        converter.convert(sample_rgba_png, output, progress_callback=lambda p: calls.append(p))
        assert len(calls) >= 1
        assert calls[-1] == 1.0

    def test_options_schema(self):
        converter = ImageConverter()
        schema = converter.get_options_schema()
        assert "quality" in schema
        assert "dpi" in schema
        assert "resize_width" in schema
        assert "ico_sizes" in schema

    def test_can_convert(self):
        converter = ImageConverter()
        assert converter.can_convert(".jpg", ".png") is True
        assert converter.can_convert(".png", ".jpg") is True
        assert converter.can_convert(".pdf", ".png") is False

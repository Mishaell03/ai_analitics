"""Тесты обработки изображений: проверка, конвертация, очистка метаданных."""

import asyncio
import io

import pytest
from PIL import Image

from app.utils.img_convertor import ImageValidationError, image_convertor


def run(coroutine):
    """ЗАПУСКАЕТ КОРУТИНУ В СИНХРОННОМ ТЕСТЕ"""

    return asyncio.run(coroutine)


def make_image(
        size: tuple[int, int] = (800, 600),
        image_format: str = "PNG",
        **kwargs,
) -> bytes:
    """ГОТОВИТ ИЗОБРАЖЕНИЕ ЗАДАННОГО ФОРМАТА"""

    buffer = io.BytesIO()

    Image.new("RGB", size, (10, 120, 200)).save(buffer, format=image_format, **kwargs)

    return buffer.getvalue()


def test_converts_png_to_webp():
    result = run(image_convertor.to_webp(data=make_image()))

    assert result.content_type == "image/webp"
    assert result.original_format == "PNG"
    assert result.width == 800
    assert result.height == 600
    assert result.size_bytes == len(result.content)

    # результат действительно WebP
    with Image.open(io.BytesIO(result.content)) as converted:
        assert converted.format == "WEBP"


def test_keeps_proportions():
    result = run(image_convertor.to_webp(data=make_image(size=(800, 400))))

    assert result.width == 800
    assert result.height == 400
    assert result.width / result.height == 2


def test_drops_image_metadata():
    source = make_image(image_format="JPEG", exif=Image.Exif())

    result = run(image_convertor.to_webp(data=source))

    with Image.open(io.BytesIO(result.content)) as converted:
        assert not converted.getexif()
        assert "exif" not in converted.info


def test_rejects_unknown_format():
    with pytest.raises(ImageValidationError) as error:
        run(image_convertor.to_webp(data=b"not an image"))

    assert error.value.code == "MEDIA_FILE_CORRUPTED"


def test_rejects_not_allowed_content_type():
    with pytest.raises(ImageValidationError) as error:
        run(image_convertor.to_webp(data=make_image(), content_type="image/svg+xml"))

    assert error.value.code == "MEDIA_FILE_TYPE_NOT_ALLOWED"


def test_rejects_too_big_file():
    with pytest.raises(ImageValidationError) as error:
        run(image_convertor.to_webp(data=make_image(), max_size=10))

    assert error.value.code == "MEDIA_FILE_TOO_LARGE"


def test_rejects_too_large_resolution():
    with pytest.raises(ImageValidationError) as error:
        run(
            image_convertor.to_webp(
                data=make_image(size=(4000, 3000)),
                max_dimension=1000,
            )
        )

    assert error.value.code == "MEDIA_IMAGE_RESOLUTION_TOO_LARGE"


def test_rejects_too_many_pixels(monkeypatch):
    monkeypatch.setattr("app.utils.img_convertor.settings.media_max_image_pixels", 100)

    with pytest.raises(ImageValidationError) as error:
        run(image_convertor.to_webp(data=make_image(size=(100, 100))))

    assert error.value.code == "MEDIA_IMAGE_RESOLUTION_TOO_LARGE"

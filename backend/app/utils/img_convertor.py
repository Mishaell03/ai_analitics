"""ОБРАБОТКА ИЗОБРАЖЕНИЙ

Изображение приходит от пользователя, поэтому перед сохранением его
нужно проверить и привести к одному формату:

    * проверить реальный формат файла (по содержимому, а не по имени);
    * проверить размер и разрешение;
    * пережать в WebP, сохранив пропорции;
    * не сохранять лишние метаданные (EXIF с координатами и камерой).

Ошибки разбора и проверки — доменные исключения: сервис переводит их
в понятные ответы API.
"""

import asyncio
import warnings
from dataclasses import dataclass
from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.config import settings

# Pillow должен сам предупреждать о слишком больших изображениях:
# лимит берём из конфигурации, а не из дефолта библиотеки
Image.MAX_IMAGE_PIXELS = settings.media_max_image_pixels


class ImageValidationError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class ProcessedImage:
    """ГОТОВОЕ К СОХРАНЕНИЮ ИЗОБРАЖЕНИЕ"""

    content: bytes
    content_type: str
    width: int
    height: int
    size_bytes: int
    original_format: str


# форматы, которые принимаем на входе
SUPPORTED_FORMATS = frozenset({
    "JPEG",
    "PNG",
    "WEBP",
    "GIF",
    "BMP",
    "AVIF",
    "TIFF",
})

# MIME-типы, которые заранее отсекаем
ALLOWED_CONTENT_TYPES = frozenset({
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
    "image/bmp",
    "image/avif",
    "image/tiff",
})


class ImageConvertor:
    """ПРОВЕРЯЕТ И КОНВЕРТИРУЕТ ИЗОБРАЖЕНИЯ"""

    async def to_webp(
        self,
        data: bytes,
        content_type: str | None = None,
        max_size: int | None = None,
        max_dimension: int | None = None,
        quality: int | None = None,
    ) -> ProcessedImage:
        return await asyncio.to_thread(
            self._to_webp_sync,
            data,
            content_type,
            max_size,
            max_dimension,
            quality,
        )

    @staticmethod
    def _to_webp_sync(
        data: bytes,
        content_type: str | None,
        max_size: int | None,
        max_dimension: int | None,
        quality: int | None,
    ) -> ProcessedImage:
        max_size = (
            max_size
            if max_size is not None
            else settings.media_max_image_size
        )
        max_dimension = (
            max_dimension
            if max_dimension is not None
            else settings.media_max_image_dimension
        )
        quality = (
            quality
            if quality is not None
            else settings.media_image_quality
        )

        if not data:
            raise ImageValidationError(
                code="MEDIA_FILE_CORRUPTED",
                message="Файл изображения пустой",
            )

        if len(data) > max_size:
            raise ImageValidationError(
                code="MEDIA_FILE_TOO_LARGE",
                message="Файл изображения больше допустимого размера",
            )

        if (
            content_type
            and content_type.lower() not in ALLOWED_CONTENT_TYPES
        ):
            raise ImageValidationError(
                code="MEDIA_FILE_TYPE_NOT_ALLOWED",
                message="Такой формат изображения не поддерживается",
            )

        try:
            with warnings.catch_warnings():
                warnings.simplefilter(
                    "error",
                    Image.DecompressionBombWarning,
                )

                with Image.open(BytesIO(data)) as image:
                    image_format = image.format

                    if image_format not in SUPPORTED_FORMATS:
                        raise ImageValidationError(
                            code="MEDIA_FILE_TYPE_NOT_ALLOWED",
                            message="Такой формат изображения не поддерживается",
                        )

                    width, height = image.size

                    if (
                        width > max_dimension
                        or height > max_dimension
                    ):
                        raise ImageValidationError(
                            code="MEDIA_IMAGE_RESOLUTION_TOO_LARGE",
                            message="Разрешение изображения больше допустимого",
                        )

                    if width * height > settings.media_max_image_pixels:
                        raise ImageValidationError(
                            code="MEDIA_IMAGE_RESOLUTION_TOO_LARGE",
                            message="Изображение содержит слишком много пикселей",
                        )

                    has_alpha = (
                        image.mode in ("RGBA", "LA")
                        or (
                            image.mode == "P"
                            and "transparency" in image.info
                        )
                    )

                    image = ImageOps.exif_transpose(image)

                    image = image.convert(
                        "RGBA" if has_alpha else "RGB"
                    )

                    image.thumbnail((
                        max_dimension,
                        max_dimension,
                    ))

                    output = BytesIO()

                    image.save(
                        output,
                        format="WEBP",
                        quality=quality,
                        method=6,
                    )

                    content = output.getvalue()

                    return ProcessedImage(
                        content=content,
                        content_type="image/webp",
                        width=image.width,
                        height=image.height,
                        size_bytes=len(content),
                        original_format=image_format,
                    )

        except ImageValidationError:
            raise

        except (
            Image.DecompressionBombError,
            Image.DecompressionBombWarning,
        ) as error:
            raise ImageValidationError(
                code="MEDIA_IMAGE_RESOLUTION_TOO_LARGE",
                message="Изображение содержит слишком много пикселей",
            ) from error

        except (
            UnidentifiedImageError,
            OSError,
            ValueError,
        ) as error:
            raise ImageValidationError(
                code="MEDIA_FILE_CORRUPTED",
                message="Не удалось прочитать изображение",
            ) from error


image_convertor = ImageConvertor()

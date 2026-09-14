from io import BytesIO

from fastapi import UploadFile
from PIL import Image


class ImageConvertor:

    @staticmethod
    async def to_webp(
        file: UploadFile,
        quality: int = 85,
    ) -> BytesIO:
        data = await file.read()

        source = BytesIO(data)

        with Image.open(source) as image:
            if image.mode in ("RGBA", "LA") or (
                image.mode == "P" and "transparency" in image.info
            ):
                image = image.convert("RGBA")
            else:
                image = image.convert("RGB")

            output = BytesIO()

            image.save(
                output,
                format="WEBP",
                quality=quality,
                method=6,
            )

        output.seek(0)

        return output


image_convertor = ImageConvertor()
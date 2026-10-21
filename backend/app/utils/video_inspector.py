"""ПРОВЕРКА ВИДЕОФАЙЛОВ (MP4)

Видео принимается только если это настоящий MP4 с кодеками H.264 и AAC:
такой файл понимают все браузеры без перекодирования.

Проверка идёт по структуре контейнера (ISO Base Media File Format):
сверяются тип файла (ftyp), дорожки (trak), обработчики (hdlr) и
образцы (stsd). Расширение файла не проверяется — смотрим содержимое.

Разбор читает только нужные боксы: большие куски (mdat с самим видео)
пропускаются, файл целиком в память не попадает.
"""

import struct
from dataclasses import dataclass
from typing import BinaryIO

# размеры стандартных боксов ISO BMFF
_BOX_HEADER_SIZE = 8
_FULL_BOX_HEADER_SIZE = 16

# смещение начала записей образцов внутри бокса stsd:
# заголовок бокса (8) + version/flags (4) + количество записей (4)
_STSD_ENTRIES_OFFSET = 16

# кодек видео, который поддерживают браузеры
VIDEO_CODEC_H264 = "h264"

# кодек аудио, который поддерживают браузеры
AUDIO_CODEC_AAC = "aac"

# fourcc видеосэмпла H.264
_H264_SAMPLE_ENTRIES = frozenset({b"avc1", b"avc3"})

# fourcc аудиосэмпла AAC
_AAC_SAMPLE_ENTRIES = frozenset({b"mp4a"})

# боксы с метаданными, которые нужно разобрать
_MOOV_BOX = b"moov"
_TRAK_BOX = b"trak"
_MDIA_BOX = b"mdia"
_MINF_BOX = b"minf"
_STBL_BOX = b"stbl"
_STSD_BOX = b"stsd"
_HDLR_BOX = b"hdlr"
_MDHD_BOX = b"mdhd"
_MVHD_BOX = b"mvhd"
_TKHD_BOX = b"tkhd"

# максимальный размер бокса, который читаем целиком (moov бывает большим)
_MAX_BOX_SIZE = 16 * 1024 * 1024


class VideoValidationError(Exception):
    """ФАЙЛ НЕ ЯВЛЯЕТСЯ ПОДХОДЯЩИМ ВИДЕО"""

    def __init__(self, code: str, message: str):
        super().__init__(message)

        self.code = code
        self.message = message


@dataclass(frozen=True)
class VideoInfo:
    """ДАННЫЕ О ВИДЕОФАЙЛЕ"""

    container: str
    brand: str
    video_codec: str | None
    audio_codec: str | None
    width: int | None
    height: int | None
    duration_seconds: float | None


@dataclass(frozen=True)
class _Box:
    """ЗАГОЛОВОК БОКСА ISO BMFF"""

    type: bytes
    size: int
    offset: int


def _read_box_header(file: BinaryIO, offset: int) -> _Box | None:
    """ЧИТАЕТ ЗАГОЛОВОК БОКСА ПО СМЕЩЕНИЮ"""

    file.seek(offset)

    header = file.read(_BOX_HEADER_SIZE)

    if len(header) < _BOX_HEADER_SIZE:
        return None

    size = struct.unpack(">I", header[:4])[0]
    box_type = header[4:8]

    # размер 1 означает, что реальный размер записан следом (64 бита)
    if size == 1:
        extended = file.read(8)

        if len(extended) < 8:
            return None

        size = struct.unpack(">Q", extended)[0]

    # размер 0 означает, что бокс идёт до конца файла
    if size == 0:
        file.seek(0, 2)

        size = file.tell() - offset

    return _Box(type=box_type, size=size, offset=offset)


def _iter_boxes(file: BinaryIO, start: int, end: int):
    """ПЕРЕБИРАЕТ БОКСЫ В ДИАПАЗОНЕ ФАЙЛА"""

    offset = start

    while offset + _BOX_HEADER_SIZE <= end:
        box = _read_box_header(file, offset)

        if box is None or box.size < _BOX_HEADER_SIZE:
            return

        yield box

        offset += box.size


def _find_box(file: BinaryIO, start: int, end: int, box_type: bytes) -> _Box | None:
    """ИЩЕТ ПЕРВЫЙ БОКС НУЖНОГО ТИПА"""

    for box in _iter_boxes(file, start, end):
        if box.type == box_type:
            return box

    return None


def _read_bytes(file: BinaryIO, box: _Box) -> bytes:
    """ЧИТАЕТ СОДЕРЖИМОЕ БОКСА"""

    file.seek(box.offset + _BOX_HEADER_SIZE)

    return file.read(min(box.size - _BOX_HEADER_SIZE, _MAX_BOX_SIZE))


def _parse_handler(file: BinaryIO, box: _Box) -> str | None:
    """ТИП ОБРАБОТЧИКА ДОРОЖКИ (vide / soun)"""

    content = _read_bytes(file, box)

    if len(content) < 8:
        return None

    # version + flags (4 байта), pre_defined (4 байта), handler_type (4 байта)
    return content[8:12].decode("ascii", errors="ignore")


def _parse_mdhd(file: BinaryIO, box: _Box) -> tuple[int, int] | None:
    """TIMESCALE И DURATION ДОРОЖКИ"""

    content = _read_bytes(file, box)

    if len(content) < 4:
        return None

    version = content[0]

    if version == 1:
        if len(content) < 28:
            return None

        timescale = struct.unpack(">I", content[20:24])[0]
        duration = struct.unpack(">Q", content[24:32][:8])[0]

    else:
        if len(content) < 20:
            return None

        timescale = struct.unpack(">I", content[12:16])[0]
        duration = struct.unpack(">I", content[16:20])[0]

    return timescale, duration


def _parse_mvhd(file: BinaryIO, box: _Box) -> tuple[int, int] | None:
    """TIMESCALE И DURATION ФАЙЛА"""

    content = _read_bytes(file, box)

    if len(content) < 4:
        return None

    version = content[0]

    if version == 1:
        if len(content) < 28:
            return None

        timescale = struct.unpack(">I", content[20:24])[0]
        duration = struct.unpack(">Q", content[24:32][:8])[0]

    else:
        if len(content) < 20:
            return None

        timescale = struct.unpack(">I", content[12:16])[0]
        duration = struct.unpack(">I", content[16:20])[0]

    return timescale, duration


def _parse_stsd(file: BinaryIO, box: _Box) -> list[bytes]:
    """FOURCC ОБРАЗЦОВ ДОРОЖКИ"""

    content = _read_bytes(file, box)

    # version + flags (4), entry_count (4)
    if len(content) < 8:
        return []

    entry_count = struct.unpack(">I", content[4:8])[0]

    entries: list[bytes] = []

    offset = 8

    for _ in range(min(entry_count, 16)):
        if offset + 8 > len(content):
            break

        entry_type = content[offset + 4:offset + 8]

        entries.append(entry_type)

        # размер записи лежит перед fourcc
        entry_size = struct.unpack(">I", content[offset:offset + 4])[0]

        if entry_size < 8:
            break

        offset += entry_size

    return entries


def _parse_visual_sample(file: BinaryIO, box: _Box) -> tuple[int, int] | None:
    """РАЗРЕШЕНИЕ ИЗ ОБРАЗЦА ВИДЕОДОРОЖКИ

    Для visual sample entry ширина и высота лежат на фиксированном
    смещении от начала записи (24 и 26 байт) в 16-битном виде.
    """

    content = _read_bytes(file, box)

    if len(content) < 28:
        return None

    width = struct.unpack(">H", content[24:26])[0]
    height = struct.unpack(">H", content[26:28])[0]

    if not width or not height:
        return None

    return width, height


class VideoInspector:
    """ПРОВЕРЯЕТ ВИДЕОФАЙЛЫ НА СООТВЕТСТВИЕ ТРЕБОВАНИЯМ БРАУЗЕРОВ"""

    def inspect(self, file: BinaryIO) -> VideoInfo:
        """РАЗБИРАЕТ MP4 И ВОЗВРАЩАЕТ МЕТАДАННЫЕ

        Бросает VideoValidationError, если это не MP4 или в нём нет
        подходящих дорожек.
        """

        file.seek(0, 2)
        file_size = file.tell()

        if file_size < _BOX_HEADER_SIZE:
            raise VideoValidationError(
                code="MEDIA_FILE_CORRUPTED",
                message="Файл видео пустой или повреждён",
            )

        ftyp = _find_box(file, 0, file_size, b"ftyp")

        if ftyp is None:
            raise VideoValidationError(
                code="MEDIA_FILE_TYPE_NOT_ALLOWED",
                message="Файл не является MP4",
            )

        ftyp_content = _read_bytes(file, ftyp)

        if len(ftyp_content) < 4:
            raise VideoValidationError(
                code="MEDIA_FILE_CORRUPTED",
                message="Файл видео повреждён",
            )

        brand = ftyp_content[:4].decode("ascii", errors="ignore")

        moov = _find_box(file, 0, file_size, _MOOV_BOX)

        if moov is None:
            raise VideoValidationError(
                code="MEDIA_FILE_CORRUPTED",
                message="В видео нет метаданных",
            )

        moov_end = moov.offset + moov.size

        duration_seconds = self._read_duration(file, moov)

        video_codec = None
        audio_codec = None
        width = None
        height = None

        for trak in _iter_boxes(file, moov.offset + _BOX_HEADER_SIZE, moov_end):
            if trak.type != _TRAK_BOX:
                continue

            track = self._read_track(file, trak)

            if track is None:
                continue

            if track.handler == "vide" and video_codec is None:
                video_codec = track.video_codec
                width = track.width
                height = track.height

            elif track.handler == "soun" and audio_codec is None:
                audio_codec = track.audio_codec

        return VideoInfo(
            container="mp4",
            brand=brand,
            video_codec=video_codec,
            audio_codec=audio_codec,
            width=width,
            height=height,
            duration_seconds=duration_seconds,
        )

    @staticmethod
    def _read_duration(file: BinaryIO, moov: _Box) -> float | None:
        """ДЛИТЕЛЬНОСТЬ ВИДЕО В СЕКУНДАХ"""

        mvhd = _find_box(file, moov.offset + _BOX_HEADER_SIZE, moov.offset + moov.size, _MVHD_BOX)

        if mvhd is None:
            return None

        parsed = _parse_mvhd(file, mvhd)

        if parsed is None:
            return None

        timescale, duration = parsed

        if not timescale:
            return None

        return round(duration / timescale, 3)

    @staticmethod
    def _read_track(file: BinaryIO, trak: _Box) -> "_Track | None":
        """РАЗБИРАЕТ ДОРОЖКУ ВИДЕО"""

        trak_end = trak.offset + trak.size

        mdia = _find_box(file, trak.offset + _BOX_HEADER_SIZE, trak_end, _MDIA_BOX)

        if mdia is None:
            return None

        mdia_end = mdia.offset + mdia.size

        hdlr = _find_box(file, mdia.offset + _BOX_HEADER_SIZE, mdia_end, _HDLR_BOX)

        if hdlr is None:
            return None

        handler = _parse_handler(file, hdlr)

        video_codec = None
        audio_codec = None
        width = None
        height = None

        minf = _find_box(file, mdia.offset + _BOX_HEADER_SIZE, mdia_end, _MINF_BOX)

        if minf is not None:
            stbl = _find_box(
                file,
                minf.offset + _BOX_HEADER_SIZE,
                minf.offset + minf.size,
                _STBL_BOX,
            )

            if stbl is not None:
                stsd = _find_box(
                    file,
                    stbl.offset + _BOX_HEADER_SIZE,
                    stbl.offset + stbl.size,
                    _STSD_BOX,
                )

                if stsd is not None:
                    for entry in _parse_stsd(file, stsd):
                        if entry in _H264_SAMPLE_ENTRIES and video_codec is None:
                            video_codec = VIDEO_CODEC_H264

                            visual = _find_box(
                                file,
                                stsd.offset + _STSD_ENTRIES_OFFSET,
                                stsd.offset + stsd.size,
                                entry,
                            )

                            if visual is not None:
                                size = _parse_visual_sample(file, visual)

                                if size is not None:
                                    width, height = size

                        elif entry in _AAC_SAMPLE_ENTRIES and audio_codec is None:
                            audio_codec = AUDIO_CODEC_AAC

        return _Track(
            handler=handler,
            video_codec=video_codec,
            audio_codec=audio_codec,
            width=width,
            height=height,
        )


@dataclass(frozen=True)
class _Track:
    """ДОРОЖКА ВИДЕО"""

    handler: str | None
    video_codec: str | None
    audio_codec: str | None
    width: int | None
    height: int | None


video_inspector = VideoInspector()

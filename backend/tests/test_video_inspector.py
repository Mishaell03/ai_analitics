"""Сборка тестовых MP4-файлов и проверка разбора контейнера."""

import io
import struct

import pytest

from app.utils.video_inspector import VideoInspector, VideoValidationError


def box(box_type: bytes, payload: bytes) -> bytes:
    """БОКС ISO BMFF"""

    return struct.pack(">I", len(payload) + 8) + box_type + payload


def full_box(box_type: bytes, version: int = 0, payload: bytes = b"") -> bytes:
    """БОКС С VERSION И FLAGS"""

    return box(box_type, struct.pack(">B3x", version) + payload)


def make_ftyp(brand: bytes = b"isom") -> bytes:
    return box(b"ftyp", brand + struct.pack(">I", 512) + b"isom" + b"mp42")


def make_mvhd(timescale: int = 1000, duration: int = 12000) -> bytes:
    payload = (
        struct.pack(">I", 0)          # creation time
        + struct.pack(">I", 0)        # modification time
        + struct.pack(">I", timescale)
        + struct.pack(">I", duration)
        + struct.pack(">I", 0x00010000)
        + struct.pack(">H", 0x0100)
        + struct.pack(">H", 0)
        + b"\x00" * 8
        + b"\x00" * 36
        + b"\x00" * 24
        + struct.pack(">I", 3)
    )

    return full_box(b"mvhd", payload=payload)


def make_hdlr(handler: bytes) -> bytes:
    payload = struct.pack(">I", 0) + handler + b"\x00" * 12 + b"\x00"

    return full_box(b"hdlr", payload=payload)


def make_mdhd(timescale: int = 1000, duration: int = 12000) -> bytes:
    payload = (
        struct.pack(">I", 0)
        + struct.pack(">I", 0)
        + struct.pack(">I", timescale)
        + struct.pack(">I", duration)
        + struct.pack(">H", 0x55C4)
        + struct.pack(">H", 0)
    )

    return full_box(b"mdhd", payload=payload)


def make_visual_sample_entry(width: int = 1280, height: int = 720) -> bytes:
    payload = (
        b"\x00" * 6                    # reserved
        + struct.pack(">H", 1)         # data reference index
        + struct.pack(">H", 0)         # pre_defined
        + struct.pack(">H", 0)         # reserved
        + b"\x00" * 12                 # pre_defined[3]
        + struct.pack(">H", width)
        + struct.pack(">H", height)
        + b"\x00" * 50                 # остальное тело записи
    )

    return box(b"avc1", payload)


def make_audio_sample_entry() -> bytes:
    payload = b"\x00" * 6 + struct.pack(">H", 1) + b"\x00" * 20

    return box(b"mp4a", payload)


def make_stsd(sample_entry: bytes) -> bytes:
    payload = struct.pack(">I", 1) + sample_entry

    return full_box(b"stsd", payload=payload)


def make_trak(handler: bytes, sample_entry: bytes) -> bytes:
    stbl = box(b"stbl", make_stsd(sample_entry))
    minf = box(b"minf", stbl)
    mdia = box(b"mdia", make_mdhd() + make_hdlr(handler) + minf)
    tkhd = full_box(b"tkhd", payload=b"\x00" * 84)

    return box(b"trak", tkhd + mdia)


def make_mp4(
        with_video: bool = True,
        with_audio: bool = True,
        width: int = 1280,
        height: int = 720,
) -> bytes:
    """СОБИРАЕТ МИНИМАЛЬНЫЙ MP4 С ДОРОЖКАМИ"""

    tracks = b""

    if with_video:
        tracks += make_trak(b"vide", make_visual_sample_entry(width, height))

    if with_audio:
        tracks += make_trak(b"soun", make_audio_sample_entry())

    moov = box(b"moov", make_mvhd() + tracks)

    return make_ftyp() + moov + box(b"mdat", b"\x00" * 64)


def test_inspect_reads_container_and_codecs():
    inspector = VideoInspector()

    info = inspector.inspect(io.BytesIO(make_mp4()))

    assert info.container == "mp4"
    assert info.brand == "isom"
    assert info.video_codec == "h264"
    assert info.audio_codec == "aac"
    assert info.width == 1280
    assert info.height == 720
    assert info.duration_seconds == 12.0


def test_inspect_reads_video_without_audio():
    inspector = VideoInspector()

    info = inspector.inspect(io.BytesIO(make_mp4(with_audio=False)))

    assert info.video_codec == "h264"
    assert info.audio_codec is None


def test_inspect_rejects_not_mp4():
    inspector = VideoInspector()

    with pytest.raises(VideoValidationError) as error:
        inspector.inspect(io.BytesIO(b"not a video at all"))

    assert error.value.code == "MEDIA_FILE_TYPE_NOT_ALLOWED"


def test_inspect_rejects_empty_file():
    inspector = VideoInspector()

    with pytest.raises(VideoValidationError) as error:
        inspector.inspect(io.BytesIO(b""))

    assert error.value.code == "MEDIA_FILE_CORRUPTED"


def test_inspect_rejects_file_without_metadata():
    inspector = VideoInspector()

    with pytest.raises(VideoValidationError) as error:
        inspector.inspect(io.BytesIO(make_ftyp() + box(b"mdat", b"\x00" * 32)))

    assert error.value.code == "MEDIA_FILE_CORRUPTED"
